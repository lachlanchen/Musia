# Musia Learning Deployment

This deploys only the public, read-only learning service at
`https://musia.lazying.art`. Native application identity: `art.lazying.musia`.
It never deploys Musia Studio, generation workers, models, private sessions,
original audio, upload handlers, or provider credentials.

## Ownership And Public Contract

Deployment code is confined to this directory and
`scripts/deploy_musia_learning.py`. Backend and web source belong to their
respective owners and are copied without modification.

The edge serves the declared GET/HEAD API routes, catalog song IDs, and exact
static paths from `musia.learning.STATIC_FILES`. POST/PUT/PATCH/DELETE/OPTIONS
return 405. Unlisted paths return 404; malformed paths and GET bodies are
rejected. OpenAPI, Studio, jobs, generation, uploads and arbitrary file serving
are absent. There is no public credential or bearer token in this release.

The builder projects eligible published songs through `PublicLibrary`, writes
only sanitized catalog/manifest/study/lyric fields, and verifies an exact
round-trip against the original public API output. Hidden/draft records and
private provenance are not shipped. Published media URLs stay on their existing
public hosts; the only local audio is the deterministic First Pulse exercise.

## Runtime

- Existing Huanayun ingress is reused; no new Caddy or reverse tunnel is started.
- `musia-learning.service` uses its own unprivileged system account and binds
  only `127.0.0.1:18440`.
- One Uvicorn worker, concurrency 8, backlog 32, keepalive 2 seconds; no access
  log, proxy-header trust, reload watcher, or server-version header.
- Read-only filesystem, private temporary directory, restricted address
  families, loopback-only IP policy, empty capabilities and no new privileges.
- Memory high/max: 96/128 MiB; no swap allowance; CPU quota 50%; tasks limit 32.
- Runtime is CPython 3.12 with the three exact server requirements and their
  recorded transitive wheel versions. No pip, compilation or dependency
  downloads run on the edge. The small runtime dependency set is prepared
  locally with wheels only. The full Musia conda environment is not copied.

## Build And Deploy

Run from the Musia repository in the `musia` environment:

```sh
PYTHONNOUSERSITE=1 conda run -n musia python -B -m unittest discover \
  -s deploy/learning -p test_deployment.py -v
PYTHONNOUSERSITE=1 conda run -n musia python -B scripts/deploy_musia_learning.py build
PYTHONNOUSERSITE=1 conda run -n musia python -B scripts/deploy_musia_learning.py deploy
```

Coordinate backend/web readiness and browser acceptance before deployment.
Build runs backend and web unit tests, then HTTP acceptance against the staged
app with the CPython 3.12 wheel set. Source hashes are checked again immediately
before deploy. A concurrent source change requires rebuilding.

Artifacts are ignored under `deploy/learning/.work/`. `latest-build.json`
identifies the exact archive, SHA-256, payload and local acceptance. Each
transaction has its own private evidence directory. Do not commit those
archives, inventories, browser evidence, wheels or raw logs.

The controller:

1. Checks memory, listener ownership, existing sites and pinned SSH access.
2. Captures the exact Caddyfile, service unit, firewall digest and preserved
   service identities in an owner-only transaction record.
3. Verifies the transferred archive and every manifest entry, installs a new
   root-owned immutable release, and starts only the Musia service.
4. Runs loopback acceptance, restarts only Musia, and repeats acceptance.
5. Adds a TLS-only 503 site when the hostname is new. It validates as the
   actual Caddy service user and reloads the existing private admin endpoint.
6. Requires certificate-verifying HTTPS from the workstation before enabling
   the learning route. It then checks the high-port route, public API, security
   failures, and every preserved public site.
7. Enables Musia and promotes `current` only after acceptance. Firewall bytes
   and unrelated service identities must remain unchanged.

There are no DNS, firewall, SSH-policy, LazyTunnel, LazyEdit, Oracle or LightMind
service changes. Certificate issuance belongs to the existing Caddy instance.
No reboot is part of this procedure, so reboot recovery remains unverified.

## Rollback And Concurrent Changes

The controller automatically attempts rollback after a staging/activation
failure. It restores the prior Caddyfile and Musia unit, stops the new service
on a first deployment, and restores the previous release link when one existed.
It refuses to overwrite a Caddyfile or unit changed by another operator.
Such conflicts require scoped manual review, never a whole-server reset.

For a known transaction and its retained receipt:

```sh
PYTHONNOUSERSITE=1 conda run -n musia python -B scripts/deploy_musia_learning.py \
  rollback --transaction <transaction-id> --receipt <release-receipt.json>
```

Keep the accepted release and immediately previous reproducible release. Do
not rerun greenfield ingress scripts, flush nftables, or use the original
LazyEdit firewall rollback as a Musia rollback.

## Administrator Access

Reuse the existing pinned `hncloud` SSH administrator configuration and the
reviewed LazyEdit `scripts/studio/remote_admin.py` helper. The helper reads the
administrator credential in-process and sends it to `sudo -S` through stdin.
Credential values never appear in argv, releases, documentation or logs.
Do not substitute provider/root credentials, weaken host-key checking, enable
passwordless sudo, or administer through a restricted tunnel account.

## Deployment Checkpoint

Latest update **2026-10-05 06:26:50 UTC**: bilingual catalog and archive selection
published from clean source commit `da41b32`. Release
`4faa66d368a185bb71670355d44debb3c819fc6449eee63798b48b1cfff0c4a5`, transaction
`20261005T142512-4faa66d368a1`; predecessor `99b459c47682...` retained.
The app API has 29 songs plus First Pulse. All 29 song responses match the
sanitized build exactly; 71 public HTTP checks and desktop/mobile browser
playback checks passed. No app binary change was needed. See the
[catalog release record](../../references/catalog-curation-2026-10-05.md)
for the scoped, owner-approved memory recovery and firmware-service restoration.
The 180 MiB guard remains unchanged. Unrelated services and firewall rules were
preserved. Private transaction evidence is in `.work/20261005T142512-4faa66d368a1/`.

Previous checkpoint **2026-09-26 05:16:05 UTC**: shared major/minor chord diagrams and
responsive footer spacing deployed successfully. Release
`2d58d928cc954a0c6eb42f67886aa84cd49d2ed6af17dafa0741ac6c6e7a0bbb`, transaction
`20260926T131441-2d58d928cc95`; predecessor `09e9dd2c...` retained. The exact
static allowlist adds `/guitar-shapes.js`. Public asset hashes, full playback
smoke, 24-shape rendering and 12 viewport/text-scale checks pass. See
[fix verification](../../references/musia-native-chords-and-navigation-2026-09-26.md).
The observations below describe the preceding September 25 deployment.

Accepted **2026-09-25 14:48:28 UTC / 22:48:28 HKT**. The public preview is live
with 31 published songs plus First Pulse, the corrected support link, 100%
initial exercise speed, and the lyric-spacing/punctuation fix. The final web
review fixes are included: a single unmetered Pulse for analyzed songs,
loading-state guards, ignored held-key repeats with assistive-click support,
and playback-rate-aware loop-end timers. Browser loops are not sample-accurate.
Only `apps/web/app.js` and `apps/web/styles.css` changed from the preceding
accepted snapshot; backend and public route contracts are unchanged.

- Current archive SHA-256:
  `09e9dd2c5a5bf79d43c69eb9dedc80efafb863a2f692348bef135254b4d0cd79`.
- Previous accepted archive SHA-256:
  `e49acbea95199aeb73025e2f7f6b24d67c9ec08bf679624f998f4d2fe9a547ac`.
- Current release: `/srv/musia-learning/releases/<current-sha256>`;
  `/srv/musia-learning/current` points there. Exactly these two releases remain.
- Enabled service: `/etc/systemd/system/musia-learning.service`, exclusively
  `127.0.0.1:18440`, PID 486129 at verification, zero automatic restarts.
  Memory was 39.6 MiB after browser QA, peak 44.6 MiB; final available edge RAM
  was 231 MiB, with no swap. These are observations, not capacity guarantees.
- Shared ingress: `/etc/lazystudio/Caddyfile`, `lazystudio-caddy.service`,
  admin `127.0.0.1:12019`, existing high ports `18080/18443`.
  Current Caddyfile SHA-256:
  `f41729ca90eeb9ae6a581746d0ab02b12135e799dc449ba1049bf46578d5ab73`.
- Public certificate: Let's Encrypt YE2, SAN `musia.lazying.art`, valid through
  **2026-12-24 13:18:00 UTC**. DNS and normal certificate-verifying HTTPS passed.
- No GUI/noVNC stack is owned by this deployment. Headless browser tests exited.

Validation: 29 backend tests, 7 web tests, 6 deployment tests; 72 HTTP checks at
both the direct high-port ingress and the public HTTPS endpoint. Staged local
and edge loopback acceptance and an independent Musia restart also passed.
Public asset hashes match the final sealed snapshot. External TCP 18440 was
unreachable (timed out in the final probe). Existing edit, agent.lightmind,
oracle-fast and auspice HTTPS probes
passed; preserved Caddy/Studio/Oracle process identities and the native nft
ruleset digest were unchanged.

Real public-site Playwright passed exercise playback, beats/chords, 25-200%
playback, phrase looping, tap feedback, persisted progress, Aya audio/lyrics,
brief export and 320/390/768/1440px layouts with zero JavaScript errors.
It also exercised actual held-Space repeat suppression and an assistive click,
and verified a single Pulse for Aya plus preserved English word spacing.
A separate public browser check held only its own song request to confirm
disabled play/vocal controls, cleared stale phrases, guarded callbacks and
successful recovery. Desktop and mobile screenshots were visually inspected.

Evidence is in the ignored local directory
`.work/20260925T224654-09e9dd2c5a5b/`: `final.json`,
`public-acceptance.json`, `activate.json`, `certificate-gate.json`,
`external-boundaries.json`, `post-browser-state.json`, `browser/result.json`,
and `browser/loading-guards.json` plus screenshots.
The owner-only edge transaction is
`/var/lib/musia-learning/deployments/20260925T224654-09e9dd2c5a5b/`, containing
the previous Caddyfile/unit, state, firewall snapshot and loopback/restart/
high-port acceptance. The reproducible package and wheel lock are retained
under `.work/build-20260925T224243/` and in the immutable release.

Transient SSH timeouts and an archive-transfer connection closure occurred
before staging; those attempts did not alter the production service. The
accepted transaction reused a deployment-owned SSH control socket and the
existing pinned administrator configuration. No shared SSH configuration or
credentials changed. The owned control connection expired automatically;
no owned control socket or test runtime remained at handoff. The main agent's
`musia-learning` tmux review server on local port 18440 was left running.

All packaged source hashes were rechecked against the workspace after public
QA and still match. The complete source/file manifest is retained at
`.work/build-20260925T224243/payload/release.json`. This is a file-hash-based
snapshot of the shared dirty worktree, not a new Git commit.

Exact rollback from the repository root, **only when rollback is authorized**:

```sh
PYTHONNOUSERSITE=1 conda run -n musia python -B scripts/deploy_musia_learning.py \
  rollback --transaction 20260925T224654-09e9dd2c5a5b \
  --receipt deploy/learning/.work/20260925T224654-09e9dd2c5a5b/release-receipt.json
```

Automatic rollback was exercised on the first rejected activation: a Caddy
handler-ordering issue returned 404 instead of 405 for POST. It restored the
exact original Caddyfile and stopped the rejected service. The corrected
handler passed acceptance; the failed package was then removed, retaining its
evidence. Rolling back the final release to its retained predecessor has not
been executed, because that would undo the accepted web fixes.

Two limits remain explicit: reboot recovery was not tested; and the existing
shared Caddy fallback returns an empty HTTP 200 for an unmatched Host. Such a
request does not reach Musia or return its data. No server-wide catchall was
changed merely to obtain a different denial status. Musia's own undeclared
paths and write methods return 404 and 405 respectively.
