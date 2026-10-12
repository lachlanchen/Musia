import Foundation

public enum PracticePattern: String, CaseIterable, Sendable {
    case hold = "Hold", strum = "Down-strum", picking = "Arpeggio"
}

public struct PracticePlan: Sendable {
    public let bpm: Int
    public let beats: Int
    public let subdivision: Int
    public let progression: Int
    public let pattern: PracticePattern
    public static let progressions = ["Click only", "Em · Am", "C · Am · F · G"]
    public static let chordNames = [[], ["Em", "Am"], ["C", "Am", "F", "G"]]
    private static let pitches = [[], [[52, 55, 59], [45, 48, 52]],
                                 [[48, 52, 55], [45, 48, 52], [53, 57, 60], [43, 47, 50]]]

    public init(bpm: Int = 60, beats: Int = 4, subdivision: Int = 1,
                progression: Int = 0, pattern: PracticePattern = .hold) {
        self.bpm = min(240, max(30, bpm))
        self.beats = [2, 3, 4, 6].contains(beats) ? beats : 4
        self.subdivision = min(3, max(1, subdivision))
        self.progression = min(2, max(0, progression))
        self.pattern = pattern
    }
    public var beatSeconds: Double { 60 / Double(bpm) }
    public var bars: Int { max(2, Self.chordNames[progression].count) }
    public var duration: Double { Double(bars * beats) * beatSeconds }
    public func beat(at time: Double) -> Int {
        guard time.isFinite, time >= 0 else { return 0 }
        return Int((time / beatSeconds).truncatingRemainder(dividingBy: Double(beats)))
    }
    public func chord(at time: Double) -> String? {
        let names = Self.chordNames[progression]
        guard !names.isEmpty, time.isFinite, time >= 0 else { return nil }
        return names[Int((time / (beatSeconds * Double(beats))).truncatingRemainder(dividingBy: Double(names.count)))]
    }
    public func audio() -> Data {
        let frames = Int((duration * Double(BeginnerPractice.sampleRate)).rounded())
        return BeginnerPractice.wav((0..<frames).map { i in
            let time = Double(i) / Double(BeginnerPractice.sampleRate)
            let tickSeconds = beatSeconds / Double(subdivision)
            let tick = Int(time / tickSeconds)
            let phase = time - Double(tick) * tickSeconds
            let downbeat = tick % (beats * subdivision) == 0
            let click = phase < 0.035 ? (downbeat ? 0.26 : 0.14) * pow(1 - phase / 0.035, 3)
                * cos(2 * .pi * (downbeat ? 1400 : 1000) * phase) : 0
            guard progression > 0 else { return click }
            let barSeconds = beatSeconds * Double(beats)
            let notes = Self.pitches[progression][min(bars - 1, Int(time / barSeconds))]
            let interval = pattern == .hold ? barSeconds : beatSeconds
            let onset = floor(time / interval) * interval
            let t = time - onset
            let envelope = min(1, t / 0.012) * min(1, (interval - t) / 0.04) * exp(-1.4 * t)
            let selected = pattern == .picking ? [notes[Int(time / beatSeconds) % notes.count]] : notes
            let harmony = selected.reduce(0.0) { $0 + sin(2 * .pi * 440 * pow(2, Double($1 - 69) / 12) * t) } / Double(selected.count)
            return click + 0.2 * envelope * harmony
        })
    }
}

public struct TapTempo {
    private var times: [Double] = []
    public init() {}
    public mutating func tap(at now: Double) -> Int? {
        guard now.isFinite else { return nil }
        if let last = times.last {
            if now <= last || now - last > 2.5 { times = [] }
            else if now - last < 0.18 { return nil }
        }
        times.append(now); times = Array(times.suffix(9))
        guard times.count >= 4 else { return nil }
        let intervals = zip(times.dropFirst(), times).map(-).sorted()
        let seconds = intervals[intervals.count / 2]
        return min(240, max(30, Int((60 / seconds).rounded())))
    }
}

public struct RhythmFeedback {
    public private(set) var offsets: [Double] = []
    private var lastTap: Double?
    public init() {}
    public mutating func tap(playback: Double, monotonic: Double, bpm: Int) {
        guard playback.isFinite, playback >= 0, monotonic.isFinite else { return }
        if let lastTap, monotonic - lastTap < 0.12 { return }
        lastTap = monotonic
        let beat = 60.0 / Double(min(240, max(30, bpm)))
        offsets.append((playback - (playback / beat).rounded() * beat) * 1000)
        offsets = Array(offsets.suffix(32))
    }
    public var averageOffset: Double { offsets.isEmpty ? 0 : offsets.map(abs).reduce(0, +) / Double(offsets.count) }
    public var bias: Double { offsets.isEmpty ? 0 : offsets.reduce(0, +) / Double(offsets.count) }
    public func inTimePercent(bpm: Int) -> Int? {
        guard offsets.count >= 4 else { return nil }
        let tolerance = max(40, 60_000.0 / Double(min(240, max(30, bpm))) * 0.08)
        return Int((100 * Double(offsets.filter { abs($0) <= tolerance }.count) / Double(offsets.count)).rounded())
    }
}
