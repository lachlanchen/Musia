#!/usr/bin/env python3
"""One admitted KVM metadata read; no remote file writes or native job launch."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import uuid

from apple_read_child import ReadCommands, clock

NAMES = ("apple_host_busy.py", "apple_read_child.py", "apple_internal_preflight.py", "apple_read_entry.py")
HOST = "echomind-kvm-macos"
HOST_UUID = "0685A36A-0F51-5C5E-B2EA-A56B06B9E36D"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload(folder):
    code = "import sys,types\n"
    for name in NAMES[:2]:
        source = (folder / name).read_text()
        module = Path(name).stem
        code += "m=types.ModuleType(" + repr(module) + ");sys.modules[" + repr(module) + "]=m\n"
        code += "exec(compile(" + repr(source) + "," + repr(name) + ",'exec'),m.__dict__)\n"
    code += "sys.argv=['apple_internal_preflight.py','--config','~/Projects/Musia/store/.runtime/config.json']\n"
    code += "exec(compile(" + repr((folder / NAMES[2]).read_text()) + ",'apple_internal_preflight.py','exec'),{'__name__':'__main__'})\n"
    value = code.encode()
    assert len(value) < 256000
    return value


def validate(admission, folder, source, now):
    uuid.UUID(admission["id"])
    assert admission["kind"] == "musia-read-boundary" and admission["build"] == "0.2.2(12)"
    assert admission["route"] == HOST and admission["hostUUID"] == HOST_UUID
    assert admission["source"] == source
    assert admission["hashes"] == {name: digest(folder / name) for name in NAMES}
    expiry = dt.datetime.fromisoformat(admission["startBeforeUTC"].replace("Z", "+00:00"))
    assert expiry.tzinfo and now < expiry
    assert admission["outerSeconds"] == 100 and admission["remoteSeconds"] == 60


def write_once(path, value):
    with open(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
        json.dump(value, stream, indent=2); stream.flush(); os.fsync(stream.fileno())


def main(admission_path, output):
    folder = Path(__file__).resolve().parent
    root = folder.parents[1]
    source = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True, timeout=3).strip()
    admission = json.loads(Path(admission_path).read_text())
    validate(admission, folder, source, dt.datetime.now(dt.timezone.utc))
    data = payload(folder)
    output = Path(output); output.mkdir(mode=0o700, parents=True, exist_ok=True)
    write_once(output / "intent.json", admission)
    commands = ReadCommands(clock() + 100, reserve=10)
    def stop(*_):
        signal.setitimer(signal.ITIMER_REAL, 0)
        raise TimeoutError("Outer read deadline/interruption")
    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    signal.setitimer(signal.ITIMER_REAL, 90)
    try:
        args = ["ssh", "-T", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
                "-o", "ConnectionAttempts=1", "-o", "ConnectTimeout=30", "-o", "ControlMaster=no",
                "-o", "ControlPath=none", HOST, "/usr/bin/python3", "-B", "-"]
        result = commands.run(args, limit=90, input_data=data)
        write_once(output / "response.json", result)
        assert result["exit"] == 0, "Remote read incomplete; no retry or native admission"
        snapshot = json.loads(result["stdout"])
        assert snapshot["state"] == "metadata_collected_not_build_admission"
        write_once(output / "snapshot.json", snapshot)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        for sig, handler in previous.items(): signal.signal(sig, handler)
        write_once(output / "local-children.json", commands.records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("admission")
    parser.add_argument("output")
    args = parser.parse_args()
    main(args.admission, args.output)
