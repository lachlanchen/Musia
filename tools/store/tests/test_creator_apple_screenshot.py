"""Offline screenshot protocol tests, never real credentials or native captures."""
import base64
import contextlib
import copy
from datetime import datetime, timezone
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
from urllib.parse import parse_qs, urlencode, urlsplit
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


def sigv4_fixture(**overrides):
    date = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    query = {"X-Amz-Algorithm": "AWS4-HMAC-SHA256", "X-Amz-Date": date, "X-Amz-Expires": "604800",
             "X-Amz-Credential": f"FIXTURE/{date[:8]}/us-east-1/s3/aws4_request", "X-Amz-SignedHeaders": "host",
             "X-Amz-Signature": "a" * 64, "partNumber": "1", "uploadId": "fixture", "apple-asset-repo-correlation-key": "fixture"}
    query.update(overrides)
    return "https://northamerica-1.object-storage.apple.com/fixture/asset/image?" + urlencode(query)


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
            self.case.assertIn(parsed.hostname, {"store-030.blobstore.apple.com", "northamerica-1.object-storage.apple.com"})
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
        self.runtime.parent.mkdir(mode=0o700)
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

    def upload(self, confirm=False, resume=None, reconcile=False):
        return m.upload(self.tier, self.png, self.sha, confirm, resume, reconcile)

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

    def seed_processed_source(self):
        self.upload(confirm=True)
        path = m.journal_path(self.tier)
        record = s.read_json(path)
        record.pop("commit_observation")
        record.update(state="unknown", last_diagnostic={"method": "PATCH", "http": 200,
                      "phase": "commit_started", "guard": "checksum_mismatch", "failure": "local_validation"})
        s.write_private(path, record)
        self.server.images[self.tier]["attributes"]["fileName"] = "SOURCE"
        self.server.calls.clear()
        return path

    def test_actual_source_normalization_reconciles_pinned_complete_readback_only(self):
        self.tier = "studio"
        path = self.seed_processed_source()
        before = path.read_bytes()
        result = self.upload()
        self.assertEqual(result["state"], "COMPLETE")
        self.assertTrue(result["processingComplete"])
        self.assertTrue(result["checksumVerified"])
        self.assertFalse(result["journalReconciled"])
        self.assertFalse(result["providerMutationsThisRun"])
        self.assertEqual(path.read_bytes(), before)
        result = self.upload(reconcile=True)
        self.assertTrue(result["journalReconciled"])
        after = s.read_json(path)
        self.assertEqual(after["state"], "complete")
        self.assertEqual(after["last_diagnostic"], json.loads(before)["last_diagnostic"])
        self.assertEqual(after["request"], json.loads(before)["request"])
        self.assertEqual(after["readback"]["attributes"]["fileName"], "SOURCE")
        self.assertEqual(after["reconciliation"]["from_state"], "unknown")
        self.assertEqual(after["reconciliation"]["method"], "GET")
        self.assertFalse(self.server.mutations)

    def test_source_normalization_requires_pinned_id_owner_size_and_exact_md5(self):
        path = self.seed_processed_source()
        before = path.read_bytes()
        original = copy.deepcopy(self.server.images[self.tier])
        changes = [lambda image: image.update(id="different-image"),
                   lambda image: image["relationships"].update(subscription=m.relationship("subscriptions", "studio")),
                   lambda image: image["relationships"].clear(),
                   lambda image: image["attributes"].update(fileSize=1),
                   lambda image: image["attributes"].update(sourceFileChecksum="0" * 32),
                   lambda image: image["attributes"].update(sourceFileChecksum=None),
                   lambda image: image["attributes"].update(sourceFileChecksum=""),
                   lambda image: image["attributes"].update(sourceFileChecksum=self.md5.upper()),
                   lambda image: image["attributes"].update(fileName="other-normalized.png")]
        for change in changes:
            self.server.images[self.tier] = copy.deepcopy(original)
            change(self.server.images[self.tier])
            with self.assertRaises(s.GuardError):
                self.upload(reconcile=True)
            self.assertEqual(path.read_bytes(), before)
        self.server.images[self.tier] = original
        record = json.loads(before)
        record.pop("screenshot_id")
        s.write_private(path, record)
        with self.assertRaises(s.GuardError):
            self.upload(reconcile=True)
        path.unlink()
        with self.assertRaises(s.GuardError):
            self.upload()
        self.assertFalse(self.server.mutations)

    def test_normalized_filename_cannot_bypass_pending_reservation_guard(self):
        path = self.seed_processed_source()
        before = path.read_bytes()
        for state in ["AWAITING_UPLOAD", "UPLOAD_COMPLETE"]:
            for checksum in [None, "", self.md5]:
                self.server.images[self.tier]["attributes"].update(
                    assetDeliveryState={"state": state}, sourceFileChecksum=checksum)
                with self.assertRaises(s.GuardError):
                    self.upload(confirm=True, resume="image-creator")
                self.assertEqual(path.read_bytes(), before)
        self.assertFalse(self.server.mutations)

    def test_immediate_missing_checksum_can_resolve_via_fresh_complete_source_readback(self):
        committed = self.server.make_image(self.tier, "UPLOAD_COMPLETE")
        committed["attributes"]["sourceFileChecksum"] = ""
        self.server.commit_response = Response({"data": committed})
        self.server.on_commit = lambda image: image["attributes"].update(fileName="SOURCE")
        result = self.upload(confirm=True)
        self.assertTrue(result["processingComplete"])
        self.assertEqual(result["state"], "COMPLETE")
        record = s.read_json(m.journal_path(self.tier))
        self.assertEqual(record["commit_observation"]["sourceFileChecksum"], "")
        self.assertEqual(record["commit_observation"]["state"], "UPLOAD_COMPLETE")
        self.assertEqual(record["readback"]["attributes"]["sourceFileChecksum"], self.md5)
        self.assertEqual([c[0] for c in self.server.mutations], ["POST", "PUT", "PUT", "PATCH"])

    def test_missing_postcommit_checksum_is_processing_not_passed_and_never_retried(self):
        self.server.commit_state = "UPLOAD_COMPLETE"
        self.server.on_commit = lambda image: image["attributes"].update(sourceFileChecksum="")
        result = self.upload(confirm=True)
        self.assertEqual(result["state"], "CHECKSUM_PENDING")
        self.assertEqual(result["providerState"], "UPLOAD_COMPLETE")
        self.assertEqual(result["action"], "processing_readback")
        self.assertFalse(result["processingComplete"])
        self.assertFalse(result["checksumVerified"])
        self.assertFalse(result["automaticRetryAuthorized"])
        path = m.journal_path(self.tier)
        self.assertEqual(s.read_json(path)["state"], "processing")
        self.server.calls.clear()
        before = path.read_bytes()
        self.assertEqual(self.upload()["state"], "CHECKSUM_PENDING")
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.upload(confirm=True, resume="image-creator")["state"], "CHECKSUM_PENDING")
        self.assertEqual(self.upload(reconcile=True)["state"], "CHECKSUM_PENDING")
        self.assertFalse(self.server.mutations)
        self.server.images[self.tier]["attributes"].update(fileName="SOURCE", sourceFileChecksum=self.md5,
                                                         assetDeliveryState={"state": "COMPLETE"})
        self.assertTrue(self.upload(reconcile=True)["processingComplete"])
        self.assertEqual(s.read_json(path)["state"], "complete")
        self.assertFalse(self.server.mutations)

    def test_complete_state_without_checksum_never_claims_complete(self):
        self.server.on_commit = lambda image: image["attributes"].update(sourceFileChecksum=None)
        result = self.upload(confirm=True)
        self.assertEqual(result["state"], "CHECKSUM_PENDING")
        self.assertEqual(result["providerState"], "COMPLETE")
        self.assertFalse(result["processingComplete"])
        self.assertFalse(result["checksumVerified"])
        self.assertEqual(s.read_json(m.journal_path(self.tier))["state"], "processing")

    def test_checksum_pending_requires_exact_protected_commit_intent(self):
        path = self.seed_processed_source()
        base = s.read_json(path)
        self.server.images[self.tier]["attributes"].update(
            fileName=base["identity"]["fileName"], sourceFileChecksum="", assetDeliveryState={"state": "UPLOAD_COMPLETE"})
        changes = [lambda record: record.pop("screenshot_id"),
                   lambda record: record["request"].update(method="POST"),
                   lambda record: record["request"].update(path=m.RESOURCE + "/different-id"),
                   lambda record: record["request"]["body"]["data"]["attributes"].update(sourceFileChecksum="wrong")]
        for change in changes:
            record = copy.deepcopy(base)
            change(record)
            s.write_private(path, record)
            before = path.read_bytes()
            with self.assertRaises(s.GuardError):
                self.upload(reconcile=True)
            self.assertEqual(path.read_bytes(), before)
        self.assertFalse(self.server.mutations)

    def test_nonempty_checksum_mismatch_never_becomes_processing_pending(self):
        path = self.seed_processed_source()
        before = path.read_bytes()
        image = self.server.images[self.tier]
        for checksum in ["0" * 32, "not-a-digest", self.md5.upper()]:
            image["attributes"].update(fileName=json.loads(before)["identity"]["fileName"], sourceFileChecksum=checksum,
                                       assetDeliveryState={"state": "UPLOAD_COMPLETE"})
            with self.assertRaisesRegex(s.GuardError, "checksum mismatch"):
                self.upload(reconcile=True)
            self.assertEqual(path.read_bytes(), before)
        self.assertFalse(self.server.mutations)

    def test_reconcile_mode_cannot_reserve_resume_or_use_confirm(self):
        with self.assertRaises(s.GuardError):
            self.upload(reconcile=True)
        with self.assertRaises(s.GuardError):
            self.upload(reconcile=True, confirm=True)
        with self.assertRaises(s.GuardError):
            self.upload(reconcile=True, resume="image-creator")
        self.assertFalse(self.server.mutations)
        self.assertFalse(m.journal_path(self.tier).exists())
        self.seed_processed_source()
        self.server.images.clear()
        with self.assertRaises(s.GuardError):
            self.upload(reconcile=True)
        self.assertFalse(self.server.mutations)

    def test_reconcile_cli_only_updates_local_journal_and_blocks_confirm_combination(self):
        path = self.seed_processed_source()
        args = ["--tier", self.tier, "--png", str(self.png), "--sha256", self.sha, "--reconcile-journal"]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(m.main(args), 0)
        self.assertTrue(json.loads(output.getvalue())["journalReconciled"])
        self.assertEqual(s.read_json(path)["state"], "complete")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            m.main(args + ["--confirm-upload"])
        self.assertFalse(self.server.mutations)

    def test_empty_pre_upload_checksum_is_accepted_but_still_requires_md5_commit(self):
        self.server.on_reserve = lambda image: image["attributes"].update(sourceFileChecksum="")
        self.assertTrue(self.upload(confirm=True)["processingComplete"])
        self.assertEqual(s.read_json(m.journal_path(self.tier))["readback"]["attributes"]["sourceFileChecksum"], self.md5)
        self.assertEqual([c[0] for c in self.server.mutations], ["POST", "PUT", "PUT", "PATCH"])

    def test_awaiting_reservation_readback_reports_exact_resource_without_mutation(self):
        for checksum in [None, "", self.md5]:
            self.server.images[self.tier] = self.server.make_image(self.tier)
            self.server.images[self.tier]["attributes"]["sourceFileChecksum"] = checksum
            result = self.upload(confirm=True)
            self.assertEqual(result["state"], "AWAITING_UPLOAD")
            self.assertEqual(result["screenshotId"], "image-creator")
            self.assertEqual(result["action"], "reservation_readback_only")
            self.assertFalse(result["processingComplete"])
            self.assertFalse(result["providerMutationsThisRun"])
            self.assertFalse(result["automaticRetryAuthorized"])
            self.assertFalse(self.server.mutations)
            self.assertFalse(m.journal_path(self.tier).exists())

    def test_empty_checksum_cannot_qualify_uploaded_or_complete_image(self):
        for state in ["UPLOAD_COMPLETE", "COMPLETE"]:
            self.server.images[self.tier] = self.server.make_image(self.tier, state)
            self.server.images[self.tier]["attributes"]["sourceFileChecksum"] = ""
            self.assert_refused()

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

    def test_observed_apple_sigv4_upload_shape_accepts_empty_checksum_and_exact_png(self):
        def modern(image):
            image["attributes"].update(sourceFileChecksum="", uploadOperations=[{
                "method": "PUT", "url": sigv4_fixture(), "offset": 0, "length": len(self.payload),
                "requestHeaders": [{"name": "Content-Type", "value": "image/png"}]}])
        self.server.on_reserve = modern
        self.assertTrue(self.upload(confirm=True)["processingComplete"])
        self.assertEqual([c[0] for c in self.server.mutations], ["POST", "PUT", "PATCH"])
        self.assertEqual(self.server.parts[1], self.payload)

    def test_sigv4_exact_host_and_path_guards(self):
        good = sigv4_fixture()
        self.assertEqual(m.asset_url(good), good)
        bad = [good.replace("https:", "http:"), good.replace("northamerica-1", "northamerica-2"),
               good.replace(".apple.com", ".apple.com.evil.test"), good.replace(".apple.com", ".amazonaws.com"),
               good.replace("northamerica-1", "user@northamerica-1"), good.replace(".com/", ".com:80/"),
               good.replace("/fixture/", "/../"), good.replace("/fixture/", "/%2e%2e/"),
               good.replace("/fixture/", "//"), good + "#fragment", good + "\\bad", good + "\n"]
        for url in bad:
            with self.subTest(url=url), self.assertRaises((s.GuardError, ValueError)):
                m.asset_url(url)

    def test_sigv4_scope_signature_dates_and_expiry_fail_closed(self):
        date = datetime.now(timezone.utc).strftime("%Y%m%d")
        invalid = [{"X-Amz-Algorithm": "other"}, {"X-Amz-SignedHeaders": "authorization;host"},
                   {"X-Amz-SignedHeaders": "content-type;host"}, {"X-Amz-Signature": "a" * 63},
                   {"X-Amz-Signature": "A" * 64}, {"X-Amz-Credential": "secret"},
                   {"X-Amz-Credential": f"FIXTURE/{date}/us-east-1/sts/aws4_request"},
                   {"X-Amz-Credential": f"FIXTURE/20000101/us-east-1/s3/aws4_request"},
                   {"X-Amz-Date": "20261399T000000Z", "X-Amz-Credential": "FIXTURE/20261399/region/s3/aws4_request"},
                   {"X-Amz-Date": "20000101T000000Z", "X-Amz-Credential": "FIXTURE/20000101/region/s3/aws4_request"},
                   {"X-Amz-Date": "20990101T000000Z", "X-Amz-Credential": "FIXTURE/20990101/region/s3/aws4_request"},
                   {"X-Amz-Expires": "0"}, {"X-Amz-Expires": "604801"}, {"X-Amz-Expires": "1e6"},
                   {"partNumber": "0"}, {"uploadId": ""}, {"Signature": "legacy"}]
        for fields in invalid:
            with self.subTest(fields=fields), self.assertRaises(s.GuardError):
                m.asset_url(sigv4_fixture(**fields))
        for suffix in ["&X-Amz-Signature=duplicate", "&other=value"]:
            with self.assertRaises(s.GuardError):
                m.asset_url(sigv4_fixture() + suffix)
        with self.assertRaises(s.GuardError):
            m.asset_url(sigv4_fixture().replace("X-Amz-Signature=", "Missing-Signature="))

    def test_legacy_host_cannot_use_modern_signature(self):
        with self.assertRaises(s.GuardError):
            m.asset_url(sigv4_fixture().replace("northamerica-1.object-storage.apple.com/fixture/", "store-030.blobstore.apple.com/assets-fixture/"))

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

    def assert_failed_attempt_never_retried(self, failure, expected_methods, complete=False, awaiting=False):
        self.server.failure = failure
        with self.assertRaisesRegex(s.GuardError, "outcome unconfirmed"):
            self.upload(confirm=True)
        self.assertEqual([c[0] for c in self.server.mutations], expected_methods)
        self.assertEqual(s.read_json(m.journal_path(self.tier))["state"], "unknown")
        before = m.journal_path(self.tier).read_bytes()
        self.server.failure = None
        if complete:
            self.assertTrue(self.upload(confirm=True)["processingComplete"])
        elif awaiting:
            result = self.upload(confirm=True)
            self.assertEqual(result["state"], "AWAITING_UPLOAD")
            self.assertFalse(result["processingComplete"])
            self.assertEqual(before, m.journal_path(self.tier).read_bytes())
        else:
            with self.assertRaises(s.GuardError):
                self.upload(confirm=True)
        self.assertEqual([c[0] for c in self.server.mutations], expected_methods)

    def test_reservation_timeout_before_acceptance_never_reposts(self):
        self.assert_failed_attempt_never_retried("reserve_before", ["POST"])

    def test_reservation_timeout_after_acceptance_is_readback_only(self):
        self.assert_failed_attempt_never_retried("reserve_after", ["POST"], awaiting=True)

    def test_non_json_reservation_is_unknown_and_never_reposts(self):
        self.server.reserve_response = Response(content=b"non-json private provider response", status=201)
        self.assert_failed_attempt_never_retried(None, ["POST"], awaiting=True)

    def test_asset_timeout_never_reuploads_or_commits(self):
        self.assert_failed_attempt_never_retried("asset", ["POST", "PUT"], awaiting=True)

    def test_asset_redirect_is_not_followed_and_never_committed(self):
        self.server.asset_status = 302
        self.assert_failed_attempt_never_retried(None, ["POST", "PUT"], awaiting=True)

    def test_old_unknown_reserve_journal_reconciles_empty_checksum_without_rewriting(self):
        self.server.failure = "reserve_after"
        with self.assertRaises(s.GuardError):
            self.upload(confirm=True)
        path = m.journal_path(self.tier)
        record = s.read_json(path)
        record.pop("last_diagnostic")
        self.assertNotIn("reservation", record)
        s.write_private(path, record)
        original = path.read_bytes()
        self.server.images[self.tier]["attributes"]["sourceFileChecksum"] = ""
        self.assertEqual(self.upload()["screenshotId"], "image-creator")
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual([c[0] for c in self.server.mutations], ["POST"])

    def seed_old_reservation(self):
        self.server.failure = "reserve_after"
        with self.assertRaises(s.GuardError):
            self.upload(confirm=True)
        path = m.journal_path(self.tier)
        record = s.read_json(path)
        record.pop("last_diagnostic")
        s.write_private(path, record)
        self.server.images[self.tier]["attributes"]["sourceFileChecksum"] = ""
        self.server.failure = None
        return path

    def test_explicit_resume_plan_is_read_only_and_preserves_unknown_journal(self):
        path = self.seed_old_reservation()
        original = path.read_bytes()
        result = self.upload(resume="image-creator")
        self.assertEqual(result["action"], "would_resume")
        self.assertEqual(result["remainingParts"], 2)
        self.assertFalse(result["providerMutationsThisRun"])
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual([c[0] for c in self.server.mutations], ["POST"])

    def test_explicit_resume_uses_existing_reservation_without_post_or_delete(self):
        self.seed_old_reservation()
        self.server.calls.clear()
        result = self.upload(confirm=True, resume="image-creator")
        self.assertTrue(result["processingComplete"])
        self.assertEqual(result["action"], "resumed_readback")
        self.assertEqual([c[0] for c in self.server.mutations], ["PUT", "PUT", "PATCH"])
        self.assertEqual(self.server.images[self.tier]["attributes"]["sourceFileChecksum"], self.md5)

    def test_studio_sigv4_resume_matches_actual_empty_checksum_protocol(self):
        self.tier = "studio"
        self.seed_old_reservation()
        self.server.images[self.tier]["attributes"]["uploadOperations"] = [{
            "method": "PUT", "url": sigv4_fixture(), "offset": 0, "length": len(self.payload),
            "requestHeaders": [{"name": "Content-Type", "value": "image/png"}]}]
        self.server.calls.clear()
        self.assertEqual(self.upload(resume="image-studio")["remainingParts"], 1)
        self.assertTrue(self.upload(confirm=True, resume="image-studio")["processingComplete"])
        self.assertEqual([c[0] for c in self.server.mutations], ["PUT", "PATCH"])

    def test_resume_cli_without_confirm_only_plans_then_confirm_completes_same_id(self):
        path = self.seed_old_reservation()
        original = path.read_bytes()
        args = ["--tier", self.tier, "--png", str(self.png), "--sha256", self.sha,
                "--resume-reservation", "image-creator"]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(m.main(args), 0)
        self.assertEqual(json.loads(output.getvalue())["action"], "would_resume")
        self.assertEqual(path.read_bytes(), original)
        self.server.calls.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(m.main(args + ["--confirm-upload"]), 0)
        self.assertEqual([c[0] for c in self.server.mutations], ["PUT", "PUT", "PATCH"])

    def test_resume_wrong_id_missing_journal_or_absent_resource_never_mutates(self):
        self.seed_old_reservation()
        self.server.calls.clear()
        with self.assertRaises(s.GuardError):
            self.upload(confirm=True, resume="other-image")
        image = self.server.images.pop(self.tier)
        with self.assertRaises(s.GuardError):
            self.upload(confirm=True, resume="image-creator")
        self.server.images[self.tier] = image
        m.journal_path(self.tier).unlink()
        with self.assertRaises(s.GuardError):
            self.upload(confirm=True, resume="image-creator")
        self.assertFalse(self.server.mutations)

    def test_resume_unknown_asset_outcome_stays_readback_only(self):
        self.server.failure = "asset"
        with self.assertRaises(s.GuardError):
            self.upload(confirm=True)
        path = m.journal_path(self.tier)
        original = path.read_bytes()
        self.server.calls.clear()
        self.server.failure = None
        with self.assertRaisesRegex(s.GuardError, "part outcome"):
            self.upload(confirm=True, resume="image-creator")
        self.assertFalse(self.server.mutations)
        self.assertEqual(path.read_bytes(), original)

    def test_resume_cannot_bypass_unknown_diagnostic_or_attempted_part_marker(self):
        path = self.seed_old_reservation()
        base = s.read_json(path)
        variants = [dict(base, part=0), dict(base, last_diagnostic={"phase": "upload_started"}),
                    dict(base, last_diagnostic={"phase": "commit_started"}),
                    dict(base, state="upload_started"), dict(base, state="commit_started")]
        self.server.calls.clear()
        for record in variants:
            s.write_private(path, record)
            original = path.read_bytes()
            with self.assertRaises(s.GuardError):
                self.upload(confirm=True, resume="image-creator")
            self.assertEqual(path.read_bytes(), original)
        self.assertFalse(self.server.mutations)

    def test_resume_fresh_ownership_or_id_change_blocks_all_asset_operations(self):
        path = self.seed_old_reservation()
        self.server.calls.clear()
        reads = []
        def change_second_read(tier):
            reads.append(tier)
            if len(reads) == 2:
                self.server.images[tier]["id"] = "other-image"
        self.server.on_screenshot_get = change_second_read
        with self.assertRaises(s.GuardError):
            self.upload(confirm=True, resume="image-creator")
        self.assertFalse(self.server.mutations)
        self.assertEqual(s.read_json(path)["state"], "unknown")

    def seed_successful_part_checkpoint(self, index=0):
        path = self.seed_old_reservation()
        record = s.read_json(path)
        image = self.server.images[self.tier]
        parts = m.upload_operations(image, self.payload)
        record.update(state="part_uploaded", screenshot_id=image["id"], reservation=image,
                      upload_plan=m.part_plan(parts, self.payload), part=index)
        s.write_private(path, record)
        for i in range(index + 1):
            part = parts[i]
            self.server.parts[i] = self.payload[part["offset"]:part["offset"] + part["length"]]
        self.server.calls.clear()
        return path

    def test_resume_sends_only_journal_proven_unattempted_parts(self):
        self.seed_successful_part_checkpoint()
        self.assertEqual(self.upload(resume="image-creator")["nextPart"], 1)
        self.assertTrue(self.upload(confirm=True, resume="image-creator")["processingComplete"])
        self.assertEqual([c[0] for c in self.server.mutations], ["PUT", "PATCH"])
        self.assertEqual(self.server.mutations[0][2]["data"], self.payload[len(self.payload) // 2:])

    def test_all_parts_checkpoint_resumes_only_exact_md5_commit(self):
        self.seed_successful_part_checkpoint(index=1)
        self.assertEqual(self.upload(resume="image-creator")["remainingParts"], 0)
        self.assertTrue(self.upload(confirm=True, resume="image-creator")["processingComplete"])
        self.assertEqual([c[0] for c in self.server.mutations], ["PATCH"])

    def test_checkpoint_changed_plan_or_unknown_commit_never_resumes(self):
        path = self.seed_successful_part_checkpoint()
        base = s.read_json(path)
        for state in ["upload_started", "unknown", "commit_started"]:
            record = dict(base, state=state)
            s.write_private(path, record)
            with self.assertRaises(s.GuardError):
                self.upload(confirm=True, resume="image-creator")
        base["upload_plan"][0]["length"] += 1
        s.write_private(path, base)
        with self.assertRaisesRegex(s.GuardError, "plan changed"):
            self.upload(confirm=True, resume="image-creator")
        self.assertFalse(self.server.mutations)

    def test_resume_submitted_subscription_never_uploads_bytes(self):
        self.seed_old_reservation()
        self.server.calls.clear()
        self.server.products[0]["attributes"]["state"] = "WAITING_FOR_REVIEW"
        for confirm in [False, True]:
            with self.assertRaises(s.GuardError):
                self.upload(confirm=confirm, resume="image-creator")
        self.assertFalse(self.server.mutations)

    def test_http_error_diagnostics_retain_only_codes_status_and_known_field(self):
        error = {"status": "409", "code": "ENTITY_ERROR.ATTRIBUTE.INVALID", "id": "private-id",
                 "title": "Bearer fixture-jwt", "detail": self.server.operations(len(self.payload))[0]["url"],
                 "source": {"pointer": "/data/attributes/fileName", "parameter": "private-param"},
                 "meta": {"token": "private-token"}}
        self.server.reserve_response = Response({"errors": [error]}, 409)
        with self.assertRaises(m.ScreenshotError) as caught:
            self.upload(confirm=True)
        record = s.read_json(m.journal_path(self.tier))
        diagnostic = record["last_diagnostic"]
        self.assertEqual(diagnostic["http"], 409)
        self.assertEqual(diagnostic["method"], "POST")
        self.assertEqual(diagnostic["phase"], "reserve_started")
        self.assertEqual(diagnostic["failure"], "http_status")
        self.assertEqual(diagnostic["provider_errors"], [{"status": "409", "code": "ENTITY_ERROR.ATTRIBUTE.INVALID",
                                                       "pointer": "/data/attributes/fileName", "message_redacted": True}])
        output = str(caught.exception) + json.dumps(diagnostic)
        for private in ["fixture-jwt", "https://", "Signature=", "private-id", "private-param", "private-token"]:
            self.assertNotIn(private, output)
        self.assertEqual(self.upload()["state"], "AWAITING_UPLOAD")
        self.assertEqual([c[0] for c in self.server.mutations], ["POST"])

    def test_diagnostic_error_payloads_are_bounded_and_free_text_is_never_retained(self):
        errors = [{"status": "Bearer token", "code": "eyJhbGciOiJFUzI1NiJ9.payload.signature",
                   "source": {"pointer": "https://store-030.blobstore.apple.com/assets-x?Signature=secret"},
                   "detail": "secret"}, {"source": {"pointer": []}}, "unexpected"] * 10
        diagnostic, _ = m.response_diagnostic(Response({"errors": errors}, 400))
        self.assertEqual(diagnostic["provider_error_count"], 30)
        self.assertLessEqual(len(diagnostic["provider_errors"]), 10)
        for private in ["secret", "Bearer", "eyJ", "https://"]:
            self.assertNotIn(private, json.dumps(diagnostic))

    def test_non_json_and_transport_failures_keep_status_without_raw_response(self):
        self.server.reserve_response = Response(content=b"non-json private provider response", status=201)
        with self.assertRaises(m.ScreenshotError):
            self.upload(confirm=True)
        diagnostic = s.read_json(m.journal_path(self.tier))["last_diagnostic"]
        self.assertEqual(diagnostic["http"], 201)
        self.assertEqual(diagnostic["response"], "non_json")
        self.assertNotIn("private provider response", json.dumps(diagnostic))

    def test_transport_diagnostic_never_copies_exception_message(self):
        self.server.failure = "reserve_before"
        with self.assertRaises(m.ScreenshotError):
            self.upload(confirm=True)
        diagnostic = s.read_json(m.journal_path(self.tier))["last_diagnostic"]
        self.assertIsNone(diagnostic["http"])
        self.assertEqual(diagnostic["failure"], "transport")
        self.assertEqual(diagnostic["exception_type"], "TimeoutError")
        self.assertNotIn("private provider response", json.dumps(diagnostic))

    def test_local_checksum_failure_retains_success_http_and_guard_reason(self):
        self.server.on_reserve = lambda image: image["attributes"].update(sourceFileChecksum="wrong")
        with self.assertRaises(m.ScreenshotError):
            self.upload(confirm=True)
        diagnostic = s.read_json(m.journal_path(self.tier))["last_diagnostic"]
        self.assertEqual(diagnostic["http"], 201)
        self.assertEqual(diagnostic["failure"], "local_validation")
        self.assertEqual(diagnostic["guard"], "checksum_mismatch")
        self.assertEqual([c[0] for c in self.server.mutations], ["POST"])

    def test_asset_http_failure_records_code_but_never_signed_url(self):
        self.server.asset_status = 403
        with self.assertRaises(m.ScreenshotError) as caught:
            self.upload(confirm=True)
        diagnostic = s.read_json(m.journal_path(self.tier))["last_diagnostic"]
        self.assertEqual(diagnostic["http"], 403)
        self.assertEqual(diagnostic["method"], "PUT")
        self.assertEqual(diagnostic["phase"], "upload_started")
        self.assertNotIn("https://", str(caught.exception))
        self.assertNotIn("Signature=", json.dumps(diagnostic))

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
