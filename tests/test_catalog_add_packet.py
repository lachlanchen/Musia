import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('catalog_add', Path(__file__).resolve().parents[1] / 'deploy/learning/catalog_add.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PacketTests(unittest.TestCase):
    def packet(self):
        prefix = 'website/data/songs/example/'
        return {'mediaId': 'example', 'item': {'id': 'example', 'manifest': 'data/songs/example/manifest.json'},
                'song': {'id': 'example'}, 'files': {prefix + path: {} for path in
                ('manifest.json', 'study.json', 'lyrics/ja-vocal/ja.json')}}

    def test_valid(self):
        self.assertEqual(module.validate_packet(self.packet()), 'example')

    def test_escapes_and_non_catalog_files_rejected(self):
        for path in ('/etc/passwd', '../manifest.json', 'website/data/songs/example/../../catalog.json',
                     'website/data/songs/example/worker.py', 'website/data/songs/another/manifest.json'):
            packet = self.packet()
            packet['files'][path] = {}
            with self.subTest(path=path), self.assertRaises(ValueError):
                module.validate_packet(packet)

    def test_identity_and_required_artifacts(self):
        for section in ('item', 'song'):
            packet = self.packet()
            packet[section]['id'] = 'other'
            with self.assertRaises(ValueError):
                module.validate_packet(packet)
        packet = self.packet()
        del packet['files']['website/data/songs/example/study.json']
        with self.assertRaises(ValueError):
            module.validate_packet(packet)

    def test_packet_is_not_mutated(self):
        packet = self.packet()
        before = copy.deepcopy(packet)
        module.validate_packet(packet)
        self.assertEqual(before, packet)

    def test_invalid_id(self):
        for value in ('../example', 'Example', 'example/test', '', 'first-pulse'):
            packet = self.packet()
            packet['mediaId'] = value
            with self.assertRaises(ValueError):
                module.validate_packet(packet)

    def test_unlist_packet_forbids_replacement_files_and_unknown_operations(self):
        packet = {'operation': 'unlist', 'mediaId': 'example', 'song': {'id': 'example'}}
        self.assertEqual(module.validate_packet(packet), 'example')
        for changes in ({'files': {}}, {'song': {'id': 'other'}}, {'operation': 'delete'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                module.validate_packet({**packet, **changes})

    def test_unlist_changes_only_visibility_and_preserves_original_objects(self):
        item = {'id': 'example', 'manifest': 'data/songs/example/manifest.json', 'title': 'Keep me'}
        catalog = {'items': [item, {'id': 'other'}]}
        manifest = {'id': 'example', 'timeline': [1, 2], 'assets': {'audio': 'same.mp3'},
                    'publication': {'review': 'accepted', 'listed': True}}
        original = copy.deepcopy((catalog, manifest))
        changed, song = module.unlist_metadata(catalog, manifest, 'example')
        self.assertEqual((catalog, manifest), original)
        self.assertEqual(changed['items'][1], catalog['items'][1])
        self.assertEqual(song['assets'], manifest['assets'])
        self.assertEqual(song['timeline'], manifest['timeline'])
        self.assertEqual(song['publication']['review'], 'accepted')
        self.assertFalse(song['publication']['listed'])
        self.assertEqual(changed['items'][0]['visibility'], 'unlisted')
        for invalid in ({'items': [item, item]}, {'items': []},
                        {**catalog, 'defaultMedia': 'example'}):
            with self.assertRaises(ValueError):
                module.unlist_metadata(invalid, manifest, 'example')

    def test_public_unlisting_requires_matching_library_and_detail_404(self):
        missing = urllib.error.HTTPError('https://example.test', 404, 'Not Found', {}, None)
        failed = urllib.error.HTTPError('https://example.test', 503, 'Unavailable', {}, None)
        with patch.object(module, 'public_api', side_effect=[{'items': [{'id': 'first-pulse'}]}, missing]):
            module.verify_public_unlisted('example', ['first-pulse'])
        for responses in ([{'items': [{'id': 'example'}]}],
                          [{'items': [{'id': 'first-pulse'}]}, {'id': 'example'}],
                          [{'items': [{'id': 'first-pulse'}]}, failed]):
            with patch.object(module, 'public_api', side_effect=responses), self.assertRaises((ValueError, urllib.error.HTTPError)):
                module.verify_public_unlisted('example', ['first-pulse'])

    def test_unlisting_acceptance_and_rollback_keep_other_songs_and_old_release(self):
        for failure in (None, 'staged', 'public'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                base, state = root / 'base', root / 'state'
                old = base / 'releases/old'
                song_path = old / 'app/website/data/songs/example/manifest.json'
                song_path.parent.mkdir(parents=True)
                song_path.write_text('{"id":"example","assets":{"audio":"same.mp3"}}')
                catalog_path = old / 'app/website/data/catalog.json'
                catalog_path.write_text(json.dumps({'items': [
                    {'id': 'example', 'manifest': 'data/songs/example/manifest.json'}, {'id': 'other'}]}))
                (old / 'release.json').write_text(json.dumps({'files': {
                    'app/website/data/catalog.json': 'old',
                    'app/website/data/songs/example/manifest.json': 'old'}}))
                before_files = {str(p.relative_to(old)): p.read_bytes() for p in old.rglob('*') if p.is_file()}
                (state / 'deployments').mkdir(parents=True)
                (base / 'current').symlink_to(old)
                unit = root / 'unit'
                original_unit = f'WorkingDirectory={old}/app\nExecStart={old}/runtime/bin/python\n'.encode()
                unit.write_bytes(original_unit)
                packet = {'operation': 'unlist', 'mediaId': 'example', 'song': {'id': 'example'}}
                packet_path = root / 'packet.json'
                packet_path.write_bytes(module.encode(packet))
                before = [{'id': 'first-pulse'}, {'id': 'example'}, {'id': 'other'}]
                after = [before[0], before[2]]
                calls = []

                def command(args):
                    calls.append(list(map(str, args)))
                    if 'is-active' in args:
                        return 'active\n'
                    if 'show' in args:
                        return 'MainPID=100\n'
                    if '-c' in args:
                        return json.dumps([{'id': 'wrong'}] if failure == 'staged' else [before[2]])
                    return ''

                with patch.object(module, 'BASE', base), patch.object(module, 'STATE', state), \
                     patch.object(module, 'UNIT', unit), patch.object(module.os, 'geteuid', return_value=0), \
                     patch.object(module, 'command', side_effect=command), \
                     patch.object(module, 'live_songs', side_effect=[before, after, before]), \
                     patch.object(module, 'wait_healthy'), \
                     patch.object(module, 'verify_route_admission') as admission, \
                     patch.object(module, 'verify_public_unlisted', side_effect=ValueError('Still listed') if failure == 'public' else None), \
                     patch.object(module, 'ingress_hashes', return_value={'config': 'unchanged'}), \
                     patch('sys.argv', ['catalog_add', str(packet_path), '--sha256', module.sha(packet_path.read_bytes()), '--expected-release', str(old)]):
                    if failure:
                        with self.assertRaises((AssertionError, ValueError)):
                            module.main()
                    else:
                        module.main()
                admission.assert_not_called()
                self.assertFalse((state / 'active-deployment').exists())
                self.assertEqual(before_files, {str(p.relative_to(old)): p.read_bytes() for p in old.rglob('*') if p.is_file()})
                restarts = [call for call in calls if 'restart' in call]
                self.assertEqual(restarts, [['systemctl', 'restart', module.SERVICE]] * (0 if failure == 'staged' else 2 if failure else 1))
                if failure:
                    self.assertEqual(unit.read_bytes(), original_unit)
                    self.assertEqual((base / 'current').resolve(), old)
                else:
                    current = (base / 'current').resolve()
                    self.assertNotEqual(current, old)
                    data = json.loads((current / 'app/website/data/songs/example/manifest.json').read_text())
                    self.assertFalse(data['publication']['listed'])
                    self.assertEqual(data['assets'], {'audio': 'same.mp3'})

    def test_declared_caddy_snippet_is_hashed_not_read_as_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'Caddyfile'
            raw = b'(known_proxy) {\n reverse_proxy localhost:1234\n}\nexample.test {\n import known_proxy # reusable snippet\n}\n'
            root.write_bytes(raw)
            self.assertEqual(module.ingress_hashes(root), {str(root): module.sha(raw)})
            self.assertEqual(root.read_bytes(), raw)

    def test_unknown_or_dynamic_caddy_import_remains_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'Caddyfile'
            for target in ('unknown_snippet', '{$SITE}', '/etc/sites/*.caddy', '/etc/../tmp/file', 'known argument'):
                root.write_text(f'(known) {{\n}}\nimport {target}\n')
                with self.subTest(target=target), self.assertRaises(ValueError):
                    module.ingress_hashes(root)

    def test_missing_or_ambiguous_route_rejected(self):
        matcher = {'method': ['GET', 'HEAD'], 'path': ['/api/v1/songs/first-pulse', '/api/v1/songs/example']}
        module.require_route({'routes': [matcher]}, 'example')
        for config in ({}, {'routes': [matcher, matcher]},
                       {'routes': [{**matcher, 'method': ['GET', 'POST']}]},
                       {'routes': [{**matcher, 'path': ['/api/v1/songs/first-pulse']}]}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                module.require_route(config, 'example')

    def test_public_song_must_match_and_be_listed_once(self):
        for song, items in (({'id': 'wrong'}, [{'id': 'example'}]),
                            ({'id': 'example'}, []),
                            ({'id': 'example'}, [{'id': 'example'}] * 2)):
            with patch.object(module, 'public_api', side_effect=[song, {'items': items}]), self.assertRaises(ValueError):
                module.verify_public_song({'id': 'example'})
        with patch.object(module, 'public_api', side_effect=[{'id': 'example'}, {'items': [{'id': 'example'}]}]):
            module.verify_public_song({'id': 'example'})

    def test_success_and_failed_acceptance_restore_only_owned_release(self):
        for failure in (None, 'local', 'public', 'ingress'):
            fail = failure is not None
            with self.subTest(fail=fail), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                base, state = root / 'base', root / 'state'
                old = base / 'releases/old'
                (old / 'app/website/data').mkdir(parents=True)
                (state / 'deployments').mkdir(parents=True)
                (old / 'app/website/data/catalog.json').write_text('{"items": []}')
                (old / 'release.json').write_text('{"files": {"app/website/data/catalog.json": "old"}}')
                (base / 'current').symlink_to(old)
                unit = root / 'unit'
                initial_unit = f'WorkingDirectory={old}/app\nExecStart={old}/runtime/bin/python\n'.encode()
                unit.write_bytes(initial_unit)
                packet = self.packet()
                packet_path = root / 'packet.json'
                packet_path.write_bytes(module.encode(packet))
                digest = module.sha(packet_path.read_bytes())
                before = [{'id': 'first-pulse'}]
                after = before + [packet['song']]
                calls = []

                def command(args):
                    calls.append(list(map(str, args)))
                    if 'is-active' in args:
                        return 'active\n'
                    if 'show' in args:
                        return 'MainPID=100\n'
                    if '-c' in args:
                        return json.dumps([packet['song']])
                    return ''

                states = [before, [{'id': 'wrong'}], before] if failure == 'local' else [before, after, before]
                with patch.object(module, 'BASE', base), patch.object(module, 'STATE', state), \
                     patch.object(module, 'UNIT', unit), patch.object(module.os, 'geteuid', return_value=0), \
                     patch.object(module, 'command', side_effect=command), \
                     patch.object(module, 'live_songs', side_effect=states), \
                     patch.object(module, 'wait_healthy'), \
                     patch.object(module, 'verify_route_admission', side_effect=ValueError('missing route') if failure == 'ingress' else None), \
                     patch.object(module, 'verify_public_song', side_effect=ValueError('public detail 404') if failure == 'public' else None), \
                     patch.object(module, 'ingress_hashes', return_value={'config': 'unchanged'}), \
                     patch('sys.argv', ['catalog_add', str(packet_path), '--sha256', digest, '--expected-release', str(old)]):
                    if fail:
                        with self.assertRaises((AssertionError, ValueError)):
                            module.main()
                    else:
                        module.main()
                self.assertFalse((state / 'active-deployment').exists())
                self.assertEqual(json.loads((old / 'app/website/data/catalog.json').read_text()), {'items': []})
                self.assertFalse(any('caddy' in arg for call in calls for arg in call if arg != 'lazystudio-caddy'))
                restart_calls = [call for call in calls if 'restart' in call]
                self.assertEqual(restart_calls, [['systemctl', 'restart', module.SERVICE]] * (0 if failure == 'ingress' else 2 if fail else 1))
                if fail:
                    self.assertEqual(unit.read_bytes(), initial_unit)
                    self.assertEqual((base / 'current').resolve(), old)
                else:
                    self.assertNotEqual((base / 'current').resolve(), old)


if __name__ == '__main__':
    unittest.main()
