#!/usr/bin/env python3
"""Realtime high-resolution screen recorder for the Fun Lazying Art player.

Unlike ``record_fun_player.py``, this script does not capture deterministic PNG
frames. It opens the website in a real Chrome window inside a high-resolution
Xvfb display, records the display with FFmpeg x11grab in real time, and muxes
the selected song audio from the manifest/cache.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import urlretrieve


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
DEFAULT_SYNC_DIR = Path("/home/lachlan/Nutstore Files/Projects/Musia")


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


def resolve_media_source(src: str) -> Path:
    parsed = urlparse(src)
    if parsed.scheme in {"http", "https"}:
        filename = Path(parsed.path).name or "remote-audio"
        cache_dir = ROOT / "data" / "video_captures" / "_audio_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cached = cache_dir / filename
        if not cached.exists() or cached.stat().st_size == 0:
            print(f"Downloading remote media for muxing: {src}", flush=True)
            urlretrieve(src, cached)
        return cached.resolve()
    return (WEBSITE / src).resolve()


def start_server(root: Path) -> tuple[ThreadingHTTPServer, str]:
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(root), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}/"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def choose_display() -> str:
    for number in range(120, 180):
        if not Path(f"/tmp/.X11-unix/X{number}").exists():
            return f":{number}"
    fail("No free Xvfb display number found.")
    return ":120"


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, env=env)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Realtime-record the Fun Lazying Art player.")
    parser.add_argument("--media-id", required=True, help="Catalog media id.")
    parser.add_argument("--asset-id", default="", help="Playable audio/video asset id.")
    parser.add_argument("--output", required=True, help="Output MP4 path.")
    parser.add_argument("--width", type=int, default=2160, help="Capture display width.")
    parser.add_argument("--height", type=int, default=3840, help="Capture display height.")
    parser.add_argument("--css-width", type=int, default=0, help="Chrome CSS viewport width. Defaults to --width.")
    parser.add_argument("--css-height", type=int, default=0, help="Chrome CSS viewport height. Defaults to --height.")
    parser.add_argument("--device-scale-factor", type=float, default=1.0, help="Chrome device scale factor.")
    parser.add_argument("--fps", type=int, default=24, help="Realtime capture frame rate.")
    parser.add_argument("--duration", type=float, default=60.0, help="Seconds to record.")
    parser.add_argument("--start", type=float, default=0.0, help="Audio/player start time in seconds.")
    parser.add_argument(
        "--capture-lead",
        type=float,
        default=0.25,
        help="Seconds of preroll to capture before browser playback starts; trimmed before muxing for tighter audio/video sync.",
    )
    parser.add_argument("--crf", type=int, default=12, help="x264 CRF. Lower is higher quality.")
    parser.add_argument("--preset", default="ultrafast", help="x264 preset. ultrafast keeps 4K realtime responsive.")
    parser.add_argument("--audio-bitrate", default="320k", help="AAC audio bitrate.")
    parser.add_argument("--include-full-lyrics", action="store_true", help="Keep the full lyrics panel visible.")
    parser.add_argument("--multilingual-lyrics", action="store_true", help="Use one-line multilingual EN/JP/ZH lyric capture layout.")
    parser.add_argument("--portrait", action=argparse.BooleanOptionalAction, default=True, help="Use portrait capture layout.")
    parser.add_argument("--advanced", action=argparse.BooleanOptionalAction, default=True, help="Enable advanced chord/guitar mode.")
    parser.add_argument("--guitar-focus", action=argparse.BooleanOptionalAction, default=True, help="Use the lower panel for guitar fingering.")
    parser.add_argument("--ffmpeg-bin", default="", help="FFmpeg binary. Defaults to /usr/bin/ffmpeg when available for x11grab.")
    parser.add_argument("--display", default="", help="Existing X display to use. Defaults to a new Xvfb display.")
    parser.add_argument("--chrome-channel", default="chrome", help="Playwright Chrome channel.")
    parser.add_argument("--chrome-bin", default="", help="Chrome binary. Defaults to google-chrome.")
    parser.add_argument("--sync-dir", default=str(DEFAULT_SYNC_DIR), help="Directory to copy the final MP4 to.")
    parser.add_argument("--no-sync", action="store_true", help="Do not copy final MP4 to --sync-dir.")
    parser.add_argument("--keep-raw", action="store_true", help="Keep the raw screen-capture MP4.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.capture_lead < 0:
        fail("--capture-lead must be non-negative.")
    if not WEBSITE.exists():
        fail(f"Missing website directory: {WEBSITE}")
    ffmpeg_bin = args.ffmpeg_bin or ("/usr/bin/ffmpeg" if Path("/usr/bin/ffmpeg").exists() else shutil.which("ffmpeg") or "")
    if not ffmpeg_bin:
        fail("ffmpeg is required.")
    for tool in ["Xvfb"]:
        if shutil.which(tool) is None:
            fail(f"{tool} is required.")
    chrome_bin = args.chrome_bin or shutil.which("google-chrome") or shutil.which("chromium") or ""
    if not chrome_bin:
        fail("google-chrome or chromium is required.")

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        fail(f"Python Playwright is required in the musia environment: {exc}")

    catalog = load_json(WEBSITE / "data" / "catalog.json")
    item = next((entry for entry in catalog.get("items", []) if entry.get("id") == args.media_id), None)
    if not item:
        fail(f"Media id not found in catalog: {args.media_id}")
    manifest = load_json(WEBSITE / item["manifest"])
    assets = playable_assets(manifest)
    if not assets:
        fail(f"No playable assets in manifest: {item['manifest']}")
    asset = next((entry for entry in assets if entry.get("id") == args.asset_id), assets[0])
    media_src = asset.get("src") or ""
    audio_path = resolve_media_source(media_src)
    if not audio_path.exists():
        fail(f"Audio/video source not found: {audio_path}")

    server, base_url = start_server(WEBSITE)
    display = args.display or choose_display()
    css_width = args.css_width or args.width
    css_height = args.css_height or args.height
    xvfb = None
    chrome = None
    ffmpeg = None
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    query = urlencode(
        {
            "asset": asset.get("id") or args.asset_id,
            "capture": "1",
            "fullLyrics": "1" if args.include_full_lyrics else "0",
            "multiLyrics": "1" if args.multilingual_lyrics else "0",
            "media": args.media_id,
            "portrait": "1" if args.portrait else "0",
            "skipIntro": "0",
            "advanced": "1" if args.advanced else "0",
            "guitarFocus": "1" if args.guitar_focus else "0",
        }
    )
    url = f"{base_url}?{query}#{args.media_id}"

    with tempfile.TemporaryDirectory(prefix="musia-fun-realtime-") as tmp:
        user_data = Path(tmp) / "chrome-profile"
        raw_video = Path(tmp) / "raw-screen.mp4"
        try:
            if not args.display:
                xvfb = subprocess.Popen(
                    ["Xvfb", display, "-screen", "0", f"{args.width}x{args.height}x24", "-ac"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(0.7)

            env = {**os.environ, "DISPLAY": display}
            port = free_port()
            chrome_cmd = [
                chrome_bin,
                f"--remote-debugging-port={port}",
                "--remote-allow-origins=*",
                f"--user-data-dir={user_data}",
                "--no-first-run",
                "--disable-session-crashed-bubble",
                "--disable-infobars",
                "--autoplay-policy=no-user-gesture-required",
                "--hide-scrollbars",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                f"--force-device-scale-factor={args.device_scale_factor:g}",
                "--window-position=0,0",
                f"--window-size={css_width},{css_height}",
                "--kiosk",
                f"--app={url}",
            ]
            print(f"Realtime URL: {url}", flush=True)
            print(
                f"Display: {display}  Capture: {args.width}x{args.height}  "
                f"CSS viewport: {css_width}x{css_height} @ {args.device_scale_factor:g}x  "
                f"Duration: {args.duration:.3f}s  Capture lead: {args.capture_lead:.3f}s",
                flush=True,
            )
            print(f"Audio: {audio_path}", flush=True)
            chrome = subprocess.Popen(chrome_cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.5)

            with sync_playwright() as playwright:
                browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                deadline = time.time() + 20
                page = None
                while time.time() < deadline and page is None:
                    pages = [p for context in browser.contexts for p in context.pages]
                    page = next((candidate for candidate in pages if args.media_id in candidate.url), None)
                    if page is None:
                        time.sleep(0.25)
                if page is None:
                    fail("Could not attach to the Chrome app page.")
                parsed_media = urlparse(media_src or "")
                if parsed_media.scheme in {"http", "https"} and audio_path.exists():
                    page.route(
                        media_src,
                        lambda route: route.fulfill(
                            status=200,
                            path=str(audio_path),
                            headers={"Access-Control-Allow-Origin": "*"},
                        ),
                    )
                    page.goto(url, wait_until="networkidle")
                page.wait_for_selector("#audio, #video", state="attached", timeout=20000)
                page.wait_for_function(
                    """() => window.funPlayerUpdateSync
                      && (document.getElementById('audio') || document.getElementById('video'))
                      && Number.isFinite((document.getElementById('audio') || document.getElementById('video')).duration)""",
                    timeout=30000,
                )
                page.evaluate(
                    """async (start) => {
                      const media = document.getElementById('audio') || document.getElementById('video');
                      media.muted = true;
                      media.volume = 0;
                      media.pause();
                      const target = Math.max(0, Number(start) || 0);
                      if (Math.abs((media.currentTime || 0) - target) > 0.05) {
                        await new Promise((resolve) => {
                          let done = false;
                          const finish = () => {
                            if (done) return;
                            done = true;
                            media.removeEventListener('seeked', finish);
                            resolve();
                          };
                          media.addEventListener('seeked', finish, { once: true });
                          media.currentTime = target;
                          window.setTimeout(finish, 3000);
                        });
                      } else {
                        media.currentTime = target;
                      }
                      window.funPlayerUpdateSync();
                    }""",
                    args.start,
                )
                page.wait_for_timeout(600)

                ffmpeg_cmd = [
                    ffmpeg_bin,
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-nostats",
                    "-f",
                    "x11grab",
                    "-draw_mouse",
                    "0",
                    "-video_size",
                    f"{args.width}x{args.height}",
                    "-framerate",
                    str(args.fps),
                    "-i",
                    f"{display}.0+0,0",
                    "-t",
                    f"{args.duration + args.capture_lead:.3f}",
                    "-c:v",
                    "libx264",
                    "-preset",
                    args.preset,
                    "-crf",
                    str(args.crf),
                    "-pix_fmt",
                    "yuv420p",
                    "-r",
                    str(args.fps),
                    str(raw_video),
                ]
                print("+", " ".join(ffmpeg_cmd), flush=True)
                ffmpeg = subprocess.Popen(ffmpeg_cmd, env=env)
                time.sleep(args.capture_lead)
                page.evaluate(
                    """async () => {
                      const media = document.getElementById('audio') || document.getElementById('video');
                      media.muted = true;
                      media.volume = 0;
                      await media.play();
                    }""",
                )
                code = ffmpeg.wait(timeout=args.duration + args.capture_lead + 120)
                if code != 0:
                    fail(f"FFmpeg screen capture failed with code {code}")
                browser.close()

            run(
                [
                    ffmpeg_bin,
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-nostats",
                    "-ss",
                    f"{args.capture_lead:.3f}",
                    "-i",
                    str(raw_video),
                    "-ss",
                    f"{args.start:.3f}",
                    "-i",
                    str(audio_path),
                    "-t",
                    f"{args.duration:.3f}",
                    "-map",
                    "0:v:0",
                    "-map",
                    "1:a:0",
                    "-c:v",
                    "copy",
                    "-c:a",
                    "aac",
                    "-b:a",
                    args.audio_bitrate,
                    "-shortest",
                    str(output),
                ]
            )
            if args.keep_raw:
                keep = output.with_name(output.stem + ".raw-screen.mp4")
                shutil.copy2(raw_video, keep)
                print(f"Raw screen capture: {keep}", flush=True)
            print(f"Output: {output}", flush=True)
            if not args.no_sync and args.sync_dir:
                sync_dir = Path(args.sync_dir).expanduser()
                sync_dir.mkdir(parents=True, exist_ok=True)
                synced = sync_dir / output.name
                shutil.copy2(output, synced)
                print(f"Synced: {synced}", flush=True)
        finally:
            server.shutdown()
            if ffmpeg and ffmpeg.poll() is None:
                ffmpeg.terminate()
                try:
                    ffmpeg.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    ffmpeg.kill()
            if chrome and chrome.poll() is None:
                chrome.terminate()
                try:
                    chrome.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    chrome.kill()
            if xvfb and xvfb.poll() is None:
                xvfb.terminate()
                try:
                    xvfb.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    xvfb.kill()


if __name__ == "__main__":
    main()
