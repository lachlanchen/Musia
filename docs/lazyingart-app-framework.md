# LazyingArt App Framework

Date: 2026-09-27. Status: **candidate foundation, not deployed shared login**.

## Decision

Unify application contracts and infrastructure, not all products into one app or
one database. A person should be able to use one LazyingArt identity, resume
their work, and understand consistent account/access states across our apps.
Native iOS remains SwiftUI/AVFoundation; Android remains Kotlin/Compose/Media3.
The public learning API must not expose Musia Studio workers or filesystem tools.

The canonical policy is Company's
`playbooks/unified-lazyingart-account-v1.md`. EchoMind's active source checkout
owns its implementation. Do not start a competing auth server or silently adopt
the older EchoMind checkout. General signup needs no invitation; access to the
EchoMind product is a separate entitlement.

## What Was Inspected

| Source snapshot | Lessons and ownership |
| --- | --- |
| Bunko `826f304f` | Optional login, private draft persistence, native secure sessions, release receipts. Build 1.0.6 (8) remains in its existing review flow. |
| OnlyIdeasApp `cf592710` | GitHub/native exchange, paper/job privacy, explicit public publishing. Keep `github-<numeric id>` ownership while adding proven mappings. |
| EchoMind formal-current `fc05a2a6` | Central code/PKCE account candidate and invitation split. Source/mocked tests are not live provider verification. |
| LazyArtCoin `41f6ebc3` plus active owner changes | Preserve `echomind:<id>`, wallet signatures and ledger history. The owner is adding Python account/link adapters; do not overwrite them. |
| Musia `5ff9fc60` plus existing creative edits | Native learning app, public read-only API, local progress and drafts, separate Studio. No accounts in the submitted candidate. |

The Bunko user handoff reports iOS/Mac Waiting for Review, Play changes in
review and automatic release. This framework task did not recheck store consoles
or alter submissions. Handoff delivery to 31 workspaces does not mean adapters
or shared login are deployed.

## Layers

```text
Native SwiftUI / Kotlin + each app's web UI
                 |
      app-owned backend and local session
                 |
 LazyingArt App Kit: contracts, protocol adapter, acceptance checks
                 |
 EchoMind-owned central account service: identity and browser SSO

Separate app-owned boundaries:
  entitlements / store purchases / credits / private data / jobs / publishing
```

| Module | This change | Next owner milestone |
| --- | --- | --- |
| Accounts | Node server client, validators, synthetic conformance tests | Register real clients, durable app sessions, native adapters, live callbacks |
| Capabilities | Shared versioned app manifest and guest/access UI decisions | Per-app server enforcement and actual service discovery |
| Session recovery | Bound return paths, single-flight refresh and atomic vault hooks | Encrypted persistent vault and integration/restart/race tests |
| Private sync | Boundary and consent contract only | Subject-scoped app data, conflict handling, export/deletion and explicit sync |
| Jobs and AI | Boundary only; no remote execution | App-specific budgets, quotes, confirmation, resumable status, cancellation |
| Credits and wallet | Explicitly separate from identity | Coin owner provides versioned nullable credit/access response; no auto-debit |
| Release operations | Candidate/client-bound acceptance checklist and CI | Each owner's signing, screenshots, privacy, reviewer and release evidence |
| Design conventions | Guest-first, profile, separate signout, preserved tasks | Native app-specific components; no universal UI shell |

Don't equate EchoMind usage credits with an Ethereum LAC balance. No shared
purchase, subscription, budget or wallet authority follows from signing in.
Future spending must be app/audience scoped, integer-unit, idempotent and
explicitly authorized with reserve/commit/release semantics before execution.

## Included Files

- `packages/lazyingart-app-kit/`: portable contracts, Node server adapter and tests.
- `apps/shared/lazyingart-app.json`: Musia adoption manifest, disabled by default.
- `tools/check_lazyingart_app.mjs`: offline checklist validator, no secret loading.
- `tools/tests/lazyingart_app.test.mjs`: Musia guest-mode/configuration tests.
- `tests/test_lazyingart_adoption.py`: checks that the current API remains read-only
  and agrees with the adoption manifest; not an account integration test.
- `.github/workflows/app-kit.yml`: source-only contract CI, no deployment rights.

No production routes, Caddy configuration, app binaries, databases, DNS, release
versions or live sessions are modified. No npm package is published. No provider
credentials or unknown client IDs are inferred from neighboring `.env` files.

## Central Protocol Compatibility

The inspected source is a custom OAuth code + minimal profile service, not an
OIDC issuer. Pin its actual deployed HTTPS origin, separate client and audience,
and exact registered HTTPS redirect. Native clients need associated domains/app
links; v1 does not accept loopback/custom-scheme redirects.

| Operation | Candidate route |
| --- | --- |
| Discovery | `GET /.well-known/lazyingart-account` |
| Authorization/consent | `GET/POST /account/authorize` |
| Exchange/refresh | `POST /account/token` |
| Minimal identity | `POST /account/profile` |
| App family revocation | `POST /account/revoke` |

Codes are one-use, 90 seconds; access credentials at most 600 seconds; refresh
families have a 30-day absolute lifetime. These are inspected source behavior,
not promises about an undeployed issuer. Revalidate on upgrades.

The app owns a secure session-bound PKCE attempt. Return parameters are `code`,
`state`, `iss` or cancellation `error=access_denied`. Secret fields only cross
the server TLS boundary. The stable identity is `(issuer, subject)`; minimal
profile contains `subject`, `display_name`, `client_id`, `account_status`.

No authorization or refresh exchange is blindly retried. Rotating refresh
credentials must be claimed transactionally before dispatch. Lost responses and
crashed claims require a fresh code/PKCE login, with drafts preserved. This
package requires the app's persistent vault rather than pretending in-memory
locks provide crash/multiple-worker safety.

This follows the redirect/PKCE and token-protection guidance in
[OAuth security BCP, RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html).
Native authorization should use the system browser/auth session rather than an
embedded login UI, following
[OAuth for native apps, RFC 8252](https://www.rfc-editor.org/rfc/rfc8252.html).

## App Adoption

### Musia

Keep library, playback, guitar lessons and local practice usable without an
account. Later, sign in at private-sync or a clearly offered cloud capability.
No user audio upload, model spending or public publishing is implied by login.
The current public learning service remains read-only and unchanged. Its Caddy
allowlist does not suddenly admit `/account/*` or Studio endpoints.

### Bunko and OnlyIdeas

The Node protocol adapter is reusable by their BFFs after owner review. Preserve
working GitHub login and local user IDs until proof-backed linking exists.
Cross-app identity must never publish private reading notes, papers or chats.
Non-GitHub commenting requires a separately reviewed server posting/moderation
implementation; it is not accomplished by adding a login button.

### EchoMind and LazyArtCoin

The active EchoMind owner owns central migration and access enforcement. Keep
ordinary account signup independent of EchoMind invitation redemption. Coin's
owner owns its Python implementation, legacy owner mapping and wallet proof.
Share fixtures/acceptance criteria instead of imposing Node on Python services.

Coin must distinguish unavailable credits from a numeric zero, and distinguish
valid global identity without EchoMind access from invalid credentials. No
automatic wallet/account merging, token conversion or ledger rewrite.

### Other Apps

Add one versioned manifest and independent client per platform, then use these
fixtures and checklist. Reuse native platform patterns; do not force every app
to run JavaScript or use the same database. App owners retain release authority.

## Rollout and Proof

1. EchoMind owner deploys the reviewed migration/issuer and supplies real
   discovery, client registration and provider callback evidence.
2. Each app registers exact web/native redirects and audience; the app owner
   implements a durable flow store, secure local session, CSRF and revocation.
3. Implement dual-proof legacy linking, ownership isolation, deletion/retention
   and recovery. Do not merge on matching email or force old sessions out.
4. Run positive and negative callbacks, timeout/refresh replay, restart, offline,
   cancellation, signout and draft restoration on exact web and native candidates.
5. Complete provider-specific and entitlement-specific checks; update privacy
   and reviewer notes. Independently prove purchases and credits are unchanged.
6. Enable one app/platform at a time after owner review, retaining the old route
   and explicit rollback. A disabled switch alone does not revoke existing
   sessions; central revocation and local-session cleanup need their own plan.

Acceptance receipts use a key `JSON.stringify([issuer, clientId])` under
`clients`, with `candidate`, `platform`, `audience`, `redirectUri`, `verifiedAt`
and boolean `checks` named in `ACCEPTANCE_GATES`. Include private evidence paths
in the owner release record, not credentials. The doctor validates declared
checks; it neither authenticates their evidence nor authorizes release.

## Verification Commands

```sh
npm test --prefix packages/lazyingart-app-kit
node --test tools/tests/lazyingart_app.test.mjs
node tools/check_lazyingart_app.mjs
PYTHONNOUSERSITE=1 conda run --no-capture-output -n musia python -m unittest discover -s tests -p 'test_learning_api.py'
PYTHONNOUSERSITE=1 conda run --no-capture-output -n musia python -m unittest discover -s tests -p 'test_lazyingart_adoption.py'
```

These are local source checks, not live provider, store or device acceptance.
No device, desktop, tunnel or heavy job is needed for this foundation work.

Verified on 2026-09-27: 52 Node contract/adoption tests, 29 existing learning API
tests and 1 new API/adoption guard passed. The Python run reports an existing
Starlette/httpx deprecation warning; it is not a failed test and dependencies
were not changed here. The offline doctor reports valid configuration, login
disabled, no registered clients, and no live verification.
