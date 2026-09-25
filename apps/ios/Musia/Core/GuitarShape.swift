import Foundation

public struct GuitarShape: Equatable, Sendable {
    public let name: String
    public let frets: [Int?]
    public let fingers: [Int?]
    public let accessibleText: String

    public static func known(_ chord: String) -> GuitarShape? {
        switch chord {
        case "Em":
            return GuitarShape(name: "Em", frets: [0, 2, 2, 0, 0, 0], fingers: [nil, 2, 3, nil, nil, nil],
                accessibleText: "Em, standard tuning, low E to high E: low E open; A fret 2, finger 2; D fret 2, finger 3; G open; B open; high E open.")
        case "Am":
            return GuitarShape(name: "Am", frets: [nil, 0, 2, 2, 1, 0], fingers: [nil, nil, 2, 3, 1, nil],
                accessibleText: "Am, standard tuning, low E to high E: low E muted; A open; D fret 2, finger 2; G fret 2, finger 3; B fret 1, finger 1; high E open.")
        default: return nil
        }
    }
}
