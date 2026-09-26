#!/usr/bin/env python3
"""Browser layout regression; synthetic chord intervals are test fixtures only."""
import argparse
import json
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:18441")
    parser.add_argument("--output", type=Path, default=Path(".runtime/learning/chord-layout"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    shapes = json.loads(Path("apps/shared/guitar-shapes.json").read_text())["shapes"]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=shutil.which("google-chrome"), args=["--disable-dev-shm-usage"])
        page = browser.new_page()
        fixture = page.request.get(args.base_url + "/api/v1/songs/first-pulse").json()
        asset = fixture["assets"][0]
        asset["chords"] = [{"name": s["name"], "start": i * .8, "end": (i+1)*.8} for i, s in enumerate(shapes)]
        fixture["title"] = "Chord rendering fixture (not a score)"
        page.route("**/api/v1/songs/first-pulse", lambda route: route.fulfill(json=fixture))
        page.goto(args.base_url)
        page.wait_for_function("() => document.querySelector('#song-title').textContent.includes('fixture')")
        page.wait_for_function("() => document.querySelector('#audio').readyState >= 1")
        for i, shape in enumerate(shapes):
            page.locator("#audio").evaluate("(audio,t)=>{audio.currentTime=t}", i*.8+.2)
            page.wait_for_function("name=>document.querySelector('#chord-name').textContent===window.Musia.displayChord(name, {capo:0,simplify:true}).guitar", arg=shape["name"])
            board = page.locator("#fretboard")
            assert page.locator(".fret-dot").count() == sum(f > 0 for f in shape["frets"]), shape["name"]
            assert page.locator(".fret-barre").count() == len(shape["barres"])
            assert board.evaluate("e => [...e.querySelectorAll('.fret-dot')].every(d=>{const a=e.getBoundingClientRect(),b=d.getBoundingClientRect();return b.top>=a.top&&b.bottom<=a.bottom})")
        results = []
        for width, height in [(320,740),(390,844),(844,390),(768,1024),(1024,768),(1440,1000)]:
            for scale in [1, 1.5]:
                page.set_viewport_size({"width":width,"height":height})
                # Increase font metrics, including fixed-pixel labels, without scaling touch geometry.
                page.evaluate("scale=>{document.querySelectorAll('body,button,input,select').forEach(e=>e.style.fontSize=17*scale+'px');document.querySelectorAll('.practice-footer>div,.practice-footer .primary-button').forEach(e=>e.style.fontSize=14*scale+'px')}", scale)
                page.locator("#fretboard").scroll_into_view_if_needed()
                page.wait_for_timeout(200)
                overflow = page.evaluate("() => [...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>({tag:e.tagName,id:e.id,cls:e.className,right:e.getBoundingClientRect().right}))")
                page.screenshot(path=str(args.output/f"current-{width}-{scale}.png"))
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (width, scale, overflow)
                footer = page.locator(".practice-footer").bounding_box()
                for selector in ["#floating-play", "#finish"]:
                    button = page.locator(selector).bounding_box()
                    assert button["y"] >= footer["y"] and button["y"]+button["height"] <= height
                page.evaluate("scrollTo(0,document.body.scrollHeight)")
                page.wait_for_timeout(100)
                controls = page.locator(".chord-controls").bounding_box()
                assert controls["y"] + controls["height"] <= footer["y"], (width,scale)
                if scale == 1:
                    page.screenshot(path=str(args.output/f"chord-{width}x{height}.png"))
                results.append({"width":width,"height":height,"textScale":scale})
        catalog = page.evaluate("""async () => {
            const {guitarShape} = await import('/guitar-shapes.js');
            const library = await (await fetch('/api/v1/library')).json();
            const missing = []; const symbols = new Set(); let assets = 0;
            for (const item of library.items) {
                const song = await (await fetch('/api/v1/songs/'+encodeURIComponent(item.id))).json();
                for (const asset of song.assets) {
                    assets++;
                    for (const chord of asset.chords) {
                        symbols.add(chord.name);
                        if (!guitarShape(chord.name)) missing.push({song:item.id,asset:asset.id,chord:chord.name});
                    }
                }
            }
            return {songs:library.items.length,assets,symbols:[...symbols].sort(),missing};
        }""")
        assert not catalog["missing"], catalog["missing"]
        browser.close()
    evidence = {"fixtureOnly":True,"chordsRendered":len(shapes),"layouts":results,"catalog":catalog}
    (args.output/"result.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()
