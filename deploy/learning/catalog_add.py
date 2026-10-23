"""Add or unlist one reviewed song in an immutable release; never edit ingress.

Run through the existing private admin helper after uploading a prepared packet.
Only the Musia learning service is restarted. Failed acceptance restores its
previous unit/current link; uncertain concurrent changes retain the journal.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import stat
import subprocess
import time
import urllib.request
import urllib.error

BASE = Path('/srv/musia-learning')
STATE = Path('/var/lib/musia-learning')
UNIT = Path('/etc/systemd/system/musia-learning.service')
SERVICE = 'musia-learning.service'
HTTPS_VERIFICATION_PORT = 443


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def validate_packet(packet):
    media_id = packet['mediaId']
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', media_id) or media_id == 'first-pulse':
        raise ValueError('Invalid song ID')
    operation = packet.get('operation', 'add')
    if operation == 'unlist':
        if set(packet) != {'operation', 'mediaId', 'song'} or packet['song'].get('id') != media_id:
            raise ValueError('Unlisting requires the exact current song DTO and no replacement files')
        return media_id
    if operation != 'add':
        raise ValueError('Unknown catalog operation')
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


def unlist_metadata(catalog, manifest, media_id):
    catalog, manifest = copy.deepcopy(catalog), copy.deepcopy(manifest)
    items = [item for item in catalog['items'] if item['id'] == media_id]
    if len(items) != 1 or manifest['id'] != media_id or media_id == 'first-pulse':
        raise ValueError('Unlisting identity mismatch')
    if catalog.get('defaultMedia') == media_id:
        raise ValueError('Select a different default before unlisting this song')
    if items[0]['manifest'] != f'data/songs/{media_id}/manifest.json':
        raise ValueError('Unexpected manifest path')
    items[0].update(visibility='unlisted', releaseStage='preview', category='preview',
                    previewLabel='Listening Preview', edition={'status': 'preview'})
    manifest.setdefault('publication', {}).update(visibility='unlisted', stage='preview', listed=False)
    manifest['edition'] = {'status': 'preview'}
    return catalog, manifest


def verify_public_unlisted(media_id, expected_ids):
    if [item['id'] for item in public_api('/api/v1/library')['items']] != expected_ids:
        raise ValueError('Public library differs after unlisting')
    try:
        public_api('/api/v1/songs/' + media_id)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    else:
        raise ValueError('Unlisted song is still publicly available in the app API')


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


def public_api(path):
    authority = 'musia.lazying.art'
    if HTTPS_VERIFICATION_PORT != 443:
        authority += ':' + str(HTTPS_VERIFICATION_PORT)
    with urllib.request.urlopen('https://' + authority + path, timeout=20) as response:
        return json.load(response)


def require_route(config, media_id):
    """A catalog item needs an admitted detail route, not just a library row."""
    matches = []

    def visit(value):
        if isinstance(value, dict):
            paths = value.get('path')
            if isinstance(paths, list) and '/api/v1/songs/first-pulse' in paths:
                matches.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(config)
    if (len(matches) != 1 or sorted(matches[0].get('method', [])) != ['GET', 'HEAD']
            or '/api/v1/songs/' + media_id not in matches[0]['path']):
        raise ValueError('New song detail route must be admitted by the ingress owner before activation')


def verify_route_admission(media_id):
    with urllib.request.urlopen('http://127.0.0.1:12019/config/', timeout=10) as response:
        require_route(json.load(response), media_id)


def verify_public_song(song):
    if public_api('/api/v1/songs/' + song['id']) != song:
        raise ValueError('Public song differs from reviewed packet')
    if [i['id'] for i in public_api('/api/v1/library')['items']].count(song['id']) != 1:
        raise ValueError('Public library must contain the new song exactly once')


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


def ingress_hashes(root=Path('/etc/lazystudio/Caddyfile')):
    paths = [root]
    result = {}
    snippets, imports = set(), set()
    while paths:
        path = paths.pop()
        if str(path) in result:
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError('Unexpected ingress file')
        data = path.read_bytes()
        result[str(path)] = sha(data)
        text = data.decode()
        snippets.update(re.findall(r'^\s*\(([a-zA-Z0-9_-]+)\)\s*\{', text, re.M))
        for line in text.splitlines():
            if re.match(r'\s*import\s', line):
                parts = shlex.split(line, comments=True)
                if len(parts) != 2:
                    raise ValueError('Ingress import requires owner review')
                target = parts[1]
                if re.fullmatch(r'/etc/[a-zA-Z0-9_./-]+', target) and '..' not in Path(target).parts:
                    paths.append(Path(target))
                elif re.fullmatch(r'[a-zA-Z0-9_-]+', target):
                    imports.add(target)
                else:
                    raise ValueError('Ingress import requires owner review')
    if not imports <= snippets:
        raise ValueError('Ingress imports an unrecognized snippet')
    return result


def main():
    global HTTPS_VERIFICATION_PORT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet', type=Path)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--expected-release', required=True)
    parser.add_argument('--attempt', type=int, default=1, help='Fresh bounded retry; preserve earlier evidence')
    parser.add_argument('--https-verification-port', type=int, choices=(443, 18443), default=443,
                        help='18443 is the existing TLS listener; requires a separate external 443 receipt')
    args = parser.parse_args()
    assert os.geteuid() == 0
    assert 1 <= args.attempt <= 99
    HTTPS_VERIFICATION_PORT = args.https_verification_port
    fd = os.open(args.packet, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as handle:
        info = os.fstat(handle.fileno())
        assert stat.S_ISREG(info.st_mode) and info.st_size <= 8 * 1024 * 1024
        raw = handle.read()
    assert sha(raw) == args.sha256
    packet = json.loads(raw)
    media_id = validate_packet(packet)
    unlist = packet.get('operation') == 'unlist'
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
        if unlist:
            assert [song for song in before if song['id'] == media_id] == [packet['song']], 'Current song changed since review'
        else:
            assert media_id not in [song['id'] for song in before], 'Add-only: existing songs require separate review'
        ingress = ingress_hashes()
        if not unlist:
            verify_route_admission(media_id)
        caddy = command(['systemctl', 'show', 'lazystudio-caddy', '-p', 'MainPID', '-p', 'InvocationID'])
        transaction = 'catalog-' + args.sha256[:24]
        if args.attempt != 1:
            transaction += '-attempt' + str(args.attempt)
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
            for name, value in packet.get('files', {}).items():
                target = release / 'app' / name
                assert target.resolve().is_relative_to(release / 'app'), 'Catalog parent escaped release'
                assert not target.exists()
                target.parent.mkdir(parents=True, exist_ok=True)
                atomic(target, encode(value), 0o644)
            catalog = release / 'app/website/data/catalog.json'
            value = json.loads(catalog.read_text())
            if unlist:
                song_path = release / f'app/website/data/songs/{media_id}/manifest.json'
                assert song_path.resolve().is_relative_to(release / 'app') and not song_path.is_symlink()
                value, song_manifest = unlist_metadata(value, json.loads(song_path.read_text()), media_id)
                atomic(song_path, encode(song_manifest), 0o644)
            else:
                assert media_id not in [i['id'] for i in value['items']]
                value['items'].insert(0, packet['item'])
            atomic(catalog, encode(value), 0o644)
            # Prove all existing DTOs remain identical before any service change.
            probe = ('import json,sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); '
                     'from musia.learning import PublicLibrary; l=PublicLibrary(Path(sys.argv[1])); '
                     'print(json.dumps([l.song(i) for i in l.entries()]))')
            staged = json.loads(command([release / 'runtime/bin/python', '-B', '-c', probe, release / 'app']))
            expected = ([song for song in before if song['id'] not in ('first-pulse', media_id)] if unlist
                        else [packet['song']] + [song for song in before if song['id'] != 'first-pulse'])
            assert staged == expected, 'Staged catalog differs from approved DTOs'
            manifest = json.loads((release / 'release.json').read_text())
            manifest['songIds'] = ['first-pulse'] + [song['id'] for song in staged]
            manifest['catalogUnlisting' if unlist else 'catalogAddition'] = {
                'mediaId': media_id, 'packetSha256': args.sha256, 'previousRelease': str(previous)}
            for name in list(manifest['files']) + ['app/' + p for p in packet.get('files', {})]:
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
            if unlist:
                verify_public_unlisted(media_id, [song['id'] for song in [before[0]] + expected])
            else:
                verify_public_song(packet['song'])
            assert ingress_hashes() == ingress
            assert command(['systemctl', 'show', 'lazystudio-caddy', '-p', 'MainPID', '-p', 'InvocationID']) == caddy
            current_link(release)
            result = {'published': not unlist, 'unlisted': unlist, 'mediaId': media_id, 'release': str(release),
                      'previousRelease': str(previous), 'packetSha256': args.sha256,
                      'songCount': len(expected) + 1, 'ingressUnchanged': True,
                      'publicDetailVerified': HTTPS_VERIFICATION_PORT == 443,
                      'tlsDetailVerified': True, 'httpsVerificationPort': HTTPS_VERIFICATION_PORT,
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
