#!/usr/bin/env python3
"""Observed native UI actions on one Musia-owned emulator; no device guessing."""
import argparse
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["inspect", "tap", "swipe-up", "swipe-down", "capture", "back"])
    parser.add_argument("value", nargs="?")
    parser.add_argument("--serial", default="emulator-5580")
    parser.add_argument("--adb", default=str(Path.home() / "Android/Sdk/platform-tools/adb"))
    parser.add_argument("--output", type=Path, default=Path("store/.runtime/practice-012/android"))
    args = parser.parse_args()
    if not re.fullmatch(r"emulator-\d+", args.serial):
        parser.error("Select a Musia-owned emulator")

    def adb(*command):
        return subprocess.check_output([args.adb, "-s", args.serial, *command], timeout=60)

    if not adb("emu", "avd", "name").decode().startswith("Musia_"):
        parser.error("Not a Musia emulator")
    if args.action == "capture":
        if not args.value or not re.fullmatch(r"[A-Za-z0-9_-]+", args.value):
            parser.error("Capture needs a plain filename")
        args.output.mkdir(parents=True, exist_ok=True)
        path = args.output / (args.value + ".png")
        path.write_bytes(adb("exec-out", "screencap", "-p"))
        print(path)
        return
    if args.action == "back":
        adb("shell", "input", "keyevent", "KEYCODE_BACK")
        return
    if args.action.startswith("swipe-"):
        width, height = map(int, re.findall(r"(\d+)x(\d+)", adb("shell", "wm", "size").decode())[-1])
        start, end = (.75, .3) if args.action == "swipe-up" else (.3, .75)
        adb("shell", "input", "swipe", str(width // 2), str(int(height * start)), str(width // 2), str(int(height * end)), "450")
        return
    adb("shell", "uiautomator", "dump", "/sdcard/musia-review.xml")
    tree = ET.fromstring(adb("exec-out", "cat", "/sdcard/musia-review.xml"))
    nodes = [n for n in tree.iter("node") if n.get("text") or n.get("content-desc") or n.get("clickable") == "true"]
    if args.action == "inspect":
        print(json.dumps([{k: n.get(k) for k in ("text", "content-desc", "class", "bounds", "enabled", "selected", "checked")} for n in nodes], ensure_ascii=False, indent=2))
    else:
        matches = [n for n in nodes if args.value in (n.get("text"), n.get("content-desc"))]
        if len(matches) != 1:
            parser.error(f"Expected one exact observed control, got {len(matches)}")
        node = matches[0]
        if node.get("enabled") != "true":
            parser.error("Control is disabled")
        x1, y1, x2, y2 = map(int, re.findall(r"\d+", node.get("bounds")))
        if x2 <= x1 or y2 <= y1:
            parser.error("Control is outside viewport")
        adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))


if __name__ == "__main__":
    main()
