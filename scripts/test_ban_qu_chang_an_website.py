#!/usr/bin/env python3
"""Check the selected song's browser playback, ruby, clock and responsive layout.

With --live, tests the deployed website. Otherwise serves the local website on
an ephemeral loopback port. Both use the real published MusiaSongs audio,
including its HTTP range/seek behavior. This is not a musical-accuracy test.
"""

import argparse
import functools
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
MEDIA_ID = "ban-qu-chang-an"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    out = ROOT / "data/creative_projects/aya-chan-ban-qu-chang-an-minimax-20260913/review/website"
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / f"website/data/songs/{MEDIA_ID}/manifest.json").read_text())
    source = manifest["assets"]["primaryAudio"]["src"]
    server = None
    if args.live:
        base = "https://fun.lazying.art/"
    else:
        handler = functools.partial(QuietHandler, directory=str(ROOT / "website"))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_port}/"
    evidence = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True,
                                         args=["--disable-dev-shm-usage", "--autoplay-policy=no-user-gesture-required"])
            try:
                for label, width, height in [("desktop", 1440, 1000), ("mobile", 390, 844)]:
                    context = browser.new_context(viewport={"width": width, "height": height},
                                                  device_scale_factor=1, is_mobile=label == "mobile")
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(base + "#" + MEDIA_ID, wait_until="networkidle", timeout=90000)
                    page.wait_for_function("document.querySelector('#audio')?.readyState >= 2", timeout=90000)
                    page.wait_for_function("document.querySelector('#cover-art')?.naturalWidth > 0")
                    assert page.locator("#media-credit").is_visible()
                    assert "MiniMax-Music3" in page.locator("#media-credit").inner_text()
                    assert page.locator("#audio").evaluate("a => !a.error && a.duration > 158 && a.duration < 159")
                    assert page.locator("#audio").evaluate("a => a.currentSrc") == source
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2")
                    page.locator("#audio").evaluate("async a => {a.muted=true; a.currentTime=0; await a.play();}")
                    page.wait_for_function("document.querySelector('#audio').currentTime > 0.3")
                    page.locator("#audio").evaluate("a => a.pause()")
                    assert page.locator("#lyric-carousel [data-token-start].active").count() == 0
                    states = []
                    for at, expected in [(16.5, "l01"), (53.5, "l07"), (118.5, "l21"), (148.5, "l28")]:
                        page.locator("#audio").evaluate("(a, t) => {a.currentTime=t; a.dispatchEvent(new Event('timeupdate'));}", at)
                        page.wait_for_timeout(300)
                        print(label, at, page.evaluate("({time:document.querySelector('#audio').currentTime, line:document.querySelector('#lyric-carousel .carousel-line.active')?.dataset.lineId, stage:document.querySelector('#stage-line').textContent})"), flush=True)
                        page.wait_for_function("id => document.querySelector('#lyric-carousel .carousel-line.active')?.dataset.lineId === id", arg=expected, timeout=5000)
                        page.wait_for_timeout(200)
                        assert page.locator("#chord-row .chord-pill.active").count() == 1
                        assert page.locator("#lyric-carousel [data-token-start].active").count() > 0
                        assert page.locator("#lyric-carousel ruby rt").count() > 0
                        states.append({"time": at, "line": expected,
                                       "chordIndex": page.locator("#chord-row").get_attribute("data-active-chord-index")})
                    assert len({item["chordIndex"] for item in states}) > 1
                    page.locator("#audio").evaluate("a => {a.currentTime=53.5; a.dispatchEvent(new Event('timeupdate'));}")
                    page.wait_for_timeout(250)
                    page.screenshot(path=str(out / f"{'live' if args.live else 'local'}-{label}.png"))
                    assert not errors, errors
                    evidence.append({"viewport": label, "playback": "passed", "states": states, "errors": errors})
                    context.close()
            finally:
                browser.close()
    finally:
        if server:
            server.shutdown()
            server.server_close()
    path = out / ("live-checks.json" if args.live else "local-checks.json")
    path.write_text(json.dumps(evidence, indent=2) + "\n")
    print(path)


if __name__ == "__main__":
    main()
