import Foundation

public struct GuitarBarre: Equatable, Sendable {
    public let fret: Int
    public let firstString: Int
    public let lastString: Int
    public let finger: Int
}

public struct GuitarShape: Equatable, Sendable {
    public let name: String
    public let frets: [Int?]
    public let fingers: [Int?]
    public let barres: [GuitarBarre]
    public var startFret: Int { (frets.compactMap { $0 }.max() ?? 0) <= 4 ? 1 : (frets.compactMap { $0 }.filter { $0 > 0 }.min() ?? 1) }
    public let fretCount = 4
    public var accessibleText: String {
        let strings = ["low E", "A", "D", "G", "B", "high E"]
        let notes = strings.indices.map { i -> String in
            guard let fret = frets[i] else { return "\(strings[i]) muted" }
            return fret == 0 ? "\(strings[i]) open" : "\(strings[i]) fret \(fret), finger \(fingers[i] ?? 0)"
        }
        let bars = barres.map { "Barre fret \($0.fret), finger \($0.finger), \(strings[$0.firstString]) to \(strings[$0.lastString])." }
        return "\(name), standard tuning, low E on the left to high E on the right: " + notes.joined(separator: "; ") + ". " + bars.joined(separator: " ")
    }

    public static func known(_ chord: String) -> GuitarShape? {
        let label = chord.trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: "\u{266f}", with: "#").replacingOccurrences(of: "\u{266d}", with: "b")
            .replacingOccurrences(of: ":maj", with: "").replacingOccurrences(of: ":min", with: "m")
        let minor = label.hasSuffix("m")
        let root = minor ? String(label.dropLast()) : label
        let aliases = ["Db": "C#", "D#": "Eb", "Gb": "F#", "G#": "Ab", "A#": "Bb", "Cb": "B", "B#": "C", "E#": "F", "Fb": "E"]
        let key = (aliases[root] ?? root) + (minor ? "m" : "")
        guard let row = shapes[key] else { return nil }
        return GuitarShape(name: label, frets: row[0].map { $0 < 0 ? nil : $0 },
                           fingers: row[1].map { $0 == 0 ? nil : $0 },
                           barres: row.dropFirst(2).map { GuitarBarre(fret: $0[0], firstString: $0[1], lastString: $0[2], finger: $0[3]) })
    }

    // BEGIN GENERATED SHAPES
    private static let shapes: [String: [[Int]]] = [
        "A": [[-1, 0, 2, 2, 2, 0], [0, 0, 1, 2, 3, 0]],
        "Am": [[-1, 0, 2, 2, 1, 0], [0, 0, 2, 3, 1, 0]],
        "Bb": [[-1, 1, 3, 3, 3, 1], [0, 1, 3, 3, 3, 1], [1, 1, 5, 1], [3, 2, 4, 3]],
        "Bbm": [[-1, 1, 3, 3, 2, 1], [0, 1, 3, 4, 2, 1], [1, 1, 5, 1]],
        "B": [[-1, 2, 4, 4, 4, 2], [0, 1, 3, 3, 3, 1], [2, 1, 5, 1], [4, 2, 4, 3]],
        "Bm": [[-1, 2, 4, 4, 3, 2], [0, 1, 3, 4, 2, 1], [2, 1, 5, 1]],
        "C": [[-1, 3, 2, 0, 1, 0], [0, 3, 2, 0, 1, 0]],
        "Cm": [[-1, 3, 5, 5, 4, 3], [0, 1, 3, 4, 2, 1], [3, 1, 5, 1]],
        "C#": [[-1, 4, 6, 6, 6, 4], [0, 1, 3, 3, 3, 1], [4, 1, 5, 1], [6, 2, 4, 3]],
        "C#m": [[-1, 4, 6, 6, 5, 4], [0, 1, 3, 4, 2, 1], [4, 1, 5, 1]],
        "D": [[-1, -1, 0, 2, 3, 2], [0, 0, 0, 1, 3, 2]],
        "Dm": [[-1, -1, 0, 2, 3, 1], [0, 0, 0, 2, 3, 1]],
        "Eb": [[-1, 6, 8, 8, 8, 6], [0, 1, 3, 3, 3, 1], [6, 1, 5, 1], [8, 2, 4, 3]],
        "Ebm": [[-1, 6, 8, 8, 7, 6], [0, 1, 3, 4, 2, 1], [6, 1, 5, 1]],
        "E": [[0, 2, 2, 1, 0, 0], [0, 2, 3, 1, 0, 0]],
        "Em": [[0, 2, 2, 0, 0, 0], [0, 2, 3, 0, 0, 0]],
        "F": [[1, 3, 3, 2, 1, 1], [1, 3, 4, 2, 1, 1], [1, 0, 5, 1]],
        "Fm": [[1, 3, 3, 1, 1, 1], [1, 3, 4, 1, 1, 1], [1, 0, 5, 1]],
        "F#": [[2, 4, 4, 3, 2, 2], [1, 3, 4, 2, 1, 1], [2, 0, 5, 1]],
        "F#m": [[2, 4, 4, 2, 2, 2], [1, 3, 4, 1, 1, 1], [2, 0, 5, 1]],
        "G": [[3, 2, 0, 0, 0, 3], [3, 2, 0, 0, 0, 4]],
        "Gm": [[3, 5, 5, 3, 3, 3], [1, 3, 4, 1, 1, 1], [3, 0, 5, 1]],
        "Ab": [[4, 6, 6, 5, 4, 4], [1, 3, 4, 2, 1, 1], [4, 0, 5, 1]],
        "Abm": [[4, 6, 6, 4, 4, 4], [1, 3, 4, 1, 1, 1], [4, 0, 5, 1]],
    ]
    // END GENERATED SHAPES
}
