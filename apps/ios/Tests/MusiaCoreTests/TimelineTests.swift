import XCTest
@testable import MusiaCore

final class TimelineTests: XCTestCase {
    private let phrases = [
        Phrase(id: "a", start: 1, end: 3, text: "A"),
        Phrase(id: "b", start: 3, end: 4, text: "B"),
        Phrase(id: "c", start: 5, end: 7, text: "C")
    ]

    func testHalfOpenIntervalsAndGaps() {
        XCTAssertNil(Timeline.current(in: phrases, at: 0))
        XCTAssertEqual(Timeline.current(in: phrases, at: 1)?.id, "a")
        XCTAssertEqual(Timeline.current(in: phrases, at: 3)?.id, "b")
        XCTAssertNil(Timeline.current(in: phrases, at: 4))
        XCTAssertNil(Timeline.current(in: phrases, at: 7))
        XCTAssertNil(Timeline.current(in: phrases, at: .nan))
        XCTAssertEqual(Timeline.next(in: phrases, at: 3)?.id, "c")
        XCTAssertEqual(Timeline.next(in: phrases, at: 4)?.id, "c")
        XCTAssertNil(Timeline.next(in: phrases, at: 8))
    }

    func testLoopValidationAndSeekBoundaries() throws {
        XCTAssertNil(LoopRange(start: 3, end: 2, duration: 10))
        XCTAssertNil(LoopRange(start: -1, end: 2, duration: 10))
        XCTAssertNil(LoopRange(start: 0, end: 11, duration: 10))
        XCTAssertNil(LoopRange(start: 0, end: 0.01, duration: 10))
        XCTAssertNil(LoopRange(start: .nan, end: 2, duration: 10))
        let loop = try XCTUnwrap(LoopRange(start: 2, end: 4, duration: 10))
        XCTAssertEqual(Timeline.clampedSeek(4, duration: 10, loop: loop), 2)
        XCTAssertEqual(Timeline.clampedSeek(1, duration: 10, loop: loop), 2)
        XCTAssertEqual(Timeline.clampedSeek(3, duration: 10, loop: loop), 3)
        XCTAssertEqual(Timeline.clampedSeek(.nan, duration: 10, loop: loop), 2)
        XCTAssertEqual(Timeline.clampedSeek(11, duration: 10, loop: nil), 10)
        XCTAssertEqual(Timeline.clampedSeek(-2, duration: 10, loop: nil), 0)
    }

    func testRateLimits() {
        XCTAssertEqual(Timeline.clampedRate(0), 0.25)
        XCTAssertEqual(Timeline.clampedRate(3), 2)
        XCTAssertEqual(Timeline.clampedRate(.infinity), 1)
    }

    func testTapOffsetUsesPlaybackRateAndRealBeatsOnly() throws {
        let beats = [Beat(time: 1), Beat(time: 2), Beat(time: 3)]
        let slow = try XCTUnwrap(TapEvaluator.evaluate(time: 1.1, rate: 0.5, beats: beats))
        XCTAssertEqual(slow.offsetMilliseconds, 200, accuracy: 0.001)
        let fast = try XCTUnwrap(TapEvaluator.evaluate(time: 1.9, rate: 2, beats: beats))
        XCTAssertEqual(fast.offsetMilliseconds, -50, accuracy: 0.001)
        XCTAssertNil(TapEvaluator.evaluate(time: 9, rate: 1, beats: beats))
        XCTAssertNil(TapEvaluator.evaluate(time: 1, rate: 0, beats: beats))
        XCTAssertNil(TapEvaluator.evaluate(time: .nan, rate: 1, beats: beats))
        XCTAssertNil(TapEvaluator.evaluate(time: 1, rate: 1, beats: []))
        XCTAssertNil(TapEvaluator.evaluate(time: 0.99, rate: 1, beats: beats))
        XCTAssertNil(TapEvaluator.evaluate(time: 3.01, rate: 1, beats: beats))
        XCTAssertNotNil(TapEvaluator.evaluate(time: 1, rate: 1, beats: beats))
        XCTAssertNotNil(TapEvaluator.evaluate(time: 3, rate: 1, beats: beats))
        let loop = LoopRange(start: 1, end: 2, duration: 3)
        XCTAssertNil(TapEvaluator.evaluate(time: 1.9, rate: 1, beats: beats, loop: loop))
    }

    func testBeatPulseDecaysInWallTimeAndDoesNotInventBeats() {
        let beats = [Beat(time: 1), Beat(time: 2)]
        XCTAssertNil(Timeline.beatIndex(in: beats, at: 0.9))
        XCTAssertEqual(Timeline.beatIndex(in: beats, at: 2), 1)
        XCTAssertEqual(Timeline.pulse(in: beats, at: 1, rate: 1), 1)
        XCTAssertEqual(Timeline.pulse(in: beats, at: 1.05, rate: 0.5), 0.5, accuracy: 0.001)
        XCTAssertEqual(Timeline.pulse(in: beats, at: 3, rate: 1), 0)
        XCTAssertEqual(Timeline.pulse(in: [], at: 1, rate: 1), 0)
    }
}
