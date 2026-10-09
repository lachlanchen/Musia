"""Native/auth/billing contracts using isolated storage and explicit provider doubles."""

from dataclasses import replace
from pathlib import Path
import secrets
import tempfile
import unittest

from fastapi.testclient import TestClient

from musia.creator.api import Settings, create_app
from musia.creator.billing import Billing, PRODUCTS, Snapshot, Verification, account_token
from musia.creator.contracts import CreatorError
from musia.creator.native_auth import NativeExchange, NativeFlow, NativeStart, challenge
from musia.creator.store import Store


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.clock = [1791504000]
        self.store = Store(Path(self.temp.name), clock=lambda:self.clock[0])
        self.flow = NativeFlow(self.store)
        self.verifier = secrets.token_urlsafe(32)
        self.start = NativeStart(challenge=challenge(self.verifier), platform="apple")

    def tearDown(self):
        self.temp.cleanup()

    def ready(self):
        attempt = self.flow.start(self.start,"fixture")
        self.flow.browser(attempt,"binding")
        token = self.store.signed_in("https://issuer.example.test","fixture","Listener","link")
        self.owner = self.store.session(token)["owner"]
        result = self.flow.finish("binding",token)
        return token, NativeExchange(**result,verifier=self.verifier,platform="apple")

    def test_full_exchange_is_one_use_and_rotates_token(self):
        old, request = self.ready()
        new = self.flow.exchange(request)
        self.assertNotEqual(new["token"],old)
        self.assertEqual(self.store.session(new["token"])["owner"],self.owner)
        with self.assertRaises(CreatorError): self.store.session(old)
        with self.assertRaises(CreatorError): self.flow.exchange(request)

    def test_wrong_pkce_and_platform_and_code_do_not_deliver(self):
        _, request = self.ready()
        for changes in ({"verifier":"x"*43},{"platform":"android"},{"code":"x"*43}):
            with self.assertRaises(CreatorError): self.flow.exchange(request.model_copy(update=changes))
        self.assertIn("token",self.flow.exchange(request))

    def test_browser_attempt_cannot_be_rebound(self):
        attempt = self.flow.start(self.start,"fixture")
        self.flow.browser(attempt,"a")
        with self.assertRaises(CreatorError): self.flow.browser(attempt,"b")

    def test_expiry_and_deleted_owner_deny_delivery(self):
        _, request = self.ready()
        self.store.delete_account(self.owner)
        with self.assertRaises(CreatorError): self.flow.exchange(request)
        self.clock[0] += 601
        with self.assertRaises(CreatorError): self.flow.exchange(request)

    def test_stale_native_flow_cleanup_revokes_undelivered_session(self):
        old,_ = self.ready()
        self.clock[0] += 601
        self.flow.start(self.start,"fixture")
        with self.assertRaises(CreatorError): self.store.session(old)

    def test_bearer_api_and_native_start_do_not_need_browser_origin(self):
        class Auth:
            def providers(self): return {"password":True}
            def verify(self,session): pass
            def sign_out(self,session): pass
        token = self.store.signed_in("issuer","one","Listener","link")
        cfg = Settings(origin="https://musia.example.test",directory=self.store.directory)
        with TestClient(create_app(cfg,store=self.store,auth=Auth()),base_url=cfg.origin) as client:
            headers={"Authorization":"Bearer "+token,"X-Musia-Request":"1"}
            self.assertEqual(client.post("/creator/api/terms",json={},headers=headers).status_code,200)
            self.assertEqual(client.get("/creator/api/me",headers=headers).json()["account"]["name"],"Listener")
            self.assertEqual(client.post("/creator/auth/native/start",json=self.start.model_dump(),headers={"X-Musia-Request":"1"}).status_code,200)
            self.assertEqual(client.post("/creator/api/terms",json={},headers={"X-Musia-Request":"1"}).status_code,403)
            self.assertEqual(client.post("/creator/api/terms",json={},headers={**headers,"Origin":"https://evil.example"}).status_code,403)
            self.assertEqual(client.post("/creator/auth/logout",json={},headers=headers).status_code,200)
            self.assertEqual(client.post("/creator/api/terms",json={},headers=headers).status_code,401)

    def test_native_callback_ends_form_redirect_on_https(self):
        store = self.store
        class Auth:
            def providers(self): return {"password":True}
            def complete(self, url, binding, received):
                self.asserted = received is store and binding == "binding"
                return store.signed_in("issuer","native-return","Listener","link")
        auth = Auth()
        attempt = self.flow.start(self.start,"fixture")
        self.flow.browser(attempt,"binding")
        cfg = Settings(origin="https://musia.example.test",directory=self.store.directory)
        with TestClient(create_app(cfg,store=store,auth=auth),base_url=cfg.origin) as client:
            client.cookies.set("__Secure-musia_creator_binding","binding")
            response = client.get("/creator/auth/callback?code=fixture",follow_redirects=False)
            self.assertEqual(response.status_code,200)
            self.assertTrue(auth.asserted)
            self.assertNotIn("location",response.headers)
            self.assertIn('id="native-return"',response.text)
            self.assertIn('art.lazying.musia://auth?',response.text)
            self.assertIn('/creator/native-return.js',response.text)
            self.assertEqual(client.get('/creator/native-return.js').status_code,200)
            self.assertIn("no-store",response.headers['cache-control'])


class BillingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.clock = [1791504000]
        self.store = Store(Path(self.temp.name),clock=lambda:self.clock[0])
        token = self.store.signed_in("issuer","one","Owner","link")
        self.owner = self.store.session(token)["owner"]
        token = self.store.signed_in("issuer","two","Other","link2")
        self.other = self.store.session(token)["owner"]
        self.snapshot = Snapshot("apple","123",PRODUCTS[0]["appleProductId"],"creator","active",self.clock[0]+3600,"test",account_token(self.owner))
        parent = self
        class Provider:
            def fetch(self,reference): return parent.snapshot
            def acknowledge(self,snapshot):
                parent.ack_usage = parent.store.profile(parent.owner)["usage"]["tier"]
                if parent.ack_fails: raise CreatorError("billing_acknowledgement_pending",503)
        self.ack_fails = False
        self.provider = Provider()
        self.config = {"schema":1,"providers":{"apple":{"environment":"test","test_owners":[self.owner,self.other]},
                                                "google":{"environment":"test","test_owners":[self.owner,self.other]}}}
        self.billing = Billing(self.store,self.config,verifier_factory=lambda provider:self.provider)
        self.request = Verification(provider="apple",reference="123")

    def tearDown(self): self.temp.cleanup()

    def test_verified_receipt_grants_and_restore_does_not_multiply_credits(self):
        result = self.billing.verify(self.owner,self.request)
        self.assertTrue(result["verified"])
        self.assertEqual(self.ack_usage,"creator")
        self.assertEqual(self.store.profile(self.owner)["usage"]["limit"],20)
        self.billing.restore(self.owner)
        self.assertEqual(self.store.profile(self.owner)["usage"]["limit"],20)
        with self.store.db() as db:
            record = db.execute("SELECT * FROM subscriptions").fetchone()
            self.assertNotEqual(record["reference"],"123")
        self.assertEqual(self.store.profile(self.owner)["usage"]["source"],"verified_subscription")

    def test_receipt_not_transferable_and_unknown_product_denied(self):
        with self.assertRaisesRegex(CreatorError,"billing_account_mismatch"):
            self.billing.verify(self.other,self.request)
        self.snapshot = replace(self.snapshot,product="other.app.creator")
        with self.assertRaises(CreatorError): self.billing.verify(self.owner,self.request)
        self.assertEqual(self.store.profile(self.owner)["usage"]["tier"],"free")

    def test_expiry_refund_hold_and_cancel_paid_through(self):
        self.snapshot = replace(self.snapshot,state="canceled")
        self.billing.verify(self.owner,self.request)
        self.assertEqual(self.store.profile(self.owner)["usage"]["tier"],"creator")
        for state in ("hold","revoked","expired","pending"):
            self.snapshot = replace(self.snapshot,state=state)
            self.billing.verify(self.owner,self.request)
            self.assertEqual(self.store.profile(self.owner)["usage"]["tier"],"free")

    def test_stale_verification_closes_access_not_new_purchase_protection(self):
        self.billing.verify(self.owner,self.request)
        self.clock[0] += 901
        self.assertEqual(self.store.profile(self.owner)["usage"]["tier"],"free")
        status = self.billing.status(self.owner)
        self.assertFalse(status["capabilities"]["apple"]["purchase"])
        self.assertEqual(status["capabilities"]["apple"]["reason"],"manage_existing_subscription")
        self.billing.restore(self.owner)
        self.assertEqual(self.store.profile(self.owner)["usage"]["tier"],"creator")

    def test_ack_unknown_outcome_preserves_grant_for_same_receipt_retry(self):
        self.ack_fails = True
        with self.assertRaises(CreatorError): self.billing.verify(self.owner,self.request)
        self.assertEqual(self.store.profile(self.owner)["usage"]["tier"],"creator")
        self.ack_fails = False
        self.assertTrue(self.billing.verify(self.owner,self.request)["verified"])

    def test_test_receipt_cannot_grant_unlisted_account(self):
        self.config["providers"]["apple"]["test_owners"] = []
        with self.assertRaisesRegex(CreatorError,"billing_test_account_required"):
            self.billing.verify(self.owner,self.request)

    def test_catalog_and_restore_do_not_require_open_sales(self):
        status = self.billing.status(self.owner)
        self.assertEqual(len(status["products"]),2)
        self.assertFalse(status["capabilities"]["apple"]["purchase"])
        self.assertTrue(status["capabilities"]["apple"]["restore"])

    def test_sandbox_checkout_requires_no_charge_setup_and_exact_test_owner(self):
        cfg = self.config["providers"]["apple"]
        cfg.update(test_sales_enabled=True, no_charge_test_setup=True,
                   reconciliation_enabled=True, test_owners=[self.owner])
        billing = Billing(self.store,self.config,verifier_factory=lambda _:self.provider)
        self.assertTrue(billing.sales_available)
        self.assertTrue(billing.status(self.owner)["capabilities"]["apple"]["purchase"])
        self.assertFalse(billing.status(self.other)["capabilities"]["apple"]["purchase"])
        for field, value in (("no_charge_test_setup",False),("reconciliation_enabled",False),
                             ("test_owners",[]),("environment","live")):
            invalid = {"schema":1,"providers":{"apple":{**cfg,field:value}}}
            with self.assertRaises(ValueError): Billing(self.store,invalid)

    def test_live_receipt_rejected_by_test_configuration(self):
        self.snapshot = replace(self.snapshot,environment="live")
        with self.assertRaisesRegex(CreatorError,"billing_environment_mismatch"):
            self.billing.verify(self.owner,self.request)
        self.assertEqual(self.store.profile(self.owner)["usage"]["tier"],"free")

    def test_provider_fetch_cannot_resurrect_deleted_account(self):
        parent = self
        class Provider:
            def fetch(self,reference):
                parent.store.delete_account(parent.owner)
                return parent.snapshot
        self.billing.verifier_factory = lambda provider:Provider()
        with self.assertRaises(CreatorError): self.billing.verify(self.owner,self.request)

    def test_reconciliation_does_not_spend_user_daily_attempt_budget(self):
        self.billing.verify(self.owner,self.request)
        for _ in range(101): self.billing.restore(self.owner,reconciliation=True)
        with self.store.db() as db:
            count = db.execute("SELECT n FROM counters WHERE owner=? AND action='billing_verify'",(self.owner,)).fetchone()[0]
        self.assertEqual(count,1)


class MaintenanceTests(NativeTests):
    def test_purge_only_deleted_owner_and_wait_for_active_worker(self):
        import fcntl
        from musia.creator.contracts import Brief, Generate
        from musia.creator.maintenance import purge_deleted
        _, _ = self.ready()
        self.store.accept_terms(self.owner)
        job = self.store.submit(self.owner,"maintenance-test-001", Generate(
            brief=Brief(title="Test",lyrics="A song",caption="Piano"),rights_confirmed=True),
            invitation_required=False)
        folder = self.store.directory / "artifacts" / job["id"]
        folder.mkdir(parents=True)
        (folder / "song.wav").write_bytes(b"fixture")
        self.assertEqual(purge_deleted(self.store)["removed"],0)
        self.store.delete_account(self.owner)
        with (self.store.directory / "worker.lock").open("a") as lock:
            fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertTrue(purge_deleted(self.store)["waitingForWorker"])
            self.assertTrue(folder.exists())
        self.assertEqual(purge_deleted(self.store)["removed"],1)
        self.assertFalse(folder.exists())


if __name__ == "__main__": unittest.main()
