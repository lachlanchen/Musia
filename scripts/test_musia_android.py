#!/usr/bin/env python3
"""Bounded UI smoke on a project-owned emulator, never an attached phone."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--adb", default=str(Path.home() / "Android/Sdk/platform-tools/adb"))
    parser.add_argument("--apk", type=Path)
    parser.add_argument("--output", type=Path, default=Path(".runtime/learning/android-review"))
    args = parser.parse_args()
    if not re.fullmatch(r"emulator-\d+", args.serial):
        parser.error("Use a dedicated Musia emulator serial, not a shared physical device")
    args.output.mkdir(parents=True, exist_ok=True)

    def adb(*command, binary=False):
        result = subprocess.run([args.adb,"-s",args.serial,*command],check=True,capture_output=True,timeout=90)
        return result.stdout if binary else result.stdout.decode("utf-8",errors="replace").strip()

    name = adb("emu","avd","name").splitlines()[0]
    if not name.startswith("Musia_"):
        parser.error("Refusing to operate another project's emulator")

    def screen():
        adb("shell","uiautomator","dump","/sdcard/musia-review-ui.xml")
        raw = adb("exec-out","cat","/sdcard/musia-review-ui.xml")
        return ET.fromstring(raw), raw

    def capture(name):
        (args.output/f"{name}.png").write_bytes(adb("exec-out","screencap","-p",binary=True))
        _, xml = screen()
        (args.output/f"{name}.xml").write_text(xml)

    def click(label, description=False, scroll=False):
        for _ in range(8):
            root,_ = screen()
            matches = [n for n in root.iter("node") if n.get("content-desc" if description else "text") == label]
            if matches:
                bounds = list(map(int,re.findall(r"\d+",matches[0].get("bounds",""))))
                if len(bounds) == 4 and bounds[2] > bounds[0] and bounds[3] > bounds[1]:
                    adb("shell","input","tap",str((bounds[0]+bounds[2])//2),str((bounds[1]+bounds[3])//2))
                    time.sleep(.6)
                    return
            if scroll:
                size = adb("shell","wm","size")
                width,height = map(int,re.findall(r"(\d+)x(\d+)",size)[-1])
                adb("shell","input","swipe",str(width//2),str(height*3//4),str(width//2),str(height//3),"300")
            else:
                time.sleep(1)
        raise AssertionError(f"Visible control not found: {label}")

    def assert_playing(name):
        for _ in range(16):
            session = adb("shell","dumpsys","media_session")
            (args.output/f"{name}-media-session.txt").write_text(session)
            musia = re.search(r"package=art\.lazying\.musia\n(.*?)(?=\n {4}\S|\Z)",session,re.S)
            if musia and re.search(r"state=(?:3\b|PLAYING\b)",musia.group(1)):
                return
            time.sleep(.5)
        raise AssertionError(f"No playing Musia media session: {name}")

    evidence = {"emulator":name,"serial":args.serial,"checks":[],"limits":["Emulator state checks do not prove audible pitch quality or real-device interruptions."]}
    if args.apk:
        adb("install","-r",str(args.apk.resolve()))
    try:
        adb("shell","am","start","-W","-n","art.lazying.musia/.MainActivity")
        time.sleep(3)
        capture("library")
        click("Practice")
        click("First Pulse")
        capture("first-pulse")
        click("Play")
        click("O open / X muted",scroll=True)
        capture("guitar-shape")
        evidence["checks"].append("Native curated guitar diagram is visible in Play mode")
        click("Play",description=True,scroll=True)
        time.sleep(2)
        assert_playing("foreground")
        evidence["checks"].append("Native First Pulse loads and Media3 reaches PLAYING")
        capture("playing")
        adb("shell","input","keyevent","KEYCODE_HOME")
        time.sleep(1)
        assert_playing("background")
        evidence["checks"].append("Media3 remains PLAYING after Home")
        adb("shell","input","keyevent","KEYCODE_SLEEP")
        time.sleep(2)
        assert_playing("screen-off")
        evidence["checks"].append("Media3 remains PLAYING with emulator display asleep")
        (args.output/"result.json").write_text(json.dumps(evidence,indent=2)+"\n")
        print(json.dumps(evidence,indent=2))
    except Exception:
        capture("failure")
        (args.output/"logcat.txt").write_text(adb("logcat","-d","-t","400"))
        raise
    finally:
        adb("shell","input","keyevent","KEYCODE_WAKEUP")
        adb("shell","am","force-stop","art.lazying.musia")


if __name__ == "__main__":
    main()
