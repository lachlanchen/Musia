# Creator Apple Test Release, 2026-10-09

## Agent, Studio And Watch, Build 9

October 9: **macOS 0.2.0 (9) is VALID / IN_BETA_TESTING** in the existing
Musia Internal owner group. It was installed through TestFlight on the Mac mini;
installed bundle/version, signature and App Store receipt presence were checked.
The updated Library populated on first open. The installed TestFlight app's
Agent default and Studio form were visually checked. Beyond the Maples played
through to its end; seeking and resuming showed an advancing clock, changing
chords, and English/Chinese/Japanese lyrics with pinyin/furigana without overlap.
The screenshots verify rendering and playback state, not physical audibility.
Cover art remained a placeholder in this inspection; image loading is not
claimed as verified. No signed-in Mac generation or purchase was performed.

**iOS 0.2.0 (9) is also VALID / IN_BETA_TESTING**, confirmed at 11:19 UTC.
It was uploaded once and accepted at 11:14 UTC, then attached to the existing
internal owner group. It embeds the native Watch companion. Both formal
0.1.2 (4) builds remain WAITING_FOR_REVIEW with unchanged attachment IDs.
No invitation resend or independently verified email delivery is claimed.

- iOS IPA: `bff6bd35d8482ac79bb038392475a12ef1589bbc60b7ccbd020f231e276d5d61`.
- iOS source: `fbfb9271b37d8a4efc8e6b31069a03c99807dc46cb7cc567fa97edf17a6515ab`.
- Universal Mac PKG: `2624fe32e4cb69707aaf6c9ce053b288de92b40e0ddef7e056a039513f1a7955`.
- Source-based iOS simulator cases 19/20/21 passed: existing QA sign-in retained
  across upgrade/relaunch, Agent default and shared Studio draft persistence,
  authenticated private playback and sign-out cleanup. All 16 exported native
  screenshots were visually reviewed, including mini-player/tab clearance.
- Swift core: 54 passed, one optional network test skipped; six catalog and
  five Watch protocol tests passed. The catalog fix prevents transient view
  cancellation from canceling the shared load.
- Watch simulator compiled/launched and its settled native screenshot was
  inspected. No physical paired Watch connectivity or haptic acceptance is
  claimed. Signed iOS inspection validates the exact embedded Watch identity,
  profile, version and entitlements, not arbitrary extensions.

Private evidence: `store/.runtime/creator-apple-20261009/ios9-qa.json`,
`mini-ios-ui-r19/`, `mini-ios-ui-r20/`, `mini-ios-ui-r21/`,
`watch-agent-core-tests.log`, `watch9-settled.png`, `mac9-internal-readback.json`,
`final9-delivery.json` and `store/.runtime/mac9-*.png`. Cases 16-18 exposed test-harness assumptions
(relocated Watch plist, old heading, expected signed-out state); they were not
silently marked passed. Build 9 source did not change during the passing tests.

The release is internal testing, not paid-service qualification. Apple financial
lifecycle and paired physical Watch testing remain open; checkout stays off.
After evidence capture, the owned Mac player and loopback RFB forward were
stopped. Shared TestFlight, store browser, tunnels and peer apps were preserved.

## Earlier Build 8 Checkpoint

October 9, 08:13 UTC: final **0.2.0 (8)** is uploaded and VALID for iOS and
macOS. Both builds are attached to the existing Musia Internal TestFlight group
with the existing owner verified. Fresh provider readback confirms both are
IN_BETA_TESTING. No invitation resend or email delivery
is claimed. This is an internal-test update, not a replacement formal submission.

Native private-playback run 12 **passed**, including advancing audio-clock
position, mini-player/tab separation on detail/root/reopened pages, and sign-out
clearing playback. Account/relaunch run 13 and complete product-screen run 15
also passed. The parent directly opened all 18 PNGs and recorded a hash-bound
visual review. These are genuine source-built iOS simulator tests, not physical
device listening or execution of the signed IPA. The separate IPA signature,
provisioning and permission inspection passed before internal qualification.
The immutable iOS source digest is
`fa16c5b51657935d384af9c2af19449e2a9fd950cd4b16d32e83079b04490a2d`;
the full Apple input digest is
`db8b8d9c4b04f3b798f12d795057381f14a9eb63b078b4f3b255c50f3fb3c8ce`.
iOS IPA SHA-256:
`f124210ef7f02d323d639a566a9aa0b078928a916529340d745b00d212d659a1`.
Mac installer SHA-256:
`70cf668ac1c5aaed8b49de7f977bcb2d6e27abd66e42f05dbaa4ae3a1952c660`.

Build 8 moves mini-player safe-area placement onto the navigation stack on both
Apple platforms, so pushed creator song pages keep their playback controls.
It also validates brief lengths and keys against the server contract, releases
only an initial definitively rejected render request, authenticates pending-public
owner audio, and cleans canceled/replaced private audio downloads. Unknown
render outcomes retain their exact owner, request body and idempotency key.
The downloaded file now keeps its MIME-derived `.mp3` or `.wav` suffix; a generic
`.audio` cache filename was rejected by AVFoundation despite correct bytes.
Swift core now runs 51 tests: **50 passed, one optional network test skipped**.
Earlier mini-player-only and pre-MIME build-8 candidates were never uploaded
and are superseded by this source; retain their evidence, not their distribution.

Genuine iOS account run 3 on Mac mini passed browser sign-in and protected-session
relaunch. Playback runs 5-7 then found missing mini-player controls on pushed
song details. Run 7 downloaded the complete verified MP3 successfully, so its
failure must not be reported as an audio-download failure. Runs 8-9 isolated the
format-suffix error; native byte-identical file probes and the actual iOS error
confirmed it. Run 10 played successfully but its logout test hit an overlapping
mini-player instead of the account row. A fully exposed center-tap and explicit
confirmation fixed the test interaction; run 12 passed the complete case.
See [playback delivery](../docs/creator-playback.md) for the full-length,
ACL-protected MP3 derivative and measured transfer improvement.

The source checkpoint `bf44ac5` is pushed. UI run 14 had only a stale account-link
selector: the signed-in link uses the actual username. Run 15 accepts that exact
fixture username or the signed-out label, without weakening product visibility
checks or changing the app. The exact run-12 test source was recovered by
hash-matching a reconstruction, not represented as a contemporaneous backup.

Google purchase acceptance does not qualify Apple billing. No actual Apple
purchase or subscription lifecycle has passed, and both formal 0.1.2 (4)
attachments remain unchanged. Both subscription review screenshots are COMPLETE,
but fresh provider GET still reports MISSING_METADATA without naming a missing
field. This is not evidence of a sandbox purchase failure.

Current private receipts: `final8-parent-visual-review.json`,
`final8-qualified/ios-qa.json`, `final8-ios-upload.json`,
`ios8-internal-attachment.json` and `mac8-internal-readback.json`, under
`store/.runtime/creator-apple-20261009/`. Upload occurred once per final artifact;
unknown responses are reconciled rather than reuploaded.

### Earlier Build 7 Checkpoint

October 9, 06:10 UTC: macOS **0.2.0 (7) is VALID and IN_BETA_TESTING**
in the existing Musia Internal group. The existing owner's membership was
verified; formal version/build attachments were unchanged. Email delivery was
not independently verified and no resend was requested. Private receipt:
`store/.runtime/creator-apple-20261009/mac-internal-readback.json`.

The source implementation is pushed as `e7d5c7e`. iOS upload is still pending
native qualification. The paragraphs below retain the earlier signing lane's
historical observations, superseded by this section where explicitly stated.

The prefix-match inventory bug is fixed, with duplicate/missing/wrong-ID tests.
The Mac upload reused the existing KVM interpreter
`~/.local/share/musia/store-python/bin/python`, not bare `/usr/bin/python3`.
It revalidated and uploaded the exact PKG once. The first bare-interpreter
attempt stopped before the upload journal because PyJWT was unavailable.

Genuine iOS simulator UI now verifies Library, Create, Account, Community and
both real StoreKit products. An unsigned test build initially failed Keychain
with `errSecMissingEntitlement`; the private simulator project now supplies
app-specific entitlements with local signing. No release app, Keychain policy,
certificate or production container was changed. This agrees with
[Apple's entitlement diagnosis](https://developer.apple.com/documentation/security/errsecmissingentitlement).
The subsequent run opened the real central login page but failed XCTest's
password-focus step. Full signed-in/relaunch acceptance is not yet claimed;
the parent is repeating the test on the Mac mini. Private KVM attempts are
`store/.runtime/creator-apple-20261009/ios-ui-r1` through `ios-ui-r4`.

## Scope

Apple build/release work only for native Musia 0.2.0 (7). No commits, native
implementation edits, billing changes, purchases, production submissions, or
withdrawals are authorized in this lane. Preserve both formal 0.1.2 (4) reviews.
The parent owns Android and billing. Do not control the shared Simulator or
interrupt ClearPair/other projects.

## Evidence Collected

The existing isolated Mac QA bundle `art.lazying.musia.creatorqa` completed on
the KVM with `passed: true`. Its result confirms live creator capabilities,
Keychain write/read/delete, minimized playback, 31 catalog entries, three
lessons, and persisted/exported local history. All eight native window captures
were copied and visually inspected: Library, Practice, Stage, Lessons, Settings,
minimum window, Create, and Community. Create/Community coverage is signed-out;
this is not signed-in creation, StoreKit, or audible-output qualification.

Existing compiler logs confirm Debug Mac and generic iOS-simulator builds.
Swift core ran 44 tests: 43 passed, one opt-in network test skipped, zero
failures. These tests are not iOS creator UI runtime evidence.

Private evidence root: `store/.runtime/creator-apple-20261009/`.
Original Mac result directory:
`~/Library/Containers/art.lazying.musia.creatorqa/Data/Library/Caches/Musia-Mac-Review/`
on `echomind-kvm-macos`.

The isolated QA app retains the pre-bump **0.1.3 (6) Debug** identity. Its Swift
implementation matches the creator source archived below, but it is not the
production bundle, the signed 0.2.0 installer, or app-specific StoreKit proof.
Screenshots are 1280x732 or 1040x732 native window captures, not new formal
store-listing screenshots. No physical audio-output qualification is claimed.

## Signed Artifacts

Both projects were regenerated on the KVM using the existing generators and
Ruby `xcodeproj` 1.28.1. Generated pbxproj and shared schemes were returned to
Linux. Mac Info.plist was byte-identical before/after generation. No Swift,
billing, API, UI, entitlement source, generator, or release-tool source was edited
by this lane. The existing parent version/generator changes were used as given.

Xcode 26.6 (17F113), scoped developer directory:
`/usr/local/echomind-formal-xcode/Xcode_26.6.app/Contents/Developer`.

| Artifact | Result | SHA-256 |
| --- | --- | --- |
| macOS 0.2.0 (7), universal PKG | Signed, validated, uploaded, available to internal owner | `573d05c771a627094a7c2559cd5b4f077dfc1e9ebcfe577cb9e961c8445e045b` |
| iOS 0.2.0 (7), IPA | Signed, local inspection and Apple validation passed; not uploaded | `eef2b4c808812ea9c381166e9a61dfbc3d391e80026c0290eba2dc4cb7bb3fbb` |

Canonical files on `echomind-kvm-macos`, under
`/Users/lachlanchen/Projects/Musia/`:

- Mac: `store/.runtime/macos-0.2.0-7/Musia.xcarchive` and
  `store/.runtime/macos-0.2.0-7/export/Musia.pkg`.
- iOS: `store/.runtime/artifacts/ios-0.2.0-7-81056579be73/build.json`,
  `Musia.xcarchive`, and `export/Musia.ipa` in that same directory.

Actual distribution signer on both apps:
`7CF3CFB6318F1C181356F57887A09342F8814BEC`. App identity is
`Q8M2S2FY77.art.lazying.musia`. Existing Musia-specific distribution profiles and
shared authorized keychains were reused; no keys exported or certificates issued.
The Mac installer has the existing LazyingArt Mac Installer certificate.
Mac package inspection confirms arm64/x86_64, sandbox/network/user-selected-file
entitlements, readable installed files, and no Debug review harness. Compiled
and native-resolved rounded icons passed. iOS inspection confirms the exact
bundle/version/profile/signer, allowed audio background mode, and no unexpected
capture permissions or extensions. Apple altool JSON success was checked, not
only process exit status. Validation is not upload, processing, or TestFlight.

Both hosts matched the same complete Apple input manifest, unchanged across
both archives:
`0190dea4015eb921b8b95252922bfccc96f509841ec62c3a7f3ace90ad121810`.
iOS release-tool source digest:
`81056579be739a857bf4264689029f0578b4c113fff88b3a5ecfd957b29c6845`.
Private before/after manifests retain individual file hashes. Static iOS/Mac
validators passed; all 42 existing store-tool tests, five icon-geometry tests,
and all 18 source icon checks passed. Mac compilation retains a nonfatal missing
AccentColor warning; no artwork/source change was made to address it.

## Production-ID Runtime Attempt

A separate copy of the existing Debug app was signed with the existing Apple
Development identity and existing `art.lazying.musia` development profile, using
the scoped signing procedure. The original app container and Keychain were not
deleted, reset, or replaced. Prior review cache and preferences were preserved
privately before running the existing `--musia-review` harness.

The process launched but produced **no fresh result**. Its sampled main thread
was waiting in `_libsecinit_appsandbox` during dyld initialization, before the
app's main code. This is evidence of a sandbox-initialization stall, not a new
CreatorKeychain failure or success. The old failed result from 21:52 PDT was
explicitly rejected as stale. The exact owned process was stopped; the signed
test app and stack diagnostic remain under private `prodid-qa/` on the KVM.

Actual native Account & subscriptions screen and StoreKit Product lookup are
**not verified**. Mac Accessibility reported disabled and the computer-use tool
reported no browser available for the existing noVNC connection. No permission
settings were changed, no shared Simulator was driven, and no native test hook
or other app source was added to bypass this limitation.

## Historical Signing-Lane Blockers

This list describes 05:26 UTC, not current delivery. The parent checkpoint
above supersedes inventory and Mac-upload observations.

1. The current Apple inventory/uploader fails closed with `Ambiguous Musia
   inventory`: Apple's identifier filter returns both `art.lazying.musia` and
   `art.lazying.musia.creatorqa`. The exact App Store app still resolves to
   `6816265930`. An exact-identifier filtering fix with duplicate/missing/wrong-ID
   regression coverage was proposed, but the tracked tool was not changed and
   the guard was not bypassed. No provider record was removed to clear it.
2. iOS creator native-UI runtime qualification is missing. A generic simulator
   compile and Mac captures do not pass that existing internal-beta gate.
3. Production-ID Mac runtime, account screen, and app-specific product lookup
   remain unverified as described above. The clone's passed QA can support
   explicitly limited internal source review only, not production qualification.

The parent reports public privacy/creator live validation, restored existing
protected Apple verification credentials, and an invalid sandbox transaction
probe returning 4000006 rather than 401. These are backend observations, not a
purchase or native StoreKit acceptance receipt. Both checkout paths remain
disabled. Draft subscription metadata remains MISSING_METADATA (review screenshot
suspected, not independently resolved here). Billing is **not finished**.
No purchase, restore-sync, entitlement grant, subscription submission, or sales
enablement was performed by this lane.

## Provider And Runtime Handoff

Read-only Apple status uses the configured app resource ID with an exact bundle
check; this does not modify or bypass the uploader's separate inventory guard.
The before/final receipts are private `apple-before.json` and `apple-final.json`.
Both formal 0.1.2 (4) submissions remain WAITING_FOR_REVIEW with unchanged builds:
iOS `7b0ae745-7e3b-44ab-9100-1de68e99cfc7`, Mac
`1d5a2c57-de54-4120-a219-5a4b158265f5`. Existing 0.1.3 (6) internal builds remain
VALID / IN_BETA_TESTING. No 0.2.0 build is present in App Store Connect. No upload,
invitation, external beta review, formal submission, withdrawal, price, or
territory mutation was made. Final readback: October 9, 05:26:37 UTC (13:26 HKT).

This lane started no GUI stack. The existing shared KVM review connection is
`http://127.0.0.1:6141/vnc.html?host=127.0.0.1&port=6141&autoconnect=1&resize=scale`;
it belongs to the shared KVM, not this lane. Parent creator browser and Android
emulator were left untouched. ClearPair jobs were observed and never stopped;
one iOS preflight returned 75 while its test was active, then succeeded after
that job finished. Musia Mac and iOS archives ran sequentially with two workers.

At cleanup, no owned Musia app/build/altool remained. The temporary signing
search list was restored to landn-release plus login. KVM free disk was 9.2 GiB,
memory_pressure reported 76% free, and swap was 258 MiB of 1024 MiB. Linux had
32 GiB available RAM and 68 GiB of 135 GiB swap used. No peer process, shared
service, container, SDK, model, previous archive, or build evidence was deleted.
No commits were made.

Resume from the signed artifacts above; do not rebuild merely to fix the
inventory tool or collect receipts. Obtain fresh platform-appropriate UI and
app-specific account/Product evidence, keep purchase gates closed, then qualify
the exact hashes for authorized test-only upload. Preserve both formal reviews.
