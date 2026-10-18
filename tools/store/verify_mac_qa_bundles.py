#!/usr/bin/env python3
"""Read-only pre-launch check for the isolated Mac hosted-test app."""
import argparse
import json
from pathlib import Path
import plistlib
import subprocess
import sys


QA_PREFIX = "art.lazying.musia.compatibilityqa"
BUNDLES = {
    "app": ("Contents/Info.plist", QA_PREFIX, "APPL"),
    "core": ("Contents/Frameworks/MusiaCore.framework/Resources/Info.plist",
             QA_PREFIX + ".core", "FMWK"),
    "tests": ("Contents/PlugIns/MusiaMacTests.xctest/Contents/Info.plist",
              QA_PREFIX + ".mactests", "BNDL"),
}


def check_bundle_ids(app):
    app = Path(app).resolve(strict=True)
    identities = {}
    for name, (relative, expected, package_type) in BUNDLES.items():
        path = (app / relative).resolve(strict=True)
        if app not in path.parents:
            raise ValueError(f"{name}: plist resolves outside the QA app")
        info = plistlib.loads(path.read_bytes())
        if not isinstance(info, dict):
            raise ValueError(f"{name}: expected a plist dictionary")
        actual = info.get("CFBundleIdentifier")
        if actual != expected:
            raise ValueError(f"{name}: expected {expected}, found {actual!r}")
        if info.get("CFBundlePackageType") != package_type:
            raise ValueError(f"{name}: wrong bundle package type")
        identities[name] = actual
    return identities


def check_entitlements(entitlements):
    if not isinstance(entitlements, dict):
        raise ValueError("QA entitlements must be a plist dictionary")
    if entitlements.get("com.apple.security.app-sandbox") is not True:
        raise ValueError("QA app must be sandboxed")
    for key in ("keychain-access-groups", "com.apple.security.application-groups"):
        if entitlements.get(key):
            raise ValueError(f"QA app must not share data through {key}")


def verify(app):
    identities = check_bundle_ids(app)
    raw = subprocess.check_output(
        ["codesign", "-d", "--entitlements", ":-", str(app)],
        stderr=subprocess.DEVNULL, timeout=20)
    check_entitlements(plistlib.loads(raw))
    return {"bundle_ids": identities, "sandbox": True, "shared_groups": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.app)
    except (OSError, ValueError, plistlib.InvalidFileException,
            subprocess.SubprocessError) as error:
        print(f"Mac QA identity check failed: {error}", file=sys.stderr)
        return 65
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
