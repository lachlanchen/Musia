#!/usr/bin/env python3
"""Bounded metadata-only Apple host inventory. Run only in an admitted read slot.

Does not unlock/import credentials, boot devices, acquire a guard, or build.
Outputs paths and metadata, never credential contents.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import time


def metadata(path):
    path = Path(path).expanduser()
    if not os.path.lexists(path):
        return {"path": str(path), "exists": False}
    info = path.lstat()
    return {"path": str(path), "exists": True, "regular": stat.S_ISREG(info.st_mode),
            "symlink": stat.S_ISLNK(info.st_mode), "uid": info.st_uid,
            "mode": oct(stat.S_IMODE(info.st_mode)), "device": info.st_dev, "inode": info.st_ino}


def collect(config_path):
    deadline = time.monotonic() + 75
    def call(argv, limit=8, env=None):
        left = deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError("Preflight deadline")
        result = subprocess.run(argv, capture_output=True, text=True,
                                timeout=min(limit, left), env=env)
        if len(result.stdout) > 2_000_000:
            raise RuntimeError("Inventory exceeds bounded output; cannot claim complete")
        return {"exit": result.returncode, "stdout": result.stdout,
                "stderr": result.stderr[:1000]}
    if platform.system() != "Darwin":
        raise RuntimeError("Use an admitted Mac read slot")
    config_path = Path(config_path).expanduser()
    info = metadata(config_path)
    if not info.get("regular") or info.get("symlink") or info.get("uid") != os.getuid() or int(info["mode"], 8) & 0o077:
        raise RuntimeError("Private app config missing or unsafe")
    cfg = json.loads(config_path.read_text())
    if cfg.get("bundle_id") != "art.lazying.musia" or cfg.get("apple_team") != "Q8M2S2FY77":
        raise RuntimeError("Wrong app configuration")
    guard = Path("/tmp/lazyingart-apple-build.lock")
    result = {"at": dt.datetime.now(dt.timezone.utc).isoformat(), "read_only": True,
              "host": platform.node(), "architecture": platform.machine(), "uid": os.getuid(),
              "guard": metadata(guard), "config": info,
              "disk_free_bytes": shutil.disk_usage(Path.home()).free}
    result["hardware"] = call(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"])
    result["memory"] = call(["memory_pressure", "-Q"])
    result["swap"] = call(["sysctl", "vm.swapusage"])
    result["selection"] = call(["xcode-select", "-p"])
    process = call(["ps", "-axo", "pid=,ppid=,pgid=,lstart=,comm="])
    if process["exit"] != 0:
        raise RuntimeError("Process inventory failed")
    result["active_tools"] = [line for line in process["stdout"].splitlines()
        if re.search(r"(?:xcodebuild|swift-frontend|clang|ld|actool|ibtool|xctest|codesign|productbuild|pkgbuild|altool|iTMSTransporter|Musia|Simulator)(?:$|[ /])", line)]
    # Do not query tools through a live peer SDK or enumerate active devices.
    if result["guard"]["exists"] or result["active_tools"]:
        result["state"] = "conflict_no_toolchain_probe"
        return result
    developer = Path(cfg.get("xcode_developer_dir", ""))
    result["configured_developer"] = str(developer)
    result["installed_xcodes"] = [str(p) for base in [Path("/Applications"), Path("/usr/local/echomind-formal-xcode")]
                                 for p in base.glob("Xcode*.app")]
    if developer.is_dir():
        env = dict(os.environ, DEVELOPER_DIR=str(developer))
        result["xcode"] = call([str(developer / "usr/bin/xcodebuild"), "-version"], env=env)
        result["runtimes"] = call(["xcrun", "simctl", "list", "runtimes", "--json"], limit=12, env=env)
        result["devices"] = call(["xcrun", "simctl", "list", "devices", "available", "--json"], limit=12, env=env)
    result["signing_inputs"] = {k: metadata(cfg[k]) for k in
        ["apple_keychain", "apple_profile_path", "apple_watch_profile_path"] if k in cfg}
    result["keychain_search"] = call(["security", "list-keychains", "-d", "user"])
    if cfg.get("apple_keychain"):
        identities = call(["security", "find-identity", "-v", "-p", "codesigning", cfg["apple_keychain"]])
        result["configured_signer_available"] = bool(cfg.get("apple_certificate_sha1")) and cfg["apple_certificate_sha1"] in identities["stdout"]
    result["guard_after"] = metadata(guard)
    result["state"] = "metadata_collected_not_build_admission"
    result["finished"] = dt.datetime.now(dt.timezone.utc).isoformat()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    print(json.dumps(collect(args.config), indent=2))
