package art.lazying.musia

import android.content.Context
import java.util.UUID
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.decodeFromString

@Serializable enum class PracticeMode { Listen, Tap, Play }
@Serializable data class Preferences(val speed: Float = 1f, val mode: PracticeMode = PracticeMode.Listen, val tapCalibrationMs: Int = 0)
@Serializable data class PracticeSession(
    val id: String, val songId: String, val assetId: String, val title: String,
    val startedAt: Long, val mode: PracticeMode, val playedMs: Long = 0,
    val tapOffsetsMs: List<Long> = emptyList()
)
@Serializable data class LocalData(val version: Int = 1, val preferences: Preferences = Preferences(), val sessions: List<PracticeSession> = emptyList())

class LocalStore private constructor(context: Context) {
    private val disk = context.getSharedPreferences("musia-local-v1", Context.MODE_PRIVATE)
    var recoveryWarning: String? = null
        private set
    private val state = MutableStateFlow(load())
    val data = state.asStateFlow()
    var activeSessionId: String? = null
        private set

    private fun load(): LocalData {
        val raw = disk.getString("data", null) ?: return LocalData()
        return try {
            MusiaJson.decodeFromString<LocalData>(raw).also {
                require(it.version == 1 && it.preferences.speed.isFinite())
            }.let { it.copy(preferences = it.preferences.copy(speed = it.preferences.speed.coerceIn(.25f, 2f), tapCalibrationMs = it.preferences.tapCalibrationMs.coerceIn(-300, 300))) }
        } catch (_: Exception) {
            recoveryWarning = "Local history could not be read. Reset local data to clear the damaged record."
            LocalData()
        }
    }

    private fun save(value: LocalData) {
        state.value = value
        // Preserve damaged source until the user explicitly resets it.
        if (recoveryWarning == null) disk.edit().putString("data", MusiaJson.encodeToString(value)).apply()
    }
    fun preferences(value: Preferences) = save(state.value.copy(preferences = value.copy(speed = value.speed.coerceIn(.25f, 2f), tapCalibrationMs = value.tapCalibrationMs.coerceIn(-300, 300))))
    fun begin(songId: String, assetId: String, title: String): String {
        val id = UUID.randomUUID().toString()
        activeSessionId = id
        val session = PracticeSession(id, songId, assetId, title, System.currentTimeMillis(), state.value.preferences.mode)
        save(state.value.copy(sessions = (listOf(session) + state.value.sessions).take(200)))
        return id
    }
    fun played(id: String, playedMs: Long) {
        save(state.value.copy(sessions = state.value.sessions.map { if (it.id == id) it.copy(playedMs = playedMs) else it }))
    }
    fun tap(offsetMs: Long) {
        val id = activeSessionId ?: return
        save(state.value.copy(sessions = state.value.sessions.map {
            if (it.id == id) it.copy(tapOffsetsMs = (it.tapOffsetsMs + offsetMs).takeLast(1000)) else it
        }))
    }
    fun finish() { activeSessionId = null }
    fun export(): String = MusiaJson.encodeToString(state.value)
    fun reset() {
        activeSessionId = null
        recoveryWarning = null
        save(LocalData())
    }
    companion object {
        @Volatile private var instance: LocalStore? = null
        fun get(context: Context): LocalStore = instance ?: synchronized(this) {
            instance ?: LocalStore(context.applicationContext).also { instance = it }
        }
    }
}

class PlaybackClock {
    var playedMs: Long = 0
        private set
    private var lastMs: Long? = null
    private var wasPlaying = false
    fun sample(nowMs: Long, playing: Boolean) {
        lastMs?.let { if (wasPlaying) playedMs += (nowMs - it).coerceAtLeast(0) }
        lastMs = nowMs
        wasPlaying = playing
    }
}
