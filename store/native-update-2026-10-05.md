# Native 0.1.2 Update

## Release Scope

Native iPhone/iPad, macOS and Android now include:

- Independently selected lyric languages, default English / 中文 / 日本語.
- Chinese pinyin and Japanese furigana attached to the correct text.
- Current and upcoming lines from the selected vocal's own translation set.
- Settings > Practice history, without a separate History navigation tab.
- Do Re Mi reference notes and first-answer listening quizzes.
- A 40-160 BPM metronome, tap-offset feedback and optional Em/Am practice.

This is ear training, not microphone pitch measurement or a singing/guitar grade.
No new microphone permission, account, subscription or analytics SDK was added.
Existing song background playback remains supported. Lesson sounds stop when
leaving the lesson or backgrounding the app.

## Exact Candidates

| Platform | Version | SHA-256 | Delivery |
| --- | --- | --- | --- |
| Android | 0.1.2 (3) | `0bd51cd813effb9082a297a0e310dbdfa5495dcf361f19df1a7b1c7a22b639e3` | Internal testing available; production changes in review |
| iOS | 0.1.2 (4) | `10c1d046df2970a99995ece42b1ea670b855817e20b1b2dac37135e37721ddb7` | Signed IPA prepared; not uploaded |
| macOS | 0.1.2 (4) | `8b851ea56603eec7d50f84584a8175ec3b29abcdc2fd7d41df34b23ce2187807` | Signed universal PKG prepared; not uploaded |

The owner explicitly chose to preserve the Apple review queues. Fresh API
readback on October 5 still shows **iOS 0.1.1 and macOS 0.1.1 WAITING_FOR_REVIEW**.
Neither submission was withdrawn, replaced or resubmitted. Preparation of 0.1.2
does not mean that version is in TestFlight or App Store review.

Google 0.1.1 (2) remains the public production release while 0.1.2 is reviewed.
Code 3 was uploaded once, qualified against the exact signed artifact, and
published to the existing internal track. No tester list or invitation changed.
No device support was lost in Google's comparison. Two nonblocking warnings:
missing deobfuscation mapping and native-library debug symbols. No release-only
R8/signing change was slipped into this update to silence them.

USD2.99 pricing, existing eligible regions, Apple manual release and Google
managed publishing remain unchanged.

## Google Submission Readback

Promoted the exact code3 internal bundle to Production without another upload.
Saved a 100% rollout to the existing targeted countries, then sent exactly one
change for review. Console confirmed **1 change sent for review** and
**Changes in review: Production / 3 (0.1.2) / Start full rollout**. This is not
approval or public availability. Do not send the same change again. Managed
publishing remains on; review approval will still require a separate release.
The Console may continue its automatic quick checks after accepting the review
request; the captured readback preserves that message. Do not interpret the
heading as proof that a human reviewer has already started.

Provider evidence is in `store/.runtime/practice-012/google-production-submit.json`
and `google-production-readback.txt`. Existing owner testers can use the already
available internal version. No invitation was resent and no account setting was
changed. Apple's existing review requests remain intact.

## Verification and Evidence

The API deployment at <https://musia.lazying.art> uses clean commit `5a3eca9`,
transaction `20261005T150626-1b2bc4faf344`. Native implementation is `dee4204`.
The additive API preserves old clients and does not publish unrelated dirty
lyric files or expose the private Studio.

- 40 Android release unit tests, lint and signed-artifact qualification passed.
- 29 Swift core tests passed, including live multilingual Aya data.
- iPhone and iPad beginner UI checks passed; native screenshots retained.
- Physical Mac mini reference-audio and metronome playback checks passed.
- Android signed-APK Settings, score, ruby, chord changes, background playback,
  offline session persistence and language-preference persistence passed.
- Backend: 32 tests. Deployment: 8 tests. Store tools: 40 tests. All passed.

Known test-environment limits are preserved: KVM has no audio output device;
its native suite passed 32/33 with the audio test failing. The Mac mini's direct
API connection timed out during live iPhone lyric UI testing. Neither failure
was relabeled a pass; live rendering was checked on Mac KVM and Android, and
practice audio separately on the physical Mac mini. Simulator logs retain the
AVAudioSession synchronous-activation responsiveness warnings.

Private evidence: `store/.runtime/practice-012/`, Android artifact folder
`store/.runtime/artifacts/android-0.1.2-3-12c1e70b59c0/`, and the corresponding
Apple Mac-host xcresults/artifacts. Source, signing, artifact and QA hashes were
checked together. No binaries, credentials, recipient emails or raw session
history were committed.

The owned Android emulator and Apple simulators are stopped. The shared store
browser is retained for its other owners; no new desktop stack was started.

See [the implementation and learning scope](../references/native-multilingual-practice-2026-10-05.md)
for contracts, checks and future microphone-pitch requirements.
