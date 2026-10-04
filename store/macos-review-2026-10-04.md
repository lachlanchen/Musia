# Native macOS Review Submission

**Submitted 2026-10-04 at 21:58:22 Hong Kong time. Status: WAITING_FOR_REVIEW.**
Fresh App Store Connect API readback confirms the exact Mac version, build and
review submission. This is not approval or public availability. Manual release
after approval remains selected, consistent with the existing iOS release.

## Release Identity

| Field | Value |
| --- | --- |
| App | Musia: Learn Music & Guitar |
| App Store record | `6816265930` |
| Bundle / team | `art.lazying.musia` / `Q8M2S2FY77` |
| Platform / version | macOS 0.1.1 (3) |
| Minimum / architectures | macOS 14; arm64 and x86_64 |
| Version resource | `252606cc-493d-4385-b901-dd4cf7f659f0` |
| Build / delivery | `912a785a-be0e-4b3c-974f-db7c96c29fd6` |
| Review submission | `cdb09c5a-7833-45a5-bba0-ffba95107a46` |
| Submitted UTC | `2026-10-04T13:58:22.169Z` |
| Processing / eligibility | VALID / APP_STORE_ELIGIBLE |
| Internal TestFlight | IN_BETA_TESTING; existing Musia Internal group |
| US price | USD2.99; fresh API readback, same app-wide purchase |
| Installer SHA-256 | `aa8251ce391daaf725267a29a92b1bce96f61d0da253fe1d565fdba840c25a26` |

No duplicate tester invitation was sent. Existing worldwide-where-eligible
availability and privacy disclosures were preserved. The iOS 0.1.1(2) submission
remains WAITING_FOR_REVIEW, with its original build and September30 submission
unchanged. Google was not modified or freshly checked in this Mac-only task.

## Native Implementation

SwiftUI/AVFoundation, not Catalyst or a web wrapper. Shared Swift core and
services preserve source-time synchronization, pitch-preserving 0.25x-2x speed,
phrase/A-B loops, timed lyrics/readings, current/next chords, guitar diagrams,
tap feedback and local history. The Mac adds a sidebar, wide practice layout,
menu/keyboard controls, Now Playing integration and sandboxed JSON export.

The sandbox allows outgoing network access and user-selected file read/write.
No microphone/camera permission, account requirement, advertising SDK or hidden
generation endpoint was added. The production binary has Hardened Runtime,
real distribution signing and no Debug review harness. System sleep pauses
audio; the app does not claim to keep a sleeping Mac awake.

## Qualification

| Check | Result |
| --- | --- |
| Release-optimized native XCTest on Intel/macOS15.7.9 | 27 passed; zero skipped/failures, including live API/audio |
| Earlier Debug native XCTest | 25 passed; two explicitly opt-in network tests initially skipped |
| Apple-silicon native build, Mac mini/macOS27 | Passed |
| Apple-silicon Swift core suite | 23 passed; one opt-in network test skipped |
| Shared-source iOS generic simulator compile | Passed; no replacement iOS binary uploaded |
| Physical iMac/macOS15.7.7 native runtime | Catalog32, lessons3, Aya audio clock, minimized playback, guitar and persisted history passed |
| KVM native runtime | Same app-scoped checks passed |
| Local store guards | 40 tests passed |
| Static iOS/Mac invariants | Passed |
| Installer | Universal architectures, signature, sandbox, permissions and checksum inspected |
| Apple validation/upload | JSON explicitly confirms success; upload COMPLETE without warnings/errors |
| Mac screenshots | Three genuine 1280x800 native captures, visually checked; all delivery states COMPLETE |

The runtime harness drives this app's own models/window, not human keyboard or
accessibility automation. Captures come from the real AppKit/SwiftUI view tree.
No web mockup or stretched screenshot was used. Physical audio-clock progression
is verified; a human listening evaluation of the Mac speakers is not claimed.
The macOS12 3040 was reachable but below the supported OS floor, so no Musia
runtime was installed there. The iMac's low free disk was respected: only a small
test app was transferred, with no SDK or build-cache installation.

The optimized local XCTest host uses ad-hoc signing and
`ENABLE_HARDENED_RUNTIME=NO` **only for test injection**. A first local Release
test attempt failed library validation until this test-host setting was applied.
The distribution archive was not weakened. Direct launching of the App
Store-signed archive was not used as qualification; TestFlight is the signed
installation route.

## Reusable Workflow

- [Native source and commands](../apps/macos/README.md)
- [Universal archive and installer builder](../tools/store/build_macos.sh)
- [Fail-closed Mac validator/uploader](../tools/store/upload_macos.py)
- [Upload-result regression tests](../tools/store/tests/test_macos_upload.py)
- [Store listing copy](macos-listing.json)
- [Guitar screenshot](assets/macos/02-guitar.png)
- [Song screenshot](assets/macos/03-song.png)
- [Lessons screenshot](assets/macos/04-lessons.png)

Two packaging lessons are now encoded in the tools:

1. Keep the runtime enclosing directory private, but make installed app files
   readable by normal users. An early `umask 077` installer failed Apple's
   validation; it was never uploaded as the accepted candidate.
2. `altool` can exit zero while its JSON contains `product-errors`. Require an
   explicit JSON success message and no errors before reporting acceptance.
   Unknown/failed responses stop the uploader. A sent upload is journaled before
   transmission and cannot be blindly resent.

The shared keychain was unlocked through its existing owner-only password file.
No passwords were printed, certificates revoked, keychain ACLs changed or peer
apps terminated. Xcode re-export intermittently failed signing; the final
installer uses Apple's supported `productbuild --component` route around the
already verified, distribution-signed universal archive. Apple validated it.

## Evidence and Next Step

Private evidence: `store/.runtime/macos-20261004/` on the source workstation;
the signed archive and final package remain under
`~/Projects/Musia/store/.runtime/macos-0.1.1-3/` on the KVM Mac. Private Apple
contacts, profiles, keys, logs and packages are excluded from Git.

Wait for Apple's review result. Reconcile this exact submission before making
another release mutation; do not remove or duplicate the separate iOS review.
After approval, manual public release is still required.

Apple references: [adding a platform to an existing app](https://developer.apple.com/help/app-store-connect/create-an-app-record/add-platforms)
and [distribution preparation and Mac sandbox requirements](https://developer.apple.com/documentation/Xcode/preparing-your-app-for-distribution).
