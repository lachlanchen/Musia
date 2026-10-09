# Creator Apple Test Release, 2026-10-09

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
| macOS 0.2.0 (7), universal PKG | Signed, local inspection and Apple validation passed; not uploaded | `573d05c771a627094a7c2559cd5b4f077dfc1e9ebcfe577cb9e961c8445e045b` |
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

## Delivery Blockers

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
