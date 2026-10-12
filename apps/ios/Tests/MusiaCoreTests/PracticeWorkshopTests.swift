import XCTest
@testable import MusiaCore

final class PracticeWorkshopTests: XCTestCase {
    func testWorkshopBoundsAndAudioClock() {
        let plan = PracticePlan(bpm: 120, beats: 3, subdivision: 2, progression: 2, pattern: .picking)
        XCTAssertEqual(plan.duration, 6)
        XCTAssertEqual(plan.chord(at: 0), "C")
        XCTAssertEqual(plan.chord(at: 1.5), "Am")
        XCTAssertEqual(plan.chord(at: 3), "F")
        XCTAssertEqual(plan.chord(at: 4.5), "G")
        XCTAssertEqual(plan.chord(at: 6), "C")
        XCTAssertEqual(plan.beat(at: 0.5), 1)
        XCTAssertEqual(plan.beat(at: 1.5), 0)
        XCTAssertEqual(plan.audio().count, 44 + 6 * 24000 * 2)
        let bounded = PracticePlan(bpm: 0, beats: 100, subdivision: 0, progression: -1)
        XCTAssertEqual(bounded.bpm, 30); XCTAssertEqual(bounded.beats, 4)
        XCTAssertNil(bounded.chord(at: .nan))
    }
    func testTempoAndTapFeedbackAcrossLoop() {
        var tempo = TapTempo()
        XCTAssertNil(tempo.tap(at: 0)); XCTAssertNil(tempo.tap(at: 0.5)); XCTAssertNil(tempo.tap(at: 1))
        XCTAssertEqual(tempo.tap(at: 1.5), 120)
        XCTAssertNil(tempo.tap(at: 1.51))
        XCTAssertNil(tempo.tap(at: 6))
        var feedback = RhythmFeedback()
        feedback.tap(playback: 7.01, monotonic: 7, bpm: 60)
        feedback.tap(playback: 0.01, monotonic: 8, bpm: 60)
        feedback.tap(playback: 1.01, monotonic: 9, bpm: 60)
        feedback.tap(playback: 2.01, monotonic: 10, bpm: 60)
        feedback.tap(playback: 2.02, monotonic: 10.01, bpm: 60)
        XCTAssertEqual(feedback.offsets.count, 4)
        XCTAssertEqual(feedback.averageOffset, 10, accuracy: 0.0001)
        XCTAssertEqual(feedback.inTimePercent(bpm: 60), 100)
    }
    func signal(_ hz: Double, count: Int = 2048) -> [Float] {
        (0..<count).map { i in
            let t = Double(i) / 16000
            return Float(0.2 * sin(2 * .pi * hz * t) + 0.08 * sin(4 * .pi * hz * t))
        }
    }
    func testPitchReferencesAndAbstention() {
        for hz in [82.4069, 130.8128, 261.6256, 440, 523.2511, 880] {
            XCTAssertEqual(PitchPractice.frequency(signal(hz)) ?? 0, hz, accuracy: hz * 0.005)
        }
        XCTAssertNil(PitchPractice.frequency([Float](repeating: 0, count: 2048)))
        XCTAssertNil(PitchPractice.frequency([Float](repeating: 0.3, count: 2048)))
        XCTAssertNil(PitchPractice.frequency([Float](repeating: .nan, count: 2048)))
        let result = PitchPractice.analyze(signal(261.6256, count: 48000), targetHz: 261.6256)
        XCTAssertEqual(result?.inTunePercent, 100)
        XCTAssertEqual(result?.medianCents ?? 999, 0, accuracy: 3)
        XCTAssertEqual(PitchPractice.analyze(signal(293.6648, count: 48000), targetHz: 261.6256)?.inTunePercent, 0)
        XCTAssertNil(PitchPractice.analyze(signal(440, count: 4096), targetHz: 440))
    }
}
