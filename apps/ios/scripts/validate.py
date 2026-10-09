#!/usr/bin/env python3
"""Static checks only. This is not a substitute for swift test / xcodebuild test."""
import json
import plistlib
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
import zlib

ROOT = Path(__file__).resolve().parents[1]
resources = ROOT / "Musia/Resources"
with (resources / "Info.plist").open("rb") as source:
    info = plistlib.load(source)
assert info["CFBundleDisplayName"] == "Musia"
assert info["UIBackgroundModes"] == ["audio"]
assert "NSMicrophoneUsageDescription" not in info
assert "NSAppTransportSecurity" not in info
with (resources / "PrivacyInfo.xcprivacy").open("rb") as source:
    privacy = plistlib.load(source)
assert privacy["NSPrivacyTracking"] is False
collected = privacy["NSPrivacyCollectedDataTypes"]
assert {item["NSPrivacyCollectedDataType"] for item in collected} == {
    "NSPrivacyCollectedDataTypeName", "NSPrivacyCollectedDataTypeUserID",
    "NSPrivacyCollectedDataTypeOtherUserContent", "NSPrivacyCollectedDataTypePurchaseHistory",
    "NSPrivacyCollectedDataTypeProductInteraction",
}
assert all(item["NSPrivacyCollectedDataTypeLinked"] and not item["NSPrivacyCollectedDataTypeTracking"]
           and item["NSPrivacyCollectedDataTypePurposes"] == ["NSPrivacyCollectedDataTypePurposeAppFunctionality"]
           for item in collected)
assert privacy["NSPrivacyAccessedAPITypes"] == [{
    "NSPrivacyAccessedAPIType": "NSPrivacyAccessedAPICategoryUserDefaults",
    "NSPrivacyAccessedAPITypeReasons": ["CA92.1"],
}]
for path in resources.rglob("Contents.json"):
    contents = json.loads(path.read_text())
    for image in contents.get("images", []):
        if "filename" in image:
            assert (path.parent / image["filename"]).is_file(), path
for name, expected in [("AppIcon.appiconset/AppIcon.png", 1024),
                       ("FirstPulseCover.imageset/FirstPulseCover.png", 512)]:
    data = (resources / "Assets.xcassets" / name).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    offset = 8
    compressed = b""
    while offset < len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        crc = struct.unpack_from(">I", data, offset + 8 + length)[0]
        assert zlib.crc32(kind + payload) & 0xffffffff == crc
        if kind == b"IHDR":
            assert struct.unpack_from(">II", payload) == (expected, expected)
            assert payload[8:10] == bytes([8, 2]), "Opaque RGB icons only"
        if kind == b"IDAT":
            compressed += payload
        offset += length + 12
    assert len(zlib.decompress(compressed)) == expected * (1 + expected * 3)
project = ROOT / "Musia.xcodeproj/project.pbxproj"
project_text = project.read_text()
assert "PRODUCT_BUNDLE_IDENTIFIER = art.lazying.musia;" in project_text
assert "MUSIA_APP_PROFILE" in project_text
scheme = ET.parse(ROOT / "Musia.xcodeproj/xcshareddata/xcschemes/Musia.xcscheme")
assert scheme.find(".//TestableReference/BuildableReference").attrib["BlueprintName"] == "MusiaTests"
swift_files = sorted((ROOT / "Musia").rglob("*.swift")) + sorted((ROOT / "Tests").rglob("*.swift"))
for path in swift_files:
    text = path.read_text()
    assert "WKWebView" not in text and "import WebKit" not in text
    assert path.name in project_text, f"Not in checked-in project: {path}"
print(f"PASS: manifests, resources, scheme, bundle identity, {len(swift_files)} Swift file references; no WebKit")

try:
    import tree_sitter
    import tree_sitter_swift
except ImportError:
    print("SKIP: optional Swift syntax parser unavailable; compiler tests still required")
else:
    parser = tree_sitter.Parser(tree_sitter.Language(tree_sitter_swift.language()))
    for path in swift_files + [ROOT / "Package.swift"]:
        tree = parser.parse(path.read_bytes())
        if tree.root_node.has_error:
            def errors(node):
                if node.type == "ERROR" or node.is_missing:
                    print(path.relative_to(ROOT), node.start_point, node.type)
                for child in node.children:
                    errors(child)
            errors(tree.root_node)
            raise AssertionError(f"Swift syntax parse failed: {path}")
    print(f"PASS: Swift syntax parse ({len(swift_files) + 1} files); NOT a compiler/type check")
