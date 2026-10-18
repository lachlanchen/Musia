# Apple Compatibility Internal Candidate

Candidate: Musia **0.2.2 (12)**. Internal testing only. Production, existing
review submissions, prices, identity, billing and generation gates are unchanged.
The original icon remains in place. Android has no source changes in this update
and retains its existing internal track; no duplicate Android upload is needed.

## Implementation

- Native Mac deployment target 12.0, with the same Intel/Apple Silicon targets.
- Availability-guarded navigation, forms, multiline fields, empty states,
  sharing and annotated-lyric layout. Monterey uses native AppKit sharing and
  measured wrapping of complete ruby pairs rather than dropping annotations.
- Native window restoration and minimum sizing work without macOS13 Window APIs.
- Media controls can stack on narrow or large-text layouts. Source-time lyrics,
  chords, playback state and creator drafts remain outside layout decisions.
- iOS17 and watchOS10 minimums remain unchanged. No fixed device-name or global
  screen-width detection was introduced. Existing native scene navigation and
  safe-area insets remain the basis for resizing.
- The optional three-second pitch recording uses back-deployable task delays;
  microphone permission, local measurement and deletion behavior are unchanged.

## Qualification Boundary

Apple requires Xcode27.1/iOS27.1 SDK for the Duo full-screen experience. The
available tools inspected for this task are Xcode27.0,26.6 and26.3. Ordinary
rotation/large-text tests are not Duo hinge, camera-region or partial-fold tests.
Do not label this candidate Duo-qualified until the official SDK and simulator
checks have passed. [Apple preparation guide](https://developer.apple.com/videos/play/tech-talks/111461/)
and [adaptive-layout guide](https://developer.apple.com/videos/play/tech-talks/111463/).

The current Xcode build-host requirement is distinct from the deployment target.
Do not install a new host OS merely to test Monterey compatibility.
[Apple Xcode requirements](https://developer.apple.com/xcode/system-requirements).

## Reproducible Checks

Local static checks:

```bash
conda run -n musia python apps/ios/scripts/validate.py
conda run -n musia python apps/macos/scripts/validate.py
conda run -n musia python -m unittest discover -s tools/store/tests
ruby apps/macos/scripts/test-project-identities.rb
```

After an explicit shared-Mac queue handback, select the installed toolchain per
command, set `MUSIA_ROOT` to an isolated checkout and run a bounded phase:

```bash
python3 tools/store/apple_build_guard.py \
  --slot-note "exact coordination handback path" --operation "Musia core QA" \
  -- bash tools/store/test_compatibility_apple.sh core /absolute/new/evidence/core
```

Other phases: `headless` (core tests plus unsigned Mac build), `mac`, `iphone`,
`ipad`, and `mobile` (iPhone then iPad under one enclosing guard, sharing the
owned build cache and stopping after a failed phase). `mobile` requires
`MUSIA_IPHONE_UDID` and `MUSIA_IPAD_UDID`; individual simulator phases require the existing,
stopped, Musia-owned `MUSIA_SIMULATOR_UDID`. The wrapper releases only its matching
directory/inode/token, and retains an uncertain guard for owner recovery.
Never delete a peer guard or treat a quiet process list as a queue handback.
Process inventory errors refuse launch rather than implying an idle host.
Failed child launch releases the unused owned guard; signal-terminated children,
interrupted connections and uncertain descendants retain it for explicit owner
recovery. Disposable-path tests exercise these cases without touching a shared
Mac or the real host guard. No command-line alternate lock path is supported.
For a separately admitted screenshot-repair round, `MUSIA_QA_CAPTURE_ONLY=1`
runs only composer rotation/background, large-text Stage playback and large-text
mini-player navigation. This is not a replacement for the full regression suite.
`MUSIA_QA_DERIVED_DATA` reuses an existing app-owned build cache. Mobile phases
have finite boot, build/test and export deadlines. Timeouts stop only their
launched process group and retain the outer guard for explicit cleanup checks.
The hosted `mac` phase overrides `MUSIA_MAC_BUNDLE_PREFIX`, not the global
`PRODUCT_BUNDLE_IDENTIFIER`. App, embedded framework and test bundle must have
distinct identities in the `art.lazying.musia.compatibilityqa` namespace.
The pre-launch verifier checks all three built plists, package types and the
app's signed sandbox/no-shared-groups entitlements, then records `mac-identity.json`.
Missing or mismatched artifacts stop the run before hosted tests. It runs only
`MacPlaybackTests` and
does not install over production. A failed process inventory retains the guard.

Native QA covers local history/export, audio clock/seek/loop, ruby wrapping,
rotation, large text, creator draft retention and the miniature player's safe
area. Screenshot review is required in addition to XCTest results. Acoustic
quality, microphone measurements with a real voice, and physical Watch behavior
must be reported separately; synthetic audio is not evidence of those passes.

## Current Evidence

- Static manifests, resource identity, native references and 50 Swift syntax
  parses passed. Store tooling: 252 unit tests passed, including12 disposable-path
  guard tests. No shared host or simulator was used for these guard tests.
- Final Intel app build with macOS12 target passed on Xcode26.3. `vtool` on the
  built app's Debug dylib reports minos12.0/SDK26.2. The source-based package
  suite passed69 tests with1 opt-in network skip and0 failures on the iMac.
  This is not a native UI/audio or Monterey runtime result.
- A reachable macOS12.7.6 host was identified read-only; no Musia runtime test
  or desktop takeover has been performed there.
- Candidate is not yet archived, uploaded, processed or assigned to testers.
  Existing iOS and Mac 0.2.1(11) builds were read back as VALID.
- Read-only store version checks confirm iOS0.1.2 remains WAITING_FOR_REVIEW
  and macOS0.1.2 remains READY_FOR_SALE. Neither was mutated.
- The admitted iMac headless round released its exact protocol1 guard; no owned
  compiler/test/runtime remained at handback.
- A separate admitted mobile round ran on Xcode27.0/iOS27.0, serially using the
  existing iPhone18 Pro Max and iPad Pro13-inch simulators. Each passed66 tests,
  skipped1 opt-in live test, and had0 failures (67 total per device). This covers
  native WAV decode/audio clock and the selected six UI tests, not acoustic
  quality, real microphone input or physical-device background playback.
- Mobile round start01:21:09UTC; exact guard release log write01:26:32.880286UTC.
  Fresh01:28:18UTC readback confirmed no compiler/test/Musia child, no guard and
  both owned simulators Shutdown. The host has been handed back.
- Initial screenshot review found landscape `XCUIApplication.screenshot()` captures
  cropped into stale portrait bounds on both devices. The existing full-screen
  Stage captures are correctly oriented. The local test-only repair uses
  `XCUIScreen.main.screenshot()` and asserts orientation dimensions. The admitted
  follow-up ran exactly three selected tests per device, all six executions
  passed. All14 resulting images were inspected: correct portrait/landscape
  canvases, composer above keyboard, accessible transport and navigation.
  Large-text content scrolls beyond the viewport; loading-state images are not
  approved store assets or proof of live-catalog availability.
- Follow-up start01:41:17UTC, exit0 and exact guard release after the final
 01:44:24UTC inventory; independent01:44:32UTC readback confirmed no guard,
  compiler/test/app child or booted simulator. Host handed back to its next owner.
- Conditional Mac hosted tests were skipped before launch: source validation
  found an argv-pattern cleanup probe matching its own verifier. The local
  repair uses exact executable-name inventory, with disposable regression
  coverage for self-match and process-query errors. The later Mac-only round
  below used that repair and verified cleanup.
- Xcode emitted responsiveness warnings for synchronous audio-session calls,
  including test calls. Playback tests passed, but the warnings remain a
  follow-up; do not describe this as a warning-free run.
- The admitted Mac-only round used frozen `185d619` with unchanged app source.
  Build-for-testing passed on Xcode27.0. The separate sandboxed QA identity and
  absence of shared keychain/application groups were verified before launch;
  its private container was confirmed in the runtime log.
- Five Mac test methods ran: three passed (reference audio/metronome, history
  reopen/export, local speed/seek/loop), one failed (ruby fallback layout, three
  assertions), and the live/remote test was skipped. The layout fixture reported
  height1164 for both800-point and180-point widths, violating its bounded-height
  and wrapping checks. Diagnosis must distinguish the offscreen hosting fixture
  from the fallback view itself; neither is cleared by a successful compile.
- The round exited65 without a repair/retry. Exact guard released; independent
  01:57:18UTC inventory confirmed no guard, compiler/test/app or booted simulator.
  Host handed back. AppKit layout reentrancy and CoreMedia warnings were retained.
- Mac runtime qualification is **failed**, not complete. Actual Monterey runtime
  and official Duo tests remain unverified. Signing/internal uploads require
  further qualification and explicit placement. No production/review change.

### Source-Only Layout Diagnosis

The next test fixture attaches the hosting view to a never-shown, test-owned
window and observes rendered geometry until it settles, for at most two seconds
per width. It retains the 20-to-600-point height bounds and narrow-greater-than-
wide assertion, adds assigned-width and non-visible/non-key-window checks, and
logs both rendered and intrinsic fitting sizes. Cleanup detaches the view and
closes only that fixture window. Production layout code is unchanged.

This tests a lifecycle hypothesis, not an established fix. Apple's
[NSHostingView documentation](https://developer.apple.com/documentation/swiftui/nshostingview)
describes layout-time size reporting; it does not establish why this fixture
failed. No local SwiftUI typecheck or runtime is available on the Linux host.
The subsequent native build below compiled the fixture, but did not execute it.
The Mac static validator now checks this candidate's macOS12 deployment target
and inherited minimum-OS plist setting, instead of the released app's macOS14
target. This does not change the released binary or qualify Monterey runtime.

### Mac Layout Round 2

Frozen `0da4ecb` passed build-for-testing and the separate QA sandbox/identity
checks. The hosted test phase reached its 600-second deadline without reporting
any executed test case or rendered/fitting geometry. A one-second process sample
found XCTest waiting for its configuration and IDE session, before test methods;
a startup log also reported a refused test-manager channel. The underlying
cause is not established. No shared service was restarted and no retry ran.

Exit76 retained the guard for explicit cleanup verification. The original
ownership metadata and directory identity matched; the wrapper, owned process
groups and QA app had exited. Exact release was02:33:56UTC; independent02:34:17UTC
inventory confirmed no guard or owned runtime. The incomplete result bundle
lacks its Info.plist and is retained as diagnostic evidence, not a test summary.
Mac qualification and internal signing/upload remain blocked. Earlier successful
mobile tests and the earlier failed Mac geometry assertions are not overwritten.

### Source-Only QA Identity Repair

Review of the saved round2 build log found that the command-line
`PRODUCT_BUNDLE_IDENTIFIER=art.lazying.musia.compatibilityqa` applied to all
three targets. The app-intents metadata commands for Musia, MusiaCore and
MusiaMacTests each show that identical identifier. The previous pre-launch
check examined only the app and could not detect this configuration defect.

The project now derives each target's identifier from `MUSIA_MAC_BUNDLE_PREFIX`
with an empty, `.core` or `.mactests` suffix. Default production identifiers,
provisioning settings, sandbox and hardened runtime remain unchanged. QA alone
overrides the prefix. A read-only artifact verifier rejects the former global
override, production identities, malformed/missing plists and shared-group
entitlements before the test process can launch. Its codesign read has a
20-second deadline. Source-only Ruby checks parse the real project and exercise
the generator in a disposable fixture; they do not run Xcode.

This repairs an observed identity collision, **not a proven cause of the
XCTest startup timeout**. The earlier Mac round ran tests with the same override.
The existing ruby assertions and application Swift sources are unchanged;
the never-shown window fixture still requires a successful native execution.
The local store suite now passes265 tests, including13 identity-verifier tests.
No shared-Mac job, service restart, archive, upload or review mutation was
performed for this repair. A new finite placement is required for native QA;
the KVM signing gate remains closed.

### Mac Identity Round 3

Frozen `3467430` passed the newly admitted build-for-testing and artifact
verification on the Mini. The actual app, embedded core framework and test
bundle now have distinct QA identifiers; package types, contained paths and
the private sandbox/no-shared-groups checks passed before hosted launch.

XCTest still did not execute any method. The owned-process log reported a
refused test-manager channel and an unavailable test daemon; a one-second
sample showed XCTest waiting for its IDE configuration. The sole owned test
process group was stopped at04:02:46UTC after this startup failure, before the
600-second cap. The wrapper returned76 and retained the guard. No retry ran.
The bundle-identity fix is verified but does not resolve the startup problem.
No mandatory method passed, and no live-test skip was observed in this round.

At04:04:55UTC, SSH banner timeouts prevented the cleanup transfer/command and
one bounded cleanup-only reconnect from executing. Cleanup is **pending**:
the guard remains retained, the QA app may remain, and no host handback is
claimed. Original ownership and exact recovery details are in the private
coordination receipt. Do not admit another job from an older cleanup record.
Evidence remains on the Mini; full local mirroring is pending connectivity.
No signing, upload, production, review or shared-service mutation occurred.

Headless evidence hashes:

| Evidence | SHA-256 |
| --- | --- |
| Core test log | `cb75af13ab6b779b34666e0306a7254f4d8c5cef15648434978c71794cb21182` |
| Final Mac build log | `9fa656c251621e0b8268f0316578d27cb247277f46c022fe42b1679e2588c4c2` |
| iPhone test log | `59cc373e19542c884b5916d2ca74018f2b541361ad81f7eb399f5f96ad798243` |
| iPad test log | `e0538438b5c93aec16cadf278d1b912ad3b1c9bad84625ecd6575f0c0ae5e9a9` |
| iPhone follow-up log | `5de6c9b229f43dda409cbbe8eee83f1c335f8e13b4da1c41de5d40379bb136c0` |
| iPad follow-up log | `7f2d19e79127dd9fd9970ab26af26b6f8c34ccefe810bfb8fa64a2a701d04b19` |
| Mac-only build log | `e5ccfcd85669e71f286b40d753c016b904df0e57ae369fccb9ecff9ea2a155a4` |
| Mac-only hosted test log | `33cb40a8efab4bba5a95307795c707a367eaf78e5cdc24f830bc00d067e4cafe` |
| Mac layout round2 build log | `a1351322620fd5bf7376d7d0a8655b14820892efaa3474443fd6c25a67e32e55` |
| Mac layout round2 test-startup log | `c65f5e9f15b5f3d1d35d1f22171f4b4ca87eac292e8ad6bf77f13d44b875d293` |

Initial mobile round source: `b6e9e62`; follow-up: `3ea6c8c`. Application
implementation unchanged since `9119183`. These are simulator UI/runtime checks,
not physical-device or Monterey runtime qualification.

Exact artifacts and final tester states belong in the compatibility handoff and
will be added here after validation. Do not promote this candidate to production.
