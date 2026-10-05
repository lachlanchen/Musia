import Foundation

public enum BeginnerPractice {
    // Fixed Do in C major. The upper Do closes the octave, rather than adding a new degree.
    public static let syllables = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Ti", "Do ↑"]
    public static let noteNames = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
    public static let midi = [60, 62, 64, 65, 67, 69, 71, 72]
    public static let sampleRate = 24000

    public static func frequency(_ index: Int) -> Double {
        440 * pow(2, Double(midi[min(7, max(0, index))] - 69) / 12)
    }

    public static func tone(_ index: Int) -> Data {
        let hz = frequency(index)
        let frames = sampleRate
        return wav((0..<frames).map { i in
            let time = Double(i) / Double(sampleRate)
            let envelope = min(1, time / 0.02) * min(1, (1 - time) / 0.08)
            return 0.24 * envelope * sin(2 * .pi * hz * time)
        })
    }

    public static func metronome(bpm: Int, chords: Bool) -> Data {
        let beatSeconds = 60.0 / Double(min(160, max(40, bpm)))
        let frames = Int((beatSeconds * 8 * Double(sampleRate)).rounded())
        let notes = [[52, 55, 59], [45, 48, 52]] // Em then Am, four beats each.
        return wav((0..<frames).map { i in
            let time = Double(i) / Double(sampleRate)
            let beat = Int(time / beatSeconds)
            let phase = time - Double(beat) * beatSeconds
            let click = phase < 0.045 ? 0.26 * pow(1 - phase / 0.045, 3)
                * cos(2 * .pi * (beat % 4 == 0 ? 1400 : 1000) * phase) : 0
            guard chords else { return click }
            let barPhase = time.truncatingRemainder(dividingBy: beatSeconds * 4)
            let envelope = min(1, barPhase / 0.015) * min(1, (beatSeconds * 4 - barPhase) / 0.04) * exp(-0.7 * barPhase)
            let harmony = notes[min(1, beat / 4)].reduce(0.0) { value, midi in
                value + sin(2 * .pi * 440 * pow(2, Double(midi - 69) / 12) * barPhase)
            } / 3
            return click + 0.2 * envelope * harmony
        })
    }

    private static func wav(_ samples: [Double]) -> Data {
        var data = Data()
        func append<T: FixedWidthInteger>(_ value: T) {
            var little = value.littleEndian
            withUnsafeBytes(of: &little) { data.append(contentsOf: $0) }
        }
        let bytes = UInt32(samples.count * 2)
        data.append(contentsOf: "RIFF".utf8); append(bytes + 36)
        data.append(contentsOf: "WAVEfmt ".utf8); append(UInt32(16)); append(UInt16(1)); append(UInt16(1))
        append(UInt32(sampleRate)); append(UInt32(sampleRate * 2)); append(UInt16(2)); append(UInt16(16))
        data.append(contentsOf: "data".utf8); append(bytes)
        for sample in samples { append(Int16((min(1, max(-1, sample)) * 32767).rounded())) }
        return data
    }
}

public struct PitchRound {
    public private(set) var targets: [Int]
    public private(set) var index = 0
    public private(set) var correct = 0
    public private(set) var answer: Int?
    public var target: Int { targets[index] }
    public var answered: Int { index + (answer == nil ? 0 : 1) }
    public var finished: Bool { index == targets.count - 1 && answer != nil }

    public init(targets: [Int]) {
        self.targets = targets.filter { (0..<8).contains($0) }
        if self.targets.isEmpty { self.targets = [0] }
    }
    public mutating func choose(_ note: Int) {
        guard answer == nil, (0..<8).contains(note) else { return }
        answer = note
        if note == target { correct += 1 }
    }
    public mutating func next() {
        guard answer != nil, !finished else { return }
        index += 1; answer = nil
    }
}
