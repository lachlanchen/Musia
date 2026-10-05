#!/usr/bin/env python3
"""Browser regression for bilingual catalog names and archived takes."""
import argparse
import shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", help="Test a deployed Fun site instead of local files")
    args = parser.parse_args()
    server = None
    if args.origin:
        origin = args.origin.rstrip("/")
    else:
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT / "website")))
        Thread(target=server.serve_forever, daemon=True).start()
        origin = f"http://127.0.0.1:{server.server_port}"
    output = ROOT / ".runtime/catalog-presentation"
    output.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=shutil.which("google-chrome"))
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                errors = []
                page.on("pageerror", lambda err: errors.append(str(err)))
                for width, height in [(1440, 1000), (390, 844)]:
                    page.set_viewport_size({"width": width, "height": height})
                    page.goto(origin + "/#ban-qu-chang-an-ace-changfeng", wait_until="domcontentloaded")
                    page.wait_for_function("document.querySelector('#media-title').textContent === \"半曲长安 · The Melody I Left in Chang'an\"")
                    assert "ban-qu-chang-an" not in page.evaluate("catalogItems().map(i=>i.id)")
                    page.screenshot(path=str(output / f"player-{width}.png"))
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), page.evaluate("Array.from(document.querySelectorAll('main,.hero-grid,.player-card,.title-row,.topbar,.lyrics-card')).map(e=>({class:e.className,width:e.getBoundingClientRect().width,right:e.getBoundingClientRect().right,viewport:innerWidth}))")
                    title = page.locator("#media-title").bounding_box()
                    assert title and title["x"] >= 0 and title["x"] + title["width"] <= width + 1
                    page.screenshot(path=str(output / f"player-{width}.png"))
                page.goto(origin + "/?hidden#ban-qu-chang-an", wait_until="domcontentloaded")
                page.wait_for_function("document.querySelector('#media-title').textContent.endsWith('Archive 01')")
                assert page.evaluate("catalogItems().every(i=>i.hidden)")
                page.goto(origin + "/#luoshenfu-original-excerpt-preview", wait_until="domcontentloaded")
                page.wait_for_function("state.activeMediaId === 'luoshenfu-original-excerpt-preview' && state.manifest?.id === state.activeMediaId")
                assert page.evaluate("playableAssets(state.manifest).filter(a=>a.type==='audio').length") == 1
                page.goto(origin + "/?showall#luoshenfu-original-excerpt-preview", wait_until="domcontentloaded")
                page.wait_for_function("state.manifest?.id === 'luoshenfu-original-excerpt-preview'")
                assert page.evaluate("playableAssets(state.manifest).filter(a=>a.type==='audio').length") == 2
                page.goto(origin + "/#aya-chan-hikari-ame", wait_until="domcontentloaded")
                page.wait_for_function("state.manifest?.id === 'aya-chan-hikari-ame'")
                before = page.locator("#media-title").inner_text()
                page.select_option("#vocal-language-select", "aya-hikari-ame-en")
                assert page.locator("#media-title").inner_text() == before
                assert page.evaluate("playableAssets(state.manifest).filter(a=>a.type==='audio').length") == 3
                assert not errors, errors
                print("PASS: desktop/mobile titles, archive list, same-language take hiding, multilingual title stability")
            finally:
                browser.close()
    finally:
        if server:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
