import ast
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parents[1]


class AppleBuildPolicyTests(unittest.TestCase):
    def install(self, home, profile):
        source = (TOOLS / "build_macos.sh").read_text()
        start = source.index('for directory in "$HOME/Library/MobileDevice/Provisioning Profiles"')
        end = source.index("\ndone", start) + len("\ndone")
        return subprocess.run(
            ["bash", "-eu", "-c", source[start:end]],
            env=dict(os.environ, HOME=str(home), profile=str(profile), uuid="test-profile"),
            capture_output=True,
        )

    def test_existing_identical_profile_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            profile = home / "source.provisionprofile"
            profile.write_bytes(b"fixture profile")
            self.assertEqual(self.install(home, profile).returncode, 0)
            targets = list(home.glob("Library/**/test-profile.provisionprofile"))
            self.assertEqual(len(targets), 2)
            before = [(p.stat().st_ino, p.stat().st_mtime_ns) for p in targets]
            self.assertEqual(self.install(home, profile).returncode, 0)
            self.assertEqual(before, [(p.stat().st_ino, p.stat().st_mtime_ns) for p in targets])

    def test_different_profile_is_preserved_and_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            profile = home / "source.provisionprofile"
            profile.write_bytes(b"expected")
            target = home / "Library/MobileDevice/Provisioning Profiles/test-profile.provisionprofile"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"other owner")
            self.assertNotEqual(self.install(home, profile).returncode, 0)
            self.assertEqual(target.read_bytes(), b"other owner")

    def test_symlink_is_preserved_and_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            profile = home / "source.provisionprofile"
            profile.write_bytes(b"expected")
            target = home / "Library/MobileDevice/Provisioning Profiles/test-profile.provisionprofile"
            target.parent.mkdir(parents=True)
            target.symlink_to(profile)
            self.assertNotEqual(self.install(home, profile).returncode, 0)
            self.assertTrue(target.is_symlink())
            self.assertEqual(profile.read_bytes(), b"expected")

    def test_ios_archive_uses_one_worker(self):
        tree = ast.parse((TOOLS / "build_native.py").read_text())
        archive = next(n for n in ast.walk(tree) if isinstance(n, ast.List)
                       and any(isinstance(x, ast.Constant) and x.value == "/usr/bin/xcodebuild" for x in n.elts)
                       and any(isinstance(x, ast.Constant) and x.value == "-archivePath" for x in n.elts))
        index = next(i for i, x in enumerate(archive.elts)
                     if isinstance(x, ast.Constant) and x.value == "-jobs")
        self.assertEqual(archive.elts[index + 1].value, "1")


if __name__ == "__main__":
    unittest.main()
