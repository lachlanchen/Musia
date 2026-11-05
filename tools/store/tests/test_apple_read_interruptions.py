"""Real Linux child fixtures for the two reviewed cancellation boundaries."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apple_read_child import ReadCommands, clock


class InterruptionTests(unittest.TestCase):
    def setUp(self):
        self.peer = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(60)"], start_new_session=True)
        self.addCleanup(self.close_peer)
        self.previous = signal.getsignal(signal.SIGTERM)
        def interrupt(*_): raise TimeoutError("fixture cancellation")
        signal.signal(signal.SIGTERM, interrupt)
        self.addCleanup(signal.signal, signal.SIGTERM, self.previous)
        self.children = []
        self.addCleanup(self.close_children)

    def close_peer(self):
        self.peer.terminate(); self.peer.wait(timeout=5)

    def close_children(self):
        for child in self.children:
            if child.poll() is None: child.kill()
            child.wait(timeout=5)

    def assert_clean(self, runner):
        self.assertIsNone(self.peer.poll(), "Outside peer must be untouched")
        self.assertTrue(runner.records[0]["children_absent"])
        self.assertTrue(runner.records[0]["complete"])
        self.assertTrue(all(c.poll() is not None for c in self.children))

    def test_signal_before_popen_returns(self):
        original = subprocess.Popen
        def spawn(*args, **kwargs):
            child = original(*args, **kwargs)
            if args[0][0] == sys.executable:
                self.children.append(child)
                os.kill(os.getpid(), signal.SIGTERM)
            return child
        runner = ReadCommands(clock()+15, reserve=10)
        with patch("apple_read_child.subprocess.Popen", side_effect=spawn):
            with self.assertRaisesRegex(TimeoutError, "fixture cancellation"):
                runner.run([sys.executable, "-c", "import time;time.sleep(60)"])
        self.assertEqual(len(self.children), 1)
        self.assert_clean(runner)

    def test_second_signal_cannot_abort_cleanup(self):
        original = subprocess.Popen
        def spawn(*args, **kwargs):
            child = original(*args, **kwargs)
            if args[0][0] == sys.executable: self.children.append(child)
            return child
        runner = ReadCommands(clock()+15, reserve=10)
        timers = [threading.Timer(delay, lambda: os.kill(os.getpid(), signal.SIGTERM)) for delay in (.5, .9)]
        try:
            for timer in timers: timer.start()
            with patch("apple_read_child.subprocess.Popen", side_effect=spawn):
                with self.assertRaisesRegex(TimeoutError, "fixture cancellation"):
                    runner.run([sys.executable, "-c", "import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)"])
        finally:
            for timer in timers: timer.cancel(); timer.join()
        self.assert_clean(runner)


if __name__ == "__main__": unittest.main()
