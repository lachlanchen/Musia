#!/usr/bin/env python3
"""Disposable Docker qualification. Never mounts live state or changes ingress.

By default no paid calls. --live-key-file permits ONE synthetic text call;
--aginti chooses the optional adapter, not a GPU render. All test containers,
networks, secrets and the disposable volume are removed on success or failure.
"""

import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default="agent-sandbox-20261015")
    parser.add_argument("--aginti", action="store_true")
    parser.add_argument("--live-key-file", type=Path)
    args = parser.parse_args()
    project = "musia-qa-" + secrets.token_hex(4)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="musia-container-qa-") as temporary:
        private = Path(temporary)
        key = args.live_key_file.read_text().strip() if args.live_key_file else "synthetic-no-charge-key"
        for name, value in (("key", key), ("token", secrets.token_urlsafe(32))):
            path = private / name
            path.write_text(value)
            # Parent is 0700; container UID can read only its explicitly mounted file.
            path.chmod(0o444)
        env = {**os.environ, "MUSIA_IMAGE_TAG": args.tag, "MUSIA_CONTAINER_PORT": str(port),
               "MUSIA_CREATOR_ORIGIN": f"http://127.0.0.1:{port}",
               "MUSIA_TEXT_KEY_FILE": str(private/"key"), "MUSIA_AGENT_TOKEN_FILE": str(private/"token")}
        base = ["docker", "compose", "-p", project, "-f", str(ROOT/"deploy/containers/compose.yaml")]
        if args.aginti:
            base += ["-f", str(ROOT/"deploy/containers/compose.aginti.yaml")]

        def run(command, *, timeout=120, check=True, stdin=None):
            result = subprocess.run(command, env=env, cwd=ROOT, input=stdin, capture_output=True,
                                    text=True, timeout=timeout)
            if check and result.returncode:
                # Docker errors may contain credential file paths but never file values.
                raise RuntimeError(result.stderr[-2000:] or "Container command failed")
            return result

        def inside(code):
            return run(base + ["exec", "-T", "app", "python", "-c", code]).stdout.strip()

        try:
            run(base + ["up", "-d", "--no-build", "--wait", "--wait-timeout", "60"])
            for route in ("/healthz", "/", "/api/v1/library", "/api/v1/lessons", "/creator/", "/creator/api/capabilities"):
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with opener.open(f"http://127.0.0.1:{port}" + route, timeout=5) as response:
                    assert response.status == 200
                    response.read()
            containers = run(base + ["ps", "-q"]).stdout.split()
            records = json.loads(run(["docker", "inspect", *containers]).stdout)
            for record in records:
                cfg, host = record["Config"], record["HostConfig"]
                assert cfg["User"] == "10001:10001" and host["ReadonlyRootfs"]
                assert host["CapDrop"] == ["ALL"] and not host["Privileged"]
                assert "no-new-privileges:true" in host["SecurityOpt"]
                assert host["Memory"] > 0 and host["PidsLimit"] <= 64
                assert not any("docker.sock" in m["Destination"] for m in record["Mounts"])
                assert not any(key in item for item in cfg["Env"])
            inside("import os; assert os.getuid()==10001; assert not os.path.exists('/var/run/docker.sock');\n"
                   "try: open('/app/forbidden','w')\nexcept OSError: pass\nelse: raise AssertionError('writable root')")
            inside("import socket; s=socket.socket(); s.settimeout(2);\n"
                   "try: s.connect(('1.1.1.1',443))\nexcept OSError: pass\nelse: raise AssertionError('unrestricted network')\nfinally: s.close()")
            inside("import httpx; c=httpx.Client(proxy='http://egress:8888',trust_env=False,timeout=5);\n"
                   "for url in ('https://example.com','https://169.254.169.254','https://api.deepseek.com.evil.test'):\n"
                   " try: c.get(url)\n except httpx.ProxyError: pass\n else: raise AssertionError('egress allowlist bypass')")
            inside("import httpx; c=httpx.Client(proxy='http://egress:8888',trust_env=False,timeout=15); "
                   "r=c.get('https://api.deepseek.com/models'); assert 200 <= r.status_code < 500")
            if args.aginti:
                run(base + ["exec", "-T", "agent", "node", "--test", "server.test.mjs"])
                inside("import httpx; r=httpx.post('http://agent:8081/v1/refine',json={'message':'hello'},trust_env=False); assert r.status_code==401")
            if args.live_key_file:
                result = inside("import json,time; from musia.creator.agent import Producer; from musia.creator.contracts import Chat,Draft; "
                                "t=time.monotonic(); r=Producer().refine(Chat(message='Keep this title and tempo. Ask one short question about the mood; do not invent lyrics.',brief=Draft(title='Synthetic canary',bpm=82))); "
                                "assert r.brief.title=='Synthetic canary' and r.brief.bpm==82; "
                                "print(json.dumps({'liveTextCall':True,'seconds':round(time.monotonic()-t,2),'validReply':True}))")
                print(result)
            # A restart must retain only this test's database, not another instance's.
            inside("import sqlite3; db=sqlite3.connect('/state/qa.sqlite'); db.execute('create table marker (v text)'); db.execute(\"insert into marker values ('retained')\"); db.commit()")
            run(base + ["restart", "app"])
            inside("import sqlite3; assert sqlite3.connect('/state/qa.sqlite').execute('select v from marker').fetchone()[0]=='retained'")
            stats = run(["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.MemUsage}}", *containers]).stdout
            print(stats.strip())
            print(json.dumps({"passed": True, "backend": "aginti" if args.aginti else "direct",
                              "rootReadonly": True, "networkRestricted": True, "stateRetained": True,
                              "paidCall": bool(args.live_key_file), "productionChanged": False}))
        except Exception:
            logs = run(base + ["logs", "--no-color", "--tail", "25"], check=False).stdout
            print(logs.replace(key, "[redacted]")[-4000:])
            raise
        finally:
            # Only resources carrying this random Compose project name are removed.
            run(base + ["down", "--volumes", "--remove-orphans"], timeout=120, check=True)


if __name__ == "__main__":
    main()
