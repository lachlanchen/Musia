package art.lazying.musia

data class Guidance(val title: String, val body: String, val steps: List<String> = emptyList())

fun practiceGuidance(songId: String, mode: PracticeMode, lessons: List<Lesson>): Guidance {
    if (songId == "first-pulse") {
        val lessonId = when (mode) {
            PracticeMode.Listen -> "listen-first"
            PracticeMode.Tap -> "tap-the-pulse"
            PracticeMode.Play -> "em-am-switch"
        }
        lessons.firstOrNull { it.id == lessonId && it.exerciseId == songId }?.let { return Guidance(it.title, it.body, it.steps) }
    }
    return when (mode) {
        PracticeMode.Listen -> Guidance("Listen for a change", "Listen for the pulse and changes in harmony. Detected chords are suggestions, not a verified score.")
        PracticeMode.Tap -> Guidance("Find a steady pulse", "Listen first, then aim for evenly spaced taps. Beat analysis can be wrong; a clear audible pulse is a better guide.")
        PracticeMode.Play -> Guidance("One small phrase", "Begin with a comfortable chord change and leave space. Check uncertain harmony against a reviewed score or a teacher.")
    }
}

fun phaseLabel(songId: String, asset: Asset, positionMs: Long, playing: Boolean): String {
    if (!playing) return "Paused"
    if (songId == "first-pulse" && asset.confidence.beats == "verified" && asset.confidence.chords == "verified") {
        return when {
            positionMs < 4000 -> "Count-in"
            positionMs < 20000 -> "Practice bar ${(positionMs - 4000) / 4000 + 1} / 4"
            else -> "Final decay"
        }
    }
    if (asset.beats.isEmpty()) return "No reference beats"
    if (positionMs < secondsToMs(asset.beats.first().time)) return "Before first reference beat"
    if (positionMs > secondsToMs(asset.beats.last().time)) return "After last reference beat"
    return "Detected pulses / Downbeat unverified"
}
