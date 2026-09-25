#!/usr/bin/env python3
"""Exercise the real learning service with Chromium; store only review evidence."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:18440")
    parser.add_argument("--output", type=Path, default=Path(".runtime/learning/review"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    evidence = {"baseUrl": args.base_url, "checks": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=shutil.which("google-chrome"),
                                     args=["--disable-dev-shm-usage"])
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(args.base_url, wait_until="domcontentloaded")
        page.wait_for_function("() => document.querySelector('#song-title').textContent === 'First Pulse'")
        assert page.locator("#evidence-label").inner_text() == "Reference exercise"
        page.wait_for_function("() => document.querySelector('#cover').naturalWidth > 0")
        page.locator("#speed").fill("100")
        page.locator("#play").click()
        page.wait_for_function("() => document.querySelector('#audio').currentTime > 4.2")
        assert page.locator("#chord-name").inner_text() == "Em"
        assert page.locator(".beat.active").count() == 1
        assert page.locator(".fret-dot").count() == 2
        assert page.locator(".fret-dot").first.evaluate("e => getComputedStyle(e).left !== 'auto'")
        page.screenshot(path=str(args.output / "desktop-practice.png"))
        evidence["checks"].append("actual exercise playback, beat and Em shape")
        page.locator('[data-mode="tap"]').click()
        for _ in range(5):
            page.locator("#tap").click()
            page.wait_for_timeout(1050)
        assert "Tap spread" in page.locator("#tap-feedback").inner_text()
        page.locator("#clear-taps").click()
        page.locator("#tap").focus()
        page.keyboard.down("Space")
        page.wait_for_timeout(1100)
        page.keyboard.down("Space")
        page.keyboard.up("Space")
        assert page.locator("#tap-feedback").inner_text() == "1 taps"
        page.locator("#tap").dispatch_event("click",{"detail":0})
        assert page.locator("#tap-feedback").inner_text() == "2 taps"
        page.locator("#play").click()
        for speed in (25, 75, 200):
            page.locator("#speed").fill(str(speed))
            assert page.locator("#audio").evaluate("e=>e.playbackRate") == speed / 100
        evidence["checks"].append("rate-aware tap feedback and 25-200% playback")
        page.locator(".phrase").first.click()
        page.locator("#play").click()
        page.wait_for_timeout(2400)
        now = page.locator("#audio").evaluate("e=>e.currentTime")
        assert 4 <= now < 8.2, now
        evidence["checks"].append("bounded phrase replay")
        page.locator("#finish").click()
        assert page.locator(".history-item").count() >= 1
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("() => document.querySelector('#song-title').textContent === 'First Pulse'")
        page.locator('[data-view="progress"]').click()
        assert page.locator(".history-item").count() >= 1
        evidence["checks"].append("local progress survives reload")
        page.locator('[data-view="library"]').click()
        page.locator("#search").fill("hikari")
        assert page.locator(".song-card").count() == 1
        page.locator(".song-card").click()
        page.wait_for_function("() => document.querySelector('#song-title').textContent.includes('Hikari')")
        page.locator("#play").click()
        page.wait_for_function("() => document.querySelector('#audio').currentTime > 1", timeout=45000)
        page.locator("#play").click()
        assert "not a verified score" in page.locator("#evidence-label").inner_text()
        assert page.locator(".beat").count() == 1
        page.locator(".phrase").first.click()
        page.wait_for_timeout(250)
        assert page.locator("#current-lyric").inner_text().strip()
        evidence["checks"].append("live Aya song streams, per-vocal lyrics, conservative analysis label")
        song = page.request.get(args.base_url + "/api/v1/songs/aya-chan-hikari-ame").json()
        english = next(a for a in song["assets"] if a["language"] == "en")
        line = next(line for line in english["lyrics"] if " " in line["text"])
        page.locator("#vocal").select_option(english["id"])
        page.locator(f'[data-phrase="{line["id"]}"]').click()
        page.wait_for_timeout(250)
        assert page.locator("#current-lyric").text_content() == line["text"]
        assert page.locator("#lesson-title").inner_text() != "Hear the Change"
        page.locator("#vocal").select_option(song["defaultAssetId"])
        page.locator(".phrase").first.click()
        evidence["checks"].append("English token rendering preserves original spaces and punctuation")
        for name, width, height in (("desktop",1440,1000),("tablet",768,1024),("mobile",390,844),("small-mobile",320,740)):
            page.set_viewport_size({"width":width,"height":height})
            page.wait_for_timeout(200)
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), name
            page.wait_for_function("() => {const image=document.querySelector('#cover'); return image.complete && image.naturalWidth > 0}")
            page.screenshot(path=str(args.output / f"{name}-aya.png"),full_page=True)
        evidence["checks"].append("no horizontal overflow across 320,390,768,1440px")
        page.locator('[data-view="create"]').click()
        page.locator('[name="title"]').fill("A first song")
        page.locator('[name="idea"]').fill("A quiet and hopeful evening")
        with page.expect_download() as download:
            page.locator('button[type="submit"]').click()
        assert download.value.suggested_filename == "musia-song-brief.json"
        evidence["checks"].append("creative brief exports without generation")
        assert not errors, errors
        evidence["javascriptErrors"] = errors
        browser.close()
    (args.output / "result.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))


if __name__ == "__main__":
    main()
