from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from browser_ui import retained_page
from storelib import GuardError


class RetainedPageTests(unittest.TestCase):
    def browser(self, ids):
        pages = [object() for _ in ids]
        sessions = []
        for target_id in ids:
            session = Mock()
            session.send.return_value = {"targetInfo": {"targetId": target_id}}
            sessions.append(session)
        context = SimpleNamespace(pages=pages, new_cdp_session=Mock(side_effect=sessions))
        return SimpleNamespace(contexts=[context]), pages, sessions

    def test_selects_exact_target_independent_of_order(self):
        for ids in (("shared", "owned"), ("owned", "shared")):
            browser, pages, sessions = self.browser(ids)
            self.assertIs(retained_page(browser, "owned"), pages[ids.index("owned")])
            for session in sessions[:ids.index("owned") + 1]:
                session.send.assert_called_once_with("Target.getTargetInfo")
                session.detach.assert_called_once()

    def test_missing_target_fails_without_selecting_another_page(self):
        browser, _, sessions = self.browser(("other-project",))
        with self.assertRaisesRegex(GuardError, "Retained tab is absent"):
            retained_page(browser, "owned")
        sessions[0].detach.assert_called_once()

    def test_missing_id_does_not_open_a_session(self):
        browser, _, _ = self.browser(("shared",))
        for target_id in (None, "", 123):
            with self.assertRaisesRegex(GuardError, "Missing owned tab ID"):
                retained_page(browser, target_id)
        browser.contexts[0].new_cdp_session.assert_not_called()

    def test_failed_read_detaches_without_falling_back(self):
        browser, _, sessions = self.browser(("shared", "owned"))
        sessions[0].send.side_effect = RuntimeError("target closed")
        with self.assertRaisesRegex(RuntimeError, "target closed"):
            retained_page(browser, "owned")
        sessions[0].detach.assert_called_once()
        sessions[1].send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
