#!/usr/bin/env python3
"""Run one admitted Apple job under the shared atomic-directory guard.

The queue owner must grant the slot first. This guard does not grant admission.
On interruption or uncertain descendants it retains the lock for owner recovery.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import uuid


class BuildGuard:
    def __init__(self, path, operation, slot_note):
        self.path = Path(path)
        self.token = uuid.uuid4().hex
        self.path.mkdir(mode=0o700)
        self.identity = self.path.stat().st_dev, self.path.stat().st_ino
        self.owner = {
            "protocol": 1, "host": socket.gethostname(), "app": "Musia",
            "thread": "019f0842-25ba-7bd2-9d4b-0b1c60d8a951", "token": self.token,
            "pid": os.getpid(), "process_start": subprocess.check_output(
                ["ps", "-p", str(os.getpid()), "-o", "lstart="], text=True).strip(),
            "acquired_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "checkout": str(Path.cwd()), "operation": operation, "slot_note": slot_note,
        }
        with (self.path / "owner.json").open("x") as handle:
            os.chmod(handle.name, 0o600)
            json.dump(self.owner, handle, indent=2)
            handle.flush(); os.fsync(handle.fileno())

    def release(self):
        info = self.path.lstat()
        if self.path.is_symlink() or (info.st_dev, info.st_ino) != self.identity:
            raise RuntimeError("Guard directory identity changed; retained")
        if json.loads((self.path / "owner.json").read_text()) != self.owner:
            raise RuntimeError("Guard ownership changed; retained")
        if {entry.name for entry in self.path.iterdir()} != {"owner.json"}:
            raise RuntimeError("Unexpected guard contents; retained")
        (self.path / "owner.json").unlink()
        self.path.rmdir()


def group_alive(group):
    try:
        os.killpg(group, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot-note", required=True)
    parser.add_argument("--operation", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a bounded foreground command is required")
    try:
        guard = BuildGuard("/tmp/lazyingart-apple-build.lock", args.operation, args.slot_note)
    except FileExistsError:
        print("Shared Apple guard occupied; no Musia job started.", flush=True)
        return 75
    for name in ["xcodebuild", "swift-frontend", "xctest"]:
        if subprocess.run(["pgrep", "-x", name], stdout=subprocess.DEVNULL).returncode == 0:
            guard.release()
            print("Peer Apple job active; released unused Musia guard.", flush=True)
            return 75
    interrupted = False

    def mark_interruption(signum, frame):
        nonlocal interrupted
        interrupted = True
        print("Interrupted connection; retaining guard until explicit owner recovery.", flush=True)

    for sig in [signal.SIGHUP, signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, mark_interruption)
    print("Musia acquired shared guard: " + guard.token, flush=True)
    child = subprocess.Popen(command, start_new_session=True,
                             env=dict(os.environ, MUSIA_APPLE_GUARD_TOKEN=guard.token))
    status = child.wait()
    if interrupted or status == 76 or group_alive(child.pid):
        print("Owned job may have descendants or interrupted cleanup; guard retained.", flush=True)
        return status or 75
    guard.release()
    print("Musia job ended; exact shared guard released.", flush=True)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
