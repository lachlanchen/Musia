# Original Icon Test Update, 2026-10-13

The owner asked to restore the original icon and submit a **test build**.
Keep version 0.2.1; increment Apple to build 11 and Android to code 9.
Production releases, formal reviews, prices, permissions, billing and generation
gates are outside this task. Do not promote the beta.

## Scope

- Exact original teal/coral/white sound-bar artwork, recovered from Git.
- Correct native rounded treatment on Mac, iPhone/iPad, Android and Watch.
- All lessons, multilingual Stage and chat-first Create from build 10/code 8
  remain unchanged. No app behavior, content or permission changes.
- First Pulse exercise artwork and the Fun website logo stay unchanged.

## Delivery

- Android **0.2.1 (9)**: available to internal testers, verified October 13,
  15:20 Hong Kong time. Existing owner membership verified; no duplicate invite
  sent. Production and managed publishing unchanged.
- Mac **0.2.1 (11)**: VALID / IN_BETA_TESTING, existing Musia Internal group,
  verified at 07:38 UTC. Build `a9b2d1cf-6383-4270-9cea-fe3a7ee82f42`.
- iOS/iPadOS **0.2.1 (11)**: VALID / IN_BETA_TESTING, existing Musia Internal
  group, verified at 07:38 UTC. Build `cb5c5f67-3ca8-4b53-a691-7a5ba993374d`.

Private receipts are in `store/.runtime/original-icon-20261013/`.
Final Apple readback confirms owner membership and both exact build attachments.
It also confirms iOS 0.1.2 (4) remains WAITING_FOR_REVIEW and Mac 0.1.2 (4)
remains READY_FOR_SALE. No formal submission or production release was performed.
All uploads are complete; do not retry or resend invitations.

## Verification

Source icon checks cover all 19 native/listing exports, visible sound bars,
transparency, Dock padding and Android's adaptive safe area. Packaged assets,
signing, versions and native smoke checks are required before distribution.
The previous beta's extensive practice/layout evidence remains historical
evidence; it is not a new physical-device test of this icon-only build.

- 234 store-tool tests pass in the `musia` environment; system Python lacks
  the existing Pydantic dependency and is not the test environment.
- Android: 53 release unit tests, lint, signed APK/AAB identity checks and native
  Stage smoke pass. Verified original icon in the launcher, EN/ZH/JA lyrics,
  source-time chord seek, play/pause clock and navigation. Owned emulator stopped.
- Shared checks: 19 icon exports and five rounded-silhouette regression tests
  pass; the exact original master SHA-256 is pinned to prevent silent changes.
- Mac signed universal archive and installer verified; compiled ICNS and native
  Workspace icon inspected at 64/512px with transparent rounded corners.
- Initial KVM iPhone suite: chat/composer passed, two audio-dependent assertions
  in the beginner suite failed. Its screenshot shows playback could not start;
  `system_profiler SPAudioDataType` reports no devices. Preserved this failed
  attempt and moved audio-dependent checks to the Mac mini, not relaxed asserts.
- Mac mini repeat: **both UI tests passed**, including actual metronome playback
  state and tap feedback. 69 core/catalog/Watch tests ran with one opt-in network
  skip and no failures. Xcode27 simulator QA used the exact same native source
  digest as the signed Xcode26.6 IPA. Native rhythm and keyboard screenshots
  were visually reviewed. This is not physical iPhone listening qualification.
- Legacy `apps/ios/scripts/validate.py` still assumes no microphone permission
  and fails on the already-intended optional local pitch feature from build10.
  The signed-IPA inspector instead validates the exact approved usage string and
  Watch capabilities. No new permission was introduced in this icon-only build.

## Artifacts

| Artifact | SHA-256 |
| --- | --- |
| Android AAB | `e5480d34af04cd714bbdf71f8bc0265281d56aa70a66d4a9e72e547a8e584daf` |
| iOS IPA | `43509ddc42aed9fdd6d340fc296f35d514a63ac0021b201f4361635149777f89` |
| Universal Mac PKG | `73cef5addde182f833769c3f2aafceb2ae4bb8290ce72b81e3f7ac4cf05ab40d` |

Android source digest: `35517d3d422119b2f279ecc72eda3efc9d288a5a6c02d2c4ebd928e1e0e8a173`.
iOS source digest: `85c852e8cac96fa9135d1743c1ce054d3abe663c723dcb86e4cdf2b9f6f4d383`.
The original master, checks and export scripts are documented under
[`apps/shared/brand`](../apps/shared/brand/README.md). The new icon is not a
rollback of the lesson/chat update.

Google reported the existing nonblocking deobfuscation/native-debug-symbol
warnings. R8 remains disabled; no device support was lost. Private captures are
test evidence, not replacement public store screenshots. The owned Android
emulator, store tab and both iPhone simulators were stopped after capture.
