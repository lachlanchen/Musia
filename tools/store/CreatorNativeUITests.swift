import XCTest

final class CreatorNativeUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    @MainActor
    private func capture(_ app: XCUIApplication, _ name: String) {
        let image = XCTAttachment(screenshot: app.screenshot())
        image.name = name
        image.lifetime = .keepAlways
        add(image)
        let tree = XCTAttachment(string: app.debugDescription)
        tree.name = name + "-accessibility"
        tree.lifetime = .keepAlways
        add(tree)
    }

    @MainActor
    private func text(_ app: XCUIApplication, containing value: String) -> XCUIElement {
        app.staticTexts.matching(NSPredicate(format: "label CONTAINS %@", value)).firstMatch
    }

    @MainActor
    private func tapVisible(_ button: XCUIElement, in app: XCUIApplication) {
        for _ in 0..<8 {
            if button.isHittable { break }
            app.swipeUp(velocity: .slow)
        }
        XCTAssertTrue(button.waitForExistence(timeout: 10))
        XCTAssertTrue(button.isHittable)
        button.tap()
    }

    @MainActor
    func testCreatorAccountAndCommunity() throws {
        let app = XCUIApplication()
        app.launch()
        defer { app.terminate() }
        XCTAssertTrue(app.buttons["library.localFirstPulse"].waitForExistence(timeout: 30))
        capture(app, "creator-library")
        let create = app.buttons.matching(NSPredicate(format: "label == 'Create'")).firstMatch
        XCTAssertTrue(create.waitForExistence(timeout: 10))
        create.tap()
        XCTAssertTrue(text(app, containing: "Make room for your next song").waitForExistence(timeout: 15))
        XCTAssertTrue(text(app, containing: "Sign in to create").exists)
        capture(app, "creator-signed-out")

        let account = app.buttons["Account & subscriptions"]
        XCTAssertTrue(account.waitForExistence(timeout: 10))
        account.tap()
        let signIn = app.buttons["Sign in with your browser"]
        XCTAssertTrue(signIn.waitForExistence(timeout: 15))
        let loginReady = XCTNSPredicateExpectation(predicate: NSPredicate(format: "enabled == true"), object: signIn)
        XCTAssertEqual(XCTWaiter.wait(for: [loginReady], timeout: 30), .completed)
        capture(app, "creator-account-signed-out")

        let unavailable = text(app, containing: "Subscription prices are unavailable from the App Store")
        let lookupError = text(app, containing: "App Store prices could not load")
        let products = app.buttons.matching(NSPredicate(format: "label BEGINSWITH 'Subscribe to '"))
        let lookupDone = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            unavailable.exists || lookupError.exists || products.count > 0
        }, object: nil)
        XCTAssertEqual(XCTWaiter.wait(for: [lookupDone], timeout: 60), .completed)
        let result = products.count > 0 ? "products-visible" : unavailable.exists ? "empty-products" : "lookup-error"
        let lookup = XCTAttachment(string: "Product.products result: \(result); purchases not attempted")
        lookup.name = "creator-product-lookup-result"
        lookup.lifetime = .keepAlways
        add(lookup)
        for index in 0..<products.count { XCTAssertFalse(products.element(boundBy: index).isEnabled) }
        let restore = app.buttons["Restore / check purchases"]
        for _ in 0..<6 {
            if restore.isHittable { break }
            app.swipeUp(velocity: .slow)
        }
        XCTAssertTrue(restore.exists)
        XCTAssertFalse(restore.isEnabled)
        XCTAssertTrue(app.buttons["Find missing Apple purchases\u{2026}"].exists)
        capture(app, "creator-product-lookup")

        app.navigationBars.buttons.element(boundBy: 0).tap()
        let community = app.buttons.matching(NSPredicate(format: "label == 'Community'")).firstMatch
        XCTAssertTrue(community.waitForExistence(timeout: 10))
        community.tap()
        XCTAssertTrue(app.segmentedControls.firstMatch.waitForExistence(timeout: 15))
        capture(app, "creator-community")

        guard let url = Bundle(for: Self.self).url(forResource: "creator-qa-fixture", withExtension: "json") else {
            XCTFail("Authorized private native login fixture not staged")
            return
        }
        let fixture = try JSONDecoder().decode(LoginFixture.self, from: Data(contentsOf: url))
        let communityAccount = app.buttons["Account & subscriptions"]
        XCTAssertTrue(communityAccount.waitForExistence(timeout: 10))
        communityAccount.tap()
        XCTAssertTrue(signIn.waitForExistence(timeout: 10))
        tapVisible(signIn, in: app)
        let consent = app.alerts.buttons["Continue"]
        if consent.waitForExistence(timeout: 5) { consent.tap() }

        let safari = XCUIApplication(bundleIdentifier: "com.apple.SafariViewService")
        let web = app.webViews.firstMatch.waitForExistence(timeout: 15) ? app : safari
        let password = web.secureTextFields.firstMatch
        XCTAssertTrue(password.waitForExistence(timeout: 30))
        let username = web.textFields.firstMatch
        XCTAssertTrue(username.exists)
        username.tap()
        username.typeText(fixture.username)
        let next = web.keyboards.buttons["Next"]
        if next.exists && next.isHittable { next.tap() }
        else { password.tap() }
        let focused = NSPredicate(format: "hasKeyboardFocus == true")
        let focus = XCTNSPredicateExpectation(predicate: focused, object: password)
        if XCTWaiter.wait(for: [focus], timeout: 5) != .completed {
            password.tap()
            let retryFocus = XCTNSPredicateExpectation(predicate: focused, object: password)
            XCTAssertEqual(XCTWaiter.wait(for: [retryFocus], timeout: 10), .completed)
        }
        password.typeText(fixture.password)
        let submit = web.buttons.matching(NSPredicate(format: "label == 'Sign in'")).firstMatch
        XCTAssertTrue(submit.exists)
        submit.tap()
        let authorize = web.buttons.matching(NSPredicate(format: "label == 'Continue'")).firstMatch
        if authorize.waitForExistence(timeout: 15) { authorize.tap() }
        let returnLink = web.links.matching(NSPredicate(format: "label CONTAINS 'Musia'")).firstMatch
        if returnLink.waitForExistence(timeout: 5) && returnLink.isHittable { returnLink.tap() }

        XCTAssertTrue(text(app, containing: "Renders remaining").waitForExistence(timeout: 45))
        XCTAssertFalse(signIn.exists)
        capture(app, "creator-account-signed-in")
        app.terminate()
        app.launch()
        let settings = app.buttons.matching(NSPredicate(format: "label == 'Settings'")).firstMatch
        XCTAssertTrue(settings.waitForExistence(timeout: 30))
        settings.tap()
        let accountLink = app.buttons.matching(NSPredicate(format: "label CONTAINS %@", fixture.display_name)).firstMatch
        XCTAssertTrue(accountLink.waitForExistence(timeout: 15))
        accountLink.tap()
        XCTAssertTrue(text(app, containing: "Renders remaining").waitForExistence(timeout: 30))
        capture(app, "creator-account-relaunched")
        let subscribed = app.buttons.matching(NSPredicate(format: "label BEGINSWITH 'Subscribe to '"))
        for index in 0..<subscribed.count { XCTAssertFalse(subscribed.element(boundBy: index).isEnabled) }
    }

    private struct LoginFixture: Decodable {
        let username: String
        let password: String
        let display_name: String
    }
}
