# Musia Creator: Agent, Access And Community

2026-10-09. **Live invitation-gated creator pilot, not a public paid service.**

Live workspace: <https://musia.lazying.art/creator/>. Active creator app/relay:
`4c61355dc154f7fe3afa51d2db72c3af889018c64bf11e2b76369bb30074110c`.
The edge remains on the previous release with identical guard/policy bytes.
See [deployment status](creator-deployment.md) for component hashes, service
ownership and the accepted main-learning release.

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

Apple and Google subscription products now exist as drafts at the exact target
prices above. They are not purchasable offers: payments are disabled and no real
Musia sandbox purchase has passed.
The app download price is a separate commercial decision from generation
subscriptions. Public web listening is free; do not silently change a store's
app price while implementing this feature.

## Live Acceptance

- Shared password sign-in uses the registered `musia-server` client and exact
  HTTPS callback. Apple, Google and GitHub remain centrally unavailable.
- A synthetic test user completed real registration, login, consent, invitation
  redemption and terms acceptance through the live services, not a database seed.
- That account completed a `deepseek-v4-pro` draft, one 90-second ACE XL Turbo
  render, large-v3 cross-window ASR and an actual `gpt-audio-1.5` audio review.
  The selected output was approved with 18 corrected timed lyric lines, and
  authenticated private browser audio playback passed. Audio-model review is
  evidence, not a claim of human listening or automatic publication.
- Live social QA passed private guest denial (404), public-pending guest denial
  (404), approved public audio range playback (206), likes/saves, comment
  moderation/deletion, report resolution and guest denial after unsharing (404).
  `store/.runtime/creator-social-qa.json` records these checks without requiring
  private identifiers here. The temporary public synthetic QA song is private again.
- Real native PKCE protocol roundtrips passed for both `apple` and `android`,
  including one-use exchange, replay rejection and logout. Android native Chrome
  Custom Tabs sign-in returned the account successfully. Keystore-backed account
  state and My Songs survived force-stop/relaunch, and private native Media3
  playback reported `PLAYING` at 9008 ms; sign-out cleared private playback.
  Android native UI and library/Stage regression passed for the exact signed
  0.2.0 (6) artifact, now available to the verified owner-only internal tester.
  Play-installed execution, physical-device listening and audible emulator
  output remain unverified. See [Android delivery](../store/creator-android-20261009.md).
- SwiftUI and Compose clients exist. Apple iOS/macOS 0.2.0 (7) artifacts are
  signed and validated, not uploaded. The signed universal Mac PKG passed Apple
  revalidation, but upload never started; the parent is repairing the KVM Python
  runtime's missing PyJWT dependency. Actual iOS 27 testing on the owned Mac mini
  simulator is progressing, with results pending. KVM macOS debug QA passed
  Keychain, capabilities, library and minimized playback checks, but the isolated QA
  bundle is not production-ID or signed-in creator-flow proof. Apple native UI
  sign-in and app-specific product lookup remain unverified; formal reviews
  are preserved. See [Apple evidence](../store/creator-apple-20261009.md).
- Maintenance and billing-reconciliation timers use the immutable creator
  release; maintenance succeeds while the queue is idle. The bounded generation
  service is active with stable run ID `creator-pilot-20261009` and a persistent
  10-dispatch budget. Input and output approval remain manual. Each dispatch
  invokes the one-shot worker; the ingress worker service is a separate relay.
  The generation CLI still runs from the source checkout in `musia`, not the
  immutable application release. Restarts do not replenish the budget.
- Apple/Google app-specific test verification and restore configuration is
  connected, with key paths validated. Sales and test checkout are both off.
  Apple's sandbox invalid-reference response `4000006` proves HTTP authentication
  only, not a purchase or entitlement.
- Main learning release
  `9dd15fbe0e9677284c2e94deecb763bc350f50bad6f98425e6ede0124e0eac08`
  was accepted in transaction `20261009T134643`. Its public Create CTA links to
  `/creator/`, with HTTP 200 verified. Local brief editing/export is unchanged;
  the October 9 creator privacy disclosures remain served at
  <https://musia.lazying.art/privacy>.

## What Exists

- Separate FastAPI creator boundary and a responsive web workspace at `/creator/`.
- Connected shared-account adapter using app-specific code/PKCE, browser binding,
  encrypted SDK token storage, introspection and durable refresh coordination.
- Three inspectable approved plans, pilot grants with explicit expiry, account
  generation limits, bounded invitation redemption, durable idempotent jobs.
- Editable agent brief, native-script lyrics, vocal language, duration, BPM and
  key. Text generation uses an explicitly configured OpenAI or DeepSeek model.
- Explicit consent before sending a brief; explicit render confirmation before
  reserving credit. Local drafts survive reload and connection failure.
- Fixed-command, one-shot ACE XL Turbo worker adapter reusing the existing sweep
  and large-v3 cross-window ASR review scripts. No arbitrary model, path, URL,
  shell or tool execution is accepted from a client or model response.
- Private audio access checks, public-after-review sharing, hearts, private saved
  lists, moderated comments, deletion, reports, mutual blocking and suspension.
- Mandatory selected-audio digest, timed corrected lyrics and input/ASR/listening/
  gap-tail/content checks before a render becomes a playable library song.
- Apple/Google server-side verification, immutable purchase-owner binding,
  restore and reconciliation, plus native StoreKit/Play Billing clients. Source
  and fixture coverage do not establish real purchase acceptance.
- Deleted-account media purge and retry of pending central revocations, with
  live maintenance scheduling; billing reconciliation is scheduled separately.
- Operator CLI and isolated ledger/API/browser tests, separate from the real
  live acceptance recorded above.

## What Is Not Live Or Complete

The live pilot does not establish completion of the entire rollout.

- Central discovery reports password=true and Apple/Google/GitHub=false. Only
  currently advertised providers may appear. Existing sibling native OAuth
  implementations do not prove those central providers are enabled.
- No real Musia Apple/Google sandbox purchase has passed. Checkout, renewal,
  restore, cancellation, refund/revocation and account-switch behavior still need
  app-specific store acceptance. `salesEnabled` remains false. Stripe is not
  implemented in the current creator billing boundary.
- Apple native UI sign-in, broader native lifecycle checks and the complete
  signed-in native creation journey still need qualification. Android internal
  availability and the passed native UI/library regression do not prove a Play
  installation, audible output or a real purchase.
- Moderators currently approve both input before GPU work and output before
  publication. The queue is not an unattended general-public generation service.
- The pilot worker renders one candidate per confirmation. Production candidate
  selection and automatic retries require a disclosed fixed compute budget; never
  silently charge several credits or promise unlimited quality regeneration.
- Timed sung lines are validated, but multilingual translations, word-level ruby,
  chords/Atlas, personalized covers, object storage, catalog-wide social actions,
  pagination, automated retention and native account export are follow-up work.
- Deleted-account media becomes inaccessible immediately. Maintenance now purges
  owned job files after the worker lock is released and retries pending central
  revocations. Retention/export scope and operational failure recovery still need
  rollout review; live timers do not prove every deletion scenario.

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
| `MUSIA_CREATOR_BILLING_CONFIG` | Protected app-specific provider configuration; connected test verification/restore does not enable sales |

The current `musia` conda environment is Python 3.10. Guest preview, tests and the
GPU worker run there. The private shared-account SDK declares Python 3.11+;
live server setup must use a small separate Python 3.11+ service environment
(set `MUSIA_PYTHON` for the wrapper), **not upgrade the shared GPU environment**.
Install `requirements-creator.txt` and a reviewed pinned private SDK checkout in
that server environment. Do not vendor secrets or the private repository into
the public npm package. The worker stays in `musia`.

The live service uses the separate service interpreter at
`/home/lachlan/.local/share/musia/creator-server/venv/bin/python` (Python 3.12).
The SDK was installed from the pinned private checkout above. Musia-specific
configuration is under `/home/lachlan/.config/musia/creator-auth`; credential
values, test-account identifiers and session evidence stay out of this document.

Registered browser callback contract:

```text
issuer:   https://chat.lazying.art
client:   musia-server
audience: musia-service
callback: https://musia.lazying.art/creator/auth/callback
scope:    profile
```

Do not borrow AiMemo/Bunko keys or infer social-provider readiness from registration.
Keep proxy limits and callback query/access-log suppression. Browser writes
require exact origin, JSON and `X-Musia-Request: 1`; native bearer writes and
native start/exchange permit an absent Origin but still require JSON and that
header. Session cookies are HttpOnly, Secure on HTTPS and scoped to `/creator`.
Native completion ends the issuer redirect chain with an HTTPS 200 bridge before
opening `art.lazying.musia://auth`; see [the native contract](creator-native-contract.md).
The public API serves media through an ACL-checked range endpoint rather than
handing out a permanent private bucket URL. Already downloaded public copies
cannot be recalled.

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
node bin/musia.js creator --data /private/musia-creator maintenance
node bin/musia.js creator --data /private/musia-creator billing-reconcile
```

Before `approve-input`, review rights, consent, abusive content and unsafe
impersonation. Before `approve-audio`, listen to the complete render and compare
large ASR, source intent and the actual performance. Include skipped/repeated/
tail phrases; preserve source-close words when ASR is wrong. Instrumental gaps
remain empty. The audit has `audioSha256`, actual `duration`, ordered `lines`
with `start/end/text/language`, and boolean acknowledgements `listeningPassed`,
`inputCompared`, `asrCompared`, `gapsAndTailChecked`, `contentApproved`.

The worker runs large-v3 with `--window-crosscheck`. For mixed vocals its
English-configured ASR remains only a first source. Follow up each
Chinese/Japanese phrase separately; never approve it as a complete multilingual
transcript. This adapter does not solve that audit by blindly copying an
English-only transcript or the planned lyrics.

`tools/creator_audio_review.py` can explicitly send the selected audio and intended
lyrics to OpenAI for independent review; it defaults to `gpt-audio-1.5` and is not
automatically called by `work-once`. Its report is private model evidence, not an
automatic approval or human-listening attestation.

The worker checks RAM/swap and requires an idle selected GPU with at least
22 GiB and 90% free VRAM; small idle resident services need not block it. It takes
a private process lock and a durable unique job claim. It does not reclaim a
crashed running job automatically. Reconcile existing output/provider outcome before
recovering a stuck job; no blind second render or quota reset. Do not run another
Musia generation concurrently. Media and model artifacts remain out of Git.

## Next Release Gates

1. Complete Apple UI sign-in/private playback and remaining cold/warm return,
   expiry and account-switch cases. Verify Android installation from Play and
   physical-device listening; retain the exact-build native UI/library results
   without treating player state as audible-output proof.
2. Qualify app-specific no-charge Apple/Google purchases and lifecycle behavior
   against the implemented verifier/restore/reconcile path. Draft products and
   pilot grants are not payment proof. Keep sales disabled until accepted, and
   keep inspection/restore/manage independent of new-purchase eligibility.
3. Qualify retention/export, deletion failure recovery, moderation escalation,
   reporting operations, worker isolation and resource/storage limits. Confirm
   commercial checkpoint permission and a pinned revision before paid rollout.
4. Extend the passed browser creation and social QA to the complete native
   creation journey and remaining cross-platform library/practice cases. Android
   internal 6 is already delivered: do not reupload it. Apple test uploads remain
   separate qualification work; preserve current formal reviews and the held
   Google production release.

Apple requires UGC filtering, reporting, blocking and contact mechanisms; Google
also requires responsible handling and reporting of AI-generated content. These
controls are implemented in the pilot, but operational moderation and store
qualification remain necessary. [Apple guidelines](https://developer.apple.com/app-store/review/guidelines/#user-generated-content),
[Google AI-generated content policy](https://support.google.com/googleplay/android-developer/answer/14094294?hl=en).

## Verification Scope

The live acceptance summary above is distinct from fixture tests. Relevant
repeatable checks include:

```bash
conda run --no-capture-output -n musia python -m unittest discover -s tests -p test_creator.py
conda run --no-capture-output -n musia python -m unittest discover -s tests -p test_creator_native_billing.py
conda run --no-capture-output -n musia python -m unittest discover -s tests -p test_creator_worker.py
conda run --no-capture-output -n musia python -m unittest discover -s tests -p test_creator_ingress.py
conda run --no-capture-output -n musia python -m unittest discover -s tests -p test_learning_api.py
node --check apps/web/creator/app.js
node --check bin/musia.js
conda run --no-capture-output -n musia python tools/test_creator_ui.py
```

Browser test requires the local preview on 8796. Identity/agent interactions in
that test are explicitly browser fixtures, not real authentication or generation.
The backend tests independently exercise real SQLite/HTTP logic in temporary
private directories. The separately accepted live synthetic user was registered
through the real account flow; it was not inserted as a fixture account.

Earlier local-preview evidence recorded on 2026-10-09 (not current suite totals
or proof of the newer native/billing surfaces):

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
  Live account/audio and protocol acceptance are recorded separately above.
