import Foundation

public struct LyricPart: Equatable, Sendable {
    public let text: String
    public let start: Double?
    public let end: Double?

    public func isActive(at time: Double) -> Bool {
        guard let start, let end else { return false }
        return time >= start && time < end
    }
}

public struct LyricRendering: Sendable {
    public let parts: [LyricPart]
    public let hasMatchedTokens: Bool

    public init(line: LyricLine) {
        let fallback = [LyricPart(text: line.text, start: nil, end: nil)]
        var result: [LyricPart] = []
        var cursor = line.text.startIndex
        for token in line.tokens {
            guard !token.text.isEmpty,
                  let range = line.text.range(of: token.text, range: cursor..<line.text.endIndex) else {
                parts = fallback; hasMatchedTokens = false
                return
            }
            if cursor < range.lowerBound {
                result.append(LyricPart(text: String(line.text[cursor..<range.lowerBound]), start: nil, end: nil))
            }
            // Always use the original substring, preserving whitespace, punctuation and graphemes.
            result.append(LyricPart(text: String(line.text[range]), start: token.start, end: token.end))
            cursor = range.upperBound
        }
        if cursor < line.text.endIndex {
            result.append(LyricPart(text: String(line.text[cursor...]), start: nil, end: nil))
        }
        parts = result.isEmpty ? fallback : result
        hasMatchedTokens = !line.tokens.isEmpty
    }
}
