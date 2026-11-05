"""Exact launchd provenance for independent OS jobs, never a name allowlist."""
import ctypes
import hashlib
from pathlib import Path
import plistlib
import re
import stat


def field(text, name):
    values = re.findall(r'^\t' + re.escape(name) + r' = (.+)$', text, re.M)
    if len(values) != 1:
        raise RuntimeError('Ambiguous launchd job field: ' + name)
    return values[0]


def qualify(row, label, detail, definition, executable, metadata):
    """The live job PID, immutable job definition and kernel path must agree."""
    path = '/System/Library/LaunchDaemons/' + label + '.plist'
    program = definition.get('Program') or definition.get('ProgramArguments', [None])[0]
    if not (re.fullmatch(r'com\.apple\.[A-Za-z0-9_.-]+', label)
            and detail.startswith('system/' + label + ' = {\n')
            and field(detail, 'pid') == str(row['pid'])
            and field(detail, 'path') == path
            and field(detail, 'domain') == 'system'
            and field(detail, 'type') == 'LaunchDaemon'
            and field(detail, 'program') == program == executable
            and definition.get('Label') == label
            and executable.startswith(('/usr/', '/System/Library/'))
            and row['ppid'] == 1
            and all(m['uid'] == 0 and not m['mode'] & 0o022
                    and m['regular'] and not m['symlink'] for m in metadata)):
        raise RuntimeError('Independent system job provenance not established')
    return dict(identity=row, label=label, path=path, executable=executable,
                detailSha256=hashlib.sha256(detail.encode()).hexdigest())


def probe(commands, rows, forbidden):
    """Read at most eight exact jobs. Unknown or racing identities stay unknown."""
    if not rows:
        return []
    if len(rows) > 8:
        raise RuntimeError('Too many unexplained processes for bounded reconciliation')
    response = commands.run(['launchctl', 'print', 'system'], 15)
    if response['exit']:
        raise RuntimeError('Cannot inspect system job domain')
    matches = re.findall(r'^\s+(\d+)\s+\S+\s+(com\.apple\.[\w.-]+)\s*$', response['stdout'], re.M)
    labels = {}
    for pid, label in matches:
        labels.setdefault(int(pid), []).append(label)
    lib = ctypes.CDLL('/usr/lib/libproc.dylib')
    lib.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    proofs = []
    for row in rows:
        if row['pid'] in forbidden or row['pgid'] in forbidden:
            continue
        values = labels.get(row['pid'], [])
        if len(values) != 1:
            continue
        label = values[0]
        response = commands.run(['launchctl', 'print', 'system/' + label], 15)
        if response['exit']:
            continue
        path = Path('/System/Library/LaunchDaemons') / (label + '.plist')
        definition = plistlib.loads(path.read_bytes())
        buf = ctypes.create_string_buffer(4096)
        if lib.proc_pidpath(row['pid'], buf, len(buf)) <= 0:
            continue
        executable = buf.value.decode()
        metadata = []
        for item in (path, Path(executable)):
            info = item.lstat()
            metadata.append(dict(uid=info.st_uid, mode=stat.S_IMODE(info.st_mode),
                                 regular=stat.S_ISREG(info.st_mode), symlink=item.is_symlink()))
        try:
            proof = qualify(row, label, response['stdout'], definition, executable, metadata)
        except RuntimeError:
            continue
        proof['definitionSha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        proofs.append(proof)
    return proofs


def reconcile_system_jobs(baseline, commands, records, current_pid):
    from apple_native_reconcile import inventory, reconcile
    current = inventory(commands.deadline)
    original = reconcile(baseline, current, records, current_pid)
    if original['passed'] or original['liveOwned'] or not original['recordedChildrenComplete']:
        return original
    forbidden = {current_pid, *(r['pid'] for r in records if r.get('pid')),
                 *(int(p) for r in records for p in r['identities'])}
    proofs = probe(commands, original['unexplainedProcesses'], forbidden)
    augmented = {int(k): v for k, v in baseline.items()}
    augmented.update({p['identity']['pid']: p['identity'] for p in proofs})
    final = reconcile(augmented, inventory(commands.deadline), records, current_pid)
    final['originalUnexplainedProcesses'] = original['unexplainedProcesses']
    final['independentSystemJobs'] = proofs
    return final
