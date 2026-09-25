import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import storelib as s
import musia_store as cli
import invite_play
from build_native import check_profile, android_manifest, android_config


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.runtime = self.root / "store/.runtime"
        self.runtime.mkdir(parents=True, mode=0o700)
        self.patches = [patch.object(s, "ROOT", self.root), patch.object(s, "RUNTIME", self.runtime)]
        for p in self.patches:
            p.start()
        (self.root / "apps/android").mkdir(parents=True)
        (self.root / "apps/android/source.kt").write_text("native")
        self.release = {"bundle_id": s.BUNDLE, "apple_team": s.TEAM, "google_developer_id": s.DEVELOPER,
                        "formal_submission_enabled": False, "version": "0.1.0", "android_version_code": 1, "ios_build": "1"}
        (self.root / "store/release.json").write_text(json.dumps(self.release))

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def test_private_files_reject_public_mode_and_symlink(self):
        f = self.runtime / "private.json"
        s.write_private(f, {})
        self.assertEqual(f.stat().st_mode & 0o777, 0o600)
        self.assertEqual(s.private_file(f), f)
        f.chmod(0o644)
        with self.assertRaises(s.GuardError):
            s.private_file(f)
        link = self.runtime / "link"
        link.symlink_to(f)
        with self.assertRaises(s.GuardError):
            s.private_file(link)

    def test_source_digest_ignores_builds_but_not_code(self):
        before = s.source_sha("android")
        build = self.root / "apps/android/build"
        build.mkdir()
        (build / "generated").write_text("noise")
        self.assertEqual(before, s.source_sha("android"))
        (self.root / "apps/android/source.kt").write_text("changed")
        self.assertNotEqual(before, s.source_sha("android"))

    def test_source_rejects_symlinks(self):
        (self.root / "apps/android/secret").symlink_to(self.root / "store/release.json")
        with self.assertRaises(s.GuardError):
            s.source_sha("android")

    def test_other_app_identity_and_formal_submit_are_rejected(self):
        for field, value in (("bundle_id", "art.lazying.bunko"), ("formal_submission_enabled", True),
                             ("google_developer_id", "123")):
            data = dict(self.release, **{field: value})
            (self.root / "store/release.json").write_text(json.dumps(data))
            with self.assertRaises(s.GuardError):
                s.release()

    def fixture(self):
        artifact = self.runtime / "Musia.aab"
        s.write_private(artifact, b"fixture-not-a-real-signature")
        build = {"state": "signed", "platform": "android", "bundle_id": s.BUNDLE,
                 "version": "0.1.0", "build_number": "1", "source_sha256": s.source_sha("android"),
                 "artifact": str(artifact), "artifact_sha256": s.digest(artifact)}
        receipt = self.runtime / "build.json"
        s.write_private(receipt, build)
        evidence = self.runtime / "evidence.txt"
        s.write_private(evidence, b"test evidence fixture")
        qa = {"platform": "android", "bundle_id": s.BUNDLE, "source_sha256": build["source_sha256"],
              "artifact_sha256": build["artifact_sha256"], "build_receipt_sha256": s.digest(receipt),
              "reviewed_at": s.now(), "qa_environment": "unit fixture, not device QA", "checks": {
                  key: {"status": "passed", "evidence": str(evidence), "sha256": s.digest(evidence)} for key in s.CHECKS}}
        qa_path = self.runtime / "qa.json"
        s.write_private(qa_path, qa)
        return receipt, qa_path, build, qa

    def test_qa_is_bound_to_exact_source_artifact_receipt_and_evidence(self):
        receipt, qa_path, build, qa = self.fixture()
        self.assertEqual(s.check_qa(receipt, qa_path)["bundle_id"], s.BUNDLE)
        for field in ("source_sha256", "artifact_sha256", "build_receipt_sha256"):
            s.write_private(qa_path, dict(qa, **{field: "wrong"}))
            with self.assertRaises(s.GuardError):
                s.check_qa(receipt, qa_path)
        s.write_private(qa_path, qa)
        (self.root / "apps/android/source.kt").write_text("untested")
        with self.assertRaises(s.GuardError):
            s.check_qa(receipt, qa_path)

    def test_pending_or_missing_evidence_cannot_qualify(self):
        receipt, qa_path, build, qa = self.fixture()
        qa["checks"]["native_smoke"]["status"] = "pending"
        s.write_private(qa_path, qa)
        with self.assertRaises(s.GuardError):
            s.check_qa(receipt, qa_path)
        qa["checks"]["native_smoke"]["status"] = "passed"
        qa["checks"]["native_smoke"]["sha256"] = "wrong"
        s.write_private(qa_path, qa)
        with self.assertRaises(s.GuardError):
            s.check_qa(receipt, qa_path)

    def test_apple_inventory_checks_exact_bundle(self):
        api = s.Apple({})
        with patch.object(api, "rows", side_effect=[[{"attributes": {"bundleId": "another.app"}}], []]):
            with self.assertRaises(s.GuardError):
                api.inventory()

    def test_no_unguarded_provider_mutation(self):
        with self.assertRaises(s.GuardError):
            s.Apple({}).request("POST", "/v1/bundleIds", {})
        with self.assertRaises(s.GuardError):
            s.Apple({}).request("DELETE", "/v1/apps/someone-else")
        for path in ("/v1/appStoreVersions", "/v1/appPriceSchedules", "/v1/users", "/v1/reviewSubmissions"):
            with self.assertRaises(s.GuardError):
                s.Apple({}).request("POST", path, {}, operation="not-authorized")

    def test_upload_snapshots_exact_bytes_and_rejects_changes(self):
        receipt, qa_path, build, qa = self.fixture()
        frozen = s.snapshot_artifact(build)
        self.assertNotEqual(frozen["artifact"], build["artifact"])
        self.assertEqual(s.digest(frozen["artifact"]), build["artifact_sha256"])
        Path(frozen["artifact"]).write_bytes(b"changed")
        with self.assertRaises(s.GuardError):
            s.snapshot_artifact(build)

    def test_android_package_permissions_and_debug_guard(self):
        xml = '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="art.lazying.musia" android:versionCode="1" android:versionName="0.1.0"><application /></manifest>'
        self.assertEqual(android_manifest(xml), set())
        for invalid in (xml.replace("art.lazying.musia", "art.lazying.bunko"),
                        xml.replace("<application />", '<application android:debuggable="true"/>'),
                        xml.replace("<application />", '<uses-permission android:name="android.permission.RECORD_AUDIO"/><application/>')):
            with self.assertRaises(s.GuardError):
                android_manifest(invalid)

    def test_android_build_rejects_jre_before_launching_gradle(self):
        with self.assertRaisesRegex(s.GuardError, "complete shared JDK"):
            android_config({"java_home": str(self.root / "missing-jdk")})

    def test_upload_and_invite_need_qa_before_provider_access(self):
        args = argparse.Namespace(build_receipt=None, qa=None, confirm_upload=True, confirm_invite=True)
        with patch.object(cli, "Apple", side_effect=AssertionError("provider touched")):
            with self.assertRaises(s.GuardError):
                cli.upload_apple(args)
            with self.assertRaises(s.GuardError):
                cli.invite_apple(args)

    def test_profile_rejects_another_app(self):
        with self.assertRaises(s.GuardError):
            check_profile({"TeamIdentifier": [s.TEAM], "Entitlements": {
                "application-identifier": s.TEAM + ".art.lazying.bunko"}}, {})

    def test_play_invitation_draft_is_not_queued_or_sent(self):
        _, _, build, _ = self.fixture()
        s.write_private(self.runtime / "operations" / ("play-upload-" + build["artifact_sha256"] + ".json"),
                        {"sha256": build["artifact_sha256"], "state": "upload_dispatched_readback_required"})
        with patch.object(invite_play, "RUNTIME", self.runtime), \
             patch.object(invite_play, "config", return_value={"self_tester_email": "owner@example.invalid"}), \
             patch.object(invite_play, "test_access", return_value="https://play.google.com/apps/internaltest/123"), \
             patch.object(invite_play, "run", side_effect=AssertionError("transport must not run")):
            result = invite_play.invite(build)
            self.assertEqual(result["state"], "private_invitation_prepared_not_sent")
            self.assertEqual(Path(result["path"]).stat().st_mode & 0o777, 0o600)
            with self.assertRaises(s.GuardError):
                invite_play.invite(build, confirm=True)
            self.assertFalse((self.runtime / "mail" / (build["artifact_sha256"] + ".json")).exists())

    def test_mail_acceptance_does_not_claim_delivery_or_allow_resend(self):
        _, _, build, _ = self.fixture()
        s.write_private(self.runtime / "operations" / ("play-upload-" + build["artifact_sha256"] + ".json"),
                        {"sha256": build["artifact_sha256"], "state": "upload_dispatched_readback_required"})
        transport = self.runtime / "mock-mail-transport"
        s.write_private(transport, b"mock; never executed")
        transport.chmod(0o700)
        cfg = {"self_tester_email": "owner@example.invalid", "sendmail_path": str(transport)}
        with patch.object(invite_play, "RUNTIME", self.runtime), \
             patch.object(invite_play, "config", return_value=cfg), \
             patch.object(invite_play, "test_access", return_value="https://play.google.com/apps/internaltest/123"), \
             patch.object(invite_play, "run", return_value=b"") as send:
            result = invite_play.invite(build, confirm=True)
            self.assertEqual(result["state"], "accepted_by_transport_delivery_unverified")
            send.assert_called_once()
            with self.assertRaises(s.GuardError):
                invite_play.invite(build, confirm=True)
            send.assert_called_once()


if __name__ == "__main__":
    unittest.main()
