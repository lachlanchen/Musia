"""Offline catalog tests. All provider requests and credentials are fixtures."""
import contextlib
import copy
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import creator_google_catalog as m
import storelib as s


def product(tier, state="DRAFT"):
    return {"packageName": m.PACKAGE, "productId": "musia_" + tier, "basePlans": [{
        "basePlanId": "monthly", "state": state,
        "autoRenewingBasePlanType": {"billingPeriodDuration": "P1M"},
        "regionalConfigs": [{"regionCode": "US", "newSubscriberAvailability": True,
                             "price": {"currencyCode": "USD", "units": str(m.PLANS[tier][1]), "nanos": 990000000}}]}]}


class Response:
    def __init__(self, value, status=200, content=None):
        self.value = copy.deepcopy(value)
        self.status_code = status
        self.content = json.dumps(value).encode() if content is None else content

    def json(self):
        if self.content == b"not json":
            raise ValueError("private raw provider response")
        return copy.deepcopy(self.value)


class FakeSession:
    def __init__(self, case):
        self.case = case
        self.products = {"musia_" + t: product(t) for t in m.PLANS}
        self.offers = {}
        self.calls = []
        self._max_refresh_attempts = 2
        self.trust_env = True
        self.adapters = {}
        self.failure = None
        self.post_response = None
        self.get_response = None
        self.offers_response = None
        self.on_get = None
        self.on_post = None
        self.apply_activation = True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def mount(self, prefix, adapter):
        self.adapters[prefix] = adapter

    @property
    def posts(self):
        return [c for c in self.calls if c[0] != "GET"]

    def request(self, method, url, **kwargs):
        self.case.assertTrue(url.startswith(m.BASE + "/"))
        path = url[len(m.BASE):]
        self.calls.append((method, path, copy.deepcopy(kwargs)))
        route, query = urlsplit(path).path, parse_qs(urlsplit(path).query)
        self.case.assertEqual(kwargs["timeout"], (10, 45))
        self.case.assertIs(kwargs["allow_redirects"], False)
        if method == "GET":
            if self.on_get:
                self.on_get(route)
            if self.get_response is not None:
                return self.get_response
            if route.endswith("/offers"):
                pid = route.split("/")[2]
                self.case.assertEqual(query["pageSize"], ["1000"])
                if self.offers_response is not None:
                    return self.offers_response
                return Response(self.offers.get((pid, query.get("pageToken", [None])[0]), {}))
            self.case.assertTrue(route.startswith("/subscriptions/"))
            pid = route.split("/")[2]
            return Response(self.products[pid]) if pid in self.products else Response({}, 404)
        self.case.assertEqual(method, "POST")
        if route == "/pricing:convertRegionPrices":
            return Response({"regionVersion": {"version": "2026/10"}})
        if route == "/subscriptions":
            pid = query["productId"][0]
            self.case.assertEqual(query["regionsVersion.version"], ["2026/10"])
            self.products[pid] = copy.deepcopy(kwargs["json"])
            self.products[pid]["basePlans"][0]["state"] = "DRAFT"
            return Response(self.products[pid], 201)
        pid = route.split("/")[2]
        self.case.assertEqual(route, m.activation_path(pid))
        self.case.assertEqual(kwargs["json"], {})
        self.case.assertEqual(self._max_refresh_attempts, 0)
        self.case.assertFalse(self.trust_env)
        self.case.assertEqual(self.adapters["https://"].max_retries.total, 0)
        for target in self.products:
            for expected in ["/subscriptions/" + target,
                             f"/subscriptions/{target}/basePlans/monthly/offers?pageSize=1000"]:
                self.case.assertIn(("GET", expected), [(c[0], c[1]) for c in self.calls[:-1]])
        record = s.read_json(self.case.journal(pid))
        self.case.assertEqual(record["state"], "started", "Intent must be durable before POST")
        self.case.assertEqual(record["path"], route)
        self.case.assertEqual(record["body"], {})
        self.case.assertEqual(self.case.journal(pid).stat().st_mode & 0o777, 0o600)
        if self.failure == "before":
            raise TimeoutError("private raw provider response")
        if self.failure == "crash":
            raise KeyboardInterrupt()
        if self.apply_activation:
            self.products[pid]["basePlans"][0]["state"] = "ACTIVE"
        if self.on_post:
            self.on_post(pid)
        if self.failure == "after":
            raise TimeoutError("private raw provider response")
        return self.post_response if self.post_response is not None else Response(self.products[pid])


class GoogleCatalogTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.runtime = Path(temporary.name)
        self.key = self.runtime / "key.json"
        self.config_path = self.runtime / "billing.json"
        self.google = {"bundle_id": m.PACKAGE, "app_id": m.APP_ID, "environment": "test",
                       "sales_enabled": False, "test_sales_enabled": False, "service_account_file": str(self.key)}
        self.config = {"schema": 1, "providers": {"google": self.google}}
        s.write_private(self.key, {"private_key": "fixture only"})
        self.save_config()
        self.api = FakeSession(self)
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(m, "RUNTIME", self.runtime))
        stack.enter_context(patch.object(s, "RUNTIME", self.runtime))
        stack.enter_context(patch.object(socket.socket, "connect", side_effect=AssertionError("Offline tests only")))
        stack.enter_context(patch("urllib.request.urlopen", side_effect=AssertionError("No real provider access")))
        self.factory = stack.enter_context(patch.object(m, "GoogleVerifier"))
        self.factory.return_value.session.return_value = self.api

    def save_config(self):
        s.write_private(self.config_path, self.config)

    def activate(self):
        return m.activate_base_plans(self.key, self.config_path)

    def journal(self, pid="musia_creator"):
        return m.activation_journal(self.runtime / "creator-google-catalog", pid)

    def assert_refused(self):
        with self.assertRaises((s.GuardError, OSError, ValueError, TypeError, AttributeError)):
            self.activate()
        self.assertFalse(self.api.posts)

    def test_default_provider_read_only_for_existing_and_missing_products(self):
        for products in [self.api.products, {}]:
            self.api.products = products
            self.assertEqual(len(m.catalog(self.key)["products"]), 2)
            self.assertFalse(self.api.posts)

    def test_apply_drafts_creation_is_unchanged_and_never_activates(self):
        self.api.products = {}
        result = m.catalog(self.key, apply=True)
        self.assertEqual([p["state"] for p in result["products"]], ["DRAFT", "DRAFT"])
        self.assertEqual(len(self.api.posts), 4)
        self.assertFalse(any(":activate" in c[1] for c in self.api.posts))
        for pid, value in self.api.products.items():
            self.assertEqual(m.approved_plan(value, pid)["state"], "DRAFT")

    def test_success_is_exact_one_shot_with_closed_gates_and_private_journals(self):
        before = self.config_path.read_bytes()
        result = self.activate()
        self.assertEqual(len(self.api.posts), 2)
        self.assertEqual([c[1] for c in self.api.posts], [m.activation_path("musia_" + t) for t in m.PLANS])
        self.assertEqual([p["action"] for p in result["products"]], ["activated_verified"] * 2)
        for field in ["salesEnabled", "testSalesEnabled", "licenseTestingVerified", "purchasesAuthorized", "releaseChanged"]:
            self.assertIs(result[field], False)
        for pid in self.api.products:
            self.assertEqual(s.read_json(self.journal(pid))["state"], "active")
            self.assertEqual(self.journal(pid).stat().st_mode & 0o777, 0o600)
        self.assertEqual(before, self.config_path.read_bytes())
        result = self.activate()
        self.assertEqual([p["action"] for p in result["products"]], ["verified_skipped"] * 2)
        self.assertEqual(len(self.api.posts), 2)

    def test_already_active_is_validated_and_skipped_without_journal(self):
        for value in self.api.products.values():
            value["basePlans"][0]["state"] = "ACTIVE"
        self.assertEqual([p["action"] for p in self.activate()["products"]], ["verified_skipped"] * 2)
        self.assertFalse(self.api.posts)
        self.assertFalse(self.journal().exists())

    def test_second_plan_validation_blocks_entire_batch(self):
        original = copy.deepcopy(self.api.products["musia_studio"])
        changes = [
            (lambda p: p.update(packageName="other")), (lambda p: p.update(productId="other")),
            (lambda p: p.update(archived=True)), (lambda p: p.update(basePlans=[])),
            (lambda p: p["basePlans"].append(copy.deepcopy(p["basePlans"][0]))),
        ]
        for key, value in [("state", "INACTIVE"), ("state", "STATE_UNSPECIFIED"), ("basePlanId", "annual"),
                           ("prepaidBasePlanType", {}), ("installmentsBasePlanType", {}),
                           ("otherRegionsConfig", {"newSubscriberAvailability": True}), ("otherRegionsConfig", None)]:
            changes.append(lambda p, k=key, v=value: p["basePlans"][0].update({k: v}))
        for key, value in [("billingPeriodDuration", "P1Y"), ("legacyCompatibleSubscriptionOfferId", "intro")]:
            changes.append(lambda p, k=key, v=value: p["basePlans"][0]["autoRenewingBasePlanType"].update({k: v}))
        for key, value in [("currencyCode", "CAD"), ("units", "9"), ("units", 29), ("nanos", 0)]:
            changes.append(lambda p, k=key, v=value: p["basePlans"][0]["regionalConfigs"][0]["price"].update({k: v}))
        changes += [lambda p: p["basePlans"][0]["regionalConfigs"][0].update(regionCode="CA"),
                    lambda p: p["basePlans"][0]["regionalConfigs"][0].update(newSubscriberAvailability=False),
                    lambda p: p["basePlans"][0]["regionalConfigs"].append({"regionCode": "CA", "newSubscriberAvailability": False})]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                self.api.products["musia_studio"] = copy.deepcopy(original)
                change(self.api.products["musia_studio"])
                self.assert_refused()
                self.assertFalse(self.journal().exists())

    def test_active_product_with_wrong_price_still_refused(self):
        self.api.products["musia_studio"]["basePlans"][0]["state"] = "ACTIVE"
        self.api.products["musia_studio"]["basePlans"][0]["regionalConfigs"][0]["price"]["units"] = "9"
        self.assert_refused()

    def test_any_existing_offer_blocks_all_activation(self):
        for value in [{"subscriptionOffers": [{"state": "DRAFT"}]}, {"subscriptionOffers": None}, {"unexpected": []}]:
            self.api.offers[("musia_studio", None)] = value
            self.assert_refused()

    def test_empty_204_offer_lists_allow_exact_activation(self):
        self.api.offers_response = Response(None, 204, content=b"")
        result = self.activate()
        self.assertEqual([p["action"] for p in result["products"]], ["activated_verified"] * 2)
        self.assertEqual(len(self.api.posts), 2)

    def test_empty_200_or_nonempty_204_offer_response_is_not_accepted(self):
        for response in [Response(None, 200, content=b""), Response({}, 204)]:
            self.api.offers_response = response
            self.assert_refused()

    def test_empty_204_product_get_is_not_an_empty_offer_list(self):
        self.api.get_response = Response(None, 204, content=b"")
        self.assert_refused()

    def test_empty_204_activation_response_remains_unknown(self):
        self.api.post_response = Response(None, 204, content=b"")
        self.assert_unknown_then_reconcile(True)

    def test_empty_paginated_offers_are_read_fully(self):
        self.api.offers[("musia_studio", None)] = {"nextPageToken": "page +/2"}
        self.api.offers[("musia_studio", "page +/2")] = {"subscriptionOffers": []}
        self.activate()
        self.assertTrue(any("pageToken=page+%2B%2F2" in c[1] for c in self.api.calls))

    def test_offers_on_later_page_or_invalid_pagination_block(self):
        self.api.offers[("musia_studio", None)] = {"nextPageToken": "next"}
        for value in [{"subscriptionOffers": [{"offerId": "intro"}]}, {"nextPageToken": "next"}, {"nextPageToken": 1}]:
            self.api.offers[("musia_studio", "next")] = value
            self.assert_refused()

    def test_unbounded_offer_pagination_fails_closed(self):
        for index in range(21):
            self.api.offers[("musia_creator", str(index) if index else None)] = {"nextPageToken": str(index + 1)}
        self.assert_refused()

    def test_config_identity_environment_and_literal_closed_gates_required(self):
        original = copy.deepcopy(self.google)
        changes = [("bundle_id", "other"), ("app_id", str(m.APP_ID)), ("app_id", 1),
                   ("environment", "live"), ("service_account_file", "/another/key.json")]
        changes += [(gate, value) for gate in ["sales_enabled", "test_sales_enabled"] for value in [True, None, 0, "false"]]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                self.config["providers"]["google"] = dict(original, **{key: value})
                self.save_config()
                self.assert_refused()
        for key in original:
            self.config["providers"]["google"] = dict(original)
            del self.config["providers"]["google"][key]
            self.save_config()
            self.assert_refused()
        self.factory.assert_not_called()

    def test_missing_and_malformed_config_fail_before_provider_session(self):
        with self.assertRaises(s.GuardError):
            m.activate_base_plans(self.key, None)
        for value in [{}, {"schema": 2, "providers": {}}, {"schema": 1, "providers": {"google": []}}, b"invalid"]:
            s.write_private(self.config_path, value)
            self.assert_refused()
        self.factory.assert_not_called()

    def test_config_and_key_must_be_private_regular_non_symlinks(self):
        for path in [self.key, self.config_path]:
            data = path.read_bytes()
            path.chmod(0o644)
            self.assert_refused()
            path.chmod(0o600)
            target = path.with_suffix(".copy")
            s.write_private(target, data)
            path.unlink()
            path.symlink_to(target)
            self.assert_refused()
            path.unlink()
            s.write_private(path, data)
        self.factory.assert_not_called()

    def test_config_change_during_preflight_blocks_even_all_active_run(self):
        for value in self.api.products.values():
            value["basePlans"][0]["state"] = "ACTIVE"
        def change(_):
            self.google["test_sales_enabled"] = True
            self.save_config()
        self.api.on_get = change
        self.assert_refused()

    def test_config_change_during_first_post_stops_second_activation(self):
        def change(_):
            self.google["sales_enabled"] = True
            self.save_config()
        self.api.on_post = change
        with self.assertRaises(s.GuardError):
            self.activate()
        self.assertEqual(len(self.api.posts), 1)
        self.assertEqual(s.read_json(self.journal())["state"], "unknown")

    def assert_unknown_then_reconcile(self, applied):
        with self.assertRaisesRegex(s.GuardError, "outcome unconfirmed"):
            self.activate()
        self.assertEqual(len(self.api.posts), 1)
        self.assertEqual(s.read_json(self.journal())["state"], "unknown")
        self.assertFalse(self.journal("musia_studio").exists())
        count = len(self.api.calls)
        self.api.failure = None
        self.api.post_response = None
        if not applied:
            with self.assertRaisesRegex(s.GuardError, "no POST retry"):
                self.activate()
            self.assertEqual(len(self.api.posts), 1)
            self.assertTrue(all(c[0] == "GET" for c in self.api.calls[count:]))
        else:
            result = self.activate()
            self.assertEqual([p["action"] for p in result["products"]], ["verified_skipped", "activated_verified"])
            self.assertEqual([c[1] for c in self.api.posts], [m.activation_path("musia_" + t) for t in m.PLANS])

    def test_timeout_before_response_never_retries_unknown_post(self):
        self.api.failure = "before"
        self.assert_unknown_then_reconcile(False)

    def test_timeout_after_mutation_reconciles_only_on_later_invocation(self):
        self.api.failure = "after"
        self.assert_unknown_then_reconcile(True)

    def test_non_json_post_is_unknown_and_later_active_readback_skips(self):
        self.api.post_response = Response(None, content=b"not json")
        self.assert_unknown_then_reconcile(True)

    def test_redirect_post_response_is_unknown_and_not_followed(self):
        self.api.post_response = Response({}, 302)
        self.assert_unknown_then_reconcile(True)

    def test_empty_post_response_is_not_success(self):
        self.api.post_response = Response(None, content=b"")
        self.assert_unknown_then_reconcile(True)

    def test_wrong_post_resource_is_not_success(self):
        self.api.post_response = Response(product("studio", "ACTIVE"))
        self.assert_unknown_then_reconcile(True)

    def test_post_active_response_requires_active_readback(self):
        self.api.apply_activation = False
        self.api.post_response = Response(product("creator", "ACTIVE"))
        self.assert_unknown_then_reconcile(False)

    def test_crash_leaves_started_journal_that_blocks_retry(self):
        self.api.failure = "crash"
        with self.assertRaises(KeyboardInterrupt):
            self.activate()
        self.assertEqual(s.read_json(self.journal())["state"], "started")
        self.api.failure = None
        with self.assertRaisesRegex(s.GuardError, "no POST retry"):
            self.activate()
        self.assertEqual(len(self.api.posts), 1)

    def test_bad_get_response_never_mutates(self):
        for response in [Response({}, 404), Response({}, 500), Response(None, content=b"not json"),
                         Response([]), Response({"error": {}}), Response({}, content=b"x" * 1048577)]:
            self.api.get_response = response
            self.assert_refused()
            self.assertFalse(self.journal().exists())

    def test_existing_journal_for_second_plan_blocks_any_new_post(self):
        s.write_private(self.journal("musia_studio"), {"state": "unknown", "package": m.PACKAGE,
                        "path": m.activation_path("musia_studio"), "body": {}})
        self.assert_refused()

    def test_mismatched_journal_and_private_permissions_are_refused(self):
        self.api.products["musia_creator"]["basePlans"][0]["state"] = "ACTIVE"
        record = {"state": "active", "package": m.PACKAGE, "path": m.activation_path("musia_creator"), "body": {}}
        for key, value in [("package", "other"), ("path", "/edits"), ("body", {"extra": 1}), ("state", "rejected")]:
            s.write_private(self.journal(), dict(record, **{key: value}))
            self.assert_refused()
        s.write_private(self.journal(), record)
        self.journal().chmod(0o644)
        self.assert_refused()

    def test_final_readback_cannot_claim_first_plan_active_after_external_change(self):
        def change(pid):
            if pid == "musia_studio":
                self.api.products["musia_creator"]["basePlans"][0]["state"] = "DRAFT"
        self.api.on_post = change
        with self.assertRaisesRegex(s.GuardError, "final readback"):
            self.activate()
        self.assertEqual(len(self.api.posts), 2)
        self.assertFalse((self.runtime / "creator-google-catalog/activation-readback.json").exists())
        with self.assertRaisesRegex(s.GuardError, "no POST retry"):
            self.activate()
        self.assertEqual(len(self.api.posts), 2)

    def test_lock_prevents_concurrent_provider_session(self):
        with s.lock("creator-google-catalog-activation"):
            self.assert_refused()
        self.factory.assert_not_called()

    def test_mutation_allowlist_and_retry_policy_fail_closed(self):
        for method, path in [("POST", "/edits"), ("PATCH", "/subscriptions/musia_creator"),
                             ("POST", "/subscriptions/musia_other/basePlans/monthly:activate")]:
            with self.assertRaises(s.GuardError):
                m.activation_request(self.api, method, path)
        self.assertFalse(self.api.calls)
        del self.api._max_refresh_attempts
        self.assert_refused()
        self.assertFalse(self.api.calls)

    def test_cli_default_and_modes_and_sanitized_errors(self):
        key = ["--service-account-file", str(self.key)]
        with contextlib.redirect_stdout(io.StringIO()), patch.object(m, "catalog", return_value={}) as read:
            self.assertEqual(m.main(key), 0)
            read.assert_called_once_with(self.key, False)
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                m.main(key + ["--apply-drafts", "--activate-base-plans"])
            self.assertEqual(m.main(key + ["--activate-base-plans"]), 1)
            self.assertEqual(m.main(key + ["--billing-config", str(self.config_path)]), 1)
        self.api.failure = "after"
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            self.assertEqual(m.main(key + ["--activate-base-plans", "--billing-config", str(self.config_path)]), 1)
        self.assertNotIn("private raw provider response", error.getvalue())


if __name__ == "__main__":
    unittest.main()
