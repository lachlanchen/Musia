# Musia 0.1.3 Internal Testing

The owner requested test distribution only on October 6, 2026: accumulate
updates without replacing the existing production review submissions.
See [the Stage design](../references/native-stage-player-2026-10-06.md).

The later [icon test update](testflight-0.1.3-icon.md) supersedes the iOS and
Android packages below. This document retains the original Stage delivery and
Mac evidence; do not re-upload these older packages.

## Delivery

| Platform | Candidate | Latest verified state |
| --- | --- | --- |
| Android | 0.1.3 (4) | Available to internal testers, October 6 |
| iPhone / iPad | 0.1.3 (5) | VALID, IN_BETA_TESTING, existing Musia Internal group |
| macOS | 0.1.3 (5) | VALID, IN_BETA_TESTING, existing Musia Internal group |

Existing Android testers use the same
[internal test link](https://play.google.com/apps/internaltest/4701000336240069263).
No production release, price, region, invitation recipient or review attachment
is changed by this update. Apple upload acceptance, VALID processing and internal
group availability were checked separately. Final Apple readback at 13:31 UTC
on October 6 confirms both exact builds available and both 0.1.2 (4) formal
versions still WAITING_FOR_REVIEW with unchanged attachments.

Open TestFlight > Musia > Update on iPhone, iPad or Mac. The existing owner
tester is retained; no duplicate invitation was sent, and email delivery is
not independently verified. iOS build ID:
`504af54f-9565-4a4f-a517-85eea8e1a4b3`; Mac build ID:
`2e4871bb-ff71-42b9-b586-8514118f0531`.
Implementation is committed as `0b6ea4d`.

## Changes

- Songs open in Stage: compact cover, title/artist, tempo and playback speed,
  multilingual current lyrics, then current/next guitar fingering.
- EN/ZH/JA are independently selectable; existing Chinese pinyin and Japanese
  furigana remain with their timed words. Existing vocal-specific data is reused.
- Playback controls remain at the bottom within safe areas. Long or enlarged
  content scrolls without covering the controls. Android Back restores navigation.
- Practice retains loops and learning controls; First Pulse opens in Practice.
- BPM follows speed and displays analysis confidence. Missing meter/chords are
  not invented. Stage is a playback layout, not a video recorder.

## Evidence And Limits

- Final signed Android candidate: 40 release unit tests, lint and signature/
  identity checks passed. Phone and tablet native UI/media-clock smoke checks
  passed, including the selected song's current chord at the paused 15-second
  position, trilingual display, transport boundary and return navigation.
- Swift core: 29 tests executed, one opt-in live-network test skipped, no failures.
- iPhone/iPad simulator: Stage/Practice switching, transport while scrolling and
  rotating, live Aya catalog and language selection passed. The first iPad
  language test failed because Search was collapsed; the test was corrected and
  rerun successfully. Its original failure is retained.
- Mac: native compilation passed. Full XCTest ran 33 tests with two skips and
  five assertion failures in the generated-tone/metronome test because the KVM
  lacks a default audio output. The other tests, including seek/speed/loop and
  history, passed. Do not summarize this whole suite as passing.
- Mac Debug runtime harness passed catalog loading, media-clock progression,
  minimized playback state, history and navigation checks. Actual native Stage
  screenshots at 1280-wide and minimum window size were visually checked.
  Media-clock success is not physical audibility verification.
- No physical-device listening, Bluetooth latency or new-build locked-screen
  playback qualification is claimed. iOS simulators also reported AVFoundation
  playback errors on this audio-less host; UI evidence is limited accordingly.
- Release-tool regression suite: 42 tests passed. No audio, lyrics, timing,
  permissions, API contract or background playback engine was changed.

## Exact Artifacts

- Android AAB SHA-256:
  `44bd4cd7d1ccdd35e00b0098c1a46aeb8be88da9697f4ce25f57e10694ef65d5`.
- iOS IPA SHA-256:
  `d32115e3cc129a3eb54141ffe9698fb55bfc164eed7c1fb5b337162c1d9e7b71`.
- Universal Mac installer SHA-256:
  `57acdd71c289f91e30086b8ec795459ad80401a6a76c96599c08088d4c1f5c6b`.

Private receipts, native captures, failed and passing logs, provider readback
and source-bound QA live under `store/.runtime/stage-013/`. Packages, signing
material and browser state stay out of Git. Earlier intermediate Android
packages were not uploaded; only the final safe-area-corrected AAB was selected.
Owned emulator, simulators, debug app and build/upload processes are stopped.
The shared noVNC browser/profile is preserved; the exact owned Play tab was
closed after release readback. No idle Musia GUI stack is retained.

## Owner Check

Open Aya Chan, Rain of Light. Check the compact tempo/cover, all three languages
and their readings, current guitar, scrolling, and playback controls. Change
speed and audio version under Playback settings; switch to Practice for loops.
Check audible playback and screen-lock continuation on a real device before
promoting this beta to a future production update.
