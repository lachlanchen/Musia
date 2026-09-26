# Musia 0.1.1 Formal Review

## Authorization and Scope

The owner requested production review for both native apps and confirmed:

- USD 2.99 on both stores, also the default for future releases.
- Worldwide distribution where requirements are satisfied.
- Commercial rights to the catalog, lyrics, translations, vocals and artwork.
- Audible and screen-locked playback work on the latest iPhone TestFlight build.
- The previously confirmed Google program-policy and export declarations remain valid.

These confirmations do not imply store approval. Check
`provider-readiness.json` for the latest observed provider state. No new binary
was needed for listing, privacy-page or release-tool changes.

## Exact Builds

| Platform | Identity | Version | Artifact SHA-256 |
| --- | --- | --- | --- |
| Apple | `art.lazying.musia`, app `6816265930` | 0.1.1 (2) | `d3e3c0024c86c458dbded347d3bbd12db65f42b3a3e8b42074693c761bbbbb9c` |
| Google | `art.lazying.musia`, app `4973883817798043601` | 0.1.1 (2) | `3fea7eb3eac69e8e3160cfda5555913502c8ae1630d5711759c57e917ce81387` |

Apple version resource: `f4337c74-f5d9-4613-879c-df5fb3712e9e`.
Attached build: `c012938a-29d5-419b-9254-29d41f074f76`, VALID.
Manual public release is selected. Reuse Google's internal AAB through
**Add from library**, not another upload. Existing owner invitations remain valid.

## Listing and Privacy

`listing.en-US.json` is the reusable, feature-accurate copy. It explicitly
distinguishes the verified First Pulse reference exercise from estimated song
analysis. Do not advertise microphone analysis, uploads or cloud generation in
this native build. No login, subscription or advertising is required.

The live privacy page is `https://musia.lazying.art/privacy`. Network requests
to catalog and media hosts expose IP addresses and selected resources; local
practice history remains on the device. GitHub Pages retains IP logs for
security. No advertising or cross-app tracking is claimed or configured.

- Apple: Device ID and Product Interaction, linked, App Functionality, not tracking.
- Google: Device or other IDs and App interactions, collected/shared, non-ephemeral,
  required for streaming; app functionality and security/compliance purposes.
- The absence of an analytics SDK does not mean external hosts collect no data.
- Resetting local history does not erase external hosting logs.
- Teen/adult audience; no account creation or account-deletion flow.

Sources: [GitHub Pages collection](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages),
[GitHub privacy](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement),
[Apple privacy details](https://developer.apple.com/app-store/app-privacy-details/),
[Google data safety](https://support.google.com/googleplay/android-developer/answer/10787469).

Apple calculated age 13+ after the music-content questionnaire. Google IARC
calculated its regional ratings independently; do not copy one store's rating
into another. Public support is `support@lazying.art`. Reviewer personal contact
details are kept in the ignored private runtime directory.

Apple availability was saved for 174 territories, excluding China mainland
because an ICP filing has not been supplied. Automatically adding future
territories is disabled so their requirements can be checked first.

## Google Submission

The exact internal AAB was added from the library to production release
**0.1.1 (2)**, targeting **172** eligible paid-app regions. Console validation
reported only optional deobfuscation/native-debug-symbol warnings. Minification
is disabled; no unqualified replacement bundle was generated for these warnings.

The final **Send changes for review** confirmation was accepted for 10 changes.
A fresh reload shows **Changes in review**, while automatic quick checks are
still running. This is not approval or public availability. Managed publishing
is **on**, so approval alone will not publish the app. Reconcile this pending
submission before any subsequent mutation; do not send a duplicate.

Google's asset-specific AI declaration labels the AI-assisted authored icon and
feature graphic and the First Pulse screenshot containing existing AI artwork.
The other unedited native screenshots are not labeled synthetic. See
[the provider's asset declaration guidance](https://support.google.com/googleplay/android-developer/answer/17262077).
Private hashes and exact original paths are in `formal/google-assets.json`.

## Authentic Review Assets

`tools/store/capture_android_review.py` records the installed native app on a
Musia-owned emulator and captures actual foreground, background and notification
media-session state. It does not reconstruct the UI or dub audio onto the demo.

```bash
PYTHONNOUSERSITE=1 conda run -n musia python tools/store/capture_android_review.py \
  --serial emulator-5580 --output store/.runtime/formal/android
```

Use an existing, exclusively owned `Musia_*` AVD and the exact reviewed APK.
The script stops the app afterward; its launcher remains responsible for
stopping the emulator. It refuses physical devices and other projects' AVDs.
This screenrecord has no audio track: it demonstrates native playback controls
and media-session state, not audible playback QA.

The foreground-service review video is available at
[the review-evidence release](https://github.com/lachlanchen/Musia/releases/tag/musia-review-0.1.1-2).
Its SHA-256 is `49a3d16663f10c1b93fde1d5524986fb570703bc3edb60a1ef574b8ca0988694`.
This prerelease contains review evidence, not a production app release.

`feature-graphic.html` renders the 1024 x 500 Play feature graphic with the
actual native app icon. Generated PNGs and raw screenshots remain ignored.
Review screenshot contents and dimensions before upload; never substitute web
screenshots or fabricated screens for a native listing.

## Apple Screenshot Continuation

The actual **Add for Review** validation currently reports only:

- A screenshot for 6.5-inch iPhone displays is required.
- A screenshot for 13-inch iPad displays is required.

The virtual Macs produced incomplete or black screenshots. A bounded native
UI-test capture also timed out before producing usable attachments. These are
not successful screenshot or audio tests. TestFlight device playback was
confirmed separately by the owner. The owner may connect an iPad later through
the established LazyTunnel route; do not assume it is connected now.

Capture genuine latest-build screens on suitable devices or a working native
simulator, inspect them, upload to the supported display sets and re-run
validation. Do not stretch unsupported images, upload black screens, replace
the qualified build, or disable iPad support just to bypass this requirement.
Then Add for Review, submit once, and read back the review ID and state.

## Provider and Runtime Discipline

Use the exact retained provider target IDs from private
`store/.runtime/formal/{apple,play}-tab.json`. The shared noVNC/CDP stack belongs
to another project: preserve it and unrelated tabs. Fresh Apple session HTTP
200 and the expected provider are authentication evidence; cached pages are not.

Keep raw provider receipts, screenshots, personal contacts and session details
under ignored `store/.runtime/`. The existing beta API mutation allowlist stays
unchanged; a formal browser submission is a separate, explicitly authorized lane.
Saved metadata, draft releases, checks running, in-review, approval and public
availability are distinct states. Reconcile uncertain mutations before retrying.

## Deployment and Verification

Privacy-page deployment transaction: `20260926T153345-99b459c47682`.
Archive SHA-256: `99b459c47682b3c97b1c171c71b82332673ad0206fd36619b01f7a7f52894ff5`.
Public acceptance checks passed. Shared ingress was preserved.

The deploy guard now fingerprints protected literal imports without retaining
their contents, refuses unsupported dynamic/nested imports and concurrent
changes, and skips ingress reload if the candidate is byte-identical. A stage
failure before mutation is recorded as such rather than a false rollback failure.

Validation: 29 store-tool tests and 8 deployment tests pass. Existing binary QA
remains tied to its exact source and artifact hashes; release-tool tests are not
a substitute for native runtime tests.
