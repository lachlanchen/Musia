# Learning App Delivery Checkpoint

Updated: 2026-09-26. This is a first learning release, not a claim that the entire
music creation roadmap or store publication is complete.

## Available

- [x] Public HTTPS app: https://musia.lazying.art
- [x] 31 published songs and one known-timing Em/Am reference exercise.
- [x] Browser listen/tap/play practice, 25-200% speed, phrase looping, current
  lyrics/readings, chord shapes, local progress and creative-brief export.
- [x] Dedicated read-only API. Private Studio/generation controls are not exposed.
- [x] 29 API tests, 7 web logic tests, 6 deployment tests, 27 store-tool guard tests.
- [x] Real public-site browser playback and workflow tests; screenshots checked
  at desktop and mobile sizes, no horizontal overflow at 320-1440 px.
- [x] Native Android debug build, 34 unit tests and lint without blocking errors.
- [x] Android API 34 emulator: reference playback, curated guitar diagram,
  Media3 PLAYING after Home and display sleep. The dedicated emulator was closed.
- [x] The exact signed release APK passed the same native smoke checks;
  screenshots and session evidence are in `.runtime/learning/android-release-review/`.
- [x] Swift core: 22 tests pass on the existing Mac build host.
- [x] Complete iOS unsigned simulator application builds for arm64 and x86_64.
- [ ] iOS native playback qualification: the virtual Mac has no audio devices;
  AVPlayer readiness failed with an invalid audio-clock error. Native WAV
  decoding passed. This is not a successful playback test.

All automatic song analysis is labeled conservatively. An API/schema check is
not independent evidence of musical correctness. The synthetic exercise is
verified by construction, not by claims about AI accuracy.

## Stores

- [x] Existing developer accounts and owner's test recipient established from
  prior successful project receipts; recipient kept in protected configuration.
- [x] Musia-specific Apple bundle identifier and App Store provisioning profile.
- [x] Separate Musia Android upload key, protected and ignored by Git.
- [x] Signed Android 0.1.0 (1) APK and AAB; 34 release unit tests passed,
  release lint passed, package/permissions and both signatures verified.
- [x] Apple app `6816265930`, **Musia: Learn Music & Guitar**; restored company
  login and exact bundle verified. The bare Musia name was unavailable.
- [x] Owner confirmed paid USD 2.99 on both platforms as the future default.
- [x] Google app `4973883817798043601`, exact package verified; owner-confirmed
  create-app policy/export declarations applied.
- [x] US price USD 2.99 saved and freshly read back in both consoles. Regional
  conversion is set; distribution countries and public availability are not.
- [x] Signed iOS archive/export and exact signature/profile inspection; Apple
  validation/upload succeeded and build 0.1.0 (1) processed VALID.
- [x] TestFlight **Musia Internal**, one owner tester and build 0.1.0 (1):
  **Testing**. Tester status **Invited**, verified after reload and by API.
- [x] Google 0.1.0 (1) **Available to internal testers**; exact owner-only tester
  list and member verified. Gmail confirmed its installation invitation sent.
- [ ] Remaining production checks including commercial content rights,
  physical-device audio interruptions, persistence and accessibility.
- [ ] Formal review submissions; neither store submission is claimed.

See [store runbook](../store/README.md) and its provider-readiness receipt. Do not
turn an unsigned debug APK, a profile, or an invitation plan into a publication
claim. Physical-device audio focus/interruption tests, native accessibility,
offline persistence, content rights and exact binary privacy checks remain
release gates.

This owner-only beta uses documented limitations, not full production
qualification. The iOS simulator playback failure remains unresolved pending
device testing. Invitations do not prove installation or email receipt.
Android install: https://play.google.com/apps/internaltest/4701000336240069263
(use the configured tester account). iOS installation uses the TestFlight
invitation. Both native builds are **0.1.0 (1)**.

## Reproduce And Inspect

- [App setup](../apps/README.md)
- [API contract](learning-api.md)
- [Deployment and rollback](../deploy/learning/README.md)
- [Product story and curriculum principles](../references/musia-learning-app-2026-09-25.md)
- Browser: `scripts/test_musia_learning_web.py --base-url https://musia.lazying.art`
- Android: `scripts/test_musia_android.py --serial emulator-5586 --apk <debug.apk>`

The Android smoke script refuses physical devices and non-Musia AVD names. It
uses the observed UI controls and examines Musia's own media session. Emulator
state evidence does not prove audible quality on a phone. Debug APKs, screenshots,
raw logs, signing material and provider receipts remain outside Git.

Signed Android artifacts are kept in the ignored directory
`store/.runtime/artifacts/android-0.1.0-1-87c66c5e98e6/`:
`Musia-qa.apk`, `Musia.aab`, and `build.json`. The APK SHA-256 is
`67958e013c0de2094a390afc72de049c4c8a10352f5b5256c2f62d3148c45fd4`.
No store upload follows automatically from a successful signed build.

## Deferred Capabilities

No cloud generation, user upload, AI chat coach, microphone assessment or
cross-device sync is enabled in this release. Creative drafts are exportable
inputs, not generated music. Existing local production tools and the Fun media
site are unchanged. The next native iteration needs more verified exercises,
reviewed song scores, accessible guitar guidance and device testing before
expanding to assessed AI coaching or authenticated creation jobs.
