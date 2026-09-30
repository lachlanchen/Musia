# Musia Native Store Release

Identity: `art.lazying.musia`, iOS SwiftUI and Android Kotlin/Compose. This worker
owns `store/` and `tools/store/` only. Native workers own `apps/ios/` and
`apps/android/`. Do not launch a store build while a native worker is building.

## Actual State

2026-09-26: both application records exist, and **paid USD 2.99** is saved in
both provider consoles. The owner chose this as the future default. Each price
was verified after a fresh page reload, not just a successful click or toast.

| Provider | Store Record | Readback |
| --- | --- | --- |
| Apple | `6816265930`, **Musia: Learn Music & Guitar** | API verified `art.lazying.musia`; US price $2.99 |
| Google | `4973883817798043601`, **Musia** | Full account inventory verified `art.lazying.musia`; US price USD 2.99 |

The owner restored Apple login; a fresh session GET returned 200 for LazyingArt
LLC. Apple rejected the bare name Musia as already used, so the descriptive
branded name above was accepted. Google creation used English (US), App and
Paid. Its Developer Program Policies and US export-law declarations were
explicitly confirmed by the owner before checking and submitting them.

Other regional prices use the providers' conversions. Apple availability is
saved for 174 territories (excluding China mainland pending ICP), and Google
production targets 172 eligible paid-app regions. Version **0.1.1 (2)** is available in both internal
testing tracks. Google's release and sole owner tester list were read back in
Console. Apple processed the signed IPA as VALID and reports IN_BETA_TESTING;
the exact build is attached to the existing owner-only Musia Internal group,
with its preceding build preserved. Existing invitations remain valid; no new
email or resend was requested for this update. See `provider-readiness.json`
for the latest TestFlight group/access readback. The owner subsequently requested
formal production review and separately confirmed commercial catalog rights,
worldwide distribution where eligible, and real iPhone playback.

**2026-09-30:** Google still reports **Changes in review** for production
0.1.1 (2), verified after a fresh Console reload; its existing 10-change
submission was preserved. Apple now reports **Waiting for Review** for the
same version after genuine native screenshot capture and submission. All eight
screenshots finished processing. No replacement binary or duplicate invitation
was needed. Google managed publishing and Apple manual release remain selected;
neither app is approved or public yet. See
[submission record](formal-review-2026-09-30.md),
[original qualification](formal-review-2026-09-26.md) and `provider-readiness.json`.

Historical inventory on 2026-09-25 found no Musia record and eight Google apps;
after creation there are nine. Earlier Apple 401/login-failed evidence is kept
privately as history, not a current blocker. The bundle identifier, app-specific
profile and separate Android upload key remain unchanged.

`listing-draft.md` is historical draft copy. `listing.en-US.json` contains the
current saved listing and reviewer steps; neither replaces provider readback.

Use the existing shared browser recorded in `.runtime/handoff.md`; do not
restart it or switch to the separate company's browser. Identify retained tabs
by exact CDP target ID with `tools/store/browser_ui.py`, not page order or a
broad URL match. Preserve other projects' tabs. If a submit is interrupted,
reconcile through inventory/current provider state before retrying; retain
operation journals. Never recreate these app records.

Apple's pricing dialog persisted its schedule on **Confirm**. The top Save
control was CSS-disabled (without a native disabled attribute), so a subsequent
click was intercepted and did not dispatch. Reload and the read-only regional
price popover confirmed $2.99; no forced click or duplicate save was needed.
Google required **Update**, then **Save changes**, followed by a fresh reload.
These observations document this console session, not permanent UI selectors.

Reuse the protected owner tester recipient when a test release is available,
not another app's tester list. Do not inherit another app's price, choose free,
or open a Google API edit merely as a status probe. Apple's initial draft 1.0
has been reconciled to 0.1.1 and the exact build 2; do not recreate it.

## Runtime And Credentials

The default wrapper uses the Musia conda environment. Its current Python lacks
PyJWT/cryptography/websocket-client; provider commands below explicitly reuse
the existing system provider runtime rather than installing duplicate packages:

```bash
MUSIA_PYTHON=/usr/bin/python3 tools/store/musia-store inventory-apple
MUSIA_PYTHON=/usr/bin/python3 tools/store/musia-store inventory-play
```

`store/.runtime/config.json` is ignored and mode 600 under a mode-700 directory.
It references the existing account-level ASC key without copying its contents.
The owner tester address and all personal invitation evidence live only here.
Never paste this file or generated private logs into a public issue/commit.
`MUSIA_STORE_CONFIG` may select another absolute owner-only config file.

The shared distribution certificate was matched against the Mac keychain by
fingerprint, then bound to Musia's own profile. A shared account certificate is
not permission to reuse another app's bundle ID, profile or Android upload key.
The Apple builder does not unlock, import into, relock or change search lists of
shared keychains. It requires an already available configured signing identity.
Coordinate any signing-session preparation with the build-host owner.

For this beta, the existing `landn-release.keychain-db` identity was reused with
Musia's own profile. The build-host preparation followed Bunko's protected
password/partition workflow without importing a certificate or changing global
search lists/timeouts. Unlock and archive must run in the **same SSH security
session**; a successful probe in an earlier SSH session did not enable the later
archive. Preserve the private failed-attempt logs; do not treat them as current
build status. The keychain was tightened to owner-only permissions.

The Mac provider runtime is `~/.local/share/musia/store-python/bin/python`
(PyJWT 2.10.1 and cryptography 45.0.7 binary wheels). Use it for provider commands;
the system Python still suffices for the native builder. No SDK or signing keys
were duplicated to install these small provider dependencies.

## Native Worker Handoff

- Android signing: `MUSIA_SIGNING_PROPERTIES` must point to the absolute
  `store/.runtime/android/signing.properties`. Its key is Musia-only. Keep the
  password file, properties and PKCS12 owner-only; do not regenerate the key.
- iOS provisioning: `store/.runtime/apple/Musia_App_Store.mobileprovision`.
  Team `Q8M2S2FY77`; profile name `Musia App Store`; UUID in `release.json`.
  Stage the profile privately on the Mac, not inside `apps/ios/`.
- Mac host: `echomind-kvm-macos`. The verified Xcode 26.6 developer directory is
  `/usr/local/echomind-formal-xcode/Xcode_26.6.app/Contents/Developer`.
  Current default Xcode is 26.3. No global `xcode-select` change is needed.
- Mac private config must use Mac-local existing ASC key/keychain paths and the
  staged Musia profile. Do not blindly copy Linux absolute paths.
- Android SDK: `/home/lachlan/Android/Sdk`; verified shared JDK:
  `/home/lachlan/.sdkman/candidates/java/21.0.10-tem`. Gradle 8.14.3 is cached.
  The system `java-21-openjdk-amd64` path currently contains only a JRE;
  the release builder rejects incomplete JDKs before launching Gradle.
- Signed AAB inspection uses a checksum-pinned shared standalone bundletool JAR.
  `tools/store/install_bundletool.py --configure` reuses or installs version
  1.18.3 outside the repo and updates only the protected local configuration.
  Its pinned SHA-256 is taken from the
  [official release asset](https://github.com/google/bundletool/releases/tag/1.18.3).
  The shared installation was verified on 2026-09-25. Do not confuse Gradle's
  library JAR with the standalone executable or commit the downloaded JAR.

## Build And QA

Current **0.1.1 (2)** fixes navigation overlap and shares all 24 major/minor
guitar diagrams across clients. Build receipts are
`.runtime/artifacts/android-0.1.1-2-0829eef1b9c2/build.json` (Linux) and
`.runtime/artifacts/ios-0.1.1-2-47891c9291fd/build.json` (Mac).
Android has 36 passing release unit tests, release lint and signed-APK
phone/tablet/enlarged-text layout and playback checks. Swift has 23 passing core
tests and one opt-in network skip; iPhone/iPad simulator navigation, rotation
and enlarged-text tests pass. The virtual Mac's system-tab screenshot and
audio-clock limitations remain. The owner has since confirmed audible and
locked-screen playback on the latest TestFlight iPhone build. Genuine listing
screenshots were captured on a hardware Mac mini on September 30; both native
capture tests passed and the chosen images were visually reviewed. See the
[fix and regression checks](../references/musia-native-chords-and-navigation-2026-09-26.md)
and [reusable capture procedure](formal-review-2026-09-30.md#native-screenshot-capture).

Historical first-beta build:

These commands only plan until `--execute-build` is supplied. The parent agent
completed an Android signed build on 2026-09-25 after the native worker finished.
The first attempt used an incomplete system JRE and failed before compilation;
its private log is retained. The verified shared JDK succeeded, with 34 release
tests, release lint, APK and AAB signature and identity checks. Artifacts and
`build.json` are under `.runtime/artifacts/android-0.1.0-1-87c66c5e98e6/`.
This final build includes the corrected native setup instructions and JDK
launcher check. Its APK/AAB bytes match the preceding successful build.
The signed iOS archive/export is now verified under
`.runtime/artifacts/ios-0.1.0-1-36bc223c0358/`. Apple validation and upload succeeded,
and the build processed as VALID. Check resources and coordinate one build per
platform/project before using the execute flag. Tool-owned locks alone cannot
detect a worker invoking Gradle or Xcode directly.

```bash
MUSIA_PYTHON=/usr/bin/python3 tools/store/musia-store build-android
# Mac, in the staged Musia checkout with its Mac-local private config:
MUSIA_PYTHON=/usr/bin/python3 tools/store/musia-store build-ios
```

Android executes release unit tests, lint, signed APK and AAB builds. iOS archives
and exports with a Musia profile mapping, without automatic provisioning.
Both preserve output/logs, hash source before/after, inspect signatures and
package/version, and emit `build.json` only after verification. Existing output
is never overwritten. Build success is NOT native runtime QA.

Use `qa.example.json` as a schema, not as evidence. In a private QA receipt,
bind the exact build-receipt hash, source hash and artifact hash. Supply passed
checks and nonempty hashed evidence for unit tests, native navigation/smoke,
offline progress, background playback, permissions and content rights. Record
the actual OS/simulator/device, review timestamp and limitations. Website tests
alone do not qualify native binaries. No check starts as passed.

For an explicitly requested **owner-only internal beta**, add `--internal-beta`
to qualification, upload and invitation commands and use an internal-beta QA
receipt. It requires exact source/artifact/receipt hashes, passed unit/native-UI/
permissions/content-review evidence, `scope: internal-owner-test`,
`production_qualified: false`, and nonempty known limitations. It does not turn
unresolved playback/device/content-rights checks into passed full-release checks.
See [internal beta review](internal-beta-review.md). iOS device playback is an
explicit owner test because simulator AVPlayer failed on the audio-less Mac.

```bash
MUSIA_PYTHON=/usr/bin/python3 tools/store/musia-store qualify \
  --build-receipt /absolute/private/build.json --qa /absolute/private/qa.json
```

Preserve receipts and evidence. The main artifact path in new build receipts is
relative to the receipt directory for cross-machine transfer; QA evidence may
also use paths relative to its receipt. Keep the same source tree on both hosts.

## Upload And Test Access

`upload-apple`, `upload-play` and `invite-self` require both QA arguments above.
They are plans without `--confirm-upload` or `--confirm-invite`. Every provider
mutation is journaled before execution; reconcile uncertain results before retry.
Never delete a journal simply to make an ambiguous upload/send run again.

- `upload-apple`: Mac only; verify exact IPA, validate with altool, then upload
  only with confirmation. A delivery result does not mean processed/available.
- `invite-self`: after an exact VALID build and matching upload receipt, create
  a Musia-only internal group without all-build access, attach only that build,
  and add the already known owner tester. No new account users, bulk invitations,
  public beta group or automatic resend. Read back relationships; adding a tester
  is not proof that an email was received.
  Apple can have multiple tester records for the same email across apps. Select
  the existing owner account through Musia's internal-group UI on first setup;
  the CLI filters `/betaTesters` by both app ID and email and verifies the
  tester-to-app relationship, never an arbitrary account-wide match. The
  `/apps/<id>/betaTesters` read was rejected by this provider; the documented
  app filter works. No new company account user is created.
- `upload-play`: needs the observed Musia app ID and internal prepare URL in
  private config. It rechecks account/app/package/track, uploads the qualified
  AAB once, and **does not click Save, Publish or Send for review**. Reconcile
  processing in the bundle library. Finish internal publication and tester-list
  selection through the observed Console flow, then read back availability.
- `invite-play-self`: requires the matching AAB upload journal and freshly
  observed exact internal release, owner tester access and opt-in URL. It writes
  a private `.eml` by default. Sending additionally needs `--confirm-invite` and
  an explicitly configured existing trusted `sendmail_path`; none is currently
  configured. It never installs a mail server or guesses SMTP credentials.
  Transport acceptance is not delivery confirmation. Gmail-browser delivery of
  that private draft remains a separately observed operator action.

Play upload leaves its single owned upload tab open, recording its ID privately,
so closing the helper cannot abort an in-flight AAB transfer. After observing
processing completion, close that exact tab. Inventory tabs always close.

Update forms can omit the package label. The upload helper now verifies the
exact package on the parent internal track, then validates the same track's
exact prepare URL and heading. A newly opened, unsaved draft can be client-side
only: navigating a second tab directly to its URL redirects away. In that case
retain the original owned draft tab, recheck the parent track separately, and
upload only the qualified, snapshotted AAB there with a mutation journal. Do
not weaken identity checks, create another draft, or retry an uncertain upload.

Formal review remains disabled. After signed native QA, separately prepare real
screenshots, supported content-rights/privacy/age declarations, support/privacy
URLs, and exact platform-specific submission plans. No accounts/microphone/
uploads/analytics SDK is the current feature scope, not a blanket claim that
streaming hosts/CDNs collect no request logs. Reviewer login should not be
required for this initial scope. Never guess a legal/privacy answer.

Google internal opt-in: https://play.google.com/apps/internaltest/4701000336240069263.
The owner-only list selection and exact member were read back after reload.
Gmail confirmed **Message sent** for its installation invitation; receipt is
private. TestFlight **Musia Internal** has exactly one owner tester and build
0.1.0 (1): **Testing** in the UI and **IN_BETA_TESTING** in the API. Owner status
is **Invited**. No external beta/review was submitted or invitation resent.
Commands distinguish a plan, a private draft, confirmed tester membership and
mail-transport acceptance. None of these proves that a recipient received email.

## Tool Tests

```bash
PYTHONNOUSERSITE=1 conda run -n musia python -B -m unittest discover -s tools/store/tests -v
bash -n tools/store/musia-store
```

These tests are local fixtures and guards, not builds or provider qualification.

## References

- `../../L-And-N/store/publishing-runbook.md`: shared account/build operational history.
- `../../Bunko/tools/store/build-ios.sh`: account certificate with app-specific profile.
- EchoMind's `docs/echomind_standard_publication.md` in the verified formal-current
  checkout: separate testing/review states, private evidence and uncertain-result reconciliation.
- [Apple app creation](https://developer.apple.com/help/app-store-connect/create-an-app-record/add-a-new-app)
- [Apple Apps API is not for creating app records](https://developer.apple.com/documentation/appstoreconnectapi/apps)
- [Apple provisioning profiles](https://developer.apple.com/documentation/appstoreconnectapi/profiles)
