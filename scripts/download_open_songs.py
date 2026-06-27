#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Download free/open songs for Musai local testing.")
    parser.add_argument("--id", choices=sorted(CATALOG), default="danny-boy-1917")
    parser.add_argument("--list", action="store_true", help="List available catalog entries.")
    parser.add_argument("--output-root", type=Path, default=Path("data/open_songs"))
    args = parser.parse_args()

    if args.list:
        for key, item in CATALOG.items():
            print(f"{key}: {item['title']}")
        return

    item = CATALOG[args.id]
    target_dir = args.output_root / args.id
    audio_path = target_dir / item["filename"]
    if audio_path.exists() and audio_path.stat().st_size > 0:
        print(audio_path)
    else:
        download(item["url"], audio_path)
        print(audio_path)

    metadata = dict(item)
    metadata["local_audio"] = str(audio_path)
    (target_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

