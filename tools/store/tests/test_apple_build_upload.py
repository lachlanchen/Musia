import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apple_build_upload import BuildAPI, upload_parts
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


if __name__ == '__main__':
    unittest.main()
