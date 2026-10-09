package art.lazying.musia

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

val MusiaJson = Json { ignoreUnknownKeys = true; encodeDefaults = true }
data class LoadState<T>(val value: T? = null, val loading: Boolean = false, val error: String? = null)

@Serializable data class Library(val version: Int, val items: List<LibraryItem>)
@Serializable data class LibraryItem(
    val id: String, val title: String, val artist: String = "",
    val coverUrl: String? = null, val duration: Double = 0.0, val kind: String = "song"
) { val isExercise: Boolean get() = kind.equals("exercise", true) }

@Serializable data class Song(
    val version: Int, val id: String, val title: String, val artist: String = "",
    val coverUrl: String? = null, val assets: List<Asset>, val defaultAssetId: String? = null
)
@Serializable data class Confidence(
    val beats: String = "unavailable", val chords: String = "unavailable",
    val melody: String = "unavailable"
)
@Serializable data class Asset(
    val id: String, val label: String, val language: String = "und",
    val audioUrl: String, val duration: Double, val bpm: Double? = null,
    val timeSignature: String? = null, val confidence: Confidence = Confidence(),
    val beats: List<Beat> = emptyList(), val chords: List<Chord> = emptyList(),
    val lyrics: List<Lyric> = emptyList(), val phrases: List<Phrase> = emptyList(),
    val melody: List<Melody> = emptyList(), val lyricTracks: List<LyricTrack> = emptyList()
) {
    val displayLyricTracks: List<LyricTrack> get() = lyricTracks.filter { it.lines.isNotEmpty() }
        .ifEmpty { if (lyrics.isEmpty()) emptyList() else listOf(LyricTrack(language, lyrics)) }
        .sortedBy { lyricLanguageRank(it.language) }
}
@Serializable data class LyricTrack(val language: String, val lines: List<Lyric>)
@Serializable data class Beat(val time: Double)
@Serializable data class Chord(val start: Double, val end: Double, val name: String, val confidence: Double? = null)
@Serializable data class Token(val text: String, val start: Double, val end: Double, val reading: String? = null)
@Serializable data class Lyric(val id: String, val start: Double, val end: Double, val text: String, val tokens: List<Token> = emptyList())
@Serializable data class Phrase(val id: String, val start: Double, val end: Double, val text: String)
@Serializable data class Melody(val start: Double, val end: Double, val note: String, val numberNote: String = "", val text: String = "")
@Serializable data class Lessons(val lessons: List<Lesson>)
@Serializable data class Lesson(val id: String, val title: String, val focus: String, val body: String, val exerciseId: String, val steps: List<String> = emptyList())

fun confidenceLabel(value: String): String = when (value) {
    "verified" -> "Verified"
    "analysis" -> "Analysis - unverified"
    "estimated" -> "Estimated - unverified"
    else -> "Unavailable"
}

fun Song.validated(): Song {
    require(version == 1) { "Unsupported song API version" }
    require(id.isNotBlank() && title.isNotBlank()) { "Song identity is missing" }
    require(assets.isNotEmpty() && assets.map { it.id }.distinct().size == assets.size) { "No unique audio assets" }
    return copy(assets = assets.map { asset ->
        require(asset.id.isNotBlank() && asset.audioUrl.isNotBlank()) { "Audio asset is incomplete" }
        require(asset.duration.isFinite() && asset.duration > 0 && asset.duration <= 86400) { "Invalid audio duration" }
        fun valid(start: Double, end: Double) = validInterval(start, end, asset.duration)
        fun cleanLyrics(lines: List<Lyric>) = lines.filter { valid(it.start, it.end) }.distinctBy { it.id }.sortedBy { it.start }.map { line ->
            line.copy(tokens = line.tokens.filter { valid(it.start, it.end) && it.start >= line.start && it.end <= line.end }.sortedBy { it.start })
        }
        asset.copy(
            beats = asset.beats.filter { it.time.isFinite() && it.time >= 0 && it.time < asset.duration }.distinctBy { it.time }.sortedBy { it.time },
            chords = asset.chords.filter { valid(it.start, it.end) && it.name.isNotBlank() }.sortedBy { it.start },
            lyrics = cleanLyrics(asset.lyrics),
            lyricTracks = asset.lyricTracks.filter { it.language.isNotBlank() }.distinctBy { it.language }
                .map { it.copy(lines = cleanLyrics(it.lines)) },
            phrases = asset.phrases.filter { valid(it.start, it.end) }.sortedBy { it.start },
            melody = asset.melody.filter { valid(it.start, it.end) }.sortedBy { it.start }
        )
    })
}
