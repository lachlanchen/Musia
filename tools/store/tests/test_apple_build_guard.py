import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("apple_build_guard", Path(__file__).parents[1] / "apple_build_guard.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AppleBuildGuardTests(unittest.TestCase):
    def test_exclusive_acquisition_and_exact_release(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "guard"
            guard = module.BuildGuard(path, "unit test", "disposable fixture")
            self.assertEqual(json.loads((path / "owner.json").read_text())["protocol"], 1)
            with self.assertRaises(FileExistsError):
                module.BuildGuard(path, "another", "disposable fixture")
            guard.release()
            self.assertFalse(path.exists())

    def test_changed_owner_is_never_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "guard"
            guard = module.BuildGuard(path, "unit test", "disposable fixture")
            (path / "owner.json").write_text('{}')
            with self.assertRaises(RuntimeError):
                guard.release()
            self.assertTrue(path.exists())

    def test_extra_content_is_never_deleted(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "guard"
            guard = module.BuildGuard(path, "unit test", "disposable fixture")
            (path / "foreign").touch()
            with self.assertRaises(RuntimeError):
                guard.release()
            self.assertTrue((path / "foreign").exists())

    def test_symlink_cannot_be_acquired(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "real").mkdir()
            (root / "guard").symlink_to(root / "real", target_is_directory=True)
            with self.assertRaises(FileExistsError):
                module.BuildGuard(root / "guard", "unit test", "disposable fixture")
            self.assertEqual(list((root / "real").iterdir()), [])
