import Foundation

public enum FirstPulse {
    public static let id = "first-pulse"
    public static let duration: Double = 22
    public static let sampleRate = 24_000
    public static let item = LibraryItem(
        id: id, title: "First Pulse", artist: "Musia exercises", coverUrl: nil,
        duration: duration, kind: "Synthesized exercise"
    )

    public static func song(audioURL: URL) throws -> Song {
        let phrases = [
            Phrase(id: "bar-1", start: 4, end: 8, text: "Em"),
            Phrase(id: "bar-2", start: 8, end: 12, text: "Am"),
            Phrase(id: "bar-3", start: 12, end: 16, text: "Em"),
            Phrase(id: "bar-4", start: 16, end: 20, text: "Am")
        ]
        let chords: [Chord] = phrases.map {
            Chord(start: $0.start, end: $0.end, name: $0.text, confidence: 1)
        }
        let asset = SongAsset(
            id: id, label: "First Pulse - Em / Am", language: "zxx", audioUrl: audioURL,
            duration: duration, bpm: 60, timeSignature: "4/4",
            confidence: Confidence(beats: .verified, chords: .verified, melody: .unavailable),
            beats: (0..<20).map { Beat(time: Double($0)) }, chords: chords, lyrics: [],
            phrases: phrases, melody: [], lyricTracks: nil
        )
        return try Song(version: 1, id: id, title: item.title, artist: item.artist,
                        coverUrl: nil, assets: [asset], defaultAssetId: id).validated()
    }

    // Exact sample positions, one second apart. No microphone, model, or external audio dependency.
    public static func wavData() -> Data {
        let frames = Int(duration) * sampleRate
        let byteCount = UInt32(frames * 2)
        var data = Data()
        func append<T: FixedWidthInteger>(_ number: T) {
            var littleEndian = number.littleEndian
            withUnsafeBytes(of: &littleEndian) { data.append(contentsOf: $0) }
        }
        data.append(contentsOf: "RIFF".utf8); append(byteCount + 36)
        data.append(contentsOf: "WAVEfmt ".utf8); append(UInt32(16))
        append(UInt16(1)); append(UInt16(1)); append(UInt32(sampleRate))
        append(UInt32(sampleRate * 2)); append(UInt16(2)); append(UInt16(16))
        data.append(contentsOf: "data".utf8); append(byteCount)
        let noteSets = [[52.0, 55.0, 59.0], [45.0, 48.0, 52.0]]
        let frequencies = noteSets.map { $0.map { 440 * pow(2, ($0 - 69) / 12) } }
        for frame in 0..<frames {
            let beat = frame / sampleRate
            let local = Double(frame % sampleRate) / Double(sampleRate)
            let frequency = beat % 4 == 0 ? 1_400.0 : 1_000.0
            var sample = beat < 20 && local < 0.05
                ? 0.5 * pow(1 - local / 0.05, 4) * cos(2 * .pi * frequency * local) : 0
            if beat >= 4 {
                let bar = min(3, (beat - 4) / 4)
                let start = (bar + 1) * 4 * sampleRate
                let length = (bar == 3 ? 6 : 4) * sampleRate
                let n = frame - start
                let time = Double(n) / Double(sampleRate)
                var envelope = min(1, Double(n) / (0.008 * Double(sampleRate))) * exp(-0.22 * time)
                if bar == 3 && time >= 4 {
                    envelope *= pow(max(0, Double(length - 1 - n) / Double(2 * sampleRate)), 2)
                } else if bar != 3 {
                    envelope *= min(1, Double(length - 1 - n) / (0.02 * Double(sampleRate)))
                }
                let tone = frequencies[bar % 2].reduce(0) { $0 + sin(2 * .pi * $1 * time) } / 3
                sample += 0.24 * envelope * tone
            }
            append(Int16((min(1, max(-1, sample)) * Double(Int16.max)).rounded()))
        }
        return data
    }
}
