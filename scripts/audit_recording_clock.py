#!/usr/bin/env python3
"""Check a recording's visible player clock against its muxed audio offset."""

import argparse
import json
import re
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--start", type=float, required=True)
    parser.add_argument("--crop", default="160:90:250:1350", help="FFmpeg w:h:x:y clock crop")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(args.video),
        "-vf", f"crop={args.crop},fps=1,scale=320:180", "-start_number", "0",
        str(args.output / "%04d.png"),
    ], check=True)
    rows = []
    for path in sorted(args.output.glob("[0-9][0-9][0-9][0-9].png")):
        for mode in ("7", "13"):
            result = subprocess.run([
                "tesseract", str(path), "stdout", "--psm", mode,
                "-c", "tessedit_char_whitelist=0123456789:",
            ], check=True, capture_output=True, text=True)
            text = result.stdout.strip()
            match = re.fullmatch(r"(\d+):(\d{2})", text)
            if match:
                break
        expected = int(args.start + int(path.stem) + 0.5)
        actual = int(match[1]) * 60 + int(match[2]) if match else None
        rows.append({"videoSecond": int(path.stem), "expected": expected,
                     "observed": actual, "ocr": text,
                     "ok": actual is not None and abs(actual - expected) <= 1})
    report = {"video": str(args.video), "sourceStart": args.start,
              "samples": rows, "failed": [row for row in rows if not row["ok"]]}
    (args.output / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"samples": len(rows), "failed": report["failed"]}))
    if not rows or report["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
