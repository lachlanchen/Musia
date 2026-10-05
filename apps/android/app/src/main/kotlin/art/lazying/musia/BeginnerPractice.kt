package art.lazying.musia

import kotlin.math.*

object BeginnerPractice {
    val syllables = listOf("Do", "Re", "Mi", "Fa", "Sol", "La", "Ti", "Do ↑")
    val noteNames = listOf("C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5")
    val midi = listOf(60, 62, 64, 65, 67, 69, 71, 72)
    const val sampleRate = 24000
    fun frequency(index: Int): Double = 440.0 * 2.0.pow((midi[index.coerceIn(0, 7)] - 69) / 12.0)
    fun tone(index: Int): ShortArray = ShortArray(sampleRate) { frame ->
        val time = frame.toDouble() / sampleRate
        val envelope = min(1.0, time / .02) * min(1.0, (1 - time) / .08)
        (0.24 * envelope * sin(2 * PI * frequency(index) * time) * 32767).roundToInt().toShort()
    }
    fun metronome(bpm: Int, chords: Boolean): ShortArray {
        val beatSeconds = 60.0 / bpm.coerceIn(40, 160)
        val notes = listOf(listOf(52, 55, 59), listOf(45, 48, 52))
        return ShortArray((beatSeconds * 8 * sampleRate).roundToInt()) { frame ->
            val time = frame.toDouble() / sampleRate
            val beat = (time / beatSeconds).toInt()
            val phase = time - beat * beatSeconds
            val click = if (phase < .045) .26 * (1 - phase / .045).pow(3) * cos(2 * PI * (if (beat % 4 == 0) 1400 else 1000) * phase) else 0.0
            val barPhase = time % (beatSeconds * 4)
            val envelope = min(1.0, barPhase / .015) * min(1.0, (beatSeconds * 4 - barPhase) / .04) * exp(-.7 * barPhase)
            val harmony = if (!chords) 0.0 else notes[(beat / 4).coerceAtMost(1)].sumOf {
                sin(2 * PI * 440 * 2.0.pow((it - 69) / 12.0) * barPhase)
            } / 3 * .2 * envelope
            ((click + harmony).coerceIn(-1.0, 1.0) * 32767).roundToInt().toShort()
        }
    }
}

data class PitchRound(val targets: List<Int>, val index: Int = 0, val correct: Int = 0, val answer: Int? = null) {
    init { require(targets.isNotEmpty() && targets.all { it in 0..7 }) }
    val target get() = targets[index]
    val answered get() = index + if (answer == null) 0 else 1
    val finished get() = index == targets.lastIndex && answer != null
    fun choose(note: Int): PitchRound = if (answer != null || note !in 0..7) this else copy(answer = note, correct = correct + if (note == target) 1 else 0)
    fun next(): PitchRound = if (answer == null || finished) this else copy(index = index + 1, answer = null)
}
