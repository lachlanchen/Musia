# Portable Creator Runtime

## Decision

2026-10-15: keep **direct DeepSeek V4 Pro API** as the default for conversational
song briefs. These operations need structured text, not an autonomous shell
agent. A separate, optional **AgInTi JSON specialist** implements the same
`Chat -> AgentReply` contract. It is not AgInTi's general CLI, Studio management
API, browser, or shell runtime. Neither backend submits renders or publishes.

Codex CLI is deliberately **not installed or invoked**. The owner clarified
that direct DeepSeek is sufficient when agent tools are unnecessary. Do not
mount a personal/company Codex profile or use a developer's active session as a
multi-user backend. A future tool-capable agent needs a separate, scoped tool
contract and isolated per-job execution, not merely a different prompt.

The direct adapter also retains the explicitly configured OpenAI API option;
it is not an automatic Codex fallback. There is no silent provider failover,
duplicate inference, repeated render, or cross-provider disclosure on failure.

## Layout

```text
native clients / browser -> existing TLS ingress -> app (learning + creator)
                                                    |
                          default: bounded DeepSeek text API via egress proxy
                          optional: private AgInTi sidecar -> egress proxy

approved render queue -> existing separate single-GPU ACE worker
```

The default Compose stack has three small services: Python app, tinyproxy and
a loopback HTTP front door (Caddy, separate from the machine's shared ingress).
AgInTi adds one Node service only when its overlay is selected. No CUDA, model
weights, conda clone, browser, Docker socket or privileged container is included.
The existing GPU worker and its approval/credit controls remain unchanged.
Native binaries and external media storage are not embedded in this image.

- App/agent run as UID/GID 10001, read-only root, no capabilities, no-new-privileges.
- State is a separate private 0700 volume; temporary files are size-limited tmpfs.
- Default app/agent network is internal. Outbound HTTPS uses the exact-host
  egress allowlist; arbitrary hosts and direct internet connections are denied.
- Only the front door's loopback port is published. Agent RPC requires a separate token.
- Provider secrets are file mounts, never image layers, prompts, Docker env
  values or public responses. Source secret files must be readable by container
  UID 10001: for local Compose, mode 0444 inside a host mode 0700 directory works.
  Docker secrets here are protected mounts, **not encryption at rest**.
- Direct API: 2 concurrent turns maximum, 75-second whole-request deadline,
  no redirects/retries, 3500-token generation limit, 64KiB response limit.
- Docker explicitly sets `MUSIA_CREATOR_DEEPSEEK_THINKING=disabled` for interactive
  speed. Operators can select `enabled` for deliberate reasoning within the same
  budget. Outside Docker an unset value preserves the provider's prior default.
- AgInTi: 1 concurrent turn, 70-second deadline, same validated request/reply;
  request history is context, never system/tool authority. Disconnect aborts inference.
- Resource limits: app 384 MiB/1 CPU, proxy 32 MiB/0.25 CPU, front door 64 MiB/0.25 CPU,
  optional agent 384 MiB/1 CPU. These are ceilings, not normal usage.
- Existing invitation, usage ledger, explicit render confirmation, private
  ownership, moderation and disabled public billing remain authoritative.

Docker shares the host kernel; this is defense in depth, not a VM-equivalent
boundary for arbitrary hostile code. No model-generated code runs here.

## Build And Preview

Use a private key file outside Git. Do not put the key in the command line.
An empty file allows a disconnected, no-provider guest preview.

```bash
export MUSIA_TEXT_KEY_FILE=/private/musia/text.key
export MUSIA_IMAGE_TAG=your-reviewed-release
COMPOSE_PARALLEL_LIMIT=1 docker compose -f deploy/containers/compose.yaml build
docker compose -f deploy/containers/compose.yaml up -d --wait
```

Build one Musia image at a time on the shared workstation. Base images are
digest-pinned and Python versions are constrained by `requirements.lock`.

Preview: <http://127.0.0.1:18796/> and <http://127.0.0.1:18796/creator/>.
Changing the port also requires setting `MUSIA_CREATOR_ORIGIN` to that exact
origin. Default guest preview has **no login, generation or paid checkout**.
A provider key alone does not authorize a user or start a song render.

Optional AgInTi:

```bash
export MUSIA_AGENT_TOKEN_FILE=/private/musia/agent.token
# Supply a separate random URL-safe token, 32-128 characters, not the API key.
COMPOSE_PARALLEL_LIMIT=1 docker compose \
  -f deploy/containers/compose.yaml -f deploy/containers/compose.aginti.yaml build
docker compose -f deploy/containers/compose.yaml \
  -f deploy/containers/compose.aginti.yaml up -d --wait
```

AgInTi is pinned to `@lazyingart/agintiflow@0.20.339-integration.0` with its npm
integrity and dependency lock. Its JSON specialist, not a locally patched copy,
is used in tests. The adapter overrides unused KaTeX to 0.18.2 to close a known
audit finding; no shared AgInTi installation or runtime is changed.

## Qualification

```bash
~/.local/share/musia/creator-server/venv/bin/python \
  -m unittest discover -s tests -p 'test_creator*.py'
~/.local/share/musia/creator-server/venv/bin/python \
  tools/export_creator_agent_contract.py --check
python tools/test_creator_containers.py --tag your-reviewed-release
python tools/test_creator_containers.py --tag your-reviewed-release --aginti
```

The container tests create a random Compose project with synthetic credentials,
verify pages, non-root/read-only/capability limits, forbidden egress, RPC auth,
state retention and AgInTi fixture behavior, then remove **only** their own
containers/networks/volume. They never bind live account or media state.

`--live-key-file /private/musia/text.key` explicitly permits one small synthetic
text-provider call per test invocation. No audio render, login, purchase or
publication occurs. Output reports validation and latency, not keys or lyrics.
Run both backends if adopting AgInTi. Fixture success alone is not live proof.

`tools/export_creator_agent_contract.py` mechanically regenerates the Node
contract from Python; change the canonical Pydantic models/prompt first.

## Login And Migration

`compose.auth.example.yaml` builds an optional authenticated target from a
reviewed private SDK wheel supplied through a BuildKit named context. Keep
that image in a private registry; never add private SDK credentials to the
build context. The SDK itself is code, not an authentication secret.

The existing SDK deliberately disables ambient HTTP proxies. Its optional
account API therefore uses ordinary outbound networking; the agent sidecar
still has only restricted egress and receives no account credentials/state.
Do not claim the auth overlay has the same egress restriction as guest preview.
Production billing verifier configuration is **not** automatically mounted.

Migrate in this order, with a named ingress owner and an explicit maintenance window:

1. Record image IDs, source revision, exact public origin, state paths, auth
   adapter revision and current units. Keep the old release available.
2. Pause new writes/queue admission; drain active chat and GPU jobs. Stop only
   Musia's owned API, generation, maintenance and reconciliation writers. Never
   copy a live SQLite database by copying only its main file or run two writers.
3. Back up **all** state, media and app-owned auth storage including WAL/SHM
   after shutdown. Preserve encryption keys, owner IDs, invitation/credit/job
   ledger and purchase bindings. Check SQLite `PRAGMA integrity_check` on a copy.
4. Restore a copy into private storage owned by the new service UID. Do not
   chmod/chown the running old installation. The ledger contains absolute media
   paths: mount copied state at the **same absolute container path**, using
   `MUSIA_CONTAINER_STATE_PATH`; do not silently rewrite rows or audio digests.
5. Use the exact existing domain/callback and registered Musia client. Stage
   authenticated image, private auth/state mounts and operator configuration.
   Existing account and billing gates are not permission to enable public sales.
6. Qualify real login/refresh/logout, private audio/range denial, quota,
   idempotency and a reviewed render against the single authoritative database.
   Reuse the existing GPU host/mounts. This container pack does not migrate GPU
   execution to another machine or implement a new cross-host worker RPC.
7. Switch only the Musia upstream after acceptance; retain domain/TLS/callback.
   Recheck native clients and public endpoints. Re-enable one writer set only.
8. If rolling back, stop the successor first and use the **latest authoritative
   state**, not a stale pre-cutover backup if new writes were accepted.

No live cutover, account migration, DNS change, payment activation or app-store
submission is performed just by building or running the disposable test pack.
Health checks prove process health, not provider availability or complete login.

## Operations

Inspect `docker compose ps` and bounded logs; do not print environment/secrets.
Use immutable image digests for transfers and retain current/previous releases.
Back up volumes separately from images and encrypt private backups in transit
and at rest. Never run `down -v` against production; that flag is only used by
the disposable QA helper. Stop a local preview after review when it is idle.

Codex remains an optional future integration. Official reference, consulted
while assessing it: [non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
and [configuration](https://learn.chatgpt.com/docs/config-file/config-reference).
