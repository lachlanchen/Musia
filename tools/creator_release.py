#!/usr/bin/env python3
"""Stage an immutable creator service and private user units; never cut over ingress."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
STATE = HOME / ".local/share/musia/creator-live"
PRIVATE = HOME / ".config/musia/creator-runtime"
PYTHON = HOME / ".local/share/musia/creator-server/venv/bin/python"


def private(path, value, *, replace=False):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    if path.exists() and not replace:
        return
    temporary = path.with_suffix(path.suffix + ".new")
    with os.fdopen(os.open(temporary,os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,0o600),"wb") as out:
        out.write(value)
        out.flush()
        os.fsync(out.fileno())
    os.replace(temporary,path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lazyedge",type=Path,required=True)
    parser.add_argument("--edge-ip",required=True)
    parser.add_argument("--edge-port",type=int,default=2222)
    parser.add_argument("--known-hosts",type=Path,required=True)
    args=parser.parse_args()
    os.umask(0o077)
    files={}
    for folder in ("musia","apps/web/creator","deploy/creator"):
        for path in (ROOT/folder).rglob("*"):
            if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts:
                files[str(path.relative_to(ROOT))]=path.read_bytes()
    files["tools/creator.py"] = (ROOT/"tools/creator.py").read_bytes()
    pin=json.loads((ROOT/"deploy/creator/lazyedge-pin.json").read_text())
    for name,expected in pin["files"].items():
        content=(args.lazyedge/name).read_bytes()
        if hashlib.sha256(content).hexdigest()!=expected:
            raise ValueError("LazyEdge digest mismatch")
        files["lazyedge/"+name]=content
    manifest={name:hashlib.sha256(value).hexdigest() for name,value in sorted(files.items())}
    revision=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    release=HOME/".local/share/musia/creator-releases"/revision
    if not release.exists():
        release.mkdir(parents=True,mode=0o700)
        for name,data in files.items():
            path=release/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data)
        (release/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    for name,expected in manifest.items():
        if hashlib.sha256((release/name).read_bytes()).hexdigest()!=expected:
            raise ValueError("Immutable release differs")
    STATE.mkdir(parents=True,exist_ok=True,mode=0o700)
    PRIVATE.mkdir(parents=True,exist_ok=True,mode=0o700)
    import secrets
    for name in ("relay","upstream"):
        private(PRIVATE/name,(secrets.token_urlsafe(48)+"\n").encode())
    key=PRIVATE/"id_ed25519"
    if not key.exists():
        subprocess.run(["ssh-keygen","-q","-t","ed25519","-N","","-C","musia-creator-tunnel","-f",str(key)],check=True)
    private(PRIVATE/"known_hosts",args.known_hosts.read_bytes())
    private(PRIVATE/"worker.json",json.dumps({"role":"worker","relaySecretFile":str(PRIVATE/"relay"),
            "upstreamSecretFile":str(PRIVATE/"upstream")}).encode())
    env={"MUSIA_CREATOR_ORIGIN":"https://musia.lazying.art","MUSIA_CREATOR_DATA":str(STATE),
         "MUSIA_CREATOR_AUTH_DIR":str(HOME/".config/musia/creator-auth"),
         "MUSIA_CREATOR_UPSTREAM_SECRET_FILE":str(PRIVATE/"upstream"),
         "MUSIA_CREATOR_GENERATION":"0","MUSIA_CREATOR_OPEN_SIGNUP":"0",
         "MUSIA_CREATOR_TEXT_BASE_URL":"https://api.deepseek.com","MUSIA_CREATOR_TEXT_MODEL":"deepseek-v4-pro"}
    if os.environ.get("DEEPSEEK_API_KEY"):
        env["MUSIA_CREATOR_TEXT_API_KEY"]=os.environ["DEEPSEEK_API_KEY"]
    if any("\n" in v or "\r" in v or '"' in v or "\\" in v for v in env.values()):
        raise ValueError("Unsafe environment value")
    private(PRIVATE/"app.env",("\n".join(k+'="'+v+'"' for k,v in env.items())+"\n").encode())
    node=Path(shutil.which("node")).resolve()
    common="Restart=on-failure\nRestartSec=5\nUMask=0077\nNoNewPrivileges=yes\nTimeoutStopSec=15\n"
    commands={
        "app": f"{PYTHON} -m uvicorn deploy.creator.upstream:create_app --factory --host 127.0.0.1 --port 8797 --workers 1 --no-proxy-headers --no-access-log",
        "worker": f"{node} {release}/deploy/creator/gateway.mjs {PRIVATE}/worker.json",
        "tunnel": f"/usr/bin/ssh -F /dev/null -N -T -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile={PRIVATE}/known_hosts -o GlobalKnownHostsFile=/dev/null -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no -o ExitOnForwardFailure=yes -o ServerAliveInterval=20 -o ServerAliveCountMax=3 -o ConnectTimeout=10 -o ForwardAgent=no -o ForwardX11=no -o ControlMaster=no -i {key} -p {args.edge_port} -R 127.0.0.1:18897:127.0.0.1:18898 musia-creator-tunnel@{args.edge_ip}",
    }
    units=PRIVATE/"units"
    units.mkdir(exist_ok=True)
    for role,command in commands.items():
        body=f"[Unit]\nDescription=Musia creator {role}\nAfter=network-online.target\n\n[Service]\nType=simple\nWorkingDirectory={release}\nEnvironment=PYTHONNOUSERSITE=1\nEnvironment=PYTHONDONTWRITEBYTECODE=1\nEnvironment=MUSIA_LAZYEDGE_ROOT={release}/lazyedge\n"
        if role=="app": body+=f"EnvironmentFile={PRIVATE}/app.env\n"
        body+=f"ExecStart={command}\n{common}MemoryMax={'768M' if role=='app' else '192M'}\nTasksMax=128\n\n[Install]\nWantedBy=default.target\n"
        private(units/f"musia-creator-{role}.service",body.encode(),replace=True)
    for action in ("maintenance","billing-reconcile"):
        body=f"[Unit]\nDescription=Musia creator {action}\n\n[Service]\nType=oneshot\nWorkingDirectory={release}\nEnvironmentFile={PRIVATE}/app.env\nEnvironment=PYTHONNOUSERSITE=1\nEnvironment=PYTHONDONTWRITEBYTECODE=1\nExecStart={PYTHON} {release}/tools/creator.py {action}\nUMask=0077\nNoNewPrivileges=yes\nTimeoutStartSec=240\n"
        private(units/f"musia-creator-{action}.service",body.encode(),replace=True)
        timer=f"[Unit]\nDescription=Musia creator {action} every five minutes\n\n[Timer]\nOnBootSec=60\nOnUnitActiveSec=300\nUnit=musia-creator-{action}.service\n\n[Install]\nWantedBy=timers.target\n"
        private(units/f"musia-creator-{action}.timer",timer.encode(),replace=True)
    # A finite, explicitly authorized batch. Restarting never replenishes its
    # persisted budget. This is not the relay guard named creator-worker.
    queue_config=PRIVATE/"queue.json"
    private(queue_config,json.dumps({"run_id":"creator-pilot-20261009",
        "enabled":True,"dispatch":True,"max_per_run":10,"max_dispatches":10,
        "max_passes":10000,"poll_seconds":30}).encode())
    queue=f"[Unit]\nDescription=Musia bounded generation queue\nAfter=network-online.target\nConditionPathExists={queue_config}\n\n[Service]\nType=simple\nWorkingDirectory={ROOT}\nEnvironment=PYTHONNOUSERSITE=1\nEnvironment=PYTHONDONTWRITEBYTECODE=1\nEnvironment=MUSIA_CREATOR_DATA={STATE}\nEnvironment=CUDA_VISIBLE_DEVICES=0\nExecStart={HOME}/miniconda3/envs/musia/bin/python {ROOT}/tools/creator.py supervise --config {queue_config}\nRestart=no\nKillMode=control-group\nTimeoutStopSec=120\nUMask=0077\nNoNewPrivileges=yes\nTasksMax=512\nMemoryMax=64G\n\n[Install]\nWantedBy=default.target\n"
    private(units/"musia-creator-generation.service",queue.encode(),replace=True)
    archive=ROOT/"store/.runtime"/f"creator-{revision}.tar.gz"
    if not archive.exists():
        with tarfile.open(archive,"w:gz") as bundle:
            for name in sorted(files):
                if name.startswith(("deploy/creator/","lazyedge/")):
                    bundle.add(release/name,arcname=name,recursive=False)
    receipt={"revision":revision,"release":str(release),"archive":str(archive),
             "archiveSha256":hashlib.sha256(archive.read_bytes()).hexdigest(),"units":str(units),
             "private":str(PRIVATE),"data":str(STATE)}
    private(PRIVATE/"staged.json",json.dumps(receipt,indent=2).encode(),replace=True)
    print(json.dumps(receipt,indent=2))


if __name__=="__main__": main()
