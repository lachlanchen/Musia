# Musia Store Submission, September 30

## Verified State

| Platform | Exact Version | Fresh Provider Readback |
| --- | --- | --- |
| Apple | 0.1.1 (2) | WAITING_FOR_REVIEW; submitted September 30, 2026 at 01:04:14 UTC |
| Google | 0.1.1 (2) | Changes in review; production full rollout and 172 regions; existing submission preserved |

Apple app `6816265930`, version `f4337c74-f5d9-4613-879c-df5fb3712e9e`,
build `c012938a-29d5-419b-9254-29d41f074f76`, review submission
`8aef616c-53e3-41b8-b96b-0f95df8b2ee0`.
Browser confirmation was **1 Item Submitted**; independent API readback returned
WAITING_FOR_REVIEW for both the version and review submission.

Google's Publishing overview was reloaded and still showed the exact production
release among its 10 pending changes. No duplicate submission, new bundle,
invitation, or cancellation was performed. The previous
[artifact hashes and qualification](formal-review-2026-09-26.md) remain valid.

Neither platform is approved or publicly available. Apple manual release and
Google managed publishing remain enabled. Do not treat submission as a public
launch or change release controls silently. Pricing remains the saved USD 2.99.

## Submission Improvements

The outstanding Apple requirement was genuine native screenshots. A hardware
Mac mini with the existing Xcode 27 / iOS 27 simulator runtime rendered usable
screens, unlike the earlier virtual Mac. Added a bounded XCTest capture routine
covering library, practice controls, an Em guitar diagram, and lessons.

- iPhone 6.9-inch: four unedited 1320 x 2868 PNGs.
- iPad 13-inch: four unedited 2064 x 2752 PNGs.
- All eight were visually inspected and Apple's API reports COMPLETE with no
  delivery errors. The iPhone set also satisfies the 6.5-inch requirement.
- The first iPad diagram capture was clipped by the scrollable sheet. An actual
  in-app scroll and recapture fixed the composition; the clipped image was not
  uploaded. Do not stretch, reconstruct, or substitute website screenshots.
- The first Release screenshot build lacked testability for the scheme's unit
  test dependencies. The capture invocation now enables testability locally.
  This is a test-build setting, not a change to the shipped binary.

Native application implementation and both signed store artifacts are unchanged.
Only screenshot tooling, UI tests and release records changed. Live capabilities
still expose guest library/lessons/exercise audio, not accounts, upload,
generation or AI coaching. Shared-login work is not part of this release.

Apple's accepted dimensions and substitute-display rules are documented in
[screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/).

## Native Screenshot Capture

Run on a real Mac with an existing Xcode/runtime and a staged Musia checkout.
Coordinate host ownership and check memory/active builds first. Create or reuse
one dedicated `Musia-Store-...` simulator, whose initial state must be Shutdown.
Do not use a peer's simulator or launch another heavy build concurrently.

```bash
/usr/bin/python3 tools/store/capture_ios_review.py \
  --device <owned-simulator-uuid> --name iphone --attempt 1 \
  --output store/.runtime/formal/<review-date>

# After the iPhone capture has ended, repeat with a dedicated iPad simulator.
# Use a new --attempt value when refining; preserve prior evidence.
```

The script reuses one DerivedData directory, runs only
`MusiaUITests/PracticeSmokeTests/testStoreScreenshots`, limits compiler jobs to
two, disables parallel simulators and signing, and exports native attachments.
Release capture uses `ENABLE_TESTABILITY=YES` and `ONLY_ACTIVE_ARCH=YES` so the
scheme's test dependencies compile without altering project release settings.

Each attempt records app-source hashes, Xcode, device identity, test logs,
attachments, and simulator shutdown status under the ignored private runtime.
Commands are bounded; timeout cleanup targets only the launched process group.
The selected simulator is shut down in the cleanup path. Existing receipt or
result-bundle paths cannot be overwritten. Capture success still requires a
separate visual review before upload; it is not audible playback certification.

Select exact owned provider target IDs using `tools/store/browser_ui.py`.
Upload reviewed images in Media Manager, verify dimensions and COMPLETE states,
then perform Add for Review and Submit for Review once. Reconcile any uncertain
response through the exact version and review-submission resources before retry.
The beta API mutation allowlist remains unchanged.

## Verification and Cleanup

- 36 release-tool guard tests passed, including seven new capture safety tests.
- 29 backend API tests and nine web/core/guitar tests passed.
- iOS project/static validation passed; local optional Swift parser unavailable.
- Native screenshot tests passed on both simulator types. Previously confirmed
  iPhone audible and locked-screen playback remains separate device evidence.
- Both dedicated simulators were shut down and no Musia build/app remained
  running. Shared browser, peer apps and signing state were preserved.

Private evidence is under `store/.runtime/formal/20260930/`, including image
hashes, upload receipts, provider readbacks and native capture logs. Retain it
outside Git. No credentials, browser profiles or device screenshots are public
source artifacts.
