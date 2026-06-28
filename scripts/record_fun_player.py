#!/usr/bin/env python3
"""Record the Fun Lazying Art player and mux it with the source audio.

This script captures the website as deterministic PNG frames with Playwright,
then uses FFmpeg to attach the media file's own audio track. It is intended for
clean social/demo videos where the audience sees Fun Lazying Art + Musia and
hears the exact rendered song file.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def fail(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def playable_assets(manifest: dict) -> list[dict]:
    assets = manifest.get("assets") or {}
    result: list[dict] = []
    primary = assets.get("primaryAudio") or {}
    if primary.get("src"):
        result.append({**primary, "id": primary.get("id") or "primary", "type": "audio"})
    for item in assets.get("alternateAudio") or []:
        if item.get("src"):
            result.append({**item, "id": item.get("id") or item.get("label") or item["src"], "type": "audio"})
    video = assets.get("primaryVideo") or {}
    if video.get("src"):
        result.append({**video, "id": video.get("id") or "video", "type": "video"})
    return result


def start_server(root: Path) -> tuple[ThreadingHTTPServer, str]:
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(root), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}/"


def first_vocal_start(manifest: dict) -> float:
    for line in (manifest.get("timeline") or {}).get("lines") or []:
        try:
            return max(0.0, float(line["start"]))
        except (KeyError, TypeError, ValueError):
            continue
    return 0.0


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record the Fun Lazying Art player as an MP4.")
    parser.add_argument("--media-id", default="", help="Catalog media id. Defaults to catalog.defaultMedia.")
    parser.add_argument("--asset-id", default="", help="Playable audio/video asset id. Defaults to first playable asset.")
    parser.add_argument("--output", default="", help="Output MP4 path.")
    parser.add_argument("--width", type=int, default=1920, help="Viewport width.")
    parser.add_argument("--height", type=int, default=1080, help="Viewport height.")
    parser.add_argument("--fps", type=int, default=24, help="Capture frames per second.")
    parser.add_argument("--crf", type=int, default=14, help="H.264 CRF quality. Lower is higher quality; default 14.")
    parser.add_argument("--preset", default="slow", help="H.264 preset. Default slow for cleaner text.")
    parser.add_argument("--audio-bitrate", default="320k", help="AAC audio bitrate. Default 320k.")
    parser.add_argument("--duration", type=float, default=0.0, help="Capture duration in seconds. Defaults to media end.")
    parser.add_argument("--start", type=float, default=-1.0, help="Start time in seconds. Overrides --skip-intro.")
    parser.add_argument("--skip-intro", action="store_true", help="Start at the first timed lyric/vocal line.")
    parser.add_argument("--site-url", default="", help="Use an existing site URL instead of a temporary local server.")
    parser.add_argument("--keep-frames", action="store_true", help="Do not delete captured PNG frames.")
    parser.add_argument("--full-page", action="store_true", help="Capture the full scrollable page instead of only the viewport.")
    parser.add_argument("--include-full-lyrics", action="store_true", help="Keep the bottom full lyrics visible during capture.")
    parser.add_argument("--chrome-channel", default="chrome", help="Playwright Chromium channel, usually chrome or chromium.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not WEBSITE.exists():
        fail(f"Missing website directory: {WEBSITE}")
    if shutil.which("ffmpeg") is None:
        fail("ffmpeg is required for muxing the captured video.")

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - depends on local setup
        fail(
            "Python Playwright is required. Install locally with:\n"
            "  python3 -m pip install --user playwright\n"
            "The script uses the installed Chrome channel, so Playwright browser downloads are optional.\n"
            f"Import error: {exc}"
        )

    catalog = load_json(WEBSITE / "data" / "catalog.json")
    media_id = args.media_id or catalog.get("defaultMedia") or ""
    item = next((entry for entry in catalog.get("items", []) if entry.get("id") == media_id), None)
    if not item:
        fail(f"Media id not found in catalog: {media_id}")

    manifest_path = WEBSITE / item["manifest"]
    manifest = load_json(manifest_path)
    assets = playable_assets(manifest)
    if not assets:
        fail(f"No playable local assets in manifest: {manifest_path}")
    asset = next((entry for entry in assets if entry.get("id") == args.asset_id), assets[0])
    media_src = asset.get("src")
    audio_path = (WEBSITE / media_src).resolve()
    if not audio_path.exists():
        fail(f"Audio/video source not found: {audio_path}")

    start = args.start if args.start >= 0 else (first_vocal_start(manifest) if args.skip_intro else 0.0)
    total_duration = float(manifest.get("duration") or 0.0)
    duration = args.duration if args.duration > 0 else max(0.1, total_duration - start)
    output = Path(args.output) if args.output else ROOT / "data" / "video_captures" / f"{media_id}{'-skip-intro' if args.skip_intro else ''}.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)

    server = None
    if args.site_url:
        base_url = args.site_url.rstrip("/") + "/"
    else:
        server, base_url = start_server(WEBSITE)

    query = urlencode({
        "capture": "1",
        "fullLyrics": "1" if args.include_full_lyrics else "0",
        "media": media_id,
        "skipIntro": "1" if args.skip_intro else "0",
    })
    url = f"{base_url}?{query}#{media_id}"
    frame_count = int(duration * args.fps + 0.999)

    with tempfile.TemporaryDirectory(prefix="musia-fun-capture-") as tmp:
        frame_dir = Path(tmp) / "frames"
        frame_dir.mkdir()
        mode = "full page" if args.full_page else "viewport"
        print(f"Capturing {frame_count} {mode} frames at {args.width}x{args.height}, {args.fps} fps", flush=True)
        print(f"URL: {url}", flush=True)
        print(f"Audio: {audio_path}", flush=True)
        print(f"Start: {start:.3f}s  Duration: {duration:.3f}s", flush=True)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                channel=args.chrome_channel,
                headless=True,
                args=[
                    "--autoplay-policy=no-user-gesture-required",
                    "--hide-scrollbars",
                    "--disable-dev-shm-usage",
                ],
            )
            page = browser.new_page(
                viewport={"width": args.width, "height": args.height},
                device_scale_factor=1,
            )
            page.goto(url, wait_until="networkidle")
            page.wait_for_selector("#audio", state="attached", timeout=15000)
            page.wait_for_function(
                """() => window.funPlayerSetTime
                  && document.getElementById('audio')
                  && Number.isFinite(document.getElementById('audio').duration)""",
                timeout=20000,
            )
            page.wait_for_timeout(400)
            for index in range(frame_count):
                timestamp = start + index / args.fps
                page.evaluate("(time) => window.funPlayerSetTime(time)", timestamp)
                page.wait_for_timeout(10)
                page.screenshot(path=str(frame_dir / f"{index:06d}.png"), full_page=args.full_page)
                if index and index % max(args.fps * 5, 1) == 0:
                    print(f"  captured {index}/{frame_count}", flush=True)
            browser.close()

        run([
            "ffmpeg",
            "-y",
            "-framerate",
            str(args.fps),
            "-i",
            str(frame_dir / "%06d.png"),
            "-ss",
            f"{start:.3f}",
            "-i",
            str(audio_path),
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            args.preset,
            "-crf",
            str(args.crf),
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(args.fps),
            "-c:a",
            "aac",
            "-b:a",
            args.audio_bitrate,
            "-movflags",
            "+faststart",
            "-shortest",
            str(output),
        ])

        if args.keep_frames:
            keep_dir = output.with_suffix("")
            if keep_dir.exists():
                shutil.rmtree(keep_dir)
            shutil.copytree(frame_dir, keep_dir)
            print(f"Frames kept at: {keep_dir}")

    if server:
        server.shutdown()
    print(f"Wrote: {output}")


if __name__ == "__main__":
    main()
