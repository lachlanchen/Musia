#!/usr/bin/env python3
"""Build the Mac asset catalog using the shared rounded icon master."""
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "ios/Musia/Resources/Assets.xcassets"
OUTPUT = ROOT / "Musia/Resources/Assets.xcassets"
OUTPUT.mkdir(parents=True, exist_ok=True)
(OUTPUT / "Contents.json").write_text(json.dumps({"info": {"author": "xcode", "version": 1}}, indent=2) + "\n")
shutil.copytree(SOURCE / "FirstPulseCover.imageset", OUTPUT / "FirstPulseCover.imageset", dirs_exist_ok=True)
icon = OUTPUT / "AppIcon.appiconset"
icon.mkdir(exist_ok=True)
subprocess.run(["node", str(ROOT.parent / "shared/scripts/export-icons.mjs"), "macos"], check=True)
images = []
for size in (16, 32, 128, 256, 512):
    for scale in (1, 2):
        name = f"icon-{size}@{scale}x.png"
        images.append({"idiom": "mac", "size": f"{size}x{size}", "scale": f"{scale}x", "filename": name})
(icon / "Contents.json").write_text(json.dumps({"images": images, "info": {"author": "xcode", "version": 1}}, indent=2) + "\n")
print("Mac icons and First Pulse artwork generated")
