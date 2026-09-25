package art.lazying.musia

import kotlin.math.abs
import kotlin.math.roundToLong

fun secondsToMs(seconds: Double): Long = (seconds * 1000).roundToLong()
fun validInterval(start: Double, end: Double, duration: Double): Boolean =
    start.isFinite() && end.isFinite() && duration.isFinite() && start >= 0 && end > start && end <= duration

// Half-open intervals prevent stale lyrics/chords at boundaries and in gaps.
fun <T> currentInterval(items: List<T>, time: Double, start: (T) -> Double, end: (T) -> Double): T? =
    items.lastOrNull { time >= start(it) && time < end(it) }

data class LoopRange(val startMs: Long, val endMs: Long) {
    init { require(startMs >= 0 && endMs - startMs >= 100) }
    val durationMs: Long get() = endMs - startMs
    fun relative(absoluteMs: Long): Long = (absoluteMs - startMs).coerceIn(0, durationMs - 1)
    fun absolute(relativeMs: Long): Long = startMs + relativeMs.coerceIn(0, durationMs)
    companion object {
        fun from(start: Double, end: Double, duration: Double): LoopRange? {
            if (!validInterval(start, end, duration)) return null
            val a = secondsToMs(start)
            val b = secondsToMs(end)
            return if (b - a >= 100) LoopRange(a, b) else null
        }
    }
}

fun beatIndex(beats: List<Beat>, time: Double): Int {
    var lo = 0
    var hi = beats.lastIndex
    while (lo <= hi) {
        val mid = (lo + hi) ushr 1
        if (beats[mid].time <= time) lo = mid + 1 else hi = mid - 1
    }
    return hi
}

fun withinBeatRange(beats: List<Beat>, positionMs: Long): Boolean =
    beats.isNotEmpty() && positionMs >= secondsToMs(beats.first().time) && positionMs <= secondsToMs(beats.last().time)

// Return real-time milliseconds, not media-time milliseconds at slowed speed.
fun tapOffsetMs(beats: List<Beat>, positionMs: Long, speed: Float, calibrationMs: Int, loop: LoopRange? = null): Long? {
    if (!speed.isFinite() || speed <= 0 || !withinBeatRange(beats, positionMs)) return null
    val eligible = if (loop == null) beats else beats.filter { secondsToMs(it.time) in loop.startMs until loop.endMs }
    if (eligible.isEmpty()) return null
    val time = positionMs / 1000.0
    val index = beatIndex(eligible, time)
    val candidates = listOfNotNull(eligible.getOrNull(index), eligible.getOrNull(index + 1)).map { secondsToMs(it.time) }.toMutableList()
    // A tap just before/after a loop boundary can belong to the adjacent cycle.
    if (loop != null) {
        candidates += secondsToMs(eligible.first().time) + loop.durationMs
        candidates += secondsToMs(eligible.last().time) - loop.durationMs
    }
    val nearest = candidates.minByOrNull { abs(positionMs - it) } ?: return null
    val offset = ((positionMs - nearest) / speed).roundToLong() - calibrationMs
    return offset.takeIf { abs(it) <= 1000 }
}
