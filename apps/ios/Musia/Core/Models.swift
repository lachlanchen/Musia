import Foundation

public enum AnalysisConfidence: String, Codable, Sendable {
    case analysis, verified, estimated, unavailable

    public init(from decoder: Decoder) throws {
        let value = try decoder.singleValueContainer().decode(String.self)
        self = Self(rawValue: value) ?? .unavailable
    }

    public var label: String {
        switch self {
        case .analysis: return "Analyzed"
        case .verified: return "Verified"
        case .estimated: return "Estimated"
        case .unavailable: return "Unavailable"
        }
    }
}

public struct Confidence: Codable, Sendable {
    public let beats: AnalysisConfidence
    public let chords: AnalysisConfidence
    public let melody: AnalysisConfidence
}

public struct LibraryResponse: Decodable, Sendable {
    public let version: Int
    public let items: [LibraryItem]

    public func validated() throws -> Self {
        guard version == 1 else { throw ContractError.version(version) }
        guard Set(items.map(\.id)).count == items.count,
              items.allSatisfy({ !$0.id.isEmpty && $0.duration.isFinite && $0.duration > 0 })
        else { throw ContractError.invalid("library") }
        return self
    }
}

public struct LibraryItem: Codable, Identifiable, Sendable {
    public let id: String
    public let title: String
    public let artist: String
    public let coverUrl: URL?
    public let duration: Double
    public let kind: String

    public init(id: String, title: String, artist: String, coverUrl: URL?, duration: Double, kind: String) {
        self.id = id; self.title = title; self.artist = artist
        self.coverUrl = coverUrl; self.duration = duration; self.kind = kind
    }
}

public struct Song: Decodable, Identifiable, Sendable {
    public let version: Int
    public let id: String
    public let title: String
    public let artist: String
    public let coverUrl: URL?
    public let assets: [SongAsset]
    public let defaultAssetId: String

    public var defaultAsset: SongAsset? { assets.first { $0.id == defaultAssetId } }

    public func validated() throws -> Self {
        guard version == 1 else { throw ContractError.version(version) }
        guard !id.isEmpty, defaultAsset != nil,
              Set(assets.map(\.id)).count == assets.count else { throw ContractError.invalid("song") }
        for asset in assets { try asset.validate() }
        return self
    }
}

public struct SongAsset: Decodable, Identifiable, Sendable {
    public let id: String
    public let label: String
    public let language: String
    public let audioUrl: URL
    public let duration: Double
    public let bpm: Double?
    public let timeSignature: String?
    public let confidence: Confidence
    public let beats: [Beat]
    public let chords: [Chord]
    public let lyrics: [LyricLine]
    public let phrases: [Phrase]
    public let melody: [MelodyNote]
    public let lyricTracks: [LyricTrack]?

    public var displayLyricTracks: [LyricTrack] {
        let tracks = lyricTracks?.filter { !$0.lines.isEmpty } ?? []
        return (tracks.isEmpty && !lyrics.isEmpty ? [LyricTrack(language: language, lines: lyrics)] : tracks)
            .sorted { LyricLanguages.rank($0.language) < LyricLanguages.rank($1.language) }
    }

    public var loopPhrases: [Phrase] {
        if !phrases.isEmpty { return phrases }
        return lyrics.map { Phrase(id: $0.id, start: $0.start, end: $0.end, text: $0.text) }
    }

    public func validate() throws {
        guard !id.isEmpty, duration.isFinite, duration > 0,
              bpm.map({ $0.isFinite && $0 > 0 }) ?? true,
              beats.allSatisfy({ $0.time.isFinite && $0.time >= 0 && $0.time < duration }),
              zip(beats, beats.dropFirst()).allSatisfy({ $0.time < $1.time })
        else { throw ContractError.invalid("audio timing") }
        try validateIntervals(chords)
        try validateIntervals(lyrics)
        try validateIntervals(phrases)
        try validateIntervals(melody)
        guard Set(lyrics.map(\.id)).count == lyrics.count,
              Set(phrases.map(\.id)).count == phrases.count
        else { throw ContractError.invalid("phrase identifiers") }
        let tracks = lyricTracks ?? []
        guard Set(tracks.map(\.language)).count == tracks.count,
              tracks.allSatisfy({ !$0.language.isEmpty })
        else { throw ContractError.invalid("lyric languages") }
        for track in tracks {
            try validateIntervals(track.lines)
            guard Set(track.lines.map(\.id)).count == track.lines.count
            else { throw ContractError.invalid("translation identifiers") }
        }
        for line in lyrics + tracks.flatMap(\.lines) {
            guard line.tokens.allSatisfy({ $0.start >= line.start && $0.end <= line.end })
            else { throw ContractError.invalid("lyric tokens") }
            try validateIntervals(line.tokens)
        }
    }

    private func validateIntervals<T: TimedInterval>(_ values: [T]) throws {
        guard values.allSatisfy({
            $0.start.isFinite && $0.end.isFinite && $0.start >= 0 && $0.end > $0.start && $0.end <= duration
        }), zip(values, values.dropFirst()).allSatisfy({ $0.start <= $1.start })
        else { throw ContractError.invalid("intervals") }
    }
}

public protocol TimedInterval {
    var start: Double { get }
    var end: Double { get }
}

public struct Beat: Codable, Sendable {
    public let time: Double
    public init(time: Double) { self.time = time }
}

public struct Chord: Codable, TimedInterval, Sendable {
    public let start: Double
    public let end: Double
    public let name: String
    public let confidence: Double?
}

public struct LyricLine: Codable, TimedInterval, Identifiable, Sendable {
    public let id: String
    public let start: Double
    public let end: Double
    public let text: String
    public let tokens: [LyricToken]
}

public struct LyricTrack: Codable, Identifiable, Sendable {
    public let language: String
    public let lines: [LyricLine]
    public var id: String { language }
}

public struct LyricToken: Codable, TimedInterval, Sendable {
    public let text: String
    public let start: Double
    public let end: Double
    public let reading: String?
}

public struct Phrase: Codable, TimedInterval, Identifiable, Sendable {
    public let id: String
    public let start: Double
    public let end: Double
    public let text: String

    public init(id: String, start: Double, end: Double, text: String) {
        self.id = id; self.start = start; self.end = end; self.text = text
    }
}

// The v1 contract permits numeric MIDI/scale values and rendered note names.
public struct NoteLabel: Decodable, Sendable {
    public let text: String
    public init(from decoder: Decoder) throws {
        let value = try decoder.singleValueContainer()
        if let string = try? value.decode(String.self) { text = string }
        else if let integer = try? value.decode(Int.self) { text = String(integer) }
        else { text = String(try value.decode(Double.self)) }
    }
}

public struct MelodyNote: Decodable, TimedInterval, Sendable {
    public let start: Double
    public let end: Double
    public let note: NoteLabel
    public let numberNote: NoteLabel
    public let text: String
}

public struct LessonsResponse: Decodable, Sendable {
    public let lessons: [Lesson]
    public func validated() throws -> Self {
        guard Set(lessons.map(\.id)).count == lessons.count,
              lessons.allSatisfy({ !$0.id.isEmpty && !$0.exerciseId.isEmpty })
        else { throw ContractError.invalid("lessons") }
        return self
    }
}

public struct Lesson: Decodable, Identifiable, Sendable {
    public let id: String
    public let title: String
    public let focus: String
    public let body: String
    public let exerciseId: String
    public let steps: [String]
}

public enum ContractError: LocalizedError {
    case version(Int)
    case invalid(String)
    public var errorDescription: String? {
        switch self {
        case .version(let version): return "This app cannot read API version \(version)."
        case .invalid(let field): return "The server returned invalid \(field). Try again after the catalog is updated."
        }
    }
}
