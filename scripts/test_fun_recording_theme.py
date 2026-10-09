#!/usr/bin/env python3
"""Check coral/sky player colors and the existing 4K publication layout."""

import argparse
from functools import partial
from http.server import ThreadingHTTPServer
import json
import re
import shutil
from threading import Thread

from playwright.sync_api import sync_playwright

from test_catalog_presentation import QuietHandler, ROOT


def contrast(first, second):
    def luminance(color):
        values = [int(v) / 255 for v in re.findall(r"\d+", color)[:3]]
        assert len(values) == 3, color
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
        return sum(v * weight for v, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    low, high = sorted((luminance(first), luminance(second)))
    return (high + 0.05) / (low + 0.05)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", help="Use the deployed website instead of local files")
    args = parser.parse_args()
    media_id = "aya-canada-beyond-the-maples"
    lines = json.loads((ROOT / f"website/data/songs/{media_id}/lyrics/ja-vocal/ja.json").read_text())["lines"]
    points = []
    for index in (0, len(lines) // 3, 2 * len(lines) // 3):
        line = lines[index]
        token = line["tokens"][len(line["tokens"]) // 2]
        points.append(((token["start"] + token["end"]) / 2, line["id"]))
    output = ROOT / ".runtime/fun-recording-theme"
    output.mkdir(parents=True, exist_ok=True)
    server = None
    if args.origin:
        origin = args.origin.rstrip("/")
    else:
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT / "website")))
        Thread(target=server.serve_forever, daemon=True).start()
        origin = f"http://127.0.0.1:{server.server_port}"
    evidence = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, executable_path=shutil.which("google-chrome"))
            try:
                for label, width, height, scale in (("desktop", 1440, 1000, 1), ("mobile", 390, 844, 1),
                                                    ("portrait-4k", 1080, 1920, 2)):
                    context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=scale)
                    try:
                        page = context.new_page()
                        errors = []
                        page.on("pageerror", lambda error: errors.append(str(error)))
                        query = "?advanced=1"
                        if scale == 2:
                            query += "&capture=1&portrait=1&multiLyrics=1&lyricsGuitar=1&publication=1"
                        page.goto(f"{origin}/{query}#{media_id}", wait_until="domcontentloaded")
                        page.wait_for_function("state.tracks.length >= 3 && state.manifest?.id === 'aya-canada-beyond-the-maples'")
                        page.wait_for_function("document.querySelector('#cover-art').naturalWidth > 0")
                        page.evaluate("document.fonts.ready")
                        states = []
                        for at, line_id in points:
                            page.evaluate("t => window.funPlayerSetTime(t)", at)
                            page.wait_for_function("id => document.querySelector('.carousel-line.active')?.dataset.lineId === id", arg=line_id)
                            page.wait_for_timeout(450)
                            assert page.locator("#lyric-carousel .text-token.active").count() > 0
                            assert page.locator("#chord-row .chord-pill.active").count() == 1
                            assert page.locator(".advanced-panel .guitar-marker").count() > 0
                            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2")
                            colors = page.evaluate("""() => {
                                const styles = selector => {
                                    const s = getComputedStyle(document.querySelector(selector));
                                    return {fg:s.color, bg:s.backgroundColor, image:s.backgroundImage};
                                };
                                return {play:styles('.play-button'), chord:styles('.chord-pill.active'),
                                    marker:styles('.guitar-marker'), panel:styles('.advanced-panel'),
                                    progress:styles('.progress-fill'), rail:styles('#seek'),
                                    word:styles('#lyric-carousel .text-token.active')};
                            }""")
                            assert colors["marker"]["bg"] == colors["chord"]["bg"] == "rgb(245, 111, 112)", colors
                            assert colors["panel"]["bg"] == "rgb(239, 249, 255)", colors
                            assert colors["rail"]["bg"] == "rgb(184, 230, 250)", colors
                            assert "245, 111, 112" in colors["progress"]["image"], colors
                            for key in ("play", "chord", "marker"):
                                assert contrast(colors[key]["fg"], colors[key]["bg"]) >= 4.5, (key, colors[key])
                            assert contrast(colors["word"]["fg"], "rgb(255, 255, 255)") >= 4.5
                            if scale == 2:
                                bounds = page.evaluate("""() => {
                                    const box = s => { const r=document.querySelector(s).getBoundingClientRect();
                                        return {top:r.top,bottom:r.bottom,left:r.left,right:r.right}; };
                                    return {player:box('.player-card'), lyrics:box('#lyric-carousel'),
                                        chords:box('#chord-row'), guitar:box('.advanced-panel')};
                                }""")
                                assert bounds["player"]["bottom"] <= bounds["lyrics"]["top"] + 1, bounds
                                assert bounds["lyrics"]["bottom"] <= bounds["chords"]["top"] + 1, bounds
                                assert bounds["chords"]["bottom"] <= bounds["guitar"]["top"] + 1, bounds
                                assert bounds["guitar"]["bottom"] <= height, bounds
                            states.append({"time":at, "line":line_id,
                                           "chord":page.locator('#chord-row').get_attribute('data-active-chord-index'),
                                           "progress":page.locator('#progress-fill').get_attribute('style')})
                        assert len({s["chord"] for s in states}) > 1, states
                        assert len({s["progress"] for s in states}) > 1, states
                        prefix = "live" if args.origin else "local"
                        page.screenshot(path=str(output / f"{prefix}-{label}.png"))
                        assert not errors, errors
                        evidence.append({"view":label, "pixels":[width * scale, height * scale], "states":states, "colors":colors})
                    finally:
                        context.close()
            finally:
                browser.close()
    finally:
        if server:
            server.shutdown()
            server.server_close()
    (output / ("live.json" if args.origin else "local.json")).write_text(json.dumps(evidence, indent=2) + "\n")
    print("PASS: coral/sky colors, contrast, timed states, desktop/mobile and native 4K publication layout")


if __name__ == "__main__":
    main()
