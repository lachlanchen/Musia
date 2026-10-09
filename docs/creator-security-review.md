# Creator Security Review

Date: 2026-10-09. Scope: current working-tree `musia/creator/{api,auth,native_auth,store,billing,billing_providers,worker,review}.py`.
This is a source review, not an assessment of deployed bytes. The operator reports
an active real pilot with billing off. No deployed configuration, private secrets,
receipts, accounts, services or databases were inspected or changed. No heavy jobs
or store calls are authorized by this review.

Initial ownership was limited to this document and
`tests/test_creator_security_regression.py`. The parent subsequently approved
narrow SEC-1 through SEC-4 fixes in `store.py`, `worker.py`, and `billing.py`.
Those local fixes are implemented; no native, deployment, supervisor or other
agent-owned files were edited by this reviewer. The parent owns commit and
redeployment. Findings below preserve the pre-fix evidence and original line
references; current implementations are summarized afterward.

## Findings Before Fixes

### SEC-1 [P1] Suspension during a render wedges the global queue

- Code: `store.py:272-284`, `store.py:435-440`, `store.py:260-265`;
  worker error fallback at `worker.py:105-109`.
- Proof from source: `suspend()` cancels only queued work. A running job keeps
  its lease; both success and failure calls to `result()` reject its now-inactive
  owner before updating the row. Every subsequent `claim()` refuses to run any
  user's job while that row remains `running`. The normal worker completion
  cannot retire it, and the existing maintenance command does not reconcile it.
- Trigger: an operator suspends an account whose render is already running.
  This is a moderation availability bug, not an unauthenticated suspension API.
- Observed offline: completion raises `sign_in_required`, leaving the job
  `running/reserved` rather than retiring its valid worker lease.
- Fix: separate owner authorization to publish from worker authorization to
  settle an already-issued lease. Once execution is confirmed finished, retire
  suspended-owner work without publishing it and release the reservation exactly
  once. Keep uncertain execution outcomes blocked for explicit reconciliation.
- Regression: `test_suspended_owner_completion_does_not_wedge_global_queue`.

### SEC-2 [P1] Unknown worker termination is refunded as a definite failure

- Code: `worker.py:24-34`, `worker.py:107-109`, `store.py:278-279`.
- Proof from source: if a stage times out and `os.killpg()` fails, `run()` raises
  the cleanup error. `work_once()` still calls `result(error=...)`, changing the
  job to `failed/released`. Another approved job is then claimable even though
  termination was never established. Separately, if the leader already exited,
  `poll() is not None` skips all process-group cleanup; leader exit alone does
  not establish that descendants have exited.
- Impact: the ledger's single-render invariant can disagree with live execution,
  and an unknown outcome receives a credit refund. The resource check is useful
  but does not prove ownership or termination of an orphaned process group.
- Fix: explicitly distinguish known stopped failure from uncertain cleanup.
  Preserve the reservation and a blocking `interrupted` state on uncertainty;
  reconcile it before another claim. Handle the whole owned process group even
  when its leader exits, without targeting unrelated processes.
- Regressions: `test_cleanup_failure_keeps_credit_and_global_claim_reserved`,
  `test_exited_leader_does_not_skip_process_group_cleanup`.
- Evidence limit: these inject process outcomes; they do not start a real child
  or demonstrate that an orphan has occurred in the pilot.
- Observed offline: injected termination failure produces `failed/released` and
  the next owner's job is claimable. A separately injected exited leader results
  in zero process-group cleanup calls.

### SEC-3 [P1, billing gate] First verification can resurrect a replaced token

- Code: `billing.py:151-155`, `billing.py:172-190`;
  Google replacement normalization at `billing_providers.py:166-168`.
- Reproducible interleaving: verification A for an unseen old token starts;
  verification B for its replacement commits first. B's `UPDATE` of the absent
  old subscription affects zero rows. A then arrives with its previously fetched
  active snapshot: there is no old row/revision to reject it, so A inserts an
  active subscription. A Studio old token can override a Creator replacement in
  `Store.allowance()`. The existing-row case correctly rejects the stale result.
- Fix: persist replacement lineage/tombstones even when the replaced token has
  not been stored, and check that lineage transactionally before any insert or
  update. Preserve owner binding and monotonic ordering across the whole chain.
- Regression: `test_unseen_replaced_token_cannot_arrive_late_and_restore_higher_tier`.
- Evidence limit: deterministic verifier doubles prove the ledger race, not
  Google's timing or a real purchase exploit. No live transaction was attempted.
  This is a pre-billing release gate; sales off is not itself a receipt forgery.
- Observed offline: the late old-token result grants `studio` after the new
  `creator` subscription commits. The pre-existing-old-row control passes.

### SEC-4 [P2, billing gate] Terminal history can starve paid reconciliation

- Code: `billing.py:204-224`; freshness cutoff at `store.py:155-156`.
- Proof from source: `restore()` always selects ten rows by expiry, regardless
  of state; `reconcile()` uses that same limited selection. Ten refunded/revoked
  historical subscriptions with later stored expiry timestamps can permanently
  crowd out a still-active row. Reconciliation reports the owner checked while
  that row goes stale; after 900 seconds the account falls back to Free.
- Fix: prioritize all entitlement-bearing or unresolved records, with bounded
  pagination/cursors if necessary. A fixed limit without progress must not
  silently exclude active records or count them as reconciled.
- Regression: `test_terminal_history_cannot_starve_active_subscription_reconciliation`.
- Evidence limit: synthetic but accepted ledger history; no claim that an
  existing pilot account has this history.
- Observed offline: reconciliation fetches only the ten revoked records and
  returns `{"checked": 1, "retry": 0}` without fetching the active token.

## Boundaries Checked

- No confirmed cross-owner content/credit access or bearer/cookie fallback was
  found in the reviewed routes. Public audio authorization is checked before
  file serving, including range/HEAD routing; no arbitrary filesystem/worker
  command endpoint was found.
- Reservations, owner-bound idempotency, worker claims and native code exchange
  use serialized SQLite transactions. Tests include wrong-lease rejection and
  one-use concurrent native exchange.
- Auth checks locally active sessions and central subject/issuer binding. The
  central SDK's implementation and real issuer behavior are outside this review.
- Billing checks normalized product, owner token, environment and freshness;
  tests include wrong-account rejection before acknowledgement and a refunded
  Google order overriding an active subscription response.
- `review.py` requires an audio-bound operator audit and bounded ordered sung
  lines. Operator attestations are not proof that human listening happened;
  there is no public review/approval route in this API.
- Restoring verified purchases with sales disabled is intentional in existing
  tests. It is not reported as a payment bypass. Deployment's actual provider
  configuration was not read.
- A concurrent agent added `supervisor.py` during review. Its current typed
  `WorkerOutcomeUnknown` handling and SEC-1/SEC-2 integration regressions were
  included in the combined test run. The rest of that new module is outside this
  review's code ownership.

## Approved Fixes

- SEC-1: `Store.result()` authorizes settlement by the existing worker lease,
  independent of whether the owner is still active. Inactive-owner completion
  becomes failed/released without storing or publishing audio. Wrong leases
  remain rejected. Deleted-owner success remains an API error after safe
  retirement; a confirmed failure can be settled by the valid lease.
- SEC-2: `WorkerOutcomeUnknown` preserves `running/reserved` and blocks further
  claims. `run()` creates a new session, uses Linux `waitid(WNOWAIT)` to retain
  the leader PID until signals finish, and checks that the leader is still our
  child with PGID = SID = PID and not the worker's own group. Cleanup sends no
  destructive signal after reaping; it probes group disappearance afterward.
  Foreign/reaped groups are never signalled. Uncertain cleanup requires explicit
  operator reconciliation; there is no automatic rerender or refund.
- SEC-2 deletion edge: account deletion still scrubs content immediately but
  retains running/interrupted claims and reservations until execution is known
  stopped. Deleting an account cannot bypass the unknown-outcome queue block.
- SEC-3: an additive `subscription_replacements` table durably binds old-token
  hashes to owner/successor hashes, including previously unseen tokens. Tombstones
  reject both in-flight stale results and fresh retries after restart. Known old
  rows expire atomically even if their last verification started later. Foreign
  owners and conflicting replacement chains are rejected. Restore skips replaced
  records. This records new verified lineage, not a retrospective repair of
  provider history; no live billing database was accessed.
- SEC-4: reconciliation uses ten-row keyset pages through every nonterminal,
  nonreplaced subscription up to the initial rowid high-water mark, not ten
  subscriptions total. Failed rows do not prevent later pages from being visited;
  new inserts are deferred to the next pass. User-triggered restore remains
  bounded to ten prioritized rows; server reconciliation covers all active rows.
- `resource_check()` and its resource-limit tests are unchanged by this reviewer.
  Existing concurrent native/account changes are preserved.

## Supervisor Handoff

Peer: Hypatia `01a11f16-37dd-7140-89ca-146516cb2e4e`, shared Musia workspace.
No peer-message tool was exposed to this review session; the parent can relay
this contract. The shared supervisor source now has explicit typed handling and
tests for this contract, which this reviewer ran without editing them:

- `WorkerOutcomeUnknown` means keep the dispatch unresolved and reserved; never
  retry it automatically, even when another transition obscures job state.
- Known stopped failure, including owner suspension, is retired by the worker.
- Valid lease reconciliation remains possible only after the operator establishes
  that the owned execution is stopped. No timeout alone authorizes a refund.
- Parent owns deployment/commit; billing remains off until separately qualified.

## Verification

Tests use temporary 0700 directories, synthetic identities and explicit billing
configuration. Network connections, process creation, waitid and group signals
are denied/mocked in the isolated-store fixture. At the parent's explicit request,
a separate Linux integration test starts exactly one disposable sleeping Python
child with a clean environment and a 0.5-second stage timeout. It verifies
PID = PGID = SID, timeout cleanup, child reaping and group disappearance, with
exact-child fallback cleanup. No GPU/model or live endpoint is used; temporary
SQLite files, logs and test billing keys are removed afterward.

Before fixes, strict mode reproduced five assertions across four findings in both
runtimes; seven nearby controls passed. After fixes all expected-failure markers
and the strict-mode switch were removed. The security file now has 23 ordinary
tests, including the real timeout test:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 conda run -n musia python -m unittest discover -s tests -p 'test_creator_security_regression.py' -v
PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 /home/lachlan/.local/share/musia/creator-server/venv/bin/python -m unittest discover -s tests -p 'test_creator_security_regression.py' -v
```

Results in both the `musia` Python 3.10 environment and the existing
`creator-server` Python 3.12 environment:

| Selection | Result |
| --- | --- |
| New security file | 23 pass, no expected failures |
| Creator + native/billing + security + worker/resource + supervisor | 130 pass in each runtime, no expected failures |

The combined suites ran with `os.environ.clear()` before discovery to prevent
existing tests from selecting ambient private billing/auth/text-provider
configuration. No ingress, live OAuth, store or render test was run by this
reviewer; the disposable-child timeout is the only real process integration test.
Both runtimes emitted an existing Starlette/httpx deprecation warning; no package
was changed. An initial test-fixture use of Python 3.11's `enterContext` was
replaced with `ExitStack` for Python 3.10 compatibility before final verification.

Parent separately reported 143 full creator tests and a real short-child worker
run passing before the final timeout test was added. Those are parent-reported
results, not extra live checks performed by this reviewer. Source changes and
tests are local only; parent release QA and deployment remain separate gates.

Completion: SEC-1 through SEC-4 are fixed and regression-verified in the local
working tree. Final combined run durations were 6.592 seconds (musia Python 3.10)
and 8.592 seconds (creator-server Python 3.12). `git diff --check` passed for the
owned scope. No test child, server or GUI stack was left running. No commit,
native edit, private-secret access or deployment was performed by this reviewer.
