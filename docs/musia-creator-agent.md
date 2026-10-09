# Musia Creator: Agent, Access And Community

2026-10-09. **Source pilot and local preview, not a live paid service.**

## Product Contract

The owner's request is to let people make music through an agent using their
LazyingArt identity, choose private/public visibility, and share music socially.
Public listening, hearts, sharing, comments and saved songs must not require a
generation subscription. An account is required for attributed social writes and
private content; anonymous public listening remains available.

The owner confirmed these launch targets on 2026-10-09:

| Plan | Monthly price | Audio renders per UTC month |
| --- | --- | --- |
| Free | Free | 2 |
| Creator | US$9.99 | 20 |
| Studio | US$29.99 | 80 |

All three allow private creations and public sharing. One render is one audio
candidate up to 180 seconds. Another candidate or vocal language is another
render, disclosed before confirmation. Reserved jobs count against the allowance;
failed, quality-rejected and queued-cancelled jobs release it. No rollover. Daily
agent-turn limits are 10/50/150; account in-flight limits are 1/2/3. The GPU worker
still runs only one job at a time. Higher tiers do not select an inferior or
superior baseline model: all use the same quality route.

No app download price, current subscriber contract, store review, provider product
or billing capability was changed. The previous paid app download is a separate
commercial decision from these generation subscriptions. Public web listening is
free; do not silently change a store's app price while implementing this feature.

## What Exists

- Separate FastAPI creator boundary and a responsive web workspace at `/creator/`.
- Optional shared-account adapter using app-specific code/PKCE, browser binding,
  encrypted SDK token storage, introspection and durable refresh coordination.
- Three inspectable approved plans, pilot grants with explicit expiry, account
  generation limits, bounded invitation redemption, durable idempotent jobs.
- Editable agent brief, native-script lyrics, vocal language, duration, BPM and
  key. Text generation uses an explicitly configured OpenAI or DeepSeek model.
- Explicit consent before sending a brief; explicit render confirmation before
  reserving credit. Local drafts survive reload and connection failure.
- Fixed-command, one-shot ACE XL Turbo worker adapter reusing the existing sweep
  and large-v3 ASR review scripts. No arbitrary model, path, URL, shell or tool
  execution is accepted from a client or model response.
- Private audio access checks, public-after-review sharing, hearts, private saved
  lists, moderated comments, deletion, reports, mutual blocking and suspension.
- Mandatory selected-audio digest, timed corrected lyrics and input/ASR/listening/
  gap-tail/content checks before a render becomes a playable library song.
- Operator CLI and isolated ledger/API/browser tests. No GPU run or paid AI call
  was performed to claim this feature's acceptance.

## What Is Not Live Or Complete

This is the first app-owned implementation, not completion of the entire rollout.

- Musia's central client/HTTPS callback is not yet registered or qualified.
- Fresh public discovery on 2026-10-09 returned password=true and Apple/Google/
  GitHub=false. Only currently advertised providers may appear. Existing sibling
  native OAuth implementations do not prove those central providers are enabled.
- No Apple, Google or Stripe products, receipt verification, checkout, renewal,
  refunds or restore integration is implemented by this change. Prices are
  approved targets, not purchasable offers. `salesEnabled` remains false.
- Native SwiftUI and Compose creator/account/billing views are still to build.
  Do not wrap this web page in a WebView and call it the native implementation.
- No production ingress, production account, store binary or public review changed.
- Moderators currently approve both input before GPU work and output before
  publication. The queue is not an unattended general-public generation service.
- The pilot worker renders one candidate per confirmation. Production candidate
  selection and automatic retries require a disclosed fixed compute budget; never
  silently charge several credits or promise unlimited quality regeneration.
- Timed sung lines are validated, but multilingual translations, word-level ruby,
  chords/Atlas, personalized covers, object storage, catalog-wide social actions,
  pagination, automated retention and native account export are follow-up work.
- Deleted-account media becomes inaccessible immediately; private file purge and
  revocation reconciliation still require an operator. This must be automated
  and qualified before public signup or paid rollout.

## Reuse And Ownership

Read-only reference snapshots:

| Repository | Snapshot | Reused lesson |
| --- | --- | --- |
| LazyingArtLinkPrivate | `7f334dbd749742c73cf16be027e77540536d68f5` | App-owned confidential client, encrypted durable flow/session vault, live provider discovery |
| OnlyIdeasApp | `d7becc943701ed16c76816c06ce43814a591681f` | Public/private distinction, reviewed sharing, idempotent hearts/saves, comment/report/block behavior |
| AiMemo | `efa50591cbf6e2969c3b80bf6705fe60e70fc57f` | Server-side usage, account deletion/revocation, independent provider entitlements |
| Bunko | `7f756f00675f98eae3643a156b3c60db5be3bfff` | Free core use, optional accounts, independent cloud allowance, no cross-app subscription merge |

EchoMind owns the central issuer. Its shared browser and subscription guidance
were read through LazyingArtLinkPrivate. No sibling source/runtime was modified.
The existing public Musia API remains read-only and the local Studio remains
private. The creator service deliberately does not import Studio handlers.

Identity is `(issuer, subject)`, not email or display name. Invitations gate the
creator pilot, not general LazyingArt registration or public listening. Invitation
codes do not grant a paid tier. Pilot grants are labelled `pilot_grant`, never
represented as verified payments or inherited EchoMind benefits.

## Runtime And Preview

```bash
node bin/musia.js creator serve --port 8796
```

Open `http://127.0.0.1:8796/creator/`. Defaults: no auth, no generation and no
payments. The UI is honest about disconnected capabilities. It still supports
local brief editing/export and plan inspection.
Run this from the source checkout. The current npm package allowlist does not
bundle the creator service; no new npm package was published for this pilot.

Configuration (server-only environment, never a frontend bundle):

| Variable | Purpose |
| --- | --- |
| `MUSIA_CREATOR_ORIGIN` | Exact HTTPS origin for deployed service; loopback HTTP for preview |
| `MUSIA_CREATOR_DATA` | Private real directory, mode 0700; SQLite mode 0600 |
| `MUSIA_CREATOR_AUTH_DIR` | Private directory containing registered `musia-server` credentials |
| `MUSIA_CREATOR_GENERATION=1` | Enable authenticated queue submission after worker qualification |
| `MUSIA_CREATOR_OPEN_SIGNUP=1` | Remove creator invitation requirement only after rollout review |
| `MUSIA_CREATOR_TEXT_MODEL` | Explicitly verified available model name |
| `MUSIA_CREATOR_TEXT_API_KEY` | Musia-owned provider credential |
| `MUSIA_CREATOR_TEXT_BASE_URL` | `https://api.openai.com/v1` or `https://api.deepseek.com` |

The current `musia` conda environment is Python 3.10. Guest preview, tests and the
GPU worker run there. The private shared-account SDK declares Python 3.11+;
live server setup must use a small separate Python 3.11+ service environment
(set `MUSIA_PYTHON` for the wrapper), **not upgrade the shared GPU environment**.
Install `requirements-creator.txt` and a reviewed pinned private SDK checkout in
that server environment. Do not vendor secrets or the private repository into
the public npm package. The worker stays in `musia`.

This workstation's prepared service interpreter is
`/home/lachlan/.local/share/musia/creator-server/venv/bin/python` (Python 3.12).
The SDK was installed from the clean pinned private checkout above. The disabled
Musia-specific configuration is under `/home/lachlan/.config/musia/creator-auth`;
only paths are recorded in the private OneTimeSync handoff, not key values.
Staging does not register the client or enable any login provider.

Desired registration, subject to the issuer owner's acceptance:

```text
issuer:   https://chat.lazying.art
client:   musia-server
audience: musia-service
callback: https://musia.lazying.art/creator/auth/callback
scope:    profile
```

Use SDK disabled onboarding with private path-only coordination. Do not borrow
AiMemo/Bunko keys, invent social-provider readiness or enable an unregistered
callback. Deploy proxy request limits and disable callback query/access logging.
All writes require exact origin, JSON and a custom header; session cookies are
HttpOnly, Secure on HTTPS and scoped to `/creator`. The public API serves media
through an ACL-checked range endpoint rather than handing out a permanent private
bucket URL. Already downloaded public copies cannot be recalled.

## Operator Workflow

All operations use a private service database, not the current public catalog.
`queue` prints private prompt/review/report information: do not put its output in
Git, screenshots, chat, shared notes or public logs.

```bash
node bin/musia.js creator --data /private/musia-creator queue
node bin/musia.js creator --data /private/musia-creator invite --days 7 --uses 1
node bin/musia.js creator --data /private/musia-creator pilot-grant ACCOUNT creator --days 30 --reason 'Owner-approved pilot'
node bin/musia.js creator --data /private/musia-creator approve-input JOB
node bin/musia.js creator --data /private/musia-creator work-once
node bin/musia.js creator --data /private/musia-creator approve-audio JOB --audit /private/review.json
node bin/musia.js creator --data /private/musia-creator moderate song JOB approve
node bin/musia.js creator --data /private/musia-creator moderate comment COMMENT approve
node bin/musia.js creator --data /private/musia-creator suspend ACCOUNT
node bin/musia.js creator --data /private/musia-creator resolve-report REPORT
```

Before `approve-input`, review rights, consent, abusive content and unsafe
impersonation. Before `approve-audio`, listen to the complete render and compare
large ASR, source intent and the actual performance. Include skipped/repeated/
tail phrases; preserve source-close words when ASR is wrong. Instrumental gaps
remain empty. The audit has `audioSha256`, actual `duration`, ordered `lines`
with `start/end/text/language`, and boolean acknowledgements `listeningPassed`,
`inputCompared`, `asrCompared`, `gapsAndTailChecked`, `contentApproved`.

For mixed vocals the worker's first full-mix English ASR pass is only a first
source. Follow up each Chinese/Japanese phrase separately; never approve it as a
complete multilingual transcript. This adapter does not solve that audit by
blindly copying an English-only transcript or the planned lyrics.

The worker checks RAM/swap and refuses an occupied GPU. It takes a private
process lock and a durable unique job claim. It does not reclaim a crashed
running job automatically. Reconcile any existing output/provider outcome before
recovering a stuck job; no blind second render or quota reset. Do not run another
Musia generation concurrently. Media and model artifacts remain out of Git.

## Next Release Gates

1. Register and qualify exact browser callback, state/S256/replay/refresh/logout,
   correct-account persistence and provider readiness; then native system-browser
   authorization plus secure native sessions/app links.
2. Bind real Apple/Google/Stripe receipts to immutable Musia owners and products.
   Implement durable notification inbox/reconciliation, paid-through cancellation,
   renewal, upgrade, restore and revocation. Current pilot grants are not payment
   proof. Keep inspection/restore/manage independent of fresh purchase capability.
3. Complete deletion/export/retention, automated moderation escalation, abuse
   controls, reporting operations, isolated worker credentials and resource/storage
   limits. Select a commercially permitted checkpoint and pin its revision.
4. Run the full real account -> approved prompt -> ACE -> independent ASR/listening
   -> corrected media -> private playback -> deliberate public share journey.
5. Integrate with native library/recording view, maintain EN/ZH/JA ruby/highlights,
   test provider purchase flows in app-specific no-charge environments, then ship
   successor internal test builds. Preserve current reviews unless asked otherwise.

Apple requires UGC filtering, reporting, blocking and contact mechanisms; Google
also requires responsible handling and reporting of AI-generated content. These
controls are implemented in the pilot, but operational moderation and store
qualification remain necessary. [Apple guidelines](https://developer.apple.com/app-store/review/guidelines/#user-generated-content),
[Google AI-generated content policy](https://support.google.com/googleplay/android-developer/answer/14094294?hl=en).

## Verification

```bash
conda run --no-capture-output -n musia python -m unittest discover -s tests -p test_creator.py
conda run --no-capture-output -n musia python -m unittest discover -s tests -p test_learning_api.py
node --check apps/web/creator/app.js
node --check bin/musia.js
conda run --no-capture-output -n musia python tools/test_creator_ui.py
```

Browser test requires the local preview on 8796. Identity/agent interactions in
that test are explicitly browser fixtures, not real authentication or generation.
The backend tests independently exercise real SQLite/HTTP logic in temporary
private directories. No synthetic account is inserted in production.

Verified on 2026-10-09:

- 39 creator tests passed on Python 3.10 and Python 3.12.
- 32 existing learning API tests passed; shared-account adoption guard passed.
- Browser checks passed at 1440, 768, 390 and 320 pixel widths with no page errors
  or horizontal page overflow; draft reload, explicit generation confirmation
  and private default were exercised.
- Liking a playing song preserves the same audio node and advances its playhead;
  switching views or closing a song stops and removes that player.
- JavaScript syntax and diff whitespace checks passed.
- Screenshots are private generated evidence under `store/.runtime/creator-ui/`,
  not proof of real sign-in, generation, checkout or production deployment.
