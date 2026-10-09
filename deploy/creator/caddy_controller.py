"""Draft local controller; never invokes SSH, a service manager, or a firewall.

Render is read-only. Apply/rollback need explicit caller-supplied validate,
reload and probe argv, a baseline SHA, and a private transaction directory.
The shared Caddy/learning owners must hold the same external maintenance lock:
POSIX rename is atomic but not a kernel compare-and-swap against other writers.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile

BEGIN = "# BEGIN MUSIA LEARNING MANAGED"
END = "# END MUSIA LEARNING MANAGED"
HOST = "musia.lazying.art"
INSERT = Path(__file__).with_name("caddy-creator.caddy").read_text()
ANCHOR = "    request_body {\n        max_size 1KB\n    }\n"
SCOPED = "    request_body @musia_not_creator {\n        max_size 1KB\n    }\n"

# Deliberately recognize only the exact production learning template. A changed
# template needs a new reviewed adapter, never a best-effort text replacement.
SITE = '''# BEGIN MUSIA LEARNING MANAGED
musia.lazying.art {
    header X-Content-Type-Options nosniff
    header Strict-Transport-Security "max-age=31536000"
    request_body {
        max_size 1KB
    }
    @musia_write {
        not method GET HEAD
    }
    handle @musia_write {
        respond "Read-only API" 405
    }
    @musia_read {
        method GET HEAD
        path ROUTE_LIST
    }
    handle @musia_read {
        reverse_proxy 127.0.0.1:18440 {
            header_up Host musia.lazying.art
            header_up -Authorization
            header_up -Cookie
            header_up -Forwarded
            transport http {
                dial_timeout 2s
                response_header_timeout 20s
                read_timeout 30s
                write_timeout 10s
            }
        }
    }
    handle {
        respond "Not found" 404
    }
}
# END MUSIA LEARNING MANAGED'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def render(original):
    text = original.decode("utf-8")
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise ValueError("Expected one existing learning managed block")
    before, tail = text.split(BEGIN)
    body, after = tail.split(END)
    if HOST in before + after or 'musia_creator' in before + after or 'musia_not_creator' in before + after:
        raise ValueError("Ambiguous Musia ownership")
    block = BEGIN + body + END
    installed = "# BEGIN MUSIA CREATOR SCOPED" in block
    baseline = block
    if installed:
        if block.count(INSERT) != 1 or block.count(SCOPED) != 1:
            raise ValueError("Unknown creator configuration")
        baseline = block.replace(INSERT, "", 1).replace(SCOPED, ANCHOR, 1)
    paths = re.findall(r"^        path (.+)$", baseline, re.MULTILINE)
    if len(paths) != 1 or any(not re.fullmatch(r"/[A-Za-z0-9_./-]*", p) or '..' in p for p in paths[0].split()):
        raise ValueError("Unknown learning route shape")
    if baseline != SITE.replace("ROUTE_LIST", paths[0]):
        raise ValueError("Learning template differs; review required")
    candidate = baseline.replace(ANCHOR, INSERT + SCOPED, 1)
    if installed and candidate != block:
        raise ValueError("Creator block differs")
    return (before + candidate + after).encode()


def read_regular(path, private=False):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path:
        raise ValueError("Symlink or relative path refused")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as file:
        meta = os.fstat(file.fileno())
        if not stat.S_ISREG(meta.st_mode) or meta.st_mode & (0o077 if private else 0o022):
            raise ValueError("Unsafe file ownership/mode")
        if meta.st_size > 4 * 1024 * 1024:
            raise ValueError("Configuration too large")
        return file.read(), meta


def fingerprint(path):
    data, meta = read_regular(path)
    return (sha(data), meta.st_dev, meta.st_ino, meta.st_uid, meta.st_gid, stat.S_IMODE(meta.st_mode))


def imports(data):
    """Pin literal imports; decline glob/snippet/nested imports for separate review."""
    result = {}
    for line in data.decode().splitlines():
        if not re.match(r"\s*import\b", line):
            continue
        match = re.fullmatch(r"\s*import (/[A-Za-z0-9_./-]+)\s*", line)
        if not match:
            raise ValueError("Only literal absolute imports can be pinned")
        path = Path(match[1])
        value, _ = read_regular(path)
        if re.search(rb"(?m)^\s*import\b", value) or HOST.encode() in value:
            raise ValueError("Nested import or imported Musia owner refused")
        result[str(path)] = list(fingerprint(path))
    return result


def exclusive_file(path, data):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), "wb") as file:
        file.write(data)
        file.flush()
        os.fsync(file.fileno())


def replace_checked(path, expected, data, meta):
    """CAS-style recheck under the shared writer lock; refuse concurrent edits."""
    fd, name = tempfile.mkstemp(prefix=".musia-creator-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(data)
            file.flush()
            os.fchmod(file.fileno(), stat.S_IMODE(meta.st_mode))
            if (meta.st_uid, meta.st_gid) != (os.getuid(), os.getgid()):
                os.fchown(file.fileno(), meta.st_uid, meta.st_gid)
            os.fsync(file.fileno())
        if fingerprint(path) != expected:
            raise ValueError("Concurrent Caddy writer; refusing replacement")
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        if path.read_bytes() != data:
            raise ValueError("Caddy readback mismatch")
    finally:
        temporary.unlink(missing_ok=True)


def run(argv, config):
    if not isinstance(argv, list) or not argv or not all(isinstance(v, str) for v in argv) or not Path(argv[0]).is_absolute():
        raise ValueError("An absolute executable and argv array are required")
    command = [v.replace("{config}", str(config)) for v in argv]
    # Commands may print private site data. Keep output out of logs and exceptions.
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=45)
    if result.returncode:
        raise RuntimeError("Validation/reload/acceptance command failed")


def transact(action, config, transaction, expected_sha, validate, reload, probe, rollback_probe=None):
    rollback_probe = rollback_probe or probe
    config, transaction = Path(config), Path(transaction)
    if not transaction.is_absolute() or transaction.resolve() != transaction:
        raise ValueError("Transaction path must be absolute and not symlinked")
    info = transaction.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.getuid():
        raise ValueError("Pre-create a private, owned transaction directory")
    lock_path = config.parent / ".musia-ingress.lock"
    lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lock_fd, "r+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        current, meta = read_regular(config)
        baseline = fingerprint(config)
        if sha(current) != expected_sha:
            raise ValueError("Caddy baseline digest mismatch")
        if action == "apply":
            candidate = render(current)
            if candidate == current:
                raise ValueError("Creator handler is already installed")
            pinned_imports = imports(current)
            exclusive_file(transaction / "Caddyfile.before", current)
            exclusive_file(transaction / "Caddyfile.candidate", candidate)
            state = {"config": str(config), "before": sha(current), "candidate": sha(candidate),
                     "imports": pinned_imports, "uid": meta.st_uid, "gid": meta.st_gid,
                     "mode": stat.S_IMODE(meta.st_mode)}
            exclusive_file(transaction / "state.json", (json.dumps(state, indent=2) + "\n").encode())
        elif action == "rollback":
            state = json.loads(read_regular(transaction / "state.json", private=True)[0])
            candidate = read_regular(transaction / "Caddyfile.before", private=True)[0]
            if state["config"] != str(config) or state["candidate"] != sha(current) or state["before"] != sha(candidate):
                raise ValueError("Rollback does not own the current configuration")
            if (meta.st_uid, meta.st_gid, stat.S_IMODE(meta.st_mode)) != (state['uid'], state['gid'], state['mode']):
                raise ValueError("Caddy ownership/mode changed")
            pinned_imports = state["imports"]
        else:
            raise ValueError("Unknown transaction action")
        source = transaction / ("Caddyfile.candidate" if action == "apply" else "Caddyfile.before")
        run(validate, source)
        if imports(current) != pinned_imports or source.read_bytes() != candidate:
            raise ValueError("Validated artifact/import changed")
        replace_checked(config, baseline, candidate, meta)
        installed = fingerprint(config)
        try:
            run(reload, config)
            run(probe if action == "apply" else rollback_probe, config)
            if fingerprint(config) != installed or imports(candidate) != pinned_imports:
                raise ValueError("Configuration changed during acceptance")
        except BaseException:
            if action == "apply":
                # Refuse rollback over another writer or changed import.
                if imports(candidate) != pinned_imports:
                    raise RuntimeError("Imported configuration changed; automatic rollback refused") from None
                run(validate, transaction / "Caddyfile.before")
                replace_checked(config, installed, current, meta)
                run(reload, config)
                run(rollback_probe, config)
            raise
        exclusive_file(transaction / (action + ".accepted.json"),
                       (json.dumps({"action": action, "sha256": sha(candidate)}) + "\n").encode())
        return sha(candidate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("render", "apply", "rollback"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--transaction", type=Path)
    for name in ("validate", "reload", "probe", "rollback-probe"):
        parser.add_argument("--" + name + "-argv", type=json.loads)
    args = parser.parse_args()
    data = read_regular(args.config)[0]
    if sha(data) != args.expected_sha256:
        parser.error("Caddy baseline digest mismatch")
    if args.action == "render":
        print(render(data).decode(), end="")
    else:
        if not args.transaction or not all((args.validate_argv, args.reload_argv, args.probe_argv, args.rollback_probe_argv)):
            parser.error("Mutations require transaction, validate, reload, acceptance and rollback acceptance argv")
        print(transact(args.action, args.config, args.transaction, args.expected_sha256,
                       args.validate_argv, args.reload_argv, args.probe_argv, args.rollback_probe_argv))


if __name__ == "__main__":
    main()
