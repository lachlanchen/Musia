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
        XCTAssertNil(GuitarShape.known("C"))
    }
}
