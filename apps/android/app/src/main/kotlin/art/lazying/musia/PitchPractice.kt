package art.lazying.musia

import kotlin.math.*

// Monophonic YIN: de Cheveigne & Kawahara, JASA 111 (2002), 1917-1930.
object PitchPractice {
    const val sampleRate = 16000
    const val frameSize = 2048
    fun frequency(input: FloatArray): Double? {
        if (input.size != frameSize || input.any { !it.isFinite() }) return null
        val mean = input.average()
        val samples = DoubleArray(input.size) { input[it] - mean }
        val energy = samples.sumOf { it * it } / samples.size
        if (energy <= .000025 || input.count { abs(it) >= .98 } >= frameSize / 100) return null
        val maxLag = sampleRate / 70
        val normalized = DoubleArray(maxLag + 1) { 1.0 }
        var cumulative = 0.0
        for (lag in 1..maxLag) {
            var difference = 0.0
            for (i in 0 until frameSize - maxLag) {
                val delta = samples[i] - samples[i + lag]
                difference += delta * delta
            }
            cumulative += difference
            normalized[lag] = if (cumulative > 0) difference * lag / cumulative else 1.0
        }
        var lag = sampleRate / 1000
        while (lag < maxLag) {
            if (normalized[lag] < .15) {
                while (lag + 1 < maxLag && normalized[lag + 1] < normalized[lag]) lag++
                val left = normalized[lag - 1]; val center = normalized[lag]; val right = normalized[lag + 1]
                val denominator = left - 2 * center + right
                val shift = if (abs(denominator) > 1e-12) .5 * (left - right) / denominator else 0.0
                val hz = sampleRate / (lag + shift.coerceIn(-1.0, 1.0))
                return hz.takeIf { it in 70.0..1000.0 }
            }
            lag++
        }
        return null
    }
    fun analyze(samples: FloatArray, targetHz: Double): PitchResult? {
        if (!targetHz.isFinite() || targetHz !in 70.0..1000.0 || samples.size !in frameSize..sampleRate * 4) return null
        val cents = mutableListOf<Double>(); var frames = 0
        for (offset in 0..samples.size - frameSize step 1024) {
            if (Thread.currentThread().isInterrupted) return null
            frames++
            frequency(samples.copyOfRange(offset, offset + frameSize))?.let { cents.add(1200 * log2(it / targetHz)) }
        }
        if (cents.size < 10 || cents.size.toDouble() / frames < .25) return null
        return PitchResult(cents)
    }
}
class PitchResult(cents: List<Double>) {
    private val values = cents.filter { it.isFinite() }.sorted()
    val medianCents = if (values.isEmpty()) 0.0 else values[values.size / 2]
    val inTunePercent = if (values.isEmpty()) 0 else (100.0 * values.count { abs(it) <= 50 } / values.size).roundToInt()
    val voicedSeconds = values.size * 1024.0 / PitchPractice.sampleRate
}
