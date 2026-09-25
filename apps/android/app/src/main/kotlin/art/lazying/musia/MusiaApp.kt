@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class, androidx.compose.foundation.layout.ExperimentalLayoutApi::class)

package art.lazying.musia

import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.repeatOnLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import java.text.DateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.abs
import kotlin.math.roundToInt
import kotlinx.coroutines.delay

private data class Destination(val name: String, val icon: ImageVector)
private val destinations = listOf(
    Destination("Songs", Icons.Default.LibraryMusic),
    Destination("Practice", Icons.Default.School),
    Destination("History", Icons.Default.History),
    Destination("Settings", Icons.Default.Settings)
)

@Composable fun MusiaApp(vm: MusiaViewModel = viewModel()) {
    var destination by rememberSaveable { mutableStateOf("Songs") }
    var playerOpen by rememberSaveable { mutableStateOf(false) }
    val local by vm.store.data.collectAsStateWithLifecycle()
    val lifecycle = LocalLifecycleOwner.current
    val snackbar = remember { SnackbarHostState() }
    LaunchedEffect(lifecycle) {
        lifecycle.lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
            while (true) { vm.refreshPlayback(); delay(50) }
        }
    }
    LaunchedEffect(vm.notice) {
        vm.notice?.let { snackbar.showSnackbar(it); vm.clearNotice() }
    }
    BackHandler(playerOpen) { playerOpen = false }
    val open: (String) -> Unit = { vm.openSong(it); playerOpen = true }
    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(title = { Text(if (playerOpen) "Now playing" else "Musia", style = MaterialTheme.typography.headlineMedium) },
                navigationIcon = { if (playerOpen) IconAction("Back", Icons.AutoMirrored.Filled.ArrowBack) { playerOpen = false } },
                actions = { if (!playerOpen && destination in listOf("Songs", "Practice")) IconAction("Refresh", Icons.Default.Refresh) { vm.reloadLibrary(); if (destination == "Practice") vm.reloadLessons() } })
        },
        bottomBar = {
            Column {
                if (!playerOpen && vm.song.value != null) {
                    HorizontalDivider()
                    Row(Modifier.fillMaxWidth().clickable { playerOpen = true }.padding(start = 16.dp, end = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                        Cover(vm.song.value?.coverUrl, vm.song.value?.title.orEmpty(), Modifier.size(48.dp))
                        Column(Modifier.weight(1f).padding(12.dp)) {
                            Text(vm.song.value?.title.orEmpty(), maxLines = 1, overflow = TextOverflow.Ellipsis, style = MaterialTheme.typography.titleMedium)
                            Text(if (vm.playback.playing) "Playing" else "Paused", style = MaterialTheme.typography.bodySmall)
                        }
                        IconAction(if (vm.playback.playing) "Pause" else "Play", if (vm.playback.playing) Icons.Default.Pause else Icons.Default.PlayArrow, vm.playback.connected) { vm.togglePlayback() }
                    }
                }
                NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
                    destinations.forEach { item ->
                        NavigationBarItem(selected = destination == item.name, onClick = { destination = item.name; playerOpen = false },
                            icon = { Icon(item.icon, item.name) }, label = { Text(item.name, maxLines = 2) })
                    }
                }
            }
        },
        snackbarHost = { SnackbarHost(snackbar) }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.TopCenter) {
            val width = Modifier.widthIn(max = 880.dp).fillMaxWidth()
            when {
                playerOpen -> PlayerScreen(vm, local.preferences, width)
                destination == "Songs" -> LibraryScreen(vm, false, open, width)
                destination == "Practice" -> LibraryScreen(vm, true, open, width)
                destination == "History" -> HistoryScreen(local, vm.store.recoveryWarning, open, width)
                else -> SettingsScreen(vm, local, width)
            }
        }
    }
}

@Composable private fun LibraryScreen(vm: MusiaViewModel, exercises: Boolean, open: (String) -> Unit, modifier: Modifier) {
    var query by rememberSaveable(exercises) { mutableStateOf("") }
    val state = vm.library
    val entries = state.value?.items.orEmpty().filter { it.isExercise == exercises && (it.title.contains(query, true) || it.artist.contains(query, true)) }
        .sortedBy { if (it.id == "first-pulse") 0 else 1 }
    LazyColumn(modifier, contentPadding = PaddingValues(bottom = 24.dp)) {
        item {
            Column(Modifier.padding(horizontal = 20.dp, vertical = 12.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(if (exercises) "Exercises & lessons" else "Song library", style = MaterialTheme.typography.headlineLarge)
                OutlinedTextField(query, { query = it }, Modifier.fillMaxWidth(), singleLine = true,
                    label = { Text("Search") }, leadingIcon = { Icon(Icons.Default.Search, null) },
                    trailingIcon = { if (query.isNotEmpty()) IconAction("Clear search", Icons.Default.Close) { query = "" } })
                if (state.loading) LinearProgressIndicator(Modifier.fillMaxWidth())
                state.error?.let { ErrorNotice(it, state.value != null) { vm.reloadLibrary() } }
                if (state.value != null && entries.isEmpty()) Text(if (query.isNotEmpty()) "No matches" else if (exercises) "No exercises published" else "No songs published")
            }
        }
        items(entries, key = { it.id }) { entry ->
            ListItem(
                headlineContent = { Text(entry.title, style = MaterialTheme.typography.titleMedium) },
                supportingContent = { Text(listOf(entry.artist, timeLabel((entry.duration * 1000).toLong())).filter { it.isNotBlank() }.joinToString(" / ")) },
                leadingContent = { Cover(entry.coverUrl, entry.title, Modifier.size(64.dp).clip(RoundedCornerShape(6.dp))) },
                trailingContent = { Icon(Icons.Default.ChevronRight, null) },
                modifier = Modifier.clickable { open(entry.id) }
            )
            HorizontalDivider(Modifier.padding(horizontal = 20.dp), color = MaterialTheme.colorScheme.surfaceVariant)
        }
        if (exercises) {
            item {
                Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("Lessons", style = MaterialTheme.typography.titleLarge)
                    if (vm.lessons.loading) LinearProgressIndicator(Modifier.fillMaxWidth())
                    vm.lessons.error?.let { ErrorNotice(it, vm.lessons.value != null) { vm.reloadLessons() } }
                    if (vm.lessons.value?.lessons?.isEmpty() == true) Text("No lessons published")
                }
            }
            items(vm.lessons.value?.lessons.orEmpty()) { lesson ->
                var expanded by rememberSaveable(lesson.id) { mutableStateOf(false) }
                Column(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 8.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(Modifier.fillMaxWidth().clickable { expanded = !expanded }, verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(lesson.title, style = MaterialTheme.typography.titleMedium)
                            Text(lesson.focus, color = MaterialTheme.colorScheme.secondary)
                        }
                        IconAction(if (expanded) "Collapse lesson" else "Expand lesson", if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore) { expanded = !expanded }
                    }
                    if (expanded) {
                        Text(lesson.body, style = MaterialTheme.typography.bodyLarge)
                        lesson.steps.forEachIndexed { index, step -> Text("${index + 1}. $step") }
                        Button(onClick = { open(lesson.exerciseId) }) { Icon(Icons.Default.PlayArrow, null); Spacer(Modifier.width(8.dp)); Text("Start exercise") }
                    }
                    HorizontalDivider()
                }
            }
        }
    }
}

@Composable private fun PlayerScreen(vm: MusiaViewModel, preferences: Preferences, modifier: Modifier) {
    val song = vm.song.value
    val asset = vm.asset
    val playback = vm.playback
    if (song == null || asset == null) {
        Column(modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            if (vm.song.loading) LinearProgressIndicator(Modifier.fillMaxWidth())
            vm.song.error?.let { ErrorNotice(it) { vm.retrySong() } }
            if (!vm.song.loading && vm.song.error == null) Text("Select a song or exercise")
        }
        return
    }
    val time = playback.positionMs / 1000.0
    val lyric = currentInterval(asset.lyrics, time, { it.start }, { it.end })
    val chord = currentInterval(asset.chords, time, { it.start }, { it.end })
    val upcoming = asset.chords.firstOrNull { it.start > time }
    val note = currentInterval(asset.melody, time, { it.start }, { it.end })
    var assetMenu by remember { mutableStateOf(false) }
    LazyColumn(modifier, contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(20.dp)) {
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Cover(song.coverUrl, song.title, Modifier.size(88.dp).clip(RoundedCornerShape(8.dp)))
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(song.title, style = MaterialTheme.typography.titleLarge)
                    if (song.artist.isNotBlank()) Text(song.artist)
                    Text(listOfNotNull(asset.bpm?.takeIf { it.isFinite() && it > 0 }?.let { "${formatNumber(it)} BPM" }, asset.timeSignature).joinToString(" / "), style = MaterialTheme.typography.bodySmall)
                }
            }
        }
        item {
            Box {
                OutlinedButton(onClick = { assetMenu = true }, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Default.Translate, null); Spacer(Modifier.width(8.dp))
                    Text("${asset.label} (${asset.language})", Modifier.weight(1f)); Icon(Icons.Default.ExpandMore, null)
                }
                DropdownMenu(expanded = assetMenu, onDismissRequest = { assetMenu = false }) {
                    song.assets.forEach { candidate ->
                        DropdownMenuItem(text = { Text("${candidate.label} (${candidate.language})") },
                            leadingIcon = { if (candidate.id == asset.id) Icon(Icons.Default.Check, null) },
                            onClick = { vm.selectAsset(candidate.id); assetMenu = false })
                    }
                }
            }
        }
        item {
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                PracticeMode.entries.forEachIndexed { index, mode ->
                    SegmentedButton(selected = preferences.mode == mode, onClick = { vm.mode(mode) },
                        shape = SegmentedButtonDefaults.itemShape(index, 3), icon = {}) { Text(mode.name) }
                }
            }
        }
        item {
            Column(Modifier.fillMaxWidth().background(MaterialTheme.colorScheme.surfaceVariant).padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    ChordReadout("Current chord", chord?.name ?: "--", Modifier.weight(1f))
                    ChordReadout("Next chord", upcoming?.name ?: "--", Modifier.weight(1f), next = true)
                }
                Text("Chords: ${if (asset.chords.isEmpty()) "Unavailable" else confidenceLabel(asset.confidence.chords)}", style = MaterialTheme.typography.bodySmall)
                HorizontalDivider()
                if (lyric == null) Text(if (asset.lyrics.isEmpty()) "No timed lyrics" else "No lyric at this position", color = MaterialTheme.colorScheme.onSurfaceVariant)
                else {
                    val parts = remember(lyric) { lyricParts(lyric) }
                    val color = MaterialTheme.colorScheme.primary
                    Text(buildAnnotatedString {
                        parts.forEach { part ->
                            val active = part.token?.let { time >= it.start && time < it.end } == true
                            withStyle(SpanStyle(color = if (active) color else Color.Unspecified, fontWeight = if (active) FontWeight.Bold else FontWeight.Normal)) {
                                append(part.text)
                            }
                        }
                    }, style = MaterialTheme.typography.headlineMedium)
                    parts.firstOrNull { it.token?.let { token -> time >= token.start && time < token.end } == true }
                        ?.token?.reading?.takeIf { it.isNotBlank() }?.let { reading ->
                            Text(reading, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
                if (preferences.mode == PracticeMode.Play) {
                    Text("Melody: ${note?.let { listOf(it.note, it.numberNote, it.text).filter { part -> part.isNotBlank() }.joinToString(" / ") } ?: "--"}")
                    Text("Melody: ${if (asset.melody.isEmpty()) "Unavailable" else confidenceLabel(asset.confidence.melody)}", style = MaterialTheme.typography.bodySmall)
                    Text("Self-guided / No microphone", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.secondary)
                }
            }
        }
        if (preferences.mode == PracticeMode.Play) item { GuitarDiagram(chord?.name ?: upcoming?.name, upcoming = chord == null) }
        item { BeatPulse(song.id, asset, playback) }
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                if (playback.buffering) LinearProgressIndicator(Modifier.fillMaxWidth())
                playback.error?.let { ErrorNotice(it) { vm.retryPlayback() } }
                if (!playback.connected && playback.error == null) Text("Connecting to playback service")
                Transport(vm, asset)
                SpeedControl(preferences.speed, vm::speed)
            }
        }
        if (preferences.mode == PracticeMode.Tap) item {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Button(onClick = vm::tap, enabled = playback.playing && withinBeatRange(asset.beats, playback.positionMs) && asset.confidence.beats in setOf("verified", "analysis", "estimated"),
                    modifier = Modifier.fillMaxWidth().heightIn(min = 88.dp), shape = RoundedCornerShape(8.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary)) {
                    Icon(Icons.Default.TouchApp, null); Spacer(Modifier.width(12.dp)); Text("Tap", style = MaterialTheme.typography.titleLarge)
                }
                Text(vm.tapFeedback ?: "No tap yet", style = MaterialTheme.typography.titleMedium)
                Text("Local timing offset / Not an instrument or singing score", style = MaterialTheme.typography.bodySmall)
            }
        }
        item {
            val guidance = practiceGuidance(song.id, preferences.mode, vm.lessons.value?.lessons.orEmpty())
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(guidance.title, style = MaterialTheme.typography.titleLarge)
                Text(guidance.body)
                guidance.steps.forEachIndexed { index, step -> Text("${index + 1}. $step") }
                if (song.id == "first-pulse") vm.lessons.error?.let { ErrorNotice(it) { vm.reloadLessons() } }
            }
        }
        item {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Phrase loop", Modifier.weight(1f), style = MaterialTheme.typography.titleLarge)
                    if (playback.loop != null) IconAction("Clear loop", Icons.Default.RepeatOn, playback.connected) { vm.setLoop(null) }
                }
                playback.loop?.let { Text("A ${timeLabel(it.startMs)} / B ${timeLabel(it.endMs)}", color = MaterialTheme.colorScheme.primary) }
                if (asset.phrases.isEmpty()) Text("No timed phrases available")
            }
        }
        items(asset.phrases) { phrase ->
            val range = LoopRange.from(phrase.start, phrase.end, asset.duration)
            val selected = range != null && range == playback.loop
            ListItem(
                headlineContent = { Text(phrase.text.ifBlank { phrase.id }) },
                supportingContent = { Text("${timeLabel(secondsToMs(phrase.start))} - ${timeLabel(secondsToMs(phrase.end))}") },
                leadingContent = { RadioButton(selected, onClick = null, enabled = range != null && playback.connected) },
                colors = ListItemDefaults.colors(containerColor = if (selected) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surface),
                modifier = Modifier.clip(RoundedCornerShape(8.dp)).clickable(enabled = range != null && playback.connected) { vm.setLoop(if (selected) null else phrase) }
            )
        }
    }
}

@Composable private fun ChordReadout(label: String, value: String, modifier: Modifier, next: Boolean = false) {
    Column(modifier, verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(label, style = MaterialTheme.typography.bodySmall)
        Text(value, style = MaterialTheme.typography.headlineLarge, color = if (next) MaterialTheme.colorScheme.secondary else MaterialTheme.colorScheme.primary)
    }
}

@Composable private fun BeatPulse(songId: String, asset: Asset, playback: PlaybackState) {
    val time = playback.positionMs / 1000.0
    val index = beatIndex(asset.beats, time)
    val beat = asset.beats.getOrNull(index)
    val pulse = playback.playing && withinBeatRange(asset.beats, playback.positionMs) && beat != null && time - beat.time < .18
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(48.dp).clip(RoundedCornerShape(8.dp)).background(if (pulse) MaterialTheme.colorScheme.secondaryContainer else MaterialTheme.colorScheme.surfaceVariant), contentAlignment = Alignment.Center) {
            Icon(Icons.Default.GraphicEq, null, tint = if (pulse) MaterialTheme.colorScheme.secondary else MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Column(Modifier.weight(1f)) {
            Text(phaseLabel(songId, asset, playback.positionMs, playback.playing), style = MaterialTheme.typography.titleMedium)
            Text("Beats: ${if (asset.beats.isEmpty()) "Unavailable" else confidenceLabel(asset.confidence.beats)}", style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable private fun Transport(vm: MusiaViewModel, asset: Asset) {
    val state = vm.playback
    val lower = state.loop?.startMs ?: 0L
    val upper = state.loop?.endMs ?: secondsToMs(asset.duration)
    var drag by remember(asset.id, state.loop) { mutableStateOf<Float?>(null) }
    Column {
        Slider(value = drag ?: state.positionMs.toFloat().coerceIn(lower.toFloat(), upper.toFloat()), onValueChange = { drag = it },
            onValueChangeFinished = { drag?.let { vm.seek(it.toLong()) }; drag = null }, valueRange = lower.toFloat()..upper.toFloat(),
            enabled = state.connected, modifier = Modifier.semantics { contentDescription = "Playback position" })
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(timeLabel((drag ?: state.positionMs.toFloat()).toLong()), style = MaterialTheme.typography.bodySmall)
            Text(timeLabel(upper), style = MaterialTheme.typography.bodySmall)
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically) {
            IconAction("Back 5 seconds", Icons.Default.Replay5, state.connected) { vm.seek(state.positionMs - 5000) }
            FilledIconButton(onClick = vm::togglePlayback, enabled = state.connected, modifier = Modifier.padding(horizontal = 24.dp).size(72.dp)) {
                Icon(if (state.playing || state.buffering) Icons.Default.Pause else Icons.Default.PlayArrow,
                    if (state.playing || state.buffering) "Pause" else "Play", Modifier.size(40.dp))
            }
            IconAction("Forward 5 seconds", Icons.Default.Forward5, state.connected) { vm.seek(state.positionMs + 5000) }
        }
    }
}

@Composable private fun SpeedControl(speed: Float, change: (Float) -> Unit) {
    var draft by remember(speed) { mutableFloatStateOf(speed) }
    Column {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text("Speed ${String.format(Locale.ROOT, "%.2f", draft)}x", style = MaterialTheme.typography.titleMedium)
            IconAction("Reset speed", Icons.Default.Restore) { change(1f) }
        }
        Slider(draft, { draft = it }, onValueChangeFinished = { change(draft) }, valueRange = .25f..2f, steps = 34,
            modifier = Modifier.semantics { contentDescription = "Playback speed, pitch preserved" })
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) { Text("0.25x"); Text("2.00x") }
    }
}

@Composable private fun HistoryScreen(local: LocalData, warning: String?, open: (String) -> Unit, modifier: Modifier) {
    LazyColumn(modifier, contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        item {
            Text("Your sessions", style = MaterialTheme.typography.headlineLarge)
            Text("On this device", color = MaterialTheme.colorScheme.onSurfaceVariant)
            if (warning != null) Text(warning, color = MaterialTheme.colorScheme.error)
            if (local.sessions.isEmpty()) Text("No sessions yet", Modifier.padding(top = 24.dp))
        }
        items(local.sessions, key = { it.id }) { session ->
            Column(Modifier.fillMaxWidth().clickable { open(session.songId) }.padding(vertical = 8.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(session.title, style = MaterialTheme.typography.titleMedium)
                Text(DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.SHORT).format(Date(session.startedAt)), style = MaterialTheme.typography.bodySmall)
                Text("${session.mode.name} / ${timeLabel(session.playedMs)} played")
                if (session.tapOffsetsMs.isNotEmpty()) Text("${session.tapOffsetsMs.size} taps / ${session.tapOffsetsMs.map { abs(it) }.average().roundToInt()} ms mean absolute offset", style = MaterialTheme.typography.bodySmall)
                HorizontalDivider(Modifier.padding(top = 8.dp))
            }
        }
    }
}

@Composable private fun SettingsScreen(vm: MusiaViewModel, local: LocalData, modifier: Modifier) {
    var resetDialog by remember { mutableStateOf(false) }
    var calibration by remember(local.preferences.tapCalibrationMs) { mutableFloatStateOf(local.preferences.tapCalibrationMs.toFloat()) }
    val export = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { it?.let(vm::export) }
    val links = LocalUriHandler.current
    LazyColumn(modifier, contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(20.dp)) {
        item { Text("Settings", style = MaterialTheme.typography.headlineLarge) }
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Tap calibration", style = MaterialTheme.typography.titleLarge)
                Text("${calibration.roundToInt()} ms", style = MaterialTheme.typography.titleMedium)
                Slider(calibration, { calibration = it }, onValueChangeFinished = { vm.calibration(calibration.roundToInt()) }, valueRange = -300f..300f, steps = 59,
                    modifier = Modifier.semantics { contentDescription = "Tap offset calibration" })
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) { Text("-300 ms"); Text("+300 ms") }
            }
        }
        item {
            HorizontalDivider()
            Text("Local data", Modifier.padding(top = 20.dp), style = MaterialTheme.typography.titleLarge)
            vm.store.recoveryWarning?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedButton(onClick = { export.launch("musia-history.json") }) { Icon(Icons.Default.FileDownload, null); Spacer(Modifier.width(8.dp)); Text("Export") }
                OutlinedButton(onClick = { resetDialog = true }) { Icon(Icons.Default.DeleteOutline, null); Spacer(Modifier.width(8.dp)); Text("Reset") }
            }
        }
        item {
            HorizontalDivider()
            Text("Service", Modifier.padding(top = 20.dp), style = MaterialTheme.typography.titleLarge)
            Text("musia.lazying.art")
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(vm.health, Modifier.weight(1f))
                IconAction("Check service health", Icons.Default.Refresh, vm.health != "Checking") { vm.checkHealth() }
            }
        }
        item {
            HorizontalDivider()
            Column(Modifier.padding(top = 20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Privacy", style = MaterialTheme.typography.titleLarge)
                Text("No account. No microphone. No advertising or analytics SDK.")
                Text("Preferences and up to 200 recent sessions stay on this device. Android cloud backup is disabled. Reset stops playback and clears local records. Exports remain in the destination you choose.")
                Text("Library, lessons, covers and audio are requested over HTTPS. Musia and media hosts receive your IP address and ordinary request metadata. Practice history and taps are not uploaded.")
                Text("Tap offsets compare touch timing with the supplied beat timeline. Bluetooth, device latency and unverified timelines affect them. Positive calibration subtracts from a late offset. No singing or guitar accuracy is assessed.")
                Text("Musia 0.1.0", style = MaterialTheme.typography.bodySmall)
                FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    TextButton(onClick = { links.openUri("https://musia.lazying.art/privacy") }) { Icon(Icons.Default.PrivacyTip, null); Spacer(Modifier.width(8.dp)); Text("Privacy policy") }
                    TextButton(onClick = { links.openUri("https://musia.lazying.art/support") }) { Icon(Icons.Default.HelpOutline, null); Spacer(Modifier.width(8.dp)); Text("Support") }
                }
            }
        }
    }
    if (resetDialog) AlertDialog(onDismissRequest = { resetDialog = false }, title = { Text("Reset local data?") },
        text = { Text("Playback will stop. This removes history and preferences from this device. Existing exports are not deleted.") },
        confirmButton = { TextButton(onClick = { vm.reset(); resetDialog = false }) { Text("Reset") } },
        dismissButton = { TextButton(onClick = { resetDialog = false }) { Text("Cancel") } })
}

@Composable private fun ErrorNotice(message: String, retained: Boolean = false, retry: () -> Unit) {
    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Icon(Icons.Default.CloudOff, null, tint = MaterialTheme.colorScheme.error)
            Text(message, Modifier.weight(1f), color = MaterialTheme.colorScheme.error)
        }
        if (retained) Text("Showing the last loaded response", style = MaterialTheme.typography.bodySmall)
        OutlinedButton(onClick = retry) { Icon(Icons.Default.Refresh, null); Spacer(Modifier.width(8.dp)); Text("Retry") }
    }
}

@Composable private fun IconAction(label: String, icon: ImageVector, enabled: Boolean = true, click: () -> Unit) {
    TooltipBox(positionProvider = TooltipDefaults.rememberPlainTooltipPositionProvider(), tooltip = { PlainTooltip { Text(label) } }, state = rememberTooltipState()) {
        IconButton(onClick = click, enabled = enabled, modifier = Modifier.size(48.dp)) { Icon(icon, label) }
    }
}

private fun timeLabel(ms: Long): String {
    val total = (ms / 1000).coerceAtLeast(0)
    return String.format(Locale.ROOT, "%d:%02d", total / 60, total % 60)
}
private fun formatNumber(value: Double): String = if (value % 1.0 == 0.0) value.toInt().toString() else String.format(Locale.ROOT, "%.1f", value)
