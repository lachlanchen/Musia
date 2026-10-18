from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import verify_mac_qa_bundles as qa


class MacQABundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = Path(self.temp.name) / "Musia.app"
        for name in qa.BUNDLES:
            self.write_info(name)

    def write_info(self, name, **changes):
        relative, identifier, package_type = qa.BUNDLES[name]
        path = self.app / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        info = {"CFBundleIdentifier": identifier, "CFBundlePackageType": package_type}
        path.write_bytes(plistlib.dumps(info | changes))

    def test_exact_distinct_qa_bundle_ids(self):
        ids = qa.check_bundle_ids(self.app)
        self.assertEqual(ids, {name: spec[1] for name, spec in qa.BUNDLES.items()})
        self.assertEqual(len(set(ids.values())), 3)

    def test_former_global_override_is_rejected(self):
        for name in ("core", "tests"):
            with self.subTest(name=name):
                self.write_info(name, CFBundleIdentifier=qa.QA_PREFIX)
                with self.assertRaisesRegex(ValueError, name):
                    qa.check_bundle_ids(self.app)
                self.write_info(name)

    def test_production_and_unexpanded_ids_are_rejected(self):
        for name, (_, expected, _) in qa.BUNDLES.items():
            for identifier in (expected.replace(".compatibilityqa", ""),
                               "$(MUSIA_MAC_BUNDLE_PREFIX)", "other.app"):
                with self.subTest(name=name, identifier=identifier):
                    self.write_info(name, CFBundleIdentifier=identifier)
                    with self.assertRaises(ValueError):
                        qa.check_bundle_ids(self.app)
                    self.write_info(name)

    def test_missing_or_invalid_plist_refuses_launch(self):
        for name, (relative, _, _) in qa.BUNDLES.items():
            path = self.app / relative
            with self.subTest(name=name):
                path.unlink()
                with self.assertRaises(FileNotFoundError):
                    qa.check_bundle_ids(self.app)
                path.write_bytes(b"not a plist")
                with self.assertRaises(plistlib.InvalidFileException):
                    qa.check_bundle_ids(self.app)
                path.write_bytes(plistlib.dumps([]))
                with self.assertRaises(ValueError):
                    qa.check_bundle_ids(self.app)
                self.write_info(name)

    def test_wrong_package_type_rejected(self):
        for name in qa.BUNDLES:
            with self.subTest(name=name):
                self.write_info(name, CFBundlePackageType="APPL" if name != "app" else "BNDL")
                with self.assertRaises(ValueError):
                    qa.check_bundle_ids(self.app)
                self.write_info(name)

    def test_versioned_framework_symlink_inside_app_allowed(self):
        resources = self.app / "Contents/Frameworks/MusiaCore.framework/Resources"
        version = resources.parent / "Versions/A"
        version.mkdir(parents=True)
        resources.rename(version / "Resources")
        resources.symlink_to("Versions/A/Resources", target_is_directory=True)
        qa.check_bundle_ids(self.app)

    def test_plist_symlink_outside_app_rejected(self):
        path = self.app / qa.BUNDLES["tests"][0]
        external = Path(self.temp.name) / "external.plist"
        path.rename(external)
        path.symlink_to(external)
        with self.assertRaisesRegex(ValueError, "outside"):
            qa.check_bundle_ids(self.app)

    def test_private_sandbox_required(self):
        qa.check_entitlements({"com.apple.security.app-sandbox": True})
        for entitlements in ({}, [], {"com.apple.security.app-sandbox": 1},
                             {"com.apple.security.app-sandbox": "true"}):
            with self.subTest(entitlements=entitlements), self.assertRaises(ValueError):
                qa.check_entitlements(entitlements)

    def test_shared_groups_forbidden(self):
        for key in ("keychain-access-groups", "com.apple.security.application-groups"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                qa.check_entitlements({"com.apple.security.app-sandbox": True, key: ["shared"]})

    def test_identity_failure_does_not_call_codesign(self):
        self.write_info("tests", CFBundleIdentifier=qa.QA_PREFIX)
        with patch.object(qa.subprocess, "check_output") as codesign:
            with self.assertRaises(ValueError):
                qa.verify(self.app)
            codesign.assert_not_called()

    def test_codesign_verification_is_bounded_and_read_only(self):
        raw = plistlib.dumps({"com.apple.security.app-sandbox": True})
        with patch.object(qa.subprocess, "check_output", return_value=raw) as codesign:
            result = qa.verify(self.app)
            self.assertTrue(result["sandbox"])
            self.assertFalse(result["shared_groups"])
            codesign.assert_called_once_with(
                ["codesign", "-d", "--entitlements", ":-", str(self.app)],
                stderr=subprocess.DEVNULL, timeout=20)

    def test_cli_failure_is_nonzero_without_launch(self):
        for error in (ValueError("bad identity"), FileNotFoundError("missing"),
                      subprocess.TimeoutExpired("codesign", 20),
                      subprocess.CalledProcessError(1, "codesign")):
            with self.subTest(error=error), \
                    patch.object(sys, "argv", ["verify", str(self.app)]), \
                    patch.object(qa, "verify", side_effect=error), \
                    patch.object(qa.sys, "stderr"):
                self.assertEqual(qa.main(), 65)

    def test_runner_has_no_global_product_id_override(self):
        runner = (Path(__file__).parents[1] / "test_compatibility_apple.sh").read_text()
        self.assertNotIn("PRODUCT_BUNDLE_IDENTIFIER=", runner)
        self.assertIn("MUSIA_MAC_BUNDLE_PREFIX=" + qa.QA_PREFIX, runner)
        self.assertLess(runner.index("verify_mac_qa_bundles.py"),
                        runner.index("xcodebuild test-without-building"))
