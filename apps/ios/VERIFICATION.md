# Verification

## Local (2026-09-25)

- Inspected Musia/parent AGENTS, AiMemo's XcodeGen setup, and LazyOracle's native
  source/project regeneration pattern. Only `apps/ios` is edited by this work.
- Checked-in Xcode project generated with Ruby xcodeproj 1.27 on Linux.
- Shell syntax, manifest/resource/project checks and Swift syntax parsing are
  run locally; this does not establish Swift compilation.
- Live library endpoint returned HTTP 200 after initial deployment DNS failure.
- Remote Mac path confirmed: `echomind-kvm-macos`, Xcode developer directory
  `/usr/local/echomind-formal-xcode/Xcode_26.6.app/Contents/Developer`.
- No signing, export, upload or submission attempted. No borrowed bundle IDs.

## Coordinated Mac Run (2026-09-25)

Source mirror: `~/Projects/Musia/apps/ios`, one build at a time, one compiler job.

- Swift package: **22 tests passed**, including opt-in live library, First Pulse,
  Aya and lessons API checks.
- Complete unsigned simulator application: **build passed**, arm64 and x86_64.
  Product bundle ID read back as `art.lazying.musia`.
- Dedicated Musia iPhone 17e, iOS 26.5: 21 core tests passed, 1 opt-in live test
  skipped. Native UI launched and rendered, but the playback smoke test failed.
- Device-cache WAV validated by ffprobe and Apple afinfo: signed 16-bit PCM,
  24 kHz mono, 22 seconds. Direct iOS `AVURLAsset` playability/duration test passed.
- Actual AVPlayer readiness failed with AVFoundationErrorDomain -11800,
  underlying NSOSStatusErrorDomain -12746. Installed SDK defines the latter as
  `kCMClockError_InvalidParameter`.
- Functional player verification is **not passed**. Failed-run screenshots are
  diagnostic evidence only, not proof of successful playback.

## Final Bounded Diagnostic

After Android's signed build completed, exactly one final targeted Xcode run
finished at 14:57 UTC on 2026-09-25, using Xcode 26.6 (17F113), macOS 15.7.9,
and the dedicated Musia iPhone 17e simulator running iOS 26.5 (x86_64).
Application and test targets compiled; the test operation exited 65:

| Test | Observed result |
| --- | --- |
| Native WAV playability and duration | Passed; playable, 22 seconds |
| Bare AVPlayer with activated audio session | Failed; item status `.failed`, -11800 / -12746 |
| Musia controller readiness and clock | Failed; identical -11800 / -12746 |

The bare-player test bypasses Musia's controller, status observers, and disabled
Play button. Session activation succeeded; the simulator reported a Speaker
route and 48 kHz sample rate, but the item still failed before playback. The
host's `system_profiler SPAudioDataType` reported no audio devices. This strongly
supports a simulator/host audio-clock limitation, rather than the theory that
Musia's disabled Play button prevents session activation. It does not establish
functional playback on a real device or prove the precise host-level cause.

No production readiness override, fake media clock, test skip, audio driver,
global Mac configuration, keychain change, VM change, signing or upload was used.
Tests retain real playback assertions. An audio-capable Mac or physical device
is required for the remaining functional acceptance checks.

Reproduce after coordinating the shared build slot and selecting an owned device:

```bash
export MUSIA_BUILD_COORDINATED=1 MUSIA_BUILD_JOBS=1
export MUSIA_DEVELOPER_DIR=/usr/local/echomind-formal-xcode/Xcode_26.6.app/Contents/Developer
export MUSIA_TEST_DESTINATION='platform=iOS Simulator,id=YOUR_OWNED_SIMULATOR_UUID'
MUSIA_ONLY_TESTING=MusiaTests/PlaybackIntegrationTests bash scripts/build.sh test
```

Evidence retained outside version control:

- Local `apps/ios/.runtime/core-tests-3.log`: 22 passing Swift tests, live API enabled.
- Local `apps/ios/.runtime/player-final-diagnostic.log`: final Xcode operation.
- Remote `~/Projects/Musia/apps/ios/build/Tests-20260925T145559Z.xcresult`:
  final diagnostic, 1 passed / 2 failed / 0 skipped.
- Remote `build/Tests-20260925T143545Z.xcresult`: earlier native UI smoke failure.
  Local `.runtime/QA-attachments` and `.runtime/readiness-error.png` retain
  screenshots for diagnosis only, not successful-playback or store evidence.

Cleanup verified: owned Musia simulator is shutdown, no Musia app/Xcode job
remains, and the project build lock is absent. The unrelated simulator was left
untouched. No project-owned noVNC stack was started. Heavy slot is released.
Source and documentation are frozen for the main agent to stage; no commit made.

## Device Review Still Required

- Real audio at 0.25x, 1x, 2x, slow-rate pitch quality and decoded duration.
- Lyric/token edges, phrase/manual A-B loops including a B at audio end.
  AVPlayer seeks are not sample-accurate gapless looping; audible seek gaps
  can occur, especially with remote media. No gapless claim is made.
- Lock screen, Control Center and headset actions; interruptions, disconnect,
  app backgrounding, network loss/retry, and media-services reset.
- First Pulse count-in and Em/Am diagrams; Aya and other songs must not inherit
  those instructions or a claimed downbeat phase.
- Small iPhone, iPad, rotation, accessibility text sizes, VoiceOver, glyph/ruby
  readability, cover loading, export cancellation and reset confirmation.
- Signing/provisioning, archive/export, privacy review, and store screenshots.
