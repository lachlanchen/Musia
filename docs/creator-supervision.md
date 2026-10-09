# Bounded Creator Supervision

`musia.creator.supervisor` is an opt-in private library, not a public API or a
qualified unattended music service. The parent owns CLI/systemd wiring. This
change enables no signup, invitation bypass, generation ingress, billing,
payment, publication or subscription capability. No GPU or paid API execution
was used to test it.

## Approved Queue First

Run in the existing `musia` conda environment, with the same private `Store`
directory as the worker. Example parent integration (this can launch real work
when explicitly enabled; it is not a dry-run command):

```python
from musia.creator.store import Store
from musia.creator.supervisor import Config, Supervisor, supervise_once

config = Config(
    run_id="operator-approved-batch-001",
    enabled=True,
    dispatch=True,
    max_per_run=2,
    max_dispatches=2,
    max_passes=8,
    poll_seconds=30,
)
store = Store(private_directory)
report = supervise_once(store, config)
# Alternatively, a finite daemon using the SAME config/run_id:
# report = Supervisor(store, config).run(stop=shutdown_event)
```

Defaults do nothing: `enabled`, `dispatch` and `review_inputs` are false. There
is no implicit enablement based on an environment key or a queued request.
`supervise_once` performs at most one poll and one worker invocation, plus
bounded input reviews if enabled. `Supervisor.run()` holds the nonblocking
`supervisor-daemon.lock` ownership lock across its finite polling loop,
including sleeps. Only one daemon or one-pass supervisor can own a store at a
time. Each pass separately holds `supervisor.lock` for journal updates, provider
calls, dispatch, and evidence capture, then closes the journal and releases
that mutation lock before sleeping. Maintenance can therefore run during idle
polling without racing an in-flight operation. A stop event prevents new work
and wakes a sleep; it does not interrupt an in-flight worker or API request.
The existing worker owns its subprocess timeouts and cleanup. The parent must
arrange signal handling and project-owned process cleanup.

An existing daemon returns `supervisor_busy` to another supervisor. Mutation
lock contention returns `maintenance_busy` for a one-pass call; a daemon waits
its configured poll interval and retries without spending an action or text
budget. Such polls count toward the invocation's finite `max_passes` polling
bound, while the persistent pass counter counts only admitted passes. A stop
event also ends a contended wait without needing to acquire the mutation lock.

The existing `worker.work_once(store)` owns resource checking, the worker lock,
atomic claim/lease, fixed command construction, generation, ASR and result
recording. The supervisor does not bypass, duplicate or modify these checks.
Busy resources leave a job queued, without a claim or credit release. The
attempt still consumes a supervisor dispatch slot; this is conservative
admission accounting, not a charge to the user. The invocation returns
`worker_error_or_deferred` because the worker exposes no typed distinction
between resource deferral and other errors. An occupied worker lock returns
`worker_busy`. These conditions stop the current loop rather than retrying.

## Bounds And Restart Rules

`max_per_run` counts side-effect attempts, not successful songs: reviewing an
input and dispatching its render use **two** slots. Independent
`max_dispatches`, `max_input_reviews`, `max_passes` and text expenditure limits
also apply. A daemon dispatches at most once per pass. Brief duration and
single-candidate compute bounds remain those of the existing contracts/worker.

Private `supervisor.sqlite` records a call/dispatch intent and its budget before
execution. Both supervisor lock files and this journal are mode 0600 under the
private 0700 creator directory. Counters survive constructing another supervisor or
restarting the process. A run ID cannot be reused with changed configuration.
Reuse the configured run ID across service restarts; never generate one per
poll/start or configure a scheduler that silently refreshes the budget. A new
run ID explicitly authorizes a new batch budget. Provider account/project
spending limits must also be configured by the operator.

Every text call reserves its entire `text_call_ceiling_microusd` up front,
including timeout, malformed response and process death. There are no refunds
or automatic retries. `max_text_spend_microusd` caps these reservations (one
micro-USD is USD 0.000001). The per-call ceiling is an **operator-verified upper
bound**, not a claim that provider billing was measured or controlled by this
module. Before enabling, qualify the server-selected model, provider rates and
tokenization against the bounded system prompt plus at most 50,000 UTF-8 bytes
of brief JSON, and the configured completion-token maximum. Include provider
reasoning/output charging in that bound. If a trustworthy upper bound is not
available, leave review disabled. Wrong pricing cannot be made safe by a local
reservation counter. Provider-side caps remain necessary for monetary safety.

## Optional Input Review

Set `review_inputs=True`, positive `max_input_reviews`,
`text_call_ceiling_microusd`, and `max_text_spend_microusd` explicitly. The
default text adapter reuses `Producer`'s server-only configuration and endpoint
allowlist: `MUSIA_CREATOR_TEXT_MODEL`, `MUSIA_CREATOR_TEXT_API_KEY`, and
`MUSIA_CREATOR_TEXT_BASE_URL`. It uses zero SDK retries, a 90-second timeout,
bounded completion tokens and a strict `pass`/`deny`/`unclear` JSON contract.
No prompt command, model-selected endpoint, tool call, path or audio-approval
field is accepted or executed. Private model reasoning is evidence, not a
public error message or instruction to the worker.

The parent must supply `consent(job) -> bool`, backed by recorded permission
to send **that submitted brief** to the configured provider. Only literal
`True` authorizes a call; missing consent, errors, stale accepted terms or an
inactive account leave it pending. The callback is checked again before a
decision is applied. Current terms disclose provider transmission for agent
requests, but describe render requests as private ACE processing. Do not
assume that agreeing to those terms alone establishes new render-review
consent. The parent owns explicit disclosure/consent storage; no schema or
frontend change is made here. Do not wire `lambda job: True` in production.

Input decisions are bound to a private SHA-256 of the immutable brief:

- `pass`: calls existing `approve_input`; no render unless separately enabled
  and budgeted, and never output approval or legal certification.
- `deny`: calls owner-bound `cancel` while queued, releasing the existing
  reservation. `reject` is for output review and is not misused on input.
- `unclear`, unavailable provider, invalid/truncated result, timeout, revoked
  consent or changed state: leave the current gate unchanged for an operator.

Each job gets at most one automated input attempt across all run IDs. Decisions
and error types are private; prompt text and raw provider exceptions are not
included in the returned status. The journal retains decision reasons, which
may echo private material: never publish it, commit it, or expose it over HTTP.
`maintenance.purge_deleted` now includes this journal in account-deletion
cleanup. It acquires the supervisor lock before the worker lock, both
nonblocking; contention returns `waitingForSupervisor` or `waitingForWorker`
without removing media or evidence. This prevents an in-flight review from
writing private evidence back after deletion. Maintenance does not take the
daemon ownership lock, so it can purge during any idle polling sleep. The lock
order is daemon ownership -> supervisor mutation -> worker for supervision,
and supervisor mutation -> worker for maintenance; neither path waits on a
peer's file lock. Retry maintenance after an in-flight pass releases its lock.

Only deleted owners' job-linked input attempts and output metadata are removed.
Their linked dispatch evidence is redacted to `{}`, while dispatch identities,
statuses, unknown `started` holds and aggregate run/budget counters are retained.
Active-owner and unlinked records are untouched. Repeated cleanup is idempotent
and cannot authorize another dispatch or replenish an exhausted budget.

Cleanup never creates a missing journal. Existing journals must be private,
owned regular SQLite files with the expected schema and no triggers; symlinks,
hardlinks, unsafe sidecars and unrelated databases fail closed before media
removal. Cleanup is limited to 64 MiB of journal and sidecar data; larger files
require operator maintenance. SQLite deletion uses `secure_delete`, compaction
to remove older free-space fragments, and a nonblocking WAL truncation
checkpoint. A busy database/checkpoint raises an error for retry, not a claim
of completed cleanup; already committed redactions stay committed. External
backups and filesystem snapshots still require
the parent's retention policy; this is not a physical-erasure guarantee.

## Crashes And Output Gate

Integrate with the approved SEC-1/SEC-2 store/worker fixes from
`docs/creator-security-review.md` before enabling dispatch. A known-stopped
suspended-owner failure is retired by the worker/store, not by this supervisor.
The worker's typed `WorkerOutcomeUnknown` always retains an unfinished dispatch
intent and requires reconciliation, even if another operation has changed the
job's visible state. Both `running` and `interrupted` representations are
supported; the supervisor does not manufacture either state or issue a refund.

Any existing `running` or `interrupted` job blocks dispatch. Age alone does not
prove a worker died. The supervisor does not expire leases, requeue, rerender,
release an unknown reservation, infer success from a WAV, or kill another
project's runtime. An unfinished dispatch intent also blocks future dispatch
across run IDs, even if the crash happened before a claim or after recording a
result. This deliberate false-positive possibility trades automatic recovery
for no blind duplicate work. An unfinished text attempt keeps that input
pending and is not sent again.

`reconciliation_required` means an operator must inspect the worker lock,
owned subprocesses, store state/lease, private logs and selected-audio hash.
There is no automatic reconciliation mutation or public repair endpoint here.
The parent must provide a separately reviewed operator recovery procedure for
unfinished journal intents. Do not delete the journal, clear a lease or invent
a fresh run ID as a recovery shortcut. Keep reservations until the existing
store/operator reconciliation establishes a known outcome.

Output inspections record the expected/observed selected-audio SHA-256 and
`manual_review_required`, `audio_hash_mismatch` or `audio_unverified`. They are
bounded to `max_per_run` files per pass, 128 MiB each, and reject redirected
paths. A matching hash proves identity, **not quality**. No content from the
worker's review directory is interpreted as permission to publish.

Automated audio auditing is **not qualified or enabled**. The existing worker's
large-v3 ASR evidence is not independent audio-model listening. Actual audio
model review plus independent ASR, source comparison, gaps/tails and accurate
corrected timing are still needed. `tools/creator_audio_review.py` is an
explicit operator tool, not invoked by this supervisor; its approximate ranges
are not publishable timestamps. Do not upload private audio under text-review
consent. The supervisor never calls `approve`, sets listening acknowledgements,
invents timed lines, or auto-rejects output. `review` remains reserved and
unpublished until the existing operator audit/approve-or-reject workflow runs.
Even qualified output approval does not bypass separate public moderation.

## Isolated Verification

```bash
PYTHONNOUSERSITE=1 conda run -n musia python -m unittest discover -s tests -p 'test_creator_supervisor.py' -v
```

Tests cover disabled defaults, resource and worker-lock deferral, supervisor
lock/concurrency, persistent action/expenditure bounds, finite polling, crashes
before/after claim and before text completion, no duplicate dispatch, consent,
input decisions/credit release, malformed model output, provider request bounds,
private evidence and the unchanged output gate. All audio bytes are synthetic;
worker rendering, GPU probing and provider clients are mocked. This is queue
orchestration verification, not a successful audio render or quality audit.
SEC-1/SEC-2 integration cases exercise the real worker/store boundary with a
mocked stage runner, including uncertain cleanup and suspended-owner failure.
Thread tests cover idle-sleep deletion followed by bounded dispatch, singleton
ownership during sleep, mutation-lock contention, an in-flight review returning
after account deletion, and stop requests during idle/contended polling.
