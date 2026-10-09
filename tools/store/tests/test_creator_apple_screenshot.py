"""Offline screenshot protocol tests, never real credentials or native captures."""
import base64
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import socket
import struct
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import storelib as s
# Tests never load real signing keys; importing the catalog needs only this stub.
fake_jwt = types.ModuleType("jwt")
fake_jwt.encode = lambda *args, **kwargs: "fixture-jwt"
with patch.dict(sys.modules, {"jwt": fake_jwt}):
    import creator_apple_screenshot as m


def png_fixture(color=(255, 0, 0)):
    """Tiny synthetic protocol fixture, not a review capture."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    rows = (b"\x00" + bytes(color) * 8) * 16
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 16, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


class Response:
    def __init__(self, value=None, status=200, content=None):
        self.status_code = status
        self.value = copy.deepcopy(value)
        self.content = json.dumps(value).encode() if content is None else content

    def json(self):
        if self.content == b"non-json private provider response":
            raise ValueError("private response must not leak")
        return copy.deepcopy(self.value)


class Session:
    def __init__(self, server):
        self.server = server
        self.trust_env = True
        self.auth = ("unwanted", "auth")
        self.headers = {"Authorization": "unwanted inherited header"}
        self.cookies = {"unwanted": "cookie"}
        self.adapters = {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def mount(self, prefix, adapter):
        self.adapters[prefix] = adapter

    def request(self, method, url, **kwargs):
        case = self.server.case
        case.assertFalse(self.trust_env)
        case.assertIsNone(self.auth)
        case.assertEqual(self.headers, {})
        case.assertEqual(self.cookies, {})
        case.assertEqual(self.adapters["https://"].max_retries.total, 0)
        case.assertIs(kwargs["allow_redirects"], False)
        case.assertIs(kwargs["verify"], True)
        case.assertEqual(kwargs["timeout"], (10, 45))
        return self.server.request(method, url, kwargs)


class Server:
    def __init__(self, case):
        self.case = case
        self.calls = []
        self.apps = [{"id": m.APP, "type": "apps", "attributes": {"bundleId": m.BUNDLE}}]
        self.groups = [{"id": "group", "attributes": {"referenceName": m.GROUP}}]
        self.products = [{"id": tier, "type": "subscriptions", "attributes": {
            "productId": f"{m.BUNDLE}.{tier}.monthly", "subscriptionPeriod": "ONE_MONTH", "state": "MISSING_METADATA"}}
            for tier in m.PLANS]
        self.images = {}
        self.parts = {}
        self.failure = None
        self.on_reserve = None
        self.on_commit = None
        self.on_screenshot_get = None
        self.commit_state = "COMPLETE"
        self.reserve_response = None
        self.commit_response = None
        self.asset_status = 200
        self.get_response = None
        self.missing_status = 404
        self.paginate = False

    @property
    def mutations(self):
        return [call for call in self.calls if call[0] != "GET"]

    def operations(self, size):
        split = size // 2
        return [{"method": "PUT", "url": "https://store-030.blobstore.apple.com/assets-test/image?"
                 f"Signature=fixture-signed-url&AWSAccessKeyId=fixture&Expires={int(time.time()) + 3600}&partNumber={index}",
                 "offset": offset, "length": length, "requestHeaders": [{"name": "Content-Type", "value": "image/png"}]}
                for index, (offset, length) in enumerate([(0, split), (split, size - split)])]

    def make_image(self, tier, state="AWAITING_UPLOAD"):
        return {"type": m.KIND, "id": "image-" + tier,
                "attributes": {"fileName": f"musia-{tier}-review-{self.case.sha}.png", "fileSize": len(self.case.payload),
                               "sourceFileChecksum": self.case.md5 if state in {"COMPLETE", "UPLOAD_COMPLETE"} else None,
                               "uploadOperations": self.operations(len(self.case.payload)),
                               "assetDeliveryState": {"state": state}},
                "relationships": {"subscription": dict(m.relationship("subscriptions", tier), links={"related": "unused"})}}

    def check_intent(self, tier, method, path, body):
        record = s.read_json(m.journal_path(tier))
        self.case.assertEqual(record["state"], {"POST": "reserve_started", "PATCH": "commit_started"}[method])
        self.case.assertEqual(record["request"], {"method": method, "path": path, "body": body})
        self.case.assertEqual(record["identity"]["sha256"], self.case.sha)
        self.case.assertEqual(m.journal_path(tier).stat().st_mode & 0o777, 0o600)

    def request(self, method, url, kwargs):
        self.calls.append((method, url, copy.deepcopy(kwargs)))
        parsed = urlsplit(url)
        path, query = parsed.path, parse_qs(parsed.query)
        if parsed.hostname != "api.appstoreconnect.apple.com":
            self.case.assertEqual(method, "PUT")
            self.case.assertEqual(parsed.hostname, "store-030.blobstore.apple.com")
            self.case.assertNotIn("authorization", {key.lower() for key in kwargs["headers"]})
            self.case.assertNotIn("fixture-jwt", json.dumps(kwargs["headers"]))
            record = s.read_json(m.journal_path(self.case.tier))
            self.case.assertEqual(record["state"], "upload_started")
            self.parts[int(query["partNumber"][0])] = kwargs["data"]
            if self.failure == "asset":
                raise TimeoutError("private asset URL must not leak")
            return Response(status=self.asset_status)
        self.case.assertEqual(kwargs["headers"], {"Authorization": "Bearer fixture-jwt"})
        if method == "GET":
            if self.get_response is not None:
                return self.get_response
            if path == "/v1/apps":
                self.case.assertEqual(query["filter[bundleId]"], [m.BUNDLE])
                return Response({"data": self.apps})
            if path == "/v1/bundleIds":
                return Response({"data": [{"id": "bundle", "attributes": {"identifier": m.BUNDLE}}]})
            if path == f"/v1/apps/{m.APP}/subscriptionGroups":
                return Response({"data": self.groups})
            if path == "/v1/subscriptionGroups/group/subscriptions":
                if self.paginate and "cursor" not in query:
                    return Response({"data": self.products[:1], "links": {"next": m.API + path + "?cursor=next"}})
                return Response({"data": self.products[1:] if self.paginate else self.products})
            if path.endswith("/appStoreReviewScreenshot"):
                tier = path.split("/")[3]
                self.case.assertEqual(query["include"], ["subscription"])
                if self.on_screenshot_get:
                    self.on_screenshot_get(tier)
                if tier not in self.images:
                    return Response({"data": None}, self.missing_status)
                return Response({"data": self.images[tier]})
            for product in self.products:
                if path == "/v1/subscriptions/" + product["id"]:
                    return Response({"data": product})
            raise AssertionError("Unexpected read endpoint: " + path)
        body = kwargs["json"]
        if method == "POST":
            self.case.assertEqual(path, m.RESOURCE)
            tier = body["data"]["relationships"]["subscription"]["data"]["id"]
            self.case.assertIn(tier, m.PLANS)
            self.check_intent(tier, method, path, body)
            self.case.assertEqual(body, {"data": {"type": m.KIND,
                "attributes": {"fileName": f"musia-{tier}-review-{self.case.sha}.png", "fileSize": len(self.case.payload)},
                "relationships": {"subscription": m.relationship("subscriptions", tier)}}})
            if self.failure == "reserve_before":
                raise TimeoutError("private provider response")
            if self.failure == "crash":
                raise KeyboardInterrupt()
            self.images[tier] = self.make_image(tier)
            if self.on_reserve:
                self.on_reserve(self.images[tier])
            if self.failure == "reserve_after":
                raise TimeoutError("private provider response")
            return self.reserve_response or Response({"data": self.images[tier]}, 201)
        self.case.assertEqual(method, "PATCH", "No deletes, reviews, prices, availability or purchases")
        tier = body["data"]["id"].removeprefix("image-")
        self.case.assertEqual(path, m.RESOURCE + "/image-" + tier)
        self.check_intent(tier, method, path, body)
        self.case.assertEqual(body, {"data": {"type": m.KIND, "id": "image-" + tier,
                                            "attributes": {"uploaded": True, "sourceFileChecksum": self.case.md5}}})
        self.case.assertEqual(b"".join(self.parts[i] for i in sorted(self.parts)), self.case.payload)
        self.images[tier]["attributes"].update(sourceFileChecksum=self.case.md5, assetDeliveryState={"state": self.commit_state})
        if self.on_commit:
            self.on_commit(self.images[tier])
        if self.failure == "commit_after":
            raise TimeoutError("private provider response")
        return self.commit_response or Response({"data": self.images[tier]})


class ScreenshotTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.runtime = self.root / "store/.runtime"
        self.tier = "creator"
        self.payload = png_fixture()
        self.sha = hashlib.sha256(self.payload).hexdigest()
        self.md5 = hashlib.md5(self.payload, usedforsecurity=False).hexdigest()
        self.png = self.runtime / "fixture.png"
        s.write_private(self.png, self.payload)
        key = self.runtime / "fixture.p8"
        s.write_private(key, b"fake key, jwt encoder mocked")
        self.cfg = {"bundle_id": s.BUNDLE, "apple_team": s.TEAM, "google_developer_id": s.DEVELOPER,
                    "asc_key_path": str(key), "asc_issuer": "fixture", "asc_key_id": "fixture"}
        s.write_private(self.runtime / "config.json", self.cfg)
        s.write_private(self.root / "store/release.json", dict(self.cfg, apple_app_id=m.APP, formal_submission_enabled=False))
        self.server = Server(self)
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(s, "ROOT", self.root))
        stack.enter_context(patch.object(s, "RUNTIME", self.runtime))
        stack.enter_context(patch.object(m, "RUNTIME", self.runtime))
        self.assertIs(m.lock, s.lock)
        stack.enter_context(patch.dict("os.environ", {"MUSIA_STORE_CONFIG": str(self.runtime / "config.json")}))
        stack.enter_context(patch.object(socket.socket, "connect", side_effect=AssertionError("Offline tests only")))
        stack.enter_context(patch("urllib.request.urlopen", side_effect=AssertionError("No real provider access")))
        stack.enter_context(patch.object(m.jwt, "encode", return_value="fixture-jwt"))
        self.sessions = stack.enter_context(patch.object(m.requests, "Session", side_effect=lambda: Session(self.server)))

    def upload(self, confirm=False):
        return m.upload(self.tier, self.png, self.sha, confirm)

    def assert_refused(self):
        with self.assertRaises((s.GuardError, OSError, ValueError, TypeError, KeyError)):
            self.upload(confirm=True)
        self.assertFalse(self.server.mutations)

    def test_default_is_readback_only_and_does_not_create_intent(self):
        result = self.upload()
        self.assertEqual(result["state"], "plan_only")
        self.assertEqual(result["action"], "would_reserve")
        self.assertFalse(result["processingComplete"])
        self.assertFalse(self.server.mutations)
        self.assertFalse(m.journal_path(self.tier).exists())

    def test_confirm_reserves_uploads_exact_ranges_commits_md5_and_reads_complete(self):
        result = self.upload(confirm=True)
        self.assertEqual(result["state"], "COMPLETE")
        self.assertTrue(result["processingComplete"])
        self.assertEqual([c[0] for c in self.server.mutations], ["POST", "PUT", "PUT", "PATCH"])
        for key in ["appReviewChanged", "subscriptionReviewSubmitted", "purchasesAuthorized"]:
            self.assertIs(result[key], False)
        record = s.read_json(m.journal_path(self.tier))
        self.assertEqual(record["state"], "complete")
        self.assertEqual(record["readback"]["attributes"]["sourceFileChecksum"], self.md5)
        self.assertEqual(m.journal_path(self.tier).stat().st_mode & 0o777, 0o600)
        self.assertEqual(m.journal_path(self.tier).parent.stat().st_mode & 0o777, 0o700)
        self.assertNotIn("fixture-jwt", json.dumps(record))
        self.assertNotIn("fixture-signed-url", json.dumps(result))
        self.assertEqual(self.upload(confirm=True)["action"], "verified_readback")
        self.assertEqual(len(self.server.mutations), 4)

    def test_studio_uses_separate_exact_subscription_and_stable_journal(self):
        self.tier = "studio"
        result = self.upload(confirm=True)
        self.assertEqual(result["product"], m.BUNDLE + ".studio.monthly")
        self.assertFalse(m.journal_path("creator").exists())
        self.assertTrue(m.journal_path("studio").exists())

    def test_processing_pending_is_not_claimed_complete_and_later_get_resolves(self):
        self.server.commit_state = "UPLOAD_COMPLETE"
        result = self.upload(confirm=True)
        self.assertFalse(result["processingComplete"])
        self.assertEqual(result["state"], "UPLOAD_COMPLETE")
        self.assertEqual(s.read_json(m.journal_path(self.tier))["state"], "processing")
        self.server.images[self.tier]["attributes"]["assetDeliveryState"]["state"] = "COMPLETE"
        self.assertTrue(self.upload()["processingComplete"])
        self.assertEqual(len(self.server.mutations), 4)

    def test_existing_complete_exact_screenshot_skips_all_writes(self):
        self.server.images[self.tier] = self.server.make_image(self.tier, "COMPLETE")
        self.assertTrue(self.upload(confirm=True)["processingComplete"])
        self.assertFalse(self.server.mutations)
        self.assertFalse(m.journal_path(self.tier).exists())

    def test_missing_relationship_200_null_is_read_only_plan(self):
        self.server.missing_status = 200
        self.assertEqual(self.upload()["state"], "plan_only")
        self.assertFalse(self.server.mutations)

    def test_catalog_pagination_is_followed_before_reservation(self):
        self.server.paginate = True
        self.upload(confirm=True)
        self.assertTrue(any("cursor=next" in call[1] for call in self.server.calls))

    def test_wrong_app_group_subscription_and_period_refuse_before_writes(self):
        original = copy.deepcopy((self.server.apps, self.server.groups, self.server.products))
        changes = [lambda: self.server.apps[0].update(id="other-app"),
                   lambda: self.server.apps[0]["attributes"].update(bundleId="other.app"),
                   lambda: self.server.groups[0]["attributes"].update(referenceName="Other"),
                   lambda: self.server.groups.append(copy.deepcopy(self.server.groups[0])),
                   lambda: self.server.products.pop(),
                   lambda: self.server.products[1]["attributes"].update(productId="other.subscription"),
                   lambda: self.server.products[1]["attributes"].update(subscriptionPeriod="ONE_YEAR"),
                   lambda: self.server.products[0].update(id="../appStoreVersions")]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                self.server.apps, self.server.groups, self.server.products = copy.deepcopy(original)
                change()
                self.assert_refused()

    def test_submitted_or_unknown_subscription_state_cannot_receive_new_image(self):
        for state in ["WAITING_FOR_REVIEW", "IN_REVIEW", "APPROVED", "UNKNOWN", None]:
            self.server.products[0]["attributes"]["state"] = state
            self.assert_refused()

    def test_unapproved_tier_never_contacts_provider(self):
        with self.assertRaises(s.GuardError):
            m.upload("other", self.png, self.sha, True)
        self.assertFalse(self.server.calls)

    def test_wrong_hash_or_changed_bytes_cannot_reach_provider(self):
        for sha in ["0" * 64, self.sha.upper(), "bad"]:
            with self.assertRaises(s.GuardError):
                m.upload(self.tier, self.png, sha, True)
        s.write_private(self.png, b"changed")
        self.assert_refused()
        self.assertFalse(self.server.calls)

    def test_png_must_be_private_regular_and_not_symlink(self):
        self.png.chmod(0o644)
        self.assert_refused()
        self.png.unlink()
        other = self.runtime / "other.png"
        s.write_private(other, self.payload)
        self.png.symlink_to(other)
        self.assert_refused()
        self.assertFalse(self.server.calls)

    def test_invalid_image_even_with_matching_hash_refuses(self):
        for payload in [b"not a PNG", self.payload[:-12], b""]:
            s.write_private(self.png, payload)
            self.sha = hashlib.sha256(payload).hexdigest()
            self.assert_refused()
        self.assertFalse(self.server.calls)

    def test_native_bytes_are_snapshotted_before_reservation(self):
        self.server.on_reserve = lambda _: s.write_private(self.png, b"file changed after hash check")
        self.assertTrue(self.upload(confirm=True)["processingComplete"])
        self.assertEqual(b"".join(self.server.parts.values()), self.payload)

    def test_existing_different_or_unconfirmed_image_never_replaced(self):
        original = self.server.make_image(self.tier, "COMPLETE")
        for field, value in [("fileName", "other.png"), ("fileSize", 1), ("sourceFileChecksum", "0" * 32),
                             ("sourceFileChecksum", None), ("assetDeliveryState", {"state": "FAILED"}),
                             ("assetDeliveryState", {"state": "AWAITING_UPLOAD"}),
                             ("assetDeliveryState", {"state": "UNKNOWN"}),
                             ("assetDeliveryState", {"state": "COMPLETE", "errors": [{"code": "FAILED"}]})]:
            self.server.images[self.tier] = copy.deepcopy(original)
            self.server.images[self.tier]["attributes"][field] = value
            self.assert_refused()

    def test_existing_screenshot_must_belong_to_selected_subscription(self):
        self.server.images[self.tier] = self.server.make_image(self.tier, "COMPLETE")
        self.server.images[self.tier]["relationships"]["subscription"] = m.relationship("subscriptions", "studio")
        self.assert_refused()

    def test_only_documented_signed_https_asset_urls_allowed(self):
        good = self.server.operations(len(self.payload))[0]["url"]
        self.assertEqual(m.asset_url(good), good)
        bad = [good.replace("https:", "http:"), good.replace("store-030.blobstore.apple.com", "api.appstoreconnect.apple.com"),
               good.replace(".apple.com", ".apple.com.evil.test"), good.replace("store-030", "evil@store-030"),
               good.replace(".com/", ".com:80/"), good.replace(".com/", ".com./"),
               good.replace("/assets-", "/other-"), good + "#fragment", good + "\n", good + "\\bad",
               good.replace("Signature=fixture-signed-url", "Signature="), good.replace("Signature=", "Unsigned="),
               good.replace("AWSAccessKeyId=fixture", "AWSAccessKeyId="), good + "&Signature=duplicate",
               good.replace(parse_qs(urlsplit(good).query)["Expires"][0], "1")]
        for url in bad:
            with self.subTest(url=url):
                with self.assertRaises((s.GuardError, ValueError)):
                    m.asset_url(url)

    def test_asset_headers_cannot_carry_auth_cookies_host_or_injection(self):
        for name, value in [("Authorization", "Bearer fixture-jwt"), ("authorization", "other"),
                            ("Cookie", "private"), ("Host", "evil.test"), ("Proxy-Authorization", "other"),
                            ("Content-Type", "image/png\r\nAuthorization: Bearer x"), ("Content-Length", "1"),
                            ("Content-MD5", "wrong")]:
            with self.subTest(name=name):
                image = self.server.make_image(self.tier)
                image["attributes"]["uploadOperations"][0]["requestHeaders"].append({"name": name, "value": value})
                with self.assertRaises(s.GuardError):
                    m.upload_operations(image, self.payload)
        self.assertFalse(self.server.calls)

    def test_correct_part_length_and_md5_headers_are_preserved(self):
        image = self.server.make_image(self.tier)
        for part in image["attributes"]["uploadOperations"]:
            data = self.payload[part["offset"]:part["offset"] + part["length"]]
            part["requestHeaders"] += [{"name": "Content-Length", "value": str(len(data))},
                {"name": "Content-MD5", "value": base64.b64encode(hashlib.md5(data, usedforsecurity=False).digest()).decode()}]
        self.assertEqual(len(m.upload_operations(image, self.payload)), 2)

    def test_invalid_method_ranges_and_missing_operations_are_rejected(self):
        changes = [lambda ops: ops.clear(), lambda ops: ops[0].update(method="POST"),
                   lambda ops: ops[0].update(offset=-1), lambda ops: ops[0].update(offset=True),
                   lambda ops: ops[0].update(length=0), lambda ops: ops[0].update(length=len(self.payload) + 1),
                   lambda ops: ops[1].update(offset=0), lambda ops: ops[1].update(offset=ops[1]["offset"] + 1),
                   lambda ops: ops.pop(), lambda ops: ops[0].update(requestHeaders=None)]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                image = self.server.make_image(self.tier)
                change(image["attributes"]["uploadOperations"])
                with self.assertRaises(s.GuardError):
                    m.upload_operations(image, self.payload)

    def test_all_operations_validated_before_any_asset_bytes_leave(self):
        def corrupt(image):
            image["attributes"]["uploadOperations"][1]["url"] = "https://evil.test/asset"
        self.server.on_reserve = corrupt
        with self.assertRaises(s.GuardError):
            self.upload(confirm=True)
        self.assertEqual([c[0] for c in self.server.mutations], ["POST"])
        self.assertEqual(s.read_json(m.journal_path(self.tier))["state"], "unknown")

    def assert_failed_attempt_never_retried(self, failure, expected_methods, complete=False):
        self.server.failure = failure
        with self.assertRaisesRegex(s.GuardError, "outcome unconfirmed"):
            self.upload(confirm=True)
        self.assertEqual([c[0] for c in self.server.mutations], expected_methods)
        self.assertEqual(s.read_json(m.journal_path(self.tier))["state"], "unknown")
        self.server.failure = None
        if complete:
            self.assertTrue(self.upload(confirm=True)["processingComplete"])
        else:
            with self.assertRaises(s.GuardError):
                self.upload(confirm=True)
        self.assertEqual([c[0] for c in self.server.mutations], expected_methods)

    def test_reservation_timeout_before_acceptance_never_reposts(self):
        self.assert_failed_attempt_never_retried("reserve_before", ["POST"])

    def test_reservation_timeout_after_acceptance_is_readback_only(self):
        self.assert_failed_attempt_never_retried("reserve_after", ["POST"])

    def test_non_json_reservation_is_unknown_and_never_reposts(self):
        self.server.reserve_response = Response(content=b"non-json private provider response", status=201)
        self.assert_failed_attempt_never_retried(None, ["POST"])

    def test_asset_timeout_never_reuploads_or_commits(self):
        self.assert_failed_attempt_never_retried("asset", ["POST", "PUT"])

    def test_asset_redirect_is_not_followed_and_never_committed(self):
        self.server.asset_status = 302
        self.assert_failed_attempt_never_retried(None, ["POST", "PUT"])

    def test_uncertain_commit_can_be_reconciled_by_matching_complete_readback(self):
        self.assert_failed_attempt_never_retried("commit_after", ["POST", "PUT", "PUT", "PATCH"], complete=True)

    def test_non_json_commit_is_not_accepted_without_later_readback(self):
        self.server.commit_response = Response(content=b"non-json private provider response")
        self.assert_failed_attempt_never_retried(None, ["POST", "PUT", "PUT", "PATCH"], complete=True)

    def test_crash_preserves_started_intent_and_blocks_new_reservation(self):
        self.server.failure = "crash"
        with self.assertRaises(KeyboardInterrupt):
            self.upload(confirm=True)
        self.assertEqual(s.read_json(m.journal_path(self.tier))["state"], "reserve_started")
        self.server.failure = None
        with self.assertRaises(s.GuardError):
            self.upload(confirm=True)
        self.assertEqual([c[0] for c in self.server.mutations], ["POST"])

    def test_wrong_checksum_commit_never_claims_completion(self):
        self.server.on_commit = lambda image: image["attributes"].update(sourceFileChecksum="0" * 32)
        self.assert_failed_attempt_never_retried(None, ["POST", "PUT", "PUT", "PATCH"])

    def test_commit_response_requires_fresh_matching_readback(self):
        def change_after_commit(tier):
            if any(c[0] == "PATCH" for c in self.server.calls):
                self.server.images[tier]["id"] = "different-image"
        self.server.on_screenshot_get = change_after_commit
        self.assert_failed_attempt_never_retried(None, ["POST", "PUT", "PUT", "PATCH"])

    def test_wrong_reservation_ownership_blocks_asset_upload(self):
        self.server.on_reserve = lambda image: image["relationships"].update(subscription=m.relationship("subscriptions", "other"))
        self.assert_failed_attempt_never_retried(None, ["POST"])

    def test_journal_identity_cannot_be_bypassed_with_a_new_png_hash(self):
        self.upload(confirm=True)
        other = png_fixture((0, 0, 255))
        s.write_private(self.png, other)
        self.sha = hashlib.sha256(other).hexdigest()
        with self.assertRaisesRegex(s.GuardError, "journal identity"):
            self.upload(confirm=True)
        self.assertEqual(len(self.server.mutations), 4)

    def test_journal_must_remain_private_and_recognized(self):
        self.upload(confirm=True)
        path = m.journal_path(self.tier)
        path.chmod(0o644)
        with self.assertRaises(s.GuardError):
            self.upload(confirm=True)
        path.chmod(0o600)
        record = s.read_json(path)
        record["state"] = "unexpected"
        s.write_private(path, record)
        with self.assertRaises(s.GuardError):
            self.upload(confirm=True)
        self.assertEqual(len(self.server.mutations), 4)

    def test_bad_api_response_fails_before_any_reservation(self):
        for response in [Response({}, 302), Response({}, 401), Response({}, 500), Response({}, content=b""),
                         Response([], 200), Response({"data": [], "errors": []}),
                         Response(content=b"non-json private provider response")]:
            self.server.get_response = response
            self.assert_refused()

    def test_api_mutation_allowlist_and_missing_intent_block_network(self):
        api = m.ScreenshotAPI()
        for method, path in [("POST", "/v1/reviewSubmissions"), ("PATCH", "/v1/appStoreVersions/version"),
                             ("POST", "/v1/subscriptionSubmissions"), ("POST", "/v1/subscriptionPrices"),
                             ("DELETE", m.RESOURCE + "/image-creator"), ("GET", "https://evil.test/v1/apps"),
                             ("POST", m.RESOURCE), ("PATCH", m.RESOURCE + "/image-creator")]:
            with self.subTest(method=method, path=path):
                with self.assertRaises(s.GuardError):
                    api.request(method, path, {})
        self.assertFalse(self.server.calls)

    def test_lock_prevents_concurrent_uploads(self):
        with s.lock("creator-apple-review-screenshot"):
            self.assert_refused()
        self.assertFalse(self.server.calls)

    def test_cli_defaults_read_only_requires_exact_input_and_suppresses_private_errors(self):
        args = ["--tier", self.tier, "--png", str(self.png), "--sha256", self.sha]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(m.main(args), 0)
        self.assertFalse(self.server.mutations)
        self.assertEqual(json.loads(output.getvalue())["state"], "plan_only")
        self.server.reserve_response = Response(content=b"non-json private provider response", status=201)
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            self.assertEqual(m.main(args + ["--confirm-upload"]), 1)
        self.assertNotIn("private provider response", error.getvalue())
        self.assertNotIn("fixture-signed-url", error.getvalue())
        self.assertNotIn("fixture-jwt", error.getvalue())
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            m.main(args[:-2])


if __name__ == "__main__":
    unittest.main()
