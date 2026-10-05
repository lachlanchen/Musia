@file:OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)
package art.lazying.musia

import android.content.Context
import android.media.*
import android.os.Handler
import android.os.Looper
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import kotlinx.coroutines.*
import kotlin.math.*

private class PracticeAudio(context: Context) {
    private val manager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    private val attributes = AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build()
    private val focus = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT).setAudioAttributes(attributes)
        .setOnAudioFocusChangeListener({ change -> if (change < 0) stop() }, Handler(Looper.getMainLooper())).build()
    private var track: AudioTrack? = null
    private var frames = 1
    var playing by mutableStateOf(false)
        private set
    val time: Double get() = ((track?.playbackHeadPosition ?: 0).toLong() and 0xffffffffL) % frames / BeginnerPractice.sampleRate.toDouble()

    fun play(pcm: ShortArray, loop: Boolean) {
        stop()
        check(manager.requestAudioFocus(focus) == AudioManager.AUDIOFOCUS_REQUEST_GRANTED) { "Audio is in use. Try again." }
        try {
            frames = pcm.size
            track = AudioTrack.Builder().setAudioAttributes(attributes)
                .setAudioFormat(AudioFormat.Builder().setSampleRate(BeginnerPractice.sampleRate).setEncoding(AudioFormat.ENCODING_PCM_16BIT).setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build())
                .setTransferMode(AudioTrack.MODE_STATIC).setBufferSizeInBytes(pcm.size * 2).build()
            check(track?.write(pcm, 0, pcm.size) == pcm.size) { "Could not prepare practice audio." }
            if (loop) check(track?.setLoopPoints(0, pcm.size, -1) == AudioTrack.SUCCESS)
            else {
                track?.setPlaybackPositionUpdateListener(object : AudioTrack.OnPlaybackPositionUpdateListener {
                    override fun onMarkerReached(finished: AudioTrack) { if (track === finished) stop() }
                    override fun onPeriodicNotification(track: AudioTrack) = Unit
                }, Handler(Looper.getMainLooper()))
                check(track?.setNotificationMarkerPosition(pcm.size) == AudioTrack.SUCCESS)
            }
            track?.play(); playing = true
        } catch (error: Exception) { stop(); throw error }
    }
    fun stop() {
        playing = false
        track?.release(); track = null
        manager.abandonAudioFocusRequest(focus)
    }
}

@Composable fun BeginnerPracticeScreen(rhythm: Boolean, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val sound = remember { PracticeAudio(context.applicationContext) }
    val scope = rememberCoroutineScope()
    val lifecycle = LocalLifecycleOwner.current
    var count by remember { mutableIntStateOf(3) }
    var quiz by remember { mutableStateOf(false) }
    var explored by remember { mutableStateOf<Int?>(null) }
    var round by remember { mutableStateOf(PitchRound(listOf(0, 1, 2, 0, 1, 2).shuffled())) }
    var heard by remember { mutableStateOf(false) }
    var bpm by remember { mutableFloatStateOf(60f) }
    var chords by remember { mutableStateOf(false) }
    var time by remember { mutableDoubleStateOf(0.0) }
    var taps by remember { mutableStateOf(emptyList<Double>()) }
    var lastTap by remember { mutableDoubleStateOf(-1.0) }
    var issue by remember { mutableStateOf<String?>(null) }
    var pending by remember { mutableStateOf<Job?>(null) }
    fun stop() { pending?.cancel(); pending = null; sound.stop() }
    fun play(loop: Boolean = false, onPlayed: () -> Unit = {}, samples: () -> ShortArray) {
        stop()
        pending = scope.launch {
            try {
                val pcm = withContext(Dispatchers.Default) { samples() }
                ensureActive(); sound.play(pcm, loop); issue = null; onPlayed()
            } catch (e: CancellationException) { throw e }
            catch (_: Exception) { issue = "Could not play practice audio. Try again." }
        }
    }
    fun reset() {
        stop(); heard = false; explored = null
        round = PitchRound((if (count == 3) listOf(0, 1, 2, 0, 1, 2) else (0..7).toList()).shuffled())
    }
    DisposableEffect(lifecycle) {
        val observer = LifecycleEventObserver { _, event -> if (event == Lifecycle.Event.ON_STOP) stop() }
        lifecycle.lifecycle.addObserver(observer)
        onDispose { lifecycle.lifecycle.removeObserver(observer); stop() }
    }
    LaunchedEffect(sound.playing) { while (sound.playing) { time = sound.time; delay(30) } }
    Column(modifier.verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(20.dp)) {
        Text(if (rhythm) "Find your pulse" else "Hear Do, Re, Mi", style = MaterialTheme.typography.headlineLarge)
        issue?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        if (!rhythm) {
            Text("Start by listening, not singing. In this exercise Do is C. Re and Mi are the next two steps up.")
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                FilterChip(selected = !quiz, onClick = { quiz = false; reset() }, label = { Text("Learn") })
                FilterChip(selected = quiz, onClick = { quiz = true; reset() }, label = { Text("Quiz") })
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                listOf(3 to "Do Re Mi", 8 to "Full octave").forEach { (size, label) ->
                    FilterChip(selected = count == size, onClick = { count = size; reset() }, label = { Text(label) })
                }
            }
            if (quiz) {
            FlowRow(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = { play { BeginnerPractice.tone(0) } }) { Icon(Icons.Default.VolumeUp, null); Text("Hear Do") }
                Text("${round.correct} / ${round.answered} correct", style = MaterialTheme.typography.titleMedium)
            }
            Text("Question ${round.index + 1} of ${round.targets.size}")
            Button(onClick = { val target = round.target; play(onPlayed = { heard = true }) { BeginnerPractice.tone(target) } }, modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp)) {
                Icon(Icons.Default.PlayArrow, null); Spacer(Modifier.width(8.dp)); Text("Listen to the note")
            }
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                (0 until count).forEach { note ->
                    OutlinedButton(onClick = {
                        if (quiz) round = round.choose(note)
                        else play(onPlayed = { explored = note }) { BeginnerPractice.tone(note) }
                    }, enabled = !quiz || (heard && round.answer == null)) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(BeginnerPractice.syllables[note], style = MaterialTheme.typography.titleLarge)
                            Text("${note % 7 + 1} · ${BeginnerPractice.noteNames[note]}", style = MaterialTheme.typography.labelSmall)
                        }
                    }
                }
            }
            if (!quiz) explored?.let { note -> Text("${BeginnerPractice.syllables[note]} · ${BeginnerPractice.noteNames[note]} · ${"%.1f".format(java.util.Locale.ROOT, BeginnerPractice.frequency(note))} Hz", style = MaterialTheme.typography.titleMedium) }
            if (quiz) round.answer?.let { answer ->
                Text(if (answer == round.target) "Correct" else "That was ${BeginnerPractice.syllables[round.target]}", style = MaterialTheme.typography.titleLarge)
                Text("${BeginnerPractice.syllables[round.target]} is ${BeginnerPractice.noteNames[round.target]}. Replay and compare it with Do.")
                Button(onClick = { if (round.finished) reset() else { round = round.next(); heard = false; stop() } }) {
                    Text(if (round.finished) "Practice again" else "Next note")
                }
            }
            Text("Score counts your first answer to each listening question. It is not a singing or guitar grade.", style = MaterialTheme.typography.bodySmall)
        } else {
            Text("BPM means beats per minute. At 60 BPM each click is one second apart. Count 1, 2, 3, 4; the stronger click is 1.")
            Text("${bpm.roundToInt()} BPM", style = MaterialTheme.typography.headlineMedium)
            Slider(value = bpm, onValueChange = { stop(); bpm = it; taps = emptyList() }, valueRange = 40f..160f, steps = 23,
                modifier = Modifier.semantics { contentDescription = "Tempo in beats per minute" })
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Em / Am chord practice", Modifier.weight(1f))
                Switch(chords, { stop(); chords = it; taps = emptyList() },
                    modifier = Modifier.semantics { contentDescription = "Chord accompaniment" })
            }
            val beat = if (sound.playing) (time / (60 / bpm)).toInt() else -1
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                (0..3).forEach { index ->
                    Box(Modifier.weight(1f).height(64.dp).background(if (beat % 4 == index) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant), contentAlignment = Alignment.Center) {
                        Text("${index + 1}", style = MaterialTheme.typography.headlineMedium, color = if (beat % 4 == index) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurface)
                    }
                }
            }
            if (chords) {
                GuitarDiagram(if (beat < 4) "Em" else "Am")
                Text("Start with one gentle down-strum on beat 1. Hold for four clicks, then change chord. You do not need to sing.")
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Button(onClick = {
                    if (sound.playing) stop() else {
                        taps = emptyList(); lastTap = -1.0
                        val tempo = bpm.roundToInt(); val accompaniment = chords
                        play(true) { BeginnerPractice.metronome(tempo, accompaniment) }
                    }
                }) { Icon(if (sound.playing) Icons.Default.Stop else Icons.Default.PlayArrow, null); Text(if (sound.playing) "Stop" else "Start") }
                OutlinedButton(onClick = {
                    val now = sound.time
                    if (abs(now - lastTap) > .12) {
                        lastTap = now
                        val seconds = 60 / bpm
                        taps = (taps + abs(now - (now / seconds).roundToInt() * seconds) * 1000).takeLast(32)
                    }
                }, enabled = sound.playing) { Icon(Icons.Default.TouchApp, null); Text("Tap the beat") }
            }
            if (taps.isNotEmpty()) Text("${taps.size} taps · average offset ${taps.average().roundToInt()} ms", style = MaterialTheme.typography.titleMedium)
            Text("Tap timing uses the playback clock. Speaker and Bluetooth delay can affect it. Chords are synthesized references, not an analysis of your playing.", style = MaterialTheme.typography.bodySmall)
        }
    }
}
