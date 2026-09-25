package art.lazying.musia

import org.junit.Assert.*
import org.junit.Test

class TimelineTest {
    private val chords = listOf(Chord(4.0, 8.0, "Em"), Chord(8.0, 12.0, "Am"), Chord(14.0, 16.0, "Em"))
    private fun chord(time: Double) = currentInterval(chords, time, { it.start }, { it.end })?.name

    @Test fun intervalsAreHalfOpen() {
        assertNull(chord(3.999))
        assertEquals("Em", chord(4.0))
        assertEquals("Em", chord(7.999))
        assertEquals("Am", chord(8.0))
        assertNull(chord(12.0))
        assertNull(chord(13.0))
        assertNull(chord(16.0))
    }
    @Test fun overlappingIntervalsPreferLatestStart() {
        val overlapping = listOf(Chord(0.0, 8.0, "Em"), Chord(4.0, 6.0, "Am"))
        assertEquals("Am", currentInterval(overlapping, 5.0, { it.start }, { it.end })?.name)
    }
    @Test fun invalidIntervalsRejected() {
        assertFalse(validInterval(-1.0, 2.0, 10.0))
        assertFalse(validInterval(2.0, 2.0, 10.0))
        assertFalse(validInterval(2.0, 12.0, 10.0))
        assertFalse(validInterval(Double.NaN, 2.0, 10.0))
        assertFalse(validInterval(0.0, Double.POSITIVE_INFINITY, 10.0))
    }
    @Test fun clipMapsRelativeAndAbsolutePositions() {
        val loop = LoopRange.from(4.0, 8.0, 22.0)!!
        assertEquals(4000L, loop.durationMs)
        assertEquals(0L, loop.relative(4000))
        assertEquals(1250L, loop.relative(5250))
        assertEquals(5250L, loop.absolute(1250))
        assertEquals(4000L, loop.absolute(0))
        assertEquals(4000L, loop.absolute(-12))
        assertEquals(8000L, loop.absolute(9000))
    }
    @Test fun seekClampsInsideExclusiveLoopEnd() {
        val loop = LoopRange(4000, 8000)
        assertEquals(0L, loop.relative(0))
        assertEquals(3999L, loop.relative(8000))
        assertEquals(3999L, loop.relative(12000))
    }
    @Test fun unusableLoopRejected() {
        assertNull(LoopRange.from(8.0, 4.0, 22.0))
        assertNull(LoopRange.from(0.0, .05, 22.0))
        assertNull(LoopRange.from(4.0, 23.0, 22.0))
        assertNull(LoopRange.from(Double.NaN, 8.0, 22.0))
        assertEquals(LoopRange(4000, 4100), LoopRange.from(4.0, 4.1, 22.0))
    }
    @Test fun beatLookupHasNoInventedLeadInBeat() {
        val beats = listOf(Beat(4.0), Beat(5.0), Beat(6.0))
        assertEquals(-1, beatIndex(beats, 3.99))
        assertEquals(0, beatIndex(beats, 4.0))
        assertEquals(1, beatIndex(beats, 5.1))
        assertEquals(-1, beatIndex(emptyList(), 5.0))
    }
    @Test fun tapConvertsToWallClockAtEverySpeed() {
        val beats = listOf(Beat(0.0), Beat(1.0), Beat(2.0))
        assertEquals(100L, tapOffsetMs(beats, 1100, 1f, 0))
        assertEquals(400L, tapOffsetMs(beats, 1100, .25f, 0))
        assertEquals(50L, tapOffsetMs(beats, 1100, 2f, 0))
        assertEquals(-200L, tapOffsetMs(beats, 900, .5f, 0))
    }
    @Test fun tapCalibrationIsSignedAndDoesNotChangeAudio() {
        assertEquals(50L, tapOffsetMs(listOf(Beat(0.0), Beat(1.0), Beat(2.0)), 1100, 1f, 50))
        assertEquals(150L, tapOffsetMs(listOf(Beat(0.0), Beat(1.0), Beat(2.0)), 1100, 1f, -50))
    }
    @Test fun noTapOutsideSuppliedBeats() {
        val beats = listOf(Beat(4.0), Beat(5.0), Beat(6.0))
        assertNull(tapOffsetMs(beats, 3999, 1f, 0))
        assertNull(tapOffsetMs(beats, 6001, 1f, 0))
        assertNull(tapOffsetMs(beats, 22000, 1f, 0))
        assertNull(tapOffsetMs(emptyList(), 0, 1f, 0))
        assertNull(tapOffsetMs(beats, 5000, 0f, 0))
        assertNull(tapOffsetMs(beats, 5000, Float.NaN, 0))
    }
    @Test fun loopTapUsesOnlyLoopBeatsAndAdjacentCycle() {
        val beats = (0..19).map { Beat(it.toDouble()) }
        assertEquals(-50L, tapOffsetMs(beats, 7950, 1f, 0, LoopRange(4000, 8000)))
        assertNull(tapOffsetMs(listOf(Beat(0.0), Beat(19.0)), 5000, 1f, 0, LoopRange(4000, 8000)))
    }
    @Test fun historyCountsActualPlayingTimeNotPausesOrMediaSeeks() {
        val clock = PlaybackClock()
        clock.sample(1000, true)
        clock.sample(1500, false)
        clock.sample(5000, true)
        clock.sample(5300, false)
        assertEquals(800L, clock.playedMs)
    }
}
