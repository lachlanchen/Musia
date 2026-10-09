import Foundation

public struct WatchPlaybackSnapshot: Codable, Equatable, Sendable {
    public var version = 1
    public var selection: String
    public var title: String
    public var chord: String?
    public var chordConfidence: String
    public var bpm: Double?
    public var position: Double
    public var duration: Double
    public var rate: Double
    public var playing: Bool
    public var ready: Bool
    public var issuedAt: Double

    public init(selection: String = "", title: String = "", chord: String? = nil,
                chordConfidence: String = "Unavailable", bpm: Double? = nil,
                position: Double = 0, duration: Double = 0, rate: Double = 1,
                playing: Bool = false, ready: Bool = false, issuedAt: Double = Date().timeIntervalSince1970) {
        self.selection = selection; self.title = title; self.chord = chord
        self.chordConfidence = chordConfidence; self.bpm = bpm
        self.position = position; self.duration = duration; self.rate = rate
        self.playing = playing; self.ready = ready; self.issuedAt = issuedAt
    }

    public var valid: Bool {
        version == 1 && selection.count <= 100 && title.count <= 240 &&
        (chord?.count ?? 0) <= 64 && chordConfidence.count <= 64 &&
        position.isFinite && duration.isFinite && position >= 0 && duration >= 0 &&
        position <= duration + 1 && duration <= 86400 &&
        rate.isFinite && (0.25...2).contains(rate) && issuedAt.isFinite &&
        (bpm.map { $0.isFinite && (1...500).contains($0) } ?? true)
    }

    public func fresh(at time: Double = Date().timeIntervalSince1970) -> Bool {
        valid && time.isFinite && (-5...30).contains(time - issuedAt)
    }

    public func encoded() -> Data? { valid ? try? JSONEncoder().encode(self) : nil }

    public static func decode(_ data: Data) -> Self? {
        guard data.count <= 8192, let value = try? JSONDecoder().decode(Self.self, from: data), value.valid else { return nil }
        return value
    }
}

public struct WatchPlaybackCommand: Codable, Sendable {
    public enum Action: String, Codable, Sendable { case refresh, play, pause, seek, rate }
    public let version: Int
    public let id: UUID
    public let selection: String
    public let action: Action
    public let value: Double?
    public let issuedAt: Double

    public init(action: Action, selection: String, value: Double? = nil,
                id: UUID = UUID(), issuedAt: Double = Date().timeIntervalSince1970) {
        version = 1; self.id = id; self.selection = selection
        self.action = action; self.value = value; self.issuedAt = issuedAt
    }

    public func valid(at time: Double = Date().timeIntervalSince1970) -> Bool {
        guard version == 1, selection.count <= 100, issuedAt.isFinite, time.isFinite,
              (-5...15).contains(time - issuedAt) else { return false }
        switch action {
        case .seek: return value.map { $0.isFinite && (0...86400).contains($0) } ?? false
        case .rate: return value.map { $0.isFinite && (0.25...2).contains($0) } ?? false
        default: return value == nil
        }
    }
}

/// Duplicate and delayed commands never act on a replacement song.
public struct WatchCommandGuard {
    private var handled: [UUID] = []
    public init() {}
    public mutating func accept(_ command: WatchPlaybackCommand, selection: String,
                                ready: Bool, now: Double = Date().timeIntervalSince1970) -> Bool {
        guard command.valid(at: now), !handled.contains(command.id),
              command.action == .refresh || (ready && !selection.isEmpty && command.selection == selection) else { return false }
        handled.append(command.id)
        if handled.count > 64 { handled.removeFirst(handled.count - 64) }
        return true
    }
}
