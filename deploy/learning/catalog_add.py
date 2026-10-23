"""Add one reviewed song to an immutable learning release; never edit ingress.

Run through the existing private admin helper after uploading a prepared packet.
Only the Musia learning service is restarted. Failed acceptance restores its
previous unit/current link; uncertain concurrent changes retain the journal.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import time
import urllib.request

BASE = Path('/srv/musia-learning')
STATE = Path('/var/lib/musia-learning')
UNIT = Path('/etc/systemd/system/musia-learning.service')
SERVICE = 'musia-learning.service'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def validate_packet(packet):
    media_id = packet['mediaId']
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', media_id):
        raise ValueError('Invalid song ID')
    prefix = f'website/data/songs/{media_id}/'
    files = packet['files']
    if not 3 <= len(files) <= 16 or packet['item']['id'] != media_id or packet['song']['id'] != media_id:
        raise ValueError('Invalid packet identity')
    if packet['item']['manifest'] != prefix.removeprefix('website/') + 'manifest.json':
        raise ValueError('Unexpected manifest path')
    for name, value in files.items():
        path = Path(name)
        if not name.startswith(prefix) or path.is_absolute() or '..' in path.parts or '\\' in name:
            raise ValueError('Packet path escapes the song')
        relative = name[len(prefix):]
        if relative not in ('manifest.json', 'study.json') and not re.fullmatch(r'lyrics/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+\.json', relative):
            raise ValueError('Non-catalog file in packet')
        if not isinstance(value, dict) or len(encode(value)) > 4 * 1024 * 1024:
            raise ValueError('Invalid catalog JSON')
    if not all(prefix + name in files for name in ('manifest.json', 'study.json')):
        raise ValueError('Incomplete song')
    return media_id


def command(args):
    return subprocess.run(list(map(str, args)), check=True, capture_output=True, text=True, timeout=60).stdout


def atomic(path, data, mode=0o600):
    temporary = path.with_name(path.name + '.catalog-new')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, 'wb') as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)


def current_link(release):
    temporary = BASE / 'current.catalog-new'
    temporary.symlink_to(release)
    os.replace(temporary, BASE / 'current')


def api(path):
    request = urllib.request.Request('http://127.0.0.1:18440' + path, headers={'Host': 'musia.lazying.art'})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def live_songs():
    return [api('/api/v1/songs/' + i['id']) for i in api('/api/v1/library')['items']]


def wait_healthy():
    for _ in range(40):
        try:
            if api('/healthz') == {'status': 'ok'}:
                return
        except OSError:
            pass
        time.sleep(0.25)
    raise RuntimeError('Musia did not become healthy')


def ingress_hashes():
    paths = [Path('/etc/lazystudio/Caddyfile')]
    result = {}
    while paths:
        path = paths.pop()
        if str(path) in result:
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError('Unexpected ingress file')
        data = path.read_bytes()
        result[str(path)] = sha(data)
        for line in data.decode().splitlines():
            if re.match(r'\s*import\s', line):
                match = re.fullmatch(r'\s*import\s+(/etc/[a-zA-Z0-9_./-]+)\s*', line)
                if not match or '..' in Path(match[1]).parts:
                    raise ValueError('Ingress import requires owner review')
                paths.append(Path(match[1]))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet', type=Path)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--expected-release', required=True)
    args = parser.parse_args()
    assert os.geteuid() == 0
    fd = os.open(args.packet, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as handle:
        info = os.fstat(handle.fileno())
        assert stat.S_ISREG(info.st_mode) and info.st_size <= 8 * 1024 * 1024
        raw = handle.read()
    assert sha(raw) == args.sha256
    packet = json.loads(raw)
    media_id = validate_packet(packet)
    with (STATE / 'deployment.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        marker = STATE / 'active-deployment'
        assert not marker.exists(), 'Another deployment needs reconciliation'
        assert (BASE / 'current').is_symlink()
        previous = (BASE / 'current').resolve()
        assert str(previous) == args.expected_release and previous.parent == BASE / 'releases'
        old_unit = UNIT.read_bytes()
        assert old_unit.count(str(previous).encode()) == 2
        assert command(['systemctl', 'is-active', SERVICE]).strip() == 'active'
        mem = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
        assert int(mem['MemAvailable'].split()[0]) >= 180 * 1024
        assert shutil.disk_usage(BASE).free > 512 * 1024 * 1024
        before = live_songs()
        assert before and before[0]['id'] == 'first-pulse', 'Unexpected built-in lesson ordering'
        assert media_id not in [song['id'] for song in before], 'Add-only: existing songs require separate review'
        ingress = ingress_hashes()
        caddy = command(['systemctl', 'show', 'lazystudio-caddy', '-p', 'MainPID', '-p', 'InvocationID'])
        transaction = 'catalog-' + args.sha256[:24]
        journal = STATE / 'deployments' / transaction
        assert not journal.exists()
        journal.mkdir(mode=0o700)
        atomic(journal / 'unit.before', old_unit)
        atomic(journal / 'before.json', encode({'release': str(previous), 'songs': before, 'ingress': ingress}))
        atomic(marker, transaction.encode())
        release = BASE / 'releases' / transaction
        changed = False
        new_unit = old_unit.replace(str(previous).encode(), str(release).encode())
        try:
            shutil.copytree(previous, release, symlinks=True)
            for name, value in packet['files'].items():
                target = release / 'app' / name
                assert target.resolve().is_relative_to(release / 'app'), 'Catalog parent escaped release'
                assert not target.exists()
                target.parent.mkdir(parents=True, exist_ok=True)
                atomic(target, encode(value), 0o644)
            catalog = release / 'app/website/data/catalog.json'
            value = json.loads(catalog.read_text())
            assert media_id not in [i['id'] for i in value['items']]
            value['items'].insert(0, packet['item'])
            atomic(catalog, encode(value), 0o644)
            # Prove all existing DTOs remain identical before any service change.
            probe = ('import json,sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); '
                     'from musia.learning import PublicLibrary; l=PublicLibrary(Path(sys.argv[1])); '
                     'print(json.dumps([l.song(i) for i in l.entries()]))')
            staged = json.loads(command([release / 'runtime/bin/python', '-B', '-c', probe, release / 'app']))
            expected = [packet['song']] + [song for song in before if song['id'] != 'first-pulse']
            assert staged == expected, 'Staged catalog differs from approved DTOs'
            manifest = json.loads((release / 'release.json').read_text())
            manifest['songIds'] = ['first-pulse'] + [song['id'] for song in staged]
            manifest['catalogAddition'] = {'mediaId': media_id, 'packetSha256': args.sha256, 'previousRelease': str(previous)}
            for name in list(manifest['files']) + ['app/' + p for p in packet['files']]:
                manifest['files'][name] = sha((release / name).read_bytes())
            atomic(release / 'release.json', encode(manifest), 0o644)
            assert UNIT.read_bytes() == old_unit and (BASE / 'current').resolve() == previous
            assert ingress_hashes() == ingress
            changed = True
            atomic(UNIT, new_unit, 0o644)
            command(['systemctl', 'daemon-reload'])
            command(['systemctl', 'restart', SERVICE])
            wait_healthy()
            assert live_songs() == [before[0]] + expected
            assert ingress_hashes() == ingress
            assert command(['systemctl', 'show', 'lazystudio-caddy', '-p', 'MainPID', '-p', 'InvocationID']) == caddy
            current_link(release)
            result = {'published': True, 'mediaId': media_id, 'release': str(release),
                      'previousRelease': str(previous), 'packetSha256': args.sha256,
                      'songCount': len(expected) + 1, 'ingressUnchanged': True,
                      'service': command(['systemctl', 'show', SERVICE, '-p', 'MainPID', '-p', 'ActiveState'])}
            atomic(journal / 'accepted.json', encode(result))
            assert marker.read_text() == transaction
            marker.unlink()
            print(json.dumps(result))
        except BaseException:
            if changed:
                assert UNIT.read_bytes() == new_unit, 'Concurrent unit edit: retain journal for reconciliation'
                atomic(UNIT, old_unit, 0o644)
                command(['systemctl', 'daemon-reload'])
                command(['systemctl', 'restart', SERVICE])
                wait_healthy()
                assert live_songs() == before
                if (BASE / 'current').resolve() == release:
                    current_link(previous)
            assert marker.read_text() == transaction
            atomic(journal / 'rolled-back.json', encode({'restored': True, 'serviceChanged': changed}))
            marker.unlink()
            raise


if __name__ == '__main__':
    main()
