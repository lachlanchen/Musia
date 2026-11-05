import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apple_internal_delivery import APP, deliver
from storelib import GuardError


class InternalDeliveryTests(unittest.TestCase):
    def test_processing_requests_build_linkage_without_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            manifest = dict(platform='IOS', version='0.2.2', build='12', artifact={'sha256': 'fixture'})
            operations = root / 'operations'; operations.mkdir(mode=0o700)
            journal = operations / 'apple-build-upload-IOS-fixture.json'
            journal.write_text(json.dumps(dict(manifest=manifest, fileId='file', buildUploadId='upload')))
            journal.chmod(0o600)
            api = Mock(); api.app.return_value = {'id': APP}
            reservation = dict(attributes=dict(cfBundleVersion='12', cfBundleShortVersionString='0.2.2',
                platform='IOS', state={'state': 'PROCESSING'}), id='upload')
            responses = {
                '/v1/buildUploads/upload?include=build': {'data': reservation},
                '/v1/buildUploadFiles/file': {'data': {'id': 'file', 'attributes': {'assetDeliveryState': {'state': 'COMPLETE'}}}},
            }
            api.request.side_effect = lambda method, path: responses[path] if method == 'GET' else self.fail('Unexpected mutation')
            api.rows.return_value = [{'id': 'file'}]
            with patch('apple_internal_delivery.qualify', return_value=manifest), \
                 patch('apple_internal_delivery.s.RUNTIME', root), \
                 patch('apple_internal_delivery.s.Apple', return_value=api), \
                 patch('apple_internal_delivery.s.apple_platform_builds', return_value=[]):
                result = deliver(root / 'manifest.json', confirm=True)
                self.assertFalse(result['available'])
                self.assertEqual(result['state'], 'processing_or_reconciliation_required')
                api.request.assert_any_call('GET', '/v1/buildUploads/upload?include=build')
                self.assertTrue(all(call.args[0] == 'GET' for call in api.request.call_args_list))
                reservation['attributes']['platform'] = 'MAC_OS'
                with self.assertRaisesRegex(GuardError, 'identity mismatch'):
                    deliver(root / 'manifest.json', confirm=True)


if __name__ == '__main__':
    unittest.main()
