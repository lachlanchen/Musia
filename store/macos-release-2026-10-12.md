# Musia Mac Release - October 12, 2026

## Approved Release

The owner requested: "Musia mac passed review post process all".
Fresh Apple API inventory confirmed the exact approved platform, version and
build before release. One manual release request was submitted and accepted
at **2026-10-11 22:43:17 UTC / October 12 06:43:17 Hong Kong**.

| Field | Verified value |
| --- | --- |
| App | Musia: Learn Music & Guitar |
| App ID / bundle | `6816265930` / `art.lazying.musia` |
| Platform | `MAC_OS` |
| Version / build | `0.1.2 (4)`, `VALID` |
| Version ID | `252606cc-493d-4385-b901-dd4cf7f659f0` |
| Build ID | `1d5a2c57-de54-4120-a219-5a4b158265f5` |
| Before | `PENDING_DEVELOPER_RELEASE`, `MANUAL` |
| After accepted release | `READY_FOR_SALE` |
| Compatibility | macOS 14+, Apple silicon and Intel |
| Package SHA-256 | `8b851ea56603eec7d50f84584a8175ec3b29abcdc2fd7d41df34b23ce2187807` |

The exact previously reviewed binary was released; no build, re-signing,
replacement attachment, new legal declaration or pricing change was made.
See [October 6 qualification/resubmission](apple-resubmission-2026-10-06.md).
This release does not include later beta-only changes.

## Public Availability

- [Mac App Store listing](https://apps.apple.com/app/id6816265930?mt=12).
- The public US page is **HTTP 200** after a short propagation delay. Its
  SoftwareApplication JSON-LD independently confirms Musia: Learn Music & Guitar,
  LazyingArt LLC, Mac, macOS 14.0+, and **USD 2.99**. Regional prices vary.
- Initial listing was HTTP 404; the separate US/HK iTunes lookup API still
  returned zero results when the page became available. Do not mistake that
  cache lag for a failed release. Version/build are verified through Apple's
  authenticated API; a fresh public purchase/install was not performed.
- Apple says a manually released version can take up to 24 hours to appear.
  [Apple release guidance](https://developer.apple.com/help/app-store-connect/manage-your-apps-availability/select-an-app-store-version-release-option).
- Do not resubmit or repeat the release request to resolve propagation.

## Preserved State

- iOS `0.1.2 (4)` remains `WAITING_FOR_REVIEW`; formal version
  `f4337c74-f5d9-4613-879c-df5fb3712e9e`, build
  `7b0ae745-7e3b-44ab-9100-1de68e99cfc7` unchanged.
- Google production `0.1.2 (3)` was already published on October 10; no Google
  mutation or fresh Google status check was part of this Mac release.
- TestFlight, internal testing, account integrations, creator pilot and disabled
  paid checkout were not changed. No new invitation was sent.

## Evidence And Follow-through

Private provider evidence is under
`store/.runtime/formal/mac-release-20261012/`: `before.json`, `preflight.json`,
the one-shot `release-request.json`, `after.json` and `public-lookup.json`.
Never commit the raw provider payloads or signing credentials.

The formal release used Apple's documented
`POST /v1/appStoreVersionReleaseRequests`, with an exact app/platform/version/
build preflight and an owner-only journal written before dispatch. The beta
helper's formal-mutation prohibition remains unchanged. An unknown response
must be reconciled before any retry.

README, store status and web download links are updated separately from the
native binary. Web deployment and final storefront evidence are recorded below
after verification.
