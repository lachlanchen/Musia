# Creator Native Contract

Implementation contract, 2026-10-09. Server origin `https://musia.lazying.art`.
All endpoints are below `/creator`. JSON requests; errors are `{detail: code}`.
Authenticated native requests use `Authorization: Bearer <opaque app session>`.
Writes use `Content-Type: application/json` and `X-Musia-Request: 1`. Native
start/exchange need no existing session; these and bearer-authenticated writes
may omit Origin. Never embed confidential issuer/provider keys.

## Current Qualification

- The live invitation-gated pilot uses registered `musia-server` shared password
  sign-in at `https://musia.lazying.art/creator/`. Apple, Google and GitHub are
  centrally unavailable. Active creator app/relay release:
  `4c61355dc154f7fe3afa51d2db72c3af889018c64bf11e2b76369bb30074110c`.
  The edge remains on `421bd8c4...` with identical guard/policy bytes; exact
  component hashes are in [deployment status](creator-deployment.md).
- Real native PKCE protocol roundtrips passed for `apple` and `android`, including
  one-use exchange, replay rejection and logout. Android native Chrome Custom
  Tabs sign-in returned the account successfully. Keystore-backed account state
  and My Songs survived force-stop/relaunch. Private native Media3 reported
  `PLAYING` at 9008 ms; sign-out cleared private playback. Android native UI and
  library/Stage regression passed against the signed QA APK bound to the exact
  0.2.0 (6) AAB. That build is **available to internal testers**, with the one
  existing owner tester verified. No Play installation, physical-device listening,
  audible emulator output or purchase is proven.
  [Exact artifact and delivery evidence](../store/creator-android-20261009.md).
- SwiftUI and Compose creator/account/billing clients exist. Apple iOS/macOS
  0.2.0 (7) artifacts are signed and validated, **not uploaded**. The universal
  Mac PKG passed Apple revalidation; upload never started because the KVM Python
  runtime lacks PyJWT, with repair underway before upload. Actual iOS 27 testing
  on the owned Mac mini simulator is progressing, not yet a passed qualification.
  KVM-hosted isolated macOS debug QA passed Keychain, capabilities, library and minimized
  playback checks, but is not production-ID or signed-in creator-flow proof.
  Apple native UI sign-in and app-specific product lookup remain unverified.
  [Apple evidence and limits](../store/creator-apple-20261009.md).
- A real synthetic user completed live registration, login, consent, invitation
  and terms, a `deepseek-v4-pro` draft, a 90-second ACE XL Turbo render, large-v3
  cross-window ASR and actual `gpt-audio-1.5` audio review. Approval used 18
  corrected timed lines; private browser playback passed. Native creation is
  not established by that browser journey; Android private player-state evidence
  is recorded separately above.
- Live social QA passed private/pending guest denial, approved public range
  playback, likes/saves, comment moderation/deletion, report resolution and
  unsharing. The temporary public synthetic QA song was returned to private.
- Apple/Google draft products match the US$9.99/US$29.99 targets. App-specific
  test verification and restore configuration is connected, with key paths
  validated; sales and test checkout are both off. No real Musia sandbox
  purchase has passed. This is not a public paid service.

Main learning release
`9dd15fbe0e9677284c2e94deecb763bc350f50bad6f98425e6ede0124e0eac08`
was accepted in transaction `20261009T134643`. The public Creator CTA links to
`/creator/`, with HTTP 200 verified, and the October 9 disclosures continue at
<https://musia.lazying.art/privacy>. This is separate from the creator release.

## Native Sign-In

1. Generate a cryptographically random 32-byte base64url PKCE verifier. Keep
   verifier/attempt together in protected native storage while authorizing.
2. POST `/auth/native/start` with `{challenge: BASE64URL(SHA256(verifier)),
   platform: "apple" | "android"}`. Response: `{attempt, url, expiresIn: 600}`.
3. Open returned HTTPS `url` in ASWebAuthenticationSession or Android Custom Tabs,
   never a WebView. The registered HTTPS callback returns an HTTP 200 HTML bridge
   for native completion, ending the issuer's form redirect chain. Same-origin
   `/creator/native-return.js` checks the scheme/host, clears callback query data
   from browser history and opens `art.lazying.musia://auth`; a visible return
   link is the fallback. A direct custom-scheme redirect is blocked by the
   issuer's form-action CSP. The custom URL carries only `attempt` and one-use
   `code`, never a session token or central credential.
4. Validate exact scheme/host and matching attempt. POST `/auth/native/exchange`
   with `{attempt, code, verifier, platform}`. Response `{token, expiresIn}`.
   Reject expired attempts, duplicate/malformed parameters and mismatched platform
   or PKCE. A successful exchange consumes the code and rotates the app session.
   Store token in Keychain/Android Keystore-encrypted storage, not preferences.
5. GET `/api/me`, fresh issuer introspection on server. Capture account identity
   and generation counter before async work; discard late results after logout.
6. POST `/auth/logout` with `{}` revokes the local session and attempts central
   revocation; durable pending central revocations are retried by maintenance.
   DELETE `/api/me` with `{}` deletes the creator account after explicit
   confirmation. Media access closes immediately; owned job files are purged
   after the active worker releases its lock. This does not delete the central
   LazyingArt account or cancel a store subscription.

No account is needed for the existing music library, lessons or public community
reads. Attributed social writes and private content require an account.

Source: `musia/creator/api.py`, `musia/creator/native_auth.py`,
`apps/web/creator/native-return.js`, Swift `CreatorAuthentication.swift`, and
Android `CreatorViewModel.kt` / `CreatorVault.kt`. Apple uses the data-protection
Keychain with device-only unlocked accessibility; Android stores ciphertext
protected by an Android Keystore AES key. Source implementation is not a
replacement for real native UI qualification.

## Creator API

GET `/api/capabilities`: login/generation/agent booleans, providers map, plans,
termsVersion, invitationRequired, salesEnabled. Never infer provider readiness.
Current provider status is password=true, Apple/Google/GitHub=false; generation
still requires account gates and manual input/output approval. The bounded
generation service is active under stable run ID `creator-pilot-20261009`, with
a persistent 10-dispatch budget that restarts do not replenish. It invokes the
one-shot worker through the checkout-backed CLI in `musia`. Maintenance and
billing-reconciliation units run from the immutable creator release; maintenance
succeeds during idle supervisor polling. The ingress relay is a separate service.

GET `/api/me`: `{account: {id,name,termsAccepted,invited,usage:{tier,period,limit,used,remaining,source}} | null}`.
POST `/api/terms` `{}`. POST `/api/invitations/redeem` `{code}`.

POST `/api/agent` `{message, brief?}` -> `{message, brief}`. Editable brief:
`{title,idea,lyrics,caption,language:"en"|"zh"|"ja"|"mixed",duration:30..180,
bpm:40..200,key:"C major"}`. Empty draft title/lyrics/caption allowed only for
agent requests; actual render requires all three. Never auto-render an agent reply.

POST `/api/jobs`, `Idempotency-Key` persisted before sending, body
`{brief,rights_confirmed:true,visibility:"private"|"public"}`. Reuse exact key/body
on unknown response, bound to original owner. GET `/api/jobs` -> `{jobs:[...]}`;
POST `/api/jobs/{id}/cancel` `{}` only while queued. No background re-render.

GET `/api/songs?mode=public|mine|saved` -> `{songs:[...]}`; GET `/api/songs/{id}`.
Song: `{id,title,language,duration,author:{id,name},mine,visibility,moderation,
lyrics,lyricLines:[{start,end,text,language}],audioUrl,sharePath,liked,saved,likes}`.
Audio URL is an ACL-checked endpoint: private playback must attach native bearer
headers or download to an owner-protected local file (erase at logout).
Public audio remains anonymous. Use existing native AVFoundation/Media3 playback.
Never use planned lyrics as completed audio's transcript.

POST `/api/songs/{id}/reactions/like|save` `{active:true|false}`.
POST `/api/songs/{id}/visibility` `{visibility}`. Public sharing enters moderation.
GET `/api/songs/{id}/comments` -> `{comments:[{id,text,author,state,mine}]}`;
comment `author` is a display-name string, unlike a song's author object.
POST to the same path with `{text}` -> `{id,state:"pending"}`.
DELETE `/api/comments/{id}` `{}`. POST `/api/songs/{id}/reports` `{reason}`.
POST `/api/accounts/{id}/block` `{active}`.
GET `/api/blocks` -> `{accounts:[{id,name}]}`.

## Subscriptions

GET `/api/billing`: `{accountToken, products:[{tier,appleProductId,googleProductId,
googleBasePlanId}], entitlement:{tier,state,expiresAt,provider,environment},
capabilities:{apple:{purchase,restore,reason},google:{purchase,restore,reason}}}`.
`expiresAt` is Unix epoch seconds or null, not an ISO date string.
Catalog remains visible when purchase disabled. Display localized store Product
prices, billing period and auto-renewal terms; never hardcode a checkout price.
Approved targets and current draft-product prices: Creator US$9.99/month for 20
renders; Studio US$29.99/month for 80; Free allows 2 renders per UTC month.
Both global `salesEnabled` and per-account provider purchase capability must
permit a new purchase. Connected test verification/restore is not checkout
permission; both sales and test checkout remain disabled.

Apple IDs: `art.lazying.musia.creator.monthly`, `art.lazying.musia.studio.monthly`.
Google IDs: `musia_creator`, `musia_studio`, base plan `monthly`.
Apple `appAccountToken` = server accountToken UUID. Google obfuscated account ID
= server accountToken UUID, no email. Server verifies immutable binding.

POST `/api/billing/verify` `{provider:"apple"|"google",reference}` where Apple
reference is transactionID and Google is purchaseToken. Server fetches provider
truth; never accept client tier, price, environment or expiry. StoreKit finishes
only after `verified:true`. The server durably binds delivery before Google
acknowledgement and returns success after acknowledgement; native code must not
bypass that ordering. Preserve unknown outcomes for restore, never buy twice.
GET `/api/billing` refreshes entitlement presentation.
POST `/api/billing/restore` `{}` reconciles known backend records. Apple also
submits current verified StoreKit entitlements; Google queries owned purchases.
Explicit missing-purchase sync is separate from ordinary restore.

Restore/manage remain independent of new sales, subject to provider capability
and original-account checks. Account switch must not deliver a purchase to the
new account. Apple/Google verifiers and scheduled reconciliation are implemented.
An Apple Server API sandbox invalid-reference response `4000006` demonstrated
HTTP authentication only, not a purchase, entitlement, restore or renewal.
Real app-specific sandbox transaction and lifecycle acceptance remain open.

## Native Scope

Create, Community and account/billing use SwiftUI/Compose native controls. Keep
existing playback, multilingual lyrics, practice, icon and Settings/History
intact. Use no WebView.
No native debug backend bypass in release. Preserve current formal reviews and
Google production 3 (0.1.2), held under managed publishing. Android 0.2.0 (6) is
already delivered for internal testing; Apple 0.2.0 (7) remains unuploaded.
Internal distribution does not qualify the new surface for production.

Remaining qualification includes Android Play-installed execution and audible
output, Apple native UI sign-in/private playback, remaining cold/warm return
and account-switch/expiry cases, the complete native creation journey, and real
Musia sandbox purchases, restore, renewal, cancellation and refund/revocation.
The passed exact-build Android UI/library and sign-out checks do not close these
other gates. Keep sales and test checkout disabled; do not reupload internal 6
or treat its availability as a public paid creator launch.
