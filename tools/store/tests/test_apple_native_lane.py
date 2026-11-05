import io
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apple_native_lane import Guard, extract_source, profile_snapshot, restore_profiles, sha
import apple_native_entry as entry


class NativeLaneTests(unittest.TestCase):
    def test_entry_pins_source_route_scope_and_budget(self):
        folder = Path(entry.__file__).parent
        now = dt.datetime.now(dt.timezone.utc)
        archive = b'fixture'
        admission = dict(kind='musia-native-internal', build='0.2.2(12)', route=entry.HOST,
                         hostUUID=entry.HOST_UUID, owner='fixture-owner',
                         source='pinned', archiveSha256=hashlib.sha256(archive).hexdigest(),
                         hashes={n: sha(folder/n) for n in (*entry.MODULES, 'apple_native_entry.py')},
                         jobs=1, cleanupSeconds=120, wholeSeconds=3600, outerSeconds=3700,
                         startBeforeUTC=(now + dt.timedelta(minutes=1)).isoformat(), platform='ios',
                         simulatorRuntime='com.apple.CoreSimulator.SimRuntime.iOS-26-5',
                         simulatorDeviceType='com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation')
        entry.validate(admission, 'pinned', archive, folder, now, 'fixture-owner')
        compile(entry.payload(admission, archive, folder), 'stream', 'exec')
        for key, value in [('route', 'other'), ('source', 'changed'), ('owner', 'other'), ('jobs', 2),
                           ('wholeSeconds', 3601), ('cleanupSeconds', 0), ('hashes', {}),
                           ('simulatorRuntime', ''), ('simulatorDeviceType', '')]:
            with self.subTest(key=key), self.assertRaises(AssertionError):
                entry.validate({**admission, key: value}, 'pinned', archive, folder, now, 'fixture-owner')

    def test_guard_refuses_existing_and_releases_only_own_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'guard'
            guard = Guard(path)
            guard.acquire(dict(owner='test-owner', id='test-id', source='test-source'))
            with self.assertRaises(FileExistsError):
                Guard(path).acquire(dict(owner='peer', id='peer', source='peer'))
            original = (path / 'owner.json').read_bytes()
            (path / 'owner.json').write_text(json.dumps({'owner': 'peer'}))
            with self.assertRaisesRegex(RuntimeError, 'token changed'):
                guard.release()
            self.assertTrue(path.exists())
            (path / 'owner.json').write_bytes(original)
            guard.release()
            self.assertFalse(path.exists())

    def archive(self, name, link=False):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w') as archive:
            member = tarfile.TarInfo(name)
            if link:
                member.type = tarfile.SYMTYPE; member.linkname = '/tmp/elsewhere'
            else:
                member.size = 3
            archive.addfile(member, None if link else io.BytesIO(b'abc'))
        return data.getvalue()

    def test_archive_refuses_traversal_links_runtime_and_foreign_tree(self):
        for name, link in [('../escape', False), ('/escape', False), ('apps/ios/linked', True),
                           ('apps/ios/.runtime/key', False), ('apps/ios-unrelated/key', False)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                with self.assertRaises(RuntimeError):
                    extract_source(self.archive(name, link), Path(folder) / 'source')

    def test_archive_extracts_only_new_private_source(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source'
            extract_source(self.archive('apps/ios/fixture.swift'), source)
            self.assertEqual((source / 'apps/ios/fixture.swift').read_bytes(), b'abc')
            with self.assertRaises(FileExistsError):
                extract_source(self.archive('apps/ios/fixture.swift'), source)

    def test_profiles_remove_only_identical_owned_additions(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            profiles = home / 'Library/MobileDevice/Provisioning Profiles'
            profiles.mkdir(parents=True)
            original = profiles / 'original'; original.write_bytes(b'original')
            before = profile_snapshot(home)
            added = profiles / 'owned'; added.write_bytes(b'owned')
            restore_profiles(home, before, {str(added): sha(added)})
            self.assertEqual(profile_snapshot(home), before)
            foreign = profiles / 'foreign'; foreign.write_bytes(b'foreign')
            with self.assertRaisesRegex(RuntimeError, 'Unowned'):
                restore_profiles(home, before, {})
            self.assertTrue(foreign.exists())
            self.assertEqual(original.read_bytes(), b'original')


if __name__ == '__main__':
    unittest.main()
