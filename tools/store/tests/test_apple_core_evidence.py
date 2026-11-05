import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apple_core_evidence import reuse_core


class CoreEvidenceTests(unittest.TestCase):
    def test_exact_source_reuses_pass_but_changes_or_failed_results_do_not(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old = root / 'native-test'; old.mkdir()
            source = root / 'source'
            path = source / 'apps/ios/Test.swift'; path.parent.mkdir(parents=True)
            path.write_text('original')
            pins = {'apps/ios/Test.swift': hashlib.sha256(path.read_bytes()).hexdigest()}
            (old / 'source-pins.json').write_text(json.dumps(pins))
            result = old / 'result.json'
            result.write_text(json.dumps(dict(admission='test', corePassed=True)))
            (old / 'core-tests.json').write_text(json.dumps(dict(exit=0, stdout="Test Suite 'All tests' passed")))
            evidence = dict(admission='test', resultSha256=hashlib.sha256(result.read_bytes()).hexdigest())
            self.assertTrue(reuse_core(evidence, source, root)['reused'])
            path.write_text('changed')
            with self.assertRaisesRegex(RuntimeError, 'source changed'):
                reuse_core(evidence, source, root)
            path.write_text('original')
            (old / 'core-tests.json').write_text(json.dumps(dict(exit=1, stdout='failure')))
            with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                reuse_core(evidence, source, root)
            result.write_text('{}')
            with self.assertRaisesRegex(RuntimeError, 'result changed'):
                reuse_core(evidence, source, root)


if __name__ == '__main__':
    unittest.main()
