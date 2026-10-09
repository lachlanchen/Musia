#!/usr/bin/env python3
"""Browser layout/interaction checks against the loopback preview, with fake identity only in browser routes."""

import argparse
import asyncio
import io
import json
from pathlib import Path
import wave

from playwright.async_api import async_playwright


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default="http://127.0.0.1:8796")
    parser.add_argument("--evidence", type=Path, default=Path("store/.runtime/creator-ui"))
    parser.add_argument("--chromium", help="Existing compatible Chrome/Chromium executable; do not duplicate browser installs")
    args = parser.parse_args()
    if args.origin != "http://127.0.0.1:8796":
        raise ValueError("This fixture check is restricted to the local creator preview")
    args.evidence.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=args.chromium)
        try:
            page = await browser.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            for width, height in ((1440,1000),(768,1024),(390,844),(320,740)):
                await page.set_viewport_size({"width":width,"height":height})
                await page.goto(args.origin+"/creator/")
                await page.get_by_text("Creator preview · service not connected",exact=True).wait_for()
                assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Overflow at {width}"
                assert await page.locator("#generate").is_disabled()
                assert await page.locator("#agent-panel").is_visible()
                await page.locator("#studio-tab").click()
                await page.locator('[name="title"]').fill("A gentle morning")
                await page.reload()
                assert await page.locator("#agent-panel").is_visible()
                assert await page.locator('[name="title"]').input_value() == "A gentle morning"
                await page.screenshot(path=str(args.evidence/f"creator-{width}.png"),full_page=True)
                await page.locator("#plans-button").click()
                assert await page.locator("#plans-dialog").is_visible()
                assert await page.locator(".plan-row").count() == 3
                assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                await page.locator('[data-close="plans-dialog"]').click()
                await page.locator('[data-tab="public"]').click()
                await page.get_by_text("No community songs have been published yet.").wait_for()
            # Simulate identity/agent only at Playwright network boundary, never the server.
            requests = []
            agent_requests = []
            track = {"id":"a"*32,"title":"Playback fixture","author":{"id":"fixture-owner","name":"UI fixture"},
                     "language":"en","mine":True,"visibility":"public","moderation":"approved",
                     "liked":False,"saved":False,"likes":0,"lyrics":"A gentle morning",
                     "sharePath":"/creator/?song="+"a"*32,"audioUrl":"/creator/api/songs/"+"a"*32+"/audio"}
            audio_bytes = io.BytesIO()
            with wave.open(audio_bytes, "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(8000)
                audio.writeframes(b"\x00\x00" * 8000 * 5)
            async def route(handle):
                path = handle.request.url.split("/creator",1)[1]
                if path == "/api/capabilities":
                    value = {"login":True,"providers":{"password":True},"generation":True,"agent":True,
                             "invitationRequired":True,"plans":[],"salesEnabled":False}
                elif path == "/api/me":
                    value = {"account":{"id":"fixture-owner","name":"UI fixture","termsAccepted":True,"invited":True,
                                        "usage":{"remaining":2,"limit":2,"period":"fixture","tier":"free"}}}
                elif path == "/api/jobs":
                    if handle.request.method == "POST":
                        requests.append(handle.request.post_data_json)
                        value={"id":"fixture-job","state":"queued"}
                    else:
                        value={"jobs":[]}
                elif path == "/api/agent":
                    agent_requests.append(handle.request.post_data_json)
                    await asyncio.sleep(0.3)
                    value={"message":"A soft chorus with room to breathe.","brief":{"title":"A gentle morning","lyrics":"[Verse]\nA gentle morning\n[Chorus]\nStay with me",
                           "caption":"Warm piano, clear vocal, hopeful chorus","idea":"Warmth","language":"en","duration":90,"bpm":100,"key":"C major"}}
                elif path.startswith("/api/songs?mode="):
                    value={"songs":[track]}
                elif path == "/api/songs/"+track["id"]:
                    value=track
                elif path == "/api/songs/"+track["id"]+"/audio":
                    return await handle.fulfill(body=audio_bytes.getvalue(),content_type="audio/wav")
                elif path == "/api/songs/"+track["id"]+"/comments":
                    value={"comments":[]}
                elif path == "/api/songs/"+track["id"]+"/reactions/like":
                    track["liked"] = handle.request.post_data_json["active"]
                    track["likes"] = int(track["liked"])
                    value={"ok":True}
                else:
                    return await handle.continue_()
                await handle.fulfill(json=value)
            await page.route("**/creator/api/**",route)
            await page.set_viewport_size({"width":1440,"height":1000})
            await page.goto(args.origin+"/creator/")
            await page.locator("#message").fill("A warm song with a gentle chorus")
            await page.locator("#send").click()
            await page.get_by_text("A soft chorus with room to breathe.",exact=True).wait_for()
            assert await page.locator('[name="lyrics"]').input_value() == "[Verse]\nA gentle morning\n[Chorus]\nStay with me"
            assert requests == [], "Agent must not generate without confirmation"
            await page.locator("#studio-tab").click()
            await page.locator('[name="title"]').fill("My manual title")
            await page.locator("#agent-tab").click()
            await page.locator("#message").fill("Keep the title and soften the chorus")
            await page.locator("#send").click()
            await page.locator("#studio-tab").click()
            await page.locator('[name="title"]').fill("Edited while thinking")
            await page.get_by_text("Your Studio edits were kept.",exact=True).wait_for()
            assert await page.locator('[name="title"]').input_value() == "Edited while thinking"
            assert len(agent_requests[1]["history"]) == 2
            assert agent_requests[1]["brief"]["title"] == "My manual title"
            await page.reload()
            await page.locator("#agent-panel").wait_for()
            assert await page.locator(".user-message").count() == 2
            assert await page.locator('[name="title"]').input_value() == "Edited while thinking"
            await page.locator("#generate").click()
            assert requests == [], "Opening confirmation must not render"
            await page.locator("#rights").check()
            await page.locator("#confirm-render").click()
            await page.get_by_text("Render queued for safety review.",exact=True).wait_for()
            assert len(requests) == 1 and requests[0]["visibility"] == "private"
            await page.screenshot(path=str(args.evidence/"creator-fixture-signed-in.png"),full_page=True)
            await page.locator('[data-tab="public"]').click()
            await page.get_by_role("button",name="Play",exact=True).click()
            await page.locator("#song-detail audio").wait_for()
            await page.wait_for_function("() => document.querySelector('#song-detail audio').readyState >= 1")
            await page.evaluate("async () => { window.testAudio = document.querySelector('#song-detail audio'); testAudio.muted = true; await testAudio.play(); }")
            await page.wait_for_function("() => testAudio.currentTime >= 0.25")
            previous_time = await page.evaluate("testAudio.currentTime")
            await page.get_by_role("button",name="Like song · 0",exact=True).click()
            await page.get_by_role("button",name="Like song · 1",exact=True).wait_for()
            playback = await page.evaluate("({sameNode:testAudio === document.querySelector('#song-detail audio'), time:testAudio.currentTime, paused:testAudio.paused})")
            assert playback["sameNode"] and not playback["paused"] and playback["time"] >= previous_time, f"Social actions must preserve playback: {playback}"
            await page.get_by_role("button",name="Close",exact=True).click()
            assert await page.locator("#song-detail").is_hidden()
            assert await page.locator("#song-detail audio").count() == 0
            assert not errors, errors
            print(json.dumps({"passed":True,"viewports":[1440,768,390,320],"draftReload":True,
                              "agentDefault":True,"conversationReload":True,"sharedDraft":True,"concurrentManualEditsPreserved":True,
                              "explicitConfirmation":True,"privateDefault":True,"socialPreservesPlayback":True,"pageErrors":errors,
                              "fixtureOnly":"No login, AI generation or purchase was performed"}))
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
