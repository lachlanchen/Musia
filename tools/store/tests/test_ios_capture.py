import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import capture_ios_review as capture
from storelib import GuardError


class NativeCaptureTests(unittest.TestCase):
    def rejected_capture(self, name="Musia-Store-iPhone", state="Shutdown", attempt="1", existing=False, outside=False):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            output = runtime / "review" if not outside else Path(directory) / "public"
            output.mkdir(parents=True)
            if existing:
                (output / "iphone-1-capture.json").write_text("{}")
            devices = {"devices": {"runtime": [{"udid": "owned-id", "name": name, "state": state}]}}
            argv = ["capture", "--device", "owned-id", "--name", "iphone", "--output", str(output), "--attempt", attempt]
            with patch.object(capture, "RUNTIME", runtime), patch.object(sys, "argv", argv), \
                    patch.object(capture.platform, "system", return_value="Darwin"), \
                    patch.object(capture.subprocess, "check_output", return_value=json.dumps(devices)), \
                    patch.object(capture, "run") as run:
                with self.assertRaises(GuardError):
                    capture.main()
                run.assert_not_called()

    def test_refuses_peer_simulator(self):
        self.rejected_capture(name="Other-Project-iPhone")

    def test_refuses_in_use_simulator(self):
        self.rejected_capture(state="Booted")

    def test_refuses_prior_evidence(self):
        self.rejected_capture(existing=True)

    def test_refuses_attempt_path_traversal(self):
        self.rejected_capture(attempt="../other")

    def test_refuses_public_output(self):
        self.rejected_capture(outside=True)

    def test_command_failure_is_not_success(self):
        with tempfile.TemporaryDirectory() as directory:
            process = Mock()
            process.wait.return_value = 65
            with patch.object(capture.subprocess, "Popen", return_value=process):
                with self.assertRaises(GuardError):
                    capture.run(["xcodebuild"], Path(directory) / "test.log", 30)

    def test_timeout_stops_only_owned_process_group(self):
        with tempfile.TemporaryDirectory() as directory:
            process = Mock(pid=123)
            process.wait.side_effect = [subprocess.TimeoutExpired("xcodebuild", 30), 0]
            with patch.object(capture.subprocess, "Popen", return_value=process) as popen, \
                    patch.object(capture.os, "killpg") as kill:
                with self.assertRaises(subprocess.TimeoutExpired):
                    capture.run(["xcodebuild"], Path(directory) / "test.log", 30)
                self.assertTrue(popen.call_args.kwargs["start_new_session"])
                kill.assert_called_once_with(123, signal.SIGTERM)


if __name__ == "__main__":
    unittest.main()
