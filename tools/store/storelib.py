"""Musia-only release guards. No provider requests or writes at import time."""
from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "store/.runtime"
BUNDLE = "art.lazying.musia"
TEAM = "Q8M2S2FY77"
DEVELOPER = "6157557679644496686"
CHECKS = {"unit_tests", "native_smoke", "offline_progress", "background_playback", "permissions", "content_rights"}
INTERNAL_BETA_CHECKS = {"unit_tests", "native_ui", "permissions", "content_review"}


class GuardError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise GuardError(message)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def private_file(path):
    path = Path(path).expanduser()
    require(path.is_absolute() and not path.is_symlink(), "Private path must be absolute and not a symlink")
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and not info.st_mode & 0o077,
            "Private file must be owner-only (0600 or 0400)")
    return path


def private_dir(path):
    path = Path(path).expanduser()
    require(path.is_absolute() and not path.is_symlink(), "Private directory must be absolute and not a symlink")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.stat()
    require(info.st_uid == os.getuid() and not info.st_mode & 0o077, "Private directory must be owner-only (0700)")
    return path


def write_private(path, value):
    path = Path(path)
    private_dir(path.parent)
    require(not path.is_symlink(), "Refusing a symlink output")
    payload = value if isinstance(value, bytes) else (json.dumps(value, indent=2) + "\n").encode()
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".musia-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_json(path):
    return json.loads(Path(path).read_text())


def release():
    value = read_json(ROOT / "store/release.json")
    require(value["bundle_id"] == BUNDLE and value["apple_team"] == TEAM
            and value["google_developer_id"] == DEVELOPER, "Musia identity/account mismatch")
    require(value.get("formal_submission_enabled") is False, "Formal submission is outside this tool")
    return value


def config():
    path = Path(os.environ.get("MUSIA_STORE_CONFIG", RUNTIME / "config.json")).expanduser()
    value = read_json(private_file(path))
    require(value.get("bundle_id") == BUNDLE and value.get("apple_team") == TEAM
            and value.get("google_developer_id") == DEVELOPER, "Private configuration identity mismatch")
    return value


@contextlib.contextmanager
def lock(name):
    private_dir(RUNTIME)
    path = RUNTIME / (name + ".lock")
    require(not path.is_symlink(), "Refusing symlink lock")
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise GuardError("Another Musia operation owns this lock") from None
        yield
    finally:
        os.close(fd)


def source_sha(platform):
    base = ROOT / "apps" / platform
    require(platform in {"ios", "android"} and base.is_dir(), "Native source tree missing")
    skip = {"build", ".build", ".gradle", ".runtime", "DerivedData", "xcuserdata", ".swiftpm"}
    records = []
    for path in sorted(base.rglob("*")):
        relative = path.relative_to(base)
        if any(part in skip for part in relative.parts) or path.name in {"local.properties", ".DS_Store"}:
            continue
        require(not path.is_symlink(), "Release source may not contain symlinks")
        if path.is_file():
            require(path.suffix not in {".p8", ".p12", ".jks", ".mobileprovision"}, "Signing material in source")
            records.append([str(relative), digest(path)])
    require(records, "Empty native source")
    return hashlib.sha256(json.dumps(records, separators=(",", ":")).encode()).hexdigest()


def run(command, *, cwd=None, env=None, log=None, input_data=None):
    result = subprocess.run([str(x) for x in command], cwd=cwd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False, input=input_data)
    if log:
        write_private(log, result.stdout + result.stderr)
    require(result.returncode == 0, "Subprocess failed; inspect its private log (command output suppressed)")
    return result.stdout


def snapshot_artifact(build):
    source = Path(build["artifact"])
    directory = private_dir(RUNTIME / "upload-inputs" / build["artifact_sha256"])
    destination = directory / source.name
    if destination.exists():
        require(not destination.is_symlink() and digest(destination) == build["artifact_sha256"], "Upload snapshot mismatch")
        return dict(build, artifact=str(destination))
    fd, temporary = tempfile.mkstemp(dir=directory, prefix=".snapshot-")
    try:
        with os.fdopen(fd, "wb") as target, source.open("rb") as handle:
            shutil.copyfileobj(handle, target, length=1024 * 1024)
            target.flush()
            os.fsync(target.fileno())
        require(digest(temporary) == build["artifact_sha256"], "Artifact changed before upload")
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return dict(build, artifact=str(destination))


class Apple:
    def __init__(self, cfg=None):
        self.cfg = cfg if cfg is not None else config()

    def request(self, method, path, body=None, operation=None):
        require(method in {"GET", "POST"} and path.startswith("/v1/") and ".." not in path,
                "Unsupported provider request")
        require(method == "GET" or operation, "Mutation must have a stable journal operation")
        require(method == "GET" or path in {"/v1/bundleIds", "/v1/profiles", "/v1/betaGroups"}
                or re.fullmatch(r"/v1/betaGroups/[A-Za-z0-9-]+/relationships/(builds|betaTesters)", path),
                "This tool cannot change prices, declarations, account users or formal review")
        receipt = RUNTIME / "operations" / (hashlib.sha256((operation or "read").encode()).hexdigest() + ".json")
        if method != "GET":
            require(not receipt.exists(), "Operation already attempted; inventory/read back before any retry")
        try:
            import jwt
        except ImportError:
            raise GuardError("Provider operation requires existing PyJWT runtime; set MUSIA_PYTHON=/usr/bin/python3") from None
        key = private_file(self.cfg["asc_key_path"])
        token = jwt.encode({"iss": self.cfg["asc_issuer"], "iat": int(time.time()),
                            "exp": int(time.time()) + 600, "aud": "appstoreconnect-v1"},
                           key.read_text(), algorithm="ES256", headers={"kid": self.cfg["asc_key_id"]})
        if method != "GET":
            write_private(receipt, {"operation": operation, "state": "started", "at": now(), "path": path})
        request = urllib.request.Request("https://api.appstoreconnect.apple.com" + path, method=method,
                                         data=json.dumps(body).encode() if body is not None else None,
                                         headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                result = json.loads(response.read() or "{}")
        except urllib.error.HTTPError as error:
            if method != "GET":
                write_private(receipt, {"operation": operation, "state": "rejected", "status": error.code, "at": now()})
            raise GuardError(f"Apple HTTP {error.code}; provider body suppressed; reconcile before retry") from None
        except (OSError, ValueError):
            raise GuardError("Apple result unknown; reconcile via inventory, do not retry mutations") from None
        if method != "GET":
            write_private(receipt, {"operation": operation, "state": "accepted", "at": now(), "response": result})
        return result

    def rows(self, path):
        rows = []
        for _ in range(20):
            result = self.request("GET", path)
            rows.extend(result["data"])
            following = result.get("links", {}).get("next")
            if not following:
                return rows
            url = urllib.parse.urlparse(following)
            require(url.scheme == "https" and url.netloc == "api.appstoreconnect.apple.com", "Unexpected pagination host")
            path = url.path + ("?" + url.query if url.query else "")
        raise GuardError("Provider pagination incomplete")

    def inventory(self):
        query = urllib.parse.urlencode({"filter[bundleId]": BUNDLE, "limit": 200})
        apps = self.rows("/v1/apps?" + query)
        bundles = self.rows("/v1/bundleIds?" + urllib.parse.urlencode({"filter[identifier]": BUNDLE, "limit": 200}))
        require(len(apps) <= 1 and len(bundles) <= 1, "Ambiguous Musia inventory")
        require(all(r["attributes"]["bundleId"] == BUNDLE for r in apps), "Apple app filter mismatch")
        require(all(r["attributes"]["identifier"] == BUNDLE for r in bundles), "Apple bundle filter mismatch")
        return {"at": now(), "bundle_id": BUNDLE, "apps": apps, "bundle_ids": bundles}

    def app(self):
        apps = self.inventory()["apps"]
        require(len(apps) == 1, "Musia App Store Connect record missing; create it through Apple's website")
        app = apps[0]
        expected = release().get("apple_app_id")
        require(not expected or expected == app["id"], "Configured Apple app ID mismatch")
        return app


def apple_platform_builds(api, app_id, build_number, platform):
    """Build numbers can overlap between an app's iOS and macOS trains."""
    require(platform in {"IOS", "MAC_OS"}, "Unsupported Musia Apple platform")
    query = urllib.parse.urlencode({"filter[app]": app_id, "filter[version]": str(build_number), "limit": 200})
    selected = []
    for row in api.rows("/v1/builds?" + query):
        require(row.get("attributes", {}).get("version") == str(build_number), "Apple build filter mismatch")
        prerelease = api.request("GET", f"/v1/builds/{row['id']}/preReleaseVersion")["data"]
        attributes = prerelease.get("attributes", {})
        require(attributes.get("platform") in {"IOS", "MAC_OS", "TV_OS", "VISION_OS"}
                and bool(attributes.get("version")), "Build platform/version could not be verified")
        if attributes["platform"] == platform:
            selected.append(row)
    return selected


def check_qa(build_path, qa_path, *, internal_beta=False):
    build_path = private_file(build_path)
    build = read_json(build_path)
    qa = read_json(private_file(qa_path))
    require(build.get("bundle_id") == BUNDLE and build.get("state") == "signed", "No signed Musia build receipt")
    platform = build["platform"]
    require(qa.get("platform") == platform and qa.get("bundle_id") == BUNDLE, "QA app/platform mismatch")
    require(qa.get("build_receipt_sha256") == digest(build_path), "QA is not bound to this build receipt")
    require(build["source_sha256"] == source_sha(platform) == qa.get("source_sha256"), "Source changed or QA missing")
    artifact = Path(build["artifact"])
    if not artifact.is_absolute():
        artifact = (build_path.parent / artifact).resolve()
    require(artifact.is_file() and not artifact.is_symlink(), "Artifact missing or symlinked")
    require(digest(artifact) == build["artifact_sha256"] == qa.get("artifact_sha256"), "Artifact hash/QA mismatch")
    current = release()
    require(build["version"] == current["version"] and str(build["build_number"]) ==
            str(current["ios_build"] if platform == "ios" else current["android_version_code"]), "Release version changed")
    require(bool(qa.get("reviewed_at")) and bool(qa.get("qa_environment")), "QA review/environment missing")
    checks = CHECKS
    if internal_beta:
        require(qa.get("scope") == "internal-owner-test" and qa.get("production_qualified") is False,
                "Internal beta receipt must explicitly exclude production qualification")
        require(isinstance(qa.get("known_limitations"), list) and qa["known_limitations"]
                and all(isinstance(x, str) and x.strip() for x in qa["known_limitations"]),
                "Internal beta needs explicit device-test limitations")
        checks = INTERNAL_BETA_CHECKS
    for check in checks:
        item = qa.get("checks", {}).get(check, {})
        require(item.get("status") == "passed", "QA check not passed: " + check)
        evidence = Path(item.get("evidence") or "")
        if not evidence.is_absolute():
            evidence = qa_path.parent / evidence
        require(evidence.is_file() and evidence.stat().st_size > 0
                and not evidence.is_symlink(), "QA evidence missing: " + check)
        require(digest(evidence) == item.get("sha256"), "QA evidence hash mismatch: " + check)
    return dict(build, artifact=str(artifact))
