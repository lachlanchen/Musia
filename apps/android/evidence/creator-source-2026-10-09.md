# Android creator source handoff

Scope: Android source only. Version remains 0.1.3 / code 5. No commits, pushes,
Gradle builds, emulator/device operations, runtime desktops or store uploads.
The earlier `verification.md` describes a previous binary, not these sources.

## Checks completed

- Kotlin PSI parser: 30 Kotlin files, zero syntax errors.
- Focused standalone JVM contract tests: 8 passed.
- Isolated Kotlin type-check of creator API, vault, ViewModel and Play Billing
  controller with cached Android 36 and official Billing 9.1.0 APIs: passed.
- `git diff --check -- apps/android`: passed.
- Official cached Billing 9.1.0 API inspection confirmed ProductDetails result,
  suspended-purchase query and pending-purchase APIs used by source.
- Source-only JVMs exited. No project runtime or GUI was launched.

Tests cover the RFC 7636 S256 vector and random verifiers; exact native return
URI, duplicate parameters, wrong/expired attempt; logout/same-account relogin
generation guards; original-owner render body/key persistence; definitive vs
unknown rejection handling; draft/terms/invitation gates; duplicate-purchase
gates and account-token binding; backend numeric expiry and conservative unknown
verification; no draft lyrics as timed transcript.

Reproduce: `bash tools/check-creator-source.sh --controllers` from apps/android.
This is a small standalone parser/JVM source check, not an Android build. It
does not certify Compose UI type checking, resource linking or runtime APIs.

## Parent build and runtime qualification

Run the app's existing sequential debug build/unit-test/lint flow when its turn
in the workstation queue arrives. New dependencies: Billing 9.1.0, Browser
1.9.0, and Media3 OkHttp data source 1.8.0. The latter may require first Maven
resolution. No version bump or signing changes were made.

Check Custom Tabs completion cold/warm, duplicate/malformed return, expiry and
process death; Keystore recovery and AtomicFile interrupted-write recovery;
offline logout revocation, account deletion and account switches during every
async flow; render disconnect/process death and exact retry; terms/invitation
gates; private/public playback, range requests, no credential redirects,
logout during buffered audio, notification controls and old learning features;
moderation/report/block/comment behavior; TalkBack, largest font, small phone
and tablet layouts.

Billing needs an actually qualified Play test account/build/product/provider:
localized monthly offers, cancellation, pending-to-purchased, suspension,
network loss before/after verification and durable server acknowledgement,
process restart, restore with new sales disabled, mismatched Musia account and
unknown binding. No sandbox purchase, provider grant or acknowledgement was
executed by this source task.

## Contract observations / limitations

- Backend `billing.status` returns `expiresAt` as epoch seconds or null. Android
  implements that numeric form; contract prose did not specify the type.
- Backend `/api/blocks` returns `{accounts:[{id,name}]}` and comment `author`
  is a string; Android follows those observed shapes.
- At source inspection, `/api/capabilities.salesEnabled` is literally false.
  Android therefore blocks new sales even if per-account Google purchase later
  becomes true. Parent must expose truthful global readiness when ready; do
  not bypass this in Android. Restore/manage do not depend on this flag.
- An interrupted purchase with no reference and no definitive cancellation
  remains blocked from repurchase even if Play's owned query is empty. There is
  no contract endpoint for support to reconcile such a launch. Preserve it and
  use support rather than resetting storage to force another purchase.
- Unknown render outcomes are retained until the original idempotent request
  succeeds. The server's job list has no request-key field; it cannot independently
  correlate an unknown request without replay. Retry remains explicit.
- No native recorder was present in this Android source baseline. Existing
  learning/player/practice code and local history are preserved; no microphone
  or recording feature was removed or added.

## Primary implementation references

- [Google Billing release notes](https://developer.android.com/google/play/billing/release-notes)
- [Play Billing integration](https://developer.android.com/google/play/billing/integrate)
- [Owned/suspended purchase query](https://developer.android.com/reference/com/android/billingclient/api/QueryPurchasesParams.Builder)
- [Pending purchases](https://developer.android.com/reference/com/android/billingclient/api/PendingPurchasesParams.Builder)
- [Subscription ProductDetails](https://developer.android.com/reference/com/android/billingclient/api/ProductDetails.SubscriptionOfferDetails)

Provider registration, backend verification tests, deployment, artifact builds
and distribution are owned by the parent.
