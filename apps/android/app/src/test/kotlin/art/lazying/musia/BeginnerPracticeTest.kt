package art.lazying.musia

import org.junit.Assert.*
import org.junit.Test
import kotlin.math.abs

class BeginnerPracticeTest {
    @Test fun pitchesUseEqualTemperamentAndAnOctave() {
        assertEquals(440.0, BeginnerPractice.frequency(5), .000001)
        assertEquals(261.625565, BeginnerPractice.frequency(0), .00001)
        assertEquals(BeginnerPractice.frequency(0) * 2, BeginnerPractice.frequency(7), .000001)
    }
    @Test fun answersCannotBeRepeatedForMorePoints() {
        var round = PitchRound(listOf(2, 0))
        assertEquals(round, round.next())
        round = round.choose(1).choose(2)
        assertEquals(0, round.correct)
        assertEquals(1, round.answered)
        round = round.next().choose(0)
        assertEquals(1, round.correct)
        assertTrue(round.finished)
        assertEquals(round, round.next())
    }
    @Test fun samplesHaveExactLengthsAndHeadroom() {
        assertEquals(24000, BeginnerPractice.tone(0).size)
        for (bpm in listOf(40, 60, 120, 160)) {
            val pcm = BeginnerPractice.metronome(bpm, true)
            assertEquals(8 * 60 * 24000 / bpm, pcm.size)
            assertTrue(pcm.maxOf { abs(it.toInt()) } in 1001..19999)
        }
    }
    @Test fun defaultLanguagesAndLegacyFallback() {
        val preferences = MusiaJson.decodeFromString<Preferences>("{}")
        assertEquals(setOf("en", "zh", "ja"), preferences.lyricLanguages)
        assertEquals("zh", lyricLanguageKey("zh-Hans"))
        val line = Lyric("l", 1.0, 2.0, "Rain")
        val asset = Asset("a", "a", "en", "https://example.org/audio", 5.0, lyrics = listOf(line))
        assertEquals(listOf(LyricTrack("en", listOf(line))), asset.displayLyricTracks)
        val revised = asset.copy(lyricTracks = listOf(LyricTrack("ja", listOf(line.copy(text = "雨"))), LyricTrack("en", listOf(line))))
        assertEquals(listOf("en", "ja"), revised.displayLyricTracks.map { it.language })
    }
}
