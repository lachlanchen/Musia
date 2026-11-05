#!/usr/bin/env python3
"""Launch one explicitly admitted Musia native round on the pinned KVM host."""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import uuid

from apple_read_child import ReadCommands, clock
from apple_read_entry import HOST, HOST_UUID, digest, write_once

MODULES = ('apple_host_busy.py', 'apple_read_child.py', 'apple_internal_preflight.py', 'apple_native_lane.py')


def validate(admission, source, archive, folder, now, owner):
    assert admission['kind'] == 'musia-native-internal' and admission['build'] == '0.2.2(12)'
    assert admission['route'] == HOST and admission['hostUUID'] == HOST_UUID
    assert owner and admission['owner'] == owner
    assert admission['source'] == source and admission['archiveSha256'] == hashlib.sha256(archive).hexdigest()
    assert admission['hashes'] == {n: digest(folder / n) for n in (*MODULES, 'apple_native_entry.py')}
    assert admission['jobs'] == 1 and admission['cleanupSeconds'] == 120
    assert 120 < admission['wholeSeconds'] <= 3600
    assert admission['outerSeconds'] == admission['wholeSeconds'] + 100
    assert now < dt.datetime.fromisoformat(admission['startBeforeUTC'])
    assert admission['platform'] in ('ios', 'macos')
    if admission['platform'] == 'ios':
        assert admission['simulatorRuntime'].startswith('com.apple.CoreSimulator.SimRuntime.iOS-')
        assert admission['simulatorDeviceType'].startswith('com.apple.CoreSimulator.SimDeviceType.iPhone-')


def payload(admission, archive, folder):
    code = 'import sys,types,json,base64\n'
    for name in MODULES:
        module = Path(name).stem
        code += 'm=types.ModuleType(' + repr(module) + ');sys.modules[' + repr(module) + ']=m\n'
        code += 'exec(compile(' + repr((folder / name).read_text()) + ',' + repr(name) + ',"exec"),m.__dict__)\n'
    code += 'sys.exit(m.run(json.loads(' + repr(json.dumps(admission)) + '),base64.b64decode('
    code += repr(base64.b64encode(archive).decode()) + ')))\n'
    return code.encode()


def main(admission_path, archive_path, output):
    folder = Path(__file__).resolve().parent
    source = subprocess.check_output(['git', '-C', str(folder.parents[1]), 'rev-parse', 'HEAD'], text=True, timeout=3).strip()
    admission = json.loads(Path(admission_path).read_text())
    archive = Path(archive_path).read_bytes()
    validate(admission, source, archive, folder, dt.datetime.now(dt.timezone.utc), os.environ.get('CODEX_THREAD_ID'))
    data = payload(admission, archive, folder)
    output = Path(output); output.mkdir(mode=0o700, parents=True, exist_ok=False)
    write_once(output / 'intent.json', admission)
    commands = ReadCommands(clock() + admission['outerSeconds'], reserve=10, maximum=16_000_000)
    def stop(*_):
        signal.setitimer(signal.ITIMER_REAL, 0)
        raise TimeoutError('Original outer native deadline/interruption')
    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    signal.setitimer(signal.ITIMER_REAL, admission['outerSeconds'] - 10)
    try:
        argv = ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                '-o', 'ConnectionAttempts=1', '-o', 'ConnectTimeout=30', '-o', 'ControlMaster=no',
                '-o', 'ControlPath=none', HOST, '/usr/bin/python3', '-B', '-']
        response = commands.run(argv, admission['outerSeconds'] - 10, input_data=data)
        write_once(output / 'response.json', response)
        if response['stdout'].strip():
            result = json.loads(response['stdout'])
            write_once(output / 'result.json', result)
        assert response['exit'] == 0, 'Native round incomplete; preserve evidence and reconcile, no replay'
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        write_once(output / 'local-children.json', commands.records)


def handback(output):
    output = Path(output)
    admission = json.loads((output / 'intent.json').read_text())
    native = json.loads((output / 'result.json').read_text())
    assert admission.get('independentReadSeconds') == 90 and admission.get('independentOuterSeconds') == 130
    assert admission['owner'] == os.environ.get('CODEX_THREAD_ID') and admission['route'] == HOST
    identifier = str(uuid.UUID(admission['id']))
    assert native['admission'] == identifier and native.get('guardReleased') and native.get('preservationVerified')
    write_once(output / 'handback-intent.json', {'admission': identifier, 'at': dt.datetime.now(dt.timezone.utc).isoformat()})
    commands = ReadCommands(clock() + 130, reserve=10)
    def stop(*_):
        signal.setitimer(signal.ITIMER_REAL, 0)
        raise TimeoutError('Independent outer read deadline/interruption')
    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    signal.setitimer(signal.ITIMER_REAL, 120)
    relative = 'Projects/Musia/store/.runtime/native-' + identifier
    remote = 'exec /usr/bin/python3 -B "$HOME/' + relative + '/source/tools/store/apple_native_handback.py" "$HOME/' + relative + '"'
    try:
        response = commands.run(['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
             '-o', 'ConnectionAttempts=1', '-o', 'ConnectTimeout=30', '-o', 'ControlMaster=no', '-o', 'ControlPath=none', HOST, remote], 120)
        write_once(output / 'handback-response.json', response)
        assert response['exit'] == 0, 'Independent cleanup incomplete; no retry or successor inference'
        proof = json.loads(response['stdout'])
        assert proof['state'] == 'passed' and proof['admission'] == identifier
        write_once(output / 'independent-handback.json', proof)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        write_once(output / 'handback-local-children.json', commands.records)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('admission', nargs='?'); parser.add_argument('archive', nargs='?'); parser.add_argument('output', nargs='?')
    parser.add_argument('--handback', type=Path, help='Read back one completed admitted operation directory')
    args = parser.parse_args()
    if args.handback:
        assert not any((args.admission, args.archive, args.output))
        handback(args.handback)
    else:
        assert args.admission and args.archive and args.output
        main(args.admission, args.archive, args.output)
