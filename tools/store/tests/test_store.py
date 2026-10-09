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
import play_console
from build_native import check_profile, android_manifest, android_config
from play_console import OwnedTab


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
        runtime = self.root / "apps/android/.runtime"
        runtime.mkdir()
        (runtime / "qa.log").write_text("device evidence is not source")
        self.assertEqual(before, s.source_sha("android"))
        (self.root / "apps/android/source.kt").write_text("changed")
        self.assertNotEqual(before, s.source_sha("android"))

    def test_source_rejects_symlinks(self):
        (self.root / "apps/android/secret").symlink_to(self.root / "store/release.json")
        with self.assertRaises(s.GuardError):
            s.source_sha("android")

    def test_apple_inventory_selects_exact_bundle_from_prefix_results(self):
        api = s.Apple(cfg={})
        app = {"id": "musia", "attributes": {"bundleId": s.BUNDLE}}
        bundle = {"id": "musia-bundle", "attributes": {"identifier": s.BUNDLE}}
        for suffix in (".creatorqa", ".core", "x"):
            sibling_app = {"id": "sibling", "attributes": {"bundleId": s.BUNDLE + suffix}}
            sibling_bundle = {"id": "sibling-bundle", "attributes": {"identifier": s.BUNDLE + suffix}}
            with self.subTest(suffix=suffix), patch.object(api, "rows", side_effect=[
                    [sibling_app, app], [bundle, sibling_bundle]]):
                inventory = api.inventory()
                self.assertEqual(inventory["apps"], [app])
                self.assertEqual(inventory["bundle_ids"], [bundle])

    def test_apple_inventory_rejects_duplicate_exact_matches(self):
        api = s.Apple(cfg={})
        app = {"id": "musia", "attributes": {"bundleId": s.BUNDLE}}
        bundle = {"id": "musia-bundle", "attributes": {"identifier": s.BUNDLE}}
        sibling = {"id": "qa", "attributes": {"identifier": s.BUNDLE + ".creatorqa"}}
        for apps, bundles in (([app, dict(app, id="duplicate")], [bundle]),
                              ([app], [sibling, bundle, dict(bundle, id="duplicate")])):
            with self.subTest(apps=apps, bundles=bundles), patch.object(
                    api, "rows", side_effect=[apps, bundles]):
                with self.assertRaisesRegex(s.GuardError, "Ambiguous Musia inventory"):
                    api.inventory()

    def test_apple_app_requires_an_exact_app_not_a_prefix_sibling(self):
        api = s.Apple(cfg={})
        bundle = {"id": "bundle", "attributes": {"identifier": s.BUNDLE}}
        for apps in ([], [{"id": "qa", "attributes": {"bundleId": s.BUNDLE + ".creatorqa"}}]):
            with self.subTest(apps=apps), patch.object(api, "rows", side_effect=[apps, [bundle]]):
                with self.assertRaisesRegex(s.GuardError, "Musia App Store Connect record missing"):
                    api.app()

    def test_apple_inventory_does_not_substitute_a_prefix_bundle(self):
        api = s.Apple(cfg={})
        sibling = {"id": "qa", "attributes": {"identifier": s.BUNDLE + ".creatorqa"}}
        with patch.object(api, "rows", side_effect=[[], [sibling]]):
            self.assertEqual(api.inventory()["bundle_ids"], [])

    def test_apple_exact_bundle_still_requires_configured_app_id(self):
        self.release["apple_app_id"] = "expected-app"
        (self.root / "store/release.json").write_text(json.dumps(self.release))
        api = s.Apple(cfg={})
        app = {"id": "wrong-app", "attributes": {"bundleId": s.BUNDLE}}
        bundle = {"id": "bundle", "attributes": {"identifier": s.BUNDLE}}
        with patch.object(api, "rows", side_effect=[[app], [bundle]]):
            with self.assertRaisesRegex(s.GuardError, "Configured Apple app ID mismatch"):
                api.app()
        app["id"] = "expected-app"
        with patch.object(api, "rows", side_effect=[[app], [bundle]]):
            self.assertEqual(api.app(), app)

    def test_apple_owner_tester_is_scoped_to_app(self):
        from unittest.mock import Mock
        api = Mock()
        owner = {"id": "musia-owner", "attributes": {"email": "owner@example.test"}}
        api.rows.side_effect = [[owner, {"id": "other", "attributes": {"email": "other@example.test"}}],
                                [{"id": "musia", "attributes": {"bundleId": s.BUNDLE}}]]
        self.assertEqual(cli.apple_owner_tester(api, "musia", "OWNER@example.test"), owner)
        self.assertIn("filter%5Bapps%5D=musia", api.rows.call_args_list[0].args[0])
        api.rows.assert_called_with("/v1/betaTesters/musia-owner/apps?limit=200")
        api.rows.side_effect = None
        for rows in ([], [owner, owner]):
            api.rows.return_value = rows
            with self.assertRaises(s.GuardError):
                cli.apple_owner_tester(api, "musia", "owner@example.test")
        api.rows.side_effect = [[owner], [{"id": "other-app", "attributes": {"bundleId": s.BUNDLE}}]]
        with self.assertRaises(s.GuardError):
            cli.apple_owner_tester(api, "musia", "owner@example.test")

    def test_apple_same_build_number_is_scoped_to_platform(self):
        from unittest.mock import Mock
        api = Mock()
        ios = {"id": "ios-4", "attributes": {"version": "4"}}
        mac = {"id": "mac-4", "attributes": {"version": "4"}}
        api.rows.return_value = [mac, ios]
        api.request.side_effect = lambda method, path: {"data": {"attributes": {
            "version": "0.1.2", "platform": "MAC_OS" if "/mac-4/" in path else "IOS"}}}
        self.assertEqual(s.apple_platform_builds(api, "musia", "4", "IOS"), [ios])
        self.assertEqual(s.apple_platform_builds(api, "musia", "4", "MAC_OS"), [mac])
        self.assertIn("filter%5Bapp%5D=musia", api.rows.call_args.args[0])
        api.request.assert_called_with("GET", "/v1/builds/ios-4/preReleaseVersion")

    def test_apple_build_lookup_fails_closed_on_unknown_identity(self):
        from unittest.mock import Mock
        api = Mock()
        api.rows.return_value = [{"id": "unverified", "attributes": {"version": "4"}}]
        api.request.return_value = {"data": {"attributes": {"version": "0.1.2"}}}
        with self.assertRaises(s.GuardError):
            s.apple_platform_builds(api, "musia", "4", "IOS")
        api.rows.return_value[0]["attributes"]["version"] = "5"
        with self.assertRaises(s.GuardError):
            s.apple_platform_builds(api, "musia", "4", "IOS")

    def test_other_app_identity_and_formal_submit_are_rejected(self):
        for field, value in (("bundle_id", "art.lazying.bunko"), ("formal_submission_enabled", True),
                             ("google_developer_id", "123")):
            data = dict(self.release, **{field: value})
            (self.root / "store/release.json").write_text(json.dumps(data))
            with self.assertRaises(s.GuardError):
                s.release()

    def test_play_update_form_proves_package_on_parent_track(self):
        from unittest.mock import Mock
        base = f"https://play.google.com/console/u/0/developers/{s.DEVELOPER}/app/123/tracks/456"
        cfg = {"google_app_id":"123", "play_internal_url":base+"?tab=releases", "play_upload_url":base+"/releases/2/prepare"}
        tab = Mock()
        tab.view.side_effect = [{"url":cfg["play_internal_url"],"text":s.BUNDLE+" Internal testing"},
                                {"url":cfg["play_upload_url"],"text":"Create internal testing release"}]
        play_console.open_verified_prepare(tab,cfg)
        self.assertEqual([c.kwargs["url"] for c in tab.call.call_args_list], [cfg["play_internal_url"],cfg["play_upload_url"]])
        for bad in (base+"/releases/2/prepare?other=1", base.replace("456","999")+"/releases/2/prepare", base.replace("/123/","/999/")+"/releases/2/prepare"):
            with self.assertRaises(s.GuardError):
                play_console.open_verified_prepare(Mock(),dict(cfg,play_upload_url=bad))

    def test_play_update_form_rejects_wrong_package_before_prepare(self):
        from unittest.mock import Mock
        base = f"https://play.google.com/console/u/0/developers/{s.DEVELOPER}/app/123/tracks/456"
        cfg = {"google_app_id":"123", "play_internal_url":base+"?tab=releases", "play_upload_url":base+"/releases/2/prepare"}
        tab = Mock()
        tab.view.return_value = {"url":cfg["play_internal_url"],"text":"another.app Internal testing"}
        with patch.object(play_console.time,"sleep"), self.assertRaises(s.GuardError):
            play_console.open_verified_prepare(tab,cfg)
        self.assertEqual(tab.call.call_count, 1)

    def test_play_track_accepts_current_listing_title_only_at_exact_url(self):
        track = f"https://play.google.com/console/u/0/developers/{s.DEVELOPER}/app/123/tracks/456?tab=releases"
        view = {"url": track, "text": "Musia: Learn Music & Guitar\nInternal testing\n7 (0.2.0)"}
        self.assertTrue(play_console.internal_view(view, track))
        for url in (track.replace("/123/", "/999/"), track.replace("/456?", "/789?"), track+"&extra=1"):
            self.assertFalse(play_console.internal_view(dict(view, url=url), track))
        for text in ("Other App\nInternal testing", "Musia: Learn Music & Guitar\nProduction", "Prefix Musia: Learn Music & Guitar\nInternal testing"):
            self.assertFalse(play_console.internal_view(dict(view, text=text), track))

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

    def test_internal_beta_does_not_satisfy_full_qualification(self):
        receipt, qa_path, build, qa = self.fixture()
        evidence = qa["checks"]["unit_tests"]
        qa.update(scope="internal-owner-test", production_qualified=False,
                  known_limitations=["Physical-device playback still needs testing"],
                  checks={key: dict(evidence) for key in s.INTERNAL_BETA_CHECKS})
        s.write_private(qa_path, qa)
        self.assertEqual(s.check_qa(receipt, qa_path, internal_beta=True)["bundle_id"], s.BUNDLE)
        with self.assertRaises(s.GuardError):
            s.check_qa(receipt, qa_path)
        for override in ({"scope": "production"}, {"production_qualified": True}, {"known_limitations": []}):
            s.write_private(qa_path, dict(qa, **override))
            with self.assertRaises(s.GuardError):
                s.check_qa(receipt, qa_path, internal_beta=True)

    def test_internal_beta_still_requires_passed_hashed_evidence(self):
        receipt, qa_path, build, qa = self.fixture()
        evidence = qa["checks"]["unit_tests"]
        qa.update(scope="internal-owner-test", production_qualified=False,
                  known_limitations=["Device testing pending"],
                  checks={key: dict(evidence) for key in s.INTERNAL_BETA_CHECKS})
        qa["checks"]["native_ui"]["status"] = "pending"
        s.write_private(qa_path, qa)
        with self.assertRaises(s.GuardError):
            s.check_qa(receipt, qa_path, internal_beta=True)
        qa["checks"]["native_ui"].update(status="passed", sha256="wrong")
        s.write_private(qa_path, qa)
        with self.assertRaises(s.GuardError):
            s.check_qa(receipt, qa_path, internal_beta=True)

    def test_apple_inventory_checks_exact_bundle(self):
        api = s.Apple({})
        with patch.object(api, "rows", side_effect=[[{"attributes": {"bundleId": "another.app"}}], []]):
            with self.assertRaises(s.GuardError):
                api.inventory()
        app = {"id": "musia", "attributes": {"bundleId": s.BUNDLE}}
        bundle = {"id": "musia-bundle", "attributes": {"identifier": s.BUNDLE}}
        foreign = {"id": "foreign", "attributes": {"identifier": "another.app"}}
        with patch.object(api, "rows", side_effect=[[app], [bundle, foreign]]):
            with self.assertRaisesRegex(s.GuardError, "Apple bundle filter mismatch"):
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

    def test_store_view_allows_body_not_yet_attached(self):
        tab = object.__new__(OwnedTab)
        with patch.object(tab, "evaluate", return_value={"url": "about:blank", "text": ""}) as evaluate:
            self.assertEqual(tab.view()["text"], "")
            self.assertIn("document.body?.innerText", evaluate.call_args.args[0])

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

    def test_play_access_checks_saved_list_and_actual_members(self):
        from unittest.mock import Mock
        base = f"https://play.google.com/console/u/0/developers/{s.DEVELOPER}/app/123/tracks/456"
        cfg = {"google_app_id": "123", "play_internal_url": base + "?tab=releases",
               "play_testers_url": base + "?tab=testers",
               "play_opt_in_url": "https://play.google.com/apps/internaltest/456",
               "self_tester_email": "owner@example.invalid"}
        for selected, members, succeeds in (
                (["Musia Internal Owner"], "owner@example.invalid", True),
                (["Other app testers"], "owner@example.invalid", False),
                (["Musia Internal Owner"], "owner@example.invalid stranger@example.invalid", False)):
            tab = Mock()
            current = {}
            tab.call.side_effect = lambda method, **kwargs: current.update(url=kwargs["url"])
            tab.view.side_effect = lambda: {"url": current["url"], "text":
                s.BUNDLE + " Internal testing Available to internal testers 1 (0.1.0)"}
            def evaluate(expression):
                if "selected, links" in expression:
                    return {"selected": selected, "links": [cfg["play_opt_in_url"]]}
                if "const b =" in expression:
                    return True
                return members
            tab.evaluate.side_effect = evaluate
            with patch.object(play_console, "config", return_value=cfg), \
                 patch.object(play_console, "OwnedTab", return_value=tab), \
                 patch.object(play_console, "RUNTIME", self.runtime), \
                 patch.object(play_console.time, "sleep"):
                build = {"build_number": "1", "version": "0.1.0", "artifact_sha256": "fixture"}
                if succeeds:
                    self.assertEqual(play_console.test_access(build), cfg["play_opt_in_url"])
                else:
                    with self.assertRaises(s.GuardError):
                        play_console.test_access(build)
            tab.close.assert_called_once()

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
