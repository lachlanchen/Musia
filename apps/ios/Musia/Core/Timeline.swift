import Foundation

public struct LoopRange: Codable, Equatable, Sendable {
    public let start: Double
    public let end: Double

    public init?(start: Double, end: Double, duration: Double) {
        guard start.isFinite, end.isFinite, duration.isFinite, duration > 0,
              start >= 0, end <= duration, end - start >= 0.1 else { return nil }
        self.start = start; self.end = end
    }

    public func constrainedSeek(_ time: Double) -> Double {
        guard time.isFinite else { return start }
        return time < start || time >= end ? start : time
    }
}

public enum Timeline {
    // Half-open intervals prevent two adjacent lyrics/chords being current at a boundary.
    public static func current<T: TimedInterval>(in intervals: [T], at time: Double) -> T? {
        guard time.isFinite else { return nil }
        return intervals.last { $0.start <= time && time < $0.end }
    }

    public static func next<T: TimedInterval>(in intervals: [T], at time: Double) -> T? {
        guard time.isFinite else { return nil }
        return intervals.first { $0.start > time }
    }

    public static func beatIndex(in beats: [Beat], at time: Double) -> Int? {
        guard time.isFinite else { return nil }
        return beats.lastIndex { $0.time <= time }
    }

    public static func pulse(in beats: [Beat], at time: Double, rate: Double) -> Double {
        guard let index = beatIndex(in: beats, at: time), rate.isFinite, rate > 0 else { return 0 }
        let elapsed = (time - beats[index].time) / rate
        return max(0, 1 - elapsed / 0.2)
    }

    public static func clampedRate(_ rate: Double) -> Double {
        rate.isFinite ? min(2, max(0.25, rate)) : 1
    }

    public static func clampedSeek(_ time: Double, duration: Double, loop: LoopRange?) -> Double {
        guard time.isFinite, duration.isFinite, duration > 0 else { return loop?.start ?? 0 }
        return loop?.constrainedSeek(time) ?? min(duration, max(0, time))
    }

    public static func timestamp(_ time: Double) -> String {
        guard time.isFinite, time >= 0, time < Double(Int.max) else { return "0:00" }
        let seconds = Int(time)
        return String(format: "%d:%02d", seconds / 60, seconds % 60)
    }
}

public struct TapFeedback: Equatable, Codable, Sendable {
    public let beatTime: Double
    public let offsetMilliseconds: Double

    public var label: String {
        if abs(offsetMilliseconds) <= 60 { return "Near the beat" }
        return "\(Int(abs(offsetMilliseconds).rounded())) ms \(offsetMilliseconds < 0 ? "early" : "late")"
    }
}

public enum TapEvaluator {
    public static func isWithinReference(time: Double, beats: [Beat], loop: LoopRange? = nil) -> Bool {
        let candidates = beats.filter { beat in
            beat.time.isFinite && (loop.map { beat.time >= $0.start && beat.time < $0.end } ?? true)
        }
        guard time.isFinite, let first = candidates.first, let last = candidates.last else { return false }
        return time >= first.time && time <= last.time
    }

    // Compare the actual media clock, not UI refresh time. Convert to wall-time at the active rate.
    public static func evaluate(time: Double, rate: Double, beats: [Beat], loop: LoopRange? = nil) -> TapFeedback? {
        guard time.isFinite, rate.isFinite, (0.25...2).contains(rate),
              isWithinReference(time: time, beats: beats, loop: loop) else { return nil }
        let candidates = beats.filter { beat in
            beat.time.isFinite && (loop.map { beat.time >= $0.start && beat.time < $0.end } ?? true)
        }
        guard let nearest = candidates.min(by: { abs($0.time - time) < abs($1.time - time) }) else { return nil }
        let offset = (time - nearest.time) / rate
        guard abs(offset) <= 0.5 else { return nil }
        return TapFeedback(beatTime: nearest.time, offsetMilliseconds: offset * 1_000)
    }
}
