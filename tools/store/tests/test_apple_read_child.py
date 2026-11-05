import os
from pathlib import Path
import signal
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apple_read_child import ReadCommands, clock, global_environment


class ReadTests(unittest.TestCase):
    def runner(self):
        return ReadCommands(clock() + 20, reserve=12, maximum=65536)

    def clean(self, runner):
        self.assertTrue(runner.records)
        for row in runner.records:
            self.assertTrue(row["children_absent"], row)
            self.assertTrue(row["complete"], row)

    def test_normal(self):
        runner = self.runner()
        self.assertEqual(runner.run([sys.executable, "-c", "print('ok')"])["stdout"], "ok\n")
        self.clean(runner)

    def test_hung_child_and_descendant(self):
        runner = self.runner()
        program = "import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);time.sleep(60)"
        with self.assertRaises(TimeoutError):
            runner.run([sys.executable, "-c", program], limit=.6)
        self.assertGreaterEqual(len(runner.records[0]["identities"]), 2)
        self.clean(runner)

    def test_output_flood(self):
        runner = self.runner()
        with self.assertRaisesRegex(RuntimeError, "output limit"):
            runner.run([sys.executable, "-c", "import os;os.write(1,b'x'*1000000)"])
        self.clean(runner)

    def test_interruption(self):
        runner = self.runner()
        old = signal.getsignal(signal.SIGTERM)
        def stop(*_): raise TimeoutError("signal fixture")
        signal.signal(signal.SIGTERM, stop)
        timer = threading.Timer(.5, lambda: os.kill(os.getpid(), signal.SIGTERM))
        timer.start()
        try:
            with self.assertRaisesRegex(TimeoutError, "signal fixture"):
                runner.run([sys.executable, "-c", "import time;time.sleep(60)"])
        finally:
            timer.cancel(); timer.join(); signal.signal(signal.SIGTERM, old)
        self.clean(runner)

    def test_receipt_failure_happens_after_cleanup(self):
        runner = self.runner()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(IsADirectoryError):
                result = runner.run([sys.executable, "-c", "print('ok')"])
                Path(directory).write_text(result["stdout"])
        self.clean(runner)

    def test_setup_failure(self):
        runner = self.runner()
        with patch("apple_read_child.selectors.DefaultSelector", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                runner.run([sys.executable, "-c", "import time;time.sleep(60)"])
        self.clean(runner)

    def test_global_environment(self):
        with patch.dict(os.environ, {"DEVELOPER_DIR": "/bad", "HOME": "/keep"}):
            env = global_environment()
            self.assertNotIn("DEVELOPER_DIR", env)
            self.assertEqual(env["HOME"], "/keep")
            self.assertEqual(os.environ["DEVELOPER_DIR"], "/bad")


if __name__ == "__main__": unittest.main()
