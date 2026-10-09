# Creator Billing Acceptance

## Current Acceptance

As of **2026-10-09, 08:21 UTC**, Play-installed Android **0.2.0 (6)** has
completed real Google no-charge test purchases for **Creator and Studio**.
Both purchases were independently provider-verified, acknowledged and bound to
the intended Musia owner. The live server durably stored each verified
entitlement; neither came from a pilot grant.

The parent closed Google's temporary owner-test checkout gate at
**08:21:09 UTC**. `test_sales_enabled=false`, public `sales_enabled=false`, and
live capabilities report `salesEnabled=false`. The gate receipt retains
`environment=test` and `qualified=false`: these bounded cases do not enable
public billing or establish complete production qualification. Apple checkout
remains disabled. Existing formal app reviews are unchanged.

### Observed Google Cases

| Case | Creator | Studio |
| --- | --- | --- |
| No-charge purchase | Native test sheet, always-approves test card and privately matched licensed billing account; no real payment method | Same checks; separate purchase after Creator expired, not an upgrade or parallel subscription |
| Verified delivery | Active test entitlement, owner binding and acknowledgement confirmed at 07:59; native allowance uses `verified_subscription` | Active test entitlement, owner binding and acknowledgement confirmed at 08:09; native verified delivery observed |
| Actual renewal | Provider expiry advanced by 300 seconds at 08:00 | Provider expiry advanced by 300 seconds in the 08:15 readback |
| Relaunch and restore | Clean relaunch preserved the session; native restore without another purchase brought server expiry into agreement by 08:02 | A separate Studio relaunch/restore case is not established by these receipts |
| Cancellation and expiry | Google UI cancellation observed; provider expired at 08:05; native restore showed Free and server ledger was expired by 08:07 | Google UI cancellation observed at 08:19; native returned to Free with an empty owned query; provider and server both expired in the 08:21 readback |

The first renewal readbacks still showed the prior server expiry. Creator's
later restore establishes propagation; Studio's final receipt establishes
matching expired provider/server state, not an independently verified
active-state restore. Both native return-to-Free observations had no unresolved
ownership notice or new purchase. The Play Billing Lab US override did not
change the real account country. Catalog visibility, license enrollment and
internal distribution alone were not treated as no-charge purchase proof.

### Protected Evidence

These dated receipts are private and Git-ignored. Do not copy tokens, account
identities, transaction/order identifiers or raw provider receipts into docs.

- Creator: [purchase](../store/.runtime/creator-google-billing-20261009/purchase-readback.json),
  [renewal](../store/.runtime/creator-google-billing-20261009/renewed-readback.json),
  [post-restore provider/server readback](../store/.runtime/creator-google-billing-20261009/post-restore-readback.json),
  [native relaunch/restore](../store/.runtime/creator-play-readiness-20261009/native-relaunch-restore-renewal.json).
- Creator expiry: [cancellation](../store/.runtime/creator-play-readiness-20261009/creator-cancellation.json),
  [provider expiry](../store/.runtime/creator-google-billing-20261009/canceled-readback.json),
  [server ledger](../store/.runtime/creator-play-readiness-20261009/creator-expired-ledger.json),
  [native Free readback](../store/.runtime/creator-play-readiness-20261009/creator-expired-native-free.json).
- Studio: [no-charge checkout](../store/.runtime/creator-play-readiness-20261009/studio-checkout-observation.json),
  [purchase/delivery journal](../store/.runtime/creator-play-readiness-20261009/studio-checkout-journal.json),
  [initial provider/server readback](../store/.runtime/creator-google-billing-20261009/studio-initial-readback.json),
  [renewed provider expiry](../store/.runtime/creator-google-billing-20261009/studio-pre-renewal.json).
- Studio expiry: [cancellation](../store/.runtime/creator-play-readiness-20261009/studio-cancellation.json),
  [native Free readback](../store/.runtime/creator-play-readiness-20261009/studio-expired-native-free.json),
  [final provider/server expiry](../store/.runtime/creator-google-billing-20261009/studio-post-cycle.json).
- [Google test-gate closure](../store/.runtime/creator-google-billing-20261009/gate-disabled.json).

## Acceptance Limits

These results do **not** establish upgrades/downgrades, refunds/revocation,
every account-switch or duplicate-purchase case, or Apple purchase/renewal/
restore acceptance. Studio followed an expired Creator subscription; it is not
upgrade evidence. No refund was requested in the documented Creator cancellation.
Further financial cases require their own authorization and exact provider,
environment, owner, native-delivery and durable-server evidence. Unknown purchase
outcomes require reconciliation, never a blind second purchase.

Apple's native product lookup and completed review screenshots are catalog and
metadata evidence only. Both screenshots are COMPLETE with exact ownership and
checksums, while the inspected API still reports `MISSING_METADATA` without a
specific remaining required field. Names/descriptions, group localization,
monthly prices, USA availability and review notes were present. Business
agreement status and subscription UI warnings remain **unobserved**; the closed
login inspection is not a diagnosed billing or sandbox blocker. It does not
establish a need for another account or a review mutation. See the protected
[metadata findings](../store/.runtime/creator-apple-20261009/subscription-missing-metadata-findings.json)
and [closed UI inspection](../store/.runtime/creator-apple-20261009/business-ui-readonly/result.json).

## Historical Checkpoints

These superseded observations are not current prerequisites or open work:

- **05:46-05:50 UTC:** the read-only checkpoint had no actual Musia purchase,
  restore or renewal evidence; Google plans were DRAFT and Apple review
  screenshots were absent. All predate the evidence above.
- **06:06 UTC:** the configured Google license tester was verified in the
  selected Console list:
  [license check](../store/.runtime/creator-license-testing-20261009/result.json).
- **06:42:37 UTC:** both approved US-only monthly plans became ACTIVE at
  USD9.99/USD29.99 with checkout gates off:
  [activation readback](../store/.runtime/creator-google-catalog/activation-readback.json).
  The later temporary test-gate opening and its 08:21 closure are separate events.
- **07:30 UTC onward:** the readiness lane established the Play installation.
  An initial disabled Subscribe control was a BillingClient ownership-check/
  reconnection problem, not a failed payment. Fresh checks subsequently enabled
  checkout. See the [Play installation](../store/.runtime/creator-play-readiness-20261009/play-installed-readback.json)
  and [connection diagnostic](../store/.runtime/creator-play-readiness-20261009/billing-client-diagnostic.json).

This reconciliation changed documentation only. It did not execute a purchase,
change a checkout gate, alter a store catalog or modify a formal review.
