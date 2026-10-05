# Musia 0.1.2 Internal Testing

The owner explicitly authorized TestFlight/internal distribution while the
existing iOS and macOS 0.1.1 App Store reviews continue. Internal testing must
not replace the formal version's attached build or cancel its review.

## Confirmed Delivery

On October 5, 2026, fresh provider readback confirmed:

| Platform | Internal version | State |
| --- | --- | --- |
| iPhone / iPad | 0.1.2 (4) | VALID, IN_BETA_TESTING |
| macOS, Intel and Apple silicon | 0.1.2 (4) | VALID, IN_BETA_TESTING |
| Android | 0.1.2 (3) | Available to internal testers |

Both Apple builds are attached to the existing **Musia Internal** group, with
the existing owner tester retained. Open TestFlight > Musia > Update. Android
testers can use the existing [internal test link](https://play.google.com/apps/internaltest/4701000336240069263).
No duplicate invitation was sent; email delivery is not independently verified.

iOS build ID: `7b0ae745-7e3b-44ab-9100-1de68e99cfc7`.
Mac build ID: `1d5a2c57-de54-4120-a219-5a4b158265f5`.
The final API readback at 08:18 UTC confirmed that iOS 0.1.1 (2) and Mac
0.1.1 (3) remain WAITING_FOR_REVIEW, with their original build attachments.
Google production 0.1.2's existing review request was not changed.

## Candidates

- iPhone/iPad: 0.1.2 (4), signed IPA SHA-256
  `10c1d046df2970a99995ece42b1ea670b855817e20b1b2dac37135e37721ddb7`.
- Mac: 0.1.2 (4), signed universal installer SHA-256
  `8b851ea56603eec7d50f84584a8175ec3b29abcdc2fd7d41df34b23ce2187807`.
- Android: 0.1.2 (3), already available to the existing internal testers;
  freshly reverified in the Console on October 5.

Application source remains `dee4204`; release-tool changes do not rebuild or
alter either Apple package. Actual processing and distribution receipts belong
under private `store/.runtime/testflight-012/`. An accepted upload alone is not
proof that the build can be installed.

## What to Test

1. Open a song such as Aya Chan, Rain of Light. Read English, Chinese and
   Japanese together; check pinyin and furigana over the appropriate words.
2. Toggle lyric languages independently of the audio version. Check that the
   choices persist after reopening the app. All three are on by default.
3. Open Settings > Practice history. Existing sessions should still be there.
4. Open Do Re Mi. Begin with Learn, then try the listening quiz. Only the first
   answer scores; this is not microphone pitch or singing evaluation.
5. Start the metronome at 60 BPM. Try optional Em/Am accompaniment and one
   gentle down-strum on beat1. Chords change every four beats.
6. Leave or background a practice tool: its tone/clicks should stop. Normal
   song playback should continue when the app is backgrounded or the screen locks.

No new microphone permission, subscription, account, tracking or upload feature
was added. Tap offsets still include device/Bluetooth latency; they are not an
instrument-performance grade.

## Repeatable Delivery

- Verify the exact app, platform, marketing version, build number and artifact
  hash. iOS and macOS can share a build number; select by prerelease platform.
- Retain the tested signed artifact. Qualify an owner-only beta with real
  unit/UI/signature/permission/content evidence and explicit limitations.
- Validate and upload once. Require both a successful process exit and Apple's
  successful JSON response; reconcile any unknown result before a retry.
- Wait for the exact build to become VALID, then add it to the existing
  **Musia Internal** group. Verify the exact build and owner relationships.
- Read back internal-beta state. Do not enable access to every future build,
  create a public group or resend an existing tester invitation.
- Recheck that the formal iOS and Mac review attachments remain unchanged.

The fresh Swift core run passed 29 tests; release-tool tests passed 42. Native
iPad UI and physical Mac practice-audio evidence are retained. The previous
live iPhone lyric UI test had a test-host network timeout, and the KVM lacks an
audio device. Those limitations remain disclosed, not converted to passed QA.

Provider references: [Apple internal testing](https://developer.apple.com/help/app-store-connect/test-a-beta-version/add-internal-testers),
[build/prerelease relationships](https://developer.apple.com/documentation/appstoreconnectapi/builds).
