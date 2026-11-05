import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import play_commit_recovery as recovery
import play_internal_api as p
import storelib as s
import test_play_internal_api as fixtures


class RecoveryTests(unittest.TestCase):
    setUp = fixtures.PlayInternalTests.setUp

    def pending(self):
        self.provider.fail_action = "commit"
        with self.assertRaises(s.GuardError):
            p.run(self.build_path, self.qa_path, execute=True, service_account_file=self.key,
                  coordination_file=self.handoff)
        self.provider.fail_action = None
        self.posts = []
        self.answer = fixtures.Response({"id": "edit-1"})
        def post(url, **kwargs):
            record = s.read_json(p.operation_path("7"))
            self.assertEqual(record["commit_recovery"][-1]["state"], "intent")
            self.posts.append(url)
            self.assertFalse(kwargs["allow_redirects"])
            self.assertIn("ERROR_IF_IN_REVIEW", url)
            return self.answer
        self.provider.post = post

    def recover(self, omit=False):
        return recovery.recover(p.operation_path("7"), self.build_path, self.qa_path,
                                self.key, self.handoff, omit_hold=omit)

    def test_only_existing_edit_committed_no_new_upload(self):
        self.pending()
        before = len(self.provider.calls)
        self.assertEqual(self.recover()["state"], "accepted")
        self.assertTrue(all(method == "GET" for method, _, _ in self.provider.calls[before:]))
        self.assertEqual(len(self.posts), 1)
        with self.assertRaises(s.GuardError): self.recover()
        self.assertEqual(len(self.posts), 1)

    def test_hold_removal_requires_exact_rejection(self):
        self.pending()
        with self.assertRaises(s.GuardError): self.recover(True)
        self.answer = fixtures.Response({"error": {"message":
            "Changes are sent for review automatically. The query parameter changesNotSentForReview must not be set."}}, 400)
        self.assertEqual(self.recover()["state"], "rejected")
        self.answer = fixtures.Response({"id": "edit-1"})
        self.assertEqual(self.recover(True)["state"], "accepted")
        self.assertNotIn("changesNotSentForReview", self.posts[-1])
        with self.assertRaises(s.GuardError): self.recover(True)

    def test_other_rejection_cannot_change_flags(self):
        self.pending()
        self.answer = fixtures.Response({"error": {"message": "Other failure"}}, 400)
        self.recover()
        with self.assertRaises(s.GuardError): self.recover(True)

    def test_closed_edit_cannot_commit(self):
        self.pending()
        self.provider.edits.clear()
        with self.assertRaises(s.GuardError): self.recover()
        self.assertFalse(self.posts)

    def test_changed_production_refuses_commit(self):
        self.pending()
        self.provider.edits["edit-1"]["tracks"]["tracks"][1]["releases"][0]["status"] = "halted"
        with self.assertRaises(s.GuardError): self.recover()
        self.assertFalse(self.posts)


if __name__ == "__main__": unittest.main()
