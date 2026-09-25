import XCTest
@testable import MusiaCore

final class LiveContractTests: XCTestCase {
    func testLiveCatalogAndAyaContractWhenExplicitlyEnabled() async throws {
        try XCTSkipUnless(ProcessInfo.processInfo.environment["MUSIA_LIVE_API"] == "1", "Opt-in public network test")
        let api = APIClient()
        let items = try await api.library()
        XCTAssertTrue(items.contains { $0.id == "first-pulse" })
        let pulse = try await api.song(id: "first-pulse")
        XCTAssertEqual(pulse.defaultAsset?.chords.map(\.name), ["Em", "Am", "Em", "Am"])
        let aya = try await api.song(id: "aya-chan-hikari-ame")
        XCTAssertFalse(aya.assets.isEmpty)
        for asset in aya.assets {
            for line in asset.lyrics {
                let rendering = LyricRendering(line: line)
                XCTAssertEqual(rendering.parts.map(\.text).joined(), line.text)
            }
        }
        let lessons = try await api.lessons()
        XCTAssertTrue(lessons.contains { $0.exerciseId == "first-pulse" })
    }
}
