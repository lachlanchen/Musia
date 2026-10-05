import XCTest
@testable import MusiaCore

final class BeginnerPracticeTests: XCTestCase {
    func testKnownEqualTemperamentPitches() {
        XCTAssertEqual(BeginnerPractice.frequency(5), 440, accuracy: 0.000001)
        XCTAssertEqual(BeginnerPractice.frequency(0), 261.625565, accuracy: 0.00001)
        XCTAssertEqual(BeginnerPractice.frequency(7), BeginnerPractice.frequency(0) * 2, accuracy: 0.000001)
        XCTAssertEqual(BeginnerPractice.noteNames.count, BeginnerPractice.syllables.count)
    }
    func testOnlyFirstAnswerCounts() {
        var round = PitchRound(targets: [2, 0])
        round.next()
        XCTAssertEqual(round.index, 0)
        round.choose(1); round.choose(2)
        XCTAssertEqual(round.correct, 0)
        XCTAssertEqual(round.answered, 1)
        round.next(); round.choose(0)
        XCTAssertEqual(round.correct, 1)
        XCTAssertTrue(round.finished)
        round.next()
        XCTAssertEqual(round.index, 1)
    }
    func testReferenceAudioHasExactDurationAndNoClipping() {
        XCTAssertEqual(BeginnerPractice.tone(0).count, 44 + 24000 * 2)
        for bpm in [40, 60, 120, 160] {
            let data = BeginnerPractice.metronome(bpm: bpm, chords: true)
            XCTAssertEqual(data.count, 44 + Int((8 * 60.0 / Double(bpm) * 24000).rounded()) * 2)
            XCTAssertEqual(String(data: data.prefix(4), encoding: .utf8), "RIFF")
            let pcm = Array(data.dropFirst(44))
            let peak = stride(from: 0, to: pcm.count, by: 2).map {
                abs(Int(Int16(bitPattern: UInt16(pcm[$0]) | UInt16(pcm[$0 + 1]) << 8)))
            }.max()!
            XCTAssertGreaterThan(peak, 1000)
            XCTAssertLessThan(peak, 20000)
        }
    }
}
