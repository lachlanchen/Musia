# Musia Native Store Release

Identity: `art.lazying.musia`, iOS SwiftUI and Android Kotlin/Compose. This worker
owns `store/` and `tools/store/` only. Native workers own `apps/ios/` and
`apps/android/`. Do not launch a store build while a native worker is building.

## Actual State

See `provider-readiness.json`. On 2026-09-25, authenticated Apple GETs found no
Musia app or bundle ID, and the complete Google Play account list had eight apps,
none Musia. Subsequently this worker registered the Musia Apple identifier,
created and validated its App Store profile, and generated a separate Musia
Android upload key. No binary, invitation, pricing choice, privacy declaration,
legal attestation or review submission was sent.

`listing-draft.md` contains feature-accurate listing copy and reviewer steps;
it is not a submitted store listing or a substitute for provider declarations.

App Store Connect web access redirected to login with `authResult=FAILED`.
Apple API credentials still work, but Apple requires its website to create the
app record. Restore the existing account's web authentication, then create an
iOS record named Musia with primary language English, bundle `art.lazying.musia`,
and a unique Musia SKU. Read back its exact bundle ID before recording the app ID.
Do not change agreements, pricing or another app. Without this record, there is
no Musia TestFlight group to attach to.

The Company's browser playbook points to the same L & N-owned shared profile
used by Bunko. Its existing Apps tab can show cached content after expiry:
a read-only session GET on 2026-09-25 returned HTTP 401. The other live store
browser inspected belongs to a different company, not this Apple team. Do not
switch accounts, reuse a personal browser, restart Chrome or repeat login
attempts. The verified restore URL/profile and timestamped evidence are in
`store/.runtime/handoff.md` (private). Restore the account-holder session there
and verify LazyingArt LLC before creating Musia's record.

Google app creation is pending an explicit pricing decision and supported
declarations. Do not inherit Bunko's paid price, silently choose free, create an
API edit as a status probe, or invent an app ID. Later create Musia's own tester
list from the protected owner recipient, not another app's tester configuration.

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

These commands only plan until `--execute-build` is supplied. The parent agent
completed an Android signed build on 2026-09-25 after the native worker finished.
The first attempt used an incomplete system JRE and failed before compilation;
its private log is retained. The verified shared JDK succeeded, with 34 release
tests, release lint, APK and AAB signature and identity checks. Artifacts and
`build.json` are under `.runtime/artifacts/android-0.1.0-1-87c66c5e98e6/`.
This final build includes the corrected native setup instructions and JDK
launcher check. Its APK/AAB bytes match the preceding successful build.
No iOS archive or provider upload was attempted. Check resources and coordinate the one build per
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

Formal review remains disabled. After signed native QA, separately prepare real
screenshots, supported content-rights/privacy/age declarations, support/privacy
URLs, and exact platform-specific submission plans. No accounts/microphone/
uploads/analytics SDK is the current feature scope, not a blanket claim that
streaming hosts/CDNs collect no request logs. Reviewer login should not be
required for this initial scope. Never guess a legal/privacy answer.

Invitation status is currently **not prepared, not queued and not sent**.
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
