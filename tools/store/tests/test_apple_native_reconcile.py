import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apple_host_busy import own_chain
from apple_native_lane import Guard
from apple_native_reconcile import inventory, reconcile
from apple_read_child import ReadCommands, clock


def linux_identity(pid):
    raw = Path('/proc/' + str(pid) + '/stat').read_text()
    fields = raw[raw.rfind(')') + 2:].split()
    return dict(pid=pid, ticks=int(fields[19]), state=fields[0])


@unittest.skipUnless(sys.platform == 'linux', 'Disposable orphan fixture uses Linux subreaper')
class NativeReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.lib = ctypes.CDLL(None)
        prior = ctypes.c_int()
        self.assertEqual(self.lib.prctl(37, ctypes.byref(prior), 0, 0, 0), 0)
        self.prior = prior.value
        self.assertEqual(self.lib.prctl(36, 1, 0, 0, 0), 0)

    def tearDown(self):
        self.assertEqual(self.lib.prctl(36, self.prior, 0, 0, 0), 0)

    def test_real_fast_detached_child_cannot_certify_absence(self):
        outside = subprocess.Popen(['/bin/sleep', '30'], start_new_session=True)
        orphan = None
        try:
            with tempfile.TemporaryDirectory() as temp:
                marker = Path(temp) / 'orphan.json'
                guard = Guard(Path(temp) / 'guard')
                guard.acquire(dict(owner='fixture', id='fixture', source='fixture'))
                before = inventory(clock() + 10)
                code = '''import os,sys,json,time
from pathlib import Path
p=os.fork()
if p:
 while not Path(sys.argv[1]).exists(): time.sleep(.001)
 os._exit(0)
os.setsid()
raw=Path('/proc/self/stat').read_text(); a=raw[raw.rfind(')')+2:].split()
with Path(sys.argv[1]).open('x') as f:
 json.dump({'pid':os.getpid(),'ticks':int(a[19])},f);f.flush();os.fsync(f.fileno())
fd=os.open('/dev/null',os.O_RDWR)
for n in (0,1,2):os.dup2(fd,n)
os.execv('/bin/sleep',['sleep','20'])
'''
                runner = ReadCommands(clock() + 15, reserve=5)
                runner.run([sys.executable, '-c', code, str(marker)], 5)
                orphan = json.loads(marker.read_text())
                current = inventory(clock() + 10)
                proof = reconcile(before, current, runner.records, os.getpid())
                if orphan['pid'] in current:
                    self.assertFalse(proof['passed'])
                    self.assertIn(orphan['pid'], {r['pid'] for r in proof['unexplainedProcesses'] + proof['liveOwned']})
                else:
                    # Sampling is permitted to catch and reap the exact child;
                    # it is never permitted to leave it live and certify absent.
                    self.assertTrue(all(r['children_absent'] for r in runner.records))
                if proof['passed']:
                    guard.release()
                else:
                    guard.verify()
                    self.assertTrue(guard.path.exists())
                self.assertIsNone(outside.poll())
                self.assertFalse(proof['signalsSent'])
                print(json.dumps(dict(fixture='fast-detached-child',
                      childLiveAtFinalSnapshot=orphan['pid'] in current,
                      finalGatePassed=proof['passed'],
                      guardRetained=guard.path.exists(), outsidePeerPreserved=True,
                      unknownFixtureChild=orphan['pid'] in {r['pid'] for r in proof['unexplainedProcesses']},
                      signalsFromReconciliation=False)))
                # Fixture-owned guard only; production uncertainty is retained.
                if guard.path.exists(): guard.release()
        finally:
            if orphan is not None:
                try:
                    row = linux_identity(orphan['pid'])
                    self.assertEqual(row['ticks'], orphan['ticks'])
                    if row['state'] != 'Z': os.kill(orphan['pid'], signal.SIGTERM)
                    os.waitpid(orphan['pid'], 0)
                except (FileNotFoundError, ChildProcessError):
                    pass
            self.assertIsNone(outside.poll())
            outside.terminate(); outside.wait(timeout=3)

    def test_ordinary_command_and_preexisting_peer(self):
        outside = subprocess.Popen(['/bin/sleep', '15'], start_new_session=True)
        try:
            before = inventory(clock() + 10)
            runner = ReadCommands(clock() + 15, reserve=5)
            result = runner.run(['/bin/echo', 'ordinary'], 5)
            current = inventory(clock() + 10)
            # Isolate the fixture from unrelated workstation processes without
            # changing the production inventory or reconciliation implementation.
            ids = set(own_chain(current, os.getpid())) | {outside.pid}
            scoped_before = {p: r for p, r in before.items() if p in ids}
            scoped_current = {p: r for p, r in current.items() if p in ids}
            proof = reconcile(scoped_before, scoped_current, runner.records, os.getpid())
            self.assertEqual(result['stdout'], 'ordinary\n')
            self.assertTrue(proof['passed'])
            self.assertFalse(proof['signalsSent'])
            self.assertIsNone(outside.poll())
        finally:
            outside.terminate(); outside.wait(timeout=3)

    def test_unobserved_new_process_not_exempted_by_command_name(self):
        base = {1: dict(pid=1, ppid=0, pgid=1, started='init', comm='init'),
                20: dict(pid=20, ppid=1, pgid=20, started='runner', comm='python')}
        for name in ('sleep', 'Python', 'xcodebuild', 'contactsd'):
            new = dict(pid=30, ppid=1, pgid=30, started='new', comm=name)
            proof = reconcile(base, {**base, 30: new}, [], 20)
            self.assertFalse(proof['passed'])
            self.assertEqual(proof['unexplainedProcesses'], [new])
            self.assertFalse(proof['signalsSent'])


if __name__ == '__main__':
    unittest.main()
