#!/usr/bin/env python3
"""Build the Mac asset catalog from Musia's existing native raster artwork."""
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
images = []
for size in (16, 32, 128, 256, 512):
    for scale in (1, 2):
        name = f"icon-{size}@{scale}x.png"
        subprocess.run(["sips", "-z", str(size * scale), str(size * scale),
                        str(SOURCE / "AppIcon.appiconset/AppIcon.png"), "--out", str(icon / name)], check=True,
                       stdout=subprocess.DEVNULL)
        images.append({"idiom": "mac", "size": f"{size}x{size}", "scale": f"{scale}x", "filename": name})
(icon / "Contents.json").write_text(json.dumps({"images": images, "info": {"author": "xcode", "version": 1}}, indent=2) + "\n")
print("Mac icons and First Pulse artwork generated")
