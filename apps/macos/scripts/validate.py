#!/usr/bin/env python3
"""Static release invariants; native compiler/runtime tests are still required."""
from pathlib import Path
import json
import plistlib
import struct

ROOT = Path(__file__).resolve().parents[1]
resources = ROOT / "Musia/Resources"
info = plistlib.loads((resources / "Info.plist").read_bytes())
assert info["LSApplicationCategoryType"] == "public.app-category.music"
assert info["ITSAppUsesNonExemptEncryption"] is False
assert "NSMicrophoneUsageDescription" not in info
assert "NSAppTransportSecurity" not in info
assert plistlib.loads((resources / "Musia.entitlements").read_bytes()) == {
    "com.apple.security.app-sandbox": True,
    "com.apple.security.network.client": True,
    "com.apple.security.files.user-selected.read-write": True,
}
project = (ROOT / "Musia.xcodeproj/project.pbxproj").read_text()
assert "PRODUCT_BUNDLE_IDENTIFIER = art.lazying.musia;" in project
assert "MACOSX_DEPLOYMENT_TARGET = 14.0;" in project
assert "MUSIA_MAC_PROFILE" in project
assert "SUPPORTS_MACCATALYST" not in project
for base in [ROOT / "Musia", ROOT / "Tests", ROOT.parent / "ios/Musia/Core",
             ROOT.parent / "ios/Musia/Views", ROOT.parent / "ios/Musia/Services"]:
    for path in base.rglob("*.swift"):
        assert path.name in project, f"Source missing from project: {path}"
        text = path.read_text()
        assert "WKWebView" not in text and "import WebKit" not in text
review = (ROOT / "Musia/MacReview.swift").read_text()
assert review.startswith("#if DEBUG\n") and review.rstrip().endswith("#endif")
icons = resources / "Assets.xcassets/AppIcon.appiconset"
images = json.loads((icons / "Contents.json").read_text())["images"]
assert len(images) == 10
for item in images:
    data = (icons / item["filename"]).read_bytes()
    size = int(item["size"].split("x")[0]) * int(item["scale"][0])
    assert item["idiom"] == "mac" and struct.unpack_from(">II", data, 16) == (size, size)
print("PASS: native Mac sources, sandbox, privacy boundary, Debug-only QA and ten icon slots")
