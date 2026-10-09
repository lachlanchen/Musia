"""Offline Mac attachment tests. No credentials, provider calls, or real PKGs."""
import contextlib
import copy
import hashlib
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
import invite_macos as m
import storelib as s


class FakeApple(s.Apple):
    def __init__(self, case, cfg):
        super().__init__(cfg)
        self.case = case
        self.calls = []
        self.app_row = {"id": "musia", "attributes": {"bundleId": s.BUNDLE}}
        self.builds = [{"id": "mac-7", "attributes": {"version": "7", "processingState": "VALID", "expired": False}}]
        self.pre = {"mac-7": {"platform": "MAC_OS", "version": "0.2.0"}}
        self.build_app = copy.deepcopy(self.app_row)
        self.groups = [{"id": "internal", "attributes": {"name": "Musia Internal", "isInternalGroup": True,
                                                       "hasAccessToAllBuilds": False}}]
        self.testers = [{"id": "owner", "attributes": {"email": "owner@example.test"}}]
        self.tester_apps = [copy.deepcopy(self.app_row)]
        self.members = [{"type": "betaTesters", "id": "owner"}]
        self.attached = [{"type": "builds", "id": "old-build"}]
        self.internal_state = "READY_FOR_BETA_TESTING"
        self.formal = [{"id": "formal-mac", "attributes": {"platform": "MAC_OS", "versionString": "0.1.2",
                                                            "appStoreState": "WAITING_FOR_REVIEW"}},
                       {"id": "formal-ios", "attributes": {"platform": "IOS", "versionString": "0.1.2",
                                                            "appStoreState": "WAITING_FOR_REVIEW"}}]
        self.formal_builds = {"formal-mac": {"id": "mac-4"}, "formal-ios": {"id": "ios-4"}}
        self.post_failure = None
        self.attach_on_post = True
        self.activate_on_post = True
        self.on_post = None
        self.readback_failure = False
        self.paginate_members = False

    @property
    def posts(self):
        return [c for c in self.calls if c[0] != "GET"]

    def request(self, method, path, body=None, operation=None):
        self.calls.append((method, path, body, operation))
        if method == "POST":
            self.case.assertEqual(path, "/v1/betaGroups/internal/relationships/builds")
            self.case.assertEqual(body, {"data": [{"type": "builds", "id": "mac-7"}]})
            self.case.assertEqual(operation, "musia-internal-builds-mac-7")
            journal = s.read_json(m.operation_path(self.case.sha))
            self.case.assertEqual(journal["state"], "intent", "Durable exact intent must precede POST")
            self.case.assertEqual(journal["identity"]["tester_id"], "owner")
            self.case.assertEqual(journal["identity"]["package_sha256"], self.case.sha)
            provider = self.case.provider_journal()
            self.case.assertFalse(provider.exists(), "Apple's existing one-shot journal must be preserved")
            s.write_private(provider, {"operation": operation, "state": "started", "path": path})
            if self.post_failure == "before":
                raise TimeoutError("private provider body must not leak")
            if self.post_failure == "crash":
                raise KeyboardInterrupt()
            if self.attach_on_post:
                self.attached.append({"type": "builds", "id": "mac-7"})
            if self.activate_on_post:
                self.internal_state = "IN_BETA_TESTING"
            if self.on_post:
                self.on_post()
            if self.post_failure == "after":
                raise TimeoutError("private provider body must not leak")
            s.write_private(provider, {"operation": operation, "state": "accepted", "response": {}})
            return {}
        self.case.assertEqual(method, "GET", "No formal/group/tester mutation is allowed")
        if self.readback_failure and self.posts:
            raise OSError("private response during readback")
        split = urlsplit(path)
        route, query = split.path, parse_qs(split.query)
        if route == "/v1/apps":
            return {"data": [self.app_row]}
        if route == "/v1/bundleIds":
            return {"data": [{"id": "bundle", "attributes": {"identifier": s.BUNDLE}}]}
        if route == "/v1/builds":
            self.case.assertEqual(query["filter[app]"], ["musia"])
            self.case.assertEqual(query["filter[version]"], ["7"])
            return {"data": self.builds}
        if route.endswith("/preReleaseVersion"):
            bid = route.split("/")[3]
            return {"data": {"attributes": self.pre[bid]}}
        if route == "/v1/builds/mac-7/app":
            return {"data": self.build_app}
        if route == "/v1/apps/musia/betaGroups":
            return {"data": self.groups}
        if route == "/v1/betaTesters":
            self.case.assertEqual(query["filter[apps]"], ["musia"])
            self.case.assertEqual(query["filter[email]"][0].casefold(), "owner@example.test")
            return {"data": self.testers}
        if route == "/v1/betaTesters/owner/apps":
            return {"data": self.tester_apps}
        if route == "/v1/betaGroups/internal/relationships/betaTesters":
            if self.paginate_members and "cursor" not in query:
                return {"data": [], "links": {"next": "https://api.appstoreconnect.apple.com" + route + "?cursor=next"}}
            return {"data": self.members}
        if route == "/v1/betaGroups/internal/relationships/builds":
            return {"data": self.attached}
        if route == "/v1/builds/mac-7/buildBetaDetail":
            return {"data": {"attributes": {"internalBuildState": self.internal_state}}}
        if route == "/v1/apps/musia/appStoreVersions":
            return {"data": self.formal}
        if route.startswith("/v1/appStoreVersions/") and route.endswith("/build"):
            return {"data": self.formal_builds[route.split("/")[3]]}
        raise AssertionError("Unexpected endpoint: " + route)


class MacInviteTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.runtime = self.root / "store/.runtime"
        self.runtime.parent.mkdir(mode=0o700)
        self.runtime.mkdir(mode=0o700)
        contexts = contextlib.ExitStack()
        self.addCleanup(contexts.close)
        contexts.enter_context(patch.object(s, "ROOT", self.root))
        contexts.enter_context(patch.object(s, "RUNTIME", self.runtime))
        contexts.enter_context(patch.dict("os.environ", {"MUSIA_STORE_CONFIG": str(self.runtime / "config.json")}))
        contexts.enter_context(patch.object(socket.socket, "connect", side_effect=AssertionError("Offline tests only")))
        contexts.enter_context(patch("urllib.request.urlopen", side_effect=AssertionError("No real provider access")))
        self.cfg = {"bundle_id": s.BUNDLE, "apple_team": s.TEAM, "google_developer_id": s.DEVELOPER,
                    "self_tester_email": "owner@example.test", "apple_certificate_sha1": "A" * 40}
        s.write_private(self.runtime / "config.json", self.cfg)
        s.write_private(self.root / "store/release.json", dict(self.cfg, apple_app_id="musia", formal_submission_enabled=False))
        self.package = self.runtime / "Musia.pkg"
        s.write_private(self.package, b"fake signed universal PKG fixture, never uploaded")
        self.sha = s.digest(self.package)
        self.receipt = self.runtime / "macos-uploads" / self.sha / "upload-accepted.json"
        self.upload = {"at": "2026-10-09T06:07:00+00:00", "platform": "MAC_OS", "bundle_id": s.BUNDLE,
                       "version": "0.2.0", "build": "7", "package_sha256": self.sha,
                       "signer_sha1": self.cfg["apple_certificate_sha1"], "architectures": ["arm64", "x86_64"]}
        s.write_private(self.receipt, self.upload)
        self.api = FakeApple(self, self.cfg)
        self.factory = contexts.enter_context(patch.object(s, "Apple", return_value=self.api))

    def invite(self, **kwargs):
        return m.invite(self.package, self.receipt, self.sha, "0.2.0", "7", **kwargs)

    def provider_journal(self):
        digest = hashlib.sha256(b"musia-internal-builds-mac-7").hexdigest()
        return self.runtime / "operations" / (digest + ".json")

    def attached(self):
        self.api.attached.append({"type": "builds", "id": "mac-7"})
        self.api.internal_state = "IN_BETA_TESTING"

    def assert_refused(self):
        with self.assertRaises((s.GuardError, OSError)):
            self.invite(confirm=True)
        self.assertFalse(self.api.posts)

    def test_default_plan_has_no_writes_and_no_private_identity_output(self):
        before = {p: p.read_bytes() for p in self.runtime.rglob("*") if p.is_file()}
        value = self.invite()
        self.assertEqual(value["state"], "attachment_plan_only")
        self.assertTrue(value["would_attach"])
        self.assertFalse(value["available"])
        self.assertFalse(self.api.posts)
        self.assertEqual(before, {p: p.read_bytes() for p in self.runtime.rglob("*") if p.is_file()})
        self.assertNotIn(self.cfg["self_tester_email"], json.dumps(value))
        self.assertNotIn("tester_id", value)

    def test_confirm_attaches_only_build_and_retains_existing_members_and_builds(self):
        before = copy.deepcopy((self.api.members, self.api.formal_builds))
        value = self.invite(confirm=True)
        self.assertEqual(value["state"], "available_to_internal_owner")
        self.assertTrue(value["available"])
        self.assertTrue(value["formal_attachments_preserved"])
        self.assertEqual(len(self.api.posts), 1)
        self.assertEqual(before, (self.api.members, self.api.formal_builds))
        self.assertIn({"type": "builds", "id": "old-build"}, self.api.attached)
        for p in [m.operation_path(self.sha), self.provider_journal(),
                  self.runtime / "macos-internal" / self.sha / "readback.json"]:
            self.assertEqual(p.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.invite(confirm=True)["state"], "available_to_internal_owner")
        self.assertEqual(len(self.api.posts), 1)

    def test_existing_attachment_never_posts(self):
        self.attached()
        self.assertTrue(self.invite(confirm=True)["available"])
        self.assertFalse(self.api.posts)

    def test_attachment_does_not_claim_availability_before_beta_testing(self):
        self.api.activate_on_post = False
        value = self.invite(confirm=True)
        self.assertEqual(value["state"], "attached_availability_pending")
        self.assertFalse(value["available"])
        self.api.internal_state = "IN_BETA_TESTING"
        self.assertTrue(self.invite(readback=True)["available"])
        self.assertEqual(len(self.api.posts), 1)

    def test_receipt_identity_hash_version_and_signer_are_required(self):
        for key, wrong in [("platform", "IOS"), ("bundle_id", "art.other"), ("version", "0.1.3"),
                           ("build", "6"), ("package_sha256", "0" * 64), ("signer_sha1", "B" * 40),
                           ("architectures", ["arm64"]), ("at", "")]:
            with self.subTest(key=key):
                s.write_private(self.receipt, dict(self.upload, **{key: wrong}))
                self.assert_refused()
        self.factory.assert_not_called()

    def test_only_canonical_accepted_upload_receipt_is_allowed(self):
        for name in ["inspection.json", "validation.json", "upload-started.json"]:
            with self.subTest(name=name):
                other = self.receipt.with_name(name)
                s.write_private(other, self.upload)
                with self.assertRaises(s.GuardError):
                    m.invite(self.package, other, self.sha, "0.2.0", "7", confirm=True)
        self.factory.assert_not_called()

    def test_missing_public_or_symlinked_receipt_is_refused(self):
        self.receipt.chmod(0o644)
        self.assert_refused()
        self.receipt.unlink()
        self.assert_refused()
        other = self.runtime / "copy.json"
        s.write_private(other, self.upload)
        self.receipt.symlink_to(other)
        self.assert_refused()

    def test_wrong_package_bytes_and_symlink_are_refused(self):
        s.write_private(self.package, b"changed")
        self.assert_refused()
        self.package.unlink()
        self.package.symlink_to(self.receipt)
        self.assert_refused()

    def test_invalid_selectors_fail_before_provider_calls(self):
        for sha, version, build in [("../unsafe", "0.2.0", "7"), (self.sha, "0.2.0/other", "7"),
                                    (self.sha, "0.2.0", "7?filter=other")]:
            with self.subTest(sha=sha, version=version, build=build), self.assertRaises(s.GuardError):
                m.invite(self.package, self.receipt, sha, version, build)
        self.factory.assert_not_called()

    def test_same_number_ios_build_is_not_selected(self):
        self.api.builds.insert(0, {"id": "ios-7", "attributes": {"version": "7", "processingState": "VALID"}})
        self.api.pre["ios-7"] = {"platform": "IOS", "version": "0.2.0"}
        self.assertEqual(self.invite(confirm=True)["build_id"], "mac-7")
        self.assertEqual(len(self.api.posts), 1)

    def test_missing_duplicate_or_wrong_platform_build_is_refused(self):
        original = copy.deepcopy(self.api.builds)
        for builds in [[], original * 2]:
            with self.subTest(builds=builds):
                self.api.builds = builds
                self.assert_refused()
        self.api.builds = original
        self.api.pre["mac-7"]["platform"] = "IOS"
        self.assert_refused()

    def test_wrong_marketing_version_or_build_app_is_refused(self):
        self.api.pre["mac-7"]["version"] = "0.1.3"
        self.assert_refused()
        self.api.pre["mac-7"]["version"] = "0.2.0"
        self.api.build_app["id"] = "another-app"
        self.assert_refused()

    def test_not_valid_or_expired_build_is_refused(self):
        for state in ["PROCESSING", "FAILED", "INVALID", None]:
            with self.subTest(state=state):
                self.api.builds[0]["attributes"]["processingState"] = state
                self.assert_refused()
        self.api.builds[0]["attributes"].update(processingState="VALID", expired=True)
        self.assert_refused()

    def test_wrong_configured_app_id_or_formal_enabled_is_refused(self):
        for fields in [{"apple_app_id": "another"}, {"formal_submission_enabled": True}]:
            release = dict(self.cfg, apple_app_id="musia", formal_submission_enabled=False)
            s.write_private(self.root / "store/release.json", dict(release, **fields))
            self.assert_refused()

    def test_group_must_exist_uniquely_and_be_restricted_internal(self):
        original = copy.deepcopy(self.api.groups)
        for groups in [[], original * 2]:
            self.api.groups = groups
            self.assert_refused()
        for field, value in [("name", "Other Internal"), ("isInternalGroup", False),
                             ("hasAccessToAllBuilds", True), ("hasAccessToAllBuilds", None)]:
            with self.subTest(field=field):
                self.api.groups = copy.deepcopy(original)
                self.api.groups[0]["attributes"][field] = value
                self.assert_refused()

    def test_tester_is_existing_unique_owner_associated_with_exact_app(self):
        original = copy.deepcopy(self.api.testers)
        for testers in [[], original * 2, [{"id": "other", "attributes": {"email": "other@example.test"}}]]:
            self.api.testers = testers
            self.assert_refused()
        self.api.testers = original
        self.api.tester_apps = [{"id": "other", "attributes": {"bundleId": s.BUNDLE}}]
        self.assert_refused()

    def test_owner_must_already_be_in_group_no_tester_attachment(self):
        self.api.members = []
        self.assert_refused()

    def test_owner_membership_pagination_is_read_fully(self):
        self.api.paginate_members = True
        self.assertTrue(self.invite(confirm=True)["available"])

    def test_missing_beta_detail_fails_closed(self):
        self.api.internal_state = None
        self.assert_refused()

    def test_unknown_after_apply_is_reconciled_without_second_post(self):
        self.api.post_failure = "after"
        value = self.invite(confirm=True)
        self.assertTrue(value["available"])
        self.assertEqual(s.read_json(self.provider_journal())["state"], "started")
        self.assertTrue(self.invite(readback=True)["available"])
        self.assertTrue(self.invite(confirm=True)["available"])
        self.assertEqual(len(self.api.posts), 1)

    def test_unknown_before_apply_never_retries_even_with_confirm(self):
        self.api.post_failure = "before"
        value = self.invite(confirm=True)
        self.assertEqual(value["state"], "attachment_unconfirmed_readback_required")
        self.assertFalse(value["would_attach"])
        for kwargs in [{}, {"confirm": True}, {"readback": True}]:
            self.assertEqual(self.invite(**kwargs)["state"], value["state"])
        self.assertEqual(len(self.api.posts), 1)
        self.attached()
        self.assertTrue(self.invite(readback=True)["available"])
        self.assertEqual(len(self.api.posts), 1)

    def test_accepted_post_without_visible_relationship_is_not_success(self):
        self.api.attach_on_post = False
        value = self.invite(confirm=True)
        self.assertFalse(value["available"])
        self.assertEqual(value["state"], "attachment_unconfirmed_readback_required")
        self.invite(confirm=True)
        self.assertEqual(len(self.api.posts), 1)

    def test_process_crash_retains_intent_and_prevents_retry(self):
        self.api.post_failure = "crash"
        with self.assertRaises(KeyboardInterrupt):
            self.invite(confirm=True)
        self.assertEqual(s.read_json(m.operation_path(self.sha))["state"], "intent")
        self.invite(confirm=True)
        self.assertEqual(len(self.api.posts), 1)

    def test_readback_failure_preserves_unknown_and_suppresses_private_error(self):
        self.api.on_post = lambda: setattr(self.api, "readback_failure", True)
        with self.assertRaises(s.GuardError) as error:
            self.invite(confirm=True)
        self.assertNotIn("private response", str(error.exception))
        self.assertEqual(s.read_json(m.operation_path(self.sha))["state"], "readback_required")
        self.api.readback_failure = False
        self.assertTrue(self.invite(readback=True)["available"])
        self.assertEqual(len(self.api.posts), 1)

    def test_legacy_operation_journal_prevents_repeating_old_script(self):
        for state in ["started", "accepted", "rejected"]:
            with self.subTest(state=state):
                s.write_private(self.provider_journal(), {"operation": "musia-internal-builds-mac-7", "state": state})
                self.assertFalse(self.invite(confirm=True)["would_attach"])
        self.assertFalse(self.api.posts)
        self.attached()
        self.assertTrue(self.invite(readback=True)["available"])

    def test_mismatched_legacy_journal_is_not_ignored(self):
        s.write_private(self.provider_journal(), {"operation": "musia-internal-builds-mac-7", "state": "started",
                                                "path": "/v1/betaGroups/other/relationships/builds"})
        self.assert_refused()

    def test_journal_identity_and_receipt_are_pinned_across_retries(self):
        self.api.post_failure = "before"
        self.invite(confirm=True)
        journal = s.read_json(m.operation_path(self.sha))
        journal["identity"]["group_id"] = "another"
        s.write_private(m.operation_path(self.sha), journal)
        with self.assertRaises(s.GuardError):
            self.invite(confirm=True)
        journal["identity"]["group_id"] = "internal"
        s.write_private(m.operation_path(self.sha), journal)
        s.write_private(self.receipt, dict(self.upload, at="2026-10-10T00:00:00Z"))
        with self.assertRaises(s.GuardError):
            self.invite(confirm=True)
        self.assertEqual(len(self.api.posts), 1)

    def test_formal_attachment_change_is_flagged_without_restoration(self):
        self.api.on_post = lambda: self.api.formal_builds.update({"formal-mac": {"id": "changed-by-peer"}})
        value = self.invite(confirm=True)
        self.assertEqual(value["state"], "formal_attachment_changed_readback_required")
        self.assertFalse(value["available"])
        self.assertFalse(self.invite(confirm=True)["formal_attachments_preserved"])
        self.assertEqual(len(self.api.posts), 1)

    def test_independent_review_progress_does_not_block_attachment(self):
        self.api.on_post = lambda: self.api.formal[0]["attributes"].update(appStoreState="IN_REVIEW")
        self.assertTrue(self.invite(confirm=True)["available"])

    def test_readback_mode_never_dispatches_a_missing_attachment(self):
        value = self.invite(readback=True)
        self.assertEqual(value["state"], "not_attached")
        self.assertFalse(value["would_attach"])
        self.assertFalse(self.api.posts)
        self.assertFalse(m.operation_path(self.sha).exists())

    def test_shared_invitation_lock_prevents_concurrent_confirm(self):
        with s.lock("apple-invite"), self.assertRaises(s.GuardError):
            self.invite(confirm=True)
        self.factory.assert_not_called()

    def test_cli_default_confirm_and_readback_are_explicit(self):
        args = [str(self.package), "--upload-receipt", str(self.receipt), "--sha256", self.sha,
                "--version", "0.2.0", "--build", "7"]
        for flags, state in [([], "attachment_plan_only"), (["--confirm"], "available_to_internal_owner"),
                             (["--readback"], "available_to_internal_owner")]:
            with self.subTest(flags=flags), contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(m.main(args + flags), 0)
                self.assertEqual(json.loads(out.getvalue())["state"], state)
        self.assertEqual(len(self.api.posts), 1)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            m.main(args + ["--confirm", "--readback"])

    def test_cli_pending_outcome_is_nonzero_and_errors_are_sanitized(self):
        args = [str(self.package), "--upload-receipt", str(self.receipt), "--sha256", self.sha,
                "--version", "0.2.0", "--build", "7", "--confirm"]
        self.api.post_failure = "before"
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(m.main(args), 2)
            self.assertNotIn("private provider body", out.getvalue())
        with patch.object(m, "invite", side_effect=OSError("private path/key")), contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(m.main(args), 1)
            self.assertNotIn("private path/key", err.getvalue())

    def test_cli_readback_missing_and_existing_pending_attachment_are_nonzero(self):
        args = [str(self.package), "--upload-receipt", str(self.receipt), "--sha256", self.sha,
                "--version", "0.2.0", "--build", "7"]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(m.main(args + ["--readback"]), 2)
            self.api.attached.append({"type": "builds", "id": "mac-7"})
            self.assertEqual(m.main(args + ["--confirm"]), 2)
        self.assertFalse(self.api.posts)


if __name__ == "__main__":
    unittest.main()
