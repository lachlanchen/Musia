#!/usr/bin/env python3
"""Build and deploy only the curated learning app, never the Musia worker."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import socket
import ssl
import subprocess
import sys
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy/learning"
WORK = DEPLOY / ".work"
ORIGIN = "https://musia.lazying.art"
EDGE_IP = "179.236.105.35"
SSH_CONFIG = Path.home() / ".config/lazytunnel/ssh-admin.conf"
CREDENTIALS = Path.home() / "Nutstore Files/Share/lazytunnel/admin-credentials.json"
HELPER = Path("/home/lachlan/DiskMech/Projects/lazyedit/scripts/studio/remote_admin.py")
HELPER_PYTHON = "/home/lachlan/miniconda3/envs/lazyedit/bin/python"
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1"}


def run(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, env=ENV, **kwargs)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_regular(source, target):
    if source.is_symlink() or not source.is_file():
        raise RuntimeError(f"Required regular source file missing: {source}")
    if any((ROOT / parent).is_symlink() for parent in source.relative_to(ROOT).parents):
        raise RuntimeError(f"Symlinked source path: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    target.chmod(0o644)


def export_catalog(learning, target):
    """Round-trip public DTOs into the minimal input schema, dropping provenance."""
    library = learning.PublicLibrary(ROOT)
    songs, items, seen = [], [], set()
    for item in library.entries():
        song = library.song(item)
        if not song or song["id"] in seen:
            continue
        seen.add(song["id"])
        songs.append(song)
        song_id = song["id"]
        items.append({"id": song_id, "kind": "song", "title": song["title"], "artist": song["artist"],
                      "cover": song["coverUrl"], "manifest": f"data/songs/{song_id}/manifest.json"})
        directory = target / "website/data/songs" / song_id
        manifest = {"id": song_id, "title": song["title"], "artist": song["artist"], "lyricSets": []}
        study = {"mediaId": song_id, "defaultAssetId": song["defaultAssetId"], "assets": {}}
        assets = []
        for asset in song["assets"]:
            asset_id, language = asset["id"], asset["language"]
            assets.append({"id": asset_id, "label": asset["label"], "languageCode": language,
                           "src": asset["audioUrl"], "duration": asset["duration"], "lyricSetId": asset_id})
            lyric_path = f"lyrics/{asset_id}.json"
            manifest["lyricSets"].append({"id": asset_id, "languageCode": language,
                                          "textTracks": [{"code": language, "path": lyric_path}]})
            write_json(directory / lyric_path, {"language": {"code": language}, "lines": asset["lyrics"]})
            study["assets"][asset_id] = {
                "src": asset["audioUrl"], "languageCode": language, "duration": asset["duration"],
                "bpm": asset["bpm"], "timeSignature": asset["timeSignature"],
                "beatConfidence": asset["confidence"]["beats"], "chordConfidence": asset["confidence"]["chords"],
                "beats": asset["beats"], "chords": asset["chords"],
                "melody": {"lines": [{"tokens": asset["melody"][n:n + 256]} for n in range(0, len(asset["melody"]), 256)]},
            }
        manifest["assets"] = {"primaryAudio": assets[0], "alternateAudio": assets[1:]}
        write_json(directory / "manifest.json", manifest)
        write_json(directory / "study.json", study)
    if not songs:
        raise RuntimeError("Refusing an empty public song catalog")
    write_json(target / "website/data/catalog.json", {"version": 1, "items": items})
    exported = learning.PublicLibrary(target)
    assert [exported.song(item) for item in exported.entries()] == songs, "curated projection changed published content"
    return songs


def archive(directory, destination):
    with destination.open("wb") as handle, gzip.GzipFile(fileobj=handle, mode="wb", filename="", mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode="w") as bundle:
            for path in sorted(directory.rglob("*")):
                if not path.is_file() or path.is_symlink():
                    if path.is_symlink():
                        raise RuntimeError(f"Symlink in release: {path}")
                    continue
                info = bundle.gettarinfo(str(path), arcname=str(path.relative_to(directory)))
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ""
                info.mode = 0o644
                with path.open("rb") as source:
                    bundle.addfile(info, source)


def build():
    WORK.mkdir(parents=True, exist_ok=True, mode=0o700)
    learning = load_module("musia_learning_release_source", ROOT / "musia/learning.py")
    source_paths = {"musia/__init__.py", "musia/learning.py", "scripts/serve_musia_learning.py", "requirements-learning.txt"}
    source_paths.update(value[0] for value in learning.STATIC_FILES.values())
    before = {p: digest(ROOT / p) for p in sorted(source_paths)}
    run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_learning_api.py", "-v"], cwd=ROOT)
    run(["node", "--test", "apps/web/tests/core.test.mjs", "apps/web/guitar-shapes.test.mjs"], cwd=ROOT)
    run([sys.executable, "tools/generate_guitar_shapes.py", "--check"], cwd=ROOT)
    job = WORK / ("build-" + time.strftime("%Y%m%dT%H%M%S"))
    job.mkdir(mode=0o700)
    tree = job / "payload"
    app = tree / "app"
    for relative in sorted(source_paths):
        copy_regular(ROOT / relative, app / relative)
    songs = export_catalog(learning, app)
    requirements = []
    for line in (ROOT / "requirements-learning.txt").read_text().splitlines():
        if line.startswith(("fastapi==", "starlette==", "uvicorn==")):
            if not re.fullmatch(r"[a-z]+==[0-9.]+", line):
                raise RuntimeError("Runtime requirement is not an exact version")
            requirements.append(line)
    if len(requirements) != 3:
        raise RuntimeError("Unexpected runtime dependencies")
    runtime_key = hashlib.sha256("\n".join(requirements).encode()).hexdigest()[:16]
    cache = WORK / ("runtime-cp312-" + runtime_key)
    if not (cache / "ready.json").exists():
        cache.mkdir(mode=0o700, exist_ok=True)
        run(["/usr/bin/python3", "-m", "venv", "--without-pip", cache / "venv"])
        wheelhouse = cache / "wheelhouse"
        run([sys.executable, "-m", "pip", "--python", cache / "venv/bin/python", "download",
             "--only-binary=:all:", "--dest", wheelhouse, *requirements])
        run([sys.executable, "-m", "pip", "--python", cache / "venv/bin/python", "install",
             "--no-compile", "--no-index", "--only-binary=:all:", "--find-links", wheelhouse, *requirements])
        installed = run([cache / "venv/bin/python", "-B", "-c",
                         "import importlib.metadata as m,json;print(json.dumps({d.metadata['Name']:d.version for d in m.distributions()}))"],
                        capture_output=True, text=True)
        write_json(cache / "ready.json", {"requirements": requirements, "installed": json.loads(installed.stdout),
                                          "wheels": {p.name: digest(p) for p in sorted(wheelhouse.glob("*.whl"))}})
    site = cache / "venv/lib/python3.12/site-packages"
    shutil.copytree(site, tree / "runtime/lib/python3.12/site-packages", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    deployment_sources = ("acceptance.py", "musia-learning.service.in", "remote.py", "test_deployment.py")
    for name in deployment_sources:
        copy_regular(DEPLOY / name, tree / "deployment" / name)
    write_json(tree / "deployment/runtime-lock.json", json.loads((cache / "ready.json").read_text()))
    manifest = {"schema": 1, "origin": ORIGIN, "nativeAppId": "art.lazying.musia", "pythonABI": "cp312-linux-x86_64",
                "sourceHashes": before, "songIds": ["first-pulse"] + [song["id"] for song in songs],
                "deploymentSourceHashes": {"deploy/learning/" + name: digest(DEPLOY / name) for name in deployment_sources},
                "staticPaths": sorted(learning.STATIC_FILES),
                "files": {str(p.relative_to(tree)): digest(p) for p in sorted(tree.rglob("*")) if p.is_file()}}
    write_json(tree / "release.json", manifest)
    # Smoke the actual staged source with the exact CPython 3.12 dependency set.
    smoke = smoke_local(cache / "venv/bin/python", app, manifest)
    write_json(job / "local-acceptance.json", smoke)
    assert before == {p: digest(ROOT / p) for p in before}, "source changed during release; rebuild"
    bundle = job / "release.tar.gz"
    archive(tree, bundle)
    sha = digest(bundle)
    receipt = {"sha256": sha, "archive": str(bundle), "payload": str(tree), "localAcceptance": str(job / "local-acceptance.json")}
    write_json(WORK / "latest-build.json", receipt)
    print(json.dumps({**receipt, "songCount": len(manifest["songIds"]), "archiveBytes": bundle.stat().st_size}, indent=2))
    return receipt


def smoke_local(python, app, manifest):
    acceptance = load_module("musia_acceptance", DEPLOY / "acceptance.py")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    log = app.parent.parent / "smoke-server.log"
    with log.open("w") as output:
        process = subprocess.Popen([str(python), "-B", "-m", "uvicorn", "musia.learning:create_app", "--factory",
                                    "--host", "127.0.0.1", "--port", str(port), "--workers", "1", "--no-access-log",
                                    "--no-proxy-headers", "--limit-concurrency", "8"], cwd=app, env=ENV,
                                   stdout=output, stderr=output)
        try:
            client = acceptance.Client(f"http://127.0.0.1:{port}")
            for _ in range(40):
                if process.poll() is not None:
                    raise RuntimeError("Staged server failed; inspect " + str(log))
                try:
                    if client.request("/healthz")[0] == 200:
                        break
                except OSError:
                    pass
                time.sleep(0.25)
            return acceptance.check(client, manifest["songIds"], manifest["staticPaths"])
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def remote(action, receipt, transaction):
    args = [action, "--sha256", receipt["sha256"], "--transaction", transaction]
    source = (DEPLOY / "remote.py").read_text()
    shell = "/usr/bin/python3 -B - " + shlex.join(args) + " <<'MUSIA_REMOTE_PYTHON'\n" + source + "\nMUSIA_REMOTE_PYTHON\n"
    try:
        result = run([HELPER_PYTHON, HELPER, "/dev/stdin", "--credentials", CREDENTIALS,
                      "--ssh-config", SSH_CONFIG, "--host", "hncloud"], input=shell, capture_output=True, text=True)
    except subprocess.CalledProcessError as error:
        print(error.stderr, file=sys.stderr)
        raise
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return json.loads(result.stdout)


def deploy(receipt):
    acceptance = load_module("musia_acceptance", DEPLOY / "acceptance.py")
    tree = Path(receipt["payload"])
    manifest = json.loads((tree / "release.json").read_text())
    assert digest(receipt["archive"]) == receipt["sha256"], "archive digest drift"
    assert all(digest(ROOT / p) == sha for p, sha in manifest["sourceHashes"].items()), "source changed after build"
    assert all(digest(ROOT / p) == sha for p, sha in manifest.get("deploymentSourceHashes", {}).items()), "deployment code changed after build"
    assert json.loads(Path(receipt["localAcceptance"]).read_text())["passed"]
    transaction = time.strftime("%Y%m%dT%H%M%S") + "-" + receipt["sha256"][:12]
    local = WORK / transaction
    local.mkdir(mode=0o700)
    write_json(local / "release-receipt.json", receipt)
    baseline = remote("preflight", receipt, transaction)
    write_json(local / "preflight.json", baseline)
    if baseline["availableMiB"] < 180:
        raise RuntimeError("Insufficient edge memory; no deployment attempted")
    for host, path in baseline["preservedHosts"].items():
        status = acceptance.Client("https://" + host, EDGE_IP).request(path, method="GET" if path != "/" else "HEAD")[0]
        assert status == 200, f"preserved site baseline failed: {host} {status}"
    run(["scp", "-q", "-F", SSH_CONFIG, "-o", "UpdateHostKeys=no", "-o", "ClearAllForwardings=yes",
         receipt["archive"], f"hncloud:/tmp/musia-learning-{receipt['sha256']}.tar.gz"])
    try:
        write_json(local / "stage.json", remote("stage", receipt, transaction))
        write_json(local / "tls-stage.json", remote("tls", receipt, transaction))
        # TLS staging serves only 503. No learning data is published before this check.
        for attempt in range(24):
            try:
                tls_status = acceptance.Client(ORIGIN, EDGE_IP).request("/healthz")[0]
                if tls_status in (200, 503):
                    break
            except (OSError, ssl.SSLError):
                pass
            if attempt == 23:
                raise RuntimeError("No verified Musia certificate within bounded issuance window")
            time.sleep(5)
        write_json(local / "certificate-gate.json", {"verified": True, "origin": ORIGIN, "status": tls_status})
        write_json(local / "activate.json", remote("activate", receipt, transaction))
        public = acceptance.check(acceptance.Client(ORIGIN, EDGE_IP), manifest["songIds"], manifest["staticPaths"])
        write_json(local / "public-acceptance.json", public)
        for host, path in baseline["preservedHosts"].items():
            status = acceptance.Client("https://" + host, EDGE_IP).request(path, method="GET" if path != "/" else "HEAD")[0]
            assert status == 200, f"preserved site regression: {host} {status}"
        write_json(local / "final.json", remote("commit", receipt, transaction))
        print(json.dumps({"deployed": True, "origin": ORIGIN, "transaction": transaction, "sha256": receipt["sha256"], "evidence": str(local)}, indent=2))
    except BaseException:
        try:
            write_json(local / "rollback.json", remote("rollback", receipt, transaction))
        except BaseException as error:
            print("ROLLBACK NEEDS OPERATOR REVIEW: " + str(error), file=sys.stderr)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "deploy", "rollback"])
    parser.add_argument("--receipt", type=Path, default=WORK / "latest-build.json")
    parser.add_argument("--transaction")
    args = parser.parse_args()
    if args.action == "build":
        build()
    else:
        receipt = json.loads(args.receipt.read_text())
        if args.action == "deploy":
            deploy(receipt)
        else:
            if not args.transaction:
                parser.error("rollback requires --transaction")
            print(json.dumps(remote("rollback", receipt, args.transaction), indent=2))


if __name__ == "__main__":
    main()
