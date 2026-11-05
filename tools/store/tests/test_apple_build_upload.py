import datetime as dt
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apple_build_upload import BuildAPI, upload_parts, qualify_cleanup
from storelib import GuardError


class UploadPartsTests(unittest.TestCase):
    def test_unknown_mutation_keeps_intent_and_cannot_repeat(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            journal = root / 'journal.json'
            journal.write_text(json.dumps({'steps': {}})); journal.chmod(0o600)
            key = root / 'key.p8'; key.write_text('synthetic'); key.chmod(0o600)
            api = BuildAPI.__new__(BuildAPI)
            api.journal = journal
            api.cfg = {'asc_key_path': str(key), 'asc_issuer': 'fixture', 'asc_key_id': 'fixture'}
            api.session = Mock()
            api.session.request.side_effect = requests.Timeout()
            with patch('apple_build_upload.jwt.encode', return_value='synthetic'):
                with self.assertRaisesRegex(GuardError, 'unknown'):
                    api.mutate('POST', '/v1/buildUploads', {'data': {}}, 'reserve')
                self.assertEqual(json.loads(journal.read_text())['steps']['reserve']['state'], 'started')
                with self.assertRaisesRegex(GuardError, 'already'):
                    api.mutate('POST', '/v1/buildUploads', {'data': {}}, 'reserve')
                with self.assertRaisesRegex(GuardError, 'Only binary'):
                    api.mutate('POST', '/v1/appStoreVersionSubmissions', {}, 'review')
            self.assertEqual(api.session.request.call_count, 1)

    def test_exact_ranges_and_destination(self):
        now = dt.datetime.now(dt.timezone.utc)
        part = dict(method='PUT', url='https://northamerica-1.object-storage.apple.com/example',
                    offset=0, length=5, expiration=(now + dt.timedelta(minutes=2)).isoformat(), requestHeaders=[])
        self.assertEqual(upload_parts([part], 5, now), [part])
        for key, value in [('url', 'https://example.com/file'), ('method', 'POST'), ('offset', 1),
                           ('length', 6), ('length', 0), ('expiration', (now-dt.timedelta(seconds=1)).isoformat()),
                           ('requestHeaders', [{'name': 'Authorization', 'value': 'secret'}])]:
            with self.subTest(key=key), self.assertRaises(GuardError):
                upload_parts([{**part, key: value}], 5, now)


class CleanupQualificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'recovery.json'
        self.native = dict(state='native_passed_pending_visual_review_and_provider_upload',
            admission='operation', guardReleased=False, ended='2026-11-05T07:00:00+00:00',
            cleanupError='RuntimeError: Unexplained native processes; retain guard without signals')
        self.manifest = dict(source='commit', native_result={'sha256': 'native-hash'}, artifact={'sha256': 'binary-hash'})
        self.recovery = dict(passed=True, admission='operation', source='commit', nativeResultSha256='native-hash',
            artifactSha256='binary-hash', readOnly=False, guardReleased=True, guardAbsent=True,
            preservationVerified=True, ownedChildrenAbsent=True, ended='2026-11-05T07:02:00+00:00',
            processReconciliation=dict(passed=True, recordedChildrenComplete=True, liveOwned=[], unexplainedProcesses=[]))
        self.handback = {**copy.deepcopy(self.recovery), 'readOnly': True, 'started': '2026-11-05T07:03:00+00:00'}
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.recovery)); self.path.chmod(0o600)
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.manifest['cleanup_recovery'] = dict(path=str(self.path), sha256=digest)
        self.handback['recoverySha256'] = digest

    def test_separate_recovery_preserves_original_native_receipt(self):
        before = copy.deepcopy(self.native)
        qualify_cleanup(self.manifest, self.native, self.handback)
        self.assertEqual(self.native, before)

    def test_original_success_path_still_works(self):
        del self.manifest['cleanup_recovery']
        self.native.update(guardReleased=True, preservationVerified=True, cleanupError=None)
        qualify_cleanup(self.manifest, self.native, self.handback)

    def test_failed_native_cannot_be_recovered_as_success(self):
        for delta in ({'error': 'build failed'}, {'state': 'failed'}, {'cleanupError': 'unknown'}, {'guardReleased': True}):
            with self.subTest(delta=delta), self.assertRaises(GuardError):
                qualify_cleanup(self.manifest, {**self.native, **delta}, self.handback)

    def test_recovery_requires_both_exact_bound_verified_proofs(self):
        changes = [('passed', False), ('guardReleased', False), ('guardAbsent', False),
                   ('preservationVerified', False), ('ownedChildrenAbsent', False), ('error', 'unfinished'),
                   ('admission', 'another'), ('source', 'other'), ('nativeResultSha256', 'different'),
                   ('artifactSha256', 'different')]
        for field, value in changes:
            with self.subTest(field=field, proof='independent'), self.assertRaises(GuardError):
                qualify_cleanup(self.manifest, self.native, {**self.handback, field: value})
            original = self.recovery[field] if field in self.recovery else None
            self.recovery[field] = value; self.save()
            with self.subTest(field=field, proof='release'), self.assertRaises(GuardError):
                qualify_cleanup(self.manifest, self.native, self.handback)
            if original is None: self.recovery.pop(field)
            else: self.recovery[field] = original
            self.save()

    def test_changed_receipt_or_early_nonindependent_proof_is_rejected(self):
        for delta in ({'recoverySha256': 'different'}, {'readOnly': False},
                      {'started': '2026-11-05T07:01:00+00:00'}, {'started': '2026-11-05T07:03:00'}):
            with self.subTest(delta=delta), self.assertRaises(GuardError):
                qualify_cleanup(self.manifest, self.native, {**self.handback, **delta})
        self.path.write_text('{}')
        with self.assertRaisesRegex(GuardError, 'Changed cleanup'):
            qualify_cleanup(self.manifest, self.native, self.handback)

    def test_unexplained_or_live_children_refuse(self):
        for delta in ({'passed': False}, {'recordedChildrenComplete': False},
                      {'liveOwned': [{'pid': 2}]}, {'unexplainedProcesses': [{'pid': 3}]}):
            handback = copy.deepcopy(self.handback)
            handback['processReconciliation'].update(delta)
            with self.subTest(delta=delta), self.assertRaises(GuardError):
                qualify_cleanup(self.manifest, self.native, handback)


if __name__ == '__main__':
    unittest.main()
