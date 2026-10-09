import Foundation
import XCTest
@testable import MusiaWatchProtocol

final class WatchProtocolTests: XCTestCase {
    func testSnapshotRoundtripAndFreshness() throws {
        let snapshot = WatchPlaybackSnapshot(selection: "song-a", title: "Home", chord: "Em", bpm: 80,
                                             position: 8, duration: 90, ready: true, issuedAt: 100)
        XCTAssertEqual(WatchPlaybackSnapshot.decode(try XCTUnwrap(snapshot.encoded())), snapshot)
        XCTAssertTrue(snapshot.fresh(at: 110))
        XCTAssertFalse(snapshot.fresh(at: 131))
        XCTAssertFalse(snapshot.fresh(at: 90))
    }
    func testRejectMalformedSnapshot() {
        var snapshot = WatchPlaybackSnapshot()
        snapshot.rate = .nan
        XCTAssertFalse(snapshot.valid)
        XCTAssertNil(snapshot.encoded())
        snapshot.rate = 1; snapshot.title = String(repeating: "x", count: 241)
        XCTAssertFalse(snapshot.valid)
        XCTAssertNil(WatchPlaybackSnapshot.decode(Data(repeating: 32, count: 8193)))
    }
    func testCommandCannotControlReplacementSongOrReplay() {
        var guarder = WatchCommandGuard()
        let command = WatchPlaybackCommand(action: .play, selection: "a", issuedAt: 100)
        XCTAssertFalse(guarder.accept(command, selection: "b", ready: true, now: 101))
        XCTAssertFalse(guarder.accept(command, selection: "a", ready: false, now: 101))
        XCTAssertTrue(guarder.accept(command, selection: "a", ready: true, now: 101))
        XCTAssertFalse(guarder.accept(command, selection: "a", ready: true, now: 102))
    }
    func testCommandBoundsAndExpiry() {
        XCTAssertFalse(WatchPlaybackCommand(action: .rate, selection: "a", value: 3, issuedAt: 100).valid(at: 101))
        XCTAssertFalse(WatchPlaybackCommand(action: .seek, selection: "a", value: -.infinity, issuedAt: 100).valid(at: 101))
        XCTAssertFalse(WatchPlaybackCommand(action: .play, selection: "a", issuedAt: 100).valid(at: 116))
        XCTAssertFalse(WatchPlaybackCommand(action: .pause, selection: "a", value: 1, issuedAt: 100).valid(at: 101))
        XCTAssertTrue(WatchPlaybackCommand(action: .rate, selection: "a", value: 0.25, issuedAt: 100).valid(at: 101))
    }
    func testRefreshDoesNotRequireSong() {
        var guarder = WatchCommandGuard()
        XCTAssertTrue(guarder.accept(WatchPlaybackCommand(action: .refresh, selection: "", issuedAt: 100),
                                     selection: "", ready: false, now: 101))
    }
}
