#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CATALOG = {
    "danny-boy-1917": {
        "title": "Schumann-Heink - Danny Boy (Londonderry Air) (1917)",
        "url": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Schumann-Heink%20-%20Danny%20Boy%20%28Londonderry%20air%29%20%281917%29.ogg",
        "source_page": "https://commons.wikimedia.org/wiki/File:Schumann-Heink_-_Danny_Boy_(Londonderry_air)_(1917).ogg",
        "license_note": "Wikimedia Commons public-domain/free-media page; verify before public/commercial use.",
        "filename": "original.ogg",
    },
    "e-scris-pe-tricolor-vocal": {
        "title": "E scris pe tricolor Unire (vocal)",
        "url": "https://commons.wikimedia.org/wiki/Special:Redirect/file/E%20scris%20pe%20tricolor%20Unire%20%28vocal%29.ogg",
        "source_page": "https://commons.wikimedia.org/wiki/File:E_scris_pe_tricolor_Unire_(vocal).ogg",
        "license_note": "Wikimedia Commons free-media page; verify before public/commercial use.",
        "filename": "original.ogg",
    },
    "chinese-vocal-ensemble": {
        "title": "Chinese Vocal and Instrumental Ensemble",
        "url": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Chinese%20Vocal%20and%20Instrumental%20Ensemble.ogg",
        "source_page": "https://commons.wikimedia.org/wiki/File:Chinese_Vocal_and_Instrumental_Ensemble.ogg",
        "license_note": "Wikimedia Commons public-domain/pre-1972 sound-recording page; verify source date and jurisdiction before public/commercial use.",
        "filename": "original.ogg",
    },
    "hotaru-no-hikari": {
        "title": "Hotaru no Hikari (Auld Lang Syne in Japan)",
        "url": "https://upload.wikimedia.org/wikipedia/commons/f/f4/Hotaru_no_Hikari%28Auld_lang_syne_in_Japan%29.ogg",
        "source_page": "https://commons.wikimedia.org/wiki/File:Hotaru_no_Hikari(Auld_lang_syne_in_Japan).ogg",
        "license_note": "Wikimedia Commons public-domain self-dedication page; verify before public/commercial use.",
        "filename": "original.ogg",
    },
    "sakura-sakura-vocal-synth": {
        "title": "Sakura Sakura (vocal synthesizer performance)",
        "url": "https://upload.wikimedia.org/wikipedia/commons/e/ed/Sakura_Sakura.song.ogg",
        "source_page": "https://commons.wikimedia.org/wiki/File:Sakura_Sakura.song.ogg",
        "license_note": "Wikimedia Commons CC BY-SA/GFDL page; share-alike attribution terms apply.",
        "filename": "original.ogg",
    },
    "moli-hua-ks-synth": {
        "title": "Mo Li Hua - Karplus-Strong synthesis demo",
        "url": "https://upload.wikimedia.org/wikipedia/commons/c/c6/%E8%8C%89%E8%8E%89%E8%8A%B1-KS%E6%BC%94%E7%A4%BA.opus",
        "source_page": "https://commons.wikimedia.org/wiki/File:%E8%8C%89%E8%8E%89%E8%8A%B1-KS%E6%BC%94%E7%A4%BA.opus",
        "license_note": "Wikimedia Commons CC0 public-domain dedication page. This is instrumental/synth, useful for melody/chord tests rather than lyric ASR.",
        "filename": "original.opus",
    },
}


def download(url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "MusaiLocalTestDownloader/0.1"})
    with urlopen(request, timeout=60) as response:
        total = response.headers.get("content-length")
        total_int = int(total) if total and total.isdigit() else None
        received = 0
        with output.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                handle.write(chunk)
                received += len(chunk)
                if total_int:
                    pct = received * 100 / total_int
                    print(f"\r{output.name}: {pct:5.1f}%", end="", file=sys.stderr)
        if total_int:
            print(file=sys.stderr)


def download_item(item_id: str, output_root: Path) -> Path:
    item = CATALOG[item_id]
    target_dir = output_root / item_id
    audio_path = target_dir / item["filename"]
    if audio_path.exists() and audio_path.stat().st_size > 0:
        print(audio_path)
    else:
        download(item["url"], audio_path)
        print(audio_path)

    metadata = dict(item)
    metadata["id"] = item_id
    metadata["local_audio"] = str(audio_path)
    (target_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return audio_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download free/open songs for Musai local testing.")
    parser.add_argument("--id", choices=sorted(CATALOG), default="danny-boy-1917")
    parser.add_argument("--all", action="store_true", help="Download every catalog entry.")
    parser.add_argument("--list", action="store_true", help="List available catalog entries.")
    parser.add_argument("--output-root", type=Path, default=Path("data/open_songs"))
    args = parser.parse_args()

    if args.list:
        for key, item in CATALOG.items():
            print(f"{key}: {item['title']}")
        return

    if args.all:
        failures = []
        for item_id in sorted(CATALOG):
            try:
                download_item(item_id, args.output_root)
            except (HTTPError, URLError, TimeoutError) as exc:
                failures.append((item_id, str(exc)))
                print(f"failed: {item_id}: {exc}", file=sys.stderr)
        if failures:
            print("Some downloads failed:", file=sys.stderr)
            for item_id, error in failures:
                print(f"- {item_id}: {error}", file=sys.stderr)
            raise SystemExit(1)
    else:
        download_item(args.id, args.output_root)


if __name__ == "__main__":
    main()
