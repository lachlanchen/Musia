#!/usr/bin/env python3
"""Native UI smoke checks on Musia's owned emulator, with retained evidence.

Install the exact signed QA APK first. This checks UI/audio-clock behavior,
not physical-speaker audibility or microphone pitch grading.
"""
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from storelib import RUNTIME, now, write_private

ADB = str(Path.home() / "Android/Sdk/platform-tools/adb")
SERIAL = "emulator-5580"
OUT = RUNTIME / "practice-012/android-final"


def adb(*args):
    return subprocess.check_output([ADB, "-s", SERIAL, *args], timeout=60)


def tree():
    adb("shell", "uiautomator", "dump", "/sdcard/musia-review.xml")
    return ET.fromstring(adb("exec-out", "cat", "/sdcard/musia-review.xml"))


def find(label, timeout=15):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        nodes = [n for n in tree().iter("node") if label in (n.get("text"), n.get("content-desc"))]
        if len(nodes) == 1:
            return nodes[0]
        time.sleep(.3)
    raise AssertionError("Missing/ambiguous visible control: " + label)


def tap(label):
    node = find(label)
    x1, y1, x2, y2 = map(int, re.findall(r"\d+", node.get("bounds")))
    assert x2 > x1 and y2 > y1
    adb("shell", "input", "tap", str((x1+x2)//2), str((y1+y2)//2))


def capture(name):
    write_private(OUT / (name + ".png"), adb("exec-out", "screencap", "-p"))
    write_private(OUT / (name + ".xml"), ET.tostring(tree()))


def swipe(up=True):
    w, h = map(int, re.findall(r"(\d+)x(\d+)", adb("shell", "wm", "size").decode())[-1])
    start, end = (.75, .3) if up else (.3, .75)
    adb("shell", "input", "swipe", str(w//2), str(int(h*start)), str(w//2), str(int(h*end)), "350")


def main():
    assert adb("emu", "avd", "name").decode().startswith("Musia_")
    adb("shell", "am", "force-stop", "art.lazying.musia")
    adb("shell", "am", "start", "-n", "art.lazying.musia/.MainActivity")
    tap("Settings")
    for label in ["English lyrics", "中文 lyrics", "日本語 lyrics"]:
        find(label)
        switches = [n for n in tree().iter("node") if n.get("checkable") == "true"
                    and any(c.get("content-desc") == label for c in n.iter("node"))]
        assert len(switches) == 1 and switches[0].get("checked") == "true", label
    capture("settings")
    tap("Practice history"); capture("history")
    tap("Practice")
    tap("Do Re Mi · Listen and learn")
    tap("Do"); find("Do · C4 · 261.6 Hz"); capture("pitch-learn")
    tap("Quiz"); tap("Listen to the note"); tap("Do")
    texts = [n.get("text", "") for n in tree().iter("node")]
    assert any("/ 1 correct" in t for t in texts)
    capture("pitch-score")
    tap("Back"); tap("Metronome & chord changes")
    find("60 BPM"); tap("Start"); tap("Tap the beat")
    capture("metronome")
    tap("Stop"); tap("Chord accompaniment")
    swipe(); tap("Start")
    shapes = set()
    for _ in range(6):
        for n in tree().iter("node"):
            if n.get("text", "").startswith("Chord shape:"):
                shapes.add(n.get("text"))
        if len(shapes) == 2:
            break
        time.sleep(.7)
    assert shapes == {"Chord shape: Em", "Chord shape: Am"}, shapes
    capture("chord-changes")
    adb("shell", "input", "keyevent", "KEYCODE_HOME")
    time.sleep(2)  # Allow the Activity to reach ON_STOP before resuming it.
    adb("shell", "am", "start", "-n", "art.lazying.musia/.MainActivity")
    find("Start"); capture("background-stopped-practice")
    tap("Songs"); tap("Search")
    adb("shell", "input", "text", "Rain%sof%sLight")
    adb("shell", "input", "keyevent", "KEYCODE_BACK")
    tap("アヤちゃん 光の雨 · Aya Chan, Rain of Light")
    # The transport is above the three-language lyrics.
    find("Playback position", timeout=30)
    capture("aya-transport")
    write_private(OUT / "smoke.json", {"at": now(), "state": "passed", "serial": SERIAL,
        "checks": ["default languages", "Settings history", "reference note", "first-answer quiz score",
                   "metronome tap", "audio-clock Em/Am transitions", "background stops practice", "live Aya loaded"],
        "limitations": ["Emulator UI and audio-clock verification; not a physical listening test"]})
    print(OUT / "smoke.json")


if __name__ == "__main__":
    main()
