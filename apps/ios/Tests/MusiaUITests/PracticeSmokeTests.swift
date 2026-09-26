import XCTest

final class PracticeSmokeTests: XCTestCase {
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
            for name in ["History", "Lessons", "Library"] {
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
