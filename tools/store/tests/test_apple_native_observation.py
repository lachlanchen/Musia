import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apple_read_child import ReadCommands, clock


class NativeObservationTests(unittest.TestCase):
    def test_native_output_does_not_trigger_ps_for_every_chunk(self):
        runner = ReadCommands(clock() + 15, reserve=5, inspection_timeout=15, observation_interval=1)
        original = runner.observe
        live = []
        def observe(record, child):
            if child.poll() is None:
                live.append(clock())
            return original(record, child)
        code = 'import time;\nfor i in range(30):\n print("output",flush=True);time.sleep(.01)'
        with patch.object(runner, 'observe', side_effect=observe):
            result = runner.run([sys.executable, '-c', code], 5)
        self.assertEqual(result['exit'], 0)
        self.assertEqual(len(result['stdout'].splitlines()), 30)
        self.assertEqual(len(live), 1)
        self.assertTrue(runner.records[0]['children_absent'])

    def test_observer_keeps_phase_deadline_and_read_defaults(self):
        runner = ReadCommands(clock() + 30, inspection_timeout=15)
        runner._phase_deadline = clock() + 1
        with patch('apple_read_child.table', return_value={}) as probe:
            runner.process_table()
        self.assertEqual(probe.call_args.args, (runner._phase_deadline, 15))
        default = ReadCommands(clock() + 30)
        self.assertEqual(default.inspection_timeout, 2)
        self.assertEqual(default.observation_interval, 0)


if __name__ == '__main__':
    unittest.main()
