#!/usr/bin/env python3
"""Capture genuine native store screenshots on one explicitly owned simulator.

Runs on a Mac with an existing Xcode/runtime. No signing, uploads, simulator
creation, profile changes or image reconstruction. The selected simulator is
shut down after the bounded test, including on failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess

from storelib import ROOT, RUNTIME, GuardError, lock, now, private_dir, require, write_private


def run(command, log, timeout):
    with log.open("wb") as handle:
        os.chmod(log, 0o600)
        process = subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            status = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=15)
            raise
    require(status == 0, f"Native capture command failed; inspect {log.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True)
    parser.add_argument("--name", required=True, choices=["iphone", "ipad"])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--attempt", default="1", help="Unique capture attempt; existing evidence is never overwritten")
    args = parser.parse_args()
    require(platform.system() == "Darwin", "Native screenshot capture needs macOS")
    require(re.fullmatch(r"[A-Za-z0-9_-]{1,40}", args.attempt) is not None, "Use a short alphanumeric attempt name")
    name = f"{args.name}-{args.attempt}"
    output = args.output.resolve()
    require(output.is_relative_to(RUNTIME.resolve()), "Capture output must be in Musia's private runtime")
    private_dir(output)
    devices = json.loads(subprocess.check_output(["xcrun", "simctl", "list", "devices", "available", "--json"]))
    matches = [row for group in devices["devices"].values() for row in group if row["udid"] == args.device]
    require(len(matches) == 1 and matches[0]["name"].startswith("Musia-Store-"), "Select an existing Musia-Store simulator")
    require(matches[0]["state"] == "Shutdown", "Capture requires a stopped owned simulator")
    result = output / f"{name}.xcresult"
    receipt_path = output / f"{name}-capture.json"
    require(not result.exists() and not receipt_path.exists(), "Do not overwrite prior native capture evidence")
    source = ROOT / "apps/ios/Musia"
    hashes = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(source.rglob("*")) if p.is_file()}
    receipt = {"started": now(), "device": matches[0], "app_sources": hashes,
               "xcode": subprocess.check_output(["xcodebuild", "-version"], text=True).strip(),
               "state": "started", "binary_uploaded": False, "screenshots_visually_reviewed": False}
    with lock("native-screenshot-capture"):
        write_private(receipt_path, receipt)
        try:
            run(["xcrun", "simctl", "boot", args.device], output / f"{name}-boot.log", 90)
            run(["xcrun", "simctl", "bootstatus", args.device, "-b"], output / f"{name}-bootstatus.log", 240)
            run(["xcodebuild", "test", "-project", str(ROOT / "apps/ios/Musia.xcodeproj"),
                 "-scheme", "Musia", "-configuration", "Release", "-sdk", "iphonesimulator",
                 "-destination", f"platform=iOS Simulator,id={args.device}",
                 "-derivedDataPath", str(output / "DerivedData"), "-resultBundlePath", str(result),
                 "-jobs", "2", "-parallel-testing-enabled", "NO", "-maximum-concurrent-test-simulator-destinations", "1",
                 "-only-testing:MusiaUITests/PracticeSmokeTests/testStoreScreenshots",
                 "CODE_SIGNING_ALLOWED=NO", "CODE_SIGNING_REQUIRED=NO",
                 "ENABLE_TESTABILITY=YES", "ONLY_ACTIVE_ARCH=YES"], output / f"{name}-test.log", 600)
            run(["xcrun", "xcresulttool", "export", "attachments", "--path", str(result),
                 "--output-path", str(output / f"{name}-attachments")], output / f"{name}-export.log", 90)
            receipt["state"] = "captured_needs_visual_review"
        except (GuardError, subprocess.TimeoutExpired):
            receipt["state"] = "failed_or_timed_out"
            raise
        finally:
            stopped = subprocess.run(["xcrun", "simctl", "shutdown", args.device], capture_output=True, timeout=60)
            receipt["shutdown_exit"] = stopped.returncode
            receipt["finished"] = now()
            write_private(receipt_path, receipt)
    print(json.dumps({"state": receipt["state"], "output": str(output), "device": args.device}))


if __name__ == "__main__":
    main()
