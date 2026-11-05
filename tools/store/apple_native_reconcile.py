"""Conservative native-process reconciliation, independent of sampled ancestry.

A missed double-fork cannot become an absence claim. New unexplained processes
are evidence of uncertainty, not permission to signal them or classify by name.
"""
import os
import subprocess
import sys

from apple_host_busy import own_chain, parse_processes
from apple_read_child import clock, defer_cancellation, same


def inventory(deadline):
    remaining = deadline - clock()
    if remaining <= 3:
        raise TimeoutError('Insufficient native process inventory/reap budget')
    column = 'ucomm=' if sys.platform == 'darwin' else 'comm='
    child = None
    try:
        with defer_cancellation():
            child = subprocess.Popen(['ps', '-axo', 'pid=,ppid=,pgid=,lstart=,' + column],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     start_new_session=True)
        out, error = child.communicate(timeout=min(5, remaining - 2))
        if child.returncode or error or len(out) > 2_000_000:
            raise RuntimeError('Incomplete native process inventory')
        rows = parse_processes(out.decode())
        # The exact unreused direct inspector is already reaped, not a name rule.
        rows.pop(child.pid, None)
        if clock() >= deadline:
            raise TimeoutError('Native process inventory deadline')
        return rows
    finally:
        with defer_cancellation(deliver=False):
            if child is not None:
                if child.poll() is None:
                    child.kill()
                child.wait(timeout=max(.01, min(2, deadline - clock())))
                child.stdout.close(); child.stderr.close()


def reconcile(baseline, current, records, current_pid):
    baseline = {int(k): v for k, v in baseline.items()}
    chain = own_chain(current, current_pid)
    known = {int(pid): row for record in records for pid, row in record['identities'].items()}
    groups = {record['pid'] for record in records if record.get('pid')}
    live = [row for pid, row in current.items()
            if row['pgid'] in groups or pid in known and same(known[pid], row)]
    complete = all(r['complete'] and r['children_absent'] for r in records)
    # Never regard adoption by init, this runner or its ancestors as peer proof.
    forbidden = {0, 1, *chain, *known, *groups}
    peers = {pid for pid, row in current.items()
             if pid not in forbidden and pid in baseline and same(baseline[pid], row)}
    changed = True
    while changed:
        changed = False
        for pid, row in current.items():
            if pid not in forbidden and pid not in peers and row['ppid'] in peers:
                peers.add(pid); changed = True
    unknown = [row for pid, row in current.items()
               if pid not in chain and pid not in peers
               and not (pid in baseline and same(baseline[pid], row))
               and not (pid in known and same(known[pid], row))]
    return dict(passed=complete and not live and not unknown,
                recordedChildrenComplete=complete, liveOwned=live,
                unexplainedProcesses=unknown,
                preservedPeerDescendants=[current[pid] for pid in sorted(peers)
                                          if pid not in baseline],
                signalsSent=False)
