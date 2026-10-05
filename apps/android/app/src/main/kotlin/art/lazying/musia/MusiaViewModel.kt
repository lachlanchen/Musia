package art.lazying.musia

import android.app.Application
import android.content.ComponentName
import android.net.Uri
import android.os.Bundle
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.core.content.ContextCompat
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import androidx.media3.common.MediaItem
import androidx.media3.common.MediaMetadata
import androidx.media3.common.PlaybackException
import androidx.media3.common.PlaybackParameters
import androidx.media3.common.Player
import androidx.media3.session.MediaController
import androidx.media3.session.SessionToken
import com.google.common.util.concurrent.ListenableFuture
import java.io.IOException
import java.net.UnknownHostException
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class LoadState<T>(val value: T? = null, val loading: Boolean = false, val error: String? = null)
data class PlaybackState(
    val connected: Boolean = false, val playing: Boolean = false,
    val buffering: Boolean = false, val positionMs: Long = 0,
    val loop: LoopRange? = null, val error: String? = null
)

@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
class MusiaViewModel(application: Application) : AndroidViewModel(application) {
    val store = LocalStore.get(application)
    var library by mutableStateOf(LoadState<Library>())
        private set
    var lessons by mutableStateOf(LoadState<Lessons>())
        private set
    var song by mutableStateOf(LoadState<Song>())
        private set
    var assetId by mutableStateOf<String?>(null)
        private set
    val asset: Asset? get() = song.value?.assets?.firstOrNull { it.id == assetId }
    var playback by mutableStateOf(PlaybackState())
        private set
    var tapFeedback by mutableStateOf<String?>(null)
        private set
    var health by mutableStateOf("Not checked")
        private set
    var notice by mutableStateOf<String?>(null)
        private set
    private var requestedId: String? = null
    private var songJob: Job? = null
    private var controller: MediaController? = null
    private var controllerFuture: ListenableFuture<MediaController>? = null
    private var closed = false
    private val listener = object : Player.Listener {
        override fun onEvents(player: Player, events: Player.Events) { refreshPlayback() }
        override fun onPlayerError(error: PlaybackException) {
            playback = playback.copy(error = "Audio unavailable (${error.errorCodeName}). Retry playback.")
        }
    }

    init { connect(); reloadLibrary(); reloadLessons() }

    fun connect() {
        controllerFuture?.let { MediaController.releaseFuture(it) }
        controllerFuture = null
        controller = null
        playback = playback.copy(connected = false, error = null)
        val app = getApplication<Application>()
        val future = MediaController.Builder(app, SessionToken(app, ComponentName(app, PlaybackService::class.java))).buildAsync()
        controllerFuture = future
        future.addListener({
            if (!closed && controllerFuture === future) {
                try {
                    controller = future.get().also { it.addListener(listener) }
                    val activeId = controller?.currentMediaItem?.mediaMetadata?.extras?.getString("songId")
                    refreshPlayback()
                    if (activeId != null && requestedId == null) openSong(activeId, restore = true)
                } catch (_: Exception) { playback = playback.copy(error = "Playback service unavailable. Reconnect.") }
            }
        }, ContextCompat.getMainExecutor(app))
    }

    fun reloadLibrary() {
        if (library.loading) return
        library = library.copy(loading = true, error = null)
        viewModelScope.launch {
            try { library = LoadState(value = MusiaApi.library()) }
            catch (e: Exception) { rethrowCancellation(e); library = library.copy(loading = false, error = failure(e)) }
        }
    }
    fun reloadLessons() {
        if (lessons.loading) return
        lessons = lessons.copy(loading = true, error = null)
        viewModelScope.launch {
            try { lessons = LoadState(value = MusiaApi.lessons()) }
            catch (e: Exception) { rethrowCancellation(e); lessons = lessons.copy(loading = false, error = failure(e)) }
        }
    }
    fun openSong(id: String, restore: Boolean = false) {
        songJob?.cancel()
        requestedId = id
        song = LoadState(loading = true)
        assetId = null
        tapFeedback = null
        if (!restore) { controller?.stop(); controller?.clearMediaItems(); playback = playback.copy(loop = null, positionMs = 0, error = null) }
        songJob = viewModelScope.launch {
            try {
                val value = MusiaApi.song(id)
                val activeAsset = if (restore) controller?.currentMediaItem?.mediaMetadata?.extras?.getString("assetId") else null
                assetId = listOfNotNull(activeAsset, value.defaultAssetId).firstOrNull { candidate -> value.assets.any { it.id == candidate } } ?: value.assets.first().id
                song = LoadState(value = value)
            } catch (e: Exception) { rethrowCancellation(e); song = LoadState(error = failure(e)) }
        }
    }
    fun retrySong() { requestedId?.let { openSong(it) } }
    fun selectAsset(id: String) {
        if (id == assetId || song.value?.assets?.none { it.id == id } != false) return
        controller?.stop(); controller?.clearMediaItems()
        assetId = id
        playback = playback.copy(loop = null, positionMs = 0, error = null)
        tapFeedback = null
    }

    private fun item(loop: LoopRange?): MediaItem? {
        val value = song.value ?: return null
        val audio = asset ?: return null
        val extras = Bundle().apply {
            putString("songId", value.id); putString("assetId", audio.id)
            putLong("loopStartMs", loop?.startMs ?: 0); putLong("loopEndMs", loop?.endMs ?: -1)
        }
        val metadata = MediaMetadata.Builder().setTitle(value.title).setArtist(value.artist).setExtras(extras)
        value.coverUrl?.let { runCatching { Uri.parse(MusiaApi.httpsUrl(it)) }.getOrNull()?.let(metadata::setArtworkUri) }
        return MediaItem.Builder().setMediaId("${value.id}/${audio.id}").setUri(MusiaApi.httpsUrl(audio.audioUrl))
            .setMediaMetadata(metadata.build()).apply {
                if (loop != null) setClippingConfiguration(MediaItem.ClippingConfiguration.Builder().setStartPositionMs(loop.startMs).setEndPositionMs(loop.endMs).build())
            }.build()
    }
    private fun configure(loop: LoopRange?, absoluteMs: Long, play: Boolean) {
        val player = controller ?: return
        val media = item(loop) ?: return
        player.setMediaItem(media, loop?.relative(absoluteMs) ?: absoluteMs.coerceAtLeast(0))
        player.repeatMode = if (loop == null) Player.REPEAT_MODE_OFF else Player.REPEAT_MODE_ONE
        player.playbackParameters = PlaybackParameters(store.data.value.preferences.speed, 1f)
        player.prepare()
        player.playWhenReady = play
        playback = playback.copy(loop = loop, error = null)
    }
    fun togglePlayback() {
        val player = controller ?: return
        if (player.isPlaying || player.playWhenReady && player.playbackState == Player.STATE_BUFFERING) {
            player.pause()
        } else {
            val expected = item(playback.loop) ?: return
            if (player.currentMediaItem?.mediaId != expected.mediaId || player.playerError != null) configure(playback.loop, playback.positionMs, true)
            else {
                if (player.playbackState == Player.STATE_ENDED) player.seekTo(0)
                if (player.playbackState == Player.STATE_IDLE) player.prepare()
                player.play()
            }
        }
    }

    fun pauseForLesson() { controller?.pause() }
    fun retryPlayback() {
        if (controller == null) connect() else configure(playback.loop, playback.positionMs, true)
    }
    fun setLoop(phrase: Phrase?) {
        val audio = asset ?: return
        val range = phrase?.let { LoopRange.from(it.start, it.end, audio.duration) }
        if (phrase != null && range == null) { notice = "This phrase is too short to loop."; return }
        configure(range, range?.startMs ?: playback.positionMs, controller?.playWhenReady == true)
        tapFeedback = null
    }
    fun seek(position: Long) {
        val audio = asset ?: return
        if (controller?.currentMediaItem == null) configure(playback.loop, position, false)
        else controller?.seekTo(playback.loop?.relative(position) ?: position.coerceIn(0, secondsToMs(audio.duration)))
        tapFeedback = null
        refreshPlayback()
    }
    fun speed(value: Float) {
        if (!value.isFinite()) return
        val safe = value.coerceIn(.25f, 2f)
        store.preferences(store.data.value.preferences.copy(speed = safe))
        controller?.playbackParameters = PlaybackParameters(safe, 1f)
        tapFeedback = null
    }
    fun mode(value: PracticeMode) {
        controller?.pause()
        store.preferences(store.data.value.preferences.copy(mode = value))
        tapFeedback = null
    }
    fun calibration(value: Int) { store.preferences(store.data.value.preferences.copy(tapCalibrationMs = value)) }
    fun lyricLanguage(code: String) {
        val current = store.data.value.preferences
        val key = lyricLanguageKey(code)
        val selected = if (key in current.lyricLanguages) current.lyricLanguages - key else current.lyricLanguages + key
        store.preferences(current.copy(lyricLanguages = selected))
    }
    fun tap() {
        val audio = asset ?: return
        val player = controller ?: return
        if (!player.isPlaying || store.data.value.preferences.mode != PracticeMode.Tap || audio.confidence.beats !in setOf("verified", "analysis", "estimated")) return
        refreshPlayback()
        if (!withinBeatRange(audio.beats, playback.positionMs)) { tapFeedback = null; return }
        val offset = tapOffsetMs(audio.beats, playback.positionMs, player.playbackParameters.speed, store.data.value.preferences.tapCalibrationMs, playback.loop)
        tapFeedback = when {
            offset == null -> "No nearby reference beat"
            offset < 0 -> "${-offset} ms early"
            offset > 0 -> "$offset ms late"
            else -> "0 ms offset"
        }
        offset?.let(store::tap)
    }
    fun refreshPlayback() {
        val player = controller ?: return
        val extras = player.currentMediaItem?.mediaMetadata?.extras
        val a = extras?.getLong("loopStartMs", 0) ?: 0
        val b = extras?.getLong("loopEndMs", -1) ?: -1
        val loop = if (b - a >= 100) LoopRange(a, b) else null
        playback = playback.copy(
            connected = player.isConnected, playing = player.isPlaying,
            buffering = player.playbackState == Player.STATE_BUFFERING,
            positionMs = loop?.absolute(player.currentPosition) ?: player.currentPosition.coerceAtLeast(0), loop = loop
        )
        if (!player.isPlaying || asset?.let { withinBeatRange(it.beats, playback.positionMs) } != true) tapFeedback = null
    }
    fun checkHealth() {
        if (health == "Checking") return
        health = "Checking"
        viewModelScope.launch {
            health = try { if (MusiaApi.healthy()) "Reachable" else "Service unavailable" }
            catch (e: Exception) { rethrowCancellation(e); "Unreachable" }
        }
    }
    fun export(uri: Uri) {
        val content = store.export()
        viewModelScope.launch {
            notice = try {
                withContext(Dispatchers.IO) {
                    val output = getApplication<Application>().contentResolver.openOutputStream(uri, "wt") ?: throw IOException("No destination")
                    output.bufferedWriter().use { it.write(content) }
                }
                "Local history exported"
            } catch (e: Exception) { rethrowCancellation(e); "Export failed. Choose another destination." }
        }
    }
    fun reset() {
        controller?.stop(); controller?.clearMediaItems()
        store.reset()
        playback = PlaybackState(connected = controller?.isConnected == true)
        tapFeedback = null
        notice = "Local history and preferences reset"
    }
    fun clearNotice() { notice = null }
    override fun onCleared() {
        closed = true
        controller?.removeListener(listener)
        controllerFuture?.let { MediaController.releaseFuture(it) }
        super.onCleared()
    }
}

private fun rethrowCancellation(e: Exception) { if (e is CancellationException) throw e }
private fun failure(e: Exception): String = when (e) {
    is UnknownHostException -> "Cannot reach musia.lazying.art. Check your connection and retry."
    is IOException -> "Connection failed. ${e.message.orEmpty().take(120)}"
    else -> "The service response is not compatible with Musia v1. Retry after the service is updated."
}
