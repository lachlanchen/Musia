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

@Composable fun BeginnerPracticeScreen(rhythm: Boolean, modifier: Modifier = Modifier, initialProgression: Int = 0) {
    val context = LocalContext.current
    val sound = remember { PracticeAudio(context.applicationContext) }
    val scope = rememberCoroutineScope()
    val lifecycle = LocalLifecycleOwner.current
    var count by remember { mutableIntStateOf(3) }
    var pitchMode by remember { mutableIntStateOf(0) }
    val quiz = pitchMode == 1
    var explored by remember { mutableStateOf<Int?>(null) }
    var round by remember { mutableStateOf(PitchRound(listOf(0, 1, 2, 0, 1, 2).shuffled())) }
    var heard by remember { mutableStateOf(false) }
    var bpm by remember { mutableFloatStateOf(60f) }
    var beats by remember { mutableIntStateOf(4) }
    var subdivision by remember { mutableIntStateOf(1) }
    var progression by remember { mutableIntStateOf(initialProgression) }
    var pattern by remember { mutableStateOf(PracticePattern.HOLD) }
    val tempoTap = remember { TapTempo() }
    var feedback by remember { mutableStateOf(RhythmFeedback()) }
    var feedbackRevision by remember { mutableIntStateOf(0) }
    var time by remember { mutableDoubleStateOf(0.0) }
    var issue by remember { mutableStateOf<String?>(null) }
    var pending by remember { mutableStateOf<Job?>(null) }
    fun stop() { pending?.cancel(); pending = null; sound.stop() }
    fun resetRhythm() { stop(); feedback = RhythmFeedback(); feedbackRevision++ }
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
        Text(if (rhythm) "First Pulse" else "Hear Do, Re, Mi", style = MaterialTheme.typography.headlineLarge)
        issue?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        if (!rhythm) {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                listOf("Listen", "Recognize", "Sing").forEachIndexed { i, label ->
                    FilterChip(selected = pitchMode == i, onClick = { pitchMode = i; reset() }, label = { Text(label) })
                }
            }
            if (pitchMode == 2) {
                PitchMatchPanel(sound.playing, { stop() }) { note, lower -> play { BeginnerPractice.tone(note, lower) } }
            } else {
            Text("In this exercise Do is C. Re and Mi are the next two steps up.")
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
            }
        } else {
            val plan = PracticePlan(bpm.roundToInt(), beats, subdivision, progression, pattern)
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("${bpm.roundToInt()} BPM", Modifier.weight(1f), style = MaterialTheme.typography.headlineLarge)
                IconButton(onClick = { resetRhythm(); bpm = (bpm - 1).coerceAtLeast(30f) }) { Icon(Icons.Default.Remove, "Slower") }
                IconButton(onClick = { resetRhythm(); bpm = (bpm + 1).coerceAtMost(240f) }) { Icon(Icons.Default.Add, "Faster") }
            }
            Slider(value = bpm, onValueChange = { resetRhythm(); bpm = it.roundToInt().toFloat() }, valueRange = 30f..240f, steps = 209,
                modifier = Modifier.semantics { contentDescription = "Tempo in beats per minute" })
            OutlinedButton(onClick = {
                resetRhythm()
                tempoTap.tap(android.os.SystemClock.elapsedRealtime() / 1000.0)?.let { bpm = it.toFloat() }
            }) { Icon(Icons.Default.TouchApp, null); Text("Tap tempo") }
            Text("Beats per bar", style = MaterialTheme.typography.titleMedium)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf(2, 3, 4, 6).forEach { n -> FilterChip(beats == n, { resetRhythm(); beats = n }, label = { Text("$n/4") }) }
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("Beat", "Eighths", "Triplets").forEachIndexed { i, label ->
                    FilterChip(subdivision == i + 1, { resetRhythm(); subdivision = i + 1 }, label = { Text(label) })
                }
            }
            Text("Progression", style = MaterialTheme.typography.titleMedium)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                PracticePlan.progressions.forEachIndexed { i, label ->
                    FilterChip(progression == i, { resetRhythm(); progression = i }, label = { Text(label) })
                }
            }
            if (progression > 0) FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                PracticePattern.entries.forEach { p -> FilterChip(pattern == p, { resetRhythm(); pattern = p }, label = { Text(p.label) }) }
            }
            val beat = if (sound.playing) plan.beat(time) else -1
            (0 until beats).toList().chunked(if (beats > 4) 3 else beats).forEach { row ->
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    row.forEach { index ->
                        Box(Modifier.weight(1f).height(60.dp).background(if (beat == index) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant), contentAlignment = Alignment.Center) {
                            Text("${index + 1}", style = MaterialTheme.typography.headlineMedium, color = if (beat == index) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurface)
                        }
                    }
                }
            }
            plan.chord(if (sound.playing) time else 0.0)?.let { chord ->
                GuitarDiagram(chord)
                Text(when (pattern) {
                    PracticePattern.HOLD -> "Strum once on 1. Let it ring, prepare the next shape, then change on the next 1."
                    PracticePattern.STRUM -> "One relaxed down-strum per beat. Keep the pulse moving while you change shape."
                    PracticePattern.PICKING -> "Listen to the chord tones one at a time. Pick slowly and evenly; the reference is synthesized, not a recording of guitar strings."
                })
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Button(onClick = {
                    if (sound.playing || pending?.isActive == true) stop() else {
                        feedback = RhythmFeedback(); feedbackRevision++
                        play(true) { plan.audio() }
                    }
                }) { Icon(if (sound.playing) Icons.Default.Stop else Icons.Default.PlayArrow, null); Text(if (sound.playing) "Stop" else if (pending?.isActive == true) "Preparing" else "Start") }
                OutlinedButton(onClick = {
                    feedback.tap(sound.time, android.os.SystemClock.elapsedRealtime() / 1000.0, bpm.roundToInt())
                    feedbackRevision++
                }, enabled = sound.playing) { Icon(Icons.Default.TouchApp, null); Text("Tap the beat") }
            }
            if (feedbackRevision >= 0 && feedback.offsets.isNotEmpty()) {
                Text("${feedback.offsets.size} taps · average offset ${feedback.averageOffset.roundToInt()} ms", style = MaterialTheme.typography.titleMedium)
                feedback.inTimePercent(bpm.roundToInt())?.let { score ->
                    Text("$score% within the timing window", style = MaterialTheme.typography.headlineSmall, color = MaterialTheme.colorScheme.primary)
                    Text(if (abs(feedback.bias) < 25) "Your taps are centered on the beat. Keep the motion relaxed."
                    else if (feedback.bias > 0) "Mostly after the click. Prepare your next tap a little sooner."
                    else "Mostly before the click. Listen for the click and ease back slightly.")
                }
            }
            Text("BPM is beats per minute; 60 BPM is one beat per second. Tap feedback uses a window of 8% of a beat, at least 40 ms. Bluetooth and touch latency can affect the result. This is tap timing, not a guitar performance grade.", style = MaterialTheme.typography.bodySmall)
        }
    }
}
