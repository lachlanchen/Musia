#!/usr/bin/env python3
"""Check the real Stage UI on a Musia-owned emulator with native evidence.

Install the exact candidate first. This deliberately cannot operate a phone.
The captures are native screenshots, not reconstructed previews.
"""
import argparse
import json
import re
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", default="emulator-5580")
    parser.add_argument("--output", type=Path, default=Path("store/.runtime/stage-013/android-final"))
    args = parser.parse_args()
    if not re.fullmatch(r"emulator-\d+", args.serial):
        parser.error("Use a project-owned emulator")
    adb_path = str(Path.home() / "Android/Sdk/platform-tools/adb")

    def adb(*words):
        return subprocess.check_output([adb_path, "-s", args.serial, *words], timeout=60)

    assert adb("emu", "avd", "name").decode().startswith("Musia_")
    args.output.mkdir(parents=True, exist_ok=True)

    def tree():
        adb("shell", "uiautomator", "dump", "/sdcard/musia-stage.xml")
        return ET.fromstring(adb("exec-out", "cat", "/sdcard/musia-stage.xml"))

    def bounds(node):
        return list(map(int, re.findall(r"\d+", node.get("bounds"))))

    def find(label):
        for _ in range(10):
            matches = [n for n in tree().iter("node") if label in (n.get("text"), n.get("content-desc"))]
            if len(matches) == 1:
                return matches[0]
            time.sleep(.3)
        raise AssertionError("Missing or ambiguous control: " + label)

    def tap(label):
        node = find(label)
        assert node.get("enabled") == "true", label
        x1, y1, x2, y2 = bounds(node)
        assert x2 > x1 and y2 > y1, label
        adb("shell", "input", "tap", str((x1+x2)//2), str((y1+y2)//2))

    def capture(name):
        (args.output / (name + ".png")).write_bytes(adb("exec-out", "screencap", "-p"))
        (args.output / (name + ".xml")).write_bytes(ET.tostring(tree()))

    def scroll():
        # Start inside the lyrics, never in the bottom transport's seek slider.
        x1, y1, x2, y2 = bounds(find("Playback position"))
        adb("shell", "input", "swipe", str((x1+x2)//2), str(int(y1*.78)), str(int((x1+x2)//2)), str(int(y1*.38)), "450")

    adb("shell", "am", "force-stop", "art.lazying.musia")
    adb("shell", "am", "start", "-W", "-n", "art.lazying.musia/.MainActivity")
    tap("Search")
    adb("shell", "input", "text", "Rain%sof%sLight")
    adb("shell", "input", "keyevent", "KEYCODE_BACK")
    tap("アヤちゃん 光の雨 · Aya Chan, Rain of Light")
    find("Stage view")
    for _ in range(3):
        tap("Forward 5 seconds")
    for label in ("English", "中文", "日本語"):
        find(label)
    capture("phone-lyrics")
    scroll()
    nodes = list(tree().iter("node"))
    diagram = next(n for n in nodes if ", standard tuning." in n.get("content-desc", ""))
    slider = find("Playback position")
    assert bounds(diagram)[3] <= bounds(slider)[1], "Diagram must not overlap transport"
    assert bounds(diagram)[3] - bounds(diagram)[1] > 200, "Diagram must be visible, not just its heading"
    # At a paused 15-second seek, the diagram must agree with the selected asset.
    with urllib.request.urlopen("https://musia.lazying.art/api/v1/songs/aya-chan-hikari-ame", timeout=30) as response:
        song = json.load(response)
    asset = next(a for a in song["assets"] if a["id"] == song["defaultAssetId"])
    chord = next(c for c in asset["chords"] if c["start"] <= 15 < c["end"])
    assert diagram.get("content-desc").startswith(chord["name"] + ","), "Wrong current chord"
    capture("phone-guitar")
    tap("Play")
    time.sleep(1.5)
    tap("Pause")
    assert "0:15" not in [n.get("text") for n in tree().iter("node")], "Media clock must advance"
    capture("paused-after-playback")
    tap("Back")
    find("Songs"); find("Settings")
    capture("navigation-restored")
    (args.output / "smoke.json").write_text(json.dumps({
        "state": "passed", "serial": args.serial,
        "checks": ["Stage default", "three languages", "paused source-time seek", "correct source chord",
                   "diagram above transport", "play/pause clock", "Back restores navigation"],
        "limitations": ["Emulator UI and media-clock test, not physical-device listening"]
    }, indent=2) + "\n")
    print(args.output / "smoke.json")


if __name__ == "__main__":
    main()
