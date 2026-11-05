"""One read-only busy classifier for the boundary, guarded preflight and release.

Non-own Python interpreters are conservatively occupied: their ucomm alone
cannot distinguish a model worker from a small service. No argv or secrets are
collected, and no process is signalled. Only the freshly verified current
process/ancestor identities may be exempted.
"""
from pathlib import Path
import os
import re
import subprocess
import time


TOOLS = frozenset({
    'xcodebuild', 'swift-frontend', 'swiftc', 'clang', 'xctest', 'altool',
    'iTMSTransporter', 'UnrealEditor', 'UnrealEditor-Cmd', 'blender',
    'ollama', 'llama-server',
})
TOOL_NAMES = TOOLS | frozenset(
    name[:width] for name in TOOLS for width in (15, 16) if len(name) > width)
PS_FORMAT = 'pid=,ppid=,pgid=,lstart=,ucomm='


def parse_processes(output):
    result = {}
    for line in output.splitlines():
        fields = line.split(None, 8)
        assert len(fields) == 9, 'Incomplete process identity; occupied'
        pid, ppid, pgid = map(int, fields[:3])
        assert pid not in result, 'Duplicate process identity; occupied'
        result[pid] = dict(pid=pid, ppid=ppid, pgid=pgid,
                           started=' '.join(fields[3:8]), comm=fields[8].strip())
    return result


def busy_reason(comm):
    name = Path(comm.strip()).name
    if name in TOOL_NAMES:
        return 'native-model-game-tool'
    if re.fullmatch(r'(?:python|pypy)(?:[0-9]+(?:\.[0-9]+)*)?', name, re.I):
        return 'external-python-runner-unqualified'
    return None


def own_chain(table, current_pid):
    """Derive ancestors from current identity, never from a name or UID allowlist."""
    chain = {}
    pid = current_pid
    while pid > 1:
        assert pid not in chain, 'Cyclic ancestry; occupied'
        assert pid in table, 'Incomplete own ancestry; occupied'
        row = table[pid]
        assert row['pid'] == pid and row['started'], 'Invalid own identity; occupied'
        chain[pid] = dict(row)
        pid = row['ppid']
    assert current_pid in chain, 'Current identity missing; occupied'
    return chain


def classify_processes(table, pinned_own, fresh_own):
    """Refuse PID reuse/reparenting, then exempt exact current/ancestor records."""
    keys = ('pid', 'ppid', 'pgid', 'started', 'comm')
    assert set(fresh_own) == set(pinned_own), 'Own identities changed; occupied'
    for pid, expected in pinned_own.items():
        assert pid in table and all(
            table[pid][k] == expected[k] == fresh_own[pid][k] for k in keys
        ), 'Own identity changed; occupied'
    return [dict(row, comm=row['comm'].strip(), reason=busy_reason(row['comm']))
            for pid, row in table.items()
            if pid not in pinned_own and busy_reason(row['comm']) is not None]


def busy_processes(table, deadline):
    pinned = own_chain(table, os.getpid())
    remaining = deadline - time.clock_gettime(time.CLOCK_MONOTONIC)
    assert remaining > 0, 'Busy inspection deadline; occupied'
    fresh = parse_processes(subprocess.check_output(
        ['ps', '-p', ','.join(map(str, sorted(pinned))), '-o', PS_FORMAT],
        text=True, timeout=min(5, remaining)))
    assert time.clock_gettime(time.CLOCK_MONOTONIC) < deadline, 'Busy inspection deadline; occupied'
    return classify_processes(table, pinned, fresh)

