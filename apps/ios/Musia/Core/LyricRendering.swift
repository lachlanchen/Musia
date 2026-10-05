import Foundation

public struct LyricPart: Equatable, Sendable {
    public let text: String
    public let start: Double?
    public let end: Double?
    public var reading: String? = nil

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
            result.append(LyricPart(text: String(line.text[range]), start: token.start, end: token.end, reading: token.reading))
            cursor = range.upperBound
        }
        if cursor < line.text.endIndex {
            result.append(LyricPart(text: String(line.text[cursor...]), start: nil, end: nil))
        }
        parts = result.isEmpty ? fallback : result
        hasMatchedTokens = !line.tokens.isEmpty
    }
}

public enum LyricLanguages {
    public static let defaults = "en,zh,ja"

    public static func key(_ code: String) -> String {
        code.split(separator: "-").first.map(String.init) ?? code
    }

    public static func label(_ code: String) -> String {
        switch key(code) {
        case "en": return "English"
        case "zh": return "中文"
        case "ja": return "日本語"
        case "mul": return "Original"
        case "yue": return "粵語"
        default: return Locale.current.localizedString(forLanguageCode: code) ?? code
        }
    }

    public static func rank(_ code: String) -> Int {
        ["en", "zh", "ja", "mul", "yue"].firstIndex(of: key(code)) ?? 5
    }

    public static func selected(_ code: String, in preference: String) -> Bool {
        preference.split(separator: ",").contains(Substring(key(code)))
    }

    public static func setting(_ code: String, enabled: Bool, in preference: String) -> String {
        var values = Set(preference.split(separator: ",").map(String.init))
        if enabled { values.insert(key(code)) } else { values.remove(key(code)) }
        return values.sorted().joined(separator: ",")
    }
}
