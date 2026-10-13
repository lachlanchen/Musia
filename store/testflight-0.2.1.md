# Practice And Simple Create Beta, 2026-10-13

## Scope

Owner requested the current icon, improved beginner lessons and simpler chat
creation in **test builds only**. Version **0.2.1**, Apple build **10**, Android
code **8**. Do not promote these builds, change pricing, replace the iOS review,
enable checkout or relax the invitation/manual-approval generation pilot.

## Changes

- Keeps the current coral/cyan ribbon icon. iOS uses the system mask, Android
  the adaptive safe area, and Mac the explicitly rounded transparent silhouette.
  This task verifies and packages existing approved artwork, not new artwork.
- Delivers the October 12 beginner workshop: Do/Re/Mi listening, first-answer
  listening quiz, local microphone pitch matching, 30-240 BPM metronome, tap
  feedback, meter/subdivision choices and synthesized chord-change references.
  The old three static lesson cards are removed. History stays under Settings.
- Create opens Agent chat. The composer stays at the bottom above keyboard and
  navigation; render controls and jobs start collapsed. Studio edits the same
  draft. Rights confirmation, explicit render confirmation, allowance and
  account/idempotency guards remain in force.
- Android explicitly resizes for the keyboard and consumes parent insets once,
  preventing the header from being panned offscreen.
- EN/ZH/JA multiselection, Chinese pinyin, Japanese furigana, Stage playback and
  source-time chord rendering remain available.

## Delivery

- Android **0.2.1 (8)**: Console confirms **Available to internal testers**,
  released October 13 at 14:50 Hong Kong time. Existing owner test access was
  verified; no new invitation was sent. Production remains 0.1.2 (3), managed
  publishing stays enabled, and its production publishing queue is empty.
- iOS/iPadOS **0.2.1 (10)**: Apple accepted the IPA, processing is VALID, and
  the exact build was attached to the existing Musia Internal owner group.
  Fresh 06:52 UTC readback confirms **IN_BETA_TESTING** for build
  `772c534f-b50e-4bde-8bde-da7b08a778a7`.
- macOS **0.2.1 (10)**: Apple accepted the universal package. Fresh 06:57 UTC
  readback confirms **VALID / IN_BETA_TESTING**, attached to the existing owner
  group: `85a34391-ee0f-4f63-85a7-658c3fb458f9`. No new invitation or email
  resend was requested. Both Apple platforms are available to the owner.

Open Musia in TestFlight on iPhone/iPad or Mac and choose Update. Android uses
the [existing internal-test link](https://play.google.com/apps/internaltest/4701000336240069263)
with the existing tester account. Availability is provider-confirmed; installation
of these exact builds on the owner's physical devices is not claimed.

No formal submission or screenshot replacement. iOS 0.1.2 (4) retains build
`7b0ae745-7e3b-44ab-9100-1de68e99cfc7` in WAITING_FOR_REVIEW. Released Mac
0.1.2 (4) retains `1d5a2c57-de54-4120-a219-5a4b158265f5`, READY_FOR_SALE.

## Qualification

- Android: 53 release unit tests, lint, signed APK/AAB inspection pass. Exact
  final QA APK passed native guest Agent/Studio, keyboard, draft, practice,
  silent-microphone abstention, background stop and Stage regression checks.
  Stage seeks wait for loaded duration and each displayed timestamp, then
  compare the current diagram to the live asset at 15 seconds.
- Apple: 69 core/catalog/Watch protocol tests, 68 passed and one optional live
  case skipped. Two iPhone simulator UI tests passed, covering beginner practice,
  Settings, default languages, chat entry and keyboard-safe composer.
- macOS Debug compile and universal signed archive pass. A source-based isolated
  QA bundle captured Create, Lessons and Settings content on the Mini. Its
  normal live-catalog harness timed out. The bounded offline capture harness is
  private instrumentation, not a product change or a network/Keychain test.
  AppKit capture omits the composited sidebar; these are not finished store
  screenshots. Do not label them full-window visual qualification.
- 234 store-tool tests and all 18 icon-export checks pass. iOS inspection
  verifies the exact embedded Watch identity/profile/version. Mac upload also
  checks the compiled/native icon, sandbox, distribution signature and both
  arm64/x86_64 architectures.

The first Android candidate had a keyboard-pan defect found in direct screenshot
review. It was not uploaded. A later practice test was interrupted when its
emulator exited; a complete repeat on the final APK passed. The old Stage script
counted early seek taps rather than waiting for settled playback; its corrected
version passed without changing the app's media-clock behavior.

Microphone practice is optional, explicitly started and local. Android uses
memory; Apple deletes its temporary WAV after measurement/cancellation/handled
failure. Neither uploads it. Silence is not given a score. This is a bounded
pitch estimate, not a calibrated singing-quality or guitar-performance grade.

## Artifacts And Evidence

| Artifact | SHA-256 |
| --- | --- |
| Final Android AAB | `cff996d416f7f18bc518b48d0e1a35e7e873c97bf3ae8ed90f464885621c5bb2` |
| iOS IPA | `6d7fcb68ff7e4a2bbe23f12afbca422409e1d25f74d144ff3c890ca397e32d75` |
| Universal Mac PKG | `22acc34bd5618ec27db491d1c81a569ecd6581d902e1d8a04c372af956396bcf` |

Android source identity is in the exact signed build receipt under
`store/.runtime/artifacts/android-0.2.1-8-c04bed7d8981/`.
Its digest is `c04bed7d898181aa218d4f8762dc1ce1e4252023c925096f3dba013a355fddab`.
iOS: `b33e4d7e3545c87c599cc1e2c39e6b3782a6f6f3deaaa5390b6dcc48762182ec`.

Private local evidence: `store/.runtime/beta-20261013/`; Apple distribution files
are in the existing Musia KVM runtime. Local PNGs are genuine native capture
drafts only, not uploaded/approved listing assets. Reusable checks:

```sh
tools/store/test_practice_beta_apple.sh <owned-stopped-simulator-udid> <fresh-output>
python tools/store/android_creator_workspace_smoke.py --serial emulator-5580 --output <output>
python tools/store/android_practice_smoke.py --output <output> --silent-microphone
python tools/store/android_stage_smoke.py --serial emulator-5580 --output <output>
node apps/shared/scripts/validate-icons.mjs
```

Set `MUSIA_ROOT` to the isolated Apple checkout. Do not run emulator microphone
tests on someone's live device. Keep test source, signed artifact and QA receipt
hashes bound together; inspect uncertain provider responses before any retry.

## Remaining Acceptance

Real iOS/Android/Mac microphone tests with natural voices, device audibility,
current-build authenticated native chat, physical paired Watch, social providers
and Apple subscription lifecycle are not newly qualified by this beta. Previous
tests remain historical evidence, not a substitute. Payments stay off, pilot
generation stays gated, and chat history remains local/account-scoped rather
than cross-device synchronized.

Task-owned emulator5580, its tmux session, the Musia iPhone simulator, isolated
Mac QA processes and owned store tabs are stopped/closed after evidence capture.
Shared browsers, tunnels, peer builds and installed TestFlight apps are preserved.

See [practice design](../docs/practice-workshop-20261012.md) and
[Agent/Studio design](../docs/creator-agent-studio-watch.md).
