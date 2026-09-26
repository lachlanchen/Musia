# Internal Beta Review

2026-09-26. The owner requested a test version. This review supports restricted
internal testing, not production qualification, a legal rights certification,
or a claim that all device behavior already works.

## Scope And Content

The native clients read Musia's existing public, published music catalog and a
synthetic First Pulse exercise. The API excludes hidden/preview media and
restricts audio URLs to the existing MusiaSongs/Fun hosts. It exposes no private
Studio files, user uploads, generation tools, model credentials or agent chat.
The owner has commissioned the catalog's music and its public website delivery;
this beta introduces no new song publication or third-party catalog import.
Detailed commercial content-rights clearance remains a production task.

First Pulse is the initial test route. AI song analyses are visibly unverified;
they must not be presented as accurate scores or guitar-performance assessment.
The beta invitation must not promise completed AI generation/coaching features.

## Privacy And Permissions Review

Source review: API/audio/cover reads use HTTPS; no microphone, camera, speech
recognition, contact or advertising-ID permission, no analytics SDK, no remote
practice-history write endpoint. Local history/export is device-local. Ordinary
IP/request metadata reaches the streaming hosts, as the app privacy text says.
iOS uses platform networking/AVFoundation, not custom encryption; its existing
non-exempt-encryption flag is unchanged. Inspect actual signed binary identity,
signature, permissions and provisioning again before uploading.

## Evidence And Limitations

- Android: 34 release unit tests and lint; exact signed APK launched on the
  Musia emulator, rendered guitar shape, and Media3 remained PLAYING in the
  foreground, Home background and display sleep. This does not verify audible
  quality, physical-device interruptions or native offline persistence.
- iOS: 22 core tests including live API; full simulator app compiled and the
  native First Pulse practice UI rendered. Its AVPlayer test failed with
  -11800/-12746, also reproduced by a bare AVPlayer on the audio-less virtual
  Mac. This remains failed/unresolved, not a passed playback test. Internal
  TestFlight enables the owner to assess it on an audio-capable device.
- The signed IPA requires separate archive/export and signature inspection;
  simulator evidence is not evidence that those operations succeeded.

Private beta QA receipts bind exact source/build/artifact hashes and the actual
evidence files. `--internal-beta` requires passed unit, native-UI, permissions
and content-review evidence plus explicit limitations. It cannot satisfy the
unchanged full QA checks. No production submission command is enabled.

## Owner Device Test

Open Practice > First Pulse. Check audible count-in, Em/Am changes, 0.25x/1x/2x
playback, repeat/seek, Home/screen lock and headphones. Try an Aya song and
report loading errors or timing problems. Check local history after restarting
the app, export/cancel and reset. These are test requests, not passed checks.

Internal testing references: [Apple internal testers](https://developer.apple.com/help/app-store-connect/test-a-beta-version/add-internal-testers)
and [Google testing tracks](https://support.google.com/googleplay/android-developer/answer/9845334).
