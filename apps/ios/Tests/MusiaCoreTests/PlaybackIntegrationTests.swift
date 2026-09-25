#if canImport(UIKit) && canImport(Musia)
import AVFoundation
import XCTest
@testable import Musia
@testable import MusiaCore

final class PlaybackIntegrationTests: XCTestCase {
    @MainActor
    func testMinimalPlayerWithActiveAudioSession() async throws {
        let session = AVAudioSession.sharedInstance()
        var activationError: NSError?
        do {
            try session.setCategory(.playback, mode: .default, policy: .longFormAudio)
            try session.setActive(true)
        } catch { activationError = error as NSError }
        defer { try? session.setActive(false, options: .notifyOthersOnDeactivation) }
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("musia-player-test.wav")
        try FirstPulse.wavData().write(to: url, options: .atomic)
        defer { try? FileManager.default.removeItem(at: url) }
        let item = AVPlayerItem(url: url)
        item.audioTimePitchAlgorithm = .spectral
        let player = AVPlayer(playerItem: item)
        defer { player.pause(); player.replaceCurrentItem(with: nil) }
        for _ in 0..<100 {
            if item.status != .unknown { break }
            try await Task.sleep(nanoseconds: 100_000_000)
        }
        let error = item.error as NSError?
        let diagnostic = "Bare player status \(item.status.rawValue); error \(String(describing: error)); underlying \(String(describing: error?.userInfo[NSUnderlyingErrorKey])); session activation \(String(describing: activationError)); route \(session.currentRoute); sample rate \(session.sampleRate)"
        XCTAssertNil(activationError, diagnostic)
        XCTAssertEqual(item.status, .readyToPlay, diagnostic)
        guard item.status == .readyToPlay else { return }
        player.playImmediately(atRate: 1)
        for _ in 0..<50 {
            if player.currentTime().seconds > 0.2 { break }
            try await Task.sleep(nanoseconds: 100_000_000)
        }
        XCTAssertGreaterThan(player.currentTime().seconds, 0.2, diagnostic)
    }

    @MainActor
    func testNativeFirstPulseReadyAndClock() async throws {
        let controller = PlaybackController(history: LocalStore())
        controller.open(id: FirstPulse.id, localExercise: true)
        for _ in 0..<100 {
            if controller.ready || controller.issue != nil { break }
            try await Task.sleep(nanoseconds: 100_000_000)
        }
        XCTAssertNil(controller.issue, controller.issue ?? "")
        XCTAssertTrue(controller.ready, controller.issue ?? "AVPlayer never became ready")
        guard controller.ready else { return }
        controller.play()
        defer { controller.pause() }
        for _ in 0..<50 {
            if controller.position > 0.2 || controller.issue != nil { break }
            try await Task.sleep(nanoseconds: 100_000_000)
        }
        XCTAssertNil(controller.issue, controller.issue ?? "")
        XCTAssertGreaterThan(controller.position, 0.2, "The AVPlayer media clock must advance")
        controller.pause()
        controller.setMode(.tap)
        controller.tap()
        XCTAssertNil(controller.tapFeedback)
    }

    @MainActor
    func testNativeDecoderAcceptsGeneratedWAV() async throws {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("musia-decoder-test.wav")
        try FirstPulse.wavData().write(to: url, options: .atomic)
        defer { try? FileManager.default.removeItem(at: url) }
        let asset = AVURLAsset(url: url)
        do {
            let playable = try await asset.load(.isPlayable)
            let duration = try await asset.load(.duration)
            XCTAssertTrue(playable)
            XCTAssertEqual(duration.seconds, 22, accuracy: 0.001)
        } catch {
            let nsError = error as NSError
            XCTFail("Native WAV decode: \(nsError.domain) \(nsError.code), underlying \(String(describing: nsError.userInfo[NSUnderlyingErrorKey]))")
        }
    }
}
#endif
