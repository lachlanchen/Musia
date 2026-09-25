import XCTest
@testable import MusiaCore

final class LyricRenderingTests: XCTestCase {
    private func line(_ text: String, tokens: [String]) throws -> LyricLine {
        let payload: [String: Any] = [
            "id": "line", "start": 0, "end": 20, "text": text,
            "tokens": tokens.enumerated().map { index, token in
                ["text": token, "start": Double(index), "end": Double(index + 1)] as [String: Any]
            }
        ]
        return try JSONDecoder().decode(LyricLine.self, from: JSONSerialization.data(withJSONObject: payload))
    }

    func testAyaTokensWithoutTrailingSpacesPreserveOriginalLine() throws {
        let original = "Lay, ay, lay away."
        let rendering = LyricRendering(line: try line(original, tokens: ["Lay", ",", "ay", ",", "lay", "away", "."]))
        XCTAssertTrue(rendering.hasMatchedTokens)
        XCTAssertEqual(rendering.parts.map(\.text).joined(), original)
        XCTAssertEqual(rendering.parts.filter { $0.isActive(at: 2.5) }.map(\.text), ["ay"])
        XCTAssertTrue(rendering.parts.filter { $0.text == " " }.allSatisfy { $0.start == nil })
    }

    func testOneUnmatchedTokenRemovesAllHighlighting() throws {
        let rendering = LyricRendering(line: try line("Lay, ay", tokens: ["Lay", ",", "missing"]))
        XCTAssertFalse(rendering.hasMatchedTokens)
        XCTAssertEqual(rendering.parts.count, 1)
        XCTAssertEqual(rendering.parts.first?.text, "Lay, ay")
        XCTAssertFalse(rendering.parts[0].isActive(at: 0.5))
    }

    func testRepeatedWordsUseSequentialRanges() throws {
        let rendering = LyricRendering(line: try line("go  go\ngo!", tokens: ["go", "go", "go"]))
        XCTAssertEqual(rendering.parts.map(\.text).joined(), "go  go\ngo!")
        XCTAssertEqual(rendering.parts.filter { $0.isActive(at: 2.5) }.count, 1)
        XCTAssertFalse(rendering.parts.last!.isActive(at: 2.5))
    }

    func testEmptyTokensAndUnicodeText() throws {
        let original = "\u{4f60}\u{597d}, world"
        let rendering = LyricRendering(line: try line(original, tokens: ["\u{4f60}", "\u{597d}", "world"]))
        XCTAssertEqual(rendering.parts.map(\.text).joined(), original)
        XCTAssertTrue(rendering.hasMatchedTokens)
        XCTAssertFalse(LyricRendering(line: try line(original, tokens: [""])).hasMatchedTokens)
        XCTAssertEqual(LyricRendering(line: try line(original, tokens: [])).parts.first?.text, original)
    }
}
