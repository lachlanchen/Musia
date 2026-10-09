# Android Creator Internal Delivery - 2026-10-09

## Agent And Studio, Build 7

October 9, 11:08 UTC: **0.2.0 (7) is Available to internal testers**. The
existing owner-only list was reverified, including its exact member and opt-in
URL. The bundle was uploaded and published once through the internal Console
flow. Production remains 3 (0.1.2), held under managed publishing with the same
one pending change. No global publish, tester change or invitation resend.

Agent is the default Create tab; Studio edits the same local, account-scoped
draft. Conversation history is bounded and persisted. Replies retain fields
edited while the request runs; render confirmation remains explicit.

- AAB: `4bc440357b99f388960a55ff5f14686c89b31c71154692af7a00121f1c5fae4e`.
- Source: `7683ed68cf536e402b36fc9c5b3be02c6605074a4c886a9760a4f2f56b362ae5`.
- QA APK: `533b9c42cb18df6a33d4e3b6b83290368c94a682c0bda8a6e4f7691def6647a7`.
- 50 release unit tests, release lint, signing/permissions and exact-artifact
  internal qualification passed. Actual owned-emulator workspace and Stage
  tests passed; screenshots were directly reviewed. These are build-7 QA-APK
  tests, not a new Play-installation or physical-audibility claim.
- The two nonblocking Console warnings are missing deobfuscation/native debug
  symbols. Device coverage is unchanged.

Evidence: `store/.runtime/creator-agent-android7/`, especially `qa.json`,
`23-published.json`, `25-production-preserved.json` and `test-access.json`.
The Console identity check now accepts its observed listing-title header only
at the exact configured app/track URL; wrong-app/track/title regressions are
covered. A prior readback failure was this obsolete label expectation, not a
failed release. Public paid checkout stays disabled.

## Later Play-Installed Checkpoint

October 9, 07:30 UTC: the actual **0.2.0 (6)** internal release was installed
from Google Play on the dedicated Musia emulator. Installer and initiator are
`com.android.vending`; four installed APK splits and the Play signing identity
were checked. Only this disposable emulator's earlier QA APK was replaced,
after its artifact and evidence were preserved. No physical device was reset.

Play signer SHA-256:
`fc75a5bdb5d494557da523ada3202842c9ed3f6bc21cb2154ebcf346e1a7d9ed`.
The installed base APK SHA-256 is
`bfddae983519f27183f2aa1b411f45e1c6f0dfeac348a219decb9d513e4d480f`.
The Play signer differs from the upload/QA signer by design.

Real native shared-password login and USD9.99/USD29.99 store prices were
observed on that installation. One explicitly no-charge Creator purchase was
confirmed; the server and independent Google GET verified its app/product,
test environment, acknowledgement and owner binding. Actual provider renewal
was also observed. See [billing acceptance](../docs/creator-billing-acceptance.md)
for the latest lifecycle evidence and remaining cases. Public paid checkout
stays disabled. Physical-device audible output is not established by this
emulator. Private evidence: `store/.runtime/creator-play-readiness-20261009/`.

The paragraphs below retain the earlier Console-only delivery checkpoint;
their installation/purchase limitations are superseded only as stated above.

## Actual Result

Google Play Console confirms **0.2.0 (6), Available to internal testers**.
The internal track is Active and identifies 6 (0.2.0) as its latest release.
Console records release on October 9 at 13:40 Hong Kong time. A fresh page
reload verified availability at 13:46; the final production check was at 13:47.

The preceding operation journal already contained the single AAB upload and
internal-only publish confirmation. This continuation reconciled those actions:
**no reupload, repeat publication, API upload, or provider mutation was made**.

Only **Musia Internal Owner** is selected. Its one member was privately matched
to the existing configured owner. No tester-list change or invitation email
was sent; email receipt and installation are not claimed.

[Internal testing opt-in](https://play.google.com/apps/internaltest/4701000336240069263)
uses that same existing tester account.

## Exact Artifact And QA

- Package: `art.lazying.musia`; signed Android 0.2.0, version code 6.
- AAB SHA-256: `464754b8604ef92d9eeb7a5062600f1fe27de7218817a24ff55ee56de3adef7f`.
- Source SHA-256: `1bac3ea216e630f3225dd4565930a93da6f11d33cbd1c40845112bbe3c68f016`.
- Existing internal-beta qualification guard passed again against the exact
  artifact, current Android source, build receipt and hashed QA evidence.
- Retained QA records 48 release unit tests; native system-browser OAuth;
  Keystore session restoration after relaunch; private song visibility and
  Media3 playback clock advancement; sign-out clearing private playback;
  and Stage player/language/seek/chord/navigation regression checks.
- These are prior signed-QA-APK emulator tests, not a fresh native test run
  during this Console continuation. No app source change or heavy build ran.
- Console accepted the release with two warnings: missing deobfuscation file
  and native debug symbols. No blocking release errors were recorded.

## Preserved Boundaries

Production **3 (0.1.2)** remains **Changes ready to publish**, with managed
publishing **on**. The final Publishing overview text and screenshot match
the pre-internal-release baseline. **Publish 1 change** was not activated.
No production promotion, global publish, review change, or Apple action occurred.
Existing formal reviews remain outside this Android-only continuation.

Purchases remain disabled; real billing receipts are unqualified. Creator
access requires an invitation, and public sharing remains moderation-gated.
Play-installed execution and physical-device audible listening remain unverified.
This is internal test distribution, not production qualification.

## Evidence And Cleanup

Private evidence is under `store/.runtime/creator-android/play-code6-console/`:
`final-result.json`, fresh Console screenshots/readbacks, owner membership
verification, and `cleanup.json`. Both existing operation journals now point
to the terminal readback. Their original dispatch evidence was preserved;
the upload journal retains its legacy dispatch marker for tool compatibility.
Do not interpret that marker as authorization to upload again.

Only the owned Google tab was closed, with absence verified afterward.
Both existing ClearPair tabs and the shared store browser were preserved.
No new GUI stack, emulator, build, or background job was launched. No commit.
