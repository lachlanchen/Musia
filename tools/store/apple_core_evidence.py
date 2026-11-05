"""Carry completed Darwin core tests only for the identical native source tree."""
import hashlib
import json
from pathlib import Path


def reuse_core(evidence, source, runtime_root):
    root = Path(runtime_root) / ('native-' + evidence['admission'])
    if root.is_symlink() or root.parent != Path(runtime_root):
        raise RuntimeError('Invalid prior native operation')
    result_path = root / 'result.json'
    if hashlib.sha256(result_path.read_bytes()).hexdigest() != evidence['resultSha256']:
        raise RuntimeError('Prior native result changed')
    result = json.loads(result_path.read_text())
    if result.get('admission') != evidence['admission'] or not result.get('corePassed'):
        raise RuntimeError('Prior core tests did not pass')
    prior = json.loads((root / 'source-pins.json').read_text())
    expected = {n: h for n, h in prior.items() if n.startswith('apps/ios/')}
    actual = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (Path(source) / 'apps/ios').rglob('*') if p.is_file()}
    if not expected or actual != expected:
        raise RuntimeError('Native source changed; core evidence is not reusable')
    tests_path = root / 'core-tests.json'
    tests = json.loads(tests_path.read_text())
    if tests.get('exit') != 0 or "Test Suite 'All tests' passed" not in tests.get('stdout', ''):
        raise RuntimeError('Prior core test receipt is incomplete')
    return dict(admission=evidence['admission'], resultSha256=evidence['resultSha256'],
                coreReceiptSha256=hashlib.sha256(tests_path.read_bytes()).hexdigest(),
                sourceFiles=len(expected), reused=True)
