package art.lazying.musia

import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import org.junit.Assert.*
import org.junit.Test

class ContractTest {
    private fun asset() = Asset("first-pulse", "Reference", "und", "https://musia.lazying.art/audio.wav", 22.0,
        bpm = 60.0, timeSignature = "4/4", confidence = Confidence("verified", "verified", "unavailable"),
        beats = (0..19).map { Beat(it.toDouble()) }, chords = listOf(Chord(4.0, 8.0, "Em"), Chord(8.0, 12.0, "Am")))
    private val lesson = Lesson("em-am-switch", "Em to Am", "play", "Em at 4s, Am at 8s, 60 BPM", "first-pulse", listOf("Let the chord ring"))

    @Test fun missingConfidenceDoesNotBecomeVerified() {
        val value = MusiaJson.decodeFromString<Asset>("""{"id":"en","label":"English","audioUrl":"/audio.mp3","duration":12} """)
        assertEquals("unavailable", value.confidence.chords)
        assertEquals("Unavailable", confidenceLabel("future-value"))
        assertEquals("Analysis - unverified", confidenceLabel("analysis"))
        assertEquals("Estimated - unverified", confidenceLabel("estimated"))
    }
    @Test fun nullMetadataAndUnknownBeatFieldsAreAccepted() {
        val value = MusiaJson.decodeFromString<Asset>("""{"id":"a","label":"a","language":"und","audioUrl":"/a.wav","duration":22,"bpm":null,"timeSignature":null,"beats":[{"time":0,"index":0}]}""")
        assertNull(value.bpm)
        assertNull(value.timeSignature)
        assertEquals(listOf(Beat(0.0)), value.beats)
    }
    @Test fun validationSortsAndDropsImpossibleEvents() {
        val data = asset().copy(beats = listOf(Beat(4.0), Beat(0.0), Beat(4.0), Beat(-1.0), Beat(Double.NaN), Beat(22.0)),
            phrases = listOf(Phrase("bad", 8.0, 4.0, "bad"), Phrase("ok", 4.0, 8.0, "Em")))
        val valid = Song(1, "first-pulse", "First Pulse", assets = listOf(data)).validated().assets.single()
        assertEquals(listOf(Beat(0.0), Beat(4.0)), valid.beats)
        assertEquals(listOf("ok"), valid.phrases.map { it.id })
    }
    @Test(expected = IllegalArgumentException::class) fun unknownVersionRejected() {
        Song(2, "x", "x", assets = listOf(asset())).validated()
    }
    @Test(expected = IllegalArgumentException::class) fun invalidDurationRejected() {
        Song(1, "x", "x", assets = listOf(asset().copy(duration = 0.0))).validated()
    }
    @Test fun firstPulseInstructionOnlyOnMatchingExercise() {
        assertEquals(lesson.body, practiceGuidance("first-pulse", PracticeMode.Play, listOf(lesson)).body)
        for (mode in PracticeMode.entries) {
            val guidance = practiceGuidance("aya-chan", mode, listOf(lesson))
            assertFalse(guidance.body.contains("60 BPM"))
            assertFalse(guidance.body.contains("Em at"))
            assertTrue(guidance.steps.isEmpty())
        }
        assertNotEquals(lesson.body, practiceGuidance("first-pulse", PracticeMode.Play, listOf(lesson.copy(exerciseId = "aya-chan"))).body)
    }
    @Test fun firstPulseCountInBarsAndTailStaySeparate() {
        assertEquals("Count-in", phaseLabel("first-pulse", asset(), 3999, true))
        assertEquals("Practice bar 1 / 4", phaseLabel("first-pulse", asset(), 4000, true))
        assertEquals("Practice bar 2 / 4", phaseLabel("first-pulse", asset(), 8000, true))
        assertEquals("Practice bar 4 / 4", phaseLabel("first-pulse", asset(), 19999, true))
        assertEquals("Final decay", phaseLabel("first-pulse", asset(), 20000, true))
        assertEquals("Paused", phaseLabel("first-pulse", asset(), 5000, false))
    }
    @Test fun songsNeverGetCountInBarsOrDownbeatClaims() {
        val song = asset().copy(confidence = Confidence("analysis", "analysis", "analysis"), beats = listOf(Beat(4.0), Beat(5.0)))
        assertEquals("Before first reference beat", phaseLabel("aya-chan", song, 3999, true))
        assertEquals("Detected pulses / Downbeat unverified", phaseLabel("aya-chan", song, 4000, true))
        assertEquals("After last reference beat", phaseLabel("aya-chan", song, 5001, true))
        assertEquals("No reference beats", phaseLabel("aya-chan", song.copy(beats = emptyList()), 5000, true))
    }
    @Test fun localExportRoundTripsWithoutRemoteAccount() {
        val data = LocalData(preferences = Preferences(.25f, PracticeMode.Tap, 25), sessions = listOf(PracticeSession("id", "song", "asset", "Title", 1000, PracticeMode.Tap, 1500, listOf(-20, 30))))
        assertEquals(data, MusiaJson.decodeFromString<LocalData>(MusiaJson.encodeToString(data)))
    }
    @Test fun relativeAndAbsoluteMediaUrlsStayHttps() {
        assertEquals("https://musia.lazying.art/audio.wav", MusiaApi.httpsUrl("/audio.wav"))
        assertEquals("https://fun.lazying.art/audio/a.mp3", MusiaApi.httpsUrl("https://fun.lazying.art/audio/a.mp3"))
    }
    @Test(expected = IllegalArgumentException::class) fun cleartextAudioRejected() { MusiaApi.httpsUrl("http://example.org/a.wav") }
    @Test(expected = IllegalArgumentException::class) fun urlCredentialsRejected() { MusiaApi.httpsUrl("https://user:secret@example.org/a.wav") }
}
