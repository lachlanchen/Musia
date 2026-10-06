# Musia Native iOS

The native [macOS target](../macos/README.md) shares the core, services and views;
its sidebar, window and menu entry point remain separate from this iOS app.

Native SwiftUI, AVFoundation/AVPlayer and MediaPlayer. No WebKit, PWA, account,
analytics SDK, microphone, or server progress. Bundle ID: `art.lazying.musia`.
Minimum iOS 17; iPhone and iPad. The checked-in `Musia.xcodeproj` and shared
`Musia` scheme are the normal build path. XcodeGen is **not required**.

Verification (2026-09-25): full unsigned simulator app compilation passed and
22 Swift core tests passed. Functional playback is **not verified**: the remote
Mac has no audio devices, and both Musia and an independent, active-session
AVPlayer fail with the same audio-clock error. The native WAV asset check passes.
No fake readiness or simulator workaround is included. See
[VERIFICATION.md](VERIFICATION.md) before release or signing handoff.

## Experience

- Library and lessons use `https://musia.lazying.art/api/v1`; HTTP, malformed
  contract, version, and playback failures are visible with explicit retry.
- Native covers, searchable library, audio-version selection, current/next
  lyrics and chords, token readings, phrase selection, and manual A/B looping.
- Sequential token matching preserves original `line.text`, including spaces
  and punctuation. Any unmatched token disables all highlighting for that line.
- Listen / Tap / Play modes; speed 0.25-2x with AVPlayer's spectral
  pitch-preserving algorithm. Extreme slowdown quality depends on the recording.
- Tap offsets use the current media clock and playback rate, never a UI timer.
  No taps are evaluated while paused, seeking, buffering, outside the first/last
  reference beat, or without beat confidence. One tap per reference beat per pass.
  This is screen-tap feedback, **not singing or guitar grading**. Bluetooth and
  device latency remain uncalibrated. Unmatched taps do not become a score.
- Only First Pulse has count-in/bar phases and Em-at-4s/Am-at-8s instructions.
  Other songs retain generic practice guidance and an unverified-downbeat label.
- Play mode includes all 24 major/minor shapes in standard tuning, open/muted
  strings, finger numbers, explicit barres, shifted fret windows and VoiceOver
  descriptions. The source is `../shared/guitar-shapes.json`; verify generated
  tables with `python tools/generate_guitar_shapes.py --check` from the repo root.
  Unsupported extensions/slash chords have no guessed fingering. No native
  transposition/capo engine.
- The mini-player reserves space within each tab's content, above native tab
  navigation, with an opaque background. It never overlays the outer TabView.
- API confidence is shown independently for beats, chords, and melody. Absent
  events are unavailable, not fabricated from BPM.
- One app-owned player survives sheet dismissal and supports background audio,
  lock-screen Now Playing, artwork, play/pause, skip, and scrub commands. Audio
  interruptions and headphone removal pause safely. No extra background mode.
- Up to 200 local sessions in app-only UserDefaults. History checkpoints every
  five seconds of runtime and on pause/backgrounding. JSON export uses the
  native Files exporter; reset clears history, speed, mode, and loop state.
  A force kill may lose the most recent uncheckpointed interval.

## First Pulse

The library has an explicitly local exercise in addition to the live catalog.
It synthesizes a 24 kHz mono PCM WAV into the app cache: four clicks at 0-3s,
Em at 4-8s, Am at 8-12s, Em at 12-16s, Am at 16-20s, then a two-second fade.
Clicks are exactly one second apart through 19s. Notes are MIDI 52/55/59 for Em
and 45/48/52 for Am. Beats/chords are verified by construction, not model output.
No generated audio is tracked. This matches the backend exercise structure in
`musia/learning.py`; it is not an offline copy of the song catalog.

## Build and Test

Inspect resources and coordinate with the Android build owner before compiling.
Scripts never SSH, upload, start another app's runtime, or install an SDK.

```bash
cd apps/ios
export MUSIA_DEVELOPER_DIR=/usr/local/echomind-formal-xcode/Xcode_26.6.app/Contents/Developer
bash scripts/build.sh preflight

# Only after the shared build slot is confirmed:
export MUSIA_BUILD_COORDINATED=1
export MUSIA_BUILD_JOBS=1
bash scripts/build.sh core-test
bash scripts/build.sh build

# Pick one installed simulator; no implicit new simulator or SDK download:
DEVELOPER_DIR="$MUSIA_DEVELOPER_DIR" xcrun simctl list devices available
export MUSIA_TEST_DESTINATION='platform=iOS Simulator,id=YOUR_SIMULATOR_UUID'
bash scripts/build.sh test
```

`core-test` runs the Foundation-only Swift package on macOS. `build` compiles
the complete iOS app for a generic simulator without signing. `test` runs the
same core XCTest suite plus AVPlayer integration tests in the app-hosted iOS
test bundle, followed by the native UI smoke test. All build artifacts
are ignored under `build/`; a project-local lock prevents concurrent builds.
Run commands sequentially, with at most one Musia test simulator. Capture
evidence, then terminate only the app/test simulator you started.

For a bounded player diagnostic on that same owned simulator:

```bash
MUSIA_ONLY_TESTING=MusiaTests/PlaybackIntegrationTests bash scripts/build.sh test
```

This compiles the app and test targets, checks native WAV playability/duration,
then checks actual player readiness and media-clock advancement both through
Musia and through a bare AVPlayer with an explicitly activated audio session.
It does not fake readiness or skip failed playback. A virtual Mac without an
audio output device can fail simulator playback even when the asset is valid;
inspect `system_profiler SPAudioDataType` and the test's underlying NSError.
Confirm playback on an audio-capable Mac/device before claiming it works.

Linux static checks (not Swift type checking):

```bash
PYTHONNOUSERSITE=1 conda run -n musia python apps/ios/scripts/validate.py
bash -n apps/ios/scripts/build.sh
```

`validate.py` checks manifests, PNG integrity/dimensions, resource references,
the shared scheme, and absence of WebKit. If `tree_sitter` and
`tree_sitter_swift` are available it also parses Swift syntax. Tests cover
half-open intervals, lyric gaps, seeks/loops, rate bounds, reference beat limits,
tap-rate math, First Pulse PCM/metadata, known chord shapes, guidance isolation,
lyric reconstruction, JSON contracts, HTTP errors, and local history/reset/export.

For maintainer-only regeneration, use `xcodegen generate --spec project.yml`,
or Ruby `xcodeproj` 1.27 with `ruby scripts/generate-project.rb`. The checked-in
project uses a native `MusiaCore.framework`, while `Package.swift` exposes the
same source to command-line tests. No third-party runtime dependencies.
Raster exports can be reproduced with `node scripts/generate-assets.mjs`
(ImageMagick required for icon resizing). The generated ribbon masters live in
`apps/shared/brand/`; do not replace them with the First Pulse exercise bars.

## Signing and Export

No team, identity, profile UUID, token, or credential is embedded in the project.
Coordinate with the publishing owner before release work. The simulator build
needs none of these values. For an explicitly authorized later archive:

```bash
export MUSIA_DEVELOPMENT_TEAM='approved-team-from-operator'
export MUSIA_SIGNING_IDENTITY='installed-identity-from-operator'
export MUSIA_PROVISIONING_PROFILE='Musia-specific-profile-from-operator'
export MUSIA_BUILD_NUMBER='operator-selected-build-number'
bash scripts/build.sh archive
export MUSIA_EXPORT_OPTIONS_PLIST='/absolute/private/path/ExportOptions.plist'
bash scripts/build.sh export
```

Export is local only; upload destinations are rejected. There are no App Store
submission commands. Signing inputs stay outside the source tree.
External build tooling must pass `MUSIA_APP_PROFILE`, not a global
`PROVISIONING_PROFILE_SPECIFIER`: the checked-in app target resolves this custom
setting, while `MusiaCore.framework` must not receive an app provisioning profile.

## Privacy and Verification

`Info.plist` declares only background audio, with normal HTTPS transport
security. No recording/location/photo permission is requested. The privacy
manifest declares app-only UserDefaults (`CA92.1`), no tracking and no app-side
collected data. History stays local unless the person exports it. Public API
and cover/audio hosts necessarily see ordinary network requests; operators
must separately review server logging and final store privacy disclosures.

Apple references: [pitch algorithm](https://developer.apple.com/documentation/avfoundation/avplayeritem/audiotimepitchalgorithm),
[Now Playing](https://developer.apple.com/documentation/mediaplayer/mpnowplayinginfocenter),
[required-reason APIs](https://developer.apple.com/documentation/bundleresources/app-privacy-configuration/nsprivacyaccessedapitypes/nsprivacyaccessedapitype).

See [VERIFICATION.md](VERIFICATION.md) for observed results and remaining
device checks. Compilation is not evidence of acoustic loop precision,
background reliability, accessibility layout, or store readiness.
