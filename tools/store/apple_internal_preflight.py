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
import signal
import stat
import time

from apple_read_child import ReadCommands, clock, global_environment
from apple_host_busy import parse_processes, own_chain, classify_processes


def metadata(path):
    path = Path(path).expanduser()
    if not os.path.lexists(path):
        return {"path": str(path), "exists": False}
    info = path.lstat()
    return {"path": str(path), "exists": True, "regular": stat.S_ISREG(info.st_mode),
            "symlink": stat.S_ISLNK(info.st_mode), "uid": info.st_uid,
            "mode": oct(stat.S_IMODE(info.st_mode)), "device": info.st_dev, "inode": info.st_ino}


def collect(config_path, commands):
    def call(argv, limit=8, env=None):
        result = commands.run(argv, limit, env=env)
        if result["exit"] != 0:
            raise RuntimeError("Required metadata command failed: " + Path(argv[0]).name)
        return result
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
    result["selection"] = call(["xcode-select", "-p"], env=global_environment())
    ps_format = "pid=,ppid=,pgid=,lstart=,ucomm="
    rows = parse_processes(call(["ps", "-axo", ps_format])["stdout"])
    chain = own_chain(rows, os.getpid())
    fresh = parse_processes(call(["ps", "-p", ",".join(map(str, sorted(chain))), "-o", ps_format])["stdout"])
    result["active_tools"] = classify_processes(rows, chain, fresh)
    # Do not query tools through a live peer SDK or enumerate active devices.
    if result["guard"]["exists"] or result["active_tools"]:
        raise RuntimeError("Host occupied; no toolchain probe")
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
    result["mac_profile"] = metadata(config_path.parent / "macos-20261004/Musia_Mac_App_Store.provisionprofile")
    result["keychain_search"] = call(["security", "list-keychains", "-d", "user"])
    if cfg.get("apple_keychain"):
        identities = call(["security", "find-identity", "-v", "-p", "codesigning", cfg["apple_keychain"]])
        result["configured_signer_available"] = bool(cfg.get("apple_certificate_sha1")) and cfg["apple_certificate_sha1"] in identities["stdout"]
        installers = call(["security", "find-identity", "-v", "-p", "basic", cfg["apple_keychain"]])
        result["mac_installer_available"] = "3rd Party Mac Developer Installer: LazyingArt LLC (Q8M2S2FY77)" in installers["stdout"]
    result["guard_after"] = metadata(guard)
    after = parse_processes(call(["ps", "-axo", ps_format])["stdout"])
    chain_after = own_chain(after, os.getpid())
    fresh_after = parse_processes(call(["ps", "-p", ",".join(map(str, sorted(chain_after))), "-o", ps_format])["stdout"])
    result["active_tools_after"] = classify_processes(after, chain_after, fresh_after)
    result["state"] = "metadata_collected_not_build_admission"
    result["finished"] = dt.datetime.now(dt.timezone.utc).isoformat()
    return result


def qualify(result):
    uuid = re.search(r'"IOPlatformUUID" = "([^"]+)"', result["hardware"]["stdout"])
    assert uuid and uuid[1] == "0685A36A-0F51-5C5E-B2EA-A56B06B9E36D", "Wrong KVM identity"
    assert result["uid"] == 501 and result["architecture"] == "x86_64", "Wrong host account/architecture"
    assert not result["guard"]["exists"] and not result["guard_after"]["exists"] and not result["active_tools"] and not result["active_tools_after"], "Occupied"
    free = re.search(r"free percentage:\s*(\d+)%", result["memory"]["stdout"])
    swap = result["swap"]["stdout"]
    total = float(re.search(r"total = ([\d.]+)M", swap)[1])
    used = float(re.search(r"used = ([\d.]+)M", swap)[1])
    assert free and int(free[1]) >= 40 and (total == used == 0 or total > 0 and used / total <= .75), "Resource gate"
    assert result["disk_free_bytes"] >= 30 * 1024 ** 3, "Disk gate"
    assert result.get("xcode") and result.get("runtimes") and result.get("devices"), "Incomplete SDK inventory"
    for key in ["apple_keychain", "apple_profile_path", "apple_watch_profile_path"]:
        item = result["signing_inputs"].get(key, {})
        assert item.get("regular") and item.get("uid") == 501 and not int(item["mode"], 8) & 0o077, "Missing or nonprivate signing input: " + key
    profile = result["mac_profile"]
    assert profile.get("regular") and profile.get("uid") == 501 and not int(profile["mode"], 8) & 0o077, "Mac profile missing or unsafe"
    assert result.get("configured_signer_available") and result.get("mac_installer_available"), "Signing identity unavailable while locked; no unlock performed"
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    commands = ReadCommands(clock() + 60)
    def interrupted(*_):
        signal.setitimer(signal.ITIMER_REAL, 0)
        raise TimeoutError("Whole read interrupted or execution budget expired")
    for sig in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM, signal.SIGHUP): signal.signal(sig, interrupted)
    signal.setitimer(signal.ITIMER_REAL, 45)
    result = {}
    try:
        result = collect(args.config, commands)
        result["read_children"] = commands.records
        qualify(result)
        print(json.dumps(result, indent=2), flush=True)
    except BaseException:
        import sys
        print(json.dumps({**result, "state": "incomplete", "read_children": commands.records}), file=sys.stderr, flush=True)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
