#!/usr/bin/env python3
"""Bounded real-provider chat check in Musia's owned browser; never renders."""
import argparse
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--confirm-provider-calls", action="store_true")
    args = parser.parse_args()
    if not args.confirm_provider_calls:
        parser.error("Two real text-model requests require --confirm-provider-calls")
    os.umask(0o077)
    fixture = json.loads(args.fixture.read_text())
    args.evidence.mkdir(parents=True, exist_ok=False)
    report = {"renderDispatched": False, "providerRequests": 0}
    origin = "https://musia.lazying.art"
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9453")
        context = browser.contexts[0]
        me = context.request.get(origin + "/creator/api/me")
        assert me.status == 200 and me.json()["account"]["name"] == fixture["username"], "Wrong QA session"
        jobs = context.request.get(origin + "/creator/api/jobs").json()
        page = context.new_page()
        saved = None
        errors = []
        try:
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(origin + "/creator/")
            page.locator("#send").wait_for()
            page.locator("#account-name").get_by_text(fixture["username"], exact=True).wait_for()
            saved = page.evaluate("Object.fromEntries(Object.entries(localStorage))")
            assert page.locator("#agent-panel").is_visible()
            page.locator("#studio-tab").click()
            page.locator('[name="title"]').fill("A Window of Morning")
            page.locator("#agent-tab").click()
            for prompt in [
                "Keep the title from Studio. Write four original English lyric lines for a gentle hopeful acoustic song. Leave room between phrases. Only prepare the draft; do not render.",
                "Keep that title and the first two lines. Make the last two lines more hopeful, and set the tempo to 80 BPM. Only update the draft."
            ]:
                page.locator("#message").fill(prompt)
                with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith("/api/agent"), timeout=150000) as pending:
                    page.locator("#send").click()
                response = pending.value
                assert response.status == 200, f"Agent HTTP {response.status}"
                request = response.request.post_data_json
                report["providerRequests"] += 1
                if report["providerRequests"] == 2:
                    assert len(request.get("history", [])) >= 2
                assert response.json()["brief"]["title"] == "A Window of Morning"
                page.wait_for_function("document.querySelector('#chat-status').textContent === 'Private draft'")
            page.locator("#studio-tab").click()
            assert page.locator('[name="title"]').input_value() == "A Window of Morning"
            assert int(page.locator('[name="bpm"]').input_value()) == 80
            assert page.locator('[name="lyrics"]').input_value().strip()
            page.screenshot(path=str(args.evidence / "studio.png"), full_page=True)
            page.reload()
            page.locator("#messages").get_by_text("Only update the draft.", exact=False).wait_for()
            assert page.locator("#agent-panel").is_visible()
            page.screenshot(path=str(args.evidence / "agent-restored.png"), full_page=True)
            assert context.request.get(origin + "/creator/api/jobs").json() == jobs, "Job state changed; reconcile"
            assert not errors, "Browser errors; inspect protected evidence"
            report.update(state="passed", historySent=True, studioUpdated=True, reloadRestored=True)
        finally:
            if saved is not None:
                page.evaluate("saved => {localStorage.clear(); for(const [k,v] of Object.entries(saved)) localStorage.setItem(k,v)}", saved)
            page.close()
            (args.evidence / "result.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))


if __name__ == "__main__":
    main()
