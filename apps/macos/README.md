# Musia for macOS

Native SwiftUI and AVFoundation app for **macOS 14 or later**, built for Intel
and Apple silicon. No Catalyst, WebView, local server or bundled browser.
The Mac target shares MusiaCore, catalog, playback, lyrics, guitar diagrams,
lessons and local history with iOS. Platform-specific code is limited to the
window/sidebar/menu structure, audio-session handling and native artwork.

## Build and Test

Use an existing Mac/Xcode installation. The generated project and icon catalog
are checked in; normal builds need neither Ruby gems nor Python packages.

```sh
xcodebuild -project apps/macos/Musia.xcodeproj -scheme Musia \
  -configuration Debug -destination 'platform=macOS' \
  -derivedDataPath store/.runtime/mac-debug -jobs 2 build
xcodebuild -project apps/macos/Musia.xcodeproj -scheme Musia \
  -configuration Debug -destination 'platform=macOS' \
  -derivedDataPath store/.runtime/mac-debug -jobs 2 test
open store/.runtime/mac-debug/Build/Products/Debug/Musia.app
```

The core also supports `swift test --package-path apps/ios --jobs 2`.
Opt-in network tests require `MUSIA_LIVE_TESTS=1` in the test runner's
environment; a skipped live test is not network qualification.
The shared live-contract test separately uses `MUSIA_LIVE_API=1`.
For release-optimized local tests, use a separate DerivedData directory,
`-configuration Release CODE_SIGN_IDENTITY=- MUSIA_MAC_PROFILE= \
PROVISIONING_PROFILE_SPECIFIER= ENABLE_TESTABILITY=YES ENABLE_HARDENED_RUNTIME=NO`,
with `TEST_RUNNER_MUSIA_LIVE_TESTS=1 TEST_RUNNER_MUSIA_LIVE_API=1` in the
`xcodebuild` environment. Ad-hoc XCTest injection requires that local-only
runtime setting; the distribution archive keeps Hardened Runtime and real
team signing. An App Store-signed archive is not an ordinary debug installation.

When adding source files, regenerate with the existing `xcodeproj` Ruby gem:

```sh
ruby apps/macos/scripts/generate-project.rb
python3 apps/macos/scripts/generate-assets.py
```

The asset generator calls the shared Node/ImageMagick exporter, using the
generated rounded Musia master with transparent outside corners and Dock padding;
it does not download or regenerate artwork. Normal builds use the checked-in
PNGs and need neither ImageMagick nor image generation. The app contains only outgoing-network and
user-selected-file-export sandbox entitlements. No microphone, camera,
incoming server or broad filesystem access is requested.

## Native Review

The Debug-only `--musia-review` harness loads the real catalog, plays First Pulse
and Aya Chan, checks minimized playback, reads saved history, visits lessons and
captures the actual AppKit/SwiftUI window. It terminates its own app on completion.
Do not run it against someone's active practice session: it creates test history.

```sh
open -g -W store/.runtime/mac-debug/Build/Products/Debug/Musia.app --args --musia-review
```

Results and native PNGs are saved inside the app sandbox at
`~/Library/Containers/art.lazying.musia/Data/Library/Caches/Musia-Mac-Review/`.
These are app-scoped programmatic runtime checks, not a claim of human or
accessibility-input testing. Inspect every screenshot and its dimensions.
A desktop that constrains the window below Apple's required screenshot size
must not be stretched or passed off as a qualifying screenshot. Use a suitable
real display instead. Release compilation excludes the harness entirely.

## Release

Bundle `art.lazying.musia` shares the existing Musia App Store record and its
owner-confirmed USD2.99 price. macOS has a separate platform version/build,
screenshots, review record and distribution profile. Do not remove an iOS
submission to submit the Mac app.

`tools/store/build_macos.sh` builds a universal archive, exports a signed installer,
checks signatures and prints its SHA-256. It requires the private Musia Mac App
Store profile and existing authorized signing keychain. Keychain unlocking uses
an owner-only password file, never a committed value. It refuses to overwrite
an existing archive and does not revoke certificates or change keychain ACLs.
The signed archive is packaged with Apple's `productbuild --component` flow.
Only the generated app's permissions are normalized for installed-user access;
private build logs, signing sources and the enclosing runtime remain private.
`ExportOptions.plist` is retained for Xcode Organizer/export use when needed.

```sh
MUSIA_MAC_PROFILE_PATH=/private/path/Musia_Mac_App_Store.provisionprofile \
  bash tools/store/build_macos.sh
```

`tools/store/upload_macos.py` rechecks the installer checksum, extracted app
identity, universal architectures, permissions, pinned signer, sandbox and absence
of the Debug harness before Apple's validation. Use the existing Musia store
Python runtime (`~/.local/share/musia/store-python/bin/python` on the shared KVM),
which has PyJWT. Add `--execute-upload` only for a qualified candidate. Uploads
are journaled before sending, and a previously attempted upload is not retried
without provider reconciliation. Both process status and Apple's JSON result must
confirm success: `altool` has returned exit zero with `product-errors` in practice.
This uploader does not change pricing, legal declarations or submit formal review.

Listing copy lives in `store/macos-listing.json`. Exact build/test/upload/review
outcomes belong in a dated store record; API tokens, account contact details,
profiles, packages and raw logs stay under ignored private runtime storage.

## Controls and Behavior

- Sidebar: Library, Practice, Lessons and History; Command-1 through Command-4.
- Space: play/pause; Command-Left/Right: seek ten seconds.
- Command-[ / Command-]: change playback speed without pitch shifting.
- Playback menu: loop markers, clear loop and normal speed.
- Playback continues while minimized or another app is active. System sleep
  pauses playback; the app does not prevent sleep or restart audio on wake.
- Closing the window is not quitting the app. Command-Q checkpoints history.
- First Pulse is available offline. Catalog songs require HTTPS connectivity.
- All timeline visuals derive from AVPlayer media time. Analyzed data remains
  labeled as analyzed; tap offsets are not guitar/singing grades.
