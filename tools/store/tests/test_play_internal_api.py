"""Offline tests only: fake Play sessions and temporary signed-receipt fixtures."""
import contextlib
import copy
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import play_internal_api as p
import storelib as s


class Response:
    def __init__(self, value=None, status=200, malformed=False):
        self.status_code = status
        self.value = copy.deepcopy(value or {})
        self.content = json.dumps(self.value).encode() if status != 204 else b""
        self.malformed = malformed

    def json(self):
        if self.malformed:
            raise ValueError("private provider body must not leak")
        return self.value


class FakePlay:
    """A transactional provider model; tracks are live only after commit."""

    def __init__(self, case):
        self.case = case
        self._max_refresh_attempts = 2
        self.mount = Mock()
        self.trust_env = True
        self.calls = []
        self.live_tracks = {"kind": "androidpublisher#tracksListResponse", "tracks": [
            {"track": "internal", "releases": [{"name": "previous", "versionCodes": ["6"], "status": "completed"}]},
            {"track": "production", "releases": [{"name": "production", "versionCodes": ["4"],
                "status": "inProgress", "userFraction": 0.2, "countryTargeting": {"countries": ["US"]},
                "releaseNotes": [{"language": "en-US", "text": "Keep this"}], "inAppUpdatePriority": 3}]},
            {"track": "wear:production", "releases": []},
            {"track": "closed-test", "releases": [{"versionCodes": ["5"], "status": "halted"}]},
        ]}
        self.initial_tracks = copy.deepcopy(self.live_tracks)
        self.live_bundles = {"bundles": [{"versionCode": 6, "sha256": "6" * 64}]}
        self.edits = {}
        self.counter = 0
        self.fail_action = None
        self.fail_response = None
        self.fail_after_apply = False
        self.change_noninternal = False
        self.change_before_update = False
        self.bad_upload_hash = False
        self.on_request = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def request(self, method, url, **kwargs):
        self.case.assertFalse(kwargs["allow_redirects"])
        self.case.assertEqual(self._max_refresh_attempts, 0)
        self.case.assertFalse(self.trust_env)
        self.calls.append((method, url, kwargs))
        if method != "GET":
            operation = s.read_json(p.operation_path("7"))
            intents = [e for e in operation["steps"].values()
                       if e["state"] == "intent" and e["method"] == method and e["url"] == url]
            self.case.assertEqual(len(intents), 1, "Durable intent must exist before every mutation")
        action = self.action(method, url)
        if self.on_request:
            self.on_request(action)
        if action == self.fail_action and not self.fail_after_apply:
            return self.failure()
        response = self.apply(action, method, url, kwargs)
        if action == self.fail_action and self.fail_after_apply:
            return self.failure()
        return response

    def failure(self):
        if self.fail_response:
            return self.fail_response
        raise TimeoutError("sensitive provider credentials/body")

    @staticmethod
    def action(method, url):
        if url == p.BASE + "/edits" and method == "POST":
            return "create"
        if url.startswith(p.UPLOAD_BASE) and method == "POST":
            return "upload"
        if ":commit" in url:
            return "commit"
        if method == "PUT":
            return "update"
        if method == "DELETE":
            return "delete"
        return url.rsplit("/", 1)[-1] if url.endswith(("/tracks", "/bundles")) else "get"

    def apply(self, action, method, url, kwargs):
        if action == "create":
            self.counter += 1
            eid = "edit-" + str(self.counter)
            self.edits[eid] = {"tracks": copy.deepcopy(self.live_tracks), "bundles": copy.deepcopy(self.live_bundles)}
            self.case.assertEqual(kwargs["json"], {})
            return Response({"id": eid})
        eid = url.split("/edits/")[1].split("/")[0].split(":")[0]
        if eid not in self.edits:
            return Response(status=404)
        edit = self.edits[eid]
        if action == "get":
            return Response({"id": eid})
        if action == "upload":
            self.case.assertEqual(url, p.UPLOAD_BASE + "/edits/" + eid + "/bundles?uploadType=media")
            self.case.assertEqual(kwargs["data"].read(), self.case.artifact_bytes)
            self.case.assertEqual(kwargs["headers"], {"Content-Type": "application/octet-stream"})
            self.case.assertEqual(kwargs["timeout"], (10, 180))
            bundle = {"versionCode": 7, "sha256": "0" * 64 if self.bad_upload_hash else self.case.build["artifact_sha256"]}
            edit["bundles"]["bundles"].append(bundle)
            if self.change_before_update:
                edit["tracks"]["tracks"][0]["releases"][0]["name"] = "concurrent UI change"
            return Response(bundle)
        if action == "update":
            self.case.assertEqual(self.live_tracks, self.initial_tracks, "Published tracks changed before commit")
            self.case.assertTrue(url.endswith("/tracks/internal"))
            edit["tracks"]["tracks"][0] = copy.deepcopy(kwargs["json"])
            if self.change_noninternal:
                edit["tracks"]["tracks"][1]["releases"][0]["userFraction"] = 0.9
            return Response(kwargs["json"])
        if action == "commit":
            self.case.assertEqual(url, p.BASE + "/edits/" + eid + ":commit" + p.COMMIT_QUERY)
            self.case.assertNotIn("json", kwargs)
            self.case.assertNotIn("data", kwargs)
            self.case.assertEqual(self.live_tracks, self.initial_tracks)
            self.live_tracks = copy.deepcopy(edit["tracks"])
            self.live_bundles = copy.deepcopy(edit["bundles"])
            del self.edits[eid]
            return Response({"id": eid})
        if action == "delete":
            del self.edits[eid]
            return Response(status=204)
        if action in {"tracks", "bundles"}:
            return Response(edit[action])
        raise AssertionError("Unbounded request: " + url)


class PlayInternalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.runtime = self.root / "store/.runtime"
        self.runtime.mkdir(parents=True, mode=0o700)
        contexts = contextlib.ExitStack()
        self.addCleanup(contexts.close)
        contexts.enter_context(patch.object(s, "ROOT", self.root))
        contexts.enter_context(patch.object(s, "RUNTIME", self.runtime))
        # Accidental real transport is an immediate test failure, not a live call.
        contexts.enter_context(patch.object(socket.socket, "connect", side_effect=AssertionError("Tests must stay offline")))
        source = self.root / "apps/android"
        source.mkdir(parents=True)
        self.source = source / "source.kt"
        self.source.write_text("test source")
        (self.root / "store/release.json").write_text(json.dumps({
            "bundle_id": s.BUNDLE, "apple_team": s.TEAM, "google_developer_id": s.DEVELOPER,
            "formal_submission_enabled": False, "version": "0.1.0", "android_version_code": 7, "ios_build": "7"}))
        self.artifact_bytes = b"unit fixture only, not an actual signed AAB"
        self.artifact = self.runtime / "Musia.aab"
        s.write_private(self.artifact, self.artifact_bytes)
        self.build = {"state": "signed", "platform": "android", "bundle_id": s.BUNDLE,
                      "version": "0.1.0", "build_number": "7", "source_sha256": s.source_sha("android"),
                      "artifact": str(self.artifact), "artifact_sha256": s.digest(self.artifact)}
        self.build_path = self.runtime / "build.json"
        s.write_private(self.build_path, self.build)
        evidence = self.runtime / "evidence.txt"
        s.write_private(evidence, b"mock QA evidence")
        self.qa = {"platform": "android", "bundle_id": s.BUNDLE, "source_sha256": self.build["source_sha256"],
                   "artifact_sha256": self.build["artifact_sha256"], "build_receipt_sha256": s.digest(self.build_path),
                   "reviewed_at": s.now(), "qa_environment": "mock only", "scope": "internal-owner-test",
                   "production_qualified": False, "known_limitations": ["Not device QA"],
                   "checks": {c: {"status": "passed", "evidence": str(evidence), "sha256": s.digest(evidence)}
                              for c in s.INTERNAL_BETA_CHECKS}}
        self.qa_path = self.runtime / "qa.json"
        s.write_private(self.qa_path, self.qa)
        self.key = self.runtime / "fake-service-account.json"
        s.write_private(self.key, {"type": "unit-fixture"})
        self.handoff = self.runtime / "parent.json"
        self.coordination = {"schema": 1, "bundle_id": p.PACKAGE, "track": "internal", "version_code": "7",
                             "artifact_sha256": self.build["artifact_sha256"], "parent_session": "unit-parent",
                             "checked_at": s.now(), **{flag: True for flag in p.COORDINATION_FLAGS}}
        s.write_private(self.handoff, self.coordination)
        self.provider = FakePlay(self)
        self.verifier = contexts.enter_context(patch.object(p, "GoogleVerifier"))
        self.verifier.return_value.session.return_value = self.provider

    def execute(self):
        return p.run(self.build_path, self.qa_path, execute=True, service_account_file=self.key,
                     coordination_file=self.handoff)

    def readback(self):
        return p.readback(p.operation_path("7"), service_account_file=self.key, coordination_file=self.handoff)

    def journal(self):
        return s.read_json(p.operation_path("7"))

    def actions(self):
        return [self.provider.action(m, u) for m, u, _ in self.provider.calls]

    def test_default_plan_is_offline_without_credentials_or_writes(self):
        before = set(self.runtime.rglob("*"))
        with patch.object(s, "snapshot_artifact", side_effect=AssertionError("Plan must not snapshot")):
            result = p.run(self.build_path, self.qa_path)
        self.assertEqual(result["state"], "planned")
        self.assertFalse(result["network"])
        self.assertEqual(before, set(self.runtime.rglob("*")))
        self.verifier.assert_not_called()

    def test_cli_default_and_mutually_exclusive_modes(self):
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(p.main(["--build-receipt", str(self.build_path), "--qa", str(self.qa_path)]), 0)
        self.assertFalse(json.loads(stdout.getvalue())["network"])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            p.main(["--execute", "--readback", "anything"])
        self.verifier.assert_not_called()

    def test_wrong_app_unsigned_artifact_and_non_android_fail_before_session(self):
        for overrides in ({"bundle_id": "another.app"}, {"state": "unsigned"}, {"platform": "ios"}):
            with self.subTest(overrides=overrides):
                s.write_private(self.build_path, dict(self.build, **overrides))
                with self.assertRaises(s.GuardError):
                    self.execute()
        self.verifier.assert_not_called()

    def test_changed_source_fails_before_session(self):
        self.source.write_text("unreviewed changes")
        with self.assertRaisesRegex(s.GuardError, "Source changed"):
            self.execute()
        self.verifier.assert_not_called()

    def test_changed_artifact_fails_before_session(self):
        s.write_private(self.artifact, b"different bytes")
        with self.assertRaisesRegex(s.GuardError, "hash/QA"):
            self.execute()
        self.verifier.assert_not_called()

    def test_pending_ui_qa_and_wrong_scope_fail_before_session(self):
        for overrides in ({"scope": "production"}, {"production_qualified": True}, {"known_limitations": []}):
            s.write_private(self.qa_path, dict(self.qa, **overrides))
            with self.assertRaises(s.GuardError):
                self.execute()
        self.qa["checks"]["native_ui"]["status"] = "pending"
        s.write_private(self.qa_path, self.qa)
        with self.assertRaisesRegex(s.GuardError, "native_ui"):
            self.execute()
        self.verifier.assert_not_called()

    def test_parent_coordination_is_mandatory_fresh_exact_and_all_flags_true(self):
        bad = [{flag: False} for flag in p.COORDINATION_FLAGS]
        bad += [{"parent_session": ""}, {"bundle_id": "other.app"}, {"track": "production"},
                {"version_code": "8"}, {"artifact_sha256": "0" * 64}, {"checked_at": "invalid"},
                {"checked_at": "2000-01-01T00:00:00+00:00"}, {"checked_at": "2099-01-01T00:00:00+00:00"},
                {"checked_at": "2026-10-09T00:00:00"}]
        for override in bad:
            with self.subTest(override=override):
                s.write_private(self.handoff, dict(self.coordination, **override))
                with self.assertRaises(s.GuardError):
                    self.execute()
        with self.assertRaises(s.GuardError):
            p.run(self.build_path, self.qa_path, execute=True, service_account_file=self.key)
        self.verifier.assert_not_called()

    def test_one_shot_media_upload_scoped_paths_baseline_and_noninternal_preserved(self):
        result = self.execute()
        self.assertEqual(result["state"], "committed_unverified")
        journal = self.journal()
        self.assertEqual(journal["baseline_tracks"], self.provider.initial_tracks)
        self.assertEqual(self.provider.live_tracks["tracks"][1:], self.provider.initial_tracks["tracks"][1:])
        self.assertEqual(self.provider.live_tracks["tracks"][0], p.target_track(journal))
        self.assertEqual(self.actions().count("upload"), 1)
        self.assertEqual(self.actions().count("commit"), 1)
        self.verifier.assert_called_once_with({"service_account_file": str(self.key)})
        self.assertNotEqual(journal["snapshot"], str(self.artifact))
        self.assertEqual(s.digest(journal["snapshot"]), self.build["artifact_sha256"])
        self.assertEqual(p.operation_path("7").stat().st_mode & 0o777, 0o600)
        adapter = self.provider.mount.call_args.args[1]
        self.assertEqual(adapter.max_retries.total, 0)
        for method, url, _ in self.provider.calls:
            self.assertTrue(url.startswith(p.BASE + "/edits") or url.startswith(p.UPLOAD_BASE + "/edits"))
            self.assertNotRegex(url, r"pricing|products|subscriptions|listings|reviews|declarations")
            if method == "PUT":
                self.assertTrue(url.endswith("/tracks/internal"))
        count = len(self.provider.calls)
        with self.assertRaisesRegex(s.GuardError, "already attempted"):
            self.execute()
        self.assertEqual(len(self.provider.calls), count)

    def test_draft_unknown_and_pending_internal_states_stop_before_upload(self):
        baseline = copy.deepcopy(self.provider.live_tracks)
        for index, status in ((0, "draft"), (1, "draft"), (0, "inProgress"), (0, "halted"), (1, "futureState"), (0, None)):
            with self.subTest(track=index, status=status):
                self.provider.live_tracks = copy.deepcopy(baseline)
                self.provider.live_tracks["tracks"][index]["releases"][0]["status"] = status
                with self.assertRaises(s.GuardError):
                    self.execute()
                self.assertNotIn("upload", self.actions())
                self.assertNotIn("commit", self.actions())
                p.operation_path("7").unlink()  # Separate fake executions, never a real operation.

    def test_noninternal_change_blocks_commit_and_keeps_published_track(self):
        self.provider.change_noninternal = True
        with self.assertRaisesRegex(s.GuardError, "Non-internal"):
            self.execute()
        self.assertNotIn("commit", self.actions())
        self.assertEqual(self.provider.live_tracks, self.provider.initial_tracks)

    def test_track_drift_before_update_blocks_update(self):
        self.provider.change_before_update = True
        with self.assertRaisesRegex(s.GuardError, "baseline changed"):
            self.execute()
        self.assertNotIn("update", self.actions())
        self.assertNotIn("commit", self.actions())

    def test_provider_bundle_hash_mismatch_blocks_track_and_commit(self):
        self.provider.bad_upload_hash = True
        with self.assertRaisesRegex(s.GuardError, "unknown"):
            self.execute()
        self.assertEqual(self.journal()["steps"]["upload_bundle"]["state"], "unknown")
        self.assertNotIn("update", self.actions())

    def test_existing_candidate_version_is_never_uploaded_again(self):
        self.provider.live_bundles["bundles"].append({"versionCode": 7, "sha256": self.build["artifact_sha256"]})
        with self.assertRaisesRegex(s.GuardError, "Version already present"):
            self.execute()
        self.assertNotIn("upload", self.actions())

    def test_unknown_upload_no_retry_and_exact_open_edit_readback(self):
        self.provider.fail_action, self.provider.fail_after_apply = "upload", True
        with self.assertRaisesRegex(s.GuardError, "outcome unknown") as error:
            self.execute()
        self.assertNotIn("sensitive", str(error.exception))
        self.assertEqual(self.journal()["state"], "unknown")
        before = len(self.provider.calls)
        with self.assertRaises(s.GuardError):
            self.execute()
        self.assertEqual(len(self.provider.calls), before)
        result = self.readback()
        self.assertEqual(result["state"], "open_edit_only_not_committed")
        self.assertTrue(result["exact_bundle_present"])
        self.assertEqual(self.actions().count("create"), 1)
        self.assertEqual(self.actions().count("upload"), 1)
        self.assertNotIn("update", self.actions())
        self.assertNotIn("commit", self.actions())
        self.assertTrue(all(method == "GET" for method, _, _ in self.provider.calls[before:]))

    def test_unknown_commit_reconciles_fresh_edit_without_double_upload(self):
        self.provider.fail_action, self.provider.fail_after_apply = "commit", True
        with self.assertRaises(s.GuardError):
            self.execute()
        self.assertEqual(self.journal()["steps"]["commit_edit"]["state"], "unknown")
        self.provider.fail_action = None
        self.source.write_text("source can move after upload; readback uses original operation")
        result = self.readback()
        self.assertEqual(result["state"], "verified")
        self.assertEqual(result["edit_id"], "edit-2")
        self.assertEqual(self.journal()["state"], "verified")
        self.assertEqual(self.actions().count("upload"), 1)
        self.assertEqual(self.actions().count("commit"), 1)
        self.assertEqual(self.actions().count("delete"), 1)
        self.assertEqual(self.provider.edits, {})
        self.assertEqual(self.journal()["readbacks"][0]["tracks"], self.provider.live_tracks)

    def test_fresh_readback_tracks_drift_is_not_success(self):
        self.execute()
        self.provider.live_tracks["tracks"][1]["releases"][0]["name"] = "changed externally"
        with self.assertRaisesRegex(s.GuardError, "Non-internal"):
            self.readback()
        self.assertNotEqual(self.journal()["state"], "verified")
        self.assertEqual(self.journal()["readbacks"][-1]["state"], "unresolved")
        self.assertEqual(self.provider.edits, {})

    def test_fresh_readback_hash_mismatch_is_not_success(self):
        self.execute()
        self.provider.live_bundles["bundles"][-1]["sha256"] = "0" * 64
        with self.assertRaisesRegex(s.GuardError, "version/hash mismatch"):
            self.readback()
        self.assertNotEqual(self.journal()["state"], "verified")
        self.assertEqual(self.provider.edits, {})

    def test_later_readback_does_not_keep_stale_verified_status(self):
        self.execute()
        self.assertEqual(self.readback()["state"], "verified")
        self.provider.live_tracks["tracks"][1]["releases"][0]["name"] = "later unrelated work"
        with self.assertRaisesRegex(s.GuardError, "Non-internal"):
            self.readback()
        self.assertEqual(self.journal()["state"], "unresolved")
        self.assertEqual(self.actions().count("upload"), 1)

    def test_fresh_readback_rejects_missing_candidate_on_internal_track(self):
        self.execute()
        self.provider.live_tracks["tracks"][0] = self.provider.initial_tracks["tracks"][0]
        with self.assertRaisesRegex(s.GuardError, "Internal release readback mismatch"):
            self.readback()
        self.assertEqual(self.journal()["state"], "unresolved")
        self.assertEqual(self.actions().count("update"), 1)

    def test_unknown_update_is_observed_without_commit_or_replay(self):
        self.provider.fail_action, self.provider.fail_after_apply = "update", True
        with self.assertRaises(s.GuardError):
            self.execute()
        result = self.readback()
        self.assertEqual(result["state"], "open_edit_only_not_committed")
        self.assertTrue(result["exact_bundle_present"])
        self.assertEqual(self.actions().count("upload"), 1)
        self.assertEqual(self.actions().count("update"), 1)
        self.assertNotIn("commit", self.actions())
        self.assertEqual(self.provider.live_tracks, self.provider.initial_tracks)

    def test_noninternal_track_removal_or_addition_is_not_preserved(self):
        baseline = self.provider.initial_tracks
        for tracks in (baseline["tracks"][:1], baseline["tracks"] + [{"track": "new-test", "releases": []}]):
            with self.subTest(tracks=tracks), self.assertRaises(s.GuardError):
                p.preserve_noninternal(baseline, {"tracks": tracks})

    def test_duplicate_or_incomplete_inventory_fails_closed(self):
        baseline = self.provider.initial_tracks
        for tracks in ({}, {"tracks": []}, {"tracks": baseline["tracks"], "nextPageToken": "more"},
                       {"tracks": baseline["tracks"] + [baseline["tracks"][0]]}):
            with self.subTest(tracks=tracks), self.assertRaises(s.GuardError):
                p.tracks_by_name(tracks)
        for bundles in ({}, {"bundles": [], "nextPageToken": "more"}, {"bundles": [{"versionCode": True}]},
                        {"bundles": [{"versionCode": 7}, {"versionCode": 7}]}):
            with self.subTest(bundles=bundles), self.assertRaises(s.GuardError):
                p.bundle_rows(bundles)

    def test_provider_errors_redirects_and_malformed_success_never_retry(self):
        for response in (Response(status=401), Response(status=409), Response(status=500),
                         Response(status=302), Response({"id": "edit-1"}, malformed=True),
                         Response({"id": "../other"})):
            with self.subTest(response=response.status_code):
                self.provider.fail_action, self.provider.fail_response = "create", response
                before = len(self.provider.calls)
                with self.assertRaises(s.GuardError):
                    self.execute()
                with self.assertRaises(s.GuardError):
                    self.execute()
                self.assertEqual(len(self.provider.calls), before + 1)
                self.assertEqual(self.journal()["steps"]["create_edit"]["state"], "unknown")
                with self.assertRaises(s.GuardError):
                    self.readback()
                self.assertEqual(len(self.provider.calls), before + 1)
                p.operation_path("7").unlink()

    def test_no_mutation_if_journal_intent_cannot_be_persisted(self):
        real_save = p.save
        def fail_intent(path, record):
            if record["steps"]:
                raise OSError("simulated disk full")
            real_save(path, record)
        with patch.object(p, "save", side_effect=fail_intent), self.assertRaises(OSError):
            self.execute()
        self.assertEqual(self.provider.calls, [])

    def test_parent_revocation_rechecked_before_next_mutation(self):
        def revoke(action):
            if action == "upload":
                s.write_private(self.handoff, dict(self.coordination, ui_quiescent=False))
        self.provider.on_request = revoke
        with self.assertRaisesRegex(s.GuardError, "Parent must confirm"):
            self.execute()
        self.assertNotIn("update", self.actions())
        self.assertNotIn("commit", self.actions())

    def test_source_changes_before_commit_block_commit(self):
        def change(action):
            if action == "update":
                self.source.write_text("changed during upload")
        self.provider.on_request = change
        with self.assertRaisesRegex(s.GuardError, "Source changed"):
            self.execute()
        self.assertNotIn("commit", self.actions())

    def test_shared_play_lock_prevents_parallel_execution(self):
        with s.lock("play-upload"), self.assertRaisesRegex(s.GuardError, "owns this lock"):
            self.execute()
        self.verifier.assert_not_called()

    def test_legacy_console_attempt_blocks_api_upload(self):
        s.write_private(self.runtime / "operations" / ("play-upload-" + self.build["artifact_sha256"] + ".json"),
                        {"state": "upload_dispatched_readback_required"})
        with self.assertRaisesRegex(s.GuardError, "Console upload"):
            self.execute()
        self.verifier.assert_not_called()

    def test_readback_wrong_service_account_or_operation_fails_before_network(self):
        self.execute()
        count = len(self.provider.calls)
        s.write_private(self.key, {"type": "different account"})
        with self.assertRaisesRegex(s.GuardError, "Service account differs"):
            self.readback()
        self.assertEqual(len(self.provider.calls), count)

    def test_request_vocabulary_rejects_unowned_edits_and_other_surfaces(self):
        self.execute()
        record = self.journal()
        api = p.PlayInternalAPI(self.provider, p.operation_path("7"), record, self.handoff, readback=True)
        count = len(self.provider.calls)
        for action in ("pricing", "products", "declarations", "reviews", "PATCH", "upload", "update", "commit"):
            with self.subTest(action=action), self.assertRaises(s.GuardError):
                api.request(action, edit="edit-1", step="malicious")
        for eid in ("unowned", "../other", "edit-1?track=production", "https://another.app"):
            with self.subTest(edit=eid), self.assertRaises(s.GuardError):
                api.request("tracks", edit=eid)
        with self.assertRaises(s.GuardError):
            api.request("delete", edit="edit-1", step="delete-original")
        record["bundle_id"] = "other.app"
        with self.assertRaises(s.GuardError):
            api.request("create", step="wrong-app")
        self.assertEqual(len(self.provider.calls), count)

    def test_request_layer_cannot_rename_a_step_to_replay_mutations(self):
        self.execute()
        record = self.journal()
        api = p.PlayInternalAPI(self.provider, p.operation_path("7"), record, self.handoff)
        count = len(self.provider.calls)
        for action, step in (("create", "create_edit"), ("update", "update_internal"), ("commit", "commit_edit")):
            for name in (step, "another_attempt"):
                with self.subTest(action=action, name=name), self.assertRaises(s.GuardError):
                    api.request(action, edit="edit-1", step=name)
        with Path(record["snapshot"]).open("rb") as media:
            for name in ("upload_bundle", "another_attempt"):
                with self.assertRaises(s.GuardError):
                    api.request("upload", edit="edit-1", step=name, media=media)
        self.assertEqual(len(self.provider.calls), count)

    def test_snapshot_corruption_before_upload_is_not_sent(self):
        def corrupt(action):
            if action == "bundles":
                s.write_private(Path(self.journal()["snapshot"]), b"corrupt")
        self.provider.on_request = corrupt
        with self.assertRaisesRegex(s.GuardError, "Qualified input changed"):
            self.execute()
        self.assertNotIn("upload", self.actions())

    def test_unknown_fresh_read_edit_deletion_cannot_be_retried(self):
        self.execute()
        self.provider.fail_action = "delete"
        with self.assertRaises(s.GuardError):
            self.readback()
        self.assertEqual(self.journal()["state"], "unknown")
        self.provider.fail_action = None
        with self.assertRaisesRegex(s.GuardError, "Prior read edit unresolved"):
            self.readback()
        self.assertEqual(self.actions().count("delete"), 1)
        self.assertEqual(self.actions().count("create"), 2)

    def test_unknown_read_edit_creation_cannot_be_blindly_repeated(self):
        self.execute()
        self.provider.fail_action = "create"
        with self.assertRaises(s.GuardError):
            self.readback()
        self.provider.fail_action = None
        count = self.actions().count("create")
        with self.assertRaisesRegex(s.GuardError, "Prior read edit unresolved"):
            self.readback()
        self.assertEqual(self.actions().count("create"), count)
        self.assertEqual(self.actions().count("upload"), 1)

    def test_missing_uncommitted_edit_never_opens_fresh_edit(self):
        self.provider.fail_action = "upload"
        with self.assertRaises(s.GuardError):
            self.execute()
        self.provider.edits.clear()
        with self.assertRaisesRegex(s.GuardError, "without commit intent"):
            self.readback()
        self.assertEqual(self.actions().count("create"), 1)


if __name__ == "__main__":
    unittest.main()
