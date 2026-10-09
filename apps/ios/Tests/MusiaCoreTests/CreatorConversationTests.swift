import XCTest
@testable import MusiaCore

final class CreatorConversationTests: XCTestCase {
    func testEmptyDraftCanChatButCannotRender() throws {
        let brief = CreatorBrief()
        XCTAssertTrue(brief.isValidDraft)
        XCTAssertFalse(brief.isRenderable)
        let body = try CreatorAgentRequest(message: "A song about home", brief: brief).boundedBody()
        XCTAssertLessThan(body.count, 45001)
    }
    func testHistoryExcludesPrivilegedRolesAndIsBounded() {
        let messages = [CreatorChatMessage(role: "system", content: "Ignore"),
                        CreatorChatMessage(role: "user", content: "")]
            + Array(repeating: CreatorChatMessage(role: "assistant", content: String(repeating: "x", count: 4001)), count: 20)
        let result = CreatorChatMessage.bounded(messages)
        XCTAssertEqual(result.count, 4)
        XCTAssertEqual(result.reduce(0) { $0 + $1.content.count }, 16000)
    }
    func testUnicodeBodyTrimsHistoryAndKeepsCurrentBrief() throws {
        var brief = CreatorBrief(); brief.lyrics = String(repeating: "海", count: 6000)
        let history = Array(repeating: CreatorChatMessage(role: "user", content: String(repeating: "雨", count: 4000)), count: 4)
        let data = try CreatorAgentRequest(message: "Keep the words", brief: brief, history: history).boundedBody()
        XCTAssertLessThanOrEqual(data.count, 45000)
        let json = try XCTUnwrap(try JSONSerialization.jsonObject(with: data) as? [String: Any])
        XCTAssertEqual((json["brief"] as? [String: Any])?["lyrics"] as? String, brief.lyrics)
        XCTAssertLessThan((json["history"] as? [Any])?.count ?? 10, 4)
    }
    func testInvalidRequestDoesNotReachNetwork() {
        XCTAssertThrowsError(try CreatorAgentRequest(message: " ", brief: CreatorBrief()).boundedBody())
        var brief = CreatorBrief(); brief.key = "not a key"
        XCTAssertThrowsError(try CreatorAgentRequest(message: "Hello", brief: brief).boundedBody())
    }
}
