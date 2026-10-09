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
}
