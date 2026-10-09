# Scoped Creator Deployment

2026-10-09. The invitation-gated creator pilot is live at
<https://musia.lazying.art/creator/>. It is **not a public paid service**.

## Active Releases

| Component | Active release or execution source |
| --- | --- |
| Creator app and workstation relay | `4c61355dc154f7fe3afa51d2db72c3af889018c64bf11e2b76369bb30074110c` |
| Maintenance and billing-reconciliation units | Same immutable `4c61355...` release, including `tools/creator.py` |
| Edge guard | `421bd8c4bd8ba3d880e952efa18b2404415e4a6073c7e8529839c0a17a76d1bd` |
| Generation CLI/service | Source checkout, existing `musia` conda environment |
| Main learning app | `9dd15fbe0e9677284c2e94deecb763bc350f50bad6f98425e6ede0124e0eac08`, accepted transaction `20261009T134643` |

The app and relay are active on the new release; the edge intentionally remains
on the previous one. The guard and routing policy are byte-identical in both
release trees:

| File | SHA-256 in both releases |
| --- | --- |
| `deploy/creator/gateway.mjs` | `0362dc18bb5edd8fb25bfdcb2e6a1964c51180fcbd7b3d8f428845d9f0098ffc` |
| `deploy/creator/policy.json` | `714477c4883f37a9ddfd690915c6ef2f5aef5696d03689c8feef796c10f805cd` |

The LazyEdge adapter, pin and ASGI transport wrapper also match byte-for-byte.
These file hashes are distinct from the release manifest digest and transfer
archive checksum; none identifies the concurrently edited checkout as immutable.

## Current Status And Limits

- Shared password sign-in is live with the registered `musia-server` callback
  `https://musia.lazying.art/creator/auth/callback`. Apple, Google and GitHub are
  centrally unavailable; registration does not enable those providers.
- A real synthetic-user registration/login/consent/invitation/terms journey
  passed, followed by a `deepseek-v4-pro` draft, a 90-second ACE XL Turbo render,
  large-v3 cross-window ASR and an actual `gpt-audio-1.5` audio review. The result
  was approved with 18 corrected timed lines; private browser playback passed.
- Social QA in `store/.runtime/creator-social-qa.json` passed private guest 404,
  public-pending guest 404, approved public range audio 206, likes/saves,
  comment moderation/deletion, report resolution and unshare guest 404. The
  temporary public synthetic QA song was returned to private.
- Real native PKCE protocol roundtrips passed for both platform values, with
  one-use exchange, replay rejection and logout. Android Chrome Custom Tabs UI
  sign-in returned the account; Keystore-backed state and My Songs survived
  force-stop/relaunch. Private native Media3 reported `PLAYING` at 9008 ms and
  sign-out cleared private playback. Native UI and library/Stage regression
  passed for the exact signed Android 0.2.0 (6) artifact, now available internally
  with the existing owner-only tester verified. Play installation and audible
  output are not proven. [Android delivery](../store/creator-android-20261009.md).
- Apple iOS/macOS 0.2.0 (7) artifacts are signed and validated, not uploaded.
  The signed universal Mac PKG passed Apple revalidation, but upload never
  started: KVM `/usr/bin/python3` lacks PyJWT. The parent is fixing that runtime
  before upload. This is a local prerequisite failure, not an accepted upload
  or an Apple rejection. Actual iOS 27 testing on the owned Mac mini simulator
  is progressing; qualification results remain pending.
  KVM macOS isolated debug QA passed Keychain, capabilities, library and minimized
  playback; it is not production-ID, signed-in creator UI or StoreKit proof.
  Apple native UI sign-in remains unverified. Existing formal reviews and
  Google production 3 (0.1.2), held under managed publishing, are preserved.
- Apple/Google products are drafts at exact US$9.99/US$29.99 monthly targets.
  App-specific test verification and restore configuration is connected, with
  key paths validated; reconciliation is implemented. Sales and test checkout
  are both off. Apple Server API sandbox invalid-reference response `4000006`
  proves HTTP authentication only, not a purchase. No real Musia sandbox
  purchase has passed.
- Maintenance and billing-reconciliation timers are active and their units run
  from the immutable app release. Maintenance succeeds during idle queue polling.
- `musia-creator-generation.service` is active with stable run ID
  `creator-pilot-20261009`, a persistent 10-dispatch budget and no automatic
  budget renewal on restart. Input and output approvals remain manual. It calls
  the one-shot GPU worker through the checkout-backed CLI in `musia`.
  The service named `worker` below is an ingress relay, not this generation queue.

This acceptance does not establish every ingress failure mode, store lifecycle,
reboot or rollback gate below. Full native limits are in
[the native contract](creator-native-contract.md).

### Main Learning And Privacy

The accepted `20261009T134643` learning transaction includes the invitation-only
Creator CTA linking to `/creator/`. The public main page and creator destination
returned HTTP 200; local brief editing/export remains unchanged. The October 9
account, AI-processing, storage, subscription and deletion disclosures continue
at <https://musia.lazying.art/privacy>, also HTTP 200. This learning release
supersedes the earlier privacy-only deployment.

Public acceptance passed for the 31-song catalog. Deployment evidence retains
restart, peer-host and firewall-preservation checks and the preserved creator
fragment. Private receipts are under
`deploy/learning/.work/20261009T134643-9dd15fbe0e96/`.
`scripts/deploy_musia_learning.py` now defaults to the shared OneTimeSync
LazyTunnel credential location; credential values and private identities stay
outside this document.

## Boundary and credentials

```text
HTTPS musia.lazying.art /creator or /creator/*
  existing shared Caddy (existing TLS, ports and firewall)
  -> edge guard                 127.0.0.1:18896  [edge host]
  -> SSH reverse listener      127.0.0.1:18897  [edge host]
  -> worker guard              127.0.0.1:18898  [workstation]
  -> ASGI transport wrapper    127.0.0.1:8797   [workstation]
  -> musia.creator.api          origin https://musia.lazying.art
```

The learning API stays at `127.0.0.1:18440`; its routes are not published through
the creator guards. Nothing exposes Studio, a job worker,
management, model names, arbitrary upstreams, or filesystem paths.

| Boundary | Credential handling |
| --- | --- |
| Client → Caddy | Native `Authorization: Bearer …` is an application session; browser sessions use creator cookies. Public reads and login need neither. |
| Caddy → edge | Caddy overwrites `X-Musia-Client-Authorization` from the incoming Authorization, then removes raw Authorization. It overwrites `X-Musia-Ingress-IP` from the direct TCP peer, strips relay headers, and sets the exact origin Host. |
| Edge → worker | Edge injects only the private relay capability in `X-LazyEdge-Relay-Authorization`. The native bearer remains in the dedicated header. |
| Worker → app wrapper | Worker validates relay first, removes it, then injects its distinct upstream capability as Authorization. |
| Wrapper → creator API | Wrapper requires the upstream capability and IPv4 loopback peer, consumes transport headers, restores only the dedicated native session as Authorization, and asserts HTTPS after validation. |

The edge never receives the upstream secret. The application never receives the
relay secret. The application handler never receives either transport credential.
The relay and upstream files must contain different, independent random tokens
of at least 32 characters. Neither one is a native session token. The SSH private
key is a fourth authority; restrict its use to the tunnel service. Credential
isolation depends on installed file ownership and service identities, not just
the role names in the templates.

Deploy the application using `deploy.creator.upstream:create_app --factory`,
not the bare creator API factory. This wrapper is necessary for the transport
contract and wraps the existing app without modifying it. Keep Uvicorn
proxy-header trust disabled and its access log disabled. The wrapper preserves
HTTPS redirects for `/creator` → `/creator/`.

Cookie and Set-Cookie forwarding is enabled only after a creator allowlist match.
`Origin`, `X-Musia-Request`, `Range`, `Content-Type`, and `Idempotency-Key` survive
sanitization. Forwarding, hop-by-hop, method-override and transport headers are
removed. Native credentials are never returned in response headers. Application
session validity, revocation, owner checks, CSRF, invitations and purchase checks
remain the API's responsibility; the gateway does not turn login into permission
to generate or subscribe.

## Reviewed runtime and policy

The adapter reuses the shared LazyEdge **0.4.0** `src/proxy.js` and
`src/security.js` APIs. `lazyedge-pin.json` pins SHA-256 for those files and
`package.json`; `lazyedge.mjs` verifies all three before importing anything.
No LazyEdge source or package was modified. These source-module paths are pinned
because `proxyHttpRequest` is not exported from that version's package root.
Any LazyEdge upgrade requires a reviewed pin update and a full ingress test run.

Set `MUSIA_LAZYEDGE_ROOT` to the existing verified installation for local testing,
or a verified immutable release directory for deployment. Do not select an
unpinned `npx`, overwrite a live installation, or install another local runtime.
The Node runtime must be an explicit existing Node 20+ executable available to
the service account; a login shell's NVM configuration is not a service runtime.

`deploy/creator/policy.json` is the non-secret shared routing manifest. Its
allowlist mirrors `musia/creator/api.py`; a test detects backend route drift.
IDs use the API store's exact `uuid.uuid4().hex` format: 32 lowercase hexadecimal
characters. Hyphenated UUID strings, uppercase IDs, arbitrary slugs and unknown
dynamic suffixes are denied. Only `like` and `save` are reaction kinds. GET/HEAD
are both allowed for song audio; other HEAD, OPTIONS, PUT, PATCH, CONNECT, TRACE,
unknown methods, undeclared routes and management endpoints are denied. The
existing `/creator` redirect is the one extra framework-owned route.

Each guard enforces 48,000-byte bodies (including chunked bodies), 32 in-flight
requests, a 150-second absolute request deadline, and LazyEdge's bounded idle
proxy timeout and disconnect cleanup. Requests exceeding a limit are rejected;
active streams are closed at their deadline. The fixed 60-second per-IP window
allows 240 general requests and 20 authentication requests; auth consumes both
budgets. State is bounded to 8,192 IPs and fails closed if full. The worker repeats
the limits using the relay-authenticated ingress IP. Limits reset on restart;
account-level durable limits remain in the app. Caddy must be the direct trusted
ingress: adding a CDN or another proxy needs a fresh IP attribution review.

## Immutable releases and templates

Use a new digest-named release directory for every reviewed revision.
`tools/creator_release.py` stages workstation application/guard releases under
`~/.local/share/musia/creator-releases/<release-digest>/`, checks the pinned
LazyEdge files and records a per-file manifest. Its release digest is derived
from that manifest, not from a Git commit. It writes private unit/configuration
artifacts under `~/.config/musia/creator-runtime/` and keeps service data under
`~/.local/share/musia/creator-live/`. It stages but does not cut over ingress.

The system-service templates also describe an `/etc/musia-creator/` credential
layout and an operator-selected immutable guard release, for example
`/srv/musia-creator/releases/<release-digest>/`. Those templates are not a claim
that the staged user units use `LoadCredential` or the same paths. Keep secrets,
auth SDK configuration and SQLite data outside release trees. Retain the current
and immediately previous reproducible release and archive SHA-256 values.

The operator must create and inspect the exact transfer archive, record its SHA-256
and file list, hash normalized `policy.json`, and verify transferred contents.
`node deploy/creator/inventory.mjs` checks the pinned modules and prints their
hashes plus a manifest digest (recursively key-sorted compact JSON, array order
preserved, UTF-8 with no trailing newline).
The module pin and release digest are not substitutes for an archive checksum.
The staging tool records an archive SHA-256 separately. Current/previous host
paths, transfer receipts and live Caddy/import hashes belong in the private
deployment handoff, not in this public status summary.

Maintenance and billing units now pin both their working directory and CLI to
the immutable app release. Generation remains an explicit exception: its unit
uses the source checkout's `tools/creator.py supervise`, `Restart=no`, and the
private queue configuration. The stable run ID and persisted budget must survive
service restarts; never create a new run ID merely to reset an exhausted budget.
Idle polling releases the supervisor mutation lock so maintenance can run,
while the separate daemon ownership lock still prevents a second supervisor.

Templates under `deploy/creator/systemd/` contain explicit placeholders:

| Template | Role and review inputs |
| --- | --- |
| `musia-creator-edge.service.in` | Edge; absolute `@NODE@`, `@GUARD_RELEASE@`, `@LAZYEDGE_RELEASE@`. |
| `musia-creator-worker.service.in` | Workstation; same inputs, separate service user. |
| `musia-creator-app.service.in` | Workstation; existing `@CREATOR_PYTHON@`, immutable `@APP_RELEASE@`, `@APP_USER@`, `@APP_GROUP@`, private `@DATA@` and `@AUTH_DIRECTORY@`. Conservative defaults are not the live pilot's acceptance status. |
| `musia-creator-tunnel.service.in` | Workstation; pinned IPv4 `@EDGE_IP@` and `@SSH_PORT@`. Exactly one reverse forward. |

The Python executable should reuse the existing Python 3.11+ creator-server
environment. Do not upgrade or clone the GPU environment. The app release must
include `deploy/creator/upstream.py`. The guard release must include
`gateway.mjs`, `lazyedge.mjs`, `lazyedge-pin.json`, and `policy.json`.

System-service templates use systemd `LoadCredential`. Store each source
credential and role binding as a protected regular, non-symlink file (0600,
root-owned); systemd
provides a private service-owned credential file. Copy the reviewed edge and
worker binding examples to their corresponding role secret directories. Their
`/run/credentials/<unit>/…` paths intentionally match the exact unit names.
The worker and app each receive the same upstream capability, in distinct
service credential mounts. The edge and worker receive the same relay capability.
Create secrets privately without echoing them, passing them in argv, or putting
values in environment files, manifests, logs or handoffs.

The staging tool instead references protected private files and an `app.env`
for the user services. That file can contain the text-provider API key: do not
print, commit or include it in evidence. Keep transport capabilities in their
separate protected files. Do not conflate this implementation with the stronger
credential-mount template; review the actual installed unit and file ownership.

The staging source generates `musia-creator-maintenance.timer` and
`musia-creator-billing-reconcile.timer`, each with a five-minute interval.
Maintenance purges only deleted-owner artifacts after acquiring the worker lock
and retries central sign-out revocations. Billing reconciliation refreshes known
bound purchases from provider truth; it does not initiate a purchase. These
timers are live, but no real Musia sandbox transaction has been accepted.
The generated maintenance services currently reference checkout
`tools/creator.py`, not the immutable application release. Review source changes
accordingly and do not describe every scheduled task as release-pinned.

Validate rendered units with the target host's `systemd-analyze verify` and
confirm all absolute executables and SDK paths are accessible under service
hardening. Promote only verified immutable release paths; switch an optional
`current` symlink atomically after acceptance. Application/guard units use
immutable absolute release paths, so changing a symlink alone does not change
a running service; the checkout-backed maintenance units are noted above.

## Restricted tunnel identity

The `ssh/` templates specify a dedicated remote `musia-creator-tunnel` account
and a separate local tunnel service user. They restrict remote listening to
`127.0.0.1:18897`, disable local forwarding, shell sessions, TTY, X11, agent,
streamlocal and tunnel-device forwarding, and forbid password login. Pin the
edge key out of band in `/etc/musia-creator/tunnel/known_hosts` under the alias
`musia-creator-edge`. Do not use trust-on-first-use or `ssh-keyscan` alone as proof.

OpenSSH's server-side `PermitListen` restricts the remote listening socket. It
does **not** prove which local destination a client chooses for `-R`; `PermitOpen`
controls local forwarding and is not that control. The exact workstation unit,
dedicated noninteractive key owner and restricted credential access own the fixed
`127.0.0.1:18898` target. Both guards still require transport authentication. This
distinction follows the [OpenSSH server configuration reference](https://man.openbsd.org/sshd_config.5).
Validate effective policy with `sshd -T -C user=musia-creator-tunnel,…` before any
operator-authorized account/config change. The templates alone do not attest to
the installed SSH policy.

## Narrow Caddy patch and conservative controller

`caddy_controller.py render` accepts only the exact existing learning managed
block from `deploy/learning/remote.py`, with its existing route list. It preserves
every original byte except for two edits inside that block:

1. Insert `caddy-creator.caddy` before the old 1KB body limit and read/write handlers.
2. Change the old body limit to `request_body @musia_not_creator`, excluding exact
   `/creator` and `/creator/*` while retaining 1KB for every other request.

The creator handler keeps the URI prefix and routes only to `127.0.0.1:18896`.
It does not create a new site block, replace the site, use `handle_path`, change
learning routes or cookies, or alter another host. Caddy sorts directives rather
than blindly using textual order; the exclusion matcher is essential, and the
creator named handle precedes the old named handles. See Caddy's
[directive ordering](https://caddyserver.com/docs/caddyfile/directives) and
[request matchers](https://caddyserver.com/docs/caddyfile/matchers).

The controller does not itself open SSH sessions or hardcode service/firewall
operations; apply/rollback execute the explicit operator-supplied commands.
Render prints the candidate and writes nothing. Apply/rollback require an exact
baseline hash, an existing 0700 transaction directory and explicit absolute
executable argv arrays for validation, reload, acceptance and rollback acceptance.
Commands use no shell and have 45-second limits. Their output is suppressed to
avoid leaking shared configuration. The deployment operator owns concrete probe
scripts and the correct existing Caddy binary/service/admin endpoint.

```bash
# Read-only, on an independently obtained local snapshot (no remote contact):
conda run -n musia python deploy/creator/caddy_controller.py render \
  --config /absolute/private/Caddyfile.snapshot \
  --expected-sha256 <snapshot-sha256>
```

The transaction makes exclusive 0600 backups, validates before replacement,
checks content and file identity immediately before atomic replacement, fsyncs,
reads back, reloads and probes. A failed apply reload/acceptance restores the exact
backup only if the installed file and imports are still owned by that transaction,
then reloads and runs separate baseline acceptance. Explicit rollback also checks
both before/after hashes and ownership. Other writers or changed imports cause
refusal instead of an overwrite. Literal absolute imports are fingerprinted;
wildcard, snippet and nested imports require separate review. Stale transaction
directories are retained for evidence and never automatically reused.

There is no kernel filesystem compare-and-swap across unrelated writers. The
controller serializes its own operations with `.musia-ingress.lock` beside Caddy.
Before applying, the operator must also hold the existing learning controller's
`/var/lib/musia-learning/deployment.lock` and coordinate the shared Caddy owner;
the current `deploy/learning/remote.py:replace_site` preserves the marked creator
fragment and its body-limit exclusion when replacing the learning site block.
That source fix does not replace shared-writer coordination or prove which
controller revision is installed on a host. Do not claim the hash recheck solves
a noncooperating writer race.

The accepted live browser and native protocol paths supersede the old
undeployed-draft status. They do not independently prove every header/path
failure mode. On ingress changes, verify native Authorization becomes the
dedicated header, raw Authorization is absent at the edge, queries survive,
and encoded-path probes cannot bypass the guards.

### Native Callback Bridge

`musia/creator/api.py` ends successful native authorization at the registered
HTTPS callback with an HTTP 200 HTML response, not a direct custom-scheme 303.
This ends the issuer's form redirect chain, whose form-action CSP otherwise
blocks the custom-scheme redirect. The page loads same-origin
`/creator/native-return.js`, which checks the fixed scheme/host, clears the
callback query from browser history and opens `art.lazying.musia://auth`.
A visible return link is the fallback. Only the attempt and one-use code enter
that URL; the native app still validates expiry, attempt and PKCE and exchanges
the code for a session. The ingress allowlist includes the bridge script.
Do not remove that route or replace the bridge with a redirect-only callback.

## Change Acceptance

The following is the checklist for subsequent changes and unrecorded failure
cases, not a statement that the live deployment has yet to begin. Reuse the
existing service/tunnel stack; do not launch a duplicate for documentation work.

Run `bash deploy/creator/preflight.sh edge` or `worker` locally on each host as
appropriate. It is read-only and does not open SSH or acquire privilege. Verify
fresh DNS/TLS, current Caddy/import hashes, learning and all other host responses,
firewall digest/ownership, service PIDs, listener ownership, memory, existing
tunnels and exact release hashes. Do not stop another service to obtain a port.

Stage only after the owner approves the concrete candidate. For an authorized
deployment, sequence the app wrapper, ingress worker, single SSH tunnel and edge
without leaving duplicate stacks. Prove all listeners are loopback;
direct app and reverse requests without transport credentials must fail. Validate
and adapt the complete candidate using the already installed Caddy executable.
Use an isolated high-port acceptance path before public cutover. Probe preserved
learning static/API/media routes, write denial and 1KB body limit; every existing
host; creator login/public reads and a native session; ranges/HEAD and cookies;
unknown host/method/path; encoded traversal; revoked app sessions; wrong relay
and upstream capabilities; 48KB body limit; concurrency/rates; 150s deadline;
disconnect cleanup; tunnel outage/recovery; and independent service restarts.

Compare firewall state and unrelated service identities before/after. The operator
must not add firewall rules or change redirect/persistence ownership for this
deployment. Do not expand invitation-gated access, enable purchases or start
unattended generation based only on ingress tests. Record exact rollback commands,
current/previous releases, sanitized probe results and applied timestamp privately.
Reboot persistence and live rollback are not established by the acceptance
summary above. Apple native UI sign-in, Android Play-installed execution and
audible-output checks, and real app-specific sandbox purchase acceptance remain
open. Android internal 6 and the main-app Creator CTA are already delivered;
Apple 0.2.0 artifacts remain unuploaded. Do not repeat the Android upload or
alter the held production release or existing formal reviews.

## Local Verification Reference

Repeatable ingress checks:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  conda run --no-capture-output -n musia python -m unittest discover \
  -s tests -p test_creator_ingress.py -v

# Also run the same suite with the existing creator-server Python executable.
node --check deploy/creator/gateway.mjs
node --check deploy/creator/lazyedge.mjs
node --check deploy/creator/fixtures/chain.mjs
node --check deploy/creator/inventory.mjs
bash -n deploy/creator/preflight.sh
```

The suite runs the actual Node guards, a TCP reverse-forward fixture and the
actual ASGI transport wrapper against a tiny HTTP app fixture. It uses only
ephemeral IPv4 loopback ports, generated in-memory test credentials, and existing
runtimes. It performs no OAuth, purchases, model loading or audio generation.
The fixture's Caddy header handling and TCP relay are stand-ins, not proof of the
target Caddy/SSH configuration. Each test closes its servers/process and checks
that its listener ports are closed. Controller mutations are confined to private
temporary fixture directories.
