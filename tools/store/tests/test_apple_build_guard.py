import importlib.util
import io
import json
import contextlib
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import Mock, patch

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

    def test_replaced_directory_is_never_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "guard"
            guard = module.BuildGuard(path, "unit test", "disposable fixture")
            path.rename(Path(folder) / "original")
            path.mkdir()
            (path / "owner.json").write_text(json.dumps(guard.owner))
            with self.assertRaises(RuntimeError):
                guard.release()
            self.assertTrue(path.exists())

    def test_inventory_requires_successful_absence_for_each_process(self):
        with patch.object(module.subprocess, "run", return_value=Mock(returncode=1)) as run:
            self.assertFalse(module.peer_job_active())
            self.assertEqual([call.args[0][-1] for call in run.call_args_list],
                             ["xcodebuild", "swift-frontend", "xctest"])
        with patch.object(module.subprocess, "run", return_value=Mock(returncode=2)):
            with self.assertRaises(RuntimeError):
                module.peer_job_active()

    def run_guard(self, path, status=0, active=False, inventory_error=None,
                  launch_error=None, descendants=False, interrupted=False):
        # Only the disposable directory is real; no build or shared lock is used.
        child = Mock(pid=12345)

        def wait():
            if interrupted:
                signal.getsignal(signal.SIGHUP)(signal.SIGHUP, None)
            return status

        child.wait.side_effect = wait
        handlers = {sig: signal.getsignal(sig) for sig in
                    [signal.SIGHUP, signal.SIGINT, signal.SIGTERM]}
        with patch.object(module, "peer_job_active", return_value=active,
                          side_effect=inventory_error), \
             patch.object(module.subprocess, "check_output", return_value="fixture start"), \
             patch.object(module.subprocess, "Popen", return_value=child,
                          side_effect=launch_error) as launch, \
             patch.object(module, "group_alive", return_value=descendants), \
             contextlib.redirect_stdout(io.StringIO()):
            result = module.main(["--slot-note", "disposable fixture",
                                  "--operation", "unit test", "--", "not-a-build"],
                                 guard_path=path)
        for sig, handler in handlers.items():
            self.assertEqual(signal.getsignal(sig), handler)
        return result, launch, child

    def test_occupied_guard_never_launches_or_changes_owner(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "guard"
            guard = module.BuildGuard(path, "unit test", "disposable fixture")
            original = (path / "owner.json").read_bytes()
            result, launch, _ = self.run_guard(path)
            self.assertEqual(result, 75)
            launch.assert_not_called()
            self.assertEqual((path / "owner.json").read_bytes(), original)
            guard.release()

    def test_peer_conflict_releases_only_unused_owned_guard(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "guard"
            result, launch, _ = self.run_guard(path, active=True)
            self.assertEqual(result, 75)
            launch.assert_not_called()
            self.assertFalse(path.exists())

    def test_inventory_errors_never_launch(self):
        for error in [OSError("missing pgrep"), RuntimeError("inventory error")]:
            with self.subTest(error=type(error).__name__), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "guard"
                result, launch, _ = self.run_guard(path, inventory_error=error)
                self.assertEqual(result, 75)
                launch.assert_not_called()
                self.assertFalse(path.exists())

    def test_launch_failure_releases_unused_owned_guard(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "guard"
            result, _, child = self.run_guard(path, launch_error=FileNotFoundError())
            self.assertEqual(result, 75)
            child.wait.assert_not_called()
            self.assertFalse(path.exists())

    def test_completed_jobs_release_after_wait(self):
        for status in [0, 65]:
            with self.subTest(status=status), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "guard"
                result, launch, child = self.run_guard(path, status=status)
                self.assertEqual(result, status)
                child.wait.assert_called_once()
                self.assertTrue(launch.call_args.kwargs["start_new_session"])
                self.assertTrue(launch.call_args.kwargs["env"]["MUSIA_APPLE_GUARD_TOKEN"])
                self.assertFalse(path.exists())

    def test_uncertain_cleanup_retains_guard(self):
        for options in [{"descendants": True}, {"interrupted": True}, {"status": 76},
                        {"status": -signal.SIGTERM}]:
            with self.subTest(options=options), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "guard"
                result, _, child = self.run_guard(path, **options)
                self.assertNotEqual(result, 0)
                child.wait.assert_called_once()
                self.assertTrue(path.exists())
                self.assertEqual(json.loads((path / "owner.json").read_text())["app"], "Musia")
