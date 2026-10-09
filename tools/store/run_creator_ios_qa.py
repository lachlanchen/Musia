#!/usr/bin/env python3
"""Run genuine creator UI tests on one stopped Musia-owned simulator, never upload."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from capture_ios_review import run
from storelib import ROOT, RUNTIME, digest, lock, now, private_dir, require, source_sha, write_private


CASES = {
    "account": "testCreatorAccountAndCommunity",
    "products": "testCreatorProducts",
    "private-playback": "testSignedInPrivatePlayback",
    "workspace": "testAgentStudioWorkspace",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True)
    parser.add_argument("--attempt", required=True, type=int)
    parser.add_argument("--case", choices=CASES, default="account",
                        help="account: signed out -> signed in; products: capture real prices, preserve session; "
                             "private-playback: signed in -> signed out; no case purchases")
    parser.add_argument("--build-receipt", required=True, type=Path)
    parser.add_argument("--developer-dir", type=Path,
                        help="Existing Xcode; otherwise use DEVELOPER_DIR or xcode-select")
    args = parser.parse_args()
    require(sys.platform == "darwin", "Use the authorized Mac")
    require(args.attempt > 0, "Attempt must be positive")
    if args.developer_dir:
        require(args.developer_dir.is_dir(), "Selected Xcode is missing")
        os.environ["DEVELOPER_DIR"] = str(args.developer_dir.resolve())
    require(subprocess.run(["pgrep", "-x", "xcodebuild"], capture_output=True).returncode != 0,
            "Peer Apple build/test active; not starting a second job")
    require(subprocess.run(["pgrep", "-x", "swift-frontend"], capture_output=True).returncode != 0,
            "Peer Swift job active; not starting a second job")
    devices = json.loads(subprocess.check_output(["xcrun", "simctl", "list", "devices", "available", "--json"]))
    matches = [d for rows in devices["devices"].values() for d in rows if d["udid"] == args.device]
    require(len(matches) == 1 and matches[0]["name"].startswith(("Musia ", "Musia-"))
            and matches[0]["state"] == "Shutdown", "Need an existing stopped Musia-owned simulator")
    import shutil
    require(shutil.disk_usage(ROOT).free > 4 * 1024 ** 3, "Less than 4 GiB free; preserve peer data and free owned obsolete caches first")
    before = source_sha("ios")
    build_path = args.build_receipt.resolve(strict=True)
    require(build_path.is_relative_to(RUNTIME.resolve()), "Use a private Musia build receipt")
    build = json.loads(build_path.read_text())
    require(build["state"] == "signed" and build["source_sha256"] == before, "App source differs from signed candidate")
    require(digest(build_path.parent / build["artifact"]) == build["artifact_sha256"], "Candidate IPA changed")
    out = RUNTIME / "creator-apple-20261009" / f"ios-ui-r{args.attempt}"
    require(not out.exists(), "Keep previous evidence; choose a fresh attempt number")
    private_dir(out)
    result = out / "creator.xcresult"
    receipt = {"at": now(), "device": matches[0], "source_sha256": before,
               "build_receipt_sha256": digest(build_path), "artifact_sha256": build["artifact_sha256"],
               "ui_test_sha256": digest(ROOT / "tools/store/CreatorNativeUITests.swift"),
               "case": args.case,
               "state": "started", "visually_reviewed": False, "production_qualified": False,
               "purchase_attempted": False, "upload_attempted": False}
    with lock("creator-ios-ui"):
        write_private(out / "receipt.json", receipt)
        booted = False
        try:
            run(["/usr/bin/ruby", str(ROOT / "tools/store/prepare_creator_ui_project.rb"), str(out / "project")],
                out / "project.log", 60)
            run(["xcrun", "simctl", "boot", args.device], out / "boot.log", 90)
            booted = True
            run(["xcrun", "simctl", "bootstatus", args.device, "-b"], out / "bootstatus.log", 240)
            run(["xcodebuild", "test", "-project", str(out / "project/MusiaCreatorQA.xcodeproj"),
                 "-scheme", "MusiaCreatorQA", "-configuration", "Debug", "-sdk", "iphonesimulator",
                 "-destination", f"platform=iOS Simulator,id={args.device}",
                 "-derivedDataPath", str(out / "DerivedData"), "-resultBundlePath", str(result),
                 "-jobs", "2", "-parallel-testing-enabled", "NO",
                 "-collect-test-diagnostics", "never", "-test-timeouts-enabled", "YES",
                 "-maximum-test-execution-time-allowance", "420",
                 "-maximum-concurrent-test-simulator-destinations", "1",
                 "-only-testing:MusiaUITests/CreatorNativeUITests/" + CASES[args.case],
                 "CODE_SIGNING_ALLOWED=YES", "CODE_SIGNING_REQUIRED=YES", "CODE_SIGN_IDENTITY=-",
                 "ONLY_ACTIVE_ARCH=YES",
                 "COMPILER_INDEX_STORE_ENABLE=NO"], out / "test.log", 720)
            require(source_sha("ios") == before, "Application source changed during QA")
            receipt["state"] = "automated_pass_needs_visual_review"
        except Exception:
            receipt["state"] = "failed_or_timed_out"
            raise
        finally:
            if result.exists():
                try:
                    run(["xcrun", "xcresulttool", "export", "attachments", "--path", str(result),
                         "--output-path", str(out / "attachments")], out / "export.log", 90)
                except Exception:
                    receipt["attachment_export_failed"] = True
            if booted:
                stopped = subprocess.run(["xcrun", "simctl", "shutdown", args.device], capture_output=True, timeout=60)
                receipt["owned_simulator_shutdown_exit"] = stopped.returncode
            receipt["finished"] = now()
            write_private(out / "receipt.json", receipt)
    print(json.dumps({"state": receipt["state"], "output": str(out)}))


if __name__ == "__main__":
    main()
