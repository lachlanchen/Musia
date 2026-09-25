import XCTest

final class PracticeSmokeTests: XCTestCase {
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
