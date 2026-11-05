#!/usr/bin/env python3
"""One admitted native QA/archive round, never a scheduler or provider uploader.

The caller streams an exact source archive and admission over the existing pinned
SSH route. No shared file is changed before the atomic protocol1 guard. All
commands retain one deadline; uncertainty keeps the guard for owner recovery.
"""
import ctypes
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import re
import secrets
import shutil
import signal
import stat
import sys
import tarfile
import uuid

from apple_host_busy import parse_processes, own_chain, classify_processes
from apple_internal_preflight import collect, qualify, metadata
from apple_read_child import ReadCommands, clock, defer_cancellation, global_environment

GUARD = Path('/tmp/lazyingart-apple-build.lock')
RESERVE = 120


def require(value, message):
    if not value:
        raise RuntimeError(message)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def once(path, data):
    with open(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as stream:
        json.dump(data, stream, indent=2)
        stream.flush(); os.fsync(stream.fileno())


class Guard:
    def __init__(self, path=GUARD):
        self.path, self.identity, self.owner = path, None, None

    def acquire(self, admission):
        with defer_cancellation():
            self.path.mkdir(mode=0o700)
            info = self.path.lstat()
            self.identity = (info.st_dev, info.st_ino)
            self.owner = dict(protocol=1, app='Musia', owner=admission['owner'],
                              admission=admission['id'], token=secrets.token_hex(24),
                              pid=os.getpid(), acquired=utc(), source=admission['source'])
            once(self.path / 'owner.json', self.owner)

    def verify(self):
        info = self.path.lstat()
        require(not self.path.is_symlink() and (info.st_dev, info.st_ino) == self.identity,
                'Guard identity changed; preserve it')
        owner = self.path / 'owner.json'
        require(not owner.is_symlink() and json.loads(owner.read_text()) == self.owner,
                'Guard token changed; preserve it')
        require({p.name for p in self.path.iterdir()} == {'owner.json'}, 'Unexpected guard contents')

    def release(self):
        self.verify()
        (self.path / 'owner.json').unlink()
        self.path.rmdir()


def extract_source(data, destination):
    destination.mkdir(mode=0o700)
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:*') as archive:
        members = archive.getmembers()
        require(sum(m.size for m in members) < 200_000_000, 'Source archive too large')
        names = set()
        for member in members:
            p = PurePosixPath(member.name)
            require(not p.is_absolute() and '..' not in p.parts and p.parts
                    and member.name not in names and (member.isdir() or member.isfile()), 'Unsafe source member')
            names.add(member.name)
            require(p.parts[:2] in {('apps', 'ios'), ('apps', 'macos'), ('tools', 'store')}
                    or str(p) in {'apps', 'tools', 'store', 'store/release.json'}, 'Unexpected source member')
            require(not set(p.parts) & {'.runtime', '.git', 'DerivedData', '.build'}, 'Runtime in source archive')
            target = destination.joinpath(*p.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as out, archive.extractfile(member) as source:
                    out.write(source.read())
                target.chmod(0o700 if member.mode & 0o111 else 0o600)


def profile_snapshot(home):
    result = {}
    for folder in ('Library/MobileDevice/Provisioning Profiles',
                   'Library/Developer/Xcode/UserData/Provisioning Profiles'):
        root = home / folder
        require(not root.is_symlink(), 'Profile directory symlink')
        if not root.exists():
            continue
        for path in root.iterdir():
            info = path.lstat()
            require(stat.S_ISREG(info.st_mode) and not path.is_symlink(), 'Unknown profile entry')
            result[str(path)] = dict(sha256=sha(path), device=info.st_dev, inode=info.st_ino,
                                     mode=stat.S_IMODE(info.st_mode), mtime=info.st_mtime_ns)
    return result


def restore_profiles(home, before, allowed):
    after = profile_snapshot(home)
    require(all(after.get(p) == record for p, record in before.items()), 'An original profile changed')
    for name in set(after) - set(before):
        require(name in allowed and after[name]['sha256'] == allowed[name], 'Unowned new profile; preserve')
    for name in set(after) - set(before):
        path = Path(name)
        require(profile_snapshot(home).get(name) == after[name], 'New profile identity changed; preserve')
        path.unlink()
    require(profile_snapshot(home) == before, 'Profile restoration incomplete')


def keychain_unlocked(path):
    # This is called only in a separately bounded child, since Security can block.
    api = ctypes.CDLL('/System/Library/Frameworks/Security.framework/Security')
    api.SecKeychainOpen.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    api.SecKeychainGetStatus.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
    api.SecKeychainOpen.restype = api.SecKeychainGetStatus.restype = ctypes.c_int32
    reference, flags = ctypes.c_void_p(), ctypes.c_uint32()
    require(api.SecKeychainOpen(os.fsencode(path), ctypes.byref(reference)) == 0, 'Cannot inspect keychain')
    try:
        require(api.SecKeychainGetStatus(reference, ctypes.byref(flags)) == 0, 'Cannot inspect lock state')
        return bool(flags.value & 1)
    finally:
        cf = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        cf.CFRelease.argtypes = [ctypes.c_void_p]
        cf.CFRelease(reference)


def run(admission, source_archive):
    os.umask(0o077)
    require(admission['kind'] == 'musia-native-internal' and admission['build'] == '0.2.2(12)', 'Wrong admission')
    uuid.UUID(admission['id']); uuid.UUID(admission['owner'])
    require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(admission['startBeforeUTC']), 'Expired admission')
    require(admission['wholeSeconds'] <= 3600 and admission['wholeSeconds'] > RESERVE
            and admission['jobs'] == 1 and admission['cleanupSeconds'] == RESERVE, 'Wrong bounds')
    require(hashlib.sha256(source_archive).hexdigest() == admission['archiveSha256'], 'Source archive mismatch')
    whole = clock() + admission['wholeSeconds']
    commands = ReadCommands(whole, reserve=RESERVE, maximum=64_000_000)
    guard, result = Guard(), dict(started=utc(), state='incomplete', admission=admission['id'],
                                 source=admission['source'], platform=admission['platform'])
    home = Path.home()
    out = home / 'Projects/Musia/store/.runtime' / ('native-' + admission['id'])
    result['operationRoot'] = str(out)
    require(not os.path.lexists(out), 'Existing operation; no replay')
    original_profiles = None
    original_devices = original_pairs = original_search = original_default = None
    original_selection = original_lock = None
    allowed_profiles, owned_devices = {}, []
    source = out / 'source'
    config_path = home / 'Projects/Musia/store/.runtime/config.json'
    cfg, source_pins = None, None

    def stop(*_):
        signal.setitimer(signal.ITIMER_REAL, 0)
        raise TimeoutError('Original native work deadline/interruption')

    def call(name, argv, seconds, env=None):
        # Installed bundles must stay readable. The enclosing operation and every
        # receipt remain private; do not stamp 0600 onto Xcode's app resources.
        mask = os.umask(0o022)
        try:
            value = commands.run([str(x) for x in argv], seconds, env=env)
        finally:
            os.umask(mask)
        if out.exists():
            once(out / (name + '.json'), value)
        require(value['exit'] == 0, 'Native phase failed: ' + name)
        return value['stdout']

    def device_state(env):
        return json.loads(call('devices-' + secrets.token_hex(3), ['xcrun', 'simctl', 'list', 'devices', '--json'], 15, env))

    def state_map(value):
        return {d['udid']: (runtime, d['name'], d['state'], d.get('isAvailable'))
                for runtime, devices in value['devices'].items() for d in devices}

    def lock_state():
        value = call('lock-' + secrets.token_hex(3), ['/usr/bin/python3', source / 'tools/store/apple_native_lane.py',
                     '--keychain-state', cfg['apple_keychain']], 12)
        require(value in ('locked\n', 'unlocked\n'), 'Unknown lock state')
        return value == 'unlocked\n'

    def busy():
        rows = parse_processes(call('processes-' + secrets.token_hex(3), ['ps', '-axo', 'pid=,ppid=,pgid=,lstart=,ucomm='], 8))
        chain = own_chain(rows, os.getpid())
        if 'rootIdentity' not in result:
            result['rootIdentity'] = chain[os.getpid()]
        require(chain[os.getpid()] == result['rootIdentity'], 'Native root identity changed')
        fresh = parse_processes(call('ancestry-' + secrets.token_hex(3), ['ps', '-p', ','.join(map(str, chain)),
                                '-o', 'pid=,ppid=,pgid=,lstart=,ucomm='], 8))
        require(not classify_processes(rows, chain, fresh), 'Peer activity; stop without signals')

    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    signal.setitimer(signal.ITIMER_REAL, max(.01, whole - RESERVE - clock()))
    env = None
    try:
        initial = {}; collect(config_path, commands, initial); qualify(initial)
        guard.acquire(admission)
        busy()
        memory = call('memory-inside', ['memory_pressure', '-Q'], 10)
        swap = call('swap-inside', ['sysctl', 'vm.swapusage'], 8)
        free = re.search(r'free percentage:\s*(\d+)%', memory)
        total = float(re.search(r'total = ([\d.]+)M', swap)[1])
        used = float(re.search(r'used = ([\d.]+)M', swap)[1])
        require(free and int(free[1]) >= 40 and (total == used == 0 or total > 0 and used / total <= .75)
                and shutil.disk_usage(home).free >= 30 * 1024 ** 3, 'Resource gate inside guard')
        out.mkdir(mode=0o700)
        once(out / 'admission.json', admission); once(out / 'initial.json', initial)
        once(out / 'guard.json', dict(owner=guard.owner, identity=guard.identity))
        extract_source(source_archive, source)
        source_pins = {str(p.relative_to(source)): sha(p) for p in source.rglob('*') if p.is_file()}
        once(out / 'source-pins.json', source_pins)
        os.chdir(source)
        cfg = json.loads(config_path.read_text())
        env = dict(os.environ, DEVELOPER_DIR=cfg['xcode_developer_dir'], MUSIA_ROOT=str(source),
                   MUSIA_STORE_RUNTIME=str(source / 'store/.runtime'), MUSIA_STORE_CONFIG=str(config_path),
                   MUSIA_BUILD_JOBS='1', MUSIA_MAC_RELEASE='0.2.2-12',
                   MUSIA_MAC_PROFILE_PATH=str(config_path.parent / 'macos-20261004/Musia_Mac_App_Store.provisionprofile'),
                   MUSIA_KEYCHAIN=cfg['apple_keychain'])
        env.pop('MUSIA_LIVE_API', None)
        interpreter = home / '.local/share/musia/store-python/bin/python'
        require(interpreter.is_file() and os.access(interpreter, os.X_OK), 'Existing store interpreter unavailable')
        password_file = home / '.config/echomind/apple/release-keychain.pass'
        password_info = metadata(password_file)
        require(password_info.get('regular') and not password_info.get('symlink')
                and password_info.get('uid') == os.getuid() and not int(password_info['mode'], 8) & 0o077,
                'Existing private signer password file unavailable; no credential changes')
        actual_source = call('native-source', ['/usr/bin/python3', '-c',
            'import sys;sys.path.insert(0,"tools/store");from storelib import source_sha;print(source_sha("ios"))'], 15, env).strip()
        require(actual_source == admission['iosSourceSha256'], 'Native source differs')
        original_devices = state_map(device_state(env))
        original_pairs = json.loads(call('pairs-before', ['xcrun', 'simctl', 'list', 'pairs', '--json'], 15, env))
        original_search = call('search-before', ['security', 'list-keychains', '-d', 'user'], 10)
        original_default = call('default-before', ['security', 'default-keychain', '-d', 'user'], 10)
        original_selection = call('selection-before', ['xcode-select', '-p'], 8, global_environment())
        original_profiles = profile_snapshot(home)
        original_lock = lock_state()
        once(out / 'preservation-before.json', dict(devices=original_devices, pairs=original_pairs,
             profiles=original_profiles, keychainUnlocked=original_lock, search=original_search,
             default=original_default, selection=original_selection))
        for key, suffix in (('apple_profile_path', '.mobileprovision'), ('apple_watch_profile_path', '.mobileprovision'),
                            ('mac', '.provisionprofile')):
            path = Path(env['MUSIA_MAC_PROFILE_PATH'] if key == 'mac' else cfg[key])
            profile = plistlib.loads(call('profile-' + key, ['security', 'cms', '-D', '-i', path], 15).encode())
            for folder in ('Library/MobileDevice/Provisioning Profiles', 'Library/Developer/Xcode/UserData/Provisioning Profiles'):
                allowed_profiles[str(home / folder / (profile['UUID'] + suffix))] = sha(path)
        call('core-tests', ['swift', 'test', '--package-path', source / 'apps/ios', '--scratch-path', out / 'core', '--jobs', '1'], 600, env)
        result['corePassed'] = True
        if admission['platform'] == 'ios':
            runtime, device_type = admission['simulatorRuntime'], admission['simulatorDeviceType']
            require(runtime.startswith('com.apple.CoreSimulator.SimRuntime.iOS-'), 'Not an iOS runtime')
            name = 'Musia-QA-' + admission['id']
            udid = call('sim-create', ['xcrun', 'simctl', 'create', name, device_type, runtime], 30, env).strip()
            uuid.UUID(udid); owned_devices.append(udid)
            once(out / 'owned-device.json', dict(udid=udid, name=name, runtime=runtime))
            call('sim-boot', ['xcrun', 'simctl', 'boot', udid], 30, env)
            call('sim-boot-ready', ['xcrun', 'simctl', 'bootstatus', udid, '-b'], 180, env)
            xcode = ['xcodebuild', '-project', 'apps/ios/Musia.xcodeproj', '-scheme', 'Musia',
                     '-configuration', 'Debug', '-destination', 'platform=iOS Simulator,id=' + udid,
                     '-derivedDataPath', out / 'ios-qa', '-jobs', '1', '-parallel-testing-enabled', 'NO',
                     'CODE_SIGNING_ALLOWED=YES', 'CODE_SIGN_IDENTITY=-', 'ONLY_ACTIVE_ARCH=YES',
                     'COMPILER_INDEX_STORE_ENABLE=NO']
            call('ios-build-for-testing', xcode + ['build-for-testing'], 900, env)
            for case in ('testSimpleCreatorComposer', 'testStageLayoutAndPracticeSwitch'):
                bundle = out / (case + '.xcresult')
                call(case, xcode + ['test-without-building', '-only-testing:MusiaUITests/PracticeSmokeTests/' + case,
                     '-resultBundlePath', bundle, '-collect-test-diagnostics', 'never', '-test-timeouts-enabled', 'YES',
                     '-maximum-test-execution-time-allowance', '180'], 300, env)
                call(case + '-captures', ['xcrun', 'xcresulttool', 'export', 'attachments', '--path', bundle,
                     '--output-path', out / (case + '-captures')], 60, env)
            result['nativeUIPassed'] = True
            call('ios-archive-export', ['bash', 'tools/store/build_creator_apple.sh', 'ios'], 1200, env)
            receipts = list((source / 'store/.runtime/artifacts').glob('ios-0.2.2-12-*/build.json'))
            require(len(receipts) == 1, 'Missing exact iOS build receipt')
            receipt = receipts[0]
            build = json.loads(receipt.read_text())
            artifact = receipt.parent / build['artifact']
            require(sha(artifact) == build['artifact_sha256'], 'Export artifact changed')
            inspection = receipt
        else:
            require(admission['platform'] == 'macos', 'Unknown native platform')
            call('mac-compile', ['xcodebuild', '-project', 'apps/macos/Musia.xcodeproj', '-scheme', 'Musia',
                 '-configuration', 'Debug', '-destination', 'generic/platform=macOS', '-derivedDataPath', out / 'mac-qa',
                 '-jobs', '1', 'CODE_SIGNING_ALLOWED=NO', 'COMPILER_INDEX_STORE_ENABLE=NO', 'build'], 900, env)
            result['macCompilePassed'] = True
            call('mac-archive-export', ['bash', 'tools/store/build_creator_apple.sh', 'macos'], 1200, env)
            artifact = source / 'store/.runtime/macos-0.2.2-12/export/Musia.pkg'
            call('mac-inspection', [home / '.local/share/musia/store-python/bin/python', 'tools/store/upload_macos.py',
                 artifact, '--sha256', sha(artifact), '--version', '0.2.2', '--build', '12', '--inspect-only'], 120, env)
            inspection = source / 'store/.runtime/macos-uploads' / sha(artifact) / 'inspection.json'
            require(inspection.is_file(), 'Mac inspection missing')
        result['artifact'] = dict(platform=admission['platform'], version='0.2.2', build='12',
             source=admission['source'], iosSourceSha256=actual_source, path=str(artifact),
             sha256=sha(artifact), bytes=artifact.stat().st_size, inspection=str(inspection),
             inspectionSha256=sha(inspection))
        once(out / 'artifact.json', result['artifact'])
        result['state'] = 'native_passed_pending_visual_review_and_provider_upload'
    except BaseException as exc:
        result['error'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        with defer_cancellation(deliver=False):
            commands.reserve = 0
            try:
                if guard.identity is not None:
                    result['guard'] = dict(identity=guard.identity, owner=guard.owner)
                    guard.verify()
                    require(all(r['complete'] and r['children_absent'] for r in commands.records), 'Child cleanup incomplete')
                    if original_devices is not None:
                        current = state_map(device_state(env))
                        # A create command may succeed even if its reply is lost.
                        # Only an exact new operation name absent from the baseline
                        # is eligible for this operation's cleanup.
                        matches = [udid for udid, row in current.items() if udid not in original_devices
                                   and row[1] == 'Musia-QA-' + admission['id']]
                        require(len(matches) <= 1, 'Ambiguous owned simulator; preserve')
                        for udid in matches:
                            if udid not in owned_devices:
                                owned_devices.append(udid)
                    for udid in owned_devices:
                        current = state_map(device_state(env))
                        require(udid in current and current[udid][1] == 'Musia-QA-' + admission['id'], 'Owned device identity changed')
                        if current[udid][2] != 'Shutdown':
                            call('sim-shutdown', ['xcrun', 'simctl', 'shutdown', udid], 35, env)
                        call('sim-delete', ['xcrun', 'simctl', 'delete', udid], 35, env)
                    if original_lock is not None:
                        if not original_lock and lock_state():
                            call('restore-keychain', ['security', 'lock-keychain', cfg['apple_keychain']], 15)
                        require(lock_state() == original_lock, 'Keychain lock state changed')
                    if original_profiles is not None:
                        restore_profiles(home, original_profiles, allowed_profiles)
                    if original_devices is not None:
                        require(state_map(device_state(env)) == original_devices, 'Original devices changed')
                    if original_pairs is not None:
                        require(json.loads(call('pairs-after', ['xcrun', 'simctl', 'list', 'pairs', '--json'], 15, env)) == original_pairs, 'Original pairs changed')
                    if original_search is not None:
                        require(call('search-after', ['security', 'list-keychains', '-d', 'user'], 10) == original_search, 'Search list changed')
                    if original_default is not None:
                        require(call('default-after', ['security', 'default-keychain', '-d', 'user'], 10) == original_default, 'Default keychain changed')
                    if original_selection is not None:
                        require(call('selection-after', ['xcode-select', '-p'], 8, global_environment()) == original_selection, 'Global SDK changed')
                    if source_pins is not None:
                        require(all((source / name).is_file() and not (source / name).is_symlink()
                                    and sha(source / name) == digest for name, digest in source_pins.items()), 'Staged source changed')
                    busy()
                    require(all(r['complete'] and r['children_absent'] for r in commands.records), 'Final child cleanup incomplete')
                    guard.release()
                    result['guardReleased'] = True
                    result['preservationVerified'] = True
            except BaseException as exc:
                result['cleanupError'] = type(exc).__name__ + ': ' + str(exc)
                result['guardReleased'] = False
            result['ended'] = utc(); result['children'] = commands.records
            if out.exists():
                once(out / 'result.json', result)
            print(json.dumps(result), flush=True)
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    return 0 if result['state'].startswith('native_passed') and result.get('guardReleased') else 1


if __name__ == '__main__':
    require(len(sys.argv) == 3 and sys.argv[1] == '--keychain-state', 'Use the admitted streaming entry')
    print('unlocked' if keychain_unlocked(Path(sys.argv[2])) else 'locked')
