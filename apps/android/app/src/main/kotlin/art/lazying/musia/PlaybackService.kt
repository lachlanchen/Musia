package art.lazying.musia

import android.app.PendingIntent
import android.content.Intent
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import androidx.media3.common.AudioAttributes
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.session.MediaSession
import androidx.media3.session.MediaSessionService
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
class PlaybackService : MediaSessionService() {
    private lateinit var player: ExoPlayer
    private lateinit var store: LocalStore
    private var session: MediaSession? = null
    private val handler = Handler(Looper.getMainLooper())
    private var journalId: String? = null
    private var journalKey: String? = null
    private var clock = PlaybackClock()
    private var lastSave = 0L
    private val accountScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private val tick = object : Runnable {
        override fun run() {
            journal()
            handler.postDelayed(this, 250)
        }
    }

    override fun onCreate() {
        super.onCreate()
        store = LocalStore.get(this)
        val vault = CreatorVault.get(this)
        player = ExoPlayer.Builder(this)
            .setMediaSourceFactory(DefaultMediaSourceFactory(CreatorAudio.Sources(this, vault))).build().apply {
            setAudioAttributes(AudioAttributes.Builder().setUsage(C.USAGE_MEDIA).setContentType(C.AUDIO_CONTENT_TYPE_MUSIC).build(), true)
            setHandleAudioBecomingNoisy(true)
            setWakeMode(C.WAKE_MODE_NETWORK)
            addListener(object : Player.Listener {
                override fun onIsPlayingChanged(isPlaying: Boolean) { journal(forceSave = true) }
                override fun onMediaItemTransition(mediaItem: MediaItem?, reason: Int) { journal(forceSave = true) }
                override fun onPlaybackStateChanged(playbackState: Int) {
                    if (playbackState == Player.STATE_ENDED || playbackState == Player.STATE_IDLE) journal(forceSave = true)
                }
            })
        }
        val intent = PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        session = MediaSession.Builder(this, player).setSessionActivity(intent).build()
        accountScope.launch {
            vault.state.collect { state ->
                val owner = player.currentMediaItem?.mediaMetadata?.extras?.getString("creatorOwner")
                if (owner != null && owner != state.session?.owner) { player.stop(); player.clearMediaItems() }
            }
        }
        handler.post(tick)
    }

    private fun journal(forceSave: Boolean = false) {
        val now = SystemClock.elapsedRealtime()
        val item = player.currentMediaItem
        val metadata = item?.mediaMetadata
        val key = item?.mediaId?.plus(":" + store.data.value.preferences.mode.name)
        clock.sample(now, player.isPlaying)
        if (key != journalKey || store.activeSessionId != journalId) {
            journalId?.let { if (store.activeSessionId == it) store.played(it, clock.playedMs) }
            store.finish()
            journalId = null
            journalKey = key
            clock = PlaybackClock()
        }
        if (player.isPlaying && journalId == null && item != null) {
            journalId = store.begin(metadata?.extras?.getString("songId").orEmpty(), metadata?.extras?.getString("assetId").orEmpty(), metadata?.title.toString())
            clock.sample(now, true)
        }
        if (forceSave || now - lastSave >= 5000) {
            journalId?.let { store.played(it, clock.playedMs) }
            lastSave = now
        }
    }

    override fun onGetSession(controllerInfo: MediaSession.ControllerInfo): MediaSession? = session

    override fun onDestroy() {
        accountScope.cancel()
        handler.removeCallbacks(tick)
        player.pause()
        journal(forceSave = true)
        store.finish()
        session?.release()
        player.release()
        session = null
        super.onDestroy()
    }
}
