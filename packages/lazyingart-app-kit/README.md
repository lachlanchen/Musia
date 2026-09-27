# LazyingArt App Kit

An incubating, dependency-free shared application foundation. Node 22+ for the
server adapter; the root contract module also runs in a browser. **Private,
unpublished, not production-enabled.** It does not create another identity
server or replace native SwiftUI/Kotlin applications.

The authoritative account design belongs to Company/EchoMind. This package
implements a client of the EchoMind `fc05a2a6` v1 source candidate: OAuth code +
PKCE + minimal profile, **not OIDC**. No ID tokens, JWKS or guessed issuer URL.

## Implemented

- Strict issuer, client, audience, exact callback and discovery contracts.
- S256 PKCE, random state, browser-session binding, atomic one-use flow hook.
- Server-only code exchange, profile, refresh and app-session revocation.
- Bounded transport: timeout, response size cap, no redirects or automatic retry.
- Refresh coordination with durable-vault hooks and logout race protection.
- Stable `(issuer, subject)` identity; minimal-profile projection.
- Guest/online/offline/reauthentication and per-feature access guidance.
- App adoption manifests and candidate-bound acceptance checklists.
- Synthetic portable fixtures, including failure cases, for other SDK owners.

Not implemented: a deployed account service, database/vault, cookies/CSRF HTTP
handlers, native account UI, account linking/deletion implementation, sync,
payments, credits, job execution, telemetry or store submission automation.

## Run

```sh
npm test --prefix packages/lazyingart-app-kit
node --test tools/tests/lazyingart_app.test.mjs
node tools/check_lazyingart_app.mjs
node tools/check_lazyingart_app.mjs --require-ready
```

The last command intentionally exits **2** for Musia's disabled candidate.
Exit 0 without `--require-ready` means configuration is valid, not login is live.
Exit 1 means invalid input. All doctor operations are offline; no `.env`, cookie,
network or credential discovery occurs. Tests inside this package are independent
of Musia files and can run after copying the package into another checkout.

## Server Integration Contract

Use `src/server.mjs` in a BFF only. Never bundle it into a frontend. Its methods
return credentials to the trusted caller; **do not serialize those results to
the browser or log them**. The native protocol implementation should use the
same fixtures but platform secure storage and a registered public client.

```js
import { createAccountClient, createRefreshCoordinator } from '@lazyingart/app-kit/server';

// Loaded from reviewed server configuration, never from request parameters.
const client = createAccountClient({
  registration, clientSecret: secrets.accountClientSecret, flowStore,
});
const refreshSession = createRefreshCoordinator({ client, vault });
```

This is an interface example, not a working deployment: registration, secrets,
flowStore and vault must be supplied by the app owner. The package is not on npm.
Use a local `file:` dependency during review; agree on an owner/version before
extracting it into a company SDK repository. No install scripts or runtime deps.

### Flow Store

`create(flow)` persists `state`, hashed browser binding, verifier, expiry, exact
issuer/client/audience/redirect and a local return path. Enforce expiry, bounded
per-session/total capacity, uniqueness and encryption/access controls. Never put
this record in a URL, localStorage or client-readable cookie.

`take(state, binding, now)` atomically checks binding + expiry and deletes the
matching record before returning it. Wrong bindings must not consume it. The
record must not reappear after a crash. All workers share this store. The test
memory implementation is **not** suitable for production.

The app must establish a random, server-issued browser-session binding before
beginning sign-in. Protect sign-in initiation against CSRF, and set a host-only,
Secure, HttpOnly cookie with appropriate SameSite and Path for the actual
callback. Do not use a global cookie shared across product subdomains.

Call `begin({ binding, returnTo })` and redirect to the returned authorization
URL. `returnTo` is an app-local path, not an arbitrary absolute redirect.
Call `complete({ binding, callbackUrl })` with the actual registered URL and
request query; do not reconstruct an origin from untrusted forwarded headers.
On `authenticated`, map the subject explicitly and issue a rotated opaque app
session. On `cancelled`, restore the draft/return path. On error, preserve drafts
and offer a fresh authorization attempt. Strip callback queries from history;
use `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, no analytics or
third-party content on callback routes. Never reuse a consumed code.

### Refresh Vault

The coordinator coalesces concurrent refreshes **in one process**. The durable
vault is responsible for correctness across workers/restarts:

1. `claimRefresh(sessionId)` transactionally changes active -> refreshing,
   removes the usable old credential and returns `{ lease, refreshToken }`.
   A live lease held by another worker returns `{ status: 'busy' }`. An expired
   lease/crash or an invalid session returns null: require a new sign-in, never
   put the old token back into service.
2. `commitRefresh(sessionId, lease, tokens)` atomically stores the rotated tokens
   and their received-at/expiry, marks active, and returns true only for the
   still-current lease. Logout, deletion or revocation invalidates that lease.
3. `requireSignIn(sessionId, lease)` compare-and-sets the affected refresh
   operation to reauth_required without overwriting a newer login or logout.
   Preserve drafts. An ambiguous persistence result must fail closed; retain
   an operation ID so storage reconciliation cannot revive a revoked token.

Never run raw `client.refresh()` on each web request. Use the coordinator/vault
with bounded foreground refresh, expiry skew and a per-session lock. A busy
result means retry reading app session state after a bounded delay, not send the
old credential again. A lost response requires a fresh code/PKCE login, often
reusing the central browser SSO session. There is no rotation grace window.

Revalidate profile when needed for foreground/revocation. A 403 is not evidence
that an email/password is wrong; product entitlements are separate. App signout
revokes its own family and clears only its app session. Global signout is a
separately labeled, recently authenticated central account action.

## Boundaries

- Pinned configuration is trusted operator input. This is not arbitrary-host
  discovery or an SSRF-safe proxy; never take issuer/endpoints from a user.
- Provider verification is the central owner's job. Discovery false means no
  corresponding provider button. Provider passwords/tokens never cross apps.
- `featureDecision` is **UI guidance**, not authorization. Backends must enforce
  current entitlement, ownership, purchase, budget, consent and rate limits.
- No shared database joins by email. Wallet proof, credit history, private
  papers, songs and purchases are not shared just because identity is shared.
- The readiness checker validates declared receipts, not their truth or freshness.
  `readyForOwnerReview` never means permission to deploy; recheck live on the
  exact candidate. Evidence contains references, never tokens or private logs.
- Register independent clients for web/iOS/Android/Mac. Native v1 requires
  verified HTTPS universal/app links; custom schemes/loopback are not supported
  by the inspected EchoMind server. Use system auth sessions, not embedded login.

See [framework and rollout](../../docs/lazyingart-app-framework.md) for ownership,
preserved legacy identities, release gates and the modules beyond accounts.
