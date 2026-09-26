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
    parser.add_argument("--layout-only", action="store_true", help="Check mini-player/navigation at phone and tablet sizes")
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

    def verify_layouts():
        original_size = adb("shell", "wm", "size")
        original_density = adb("shell", "wm", "density")
        original_font = adb("shell", "settings", "get", "system", "font_scale")
        size_override = re.search(r"Override size: (\d+x\d+)", original_size)
        density_override = re.search(r"Override density: (\d+)", original_density)
        try:
            click("Back", description=True)
            for label, width, height, density, scale in [
                ("phone", 1080, 2400, 420, 1),
                ("phone-large-text", 1080, 2400, 420, 1.5),
                ("tablet", 1600, 2560, 240, 1),
                ("tablet-landscape-large-text", 2560, 1600, 240, 1.5),
            ]:
                adb("shell", "wm", "size", f"{width}x{height}")
                adb("shell", "wm", "density", str(density))
                adb("shell", "settings", "put", "system", "font_scale", str(scale))
                time.sleep(2)
                for destination in ["History", "Settings", "Songs"]:
                    click(destination)
                root, _ = screen()
                parents = {child: parent for parent in root.iter() for child in parent}

                def control_bounds(text, description=False):
                    key = "content-desc" if description else "text"
                    target = next(n for n in root.iter("node") if n.get(key) == text)
                    while target.get("clickable") != "true" and target.get("selected") != "true" and target in parents:
                        target = parents[target]
                    return tuple(map(int, re.findall(r"\d+", target.get("bounds", ""))))

                mini = control_bounds("First Pulse")
                assert len(mini) == 4 and mini[2] > mini[0] and mini[3] > mini[1], (label, mini)
                assert 0 <= mini[0] < mini[2] <= width and 0 <= mini[1] < mini[3] <= height
                for destination in ["Songs", "Practice", "History", "Settings"]:
                    bounds = control_bounds(destination)
                    assert len(bounds) == 4 and bounds[2] > bounds[0] and bounds[3] > bounds[1]
                    assert mini[3] <= bounds[1] < bounds[3] <= height, (label, mini, destination, bounds)
                capture("navigation-" + label)
                evidence["checks"].append(f"Mini-player above all four tappable tabs: {label}")
        finally:
            adb("shell", "wm", "size", size_override.group(1) if size_override else "reset")
            adb("shell", "wm", "density", density_override.group(1) if density_override else "reset")
            if original_font == "null":
                adb("shell", "settings", "delete", "system", "font_scale")
            else:
                adb("shell", "settings", "put", "system", "font_scale", original_font)

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
        if args.layout_only:
            verify_layouts()
            (args.output/"result.json").write_text(json.dumps(evidence,indent=2)+"\n")
            print(json.dumps(evidence,indent=2))
            return
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
