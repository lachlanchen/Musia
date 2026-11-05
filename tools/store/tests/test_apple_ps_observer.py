import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apple_read_child import ReadCommands, clock


class ProcessSnapshotTests(unittest.TestCase):
    def test_ps_snapshot_is_not_sampled_by_a_concurrent_ps(self):
        runner = ReadCommands(clock() + 15, reserve=5)
        original = runner.observe
        observed = []
        def observe(record, child):
            # A nested inspector launched here can contaminate the snapshot.
            self.assertIsNotNone(child.returncode)
            observed.append(child.pid)
            return original(record, child)
        with patch.object(runner, 'observe', side_effect=observe):
            result = runner.run(['ps', '-p', str(os.getpid()), '-o', 'pid='], limit=5)
        self.assertEqual(result['exit'], 0)
        self.assertIn(str(os.getpid()), result['stdout'])
        self.assertTrue(observed, 'Post-command exact cleanup must still execute')
        self.assertTrue(runner.records[0]['complete'])
        self.assertTrue(runner.records[0]['children_absent'])

    def test_non_ps_children_still_have_live_ancestry_sampling(self):
        runner = ReadCommands(clock() + 15, reserve=5)
        original = runner.observe
        live = []
        def observe(record, child):
            if child.poll() is None:
                live.append(child.pid)
            return original(record, child)
        with patch.object(runner, 'observe', side_effect=observe):
            result = runner.run([sys.executable, '-c', 'import time;time.sleep(.15)'], limit=5)
        self.assertEqual(result['exit'], 0)
        self.assertTrue(live)
        self.assertTrue(runner.records[0]['children_absent'])


if __name__ == '__main__':
    unittest.main()
