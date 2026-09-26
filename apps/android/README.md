# Musia Native Android

Native Kotlin + Jetpack Compose application, ID `art.lazying.musia`. No WebView,
Capacitor, account, microphone, analytics SDK, or server-side practice progress.
Only this subtree is owned by the Android implementation.

## Shared Toolchain

Matches the cached patterns read from `../../../AiMemo/android` and
`../../../LazyOracle/native/android`: AGP 8.13.0, Kotlin/Compose compiler 2.1.0,
Compose BOM 2025.09.00, Gradle 8.14.3, shared OpenJDK 21, Java bytecode 17,
Android SDK/target 36, minimum Android 8.0/API 26. Media3 is pinned to 1.8.0.

`gradlew` is deliberately a small **shared installation launcher**, not a binary
wrapper. It finds the existing Gradle 8.14.3 distribution in `~/.gradle`, or uses
`GRADLE_HOME`. It does not download a Gradle distribution, SDK, or JDK. The normal
Gradle dependency cache is shared. Media3 dependencies may need Maven access on
the first build. No SDK or third-party repository is vendored here.

```bash
cd /home/lachlan/ProjectsLFS/Musia/apps/android
export JAVA_HOME=/home/lachlan/.sdkman/candidates/java/21.0.10-tem
export ANDROID_HOME=/home/lachlan/Android/Sdk
free -h
pgrep -af 'GradleDaemon|gradle.*Musia|Xvfb|x11vnc|websockify'
tmux list-sessions
ss -ltnp
bash ./gradlew --no-daemon --max-workers=2 :app:assembleDebug :app:testDebugUnitTest :app:lintDebug
```

Use a complete existing JDK containing `javac`, not only a Java runtime. The
system `/usr/lib/jvm/java-21-openjdk-amd64` currently lacks that compiler.
The launcher accepts `JAVA_HOME` or reuses the shared SDKMAN Java installation.

Debug APK: `app/build/outputs/apk/debug/app-debug.apk`. Unit-test report:
`app/build/reports/tests/testDebugUnitTest/index.html`. Do not commit build trees.
Do not overlap this command with another Musia heavy build. Bounded sequential
rebuilds were explicitly authorized after the first compile; no emulator or GUI
stack was started by this implementation.

## Release Signing

Release tasks fail closed without `MUSIA_SIGNING_PROPERTIES`. The gate checks
the resolved task graph, including `build`, aliases, and abbreviated release
task names. Debug signing is never used as a release fallback.

Provision a private absolute properties path **outside this source subtree**,
with POSIX mode 600. Its fields are `storeFile` (absolute path), `storePassword`,
`keyAlias`, and `keyPassword`. The existing keystore must also be outside this
subtree, with no group/other access. Do not put secrets in CLI arguments, source,
logs, or commits. The build never generates a release key.

```bash
export MUSIA_SIGNING_PROPERTIES=/protected/private/location/musia.properties
bash ./gradlew --no-daemon --max-workers=2 :app:bundleRelease
```

This is a future release command, not an additional build performed by this
delivery. Release signing and Play publication require separately provisioned
credentials and authorization.

## API and Honest States

- Origin is fixed to `https://musia.lazying.art`.
- Requests: `/api/v1/library`, `/api/v1/songs/{id}`, `/api/v1/lessons`, `/healthz`.
- Repository contract: `../../docs/learning-api.md`.
- Times are seconds on each selected asset's original audio timeline; interval
  ends are exclusive. `kind: "exercise"` selects the exercise list.
- Relative media URLs resolve against the API origin. Cleartext URLs and URLs
  containing credentials are rejected. Unknown JSON fields are ignored;
  unsupported versions and malformed required content produce retryable errors.
- No fabricated catalogue, bundled demo audio, or persisted catalogue fallback.
  A refresh failure may retain an explicitly labelled response from this process.
  Empty successful results are distinct from network errors. No successful
  `/healthz` result is presented as proof of media availability.
- Missing/unknown confidence is unavailable. Analysis and estimates are labelled
  unverified. Empty event arrays stay unavailable. No BPM-generated beat grid.
- First Pulse lessons match both lesson ID and `exerciseId: first-pulse`.
  Only that verified exercise has count-in, practice-bar, and decay phases.
  Other songs get generic musical guidance, no inferred bar/downbeat counting.
- Public privacy/support links: `/privacy` and `/support`.

## Playback and Practice

`PlaybackService` owns ExoPlayer and MediaSession, audio focus, becoming-noisy
handling, wake behavior, session notification, and history checkpoints. The
activity uses a MediaController. Android's media notification provides playback
controls while the UI is backgrounded. The service is non-exported.

Speed is 0.25x through 2.0x with pitch fixed at 1.0. Selecting a phrase creates
a Media3 clipped media item with `REPEAT_MODE_ONE`; there is no UI-timer-based
seek loop. Display positions map back to the original asset timeline. Clearing
a loop retains the absolute position. Changing assets clears the old loop.
Loop changes re-prepare the source and may buffer; sample-perfect gapless
looping has not been claimed.

Listen shows current lyrics/tokens and current/upcoming chords. Tap reports
local touch offsets against supplied beats in real-time milliseconds, corrected
for playback speed. Play adds the available melody guide and remains self-guided.
No guitar, singing, pitch, or microphone accuracy is measured.
Word highlighting matches tokens sequentially within the original lyric text;
it never reconstructs whitespace or punctuation. If any token cannot be matched,
the entire original line displays without word highlighting. Active-token
pronunciation readings appear separately and never modify the original text.
Play includes all 24 major/minor standard-tuning fretboard diagrams, low E on
the left, with open/mute markers, finger numbers, explicit barres, shifted fret
windows and TalkBack descriptions. The source is `../shared/guitar-shapes.json`;
verify generated tables with `python tools/generate_guitar_shapes.py --check`
from the repo root. Unsupported extensions/slash chords remain explicitly
unavailable; there is no guessed simplification or transposition.

No tap is accepted while paused/buffering, before the first supplied beat, or
after the last supplied beat. Feedback clears in those states. Positive manual
calibration subtracts from late offsets; it does not alter the audio. Output
latency, touch latency, Bluetooth, and incorrect beat analysis remain limitations.

History records actual playing wall time, not media seek distance or paused
time. The service checkpoints every five seconds and on transitions. Abrupt
process termination can lose the latest checkpoint interval. Sessions span
pause/resume of the same song/asset/mode while the service survives. A changed
song, asset, mode, or service lifetime starts a new session.

## Privacy and Local Data

Preferences and the newest 200 sessions use app-private SharedPreferences.
Each session retains at most its latest 1,000 tap offsets. No practice history
or taps are uploaded. Export uses Android's document picker, requires no storage
permission, and includes preferences/history in versioned JSON. The user chooses
the destination, which may itself be a cloud document provider. Reset stops and
clears playback and removes local history/preferences, but not existing exports.
Corrupt saved data is reported and preserved until explicit reset.

Cloud app backup is disabled, with explicit Android 12+ cloud and device-transfer
exclusions. Covers are bounded to a 12 MiB in-memory bitmap
cache; no persistent media cache is configured. API/audio/cover hosts receive
normal HTTPS requests, IP addresses and request metadata. No credentials are
sent. The merged APK requests Internet, network-state, media-playback
foreground-service, wake-lock, and AndroidX's app-scoped non-exported receiver
permission. It requests no microphone, camera, account, or storage permission.
Uninstall removes app-private data.

## Verification Scope

Unit tests cover half-open intervals/gaps, invalid data, phrase-loop boundaries,
absolute/relative clipping positions, speed-corrected tap offsets, calibration,
strict first/last-beat guards, actual playing time, JSON compatibility,
confidence labels, First Pulse-only lessons/phases, and HTTPS URL policy.

Before release, use a physical device for notification controls, lock-screen
playback, audio focus/headphones, repeated loops at 0.25x and 2x, rotation and
process recreation, offline retry, export/reset, large fonts, TalkBack, and
phone/tablet layout. No device, emulator, screenshots, audio audition, or signed
release is implied by a successful JVM test/debug build. Build evidence is in
`evidence/verification.md`.

Implementation reference: Android's official [MediaSessionService background
playback guide](https://developer.android.com/media/media3/session/background-playback).
