import XCTest
@testable import MusiaCore

final class PracticeGuidanceTests: XCTestCase {
    func testExerciseInstructionsNeverLeakToOtherSongs() {
        for mode in PracticeMode.allCases {
            let other = PracticeGuidance.text(songID: "aya", mode: mode)
            XCTAssertFalse(other.contains("Em"))
            XCTAssertFalse(other.contains("Am"))
            XCTAssertFalse(other.contains("60 BPM"))
            XCTAssertFalse(other.contains("count-in"))
        }
        XCTAssertTrue(PracticeGuidance.text(songID: "first-pulse", mode: .play).contains("Em at 4"))
        XCTAssertTrue(PracticeGuidance.text(songID: "first-pulse", mode: .play).contains("Am at 8"))
    }

    func testConservativePhaseOutsideReferenceExercise() {
        XCTAssertEqual(PracticeGuidance.phase(songID: "aya", time: 0, playing: true, hasBeats: true),
                       "Reference pulses - downbeat unverified")
        XCTAssertEqual(PracticeGuidance.phase(songID: "aya", time: 5, playing: false, hasBeats: true), "Ready")
        XCTAssertEqual(PracticeGuidance.phase(songID: "first-pulse", time: 3.99, playing: true, hasBeats: true), "Count-in")
        XCTAssertEqual(PracticeGuidance.phase(songID: "first-pulse", time: 4, playing: true, hasBeats: true), "Bar 1 of 4")
        XCTAssertEqual(PracticeGuidance.phase(songID: "first-pulse", time: 20, playing: true, hasBeats: true), "Final chord fade")
    }

    func testOnlyKnownGuitarShapesWithCorrectStringOrder() throws {
        let em = try XCTUnwrap(GuitarShape.known("Em"))
        XCTAssertEqual(em.frets, [0, 2, 2, 0, 0, 0])
        XCTAssertEqual(em.fingers, [nil, 2, 3, nil, nil, nil])
        let am = try XCTUnwrap(GuitarShape.known("Am"))
        XCTAssertEqual(am.frets, [nil, 0, 2, 2, 1, 0])
        XCTAssertEqual(am.fingers, [nil, nil, 2, 3, 1, nil])
        XCTAssertTrue(am.accessibleText.contains("low E muted"))
        XCTAssertNil(GuitarShape.known("Em7"))
        XCTAssertEqual(GuitarShape.known("C")?.frets, [nil, 3, 2, 0, 1, 0])
    }

    func testAllCatalogChordsHaveExactTonesAndVisibleFrets() throws {
        let roots = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
        let tuning = [40, 45, 50, 55, 59, 64]
        for (pitch, root) in roots.enumerated() {
            for suffix in ["", "m"] {
                let shape = try XCTUnwrap(GuitarShape.known(root + suffix))
                let notes = shape.frets.enumerated().compactMap { index, fret in fret.map { (tuning[index] + $0) % 12 } }
                XCTAssertEqual(Set(notes), Set([pitch, (pitch + (suffix == "m" ? 3 : 4)) % 12, (pitch + 7) % 12]))
                XCTAssertEqual(notes.first, pitch)
                for fret in shape.frets.compactMap({ $0 }).filter({ $0 > 0 }) {
                    XCTAssertTrue((shape.startFret..<(shape.startFret + shape.fretCount)).contains(fret))
                }
            }
        }
        XCTAssertEqual(GuitarShape.known("Eb")?.startFret, 6)
        XCTAssertEqual(GuitarShape.known("Gm")?.startFret, 3)
        XCTAssertEqual(GuitarShape.known("F")?.barres.first?.lastString, 5)
        XCTAssertEqual(GuitarShape.known("B")?.barres.count, 2)
    }

    func testEnharmonicAliasesAndUnknownQualities() {
        for (alias, name) in [("Db", "C#"), ("G\u{266d}m", "F#m"), ("D#:min", "Ebm"), ("C:maj", "C")] {
            XCTAssertEqual(GuitarShape.known(alias)?.frets, GuitarShape.known(name)?.frets)
        }
        for name in ["", "N", "C7", "Cmaj7", "C/E", "H", "Em/G"] { XCTAssertNil(GuitarShape.known(name)) }
    }
}
