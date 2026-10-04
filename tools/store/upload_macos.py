#!/usr/bin/env python3
"""Validate one signed Musia Mac installer and upload once, never submit review."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import sys
import tempfile

from storelib import BUNDLE, TEAM, Apple, RUNTIME, config, digest, lock, now, require, run, write_private


def check_altool_result(raw):
    """altool can report validation failure with process exit status zero."""
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        require(False, "Unrecognized Apple response; inspect private log before retrying")
    require(isinstance(value, dict) and not value.get("product-errors") and not value.get("errors")
            and bool(value.get("success-message")), "Apple did not confirm success; inspect private log")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--build", required=True)
    parser.add_argument("--execute-upload", action="store_true")
    args = parser.parse_args()
    require(sys.platform == "darwin", "Run on the authorized Mac")
    package = args.package.resolve(strict=True)
    require(package.suffix == ".pkg" and digest(package) == args.sha256, "Installer checksum mismatch")
    cfg = config()
    folder = RUNTIME / "macos-uploads" / args.sha256
    with lock("upload-macos"):
        signature = run(["pkgutil", "--check-signature", package])
        require(b"3rd Party Mac Developer Installer: LazyingArt LLC (Q8M2S2FY77)" in signature,
                "Wrong installer signer")
        write_private(folder / "installer-signature.txt", signature)
        with tempfile.TemporaryDirectory(prefix="musia-mac-inspect-") as temporary:
            expanded = Path(temporary) / "expanded"
            run(["pkgutil", "--expand-full", package, expanded])
            apps = list(expanded.rglob("Musia.app"))
            require(len(apps) == 1, "Expected one Musia app")
            app = apps[0]
            info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
            require(info["CFBundleIdentifier"] == BUNDLE and info["CFBundleShortVersionString"] == args.version
                    and info["CFBundleVersion"] == args.build, "Installer identity/version mismatch")
            run(["codesign", "--verify", "--deep", "--strict", app])
            entitlements = plistlib.loads(run(["codesign", "-d", "--entitlements", ":-", app]))
            require(entitlements.get("com.apple.security.app-sandbox") is True
                    and entitlements.get("com.apple.developer.team-identifier") == TEAM
                    and entitlements.get("com.apple.application-identifier") == TEAM + "." + BUNDLE
                    and not entitlements.get("com.apple.security.get-task-allow", False),
                    "Invalid sandbox or distribution entitlements")
            prefix = Path(temporary) / "signer"
            run(["codesign", "-d", "--extract-certificates=" + str(prefix), app])
            signer = hashlib.sha1(Path(str(prefix) + "0").read_bytes()).hexdigest().upper()
            require(signer == cfg["apple_certificate_sha1"], "Unexpected application signer")
            binary = app / "Contents/MacOS/Musia"
            run(["lipo", binary, "-verify_arch", "arm64", "x86_64"])
            require(b"--musia-review" not in binary.read_bytes(), "Debug review harness leaked into release")
            for path in [app, *app.rglob("*")]:
                if not path.is_symlink():
                    required = 0o055 if path.is_dir() else 0o044
                    require(path.stat().st_mode & required == required, "Installed bundle has private-only permissions")
        receipt = {"at": now(), "platform": "MAC_OS", "bundle_id": BUNDLE, "version": args.version,
                   "build": args.build, "package_sha256": args.sha256, "signer_sha1": signer,
                   "architectures": ["arm64", "x86_64"], "entitlements": entitlements}
        write_private(folder / "inspection.json", receipt)
        key = Path(cfg["asc_key_path"])
        env = dict(os.environ, API_PRIVATE_KEYS_DIR=str(key.parent))
        common = ["--type", "macos", "--file", package, "--apiKey", cfg["asc_key_id"],
                  "--apiIssuer", cfg["asc_issuer"], "--output-format", "json"]
        checked = run(["xcrun", "altool", "--validate-app", *common], env=env, log=folder / "validation.json")
        check_altool_result(checked)
        print("Signed universal installer passed local inspection and Apple validation", flush=True)
        if not args.execute_upload:
            return
        require(not (folder / "upload-started.json").exists(), "Upload attempted already; reconcile provider before any retry")
        app = Apple().app()
        existing = Apple().rows(f"/v1/builds?filter[app]={app['id']}&filter[version]={args.build}&include=preReleaseVersion")
        require(not existing, "Build number exists on this app; reconcile before uploading")
        write_private(folder / "upload-started.json", receipt)
        uploaded = run(["xcrun", "altool", "--upload-app", *common], env=env, log=folder / "upload.json")
        check_altool_result(uploaded)
        write_private(folder / "upload-accepted.json", receipt)
        print("Apple accepted the upload; processing and review are separate steps")


if __name__ == "__main__":
    main()
