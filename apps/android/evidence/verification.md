# Android Verification

Implementation date: 2026-09-25. Scope: `apps/android` only.

## Frozen Handoff

App sources and build configuration are frozen at the tested debug APK below.
The final QA handoff changes documentation only; no rebuild was started.
The single-asset `und` label is deferred to a future build.

- Tests: 34 passed, no failures/errors/skips.
- Lint: 0 errors, 12 advisory warnings.
- APK SHA-256 rechecked after main-agent emulator QA and unchanged:
  `04ce7ce7fdfc08390ea22bf6bf70dfddde1e1d6ffa013fa9a9cdd7f1f0553bcb`.
- Android build processes: none remaining. No Gradle or Kotlin daemon matched
  the final process probe. No Android emulator was started for this handoff.
- iOS work is ongoing elsewhere; no iOS process or source was touched.

## Before Build

- Read AiMemo Android and LazyOracle native Android build configuration.
- Reuse shared SDK `/home/lachlan/Android/Sdk`, shared Java 21 and cached
  Gradle 8.14.3. No duplicate SDK, emulator, GUI stack or model job created.
  Actual build JDK inherited from `JAVA_HOME`:
  `/home/lachlan/.sdkman/candidates/java/21.0.10-tem` (Eclipse Adoptium).
- Workstation check: 60 GiB available RAM; 40/71 GiB swap in use. Existing
  desktops and other projects' build processes were left untouched.
- Backend contract read from `docs/learning-api.md`. Native models align with
  asset-specific timelines, nullable BPM/meter, optional beat indices and
  string note/number-note fields. All times are seconds.
- Public API initially failed DNS, then failed TLS negotiation while deployment
  was in progress. No catalogue or media success was fabricated.

## Build

The initial permitted invocation ran:

```text
bash ./gradlew --no-daemon --max-workers=2 :app:assembleDebug :app:testDebugUnitTest
```

- Result: `BUILD FAILED in 52s`, 23 tasks executed.
- Dependency resolution, Android resource/manifest processing and external DEX
  merging completed. Kotlin reported only the unavailable auto-mirrored
  `LibraryMusic` import and its use in `MusiaApp.kt`.
- Bounded source fix applied: use the cached `Icons.Default.LibraryMusic`.
- That first attempt produced no APK or unit-test results. The user subsequently
  authorized bounded sequential compile/test/lint reruns until passing.
- Raw build log: `evidence/build-debug.log` (ignored generated evidence).
- Build process and its single-use Gradle daemon exited. No Gradle/Kotlin daemon
  remained in the post-build process check. RAM available: 59 GiB, swap 40/71 GiB.
- No release key provided or read. No release task executed.

## Final Result

Completed 2026-09-25 14:24 UTC (22:24 Hong Kong). Final command:

```text
bash ./gradlew --no-daemon --max-workers=2 :app:assembleDebug :app:testDebugUnitTest :app:lintDebug
BUILD SUCCESSFUL in 1m 2s
53 actionable tasks: 26 executed, 27 up-to-date
```

- Three invocations total, never overlapping: initial icon-import failure;
  authorized retry with successful APK/tests but an API-26 style lint error;
  final successful build after removing that attribute and making local-data
  backup exclusions explicit. No dependencies were upgraded to clear warnings.
- APK: `app/build/outputs/apk/debug/app-debug.apk`, 21,261,962 bytes.
- SHA-256: `04ce7ce7fdfc08390ea22bf6bf70dfddde1e1d6ffa013fa9a9cdd7f1f0553bcb`.
- `apksigner verify --verbose`: verifies, APK signature scheme v2, one debug signer.
- `aapt dump badging`: `art.lazying.musia`, version 1 / 0.1.0, min SDK 26,
  target/compile SDK 36, launcher `art.lazying.musia.MainActivity`.
- Unit tests: **34 passed, zero failed/errors/skipped**. Contract 12, timeline 12,
  guitar shapes 3, original-text lyric parts 7.
- Lyric tests include Aya's `Lay, ay, ay, ay`, sequential repeated tokens,
  punctuation, multilingual whitespace, mismatch/empty-token full-line fallback,
  and keeping pronunciation readings separate. UI renders only one lyric line.
- Lint: **0 errors, 12 warnings**. Warnings are pinned dependency/target-version
  notices and two optional Kotlin extension suggestions. A HelpOutline icon
  deprecation warning remains; it does not prevent compile or lint success.
- Reports: `app/build/reports/tests/testDebugUnitTest/index.html` and
  `app/build/reports/lint-results-debug.html`.
- Logs: `evidence/build-debug.log`, `evidence/build-debug-retry.log`,
  `evidence/build-debug-final.log` (ignored generated evidence).
- Musia final Gradle daemon PID 3741507 exited at 22:24:00 Hong Kong. Its
  `currentDir` was verified as this subtree. Other projects' processes were not
  stopped. Post-build available RAM 58 GiB; swap 40/71 GiB. No Android-owned GUI
  port was added. The Musia heavy-build slot is free.

## Public API Smoke

Once deployment became reachable, read-only HTTPS requests succeeded:

- `/healthz`: HTTP 200, `{"status":"ok"}`.
- `/api/v1/library`: version 1, 32 items, `first-pulse` first.
- `/api/v1/songs/first-pulse`: 22 seconds, 60 BPM, verified beats/chords,
  unavailable melody, no lyrics.
- `/api/v1/songs/aya-chan-hikari-ame`: three language assets; confidence remains
  analysis/unavailable, not verified. English first line and tokens match the
  spacing regression fixture exactly.
- `/api/v1/lessons`: three known lesson IDs, all scoped to `first-pulse`.

These HTTP checks do not prove Android playback or audio audibility.

## Runtime Handoff

- Current Android-owned noVNC URL: none.
- Android-owned GUI/emulator/tmux sessions: none.
- No service/device runtime started by this implementation.
- Main agent completed coordinated emulator QA on `Musia_Review_API34`, serial
  `emulator-5586`. Read-only verification of the main-owned
  `.runtime/learning/android-review/result.json` confirms:
  - Curated native guitar diagram visible in Play mode; main reports visual QA passed.
  - First Pulse loads and Media3 reaches PLAYING.
  - Media3 remains PLAYING after Home.
  - Media3 remains PLAYING with the emulator display asleep.
- Main reports the app force-stopped and emulator closed after evidence capture.
  This handoff independently verified ports 5586/5587 have no listeners and no
  `Musia_Review_API34` process remains. The Android heavy-build slot is free.
- Limits retained from the QA result: emulator state checks do not establish
  audible pitch quality or behavior under real-device interruptions. Physical
  device/audio-focus, full accessibility/layout, loop-boundary audition and
  export/reset coverage remain release QA considerations, not claimed results.
- No store release was built or signed. Release credentials were not supplied;
  the signing gate was not exercised with credentials.
