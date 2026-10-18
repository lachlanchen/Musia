import sys
from pathlib import Path
import signal
import subprocess
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import apple_qa_command as qa


class AppleQACommandTests(unittest.TestCase):
    def test_app_exit_requires_proven_absence_not_inventory_error(self):
        for status in [0, 1, 2]:
            with patch.object(qa.subprocess, 'run', return_value=Mock(returncode=status)) as check:
                self.assertEqual(qa.qa_app_exited(), status == 1)
                self.assertEqual(check.call_args.args[0], ['pgrep', '-x', 'Musia'])

    def test_app_exit_does_not_match_its_own_verifier_arguments(self):
        # A disposable process carries the path which fooled the former -f check.
        # Exercise real pgrep locally, without any shared host or app launch.
        source = "import os,subprocess,sys; r=subprocess.run(['pgrep','-x',sys.argv[1]],capture_output=True,text=True); assert str(os.getpid()) not in r.stdout.splitlines(); assert r.returncode==1"
        subprocess.run([sys.executable, '-c', source, 'MusiaQAFixture',
                        '/tmp/MusiaQAFixture.app/Contents/MacOS/MusiaQAFixture'],
                       check=True, timeout=10)

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
