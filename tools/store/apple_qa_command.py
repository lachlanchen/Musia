#!/usr/bin/env python3
"""Bound an owned QA command; uncertain cleanup retains the outer Apple guard."""
import os
import signal
import subprocess
import sys

from apple_build_guard import group_alive


def run(command, timeout):
    process = subprocess.Popen(command, start_new_session=True)
    try:
        status = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=15)
        print("QA deadline reached; outer guard must remain for cleanup verification.", flush=True)
        return 76
    if status < 0 or group_alive(process.pid):
        return 76
    return status


if __name__ == "__main__":
    timeout = int(sys.argv[1])
    if not 1 <= timeout <= 1800 or len(sys.argv) < 3:
        raise SystemExit(64)
    raise SystemExit(run(sys.argv[2:], timeout))
