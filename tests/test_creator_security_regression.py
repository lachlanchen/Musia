"""Offline security tests; one explicit disposable-child test, no network/GPU/secrets."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, nullcontext
from dataclasses import replace
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from musia.creator.api import Settings, create_app
from musia.creator.auth import CentralAuth
from musia.creator.billing import Billing, PRODUCTS, Snapshot, Verification, account_token
from musia.creator.billing_providers import GoogleVerifier
from musia.creator.contracts import Brief, CreatorError, Generate
from musia.creator.native_auth import NativeExchange, NativeFlow, NativeStart, challenge
from musia.creator.store import Store
from musia.creator.worker import WorkerOutcomeUnknown, run, work_once


class IsolatedStore(unittest.TestCase):
    def setUp(self):
        patches = ExitStack()
        self.addCleanup(patches.close)
        patches.enter_context(patch.dict(os.environ, {}, clear=True))
        for target in ("socket.create_connection", "socket.socket.connect", "socket.socket.connect_ex",
                       "subprocess.Popen", "os.killpg", "os.waitid"):
            patches.enter_context(patch(target, side_effect=AssertionError("External I/O forbidden")))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = 1791504000
        self.store = Store(Path(self.temp.name), clock=lambda: self.now)
        self.token, self.owner = self.account("owner")
        self.other_token, self.other = self.account("other")

    def account(self, subject):
        token = self.store.signed_in("https://issuer.example.test", subject, subject, "fake-link-" + subject)
        owner = self.store.session(token)["owner"]
        self.store.accept_terms(owner)
        return token, owner

    def queued(self, owner, key):
        self.now += 1
        request = Generate(brief=Brief(title="Fixture", lyrics="A test line", caption="Piano"),
                           rights_confirmed=True)
        job = self.store.submit(owner, key, request, invitation_required=False)
        self.store.approve_input(job["id"])
        return job["id"]

    def job(self, job):
        with self.store.db() as db:
            return dict(db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone())


class WorkerSecurityTests(IsolatedStore):
    def setUp(self):
        super().setUp()
        patches = ExitStack()
        self.addCleanup(patches.close)
        for name in ("getpgid", "getsid"):
            patches.enter_context(patch("musia.creator.worker.os." + name, return_value=424242))
        patches.enter_context(patch("musia.creator.worker.os.getpgrp", return_value=1))
        patches.enter_context(patch("musia.creator.worker.os.waitid", return_value=SimpleNamespace(si_code=os.CLD_EXITED, si_status=0)))

    def test_suspended_owner_completion_does_not_wedge_global_queue(self):
        """SEC-1: a valid worker lease must be able to retire nonpublishable work."""
        job = self.queued(self.owner, "first")
        claim = self.store.claim()
        next_job = self.queued(self.other, "second")
        self.store.suspend(self.owner)
        settlement_error = None
        try:
            self.store.result(job, claim["lease"], error="known_worker_failure")
        except CreatorError as exc:
            settlement_error = exc.code
        row = self.job(job)
        self.assertIn(row["state"], ("failed", "cancelled"),
                      f"Completed worker left {row['state']}; error={settlement_error}")
        self.assertEqual(row["credit"], "released")
        self.assertEqual(self.store.claim()["id"], next_job)

    def test_cleanup_failure_keeps_credit_and_global_claim_reserved(self):
        """SEC-2: failure to terminate a process is not a known failed render."""
        job = self.queued(self.owner, "first")
        self.queued(self.other, "second")
        process = Mock(pid=424242)
        process.wait.return_value = 0
        with patch("musia.creator.worker.resource_check"), \
             patch("musia.creator.worker.subprocess.Popen", return_value=process), \
             patch("musia.creator.worker.wait_leader", side_effect=subprocess.TimeoutExpired("fixture", 7200)), \
             patch("musia.creator.worker.os.killpg", side_effect=PermissionError("fixture cleanup failure")) as kill:
            with self.assertRaises(WorkerOutcomeUnknown):
                work_once(self.store)
        kill.assert_called_once_with(process.pid, signal.SIGTERM)
        row = self.job(job)
        next_claim = self.store.claim()
        self.assertEqual((row["credit"], next_claim["id"] if next_claim else None), ("reserved", None),
                         "Unknown live process outcome must not refund or admit another GPU job")

    def test_exited_leader_does_not_skip_process_group_cleanup(self):
        """SEC-2: leader exit alone does not prove its child group has exited."""
        process = Mock(pid=424242)
        process.wait.return_value = 1
        with patch("musia.creator.worker.subprocess.Popen", return_value=process), \
             patch("musia.creator.worker.os.waitid", return_value=SimpleNamespace(si_code=os.CLD_EXITED, si_status=1)), \
             patch("musia.creator.worker.os.killpg", side_effect=[None, None, ProcessLookupError()]) as kill:
            with self.assertRaises(RuntimeError):
                run(["never-executed-fixture"], self.store.directory / "worker.log")
        self.assertTrue(kill.called, "No attempt to probe or terminate the remaining child group")

    def test_wrong_lease_cannot_release_another_owners_running_work(self):
        job = self.queued(self.owner, "first")
        self.store.claim()
        self.queued(self.other, "second")
        with self.assertRaisesRegex(CreatorError, "worker_lease_lost"):
            self.store.result(job, "forged-lease", error="failed")
        self.assertEqual(self.job(job)["credit"], "reserved")
        self.assertIsNone(self.store.claim())

    def test_suspended_success_never_becomes_publishable(self):
        job = self.queued(self.owner, "suspend-success")
        lease = self.store.claim()["lease"]
        self.store.suspend(self.owner)
        self.store.result(job, lease, audio="fixture", audio_hash="a" * 64, review="fixture")
        self.assertEqual((self.job(job)["state"], self.job(job)["credit"]), ("failed", "released"))
        self.assertIsNone(self.job(job)["audio"])
        self.assertEqual(self.store.songs(), [])

    def test_deleted_owner_keeps_lease_until_confirmed_completion(self):
        job = self.queued(self.owner, "delete-running")
        lease = self.store.claim()["lease"]
        next_job = self.queued(self.other, "next")
        self.store.delete_account(self.owner)
        self.assertEqual((self.job(job)["state"], self.job(job)["credit"]), ("running", "reserved"))
        self.assertEqual(self.job(job)["brief"], "{}")
        self.assertIsNone(self.store.claim())
        with self.assertRaisesRegex(CreatorError, "worker_lease_lost"):
            self.store.result(job, "wrong-lease", error="confirmed-stopped")
        self.store.result(job, lease, error="confirmed-stopped")
        self.assertEqual(self.store.claim()["id"], next_job)

    def test_foreign_or_reaped_group_is_never_signalled(self):
        process = Mock(pid=424242)
        for target, values in (("os.getpgid", {"return_value": 777}),
                               ("os.getsid", {"return_value": 777}),
                               ("os.getpgrp", {"return_value": 424242}),
                               ("os.waitid", {"side_effect": ChildProcessError("fixture reaped child")})):
            with self.subTest(target=target), \
                 patch("musia.creator.worker.subprocess.Popen", return_value=process), \
                 patch("musia.creator.worker." + target, **values), \
                 patch("musia.creator.worker.os.killpg") as kill:
                with self.assertRaises(WorkerOutcomeUnknown):
                    run(["fixture"], self.store.directory / "worker.log")
                kill.assert_not_called()
                process.wait.assert_not_called()

    def test_group_signals_precede_leader_reap_and_use_owned_session(self):
        process = Mock(pid=424242)
        events = []
        process.wait.side_effect = lambda **_: events.append("reap") or 0

        def signal_group(pid, sig):
            self.assertEqual(pid, process.pid)
            events.append(sig)
            if sig == 0:
                raise ProcessLookupError()

        with patch("musia.creator.worker.subprocess.Popen", return_value=process) as spawn, \
             patch("musia.creator.worker.os.killpg", side_effect=signal_group):
            run(["fixture"], self.store.directory / "worker.log")
        self.assertTrue(spawn.call_args.kwargs["start_new_session"])
        self.assertEqual(events, [signal.SIGTERM, signal.SIGKILL, "reap", 0])

    def test_timeout_with_confirmed_cleanup_releases_once(self):
        job = self.queued(self.owner, "timeout")
        process = Mock(pid=424242)
        process.wait.return_value = 0
        with patch("musia.creator.worker.resource_check"), \
             patch("musia.creator.worker.subprocess.Popen", return_value=process), \
             patch("musia.creator.worker.wait_leader", side_effect=[subprocess.TimeoutExpired("fixture", 1), 0]), \
             patch("musia.creator.worker.os.killpg", side_effect=[None, None, ProcessLookupError()]):
            with self.assertRaises(subprocess.TimeoutExpired):
                work_once(self.store)
        self.assertEqual((self.job(job)["state"], self.job(job)["credit"]), ("failed", "released"))

    def test_surviving_group_after_sigkill_keeps_claim_reserved(self):
        job = self.queued(self.owner, "surviving-group")
        self.queued(self.other, "next")
        process = Mock(pid=424242)
        process.wait.return_value = 0
        with patch("musia.creator.worker.resource_check"), \
             patch("musia.creator.worker.subprocess.Popen", return_value=process), \
             patch("musia.creator.worker.wait_leader", return_value=0), \
             patch("musia.creator.worker.time.monotonic", side_effect=[0, 6]), \
             patch("musia.creator.worker.os.killpg"):
            with self.assertRaises(WorkerOutcomeUnknown):
                work_once(self.store)
        self.assertEqual((self.job(job)["state"], self.job(job)["credit"]), ("running", "reserved"))
        self.assertIsNone(self.store.claim())


@unittest.skipUnless(sys.platform.startswith("linux"), "Linux owned-process-group contract")
class RealWorkerCleanupTests(unittest.TestCase):
    def test_real_sleeping_child_timeout_is_reaped_and_group_is_gone(self):
        """One disposable Python child; no GPU, model, network or live service."""
        spawned = []
        popen = subprocess.Popen

        def capture(*args, **kwargs):
            child = popen(*args, **kwargs)
            spawned.append(child)
            return child

        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {"PATH": "/usr/bin:/bin"}, clear=True), \
             patch("musia.creator.worker.subprocess.Popen", side_effect=capture):
            log = Path(directory) / "worker.log"
            try:
                with self.assertRaises(subprocess.TimeoutExpired):
                    run([sys.executable, "-I", "-c",
                         "import os,time; print(os.getpid(),os.getpgrp(),os.getsid(0),flush=True); time.sleep(30)"],
                        log, timeout=0.5)
                self.assertEqual(len(spawned), 1)
                child = spawned[0]
                self.assertEqual(log.read_text().strip(), f"{child.pid} {child.pid} {child.pid}")
                self.assertIsNotNone(child.returncode)
                with self.assertRaises(ProcessLookupError):
                    os.killpg(child.pid, 0)
                with self.assertRaises(ChildProcessError):
                    os.waitpid(child.pid, os.WNOHANG)
            finally:
                # Only the captured, still-unreaped child may be killed on a
                # test failure; never signal a possibly reused process group.
                for child in spawned:
                    if child.returncode is None:
                        child.kill()
                        child.wait(timeout=5)


class BillingSecurityTests(IsolatedStore):
    def setUp(self):
        super().setUp()
        self.snapshots = {}
        self.provider = Mock()
        self.provider.fetch.side_effect = lambda reference: self.snapshots[reference]
        self.billing = Billing(self.store, {"schema": 1, "providers": {
            "google": {"environment": "test", "test_owners": [self.owner]}
        }}, verifier_factory=lambda _: self.provider)

    def snapshot(self, reference, **changes):
        value = Snapshot("google", reference, PRODUCTS[0]["googleProductId"], "creator", "active",
                         self.now + 3600, "test", account_token(self.owner))
        self.snapshots[reference] = replace(value, **changes)
        return self.snapshots[reference]

    def verify(self, reference):
        return self.billing.verify(self.owner, Verification(provider="google", reference=reference))

    def interleaved_replacement(self):
        old = self.snapshot("old-token", tier="studio", product=PRODUCTS[1]["googleProductId"])
        new = self.snapshot("new-token", replaces="old-token")

        def fetch(reference):
            if reference == old.reference:
                # Pause the first fetch after its operation begins; commit the
                # replacement before delivering the older provider snapshot.
                self.verify(new.reference)
                return old
            return new

        self.provider.fetch.side_effect = fetch

    def test_unseen_replaced_token_cannot_arrive_late_and_restore_higher_tier(self):
        """SEC-3: replacements need durable tombstones for not-yet-stored tokens."""
        self.interleaved_replacement()
        try:
            self.verify("old-token")
        except CreatorError as exc:
            self.assertEqual(exc.code, "billing_verification_superseded")
        self.assertEqual(self.store.profile(self.owner)["usage"]["tier"], "creator",
                         "Late old-token result restored Studio after Creator replacement committed")

    def test_existing_replaced_token_rejects_the_same_late_snapshot(self):
        self.snapshot("old-token", tier="studio", product=PRODUCTS[1]["googleProductId"])
        self.verify("old-token")
        self.interleaved_replacement()
        with self.assertRaisesRegex(CreatorError, "billing_verification_superseded"):
            self.verify("old-token")
        self.assertEqual(self.store.profile(self.owner)["usage"]["tier"], "creator")

    def test_replacement_tombstone_survives_restart_and_blocks_fresh_old_token_retry(self):
        self.snapshot("old-token", tier="studio", product=PRODUCTS[1]["googleProductId"])
        self.snapshot("new-token", replaces="old-token")
        self.verify("new-token")
        self.billing = Billing(self.store, self.billing.config, verifier_factory=lambda _: self.provider)
        with self.assertRaisesRegex(CreatorError, "billing_verification_superseded"):
            self.verify("old-token")
        self.provider.fetch.reset_mock()
        self.billing.restore(self.owner, reconciliation=True)
        self.assertEqual([call.args[0] for call in self.provider.fetch.call_args_list], ["new-token"])
        self.assertEqual(self.store.profile(self.owner)["usage"]["tier"], "creator")

    def test_replacement_cannot_expire_another_accounts_purchase(self):
        self.billing.config["providers"]["google"]["test_owners"].append(self.other)
        self.snapshot("foreign-old", account_token=account_token(self.other))
        self.billing.verify(self.other, Verification(provider="google", reference="foreign-old"))
        self.snapshot("bad-replacement", replaces="foreign-old")
        with self.assertRaisesRegex(CreatorError, "billing_account_mismatch"):
            self.verify("bad-replacement")
        self.assertEqual(self.store.profile(self.other)["usage"]["tier"], "creator")
        self.assertEqual(self.store.profile(self.owner)["usage"]["tier"], "free")

    def test_terminal_history_cannot_starve_active_subscription_reconciliation(self):
        """SEC-4: the first ten rows must not exclude an active paid record forever."""
        self.snapshot("current-token")
        self.verify("current-token")
        for index in range(10):
            reference = f"revoked-history-{index}"
            self.snapshot(reference, state="revoked", expires=self.now + 7200 + index)
            self.verify(reference)
        self.now += 901
        self.provider.fetch.reset_mock()
        result = self.billing.reconcile()
        fetched = [call.args[0] for call in self.provider.fetch.call_args_list]
        self.assertIn("current-token", fetched, f"Reconciliation reports {result} but skips the paid record")
        self.assertEqual(self.store.profile(self.owner)["usage"]["tier"], "creator")

    def test_reconciliation_visits_every_active_record_across_bounded_pages(self):
        references = [f"active-{index}" for index in range(25)]
        for reference in references:
            self.snapshot(reference)
            self.verify(reference)
        self.now += 901
        self.provider.fetch.reset_mock()
        self.assertEqual(self.billing.reconcile(), {"checked": 1, "retry": 0})
        self.assertEqual([call.args[0] for call in self.provider.fetch.call_args_list], references)
        with self.store.db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM subscriptions WHERE verified=?", (self.now,)).fetchone()[0], 25)

    def test_reconciliation_failure_on_one_page_does_not_skip_later_pages(self):
        references = [f"active-{index}" for index in range(21)]
        for reference in references:
            self.snapshot(reference)
            self.verify(reference)
        self.now += 901

        def fetch(reference):
            if reference == "active-10":
                raise CreatorError("billing_provider_unavailable", 503)
            return self.snapshots[reference]

        self.provider.fetch.side_effect = fetch
        self.provider.fetch.reset_mock()
        self.assertEqual(self.billing.reconcile(), {"checked": 0, "retry": 1})
        self.assertEqual([call.args[0] for call in self.provider.fetch.call_args_list], references)

    def test_fetched_purchase_for_other_account_never_grants_or_acknowledges(self):
        self.snapshot("foreign-token", account_token=account_token(self.other))
        with self.assertRaisesRegex(CreatorError, "billing_account_mismatch"):
            self.verify("foreign-token")
        self.provider.acknowledge.assert_not_called()
        self.assertEqual(self.store.profile(self.owner)["usage"]["tier"], "free")
        with self.store.db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM subscriptions").fetchone()[0], 0)

    def test_google_refunded_order_overrides_active_subscription_and_skips_ack(self):
        verifier = GoogleVerifier({"environment": "test"})
        subscription = {
            "kind": "androidpublisher#subscriptionPurchaseV2", "testPurchase": {},
            "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
            "acknowledgementState": "ACKNOWLEDGEMENT_STATE_PENDING",
            "externalAccountIdentifiers": {"obfuscatedExternalAccountId": account_token(self.owner)},
            "lineItems": [{"productId": "musia_creator", "offerDetails": {"basePlanId": "monthly"},
                           "expiryTime": "2026-10-10T00:00:00Z", "latestSuccessfulOrderId": "GPA.1234-5678"}],
        }
        order = {"orderId": "GPA.1234-5678", "purchaseToken": "fixture-token", "state": "REFUNDED",
                 "lineItems": [{"productId": "musia_creator"}]}
        with patch.object(verifier, "session", return_value=nullcontext(Mock())) as session, \
             patch.object(verifier, "response", side_effect=[subscription, order]):
            snapshot = verifier.fetch("fixture-token")
            verifier.acknowledge(snapshot)
        self.assertEqual(snapshot.state, "revoked")
        self.assertEqual(session.call_count, 1)


class AuthenticationSecurityTests(IsolatedStore):
    def test_native_code_concurrent_exchange_delivers_one_session(self):
        flow = NativeFlow(self.store)
        verifier = "v" * 43
        attempt = flow.start(NativeStart(challenge=challenge(verifier), platform="apple"), "fixture-peer")
        flow.browser(attempt, "fixture-binding")
        completion = flow.finish("fixture-binding", self.token)
        request = NativeExchange(**completion, verifier=verifier, platform="apple")

        def exchange(_):
            try:
                return flow.exchange(request)["token"]
            except CreatorError as exc:
                return exc.code

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(exchange, range(2)))
        self.assertEqual(outcomes.count("sign_in_failed"), 1)
        token = next(value for value in outcomes if value != "sign_in_failed")
        self.assertEqual(self.store.session(token)["owner"], self.owner)
        with self.assertRaises(CreatorError):
            self.store.session(self.token)

    def test_bad_bearer_cannot_fall_back_to_valid_browser_cookie(self):
        auth = Mock()
        auth.providers.return_value = {"password": True}
        billing = Billing(self.store, {"schema": 1, "providers": {}})
        settings = Settings(origin="https://musia.example.test", directory=self.store.directory)
        app = create_app(settings, store=self.store, auth=auth, producer=SimpleNamespace(available=False), billing=billing)
        with TestClient(app, base_url=settings.origin) as client:
            client.cookies.set("__Secure-musia_creator", self.token, domain="musia.example.test", path="/creator")
            self.assertEqual(client.get("/creator/api/jobs").status_code, 200)
            for value in ("Basic fake", "Bearer invalid-fixture-token"):
                response = client.get("/creator/api/jobs", headers={"Authorization": value})
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json(), {"detail": "sign_in_required"})

    def test_central_introspection_is_subject_bound_and_rejects_wrong_issuer(self):
        # Construct the adapter with doubles, never invoke its private config loader.
        auth = CentralAuth.__new__(CentralAuth)
        auth.error = type("FakeLinkError", (Exception,), {})
        auth.vault, auth.client = Mock(), Mock()
        auth.vault.session.return_value = (SimpleNamespace(access_token="fixture-access-token"), None)
        auth.client.introspect.return_value = SimpleNamespace(issuer="https://wrong.example.test")
        with self.assertRaisesRegex(CreatorError, "reconnect_account"):
            auth.verify(self.store.session(self.token))
        auth.vault.session.assert_called_once_with("fake-link-owner", expected_subject="owner")
        auth.client.introspect.assert_called_once_with("fixture-access-token", expected_subject="owner")


if __name__ == "__main__":
    unittest.main()
