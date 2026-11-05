#!/usr/bin/env python3
"""Independent bounded readback after one native round; never cleans or signals peers."""
import json
import os
from pathlib import Path
import signal
import sys

from apple_native_lane import GUARD, profile_snapshot, require, sha, utc
from apple_host_busy import parse_processes, own_chain, classify_processes
from apple_read_child import ReadCommands, clock, global_environment


def inspect(root):
    root = Path(root).expanduser()
    require(root.parent == Path.home() / 'Projects/Musia/store/.runtime' and root.name.startswith('native-'), 'Wrong operation path')
    require(not root.is_symlink(), 'Symlink operation path')
    admission = json.loads((root / 'admission.json').read_text())
    result = json.loads((root / 'result.json').read_text())
    require(result.get('guardReleased') and result.get('preservationVerified') and not result.get('cleanupError'), 'Owner cleanup incomplete')
    commands = ReadCommands(clock() + 90, reserve=15)
    def stop(*_):
        signal.setitimer(signal.ITIMER_REAL, 0)
        raise TimeoutError('Independent read deadline/interruption')
    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    signal.setitimer(signal.ITIMER_REAL, 75)
    proof = dict(admission=admission['id'], at=utc())
    def call(argv, limit=10, env=None):
        value = commands.run([str(x) for x in argv], limit, env=env)
        require(value['exit'] == 0, 'Independent command failed')
        return value['stdout']
    try:
        require(not os.path.lexists(GUARD), 'A shared guard exists; do not probe SDK')
        rows = parse_processes(call(['ps', '-axo', 'pid=,ppid=,pgid=,lstart=,ucomm=']))
        chain = own_chain(rows, os.getpid())
        fresh = parse_processes(call(['ps', '-p', ','.join(map(str, chain)), '-o', 'pid=,ppid=,pgid=,lstart=,ucomm=']))
        require(not classify_processes(rows, chain, fresh), 'Host occupied; no SDK read')
        root_identity = result['rootIdentity']
        root_current = rows.get(root_identity['pid'])
        require(not root_current or root_current['started'] != root_identity['started'], 'Native root still exists')
        for child in result['children']:
            require(child['complete'] and child['children_absent'], 'Unclosed native child')
            require(not any(row['pgid'] == child['pid'] for row in rows.values()), 'Native group still exists')
            for identity in child['identities'].values():
                current = rows.get(identity['pid'])
                require(not current or current['started'] != identity['started'], 'Native identity still exists')
        proof['ownedChildrenAbsent'] = True
        cfg = json.loads((root.parent / 'config.json').read_text())
        env = dict(os.environ, DEVELOPER_DIR=cfg['xcode_developer_dir'])
        original = json.loads((root / 'preservation-before.json').read_text())
        devices = json.loads(call(['xcrun', 'simctl', 'list', 'devices', '--json'], 15, env))
        current = {d['udid']: [runtime, d['name'], d['state'], d.get('isAvailable')]
                   for runtime, values in devices['devices'].items() for d in values}
        require(current == original['devices'], 'Device baseline changed')
        require(json.loads(call(['xcrun', 'simctl', 'list', 'pairs', '--json'], 15, env)) == original['pairs'], 'Pair baseline changed')
        require(profile_snapshot(Path.home()) == original['profiles'], 'Profile baseline changed')
        require(call(['security', 'list-keychains', '-d', 'user']) == original['search'], 'Search list changed')
        require(call(['security', 'default-keychain', '-d', 'user']) == original['default'], 'Default keychain changed')
        require(call(['xcode-select', '-p'], env=global_environment()) == original['selection'], 'SDK selection changed')
        lock = call(['/usr/bin/python3', root / 'source/tools/store/apple_native_lane.py', '--keychain-state', cfg['apple_keychain']])
        require(lock == ('unlocked\n' if original['keychainUnlocked'] else 'locked\n'), 'Keychain lock changed')
        pins = json.loads((root / 'source-pins.json').read_text())
        require(all(not (root / 'source' / name).is_symlink() and sha(root / 'source' / name) == digest for name, digest in pins.items()), 'Source pins changed')
        require(not os.path.lexists(GUARD), 'Guard appeared during final read')
        proof.update(guardAbsent=True, preservationVerified=True, sourcePinsVerified=True, state='passed')
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        proof['children'] = commands.records
        proof['ended'] = utc()
        print(json.dumps(proof), flush=True)
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == '__main__':
    require(len(sys.argv) == 2, 'One exact operation path required')
    inspect(sys.argv[1])
