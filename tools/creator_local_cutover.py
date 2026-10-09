#!/usr/bin/env python3
"""Promote staged creator app/relay units only; never change edge, tunnel or GPU queue."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import time
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    home = Path.home()
    private = home / ".config/musia/creator-runtime"
    staged = json.loads((private / "staged.json").read_text())
    units = ["musia-creator-" + role + ".service" for role in ("app", "worker", "maintenance", "billing-reconcile")]
    target = home / ".config/systemd/user"
    release = Path(staged["release"])
    assert release.parent == home / ".local/share/musia/creator-releases"
    for name in units:
        assert release.as_posix() in (private / "units" / name).read_text()
        assert (target / name).is_file()
    with sqlite3.connect(f"file:{home}/.local/share/musia/creator-live/creator.sqlite?mode=ro", uri=True) as db:
        assert db.execute("SELECT count(*) FROM jobs WHERE state='running'").fetchone()[0] == 0, "Active render; retry when idle"
    result = {"release": release.name, "units": units, "applied": False}
    if not args.apply:
        print(json.dumps(result)); return
    evidence = private / ("cutover-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    evidence.mkdir(mode=0o700)
    for name in units:
        shutil.copy2(target / name, evidence / name)
    try:
        for name in units:
            shutil.copy2(private / "units" / name, target / name)
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "restart", *units[:2]], check=True)
        for attempt in range(12):
            try:
                with urllib.request.urlopen("https://musia.lazying.art/creator/api/capabilities", timeout=15) as response:
                    caps = json.load(response)
                assert caps["login"] and caps["agent"] and not caps["salesEnabled"]
                with urllib.request.urlopen("https://musia.lazying.art/creator/app.js", timeout=15) as response:
                    assert response.read() == (release / "apps/web/creator/app.js").read_bytes()
                break
            except Exception:
                if attempt == 11: raise
                time.sleep(2)
        result["applied"] = True
    except Exception:
        for name in units:
            shutil.copy2(evidence / name, target / name)
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "restart", *units[:2]], check=True)
        raise
    finally:
        (evidence / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
