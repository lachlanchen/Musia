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
conda run -n musia python -m unittest discover -s tools/store/tests
```

After an explicit shared-Mac queue handback, select the installed toolchain per
command, set `MUSIA_ROOT` to an isolated checkout and run a bounded phase:

```bash
python3 tools/store/apple_build_guard.py \
  --slot-note "exact coordination handback path" --operation "Musia core QA" \
  -- bash tools/store/test_compatibility_apple.sh core /absolute/new/evidence/core
```

Other phases: `mac`, `iphone`, `ipad`. Simulator phases require the existing,
stopped, Musia-owned `MUSIA_SIMULATOR_UDID`. The wrapper releases only its matching
directory/inode/token, and retains an uncertain guard for owner recovery.
Never delete a peer guard or treat a quiet process list as a queue handback.

Native QA covers local history/export, audio clock/seek/loop, ruby wrapping,
rotation, large text, creator draft retention and the miniature player's safe
area. Screenshot review is required in addition to XCTest results. Acoustic
quality, microphone measurements with a real voice, and physical Watch behavior
must be reported separately; synthetic audio is not evidence of those passes.

## Current Evidence

- Static manifests, resource identity, native references and 50 Swift syntax
  parses passed. Store tooling: 238 unit tests passed.
- Initial Intel build with macOS12 target passed on Xcode26.3; subsequent native
  QA changes still require a fresh compile/test round.
- A reachable macOS12.7.6 host was identified read-only; no Musia runtime test
  or desktop takeover has been performed there.
- Candidate is not yet archived, uploaded, processed or assigned to testers.
  Existing iOS and Mac 0.2.1(11) builds were read back as VALID.

Exact artifacts and final tester states belong in the compatibility handoff and
will be added here after validation. Do not promote this candidate to production.
