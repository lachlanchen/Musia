#if DEBUG
import AppKit
import MusiaCore

// Explicit opt-in, app-scoped qualification. Never compiled into store releases.
@MainActor
enum MacReview {
    private static var started = false
    private static func wait(_ condition: () -> Bool) async throws {
        for _ in 0..<200 {
            if condition() { return }
            try await Task.sleep(for: .milliseconds(100))
        }
        throw NSError(domain: "MusiaReview", code: 1, userInfo: [NSLocalizedDescriptionKey: "Timed out"])
    }

    static func run(catalog: CatalogStore, history: LocalStore, player: PlaybackController,
                    navigation: MacNavigation, creator: CreatorStore) async {
        guard !started else { return }
        started = true
        let directory = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("Musia-Mac-Review", isDirectory: true)
        var checks: [String: Any] = [:]
        do {
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            try await wait { NSApp.windows.contains { $0.identifier?.rawValue == "main" || $0.title == "Musia" } }
            let window = NSApp.windows.first { $0.identifier?.rawValue == "main" || $0.title == "Musia" }!
            window.setFrame(NSRect(x: 0, y: 0, width: 1280, height: 800), display: true)
            await catalog.loadLibrary(force: true)
            guard !catalog.items.isEmpty, catalog.libraryError == nil else {
                throw NSError(domain: "MusiaReview", code: 2, userInfo: [NSLocalizedDescriptionKey: catalog.libraryError ?? "Empty catalog"])
            }
            checks["catalog_count"] = catalog.items.count
            try await capture(window, "01-library", directory)
            player.open(id: FirstPulse.id, localExercise: true)
            navigation.section = .practice
            try await wait { player.ready || player.issue != nil }
            guard player.ready else { throw NSError(domain: "MusiaReview", code: 3) }
            player.setMode(.play)
            player.seek(to: 6)
            try await wait { !player.seeking }
            try await capture(window, "02-guitar", directory)
            checks["guitar_reference"] = Timeline.current(in: player.asset?.chords ?? [], at: player.position)?.name
            player.play()
            try await wait { player.position > 6.4 }
            window.miniaturize(nil)
            let before = player.position
            try await Task.sleep(for: .seconds(2))
            checks["minimized_playback"] = player.position > before + 1
            window.deminiaturize(nil)
            player.pause()
            checks["persisted_sessions"] = LocalStore().records.count
            let song = catalog.items.first { $0.id == "aya-chan-hikari-ame" } ?? catalog.items[0]
            player.open(id: song.id)
            try await wait { player.ready || player.issue != nil }
            guard player.ready else {
                throw NSError(domain: "MusiaReview", code: 4, userInfo: [NSLocalizedDescriptionKey: player.issue ?? "Remote audio unavailable"])
            }
            player.play()
            try await wait { player.position > 0.5 }
            checks["remote_audio_clock"] = player.position
            checks["remote_song"] = song.id
            if let phrase = player.asset?.lyrics.first {
                player.seek(to: phrase.start + 0.5)
                try await wait { !player.seeking }
            }
            player.pause()
            try await capture(window, "03-song", directory)
            navigation.section = .lessons
            await catalog.loadLessons(force: true)
            checks["lesson_count"] = catalog.lessons.count
            try await capture(window, "04-lessons", directory)
            navigation.section = .settings
            try await capture(window, "05-settings", directory)
            checks["history_export_bytes"] = try history.export().count
            window.setContentSize(NSSize(width: 1040, height: 680))
            navigation.section = .practice
            try await capture(window, "06-minimum-window", directory)
            await creator.refresh()
            checks["creator_live_capabilities"] = creator.capabilities?.login == true
            // Isolated sentinel: never read or overwrite a real session in QA.
            let key = "review-sentinel-" + UUID().uuidString
            try CreatorKeychain.write("sentinel", key: key)
            checks["creator_keychain"] = try CreatorKeychain.read(String.self, key: key) == "sentinel"
            try CreatorKeychain.remove(key)
            checks["creator_keychain_removed"] = try CreatorKeychain.read(String.self, key: key) == nil
            navigation.section = .create
            try await capture(window, "07-creator", directory)
            navigation.section = .community
            try await capture(window, "08-community", directory)
            checks["passed"] = checks["minimized_playback"] as? Bool == true && !catalog.lessons.isEmpty
                && checks["creator_live_capabilities"] as? Bool == true
                && checks["creator_keychain"] as? Bool == true
                && checks["creator_keychain_removed"] as? Bool == true
        } catch {
            checks["passed"] = false
            checks["error"] = error.localizedDescription
        }
        player.pause(); player.setRate(1); player.setMode(.listen)
        checks["system"] = ProcessInfo.processInfo.operatingSystemVersionString
        if let data = try? JSONSerialization.data(withJSONObject: checks, options: [.prettyPrinted, .sortedKeys]) {
            try? data.write(to: directory.appendingPathComponent("result.json"), options: .atomic)
        }
        NSApp.terminate(nil)
    }

    private static func capture(_ window: NSWindow, _ name: String, _ directory: URL) async throws {
        try await Task.sleep(for: .seconds(2))
        guard let view = window.contentView?.superview, let bitmap = view.bitmapImageRepForCachingDisplay(in: view.bounds) else {
            throw NSError(domain: "MusiaReview", code: 5)
        }
        view.layoutSubtreeIfNeeded()
        view.cacheDisplay(in: view.bounds, to: bitmap)
        guard let data = bitmap.representation(using: .png, properties: [:]) else {
            throw NSError(domain: "MusiaReview", code: 6)
        }
        try data.write(to: directory.appendingPathComponent(name + ".png"), options: .atomic)
    }
}
#endif
