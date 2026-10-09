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
    private func fullyVisible(_ element: XCUIElement, in app: XCUIApplication) -> Bool {
        guard element.exists, !element.frame.isEmpty, app.frame.contains(element.frame) else { return false }
        let bars = app.navigationBars.allElementsBoundByIndex + app.tabBars.allElementsBoundByIndex
        return !bars.contains { $0.exists && $0.frame.intersects(element.frame) }
    }

    @MainActor
    private func assertMiniPlayer(_ app: XCUIApplication, stage: String) {
        let open = app.buttons["mini.open"]
        let play = app.buttons["mini.play"]
        let buttons = app.tabBars.firstMatch.exists ? app.tabBars.firstMatch.buttons : app.buttons
        let tabs = ["Library", "Lessons", "Create", "Community", "Settings"].map { name in
            buttons.matching(NSPredicate(format: "label == %@ AND identifier != 'BackButton'", name)).firstMatch
        }
        let visible = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            guard open.exists, play.exists, open.isHittable, play.isHittable,
                  !open.frame.isEmpty, !play.frame.isEmpty else { return false }
            // The container's safe-area background can extend behind the tabs.
            let controls = open.frame.union(play.frame)
            return app.frame.contains(controls) && tabs.allSatisfy {
                $0.exists && $0.isHittable && !$0.frame.isEmpty &&
                    app.frame.contains($0.frame) && !$0.frame.intersects(controls)
            }
        }, object: nil)
        let result = XCTWaiter.wait(for: [visible], timeout: 10)
        capture(app, stage)
        XCTAssertEqual(result, .completed, "Mini-player controls must stay inside the app and clear of every tab")
    }

    @MainActor
    func testAgentStudioWorkspace() throws {
        let app = XCUIApplication()
        app.launch()
        defer { app.terminate() }
        XCTAssertTrue(app.buttons["library.localFirstPulse"].waitForExistence(timeout: 30))
        app.buttons.matching(NSPredicate(format: "label == 'Create'")).firstMatch.tap()
        let workspace = app.segmentedControls["creator.workspace"]
        XCTAssertTrue(workspace.waitForExistence(timeout: 15))
        XCTAssertTrue(workspace.buttons["Agent"].isSelected)
        XCTAssertTrue(app.textFields["Message Musia"].exists || app.textViews["Message Musia"].exists)
        capture(app, "workspace-agent-default")
        workspace.buttons["Studio"].tap()
        let title = app.textFields["Title"]
        tapVisible(title, in: app)
        let original = title.value as? String ?? ""
        let marker = "Workspace Test - Morning Light"
        title.press(forDuration: 1.1)
        if app.menuItems["Select All"].waitForExistence(timeout: 2) { app.menuItems["Select All"].tap() }
        else {
            title.typeText(String(repeating: XCUIKeyboardKey.delete.rawValue, count: original.count))
        }
        title.typeText(marker)
        app.swipeDown()
        let done = app.toolbars.buttons["Done"]
        if done.exists { done.tap() }
        capture(app, "workspace-studio-edit")
        app.terminate()
        app.launch()
        let create = app.buttons.matching(NSPredicate(format: "label == 'Create'")).firstMatch
        XCTAssertTrue(create.waitForExistence(timeout: 30))
        create.tap()
        XCTAssertTrue(workspace.waitForExistence(timeout: 15))
        XCTAssertTrue(workspace.buttons["Agent"].isSelected)
        XCTAssertTrue(text(app, containing: marker).waitForExistence(timeout: 20))
        capture(app, "workspace-agent-restored")
        workspace.buttons["Studio"].tap()
        XCTAssertTrue(title.waitForExistence(timeout: 10))
        XCTAssertEqual(title.value as? String, marker)
        tapVisible(title, in: app)
        title.typeText(String(repeating: XCUIKeyboardKey.delete.rawValue, count: marker.count))
        if !original.isEmpty && original != "Title" { title.typeText(original) }
        // No Send, render, purchase or public mutation is dispatched by this test.
    }

    @MainActor
    func testCreatorProducts() throws {
        let app = XCUIApplication()
        app.launch()
        defer { app.terminate() }
        XCTAssertTrue(app.buttons["library.localFirstPulse"].waitForExistence(timeout: 30))
        let create = app.buttons.matching(NSPredicate(format: "label == 'Create'")).firstMatch
        XCTAssertTrue(create.waitForExistence(timeout: 10))
        create.tap()
        guard let fixtureURL = Bundle(for: Self.self).url(forResource: "creator-qa-fixture", withExtension: "json") else {
            XCTFail("Private login fixture missing"); return
        }
        let fixture = try JSONDecoder().decode(LoginFixture.self, from: Data(contentsOf: fixtureURL))
        let account = app.buttons.matching(NSPredicate(format: "label == %@ OR label == %@",
            "Account & subscriptions", fixture.username)).firstMatch
        XCTAssertTrue(account.waitForExistence(timeout: 15))
        tapVisible(account, in: app)
        XCTAssertTrue(app.buttons["Refresh account"].waitForExistence(timeout: 15))
        let lookup = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            app.buttons["Subscribe to Musia Creator"].exists || app.buttons["Reload App Store prices"].exists
        }, object: nil)
        _ = XCTWaiter.wait(for: [lookup], timeout: 15)
        let reload = app.buttons["Reload App Store prices"]
        if reload.exists { tapVisible(reload, in: app) }
        for (name, renders) in [("Musia Creator", 20), ("Musia Studio", 80)] {
            let title = app.staticTexts[name]
            let description = app.staticTexts["Create \(renders) songs monthly. Keep private or share."]
            let subscribe = app.buttons["Subscribe to \(name)"]
            let row = app.cells.containing(.staticText, identifier: name).firstMatch
            let price = row.staticTexts.matching(NSPredicate(format: "label MATCHES %@", ".*[0-9].* / 1 month")).firstMatch
            let deadline = Date().addingTimeInterval(60)
            while Date() < deadline {
                if [title, description, price, subscribe].allSatisfy({ fullyVisible($0, in: app) }) { break }
                let moveDown = title.exists && title.frame.minY < app.navigationBars.firstMatch.frame.maxY
                let start = app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.6))
                let end = app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: moveDown ? 0.78 : 0.42))
                start.press(forDuration: 0.1, thenDragTo: end)
            }
            capture(app, "creator-product-\(name == "Musia Creator" ? "creator" : "studio")")
            for element in [title, description, price, subscribe] {
                XCTAssertTrue(fullyVisible(element, in: app), "Full \(name) title, description, price and button must be onscreen")
            }
            // Inspect real StoreKit UI only; never tap Subscribe, Restore or Sync.
        }
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
        XCTAssertTrue(app.segmentedControls["creator.workspace"].waitForExistence(timeout: 15))
        XCTAssertTrue(app.segmentedControls["creator.workspace"].buttons["Agent"].isSelected)
        let existingFixtureURL = try XCTUnwrap(Bundle(for: Self.self).url(forResource: "creator-qa-fixture", withExtension: "json"))
        let existingFixture = try JSONDecoder().decode(LoginFixture.self, from: Data(contentsOf: existingFixtureURL))
        let retainedAccount = app.buttons[existingFixture.username]
        if retainedAccount.waitForExistence(timeout: 15) {
            capture(app, "creator-upgrade-session-preserved")
            retainedAccount.tap()
            XCTAssertTrue(text(app, containing: "Renders remaining").waitForExistence(timeout: 30))
            capture(app, "creator-account-signed-in")
            app.terminate()
            app.launch()
            let settings = app.buttons.matching(NSPredicate(format: "label == 'Settings'")).firstMatch
            XCTAssertTrue(settings.waitForExistence(timeout: 30))
            settings.tap()
            let restored = app.buttons.matching(NSPredicate(format: "label CONTAINS %@", existingFixture.username)).firstMatch
            XCTAssertTrue(restored.waitForExistence(timeout: 15))
            restored.tap()
            XCTAssertTrue(text(app, containing: "Renders remaining").waitForExistence(timeout: 30))
            capture(app, "creator-account-relaunched")
            return
        }
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
        // The system password-save sheet blocks the issuer's consent page.
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        for surface in [springboard, web, app] {
            let later = surface.buttons["Not Now"]
            if later.waitForExistence(timeout: 3) && later.isHittable { later.tap(); break }
        }
        let authorize = web.buttons.matching(NSPredicate(format: "label == 'Continue'")).firstMatch
        if authorize.waitForExistence(timeout: 15) { authorize.tap() }
        let returnLink = web.links.matching(NSPredicate(format: "label CONTAINS 'Musia'")).firstMatch
        if returnLink.waitForExistence(timeout: 5) && returnLink.isHittable { returnLink.tap() }

        let signedIn = text(app, containing: "Renders remaining").waitForExistence(timeout: 45)
        if !signedIn { capture(app, "creator-return-failed"); capture(web, "creator-web-return-failed") }
        XCTAssertTrue(signedIn)
        XCTAssertFalse(signIn.exists)
        capture(app, "creator-account-signed-in")
        app.terminate()
        app.launch()
        let settings = app.buttons.matching(NSPredicate(format: "label == 'Settings'")).firstMatch
        XCTAssertTrue(settings.waitForExistence(timeout: 30))
        settings.tap()
        let accountLink = app.buttons.matching(NSPredicate(format: "label CONTAINS %@", fixture.username)).firstMatch
        XCTAssertTrue(accountLink.waitForExistence(timeout: 15))
        accountLink.tap()
        XCTAssertTrue(text(app, containing: "Renders remaining").waitForExistence(timeout: 30))
        capture(app, "creator-account-relaunched")
        let subscribed = app.buttons.matching(NSPredicate(format: "label BEGINSWITH 'Subscribe to '"))
        for index in 0..<subscribed.count { XCTAssertFalse(subscribed.element(boundBy: index).isEnabled) }
    }

    @MainActor
    func testSignedInPrivatePlayback() throws {
        let app = XCUIApplication()
        app.launch()
        defer { app.terminate() }
        XCTAssertTrue(app.buttons["library.localFirstPulse"].waitForExistence(timeout: 30))
        app.buttons.matching(NSPredicate(format: "label == 'Community'")).firstMatch.tap()
        let mine = app.segmentedControls.buttons["My songs"]
        XCTAssertTrue(mine.waitForExistence(timeout: 15))
        mine.tap()
        let song = app.buttons.matching(NSPredicate(format: "label CONTAINS 'A Little Room for Morning' AND identifier != 'mini.open'")).firstMatch
        XCTAssertTrue(song.waitForExistence(timeout: 30))
        capture(app, "creator-private-library")
        song.tap()
        let open = app.buttons["Open in player"]
        XCTAssertTrue(open.waitForExistence(timeout: 15))
        open.tap()
        let play = app.buttons["mini.play"]
        let downloaded = play.waitForExistence(timeout: 240)
        if !downloaded { capture(app, "creator-private-download-failed") }
        XCTAssertTrue(downloaded)
        let ready = XCTNSPredicateExpectation(predicate: NSPredicate(format: "enabled == true"), object: play)
        let readyResult = XCTWaiter.wait(for: [ready], timeout: 30)
        if readyResult != .completed {
            capture(app, "creator-private-not-ready-mini")
            let miniOpen = app.buttons["mini.open"]
            if miniOpen.exists && miniOpen.isHittable {
                miniOpen.tap()
                _ = app.buttons["practice.close"].waitForExistence(timeout: 10)
                capture(app, "creator-private-not-ready-player")
            }
        }
        XCTAssertEqual(readyResult, .completed)
        XCTAssertTrue(open.exists)
        assertMiniPlayer(app, stage: "creator-private-detail-mini")
        play.tap()
        app.buttons["mini.open"].tap()
        let position = app.sliders["Playback position"]
        XCTAssertTrue(position.waitForExistence(timeout: 15))
        let initial = position.value as? String
        let advances = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            (position.value as? String) != initial
        }, object: nil)
        XCTAssertEqual(XCTWaiter.wait(for: [advances], timeout: 20), .completed)
        capture(app, "creator-private-playing")
        app.buttons["practice.close"].tap()
        XCTAssertTrue(open.waitForExistence(timeout: 15))
        assertMiniPlayer(app, stage: "creator-private-detail-return-mini")
        app.navigationBars["Song"].buttons.element(boundBy: 0).tap()
        XCTAssertTrue(mine.waitForExistence(timeout: 15))
        assertMiniPlayer(app, stage: "creator-private-root-mini")
        tapVisible(song, in: app)
        XCTAssertTrue(open.waitForExistence(timeout: 15))
        assertMiniPlayer(app, stage: "creator-private-reopened-mini")
        app.buttons.matching(NSPredicate(format: "label == 'Settings'")).firstMatch.tap()
        guard let fixtureURL = Bundle(for: Self.self).url(forResource: "creator-qa-fixture", withExtension: "json") else {
            XCTFail("Private login fixture missing"); return
        }
        let fixture = try JSONDecoder().decode(LoginFixture.self, from: Data(contentsOf: fixtureURL))
        let account = app.buttons.matching(NSPredicate(format: "label CONTAINS %@", fixture.username)).firstMatch
        XCTAssertTrue(account.waitForExistence(timeout: 15))
        account.tap()
        let signOut = app.buttons["Sign out"]
        let mini = app.descendants(matching: .any).matching(identifier: "mini.player").firstMatch
        for _ in 0..<8 {
            if signOut.exists && signOut.isHittable && fullyVisible(signOut, in: app) &&
                mini.exists && signOut.frame.maxY <= mini.frame.minY { break }
            app.swipeUp(velocity: .slow)
        }
        capture(app, "creator-private-before-signout")
        XCTAssertTrue(mini.exists && signOut.isHittable && fullyVisible(signOut, in: app))
        XCTAssertLessThanOrEqual(signOut.frame.maxY, mini.frame.minY)
        // XCTest's edge hit point can fall under the mini-player for a clipped row.
        signOut.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
        let dialogTitle = app.staticTexts["Sign out of Musia?"]
        let dialogVisible = dialogTitle.waitForExistence(timeout: 10)
        capture(app, "creator-private-signout-confirmation")
        XCTAssertTrue(dialogVisible)
        let confirmations = app.buttons.matching(NSPredicate(format: "label == 'Sign out'"))
        let visibleConfirmations = confirmations.allElementsBoundByIndex.filter { $0.isHittable }
        XCTAssertEqual(visibleConfirmations.count, 1, "Require the unique visible logout confirmation")
        visibleConfirmations[0].tap()
        let cleared = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            !app.buttons["mini.open"].exists && !dialogTitle.exists && confirmations.count == 0
        }, object: nil)
        let clearResult = XCTWaiter.wait(for: [cleared], timeout: 15)
        if clearResult != .completed { capture(app, "creator-private-signout-failed") }
        XCTAssertEqual(clearResult, .completed)
        let signedOut = text(app, containing: "An account is optional")
        for _ in 0..<8 {
            if signedOut.exists && fullyVisible(signedOut, in: app) { break }
            app.swipeDown(velocity: .slow)
        }
        capture(app, "creator-private-signout-cleared")
        XCTAssertTrue(signedOut.waitForExistence(timeout: 15))
        XCTAssertTrue(app.buttons["Sign in with your browser"].exists)
        XCTAssertFalse(app.buttons["mini.open"].exists)
    }

    private struct LoginFixture: Decodable {
        let username: String
        let password: String
    }
}
