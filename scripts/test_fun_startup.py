#!/usr/bin/env python3
"""Check random Fun startup, catalog visibility and deterministic shared links."""
import argparse
import shutil
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread

from playwright.sync_api import sync_playwright

from test_catalog_presentation import QuietHandler, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", help="Test the deployed site instead of local files")
    args = parser.parse_args()
    server = None
    if args.origin:
        origin = args.origin.rstrip("/")
    else:
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT / "website")))
        Thread(target=server.serve_forever, daemon=True).start()
        origin = f"http://127.0.0.1:{server.server_port}"
    output = ROOT / ".runtime/random-startup"
    output.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=shutil.which("google-chrome"))
            try:
                page = browser.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                # Reproducible first/last draws exercise boot, not just a helper.
                page.add_init_script("if (location.protocol.startsWith('http')) Math.random = () => Number(sessionStorage.getItem('startup-test-draw') || 0)")

                def ready():
                    page.wait_for_function("state.manifest?.id === state.activeMediaId && !!state.activeAssetId")

                for width, height in [(1440, 1000), (390, 844)]:
                    page.set_viewport_size({"width": width, "height": height})
                    page.goto(origin + "/", wait_until="domcontentloaded")
                    ready()
                    page.evaluate("sessionStorage.setItem('startup-test-draw', '0')")
                    page.reload(wait_until="domcontentloaded")
                    ready()
                    songs = page.evaluate("catalogItems().filter(i=>['song','localized-song'].includes(i.kind)).map(i=>i.id)")
                    assert len(songs) > 1, "Live catalog must contain multiple public songs for this regression"
                    assert page.evaluate("state.activeMediaId") == songs[0]
                    page.evaluate("sessionStorage.setItem('startup-test-draw', '0.999999')")
                    page.reload(wait_until="domcontentloaded")
                    ready()
                    assert page.evaluate("state.activeMediaId") == songs[-1]
                    assert page.evaluate("location.hash === '' && state.mediaElement.paused")
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
                    page.screenshot(path=str(output / f"player-{width}.png"))

                # Test edge cases independently from today's catalog contents.
                checks = page.evaluate("""() => {
                    const saved = [state.catalog, state.showAllMedia, state.hiddenOnlyMedia, state.previewOnlyMedia];
                    const song = {id:'song', kind:'song'};
                    const localized = {id:'localized', kind:'localized-song'};
                    const hidden = {id:'archive', kind:'song', hidden:true};
                    const preview = {id:'preview', kind:'song', visibility:'unlisted'};
                    const mv = {id:'mv', kind:'mv'};
                    try {
                        state.catalog = {defaultMedia:'archive', items:[hidden, preview, mv, song, localized]};
                        state.showAllMedia = state.hiddenOnlyMedia = state.previewOnlyMedia = false;
                        const checks = [initialMediaItem('',()=>0).id === 'song',
                            initialMediaItem('',()=>0.999).id === 'localized',
                            initialMediaItem('archive',()=>0).id === 'archive',
                            initialMediaItem('missing',()=>0).id === 'song'];
                        state.hiddenOnlyMedia = true;
                        checks.push(initialMediaItem('',()=>0).id === 'archive');
                        state.hiddenOnlyMedia = false; state.previewOnlyMedia = true;
                        checks.push(initialMediaItem('',()=>0).id === 'preview');
                        state.previewOnlyMedia = false; state.showAllMedia = true;
                        checks.push(initialMediaItem('',()=>0).id === 'archive');
                        state.showAllMedia = false; state.catalog.items = [mv];
                        checks.push(initialMediaItem('',()=>0).id === 'mv');
                        state.catalog.items = [hidden, preview];
                        checks.push(initialMediaItem('',()=>0) === undefined);
                        state.catalog.items = [];
                        checks.push(initialMediaItem('',()=>0) === undefined);
                        return checks;
                    } finally {
                        [state.catalog, state.showAllMedia, state.hiddenOnlyMedia, state.previewOnlyMedia] = saved;
                    }
                }""")
                assert all(checks), checks
                for path, expected in [
                    ("/#aya-chan-hikari-ame", "aya-chan-hikari-ame"),
                    ("/?media=aya-canada-beyond-the-maples", "aya-canada-beyond-the-maples"),
                    ("/?id=ban-qu-chang-an", "ban-qu-chang-an"),
                    ("/atlas/aya-chan-hikari-ame/", "aya-chan-hikari-ame"),
                ]:
                    page.goto("about:blank")
                    page.goto(origin + path, wait_until="domcontentloaded")
                    ready()
                    assert page.evaluate("state.activeMediaId") == expected, path
                assert not errors, errors
                print("PASS: random desktop/mobile startup, visibility, empty pools, deep links and paused playback")
            finally:
                browser.close()
    finally:
        if server:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
