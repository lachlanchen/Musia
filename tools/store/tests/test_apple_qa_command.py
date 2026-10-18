import sys
from pathlib import Path
import signal
import subprocess
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import apple_qa_command as qa


class AppleQACommandTests(unittest.TestCase):
    def test_returns_exit_status_after_clean_completion(self):
        for status in [0, 65]:
            child = Mock(pid=123, wait=Mock(return_value=status))
            with patch.object(qa.subprocess, 'Popen', return_value=child) as launch, \
                    patch.object(qa, 'group_alive', return_value=False):
                self.assertEqual(qa.run(['fixture'], 30), status)
                self.assertTrue(launch.call_args.kwargs['start_new_session'])
                child.wait.assert_called_once_with(timeout=30)

    def test_timeout_retains_outer_guard_even_after_child_exit(self):
        child = Mock(pid=123)
        child.wait.side_effect = [subprocess.TimeoutExpired('fixture', 30), 0]
        with patch.object(qa.subprocess, 'Popen', return_value=child), \
                patch.object(qa.os, 'killpg') as stop:
            self.assertEqual(qa.run(['fixture'], 30), 76)
            stop.assert_called_once_with(123, signal.SIGTERM)

    def test_timeout_escalates_only_owned_group(self):
        child = Mock(pid=123)
        child.wait.side_effect = [subprocess.TimeoutExpired('fixture', 30),
                                 subprocess.TimeoutExpired('fixture', 15), -9]
        with patch.object(qa.subprocess, 'Popen', return_value=child), \
                patch.object(qa.os, 'killpg') as stop:
            self.assertEqual(qa.run(['fixture'], 30), 76)
            self.assertEqual([call.args for call in stop.call_args_list],
                             [(123, signal.SIGTERM), (123, signal.SIGKILL)])

    def test_uncertain_cleanup_retains_guard(self):
        for status, descendants in [(-15, False), (0, True)]:
            child = Mock(pid=123, wait=Mock(return_value=status))
            with patch.object(qa.subprocess, 'Popen', return_value=child), \
                    patch.object(qa, 'group_alive', return_value=descendants):
                self.assertEqual(qa.run(['fixture'], 30), 76)
