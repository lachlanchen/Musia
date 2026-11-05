from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apple_system_job_provenance import qualify, reconcile_system_jobs


class SystemJobTests(unittest.TestCase):
    def test_reconciliation_accepts_only_same_proven_identity(self):
        init = dict(pid=1, ppid=0, pgid=1, started='init', comm='launchd')
        root = dict(pid=2, ppid=1, pgid=2, started='runner', comm='Python')
        job = dict(pid=3, ppid=1, pgid=3, started='job', comm='anything')
        rows = {1:init, 2:root, 3:job}
        runner = SimpleNamespace(deadline=999)
        with patch('apple_native_reconcile.inventory', return_value=rows), \
             patch('apple_system_job_provenance.probe', return_value=[dict(identity=job)]):
            result = reconcile_system_jobs({1:init}, runner, [], 2)
        self.assertTrue(result['passed'])
        for final in ({**rows, 3:{**job, 'started':'reused'}},
                      {**rows, 4:{**job, 'pid':4, 'pgid':4}}):
            with patch('apple_native_reconcile.inventory', side_effect=[rows, final]), \
                 patch('apple_system_job_provenance.probe', return_value=[dict(identity=job)]):
                self.assertFalse(reconcile_system_jobs({1:init}, runner, [], 2)['passed'])

    def test_owned_live_child_cannot_use_system_job_probe(self):
        root = dict(pid=2, ppid=1, pgid=2, started='runner', comm='Python')
        child = dict(pid=3, ppid=1, pgid=3, started='owned', comm='bluetoothd')
        records = [dict(pid=3, identities={'3':child}, complete=True, children_absent=True)]
        with patch('apple_native_reconcile.inventory', return_value={2:root,3:child}), \
             patch('apple_system_job_provenance.probe') as probe:
            result = reconcile_system_jobs({}, SimpleNamespace(deadline=999), records, 2)
        self.assertFalse(result['passed'])
        probe.assert_not_called()

    def test_pid_job_definition_and_executable_all_must_agree(self):
        row = dict(pid=123, ppid=1, pgid=123, started='exact', comm='not-used')
        label = 'com.apple.example'
        program = '/usr/libexec/example'
        detail = ('system/com.apple.example = {\n\tpid = 123\n'
                  '\tpath = /System/Library/LaunchDaemons/com.apple.example.plist\n'
                  '\tdomain = system\n\ttype = LaunchDaemon\n'
                  '\tprogram = /usr/libexec/example\n}\n')
        definition = dict(Label=label, Program=program)
        metadata = [dict(uid=0, mode=0o644, regular=True, symlink=False)] * 2
        self.assertEqual(qualify(row, label, detail, definition, program, metadata)['identity'], row)
        bad = [({**row, 'pid': 124}, detail, definition, program, metadata),
               (row, detail, {**definition, 'Program': '/tmp/spoof'}, program, metadata),
               (row, detail, definition, '/tmp/spoof', metadata),
               (row, detail, definition, program, [dict(uid=0, mode=0o666, regular=True, symlink=False)]),
               (row, detail.replace('\tdomain = system', '\tdomain = gui/501'), definition, program, metadata),
               (row, detail, definition, program, [dict(uid=0, mode=0o644, regular=True, symlink=True)])]
        for args in bad:
            with self.subTest(args=args), self.assertRaises(RuntimeError):
                qualify(args[0], label, *args[1:])


if __name__ == '__main__':
    unittest.main()
