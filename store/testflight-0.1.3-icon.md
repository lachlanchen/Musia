# Musia Icon Test Update

The owner requested iOS and Android test builds on October 6, 2026, after
approving the coral/cyan ribbon icon and rounded-corner treatment. This is
**test distribution only**. Preserve both Apple 0.1.2 (4) formal submissions,
the existing Mac 0.1.3 (5) beta, and all production settings.

## Delivery

| Platform | Version | Verified state |
| --- | --- | --- |
| Android | 0.1.3 (5) | Available to internal testers |
| iPhone / iPad | 0.1.3 (6) | VALID, IN_BETA_TESTING, existing Musia Internal group |
| Mac | 0.1.3 (5) | Existing beta unchanged; not rebuilt |

Existing Android testers use the same
[internal test link](https://play.google.com/apps/internaltest/4701000336240069263).
No tester list, invitation recipient, production review, price, region or public
listing artwork is changed. A successful upload is not proof of availability;
read provider processing and the exact internal-group relationship separately.

Final Apple readback at **15:29 UTC, October 6** confirms iOS build 6 available
in the existing internal group. Build ID:
`194ed056-52f0-4e3a-82f1-78307a7b2707`.
Upload acceptance at 15:25 UTC and VALID processing at 15:28 UTC were checked
separately. The existing owner tester was retained; no duplicate invitation was
sent, and email delivery is not independently verified.

Both Apple 0.1.2 (4) formal versions remain WAITING_FOR_REVIEW with unchanged
attachments: iOS `7b0ae745-7e3b-44ab-9100-1de68e99cfc7`, Mac
`1d5a2c57-de54-4120-a219-5a4b158265f5`. Mac beta build
`2e4871bb-ff71-42b9-b586-8514118f0531` remains available and unchanged.

## Included Changes

- New ribbon M icon, committed as `0516cc6`, with platform-appropriate corners.
- iOS uses an opaque square source and the system's rounded mask. Android uses
  a safe-area-aware adaptive icon and rounded legacy fallbacks.
- The [Stage-player update](testflight-0.1.3.md) remains included: compact
  cover/tempo, multilingual timed lyrics with readings, guitar fingering and
  a fixed playback bar, plus the existing Practice tools.
- No catalog, audio, lyric text, timing, playback engine or permission changes.

## Verification

- Android: 40 release unit tests, release lint, signer/identity checks and exact
  signed QA APK inspection passed. Native API34 smoke checks confirmed Stage,
  three languages, source-time seek, the live source chord at 15 seconds,
  diagram/transport boundaries, advancing playback clock and return navigation.
  The native launcher screenshot confirms the new icon is installed.
- iOS: fresh Xcode 26.6 iPhone simulator tests passed for live multilingual
  selection and Stage/Practice layout, including scrolling and rotation.
  Swift core tests: 29 executed, one opt-in network test skipped, zero failures.
  Prior iPad Stage/language evidence is retained for the unchanged UI; it is
  not represented as a fresh build-6 physical-device test.
- Shared artwork validation passed all 18 exports, dimensions, PNG color types,
  rounded transparency, small-size detail and Android adaptive safe area.
- No physical-speaker, Bluetooth-latency or new-build locked-screen playback
  verification is claimed. The KVM Mac has no audio output. Simulator UI tests
  do not establish audible playback or lyric alignment.
- Google reported no blocking errors and two diagnostic warnings: missing
  deobfuscation file (R8 is disabled) and native debug symbols.
- Store-tool regression suite: all 42 tests passed. iOS manifest/resource/
  scheme validation passed; actual Xcode compiler tests supply the compiler
  evidence that the Linux static validator cannot provide.

## Receipts

Android AAB SHA-256:
`2c2c5b41701c89c463deb7d56470ffd15a858dcc87bd91fa04486e81d1eac3dc`.
Signed QA APK SHA-256:
`0ac6d09e795c77e528594d3101b456c181c994e4f1b6de8bc1d4459d490bf0b8`.
iOS IPA SHA-256:
`146929a05cd5fa3034d1a937715f590480efa430b0acb86e346021e83e682b62`.

Private source-bound QA, native screenshots, provider journals and readback live
under `store/.runtime/icon-beta-013/`. The Android build receipt is under
`store/.runtime/artifacts/android-0.1.3-5-d4109767506f/`.
The iOS signed archive and IPA remain on the established KVM Mac under
`store/.runtime/artifacts/ios-0.1.3-6-097661af6953/` in its Musia checkout.
Secrets, packages, browser state and raw provider evidence stay outside Git.

The owned Android emulator and upload tab were closed after verification;
no iOS simulator, build or upload process remains running. The shared store
browser/profile remains available to other projects.

## Test On A Device

Update the existing Musia installation from TestFlight or the internal Play
track. Check the ribbon icon in the launcher, then open Aya Chan, Rain of Light
in Stage. Verify EN/ZH/JA and their readings, seek to a different chord, scroll
past the diagram, and switch to Practice. Check audible playback and screen-lock
continuation on a real device before promoting this beta to production.
