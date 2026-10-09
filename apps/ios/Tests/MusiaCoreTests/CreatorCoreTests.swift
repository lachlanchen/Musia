import XCTest
@testable import MusiaCore

final class CreatorCoreTests: XCTestCase {
    private let now = Date(timeIntervalSince1970: 1_000)
    private var attempt: NativeAuthAttempt {
        NativeAuthAttempt(attempt: "expected", verifier: String(repeating: "a", count: 43), expiresAt: now.addingTimeInterval(600))
    }
    func testCallbackRequiresExactTargetAndAttempt() throws {
        XCTAssertEqual(try attempt.code(from: URL(string: "art.lazying.musia://auth?attempt=expected&code=once")!, now: now), "once")
        let invalid = [
            "https://auth?attempt=expected&code=once",
            "art.lazying.musia://evil?attempt=expected&code=once",
            "art.lazying.musia://auth.evil?attempt=expected&code=once",
            "art.lazying.musia://auth/path?attempt=expected&code=once",
            "art.lazying.musia://auth:443?attempt=expected&code=once",
            "art.lazying.musia://user@auth?attempt=expected&code=once",
            "art.lazying.musia://auth?attempt=other&code=once",
            "art.lazying.musia://auth?attempt=expected&attempt=expected&code=once",
            "art.lazying.musia://auth?attempt=expected&code=once&code=twice",
            "art.lazying.musia://auth?attempt=expected&code=",
            "art.lazying.musia://auth?attempt=expected&code=once#fragment",
            "art.lazying.musia://auth?attempt=expected&code=once&token=forbidden"
        ]
        for value in invalid {
            XCTAssertThrowsError(try attempt.code(from: URL(string: value)!, now: now), value)
        }
        XCTAssertThrowsError(try attempt.code(from: URL(string: "art.lazying.musia://auth?attempt=expected&code=once")!, now: now.addingTimeInterval(600)))
    }
    func testUnknownRenderSurvivesPersistenceWithoutChangingBodyOrOwner() throws {
        var brief = CreatorBrief(); brief.title = "First song"; brief.lyrics = "A short line"; brief.caption = "Warm piano"
        let pending = PendingCreatorRender(owner: "original-owner", request: .init(brief: brief, visibility: .private))
        let before = try CreatorAPI.body(pending.request)
        let saved = try JSONEncoder().encode(pending)
        let restored = try JSONDecoder().decode(PendingCreatorRender.self, from: saved)
        brief.title = "Unrelated edited draft"
        XCTAssertEqual(restored, pending)
        XCTAssertEqual(try CreatorAPI.body(restored.request), before)
        XCTAssertEqual(restored.request.brief.title, "First song")
        XCTAssertTrue(restored.canRetry(owner: "original-owner"))
        XCTAssertFalse(restored.canRetry(owner: "new-owner"))
        XCTAssertFalse(restored.canRetry(owner: nil))
        XCTAssertEqual(restored.key, pending.key)
    }
    func testAccountGenerationRejectsLateResultsEvenForSameOwner() {
        let original = CreatorIdentity(owner: "one", generation: UUID())
        XCTAssertTrue(original.accepts(original))
        XCTAssertFalse(original.accepts(nil))
        XCTAssertFalse(original.accepts(CreatorIdentity(owner: "two", generation: original.generation)))
        XCTAssertFalse(original.accepts(CreatorIdentity(owner: "one", generation: UUID())))
    }
    func testAgentDraftCanBeEmptyButRenderCannot() {
        var brief = CreatorBrief()
        XCTAssertFalse(brief.isRenderable)
        brief.title = "Song"; brief.lyrics = "Line"; brief.caption = "Acoustic"
        XCTAssertTrue(brief.isRenderable)
        brief.duration = 181; XCTAssertFalse(brief.isRenderable)
        brief.duration = 30; brief.bpm = 39; XCTAssertFalse(brief.isRenderable)
        brief.bpm = 40; brief.language = "unknown"; XCTAssertFalse(brief.isRenderable)
        brief.language = "mixed"; brief.lyrics = " \n "; XCTAssertFalse(brief.isRenderable)
    }
    func testRenderLengthsMatchServerCodePointBounds() {
        let fields: [(WritableKeyPath<CreatorBrief, String>, Int)] = [
            (\.title, 120), (\.idea, 4000), (\.lyrics, 6000), (\.caption, 1600)
        ]
        for (field, limit) in fields {
            var brief = renderableBrief()
            brief[keyPath: field] = String(repeating: "x", count: limit)
            XCTAssertTrue(brief.isRenderable)
            brief[keyPath: field] += "x"
            XCTAssertFalse(brief.isRenderable)
            brief[keyPath: field] = String(repeating: "e\u{301}", count: limit / 2)
            XCTAssertEqual(brief[keyPath: field].unicodeScalars.count, limit)
            XCTAssertTrue(brief.isRenderable, "Combining marks count individually")
            brief[keyPath: field] += "\u{301}"
            XCTAssertFalse(brief.isRenderable, "One grapheme can exceed the scalar bound")
            brief[keyPath: field] = String(repeating: "\u{1F3B5}", count: limit)
            XCTAssertTrue(brief.isRenderable, "Supplementary scalars are not two code points")
            brief[keyPath: field] += "\u{1F3B5}"
            XCTAssertFalse(brief.isRenderable)
        }
    }
    func testRenderRequiresExactServerKeyAndNumericRanges() {
        var brief = renderableBrief()
        for note in ["A", "B", "C", "D", "E", "F", "G"] {
            for accidental in ["", "#", "b"] {
                for mode in ["major", "minor"] {
                    brief.key = "\(note)\(accidental) \(mode)"
                    XCTAssertTrue(brief.isRenderable, brief.key)
                }
            }
        }
        for key in ["", "C", "c major", "H minor", "C  major", "C Major", " C major", "C major ",
                    "C major\n", "C major\r\n", "C\u{266F} major", "C major; command"] {
            brief.key = key
            XCTAssertFalse(brief.isRenderable, key)
        }
        brief.key = "C major"
        for duration in [29, 30, 180, 181] {
            brief.duration = duration
            XCTAssertEqual(brief.isRenderable, (30...180).contains(duration))
        }
        brief.duration = 90
        for bpm in [39, 40, 200, 201] {
            brief.bpm = bpm
            XCTAssertEqual(brief.isRenderable, (40...200).contains(bpm))
        }
    }
    func testOnlyInitialExactInvalidRequestCanDiscardFrozenRender() throws {
        let pending = PendingCreatorRender(owner: "owner", key: "unchanged-key",
                                          request: .init(brief: renderableBrief(), visibility: .private))
        let body = try CreatorAPI.body(pending.request)
        XCTAssertTrue(pending.canDiscard(after: CreatorError.server(422, "invalid_request"), initial: true))
        let retained: [Error] = [
            CreatorError.server(422, "request_failed"), CreatorError.server(400, "invalid_request"),
            CreatorError.server(401, "invalid_request"), CreatorError.server(403, "invalid_request"),
            CreatorError.server(409, "idempotency_conflict"), CreatorError.server(409, "invalid_request"),
            CreatorError.server(429, "monthly_generation_limit"), CreatorError.server(500, "invalid_request"),
            CreatorError.server(503, "queue_full"), URLError(.timedOut), URLError(.networkConnectionLost),
            CancellationError(), CreatorError.sessionChanged, CreatorError.storage,
            ContractError.invalid("render acknowledgement")
        ]
        for error in retained {
            XCTAssertFalse(pending.canDiscard(after: error, initial: true), String(describing: error))
        }
        for error in retained + [CreatorError.server(422, "invalid_request")] {
            XCTAssertFalse(pending.canDiscard(after: error, initial: false), "Retries must retain unknown outcomes")
        }
        XCTAssertEqual(pending.key, "unchanged-key")
        XCTAssertEqual(try CreatorAPI.body(pending.request), body)
    }
    func testOnlyApprovedPublicSongsMayPlayWithoutAuthentication() throws {
        for visibility in ["private", "public"] {
            for moderation in ["private", "pending", "approved", "rejected", "future"] {
                for mine in [true, false] {
                    let song: CreatorSong = try decode("""
                    {"id":"song-1","title":"Song","language":"en","duration":60,
                    "author":{"id":"a","name":"Author"},"mine":\(mine),
                    "visibility":"\(visibility)","moderation":"\(moderation)",
                    "lyrics":"","lyricLines":[],"audioUrl":"/creator/api/songs/song-1/audio",
                    "sharePath":null,"liked":false,"saved":false,"likes":0}
                    """)
                    XCTAssertEqual(song.requiresAuthenticatedPlayback,
                                   visibility != "public" || moderation != "approved")
                }
            }
        }
    }
    func testPlaybackSuffixUsesMPEGMIMEIncludingCaseAndParameters() throws {
        for contentType in ["audio/mpeg", "Audio/MPEG", "audio/mpeg; charset=binary",
                            " AUDIO/MPEG ; charset=binary; name=song.wav "] {
            XCTAssertEqual(try CreatorAPI.playbackFileSuffix(contentType: contentType), "mp3")
        }
    }
    func testPlaybackSuffixPreservesSupportedWAVFallbacks() throws {
        for contentType in ["audio/wav", "audio/x-wav", "audio/wave", "audio/vnd.wave"] {
            XCTAssertEqual(try CreatorAPI.playbackFileSuffix(contentType: contentType), "wav")
            XCTAssertEqual(try CreatorAPI.playbackFileSuffix(contentType:
                " " + contentType.uppercased() + "; codecs=1; name=song.mp3"), "wav")
        }
    }
    func testPlaybackSuffixRejectsMissingAndUnexpectedContentTypes() {
        let unsupported: [String?] = [nil, "", " ", "; audio/mpeg", "text/html", "application/json",
            "application/octet-stream", "audio/ogg", "audio/mp4", "audio/mp3", "video/mpeg",
            "audio/mpeg, text/html", "audio/mpeg-extra", "text/html; name=song.mp3"]
        for contentType in unsupported {
            XCTAssertThrowsError(try CreatorAPI.playbackFileSuffix(contentType: contentType)) { error in
                guard case CreatorError.unavailable = error else {
                    XCTFail("Expected an unsupported audio format error, got \(error)"); return
                }
            }
        }
    }
    func testPurchaseGateFailsClosedForPendingPaidThroughAndUnknownStates() {
        let identity = CreatorIdentity(owner: "a", generation: UUID())
        func permits(_ state: String, pending: Bool = false, sales: Bool = true, purchase: Bool = true,
                     binding: CreatorIdentity? = nil) -> Bool {
            CreatorPurchaseGate.allows(state: state, purchaseEnabled: purchase, salesEnabled: sales,
                hasPending: pending, identity: identity, binding: binding ?? identity)
        }
        XCTAssertTrue(permits("free"))
        XCTAssertFalse(permits("free", pending: true))
        XCTAssertFalse(permits("free", sales: false))
        XCTAssertFalse(permits("free", purchase: false))
        for state in ["active", "pending", "grace", "hold", "canceled_paid_through", "future_state"] {
            XCTAssertFalse(permits(state), state)
        }
        XCTAssertFalse(permits("free", binding: CreatorIdentity(owner: "b", generation: UUID())))
        XCTAssertFalse(CreatorPurchaseGate.allows(state: "free", purchaseEnabled: true, salesEnabled: true,
            hasPending: false, identity: nil, binding: nil))
    }
    func testAccountAndClosedSalesBillingDecodeIndependently() throws {
        let account: CreatorMe = try decode("""
        {"account":{"id":"a","name":"Listener","termsAccepted":true,"invited":false,
        "usage":{"tier":"free","period":"2026-10","limit":2,"used":1,"remaining":1,"source":"server"}}}
        """)
        XCTAssertEqual(account.account?.usage.remaining, 1)
        let billing: CreatorBilling = try decode("""
        {"accountToken":"00000000-0000-4000-8000-000000000001",
        "products":[{"tier":"creator","appleProductId":"art.lazying.musia.creator.monthly"}],
        "entitlement":{"tier":"creator","state":"active","expiresAt":null,"provider":"apple","environment":"sandbox"},
        "capabilities":{"apple":{"purchase":false,"restore":true,"reason":"sales_closed"}}}
        """)
        XCTAssertFalse(billing.capabilities.apple.purchase)
        XCTAssertTrue(billing.capabilities.apple.restore)
        XCTAssertEqual(billing.products.count, 1)
        XCTAssertEqual(billing.entitlement.tier, "creator")
    }
    func testSongDecodingUsesTimedAudioLyricsAndDoesNotInventAnalysis() throws {
        let song: CreatorSong = try decode("""
        {"id":"song-1","title":"Song","language":"en","duration":60,
        "author":{"id":"a","name":"Author"},"mine":true,"visibility":"private","moderation":"private",
        "lyrics":"This unaligned text must not be copied into the player",
        "lyricLines":[{"start":1,"end":3,"text":"Actually sung","language":"en"}],
        "audioUrl":"/creator/api/songs/song-1/audio","sharePath":null,"liked":false,"saved":true,"likes":0}
        """)
        let adapted = try song.playbackSong(audioURL: URL(fileURLWithPath: "/tmp/protected.mp3"))
        XCTAssertEqual(adapted.defaultAsset?.lyrics.first?.text, "Actually sung")
        XCTAssertEqual(adapted.defaultAsset?.confidence.beats, .unavailable)
        XCTAssertTrue(adapted.defaultAsset?.beats.isEmpty == true)
        XCTAssertEqual(adapted.defaultAsset?.audioUrl.scheme, "file")
    }
    func testQueuedIsTheOnlyCancellableJobAndFutureStatesStayVisible() throws {
        let jobs: CreatorJobs = try decode("""
        {"jobs":[{"id":"1","state":"queued"},{"id":"2","state":"running"},{"id":"3","state":"future_state"}]}
        """)
        XCTAssertTrue(jobs.jobs[0].canCancel)
        XCTAssertFalse(jobs.jobs[1].canCancel)
        XCTAssertFalse(jobs.jobs[2].canCancel)
        XCTAssertFalse(jobs.jobs[2].isTerminal)
    }
    func testServerReadyJobCommentsBlocksAndNumericExpiry() throws {
        let jobs: CreatorJobs = try decode("""
        {"jobs":[{"id":"render","state":"ready","error":null,"brief":{
        "title":"Home","idea":"Returning home","lyrics":"Home again","caption":"Warm piano",
        "language":"en","duration":90,"bpm":80,"key":"C major"}}]}
        """)
        XCTAssertEqual(jobs.jobs.first?.title,"Home")
        XCTAssertEqual(jobs.jobs.first?.songId,"render")
        XCTAssertTrue(jobs.jobs.first?.isTerminal == true)
        let comment: CreatorComment = try decode("""
        {"id":"comment","text":"Beautiful","author":"Listener","state":"approved","mine":false}
        """)
        XCTAssertEqual(comment.author,"Listener")
        let blocks: CreatorBlocks = try decode("{\"accounts\":[{\"id\":\"blocked\",\"name\":\"Listener\"}]}")
        XCTAssertEqual(blocks.blocks.count,1)
        let billing: CreatorBilling = try decode("""
        {"accountToken":"00000000-0000-4000-8000-000000000001","products":[],
        "entitlement":{"tier":"creator","state":"active","expiresAt":1791507600,"provider":"apple","environment":"test"},
        "capabilities":{"apple":{"purchase":false,"restore":true,"reason":"manage_existing_subscription"}}}
        """)
        XCTAssertEqual(billing.entitlement.expiresAt,1791507600)
    }
    func testUnknownRenderResponseCannotBeTreatedAsAcknowledgement() throws {
        let wrapped: CreatorJobReceipt = try decode("{\"job\":{\"id\":\"job-1\",\"state\":\"queued\"}}")
        let direct: CreatorJobReceipt = try decode("{\"id\":\"job-1\",\"state\":\"queued\"}")
        XCTAssertEqual(wrapped.job.id, direct.job.id)
        for body in ["{}", "{\"detail\":\"temporary_error\"}", "{\"id\":\"\",\"state\":\"queued\"}"] {
            XCTAssertThrowsError(try decode(body) as CreatorJobReceipt)
        }
    }
    func testAuthorizedMediaCannotSendCredentialsToAnotherOrigin() throws {
        XCTAssertEqual(try CreatorAPI.mediaURL("/creator/api/songs/a/audio").host, "musia.lazying.art")
        for value in ["https://evil.test/creator/audio", "http://musia.lazying.art/creator/audio",
                      "https://musia.lazying.art:444/creator/audio", "https://user@musia.lazying.art/creator/audio",
                      "file:///creator/audio", "/api/v1/audio"] {
            XCTAssertThrowsError(try CreatorAPI.mediaURL(value), value)
        }
        XCTAssertEqual(try CreatorAPI.segment("a/b?c"), "a%2Fb%3Fc")
        XCTAssertThrowsError(try CreatorAPI.segment(".."))
    }
    private func decode<T: Decodable>(_ json: String) throws -> T {
        try JSONDecoder().decode(T.self, from: Data(json.utf8))
    }
    private func renderableBrief() -> CreatorBrief {
        var brief = CreatorBrief()
        brief.title = "Song"; brief.lyrics = "Line"; brief.caption = "Piano"
        return brief
    }
}
