"""Find an explicitly retained browser tab without relying on page ordering."""
from storelib import require


def retained_page(browser, target_id):
    require(isinstance(target_id, str) and bool(target_id), "Missing owned tab ID")
    for context in browser.contexts:
        for page in context.pages:
            session = context.new_cdp_session(page)
            try:
                observed = session.send("Target.getTargetInfo")["targetInfo"]["targetId"]
            finally:
                session.detach()
            if observed == target_id:
                return page
    require(False, "Retained tab is absent; inspect before opening or changing another tab")
