import Foundation

public struct CreatorCapabilities: Decodable, Sendable {
    public let login: Bool
    public let generation: Bool
    public let agent: Bool
    public let termsVersion: String
    public let invitationRequired: Bool
    public let salesEnabled: Bool
}

public struct CreatorUsage: Codable, Sendable {
    public let tier: String
    public let period: String
    public let limit: Int
    public let used: Int
    public let remaining: Int
    public let source: String
}

public struct CreatorAccount: Decodable, Sendable, Identifiable {
    public let id: String
    public let name: String
    public let termsAccepted: Bool
    public let invited: Bool
    public let usage: CreatorUsage
}
public struct CreatorMe: Decodable { public let account: CreatorAccount? }

public struct CreatorBrief: Codable, Equatable, Sendable {
    public var title = ""
    public var idea = ""
    public var lyrics = ""
    public var caption = ""
    public var language = "en"
    public var duration = 90
    public var bpm = 100
    public var key = "C major"
    public init() {}
    public var isRenderable: Bool {
        // Pydantic counts Unicode code points, not graphemes or UTF-16 units.
        let lengthsValid = title.unicodeScalars.count <= 120 && idea.unicodeScalars.count <= 4000
            && lyrics.unicodeScalars.count <= 6000 && caption.unicodeScalars.count <= 1600
        let keyValid = key.range(of: #"^[A-G](?:#|b)? (?:major|minor)$"#, options: .regularExpression)
            == (key.startIndex..<key.endIndex)
        return lengthsValid && keyValid
        && [title, lyrics, caption].allSatisfy { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        && ["en", "zh", "ja", "mixed"].contains(language)
        && (30...180).contains(duration) && (40...200).contains(bpm)
    }
}

public struct CreatorAgentReply: Decodable {
    public let message: String
    public let brief: CreatorBrief
}
public struct CreatorAgentRequest: Encodable {
    public let message: String
    public let brief: CreatorBrief
    public init(message: String, brief: CreatorBrief) { self.message = message; self.brief = brief }
}

public enum CreatorVisibility: String, Codable, CaseIterable, Sendable { case `private`, `public` }
public struct CreatorRenderRequest: Codable, Equatable, Sendable {
    public let brief: CreatorBrief
    public let rights_confirmed: Bool
    public let visibility: CreatorVisibility
    public init(brief: CreatorBrief, visibility: CreatorVisibility) {
        self.brief = brief; self.rights_confirmed = true; self.visibility = visibility
    }
}

/// Keep the frozen request and identity until the server acknowledges it. A failed
/// list refresh is never evidence that a submitted render did not run.
public struct PendingCreatorRender: Codable, Equatable, Sendable {
    public let owner: String
    public let key: String
    public let request: CreatorRenderRequest
    public init(owner: String, key: String = UUID().uuidString, request: CreatorRenderRequest) {
        self.owner = owner; self.key = key; self.request = request
    }
    public func canRetry(owner: String?) -> Bool { self.owner == owner }
    public func canDiscard(after error: Error, initial: Bool) -> Bool {
        guard initial, let failure = error as? CreatorError else { return false }
        if case .server(422, "invalid_request") = failure { return true }
        return false
    }
}

public struct CreatorIdentity: Equatable, Sendable {
    public let owner: String
    public let generation: UUID
    public init(owner: String, generation: UUID) { self.owner = owner; self.generation = generation }
    public func accepts(_ other: CreatorIdentity?) -> Bool { self == other }
}

public enum CreatorPurchaseGate {
    public static func allows(state: String, purchaseEnabled: Bool, salesEnabled: Bool,
                              hasPending: Bool, identity: CreatorIdentity?, binding: CreatorIdentity?) -> Bool {
        guard let identity, identity == binding else { return false }
        return purchaseEnabled && salesEnabled && !hasPending
            && ["none", "free", "inactive", "expired", "revoked"].contains(state)
    }
}

public struct CreatorJob: Decodable, Identifiable, Sendable {
    public let id: String
    public let status: String
    public let title: String?
    public let songId: String?
    public let message: String?
    public var canCancel: Bool { status == "queued" }
    public var isTerminal: Bool { ["ready", "failed", "cancelled", "canceled"].contains(status) }
    private enum CodingKeys: String, CodingKey { case id, state, brief, error }
    public init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        id = try values.decode(String.self, forKey: .id)
        status = try values.decode(String.self, forKey: .state)
        title = try values.decodeIfPresent(CreatorBrief.self, forKey: .brief)?.title
        songId = status == "ready" ? id : nil
        message = try values.decodeIfPresent(String.self, forKey: .error)
    }
}
public struct CreatorJobs: Decodable { public let jobs: [CreatorJob] }
public struct CreatorJobReceipt: Decodable {
    public let job: CreatorJob
    private enum CodingKeys: String, CodingKey { case job }
    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        if container.contains(.job) { job = try container.decode(CreatorJob.self, forKey: .job) }
        else { job = try CreatorJob(from: decoder) }
        guard !job.id.isEmpty, !job.status.isEmpty else { throw ContractError.invalid("render acknowledgement") }
    }
}
public struct CreatorAuthor: Codable, Sendable {
    public let id: String
    public let name: String
}
public struct CreatorLyricLine: Codable, Sendable {
    public let start: Double
    public let end: Double
    public let text: String
    public let language: String
}
public struct CreatorSong: Decodable, Identifiable, Sendable {
    public let id: String
    public let title: String
    public let language: String
    public let duration: Double
    public let author: CreatorAuthor
    public let mine: Bool
    public let visibility: CreatorVisibility
    public let moderation: String
    public let lyrics: String
    public let lyricLines: [CreatorLyricLine]
    public let audioUrl: String?
    public let sharePath: String?
    public let liked: Bool
    public let saved: Bool
    public let likes: Int

    public var requiresAuthenticatedPlayback: Bool {
        visibility != .public || moderation != "approved"
    }

    /// Only completed audio's supplied timed lines enter the learning player.
    /// No beat, chord or pitch estimates are invented for a generated song.
    public func playbackSong(audioURL: URL) throws -> Song {
        let lines = lyricLines.enumerated().map { index, line in
            LyricLine(id: String(index), start: line.start, end: line.end, text: line.text, tokens: [])
        }
        let asset = SongAsset(id: id, label: "Community song", language: language,
            audioUrl: audioURL, duration: duration, bpm: nil, timeSignature: nil,
            confidence: Confidence(beats: .unavailable, chords: .unavailable, melody: .unavailable),
            beats: [], chords: [], lyrics: lines, phrases: [], melody: [], lyricTracks: nil)
        return try Song(version: 1, id: "creator:" + id, title: title, artist: author.name,
                        coverUrl: nil, assets: [asset], defaultAssetId: id).validated()
    }
}
public struct CreatorSongs: Decodable { public let songs: [CreatorSong] }
public struct CreatorComment: Decodable, Identifiable {
    public let id: String
    public let text: String
    public let author: String
    public let state: String
    public let mine: Bool
}
public struct CreatorComments: Decodable { public let comments: [CreatorComment] }
public struct CreatorBlocks: Decodable {
    public let blocks: [CreatorAuthor]
    private enum CodingKeys: String, CodingKey { case blocks = "accounts" }
}

public struct CreatorBilling: Decodable {
    public struct CatalogProduct: Decodable, Identifiable {
        public let tier: String
        public let appleProductId: String
        public var id: String { appleProductId }
    }
    public struct Entitlement: Decodable {
        public let tier: String
        public let state: String
        public let expiresAt: Double?
        public let provider: String?
        public let environment: String?
    }
    public struct ProviderCapability: Decodable {
        public let purchase: Bool
        public let restore: Bool
        public let reason: String?
    }
    public struct Capabilities: Decodable { public let apple: ProviderCapability }
    public let accountToken: UUID
    public let products: [CatalogProduct]
    public let entitlement: Entitlement
    public let capabilities: Capabilities
}
public struct CreatorVerification: Decodable { public let verified: Bool }

public struct NativeAuthStart: Decodable {
    public let attempt: String
    public let url: URL
    public let expiresIn: Double
}
public struct NativeAuthToken: Codable {
    public let token: String
    public let expiresIn: Double
}
public struct NativeAuthAttempt: Codable, Sendable {
    public let attempt: String
    public let verifier: String
    public let expiresAt: Date
    public init(attempt: String, verifier: String, expiresAt: Date) {
        self.attempt = attempt; self.verifier = verifier; self.expiresAt = expiresAt
    }
    public func code(from url: URL, now: Date = Date()) throws -> String {
        guard now < expiresAt,
              let parts = URLComponents(url: url, resolvingAgainstBaseURL: false),
              parts.scheme == "art.lazying.musia", parts.host == "auth",
              parts.path.isEmpty, parts.port == nil, parts.user == nil, parts.password == nil,
              parts.fragment == nil, let items = parts.queryItems, items.count == 2,
              items.filter({ $0.name == "attempt" }).count == 1,
              items.first(where: { $0.name == "attempt" })?.value == attempt,
              items.filter({ $0.name == "code" }).count == 1,
              let code = items.first(where: { $0.name == "code" })?.value,
              !code.isEmpty, code.count <= 4096
        else { throw CreatorError.invalidCallback }
        return code
    }
}

public enum CreatorError: LocalizedError {
    case invalidCallback, sessionChanged, signInRequired, unsafeURL, storage, unavailable(String)
    case server(Int, String)
    public var errorDescription: String? {
        switch self {
        case .invalidCallback: return "Sign-in could not be validated. Start sign-in again."
        case .sessionChanged: return "Your account changed. Refresh to continue."
        case .signInRequired: return "Sign in to use this feature."
        case .unsafeURL: return "The server returned an unsupported address."
        case .storage: return "Secure storage is unavailable. Unlock your device and try again."
        case .unavailable(let message): return message
        case .server(401, _): return "Your session has expired. Sign in again."
        case .server(403, _): return "This action is not available for this account. Refresh your account and check access."
        case .server(429, _): return "Usage or request limit reached. Check your allowance and try later."
        case .server(let status, let code):
            return "The request could not be completed (\(status), \(code.replacingOccurrences(of: "_", with: " ")))."
        }
    }
}
