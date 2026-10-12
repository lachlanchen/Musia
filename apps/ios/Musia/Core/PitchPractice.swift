import Foundation

/// Bounded monophonic YIN measurement. No speech recognition or model score.
/// Algorithm: de Cheveigne & Kawahara, JASA 111 (2002), 1917-1930.
public enum PitchPractice {
    public static let sampleRate = 16000
    public static let frameSize = 2048
    public static func frequency(_ input: [Float]) -> Double? {
        guard input.count == frameSize, input.allSatisfy({ $0.isFinite }) else { return nil }
        let mean = input.reduce(0.0) { $0 + Double($1) } / Double(input.count)
        let samples = input.map { Double($0) - mean }
        let energy = samples.reduce(0) { $0 + $1 * $1 } / Double(samples.count)
        guard energy > 0.000025, input.filter({ abs($0) >= 0.98 }).count < frameSize / 100 else { return nil }
        let maxLag = sampleRate / 70
        var normalized = [Double](repeating: 1, count: maxLag + 1)
        var cumulative = 0.0
        for lag in 1...maxLag {
            var difference = 0.0
            for i in 0..<(frameSize - maxLag) {
                let delta = samples[i] - samples[i + lag]
                difference += delta * delta
            }
            cumulative += difference
            normalized[lag] = cumulative > 0 ? difference * Double(lag) / cumulative : 1
        }
        var lag = sampleRate / 1000
        while lag < maxLag {
            if normalized[lag] < 0.15 {
                while lag + 1 < maxLag && normalized[lag + 1] < normalized[lag] { lag += 1 }
                let left = normalized[lag - 1], center = normalized[lag], right = normalized[lag + 1]
                let denominator = left - 2 * center + right
                let shift = abs(denominator) > 1e-12 ? 0.5 * (left - right) / denominator : 0
                let hz = Double(sampleRate) / (Double(lag) + min(1, max(-1, shift)))
                return (70...1000).contains(hz) ? hz : nil
            }
            lag += 1
        }
        return nil
    }

    public static func analyze(_ samples: [Float], targetHz: Double) -> PitchResult? {
        guard targetHz.isFinite, (70...1000).contains(targetHz), samples.count >= frameSize,
              samples.count <= sampleRate * 4 else { return nil }
        var cents = [Double]()
        var frames = 0
        for offset in stride(from: 0, through: samples.count - frameSize, by: 1024) {
            if Task.isCancelled { return nil }
            frames += 1
            if let hz = frequency(Array(samples[offset..<(offset + frameSize)])) {
                cents.append(1200 * log2(hz / targetHz))
            }
        }
        guard cents.count >= 10, Double(cents.count) / Double(frames) >= 0.25 else { return nil }
        return PitchResult(cents: cents)
    }
}

public struct PitchResult: Sendable {
    public let medianCents: Double
    public let inTunePercent: Int
    public let voicedSeconds: Double
    public init(cents: [Double]) {
        let values = cents.filter { $0.isFinite }.sorted()
        medianCents = values.isEmpty ? 0 : values[values.count / 2]
        inTunePercent = values.isEmpty ? 0 : Int((100 * Double(values.filter { abs($0) <= 50 }.count) / Double(values.count)).rounded())
        voicedSeconds = Double(values.count) * 1024 / Double(PitchPractice.sampleRate)
    }
}
