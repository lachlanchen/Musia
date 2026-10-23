from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest

from musia.creator.store import Store
from musia.creator.supervisor import Config, _Journal, daemon_lock
from tools.renew_creator_polling import renew


class PollRenewalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        Store(self.root)
        self.config = Config(run_id='old', enabled=True, dispatch=True, max_per_run=10, max_dispatches=10, max_passes=1)
        self.path = self.root / 'queue.json'
        self.path.write_text(json.dumps(asdict(self.config)))
        self.path.chmod(0o600)
        journal = _Journal(self.root, self.config)
        journal.next_pass()
        action = journal.reserve('dispatch')
        journal.finish(action, 'worker_completed', {})
        journal.db.close()

    def test_carries_only_unused_budget_and_keeps_review_manual(self):
        dry = renew(self.root, self.path, 'new')
        self.assertFalse(dry['applied'])
        self.assertEqual(json.loads(self.path.read_text())['run_id'], 'old')
        result = renew(self.root, self.path, 'new', apply=True)
        self.assertEqual(result['next']['max_dispatches'], 9)
        self.assertEqual(result['next']['max_per_run'], 9)
        self.assertFalse(result['next']['review_inputs'])
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        with self.assertRaises(ValueError): renew(self.root, self.path, 'another')

    def test_never_takes_active_daemon(self):
        with daemon_lock(self.root), self.assertRaises(BlockingIOError):
            renew(self.root, self.path, 'new', apply=True)

    def test_unresolved_dispatch_blocks(self):
        journal = _Journal(self.root, self.config)
        journal.reserve('dispatch'); journal.db.close()
        with self.assertRaisesRegex(ValueError, 'unresolved'): renew(self.root, self.path, 'new')

    def test_config_changes_cannot_refill_budget(self):
        value = asdict(self.config); value['max_dispatches'] = 100
        self.path.write_text(json.dumps(value))
        with self.assertRaises(ValueError): renew(self.root, self.path, 'new')
