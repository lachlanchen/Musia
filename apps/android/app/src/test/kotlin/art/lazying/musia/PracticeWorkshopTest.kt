package art.lazying.musia

import org.junit.Assert.*
import org.junit.Test
import kotlin.math.*

class PracticeWorkshopTest {
    @Test fun workshopBoundsAndAudioClock() {
        val plan = PracticePlan(120, 3, 2, 2, PracticePattern.PICKING)
        assertEquals(6.0, plan.duration, .0001)
        assertEquals(listOf("C", "Am", "F", "G", "C"), (0..4).map { plan.chord(it * 1.5) })
        assertEquals(1, plan.beat(.5)); assertEquals(0, plan.beat(1.5))
        assertEquals(6 * 24000, plan.audio().size)
        val bounded = PracticePlan(0, 100, 0, -1)
        assertEquals(30, bounded.bpm); assertEquals(4, bounded.beats)
        assertNull(bounded.chord(Double.NaN))
    }
    @Test fun tempoAndFeedbackAcrossLoop() {
        val tempo = TapTempo()
        assertNull(tempo.tap(0.0)); assertNull(tempo.tap(.5)); assertNull(tempo.tap(1.0))
        assertEquals(120, tempo.tap(1.5)); assertNull(tempo.tap(1.51)); assertNull(tempo.tap(6.0))
        val feedback = RhythmFeedback()
        listOf(7.01, .01, 1.01, 2.01).forEachIndexed { i, time -> feedback.tap(time, 7.0 + i, 60) }
        feedback.tap(2.02, 10.01, 60)
        assertEquals(4, feedback.offsets.size)
        assertEquals(10.0, feedback.averageOffset, .0001)
        assertEquals(100, feedback.inTimePercent(60))
    }
    private fun signal(hz: Double, count: Int = 2048) = FloatArray(count) { i ->
        val t = i / 16000.0
        (.2 * sin(2 * PI * hz * t) + .08 * sin(4 * PI * hz * t)).toFloat()
    }
    @Test fun pitchReferencesAndAbstention() {
        listOf(82.4069, 130.8128, 261.6256, 440.0, 523.2511, 880.0).forEach { hz ->
            assertEquals(hz, PitchPractice.frequency(signal(hz)) ?: 0.0, hz * .005)
        }
        assertNull(PitchPractice.frequency(FloatArray(2048)))
        assertNull(PitchPractice.frequency(FloatArray(2048) { .3f }))
        assertNull(PitchPractice.frequency(FloatArray(2048) { Float.NaN }))
        val random = java.util.Random(42)
        assertNull(PitchPractice.frequency(FloatArray(2048) { (random.nextDouble() * .2 - .1).toFloat() }))
        val result = PitchPractice.analyze(signal(261.6256, 48000), 261.6256)
        assertEquals(100, result?.inTunePercent)
        assertEquals(0.0, result?.medianCents ?: 999.0, 3.0)
        assertEquals(0, PitchPractice.analyze(signal(293.6648, 48000), 261.6256)?.inTunePercent)
        assertNull(PitchPractice.analyze(signal(440.0, 4096), 440.0))
    }
}
