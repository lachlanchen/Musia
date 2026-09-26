"""Reviewed root-side controller, delivered over the existing private sudo helper."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import pwd
import re
import shutil
import socket
import stat
import subprocess
import tarfile
import time
from pathlib import Path

BASE = Path("/srv/musia-learning")
STATE = Path("/var/lib/musia-learning")
CADDY = Path("/etc/lazystudio/Caddyfile")
UNIT = Path("/etc/systemd/system/musia-learning.service")
SERVICE = "musia-learning.service"
HOST = "musia.lazying.art"
BEGIN, END = "# BEGIN MUSIA LEARNING MANAGED", "# END MUSIA LEARNING MANAGED"
PRESERVED = {"edit.lazying.art": "/v1/studio/health", "agent.lightmind.art": "/",
             "oracle-fast.lazying.art": "/", "auspice.lazying.art": "/"}


def command(args, check=True):
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    if check and result.returncode:
        raise RuntimeError(f"Command failed: {args[0]}: {result.stderr[-3000:]}")
    return result


def sha(data):
    return hashlib.sha256(data).hexdigest()


def atomic(path, data, mode=0o600, owner=None):
    temporary = path.with_name(path.name + ".musia-new")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        if owner:
            os.chown(temporary, *owner)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def json_write(path, data):
    atomic(path, (json.dumps(data, sort_keys=True, indent=2) + "\n").encode())


def firewall_hash():
    return sha(command(["nft", "--stateless", "--numeric", "list", "ruleset"]).stdout.encode())


def processes():
    names = ["lazystudio-caddy", "lazystudio-edge", "lazystudio-facade", "oracle-gateway"]
    return {name: command(["systemctl", "show", name, "--property=MainPID,InvocationID"]).stdout for name in names}


def port_open():
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", 18440)) == 0


def ingress_imports(text, *, allowed_root=Path('/etc')):
    """Fingerprint protected, literal imports without retaining their secret contents."""
    records = {}
    for line in text.splitlines():
        if not re.match(r'^\s*import\b', line):
            continue
        match = re.fullmatch(r'\s*import\s+(/[A-Za-z0-9_./-]+)\s*', line)
        assert match, 'Only literal absolute ingress imports are supported'
        path = Path(match[1])
        assert '..' not in path.parts and path.is_relative_to(allowed_root), 'Import outside protected configuration'
        assert not any(p.is_symlink() for p in (path, *path.parents)), 'Symlink ingress import refused'
        info = path.stat()
        assert stat.S_ISREG(info.st_mode) and not info.st_mode & 0o022, 'Writable or non-file ingress import'
        content = path.read_bytes()
        assert not re.search(rb'(?m)^\s*import\b', content), 'Nested imports require separate review'
        assert HOST.encode() not in content, 'Imported Musia site has another owner'
        records[str(path)] = {'sha256': sha(content), 'uid': info.st_uid, 'gid': info.st_gid, 'mode': stat.S_IMODE(info.st_mode)}
    return records


def preflight():
    assert os.geteuid() == 0
    assert not CADDY.is_symlink() and CADDY.is_file(), "Unexpected ingress configuration"
    text = CADDY.read_text()
    imports = ingress_imports(text)
    assert "admin 127.0.0.1:12019" in text and "https_port 18443" in text
    for host in PRESERVED:
        assert host in text, f"Missing preserved host: {host}"
    if HOST in text:
        assert text.count(BEGIN) == text.count(END) == 1, "Musia site has another owner"
    if port_open():
        assert UNIT.exists() and command(["systemctl", "is-active", SERVICE], False).stdout.strip() == "active", "18440 belongs to another process"
        assert str(BASE) in UNIT.read_text(), "Musia unit has another owner"
    memory = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
    return {"availableMiB": int(memory["MemAvailable"].split()[0]) // 1024,
            "caddySha256": sha(CADDY.read_bytes()), "ingressImports": imports, "firewallSha256": firewall_hash(),
            "preservedHosts": PRESERVED, "processes": processes(), "portOccupied": port_open()}


def load_acceptance(release):
    path = release / "deployment/acceptance.py"
    spec = importlib.util.spec_from_file_location("musia_acceptance", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def smoke(release, high_port=False):
    acceptance = load_acceptance(release)
    manifest = json.loads((release / "release.json").read_text())
    base = "https://musia.lazying.art:18443" if high_port else "http://127.0.0.1:18440"
    client = acceptance.Client(base, "127.0.0.1")
    for _ in range(40):
        try:
            if client.request("/healthz")[0] == 200:
                break
        except OSError:
            pass
        time.sleep(0.25)
    return acceptance.check(client, manifest["songIds"], manifest["staticPaths"])


def preserved_checks(release):
    acceptance = load_acceptance(release)
    for host, path in PRESERVED.items():
        status = acceptance.Client(f"https://{host}:18443", "127.0.0.1").request(path, method="GET" if path != "/" else "HEAD")[0]
        assert status == 200, f"Preserved high-port site failed: {host} {status}"


def assert_unchanged(state):
    assert ingress_imports(CADDY.read_text()) == state['baseline'].get('ingressImports', {}), 'Imported ingress configuration changed'
    assert firewall_hash() == state["baseline"]["firewallSha256"], "Firewall changed during transaction"
    assert processes() == state["baseline"]["processes"], "Preserved service identity changed"


def extract_release(archive, release, expected):
    fd = os.open(archive, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        assert stat.S_ISREG(info.st_mode) and info.st_size < 64 * 1024 * 1024
        assert info.st_uid == pwd.getpwnam("lachlan").pw_uid
        assert sha(handle.read()) == expected, "Transferred package checksum mismatch"
        handle.seek(0)
        assert not release.exists(), "Release already exists; do not overwrite immutable contents"
        release.mkdir(mode=0o755)
        with tarfile.open(fileobj=handle, mode="r:gz") as bundle:
            total, seen = 0, set()
            for member in bundle:
                path = Path(member.name)
                assert member.isfile() and not path.is_absolute() and ".." not in path.parts
                assert member.name not in seen and member.size <= 32 * 1024 * 1024
                assert path.parts[0] in {"app", "runtime", "deployment", "release.json"}
                total += member.size
                assert total <= 192 * 1024 * 1024
                seen.add(member.name)
                target = release / path
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
                with target.open("xb") as output:
                    shutil.copyfileobj(bundle.extractfile(member), output)
                target.chmod(0o644)
    manifest = json.loads((release / "release.json").read_text())
    assert seen == set(manifest["files"]) | {"release.json"}, "Unmanifested release contents"
    for name, checksum in manifest["files"].items():
        assert sha((release / name).read_bytes()) == checksum, name
    assert manifest["origin"] == "https://" + HOST
    assert manifest["nativeAppId"] == "art.lazying.musia"
    assert manifest["pythonABI"] == "cp312-linux-x86_64"


def stage(directory, release, package_sha):
    baseline = preflight()
    assert baseline["availableMiB"] >= 180, "Insufficient memory"
    active = STATE / "active-deployment"
    assert not active.exists(), "Another Musia deployment is unfinished"
    assert not directory.exists(), "Transaction already exists"
    directory.mkdir(mode=0o700)
    previous = BASE / "current"
    assert not previous.exists() or previous.is_symlink(), "current is not a release symlink"
    state = {"baseline": baseline, "release": str(release), "sha256": package_sha, "phase": "staging",
             "expectedCaddySha256": baseline["caddySha256"], "previousRelease": str(previous.resolve()) if previous.is_symlink() else None,
             "previousUnit": UNIT.exists(), "previousActive": command(["systemctl", "is-active", SERVICE], False).stdout.strip() == "active",
             "previousEnabled": command(["systemctl", "is-enabled", SERVICE], False).stdout.strip() == "enabled"}
    meta = CADDY.stat()
    state["caddyMode"], state["caddyOwner"] = stat.S_IMODE(meta.st_mode), [meta.st_uid, meta.st_gid]
    atomic(directory / "Caddyfile.before", CADDY.read_bytes())
    if UNIT.exists():
        atomic(directory / "unit.before", UNIT.read_bytes())
    atomic(directory / "nft.before", command(["nft", "--stateless", "--numeric", "list", "ruleset"]).stdout.encode())
    json_write(directory / "state.json", state)
    atomic(active, directory.name.encode())
    (BASE / "releases").mkdir(parents=True, exist_ok=True, mode=0o755)
    extract_release(Path(f"/tmp/musia-learning-{package_sha}.tar.gz"), release, package_sha)
    command(["/usr/bin/python3", "-m", "venv", "--without-pip", release / "runtime"])
    try:
        account = pwd.getpwnam("musia-learning")
        assert account.pw_uid != 0 and account.pw_dir == "/nonexistent" and account.pw_shell == "/usr/sbin/nologin"
    except KeyError:
        command(["useradd", "--system", "--user-group", "--no-create-home", "--home-dir", "/nonexistent",
                 "--shell", "/usr/sbin/nologin", "musia-learning"])
    unit = (release / "deployment/musia-learning.service.in").read_text().replace("@RELEASE@", str(release)).encode()
    candidate = directory / SERVICE
    atomic(candidate, unit, 0o644)
    command(["systemd-analyze", "verify", candidate])
    state["installedUnitSha256"] = sha(unit)
    json_write(directory / "state.json", state)
    atomic(UNIT, unit, 0o644)
    command(["systemctl", "daemon-reload"])
    command(["systemctl", "restart", SERVICE])
    first = smoke(release)
    command(["systemctl", "restart", SERVICE])
    second = smoke(release)
    listeners = command(["ss", "-ltnH", "( sport = :18440 )"]).stdout.splitlines()
    assert len(listeners) == 1 and listeners[0].split()[3] == "127.0.0.1:18440", "Incorrect listening boundary"
    preserved_checks(release)
    assert_unchanged(state)
    state["phase"] = "staged"
    json_write(directory / "state.json", state)
    json_write(directory / "loopback-acceptance.json", first)
    json_write(directory / "restart-acceptance.json", second)
    return {"staged": True, "release": str(release), "loopback": "127.0.0.1:18440", "songCount": first["songCount"], "restartPassed": second["passed"]}


def site_block(release, tls_only=False):
    if tls_only:
        return f'{BEGIN}\n{HOST} {{\n    header X-Content-Type-Options nosniff\n    respond "Musia deployment pending" 503\n}}\n{END}\n'
    manifest = json.loads((release / "release.json").read_text())
    routes = manifest["staticPaths"] + ["/healthz", "/api/v1/library", "/api/v1/lessons", "/api/v1/capabilities", "/api/v1/exercises/first-pulse/audio.wav"]
    routes += ["/api/v1/songs/" + item for item in manifest["songIds"]]
    assert all(re.fullmatch(r"/[A-Za-z0-9_./-]*", path) and ".." not in path for path in routes)
    return f'''{BEGIN}
{HOST} {{
    header X-Content-Type-Options nosniff
    header Strict-Transport-Security "max-age=31536000"
    request_body {{
        max_size 1KB
    }}
    @musia_write {{
        not method GET HEAD
    }}
    handle @musia_write {{
        respond "Read-only API" 405
    }}
    @musia_read {{
        method GET HEAD
        path {" ".join(sorted(set(routes)))}
    }}
    handle @musia_read {{
        reverse_proxy 127.0.0.1:18440 {{
            header_up Host {HOST}
            header_up -Authorization
            header_up -Cookie
            header_up -Forwarded
            transport http {{
                dial_timeout 2s
                response_header_timeout 20s
                read_timeout 30s
                write_timeout 10s
            }}
        }}
    }}
    handle {{
        respond "Not found" 404
    }}
}}
{END}
'''


def replace_site(original, block):
    if BEGIN in original:
        assert original.count(BEGIN) == original.count(END) == 1
        before, rest = original.split(BEGIN)
        _, after = rest.split(END)
        return before + block.rstrip("\n") + after
    assert HOST not in original, "Existing unmanaged hostname"
    return original + "\n" + block


def install_caddy(directory, state, candidate_bytes):
    assert sha(CADDY.read_bytes()) == state["expectedCaddySha256"], "Concurrent Caddy change; refuse overwrite"
    assert_unchanged(state)
    if candidate_bytes == CADDY.read_bytes():
        return
    candidate = CADDY.parent / ("Caddyfile.musia-" + directory.name)
    atomic(candidate, candidate_bytes, state["caddyMode"], tuple(state["caddyOwner"]))
    try:
        command(["runuser", "-u", "lazystudio", "--", "/usr/bin/caddy", "validate", "--config", candidate, "--adapter", "caddyfile"])
        assert sha(CADDY.read_bytes()) == state["expectedCaddySha256"], "Concurrent ingress edit during validation"
        assert_unchanged(state)
        state["expectedCaddySha256"] = sha(candidate_bytes)
        json_write(directory / "state.json", state)
        os.replace(candidate, CADDY)
        command(["runuser", "-u", "lazystudio", "--", "/usr/bin/caddy", "reload", "--config", CADDY,
                 "--adapter", "caddyfile", "--address", "127.0.0.1:12019"])
    finally:
        candidate.unlink(missing_ok=True)


def rollback(directory, state):
    assert sha(CADDY.read_bytes()) in {state["expectedCaddySha256"], state["baseline"]["caddySha256"]}, "Concurrent ingress change; manual scoped rollback needed"
    if sha(CADDY.read_bytes()) != state["baseline"]["caddySha256"]:
        install_caddy(directory, state, (directory / "Caddyfile.before").read_bytes())
    if UNIT.exists() and state.get("installedUnitSha256"):
        assert sha(UNIT.read_bytes()) == state["installedUnitSha256"], "Concurrent Musia unit change"
        command(["systemctl", "stop", SERVICE])
        if state["previousUnit"]:
            atomic(UNIT, (directory / "unit.before").read_bytes(), 0o644)
        else:
            command(["systemctl", "disable", SERVICE], False)
            UNIT.unlink()
        command(["systemctl", "daemon-reload"])
        if state["previousActive"]:
            command(["systemctl", "start", SERVICE])
        if state["previousEnabled"]:
            command(["systemctl", "enable", SERVICE])
        else:
            command(["systemctl", "disable", SERVICE], False)
    current = BASE / "current"
    if state["previousRelease"]:
        promote_current(Path(state["previousRelease"]))
    elif current.is_symlink():
        assert str(current.resolve()) == state["release"]
        current.unlink()
    state["phase"] = "rolled-back"
    json_write(directory / "state.json", state)
    active = STATE / "active-deployment"
    if active.exists() and active.read_text() == directory.name:
        active.unlink()
    assert firewall_hash() == state["baseline"]["firewallSha256"]
    return {"rolledBack": True, "previousRelease": state["previousRelease"], "caddySha256": sha(CADDY.read_bytes())}


def promote_current(release):
    candidate = BASE / "current.musia-new"
    assert not candidate.exists() and not candidate.is_symlink()
    candidate.symlink_to(release)
    os.replace(candidate, BASE / "current")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["preflight", "stage", "tls", "activate", "commit", "rollback"])
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--transaction", required=True)
    args = parser.parse_args()
    assert re.fullmatch(r"[a-f0-9]{64}", args.sha256)
    assert re.fullmatch(r"[0-9]{8}T[0-9]{6}-[a-f0-9]{12}", args.transaction)
    if args.action == "preflight":
        print(json.dumps(preflight()))
        return
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    assert not STATE.is_symlink() and STATE.stat().st_uid == 0
    with (STATE / "deployment.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        deployments = STATE / "deployments"
        deployments.mkdir(exist_ok=True, mode=0o700)
        directory = deployments / args.transaction
        release = BASE / "releases" / args.sha256
        if args.action == "stage":
            result = stage(directory, release, args.sha256)
        else:
            if args.action == 'rollback' and not (directory / 'state.json').exists():
                active = STATE / 'active-deployment'
                assert not active.exists() or active.read_text() != directory.name, 'Missing state for an active transaction'
                print(json.dumps({'rolledBack': False, 'reason': 'Stage did not reach the mutation checkpoint'}))
                return
            state = json.loads((directory / "state.json").read_text())
            assert state["sha256"] == args.sha256 and state["release"] == str(release)
            if args.action == "rollback":
                result = rollback(directory, state)
            else:
                assert (STATE / "active-deployment").read_text() == directory.name
                assert_unchanged(state)
                if args.action == "tls":
                    assert state["phase"] == "staged"
                    if HOST not in CADDY.read_text():
                        install_caddy(directory, state, replace_site(CADDY.read_text(), site_block(release, True)).encode())
                    preserved_checks(release)
                    state["phase"] = "tls-staged"
                    result = {"tlsStaged": True, "caddySha256": state["expectedCaddySha256"]}
                elif args.action == "activate":
                    assert state["phase"] == "tls-staged"
                    install_caddy(directory, state, replace_site(CADDY.read_text(), site_block(release)).encode())
                    preserved_checks(release)
                    result = smoke(release, high_port=True)
                    json_write(directory / "high-port-acceptance.json", result)
                    state["phase"] = "activated"
                else:
                    assert state["phase"] == "activated"
                    assert sha(CADDY.read_bytes()) == state["expectedCaddySha256"]
                    assert_unchanged(state)
                    command(["systemctl", "enable", SERVICE])
                    promote_current(release)
                    state["phase"] = "accepted"
                    state["acceptedUTC"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    state["service"] = command(["systemctl", "show", SERVICE, "--property=ActiveState,MainPID,MemoryCurrent,MemoryPeak,NRestarts"]).stdout
                    (STATE / "active-deployment").unlink()
                    result = state
                json_write(directory / "state.json", state)
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
