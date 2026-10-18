import AVFoundation
import AppKit
import SwiftUI
import XCTest
@testable import Musia
@testable import MusiaCore

private struct RubyLayoutSize: PreferenceKey {
    static let defaultValue = CGSize.zero
    static func reduce(value: inout CGSize, nextValue: () -> CGSize) { value = nextValue() }
}

final class MacPlaybackTests: XCTestCase {
    @MainActor
    func testMontereyRubyFallbackWrapsWithoutDroppingTokens() async throws {
        let words = ["wind", "over", "the", "mountains", "and", "sea"]
        func height(_ width: CGFloat) async throws -> CGFloat {
            var measured: CGSize?
            let view = NSHostingView(rootView: MontereyTokenFlow(count: words.count) { index in
                VStack { Text("reading").font(.caption); Text(words[index]).font(.title2) }
            }
            .background(GeometryReader { proxy in
                Color.clear.preference(key: RubyLayoutSize.self, value: proxy.size)
            })
            .onPreferenceChange(RubyLayoutSize.self) { measured = $0 }
            .frame(width: width, alignment: .topLeading))

            // Give preferences a window-backed layout lifecycle without showing UI.
            // A plain container prevents hosting-view size hints resizing the window.
            let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: width, height: 700),
                                  styleMask: .borderless, backing: .buffered, defer: false)
            window.isReleasedWhenClosed = false
            let container = NSView(frame: NSRect(x: 0, y: 0, width: width, height: 700))
            window.contentView = container
            view.frame = container.bounds
            view.autoresizingMask = [.width, .height]
            container.addSubview(view)
            defer {
                view.removeFromSuperview()
                window.contentView = nil
                window.close()
            }
            XCTAssertFalse(window.isVisible)
            XCTAssertFalse(window.isKeyWindow)
            XCTAssertTrue(view.window === window)

            var previous: CGSize?
            var stablePasses = 0
            var settled = false
            for _ in 0..<20 {
                view.layoutSubtreeIfNeeded()
                try await Task.sleep(nanoseconds: 100_000_000)
                if let current = measured, current == previous,
                   abs(current.width - width) < 0.5, current.height > 20 {
                    stablePasses += 1
                } else { stablePasses = 0 }
                previous = measured
                if stablePasses >= 3 { settled = true; break }
            }
            let fitting = view.fittingSize
            print("Musia ruby layout: assigned=\(width) rendered=\(String(describing: measured)) fitting=\(fitting) settled=\(settled)")
            let size = try XCTUnwrap(settled ? measured : nil,
                                    "Window-backed ruby layout did not settle at its assigned width")
            XCTAssertFalse(window.isVisible)
            XCTAssertFalse(window.isKeyWindow)
            XCTAssertEqual(size.width, width, accuracy: 0.5)
            XCTAssertTrue(size.height.isFinite)
            XCTAssertGreaterThan(size.height, 20)
            XCTAssertLessThan(size.height, 600)
            return size.height
        }
        let wide = try await height(800)
        let narrow = try await height(180)
        XCTAssertGreaterThan(narrow, wide)
    }

    @MainActor
    func testBeginnerReferenceAudioAndMetronomeClock() async throws {
        let sound = PracticeSound()
        defer { sound.stop() }
        XCTAssertTrue(sound.play(BeginnerPractice.tone(0)))
        try await waitFor { sound.time > 0.2 }
        try await waitFor { !sound.playing }
        XCTAssertTrue(sound.play(BeginnerPractice.metronome(bpm: 120, chords: true), loop: true))
        try await waitFor { sound.time > 2.1 }
        XCTAssertEqual(Int(sound.time / 0.5) / 4, 1, "Am starts at the fifth beat")
        sound.stop()
        XCTAssertFalse(sound.playing)
    }
    @MainActor
    private func waitFor(_ condition: () -> Bool) async throws {
        for _ in 0..<150 {
            if condition() { return }
            try await Task.sleep(nanoseconds: 100_000_000)
        }
        XCTFail("Player state timed out")
    }

    @MainActor
    func testLocalPlaybackSpeedSeekAndLoop() async throws {
        let player = PlaybackController(history: LocalStore())
        defer { player.pause(); player.setRate(1); player.setMode(.listen) }
        player.open(id: FirstPulse.id, localExercise: true)
        try await waitFor { player.ready || player.issue != nil }
        XCTAssertNil(player.issue)
        XCTAssertTrue(player.ready)
        XCTAssertEqual(player.duration, 22, accuracy: 0.05)
        player.setRate(0.5)
        player.play()
        try await waitFor { player.position > 0.3 }
        XCTAssertTrue(player.isPlaying)
        player.pause()
        let stopped = player.position
        try await Task.sleep(nanoseconds: 300_000_000)
        XCTAssertEqual(player.position, stopped, accuracy: 0.1)
        player.seek(to: 6)
        try await waitFor { !player.seeking }
        XCTAssertEqual(player.position, 6, accuracy: 0.05)
        player.setLoop(start: 4, end: 5)
        player.setRate(2)
        player.play()
        try await Task.sleep(nanoseconds: 1_500_000_000)
        XCTAssertGreaterThanOrEqual(player.position, 3.95)
        XCTAssertLessThan(player.position, 5.2)
        player.pause()
        player.clearLoop()
        XCTAssertNil(player.loop)
        player.setMode(.tap)
        player.tap()
        XCTAssertNil(player.tapFeedback, "Paused taps must not be graded")
    }

    @MainActor
    func testHistorySurvivesStoreReopen() async throws {
        let history = LocalStore()
        let player = PlaybackController(history: history)
        defer { player.pause() }
        player.open(id: FirstPulse.id, localExercise: true)
        try await waitFor { player.ready || player.issue != nil }
        XCTAssertNil(player.issue)
        player.play()
        try await waitFor { player.position > 1 }
        player.pause()
        XCTAssertFalse(history.records.isEmpty)
        XCTAssertEqual(LocalStore().records.count, history.records.count)
        let data = try history.export()
        XCTAssertNotNil(try JSONSerialization.jsonObject(with: data))
    }

    @MainActor
    func testRemoteSongPlayback() async throws {
        guard ProcessInfo.processInfo.environment["MUSIA_LIVE_TESTS"] == "1" else {
            throw XCTSkip("Set MUSIA_LIVE_TESTS=1 for the real catalog/audio test")
        }
        let items = try await APIClient().library()
        let item = try XCTUnwrap(items.first { $0.id == "aya-chan-hikari-ame" })
        let song = try await APIClient().song(id: item.id)
        for asset in song.assets {
            XCTAssertEqual(Set(asset.displayLyricTracks.map { LyricLanguages.key($0.language) }), Set(["en", "zh", "ja"]))
            for language in ["zh", "ja"] {
                let track = try XCTUnwrap(asset.displayLyricTracks.first { LyricLanguages.key($0.language) == language })
                XCTAssertTrue(track.lines.flatMap(\.tokens).contains { !($0.reading ?? "").isEmpty })
            }
        }
        let player = PlaybackController(history: LocalStore())
        defer { player.pause() }
        player.open(id: item.id)
        try await waitFor { player.ready || player.issue != nil }
        XCTAssertNil(player.issue)
        XCTAssertTrue(player.ready)
        player.play()
        try await waitFor { player.position > 0.25 || player.issue != nil }
        XCTAssertNil(player.issue)
        XCTAssertGreaterThan(player.position, 0.25)
    }
}
