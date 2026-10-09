import tempfile
import unittest
from pathlib import Path
import plistlib
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_native import BUNDLE, WATCH_BUNDLE, check_watch_info, embedded_watch
from storelib import GuardError


class WatchBundleTests(unittest.TestCase):
    def info(self):
        return {"CFBundleIdentifier": WATCH_BUNDLE, "CFBundleShortVersionString": "0.2.0",
                "CFBundleVersion": "9", "WKApplication": True, "WKCompanionAppBundleIdentifier": BUNDLE,
                "WKRunsIndependentlyOfCompanionApp": False, "UIDeviceFamily": [4],
                "CFBundleSupportedPlatforms": ["WatchOS"], "MinimumOSVersion": "10.0", "CFBundleExecutable": "MusiaWatch"}

    def test_exact_companion(self):
        check_watch_info(self.info(), {"version": "0.2.0", "ios_build": "9"})

    def test_wrong_identity_permissions_or_platform_rejected(self):
        for change in ({"CFBundleIdentifier": "other"}, {"WKCompanionAppBundleIdentifier": "other"},
                       {"CFBundleVersion": "8"}, {"WKRunsIndependentlyOfCompanionApp": True},
                       {"NSMicrophoneUsageDescription": "Record"}, {"WKBackgroundModes": ["workout-processing"]},
                       {"UIDeviceFamily": [1]}, {"CFBundleSupportedPlatforms": ["WatchSimulator"]}):
            with self.subTest(change=change), self.assertRaises(GuardError):
                check_watch_info(self.info() | change, {"version": "0.2.0", "ios_build": "9"})

    def test_exact_one_embedded_watch_and_no_other_extensions(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / "Musia.app"
            watch = app / "Watch/MusiaWatch.app"
            watch.mkdir(parents=True)
            (watch / "Info.plist").write_bytes(plistlib.dumps(self.info()))
            (watch / "MusiaWatch").write_bytes(b"test executable")
            release = {"version": "0.2.0", "ios_build": "9"}
            self.assertEqual(embedded_watch(app, release), watch)
            (app / "PlugIns/Unknown.appex").mkdir(parents=True)
            with self.assertRaises(GuardError):
                embedded_watch(app, release)

    def test_older_build_does_not_allow_watch(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory)
            self.assertIsNone(embedded_watch(app, {"ios_build": "8"}))
            (app / "Watch/Unexpected.app").mkdir(parents=True)
            with self.assertRaises(GuardError):
                embedded_watch(app, {"ios_build": "8"})
