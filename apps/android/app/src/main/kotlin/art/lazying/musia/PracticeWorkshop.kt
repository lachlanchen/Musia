package art.lazying.musia

import kotlin.math.*

enum class PracticePattern(val label: String) { HOLD("Hold"), STRUM("Down-strum"), PICKING("Arpeggio") }

class PracticePlan(bpm: Int = 60, beats: Int = 4, subdivision: Int = 1, progression: Int = 0,
                   val pattern: PracticePattern = PracticePattern.HOLD) {
    val bpm = bpm.coerceIn(30, 240)
    val beats = if (beats in listOf(2, 3, 4, 6)) beats else 4
    val subdivision = subdivision.coerceIn(1, 3)
    val progression = progression.coerceIn(0, 2)
    val beatSeconds get() = 60.0 / bpm
    val bars get() = max(2, chordNames[progression].size)
    val duration get() = bars * beats * beatSeconds
    fun beat(time: Double) = if (!time.isFinite() || time < 0) 0 else ((time / beatSeconds) % beats).toInt()
    fun chord(time: Double): String? {
        val names = chordNames[progression]
        if (names.isEmpty() || !time.isFinite() || time < 0) return null
        return names[((time / (beatSeconds * beats)) % names.size).toInt()]
    }
    fun audio(): ShortArray = ShortArray((duration * BeginnerPractice.sampleRate).roundToInt()) { i ->
        val time = i.toDouble() / BeginnerPractice.sampleRate
        val tickSeconds = beatSeconds / subdivision
        val tick = (time / tickSeconds).toInt()
        val phase = time - tick * tickSeconds
        val downbeat = tick % (beats * subdivision) == 0
        val click = if (phase < .035) (if (downbeat) .26 else .14) * (1 - phase / .035).pow(3) * cos(2 * PI * (if (downbeat) 1400 else 1000) * phase) else 0.0
        var harmony = 0.0
        if (progression > 0) {
            val barSeconds = beatSeconds * beats
            val notes = pitches[progression][min(bars - 1, (time / barSeconds).toInt())]
            val interval = if (pattern == PracticePattern.HOLD) barSeconds else beatSeconds
            val t = time - floor(time / interval) * interval
            val envelope = min(1.0, t / .012) * min(1.0, (interval - t) / .04) * exp(-1.4 * t)
            val selected = if (pattern == PracticePattern.PICKING) listOf(notes[(time / beatSeconds).toInt() % notes.size]) else notes
            harmony = selected.sumOf { sin(2 * PI * 440 * 2.0.pow((it - 69) / 12.0) * t) } / selected.size * .2 * envelope
        }
        ((click + harmony).coerceIn(-1.0, 1.0) * 32767).roundToInt().toShort()
    }
    companion object {
        val progressions = listOf("Click only", "Em · Am", "C · Am · F · G")
        val chordNames = listOf(emptyList(), listOf("Em", "Am"), listOf("C", "Am", "F", "G"))
        private val pitches = listOf(emptyList(), listOf(listOf(52, 55, 59), listOf(45, 48, 52)),
            listOf(listOf(48, 52, 55), listOf(45, 48, 52), listOf(53, 57, 60), listOf(43, 47, 50)))
    }
}

class TapTempo {
    private val times = mutableListOf<Double>()
    fun tap(now: Double): Int? {
        if (!now.isFinite()) return null
        times.lastOrNull()?.let { last ->
            if (now <= last || now - last > 2.5) times.clear()
            else if (now - last < .18) return null
        }
        times.add(now); if (times.size > 9) times.removeAt(0)
        if (times.size < 4) return null
        val intervals = times.zipWithNext { a, b -> b - a }.sorted()
        return (60 / intervals[intervals.size / 2]).roundToInt().coerceIn(30, 240)
    }
}

class RhythmFeedback {
    private val history = mutableListOf<Double>()
    val offsets: List<Double> get() = history.toList()
    private var lastTap: Double? = null
    fun tap(playback: Double, monotonic: Double, bpm: Int) {
        if (!playback.isFinite() || playback < 0 || !monotonic.isFinite()) return
        if (lastTap != null && monotonic - lastTap!! < .12) return
        lastTap = monotonic
        val beat = 60.0 / bpm.coerceIn(30, 240)
        history.add((playback - floor(playback / beat + .5) * beat) * 1000)
        if (history.size > 32) history.removeAt(0)
    }
    val averageOffset get() = if (history.isEmpty()) 0.0 else history.map { abs(it) }.average()
    val bias get() = if (history.isEmpty()) 0.0 else history.average()
    fun inTimePercent(bpm: Int): Int? {
        if (history.size < 4) return null
        val tolerance = max(40.0, 60_000.0 / bpm.coerceIn(30, 240) * .08)
        return (100.0 * history.count { abs(it) <= tolerance } / history.size).roundToInt()
    }
}
