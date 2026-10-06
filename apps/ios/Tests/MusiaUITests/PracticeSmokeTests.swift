import XCTest

final class PracticeSmokeTests: XCTestCase {
    @MainActor
    func testStageLayoutAndPracticeSwitch() {
        let app = XCUIApplication()
        app.launchArguments = ["-lyricLanguages", "en,zh,ja"]
        app.launch()
        defer { app.terminate(); XCUIDevice.shared.orientation = .portrait }
        let exercise = app.buttons["library.localFirstPulse"]
        XCTAssertTrue(exercise.waitForExistence(timeout: 15)); exercise.tap()
        let views = app.segmentedControls["player.view"]
        XCTAssertTrue(views.waitForExistence(timeout: 10))
        views.buttons["Stage"].tap()
        let play = app.buttons["practice.transport.play"]
        for orientation in [UIDeviceOrientation.portrait, .landscapeRight] {
            XCUIDevice.shared.orientation = orientation
            XCTAssertTrue(play.waitForExistence(timeout: 5))
            XCTAssertTrue(play.isHittable)
            XCTAssertTrue(app.frame.contains(play.frame))
            // The transport must remain tappable even when the stage is scrolled.
            app.swipeUp(velocity: .slow)
            XCTAssertTrue(play.isHittable)
            let image = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
            image.name = "stage-\(orientation.rawValue)"; image.lifetime = .keepAlways; add(image)
            app.swipeDown(velocity: .slow)
        }
        views.buttons["Practice"].tap()
        XCTAssertTrue(app.segmentedControls["practice.mode"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testBeginnerPracticeAndSettings() {
        let app = XCUIApplication()
        app.launchArguments = ["-lyricLanguages", "en,zh,ja"]
        app.launch()
        defer { app.terminate() }
        func capture(_ name: String) {
            let image = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
            image.name = name; image.lifetime = .keepAlways; add(image)
        }
        let lessons = app.buttons.matching(NSPredicate(format: "label == 'Lessons'")).firstMatch
        XCTAssertTrue(lessons.waitForExistence(timeout: 15)); lessons.tap()
        let pitch = app.buttons["lesson.pitch"]
        XCTAssertTrue(pitch.waitForExistence(timeout: 10)); pitch.tap()
        let doNote = app.buttons["pitch.note.0"]
        XCTAssertTrue(doNote.waitForExistence(timeout: 5)); doNote.tap()
        XCTAssertTrue(app.staticTexts.containing(NSPredicate(format: "label CONTAINS '261.6 Hz'")).firstMatch.waitForExistence(timeout: 5))
        capture("pitch-learn")
        app.segmentedControls.buttons["Quiz"].tap()
        XCTAssertFalse(doNote.isEnabled)
        app.buttons["pitch.listen"].tap()
        XCTAssertTrue(doNote.isEnabled); doNote.tap()
        XCTAssertFalse(doNote.isEnabled)
        capture("pitch-score")
        app.navigationBars.buttons.element(boundBy: 0).tap()
        let metronome = app.buttons["lesson.metronome"]
        XCTAssertTrue(metronome.waitForExistence(timeout: 5)); metronome.tap()
        let start = app.buttons["metronome.startStop"]
        XCTAssertTrue(start.waitForExistence(timeout: 5)); start.tap()
        XCTAssertTrue(app.buttons["metronome.tap"].isEnabled)
        app.buttons["metronome.tap"].tap()
        capture("metronome-running")
        start.tap()
        XCTAssertFalse(app.buttons["metronome.tap"].isEnabled)
        app.navigationBars.buttons.element(boundBy: 0).tap()
        let settings = app.buttons.matching(NSPredicate(format: "label == 'Settings'")).firstMatch
        settings.tap()
        XCTAssertTrue(app.buttons["Practice history"].waitForExistence(timeout: 5))
        capture("settings-languages")
        app.buttons["Practice history"].tap()
        XCTAssertTrue(app.navigationBars["History"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testLiveMultilingualLyrics() {
        let app = XCUIApplication()
        app.launchArguments = ["-lyricLanguages", "en,zh,ja"]
        app.launch()
        defer { app.terminate() }
        let search = app.searchFields.firstMatch
        // iPad's native toolbar initially collapses search into its icon.
        if !search.exists, app.buttons["Search"].exists { app.buttons["Search"].tap() }
        if !search.isHittable { app.swipeDown() }
        XCTAssertTrue(search.waitForExistence(timeout: 15)); search.tap(); search.typeText("Rain of Light")
        let song = app.buttons["library.song.aya-chan-hikari-ame"]
        XCTAssertTrue(song.waitForExistence(timeout: 30)); song.tap()
        let languages = app.buttons["practice.lyricLanguages"]
        for _ in 0..<5 { if languages.isHittable { break }; app.swipeUp(velocity: .slow) }
        XCTAssertTrue(languages.waitForExistence(timeout: 15))
        let image = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        image.name = "multilingual-lyrics"; image.lifetime = .keepAlways; add(image)
        languages.tap()
        let jp = app.buttons["日本語"]
        XCTAssertTrue(jp.waitForExistence(timeout: 5))
        jp.tap()
        let menu = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        menu.name = "lyric-language-selection"; menu.lifetime = .keepAlways; add(menu)
    }

    @MainActor
    func testStoreScreenshots() {
        let app = XCUIApplication()
        app.launchArguments = ["-musia.mode.v1", "Listen", "-musia.rate.v1", "1",
                               "-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryL"]
        XCUIDevice.shared.orientation = .portrait
        app.launch()
        defer { app.terminate() }

        func capture(_ name: String) {
            Thread.sleep(forTimeInterval: 1)
            let image = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
            image.name = "store-\(name)"
            image.lifetime = .keepAlways
            add(image)
        }

        let exercise = app.buttons["library.localFirstPulse"]
        XCTAssertTrue(exercise.waitForExistence(timeout: 20))
        let loading = app.staticTexts["Loading library..."]
        let loaded = NSPredicate { _, _ in !loading.exists }
        _ = XCTWaiter.wait(for: [XCTNSPredicateExpectation(predicate: loaded, object: nil)], timeout: 30)
        capture("library")

        exercise.tap()
        let transport = app.buttons["practice.transport.play"]
        XCTAssertTrue(transport.waitForExistence(timeout: 15))
        capture("practice")

        app.segmentedControls["practice.mode"].buttons["Play"].tap()
        let shape = app.descendants(matching: .any)["guitar.Em"].firstMatch
        for _ in 0..<3 {
            if shape.isHittable { break }
            app.swipeUp(velocity: .slow)
        }
        XCTAssertTrue(shape.waitForExistence(timeout: 5))
        XCTAssertTrue(shape.isHittable)
        // iPad presents a shorter sheet; bring the whole diagram into view.
        if app.frame.width > 700 {
            let start = app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.60))
            let end = app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.46))
            start.press(forDuration: 0.05, thenDragTo: end)
        }
        capture("guitar")

        app.buttons["practice.close"].tap()
        let lessons = app.buttons.matching(NSPredicate(format: "label == 'Lessons'")).firstMatch
        XCTAssertTrue(lessons.waitForExistence(timeout: 5))
        lessons.tap()
        capture("lessons")
    }

    @MainActor
    func testMiniPlayerDoesNotCoverNavigation() {
        verifyMiniPlayerNavigation(largeText: false)
    }

    @MainActor
    func testMiniPlayerNavigationWithLargeText() {
        verifyMiniPlayerNavigation(largeText: true)
    }

    @MainActor
    private func verifyMiniPlayerNavigation(largeText: Bool) {
        let app = XCUIApplication()
        if largeText { app.launchArguments = ["-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryAccessibilityXXXL"] }
        app.launch()
        defer { app.terminate(); XCUIDevice.shared.orientation = .portrait }
        let baseline = XCTAttachment(screenshot: app.screenshot())
        baseline.name = "navigation-before-selection"
        baseline.lifetime = .keepAlways
        add(baseline)
        let exercise = app.buttons["library.localFirstPulse"]
        XCTAssertTrue(exercise.waitForExistence(timeout: 15))
        exercise.tap()
        let close = app.buttons["practice.close"]
        XCTAssertTrue(close.waitForExistence(timeout: 10))
        close.tap()
        let mini = app.buttons["mini.open"]
        XCTAssertTrue(mini.waitForExistence(timeout: 10))
        for orientation in [UIDeviceOrientation.portrait, .landscapeRight] {
            XCUIDevice.shared.orientation = orientation
            let rotated = NSPredicate { _, _ in
                orientation == .portrait ? app.frame.height > app.frame.width : app.frame.width > app.frame.height
            }
            XCTAssertEqual(XCTWaiter.wait(for: [XCTNSPredicateExpectation(predicate: rotated, object: nil)], timeout: 10), .completed)
            for name in ["Settings", "Lessons", "Library"] {
                // iPad exposes its top floating tabs as buttons, not a TabBar.
                let tab = app.buttons.matching(NSPredicate(format: "label == %@", name)).firstMatch
                XCTAssertTrue(tab.waitForExistence(timeout: 5))
                XCTAssertTrue(tab.isHittable, "\(name) must remain tappable")
                XCTAssertFalse(tab.frame.intersects(mini.frame), "Mini-player must not overlap \(name)")
                XCTAssertTrue(app.frame.contains(mini.frame), "Mini-player must remain inside the screen")
                tab.tap()
                XCTAssertTrue(tab.isSelected)
                XCTAssertTrue(mini.isHittable)
            }
            // Let the tab transition settle before retaining visual evidence.
            Thread.sleep(forTimeInterval: 1)
            let image = XCTAttachment(screenshot: app.screenshot())
            image.name = "mini-player-\(orientation.rawValue)-large-text-\(largeText)"
            image.lifetime = .keepAlways
            add(image)
            let tree = XCTAttachment(string: app.debugDescription)
            tree.name = "navigation-frames-\(orientation.rawValue)"
            tree.lifetime = .keepAlways
            add(tree)
        }
        mini.tap()
        XCTAssertTrue(close.waitForExistence(timeout: 5))
    }

    @MainActor
    func testFirstPulsePlaybackKnownShapeAndPausedTap() {
        let app = XCUIApplication()
        app.launchArguments = ["-musia.mode.v1", "Listen", "-musia.rate.v1", "1"]
        app.launch()
        let exercise = app.buttons["library.localFirstPulse"]
        XCTAssertTrue(exercise.waitForExistence(timeout: 15))
        exercise.tap()
        let transport = app.buttons["practice.transport.play"]
        XCTAssertTrue(transport.waitForExistence(timeout: 15))
        let ready = NSPredicate(format: "enabled == true")
        expectation(for: ready, evaluatedWith: transport)
        waitForExpectations(timeout: 20)
        app.segmentedControls["practice.mode"].buttons["Play"].tap()
        app.swipeUp()
        let shape = app.descendants(matching: .any)["guitar.Em"].firstMatch
        XCTAssertTrue(shape.waitForExistence(timeout: 5))
        let diagram = XCTAttachment(screenshot: app.screenshot())
        diagram.name = "first-pulse-em-fingering"
        diagram.lifetime = .keepAlways
        add(diagram)
        app.swipeDown()
        transport.tap()
        expectation(for: NSPredicate(format: "label == 'Pause'"), evaluatedWith: transport)
        waitForExpectations(timeout: 15)
        transport.tap()
        app.segmentedControls["practice.mode"].buttons["Tap"].tap()
        app.swipeUp()
        let tapPad = app.buttons["practice.tap"]
        XCTAssertTrue(tapPad.waitForExistence(timeout: 5))
        XCTAssertFalse(tapPad.isEnabled)
        let tap = XCTAttachment(screenshot: app.screenshot())
        tap.name = "paused-tap-disabled"
        tap.lifetime = .keepAlways
        add(tap)
        app.terminate()
    }
}
