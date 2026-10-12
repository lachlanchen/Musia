@file:OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)
package art.lazying.musia

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.media.*
import android.os.SystemClock
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import kotlinx.coroutines.*
import kotlin.math.*

@SuppressLint("MissingPermission") // Permission is checked immediately before the explicit three-second capture.
@Composable fun PitchMatchPanel(referencePlaying: Boolean, stopReference: () -> Unit, listen: (Int, Boolean) -> Unit) {
    val context = LocalContext.current
    val lifecycle = LocalLifecycleOwner.current
    val scope = rememberCoroutineScope()
    var note by remember { mutableIntStateOf(0) }
    var lower by remember { mutableStateOf(true) }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf<String?>(null) }
    var result by remember { mutableStateOf<PitchResult?>(null) }
    var job by remember { mutableStateOf<Job?>(null) }
    var attempt by remember { mutableIntStateOf(0) }
    fun cancel() { attempt++; job?.cancel(); job = null; busy = false; message = null }
    fun start() {
        cancel(); stopReference(); result = null
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            message = "Microphone access is off. Listening practice still works; enable the microphone in system settings to match your voice."
            return
        }
        val target = BeginnerPractice.frequency(note) / if (lower) 2 else 1
        val currentAttempt = attempt
        busy = true; message = "Preparing microphone..."
        job = scope.launch {
            val manager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
            val focus = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_EXCLUSIVE)
                .setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build())
                .setOnAudioFocusChangeListener { if (it < 0) cancel() }.build()
            try {
                check(manager.requestAudioFocus(focus) == AudioManager.AUDIOFOCUS_REQUEST_GRANTED)
                delay(400)
                message = "Sing or hum one comfortable note..."
                val samples = withContext(Dispatchers.IO) {
                    val rate = PitchPractice.sampleRate
                    val minBuffer = AudioRecord.getMinBufferSize(rate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
                    check(minBuffer > 0)
                    val recorder = AudioRecord.Builder().setAudioSource(MediaRecorder.AudioSource.VOICE_RECOGNITION)
                        .setAudioFormat(AudioFormat.Builder().setSampleRate(rate).setChannelMask(AudioFormat.CHANNEL_IN_MONO).setEncoding(AudioFormat.ENCODING_PCM_16BIT).build())
                        .setBufferSizeInBytes(max(minBuffer, 8192)).build()
                    try {
                        check(recorder.state == AudioRecord.STATE_INITIALIZED)
                        recorder.startRecording()
                        val pcm = ShortArray(rate * 3)
                        var read = 0
                        val end = SystemClock.elapsedRealtime() + 3500
                        while (read < pcm.size && SystemClock.elapsedRealtime() < end) {
                            ensureActive()
                            val size = recorder.read(pcm, read, min(1024, pcm.size - read), AudioRecord.READ_NON_BLOCKING)
                            check(size >= 0)
                            if (size == 0) delay(10) else read += size
                        }
                        FloatArray(read) { pcm[it] / 32768f }
                    } finally { recorder.release() }
                }
                ensureActive(); message = "Measuring pitch..."
                result = withContext(Dispatchers.Default) { PitchPractice.analyze(samples, target) }
                message = if (result == null) "Not enough clear, steady voice to score. Try a quiet room, a comfortable pitch, and a gentle hum." else null
            } catch (e: CancellationException) { throw e }
            catch (_: Exception) { message = "Could not measure this take. Check the microphone and try again." }
            finally { manager.abandonAudioFocusRequest(focus); if (currentAttempt == attempt) busy = false }
        }
    }
    val permission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) start() else message = "Microphone access is off. Listening practice still works."
    }
    DisposableEffect(lifecycle) {
        val observer = LifecycleEventObserver { _, event -> if (event == Lifecycle.Event.ON_STOP) cancel() }
        lifecycle.lifecycle.addObserver(observer)
        onDispose { lifecycle.lifecycle.removeObserver(observer); cancel() }
    }
    LaunchedEffect(referencePlaying) { if (referencePlaying) cancel() }
    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("Match a note", style = MaterialTheme.typography.headlineSmall)
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            BeginnerPractice.syllables.forEachIndexed { i, label ->
                FilterChip(note == i, { cancel(); stopReference(); result = null; note = i }, label = { Text(label) }, enabled = !busy)
            }
        }
        Row {
            Text("Lower octave", Modifier.weight(1f))
            Switch(lower, { cancel(); stopReference(); result = null; lower = it }, enabled = !busy)
        }
        Text("Listen, let the tone stop, then hum or sing gently. Choose a comfortable octave; do not strain.")
        FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedButton(onClick = { cancel(); listen(note, lower) }) { Icon(Icons.Default.VolumeUp, null); Text("Listen") }
            Button(onClick = {
                if (busy) cancel()
                else if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) start()
                else { stopReference(); permission.launch(Manifest.permission.RECORD_AUDIO) }
            }) { Icon(if (busy) Icons.Default.Stop else Icons.Default.Mic, null); Text(if (busy) "Stop" else "Sing · 3 seconds") }
        }
        message?.let { Text(it) }
        result?.let {
            Text("${it.inTunePercent}% within half a semitone", style = MaterialTheme.typography.headlineSmall, color = MaterialTheme.colorScheme.primary)
            Text("${"%.1f".format(java.util.Locale.ROOT, it.voicedSeconds)} seconds of clear pitch · ${it.medianCents.roundToInt()} cents from target")
            Text(if (abs(it.medianCents) <= 50) "You found the note. Repeat gently, then try the next step."
                else if (it.medianCents > 0) "Your note is higher. Listen again and glide down gently."
                else "Your note is lower. Listen again and glide up gently.")
        }
        Text("On-device pitch estimate, not a singing-quality grade. One voice only; no backing music. A semitone is 100 cents. The three-second take stays in memory and is never saved or uploaded.", style = MaterialTheme.typography.bodySmall)
    }
}
