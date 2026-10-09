#!/usr/bin/env python3
"""Native Agent/Studio edit check on one owned emulator; no sign-in or render."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert re.fullmatch(r"emulator-\d+", args.serial)
    adb_path = str(Path.home() / "Android/Sdk/platform-tools/adb")
    def adb(*command):
        return subprocess.check_output([adb_path, "-s", args.serial, *command], timeout=60)
    assert adb("emu", "avd", "name").decode().startswith("Musia_")
    args.output.mkdir(parents=True, exist_ok=False)
    def tree():
        adb("shell", "uiautomator", "dump", "/sdcard/musia-workspace.xml")
        return ET.fromstring(adb("exec-out", "cat", "/sdcard/musia-workspace.xml"))
    def find(label):
        for _ in range(8):
            rows = [n for n in tree().iter("node") if label in (n.get("text"), n.get("content-desc"))]
            if len(rows) == 1:
                return rows[0]
            time.sleep(.3)
        raise AssertionError("Missing or ambiguous control: " + label)
    def tap_node(node):
        assert node.get("enabled") == "true"
        a,b,c,d = map(int, re.findall(r"\d+", node.get("bounds")))
        assert c > a and d > b
        adb("shell", "input", "tap", str((a+c)//2), str((b+d)//2))
    def tap(label):
        tap_node(find(label))
    def capture(name):
        (args.output / (name + ".png")).write_bytes(adb("exec-out", "screencap", "-p"))
        (args.output / (name + ".xml")).write_bytes(ET.tostring(tree()))
    adb("shell", "am", "force-stop", "art.lazying.musia")
    adb("shell", "am", "start", "-W", "-n", "art.lazying.musia/.MainActivity")
    tap("Create")
    find("What would you like to make?")
    find("Message Musia")
    assert find("Send message").get("enabled") == "false"
    capture("agent-default")
    tap("Studio")
    root = tree()
    field = next(n for n in root.iter("node") if n.get("class") == "android.widget.EditText" and
                 any(c.get("text") == "Title" for c in n.iter("node")))
    assert not field.get("text"), "Use an empty QA guest workspace; preserve existing drafts"
    tap_node(field)
    adb("shell", "input", "text", "Morning%sLight")
    adb("shell", "input", "keyevent", "KEYCODE_BACK")
    root = tree()
    actual = next(n.get("text") for n in root.iter("node") if n.get("class") == "android.widget.EditText" and n.get("text"))
    capture("studio-edit")
    tap("Agent")
    find("Message Musia")
    tap("Studio")
    assert any(n.get("class") == "android.widget.EditText" and n.get("text") == actual for n in tree().iter("node"))
    capture("studio-preserved")
    result = {"state":"passed", "serial":args.serial,
              "checks":["Agent default", "sign-in required to send", "Studio editable", "shared draft survives tab switches"],
              "limitations":["Signed QA APK; guest UI only, not authenticated chat or Play-installed execution"],
              "rendered":False, "purchased":False}
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
