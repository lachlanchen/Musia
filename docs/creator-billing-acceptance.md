# Creator Billing Acceptance

## Later Parent And Test-Lane Evidence

At 06:42:37 UTC both Google `monthly` base plans were activated and read back
as **ACTIVE**, with the approved US-only USD9.99/USD29.99 monthly configuration.
Musia public and owner-test checkout remain off. This changed no app release.
Private receipt: `store/.runtime/creator-google-catalog/activation-readback.json`.
The guarded catalog tool reconciles existing ACTIVE plans without repeating
activation and accepts an empty HTTP 204 only for the provider's offers-list GET.

October 9: both actual Apple subscription products appear in the native iOS
simulator account screen. No purchase was attempted. macOS 0.2.0 (7) is now
available in internal TestFlight; iOS upload is pending. Google Console License
testing was inspected through the existing authorized session: the configured
Musia self-tester is a member of a selected list, and selection persisted after
reload. Protected receipt: `store/.runtime/creator-license-testing-20261009/result.json`.
No license settings were changed. The newly owned tab was closed and peer tabs
preserved. Enrollment is no longer a blocker, but the installing Play account,
storefront, actual no-charge instrument and purchase lifecycle still need proof.

The earlier read-only checkpoint below is retained as dated evidence, not a
claim that products or license enrollment remain unverified.

## Earlier Checkpoint

Read-only checkpoint: 2026-10-09, 05:46-05:50 UTC (13:46-13:50 HKT).
App `6816265930`; bundle/package `art.lazying.musia`. **Not accepted yet:**
no actual Musia provider purchase, restore, or renewal was exercised here.
No purchase, activation, credential change, native edit, browser/device action,
upload, review change, or commit was performed.

## Verified State

Live `/creator/api/capabilities` reports Free 2, Creator 20 at USD9.99,
Studio 80 at USD29.99 per month; `salesEnabled=false`. Central login is
password-only: Apple/Google/GitHub login providers are false. These login
providers are independent of native store billing.

| Store product | Actual saved US monthly price | Provider state |
| --- | --- | --- |
| Apple `art.lazying.musia.creator.monthly` | USD9.99 | `MISSING_METADATA` |
| Apple `art.lazying.musia.studio.monthly` | USD29.99 | `MISSING_METADATA` |
| Google `musia_creator`, base plan `monthly` | USD9.99 | `DRAFT` |
| Google `musia_studio`, base plan `monthly` | USD29.99 | `DRAFT` |

Apple price proof is fresh GET `/v1/subscriptions/{id}/prices` with
`filter[territory]=USA&include=subscriptionPricePoint,territory`: each saved
price's relationship resolves to `customerPrice=9.99` or `29.99`, respectively,
and included territory `USA` has `currency=USD`. Each has one current record,
`startDate=null`, `preserved=false`, `planType=UPFRONT`; pagination is complete.
This is not the catalog tool's `approvedUSD` label or `usPriceCount` alone.
Google GET `/applications/art.lazying.musia/subscriptions/{product}` returns
`P1M`, US-only regional configuration, USD units 9/29 plus nanos 990000000.
`newSubscriberAvailability=true` does not override the base plan's `DRAFT` state.

Apple's **confirmed missing field is the App Review screenshot on both
subscriptions**: GET `/v1/subscriptions/{id}/appStoreReviewScreenshot` succeeds
with `data=null`. Both have reference/product names, `ONE_MONTH`, review notes,
en-US display names/descriptions, saved prices and USA availability. The group
has its en-US display name; Studio level 1 and Creator level 2 are set.
Screenshot absence explains a concrete review-metadata gap, not an exhaustive
Apple validation result. Capture the real native paywall, upload it separately
to each product's Review Information, then read the status again under separate
authorization. [Apple review screenshot definition](https://developer.apple.com/help/app-store-connect/reference/in-app-purchases-and-subscriptions/in-app-purchase-information/).

Do not make review readiness an invented sandbox gate: Apple's minimum sandbox
product setup is reference name, product ID, localized name and price, alongside
active membership and the Paid Applications Agreement. Product lookup on the
actual Musia build and current agreement status remain unverified here.
[Apple sandbox preparation](https://developer.apple.com/documentation/storekit/testing-in-app-purchases-with-sandbox?changes=_1).

## Accounts And Blockers

- Apple GET `/v2/sandboxTesters` returns exactly one team tester: USA,
  `interruptPurchases=false`, `MONTHLY_RENEWAL_EVERY_FIVE_MINUTES`. Its identity
  matches `~/.config/aimemo/apple/sandbox-tester-20261003.json`; a password exists,
  but its purpose is explicitly **AiMemo sandbox only**. This is not permission
  to reuse it for Musia or change its settings/history. No credentials are copied.
- Ordinary TestFlight purchases already use sandbox. A separate sandbox account
  is needed for configurable sandbox controls, not as a prerequisite to an
  initial TestFlight purchase. Default TestFlight renewal is daily, up to six
  renewals. [Apple TestFlight guidance](https://developer.apple.com/help/app-store-connect/test-a-beta-version/testing-subscriptions-and-in-app-purchases-in-testflight/).
- Apple build 7 lookup returned zero builds at 05:48 UTC. Signed 0.2.0 (7)
  artifacts exist per `store/creator-apple-20261009.md`; the parent owns native
  qualification/upload. Do not use the `.creatorqa` app as subscription proof.
- Google's owning agent's saved Console receipt at 05:46:37 UTC reports
  0.2.0 (6) available to internal testers. This investigation did not drive its
  tab or verify installation. Protected evidence:
  `store/.runtime/creator-android/play-code6-console/11-internal-reloaded.json`.
- Saved Google tester metadata in
  `~/.config/echomind/private/google-play-tester.json` matches Musia's configured
  internal owner, but is scoped to EchoMind sign-in. Neither that match nor a
  saved internal-test list named "license testers" proves license enrollment.
  No confirmed license-testing selection was found in the inspected evidence;
  no new provider account access was attempted.
- Local `~/.config/musia/creator-runtime/billing.json` has both providers in
  `test`, reconciliation enabled, one test owner each, `qualified=false`,
  `sales_enabled=false`, `test_sales_enabled=false`, and no
  `no_charge_test_setup`. Referenced keys/certificates exist and are owner-only.
  Read-only SQLite inspection found zero subscriptions/verification operations;
  each allowlisted Musia user is active, invited, on current terms and has no
  active pilot grant. Account IDs and secrets are intentionally omitted.

## Next Authorized Test

These are future operator steps, **not actions authorized or executed by this
investigation**. Keep public sales closed and preserve existing formal reviews.

1. **Apple:** parent qualifies/uploads the existing signed artifact and confirms
   the exact platform/build in TestFlight. Install on an exclusively assigned
   device, use a US storefront, sign into Musia through central password login,
   and verify both real StoreKit products/prices. Ordinary TestFlight testing
   needs no owner-account sign-out. For accelerated tests, first obtain scoped
   reuse approval or create a Musia-specific US tester at App Store Connect >
   Users and Access > Sandbox > +, using an email not already an Apple Account.
   [Sandbox account setup](https://developer.apple.com/help/app-store-connect/test-in-app-purchases/create-a-sandbox-apple-account/).
   On a dedicated iOS device, install TestFlight first; for sandbox controls only,
   sign out of Media & Purchases and sign into Settings > Developer > Sandbox
   Apple Account. Do not do this on the shared device without its owner's approval.
   [Device setup](https://developer.apple.com/documentation/storekit/testing-in-app-purchases-with-sandbox?changes=_1).
2. **Google:** ask the lane owner to read Play Console > Settings > License
   testing and confirm the exact installing account is selected. Add it only
   with authorization. Publishing-account automatic eligibility is a documented
   alternative, but that account identity was not established here.
   [License setup](https://support.google.com/googleplay/android-developer/answer/6062777?hl=en).
   Separately authorize activation of both `monthly` base plans; `DRAFT` is not
   purchasable. Activation affects the app's catalog, not just its internal
   track, so retain Musia's server purchase gates. Read back `ACTIVE`, use the
   US Play storefront and install code 6 through the existing internal opt-in.
   [Base-plan states](https://developers.google.com/android-publisher/api-ref/rest/v3/monetization.subscriptions).
3. **Backend:** after the no-charge setup is established, the parent may enable
   only that provider's `test_sales_enabled` plus `no_charge_test_setup`, keeping
   `environment=test`, explicit `test_owners`, reconciliation on and public
   `sales_enabled=false`. Confirm fresh per-owner purchase capability; do not
   bypass it with a debug client or pilot entitlement.
4. **Purchase once:** on Apple require the exact Musia product and explicit
   TestFlight/sandbox no-charge context. On Google require the exact account,
   test-purchase notice and "Test instrument, always approves"; never select a
   real payment method. Internal testing alone can charge real money. Monthly
   Google test renewal is approximately five minutes.
   [Google billing tests](https://developer.android.com/google/play/billing/test).
5. **Acceptance evidence:** native delivery must call the normal
   `/creator/api/billing/verify` with its actual transaction ID/purchase token.
   Independently fetch fresh provider truth: correct app/product, test environment,
   owner binding, active state and expiry; confirm durable delivery and Google
   acknowledgement. `/api/me` must show limit 20/80 and
   `usage.source=verified_subscription`, not a grant. Reopen/relaunch and restore
   without another purchase; then capture an actual renewal and updated expiry.
   Qualify each tier, cancellation/paid-through expiry, refund/revocation and
   intended upgrade behavior separately before claiming lifecycle completion.
   Current server purchase capability blocks accounts with unresolved ownership;
   do not force a second subscription to manufacture upgrade evidence.

Keep transaction/account identifiers and raw receipts in protected Musia
evidence. Local StoreKit fixtures, synthetic-token HTTP errors, catalog reads,
TEST notifications and another app's successful purchase cannot close these cases.

Sources inspected: `musia/creator/billing*.py`, both `tools/store/creator_*catalog.py`
tools, protected catalog journals, and the canonical private subscription guide
`LazyingArtLinkPrivate/docs/subscriptions/echomind-handoff-20261004.md`.
No native runtime, build, GUI stack or regression suite was started by this lane.
