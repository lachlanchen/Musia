"""Dependency-free HTTP acceptance for the bounded public learning contract."""

from __future__ import annotations

import argparse
import http.client
import io
import json
import ssl
import wave
from urllib.parse import urlsplit


class Client:
    def __init__(self, base_url, connect_ip=None):
        self.url = urlsplit(base_url)
        self.connect_ip = connect_ip

    def request(self, path, method="GET", headers=None, body=None):
        port = self.url.port or (443 if self.url.scheme == "https" else 80)
        if self.url.scheme == "https":
            connection = http.client.HTTPSConnection(self.url.hostname, port, timeout=30)
            if self.connect_ip:
                import socket
                raw = socket.create_connection((self.connect_ip, port), timeout=30)
                connection.sock = ssl.create_default_context().wrap_socket(raw, server_hostname=self.url.hostname)
        else:
            connection = http.client.HTTPConnection(self.connect_ip or self.url.hostname, port, timeout=30)
        try:
            connection.request(method, path, body=body, headers={"Host": self.url.netloc, **(headers or {})})
            response = connection.getresponse()
            data = response.read(8 * 1024 * 1024 + 1)
            assert len(data) <= 8 * 1024 * 1024, "response exceeds acceptance limit"
            return response.status, dict((k.lower(), v) for k, v in response.getheaders()), data
        finally:
            connection.close()


def check(client, expected_ids=None, static_paths=None):
    evidence = []

    def get(path, expected=200, method="GET", headers=None, body=None):
        status, response_headers, data = client.request(path, method, headers, body)
        assert status == expected, f"{method} {path}: expected {expected}, got {status}"
        assert response_headers.get("x-content-type-options") == "nosniff", path
        evidence.append({"method": method, "path": path, "status": status, "bytes": len(data)})
        return response_headers, data

    _, raw = get("/healthz")
    assert json.loads(raw) == {"status": "ok"}
    _, raw = get("/api/v1/capabilities")
    capability = json.loads(raw)
    assert capability["readOnly"] is True
    assert all(capability[k]["available"] is False for k in ("cloudGeneration", "upload", "aiCoaching", "accounts"))
    _, raw = get("/api/v1/library")
    catalog = json.loads(raw)["items"]
    ids = [item["id"] for item in catalog]
    assert ids and ids[0] == "first-pulse" and len(ids) == len(set(ids))
    if expected_ids is not None:
        assert ids == expected_ids, "published catalog differs from reviewed release"
    for song_id in ids:
        _, raw = get("/api/v1/songs/" + song_id)
        song = json.loads(raw)
        assert song["id"] == song_id and song["assets"]
        assert not any(marker in raw for marker in (b"/home/", b"/Users/", b"data/runs/", b"data/creative_projects/", b"file://"))
        for asset in song["assets"]:
            assert asset["audioUrl"].startswith("https://")
    _, raw = get("/api/v1/lessons")
    assert len(json.loads(raw)["lessons"]) >= 3
    _, audio = get("/api/v1/exercises/first-pulse/audio.wav")
    with wave.open(io.BytesIO(audio)) as stream:
        assert stream.getnchannels() == 1 and stream.getframerate() == 24000
        assert stream.getnframes() == 22 * 24000
    headers, part = get("/api/v1/exercises/first-pulse/audio.wav", 206, headers={"Range": "bytes=0-43"})
    assert part == audio[:44] and headers["content-range"].startswith("bytes 0-43/")
    get("/api/v1/exercises/first-pulse/audio.wav", 416, headers={"Range": "bytes=999999999-"})
    for path in static_paths or ["/", "/app.js", "/core.js", "/styles.css", "/privacy", "/support", "/vendor/lucide.js", "/assets/musia.js", "/assets/brand.png"]:
        _, content = get(path)
        assert content, f"empty static asset: {path}"
    for path in ("/docs", "/redoc", "/openapi.json", "/api/settings", "/api/chat/send", "/api/v1/generate", "/api/v1/upload", "/api/v1/songs/not-a-shipped-song", "/.env", "/musia/learning.py", "/assets/not-present.js"):
        get(path, 404)
    for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
        get("/api/v1/library", 405, method=method)
    for path in ("/api/v1/songs/%2e%2e", "/api/v1/songs/a%2fb", "/assets/../.env", "/api/v1/songs/%252e%252e"):
        status, _, _ = client.request(path)
        assert status in (400, 404), (path, status)
        evidence.append({"method": "GET", "path": path, "status": status})
    status, _, _ = client.request("/healthz", body=b"x", headers={"Content-Length": "1"})
    assert status == 400, f"GET body accepted: {status}"
    _, body = get("/api/v1/library", method="HEAD")
    assert not body
    return {"passed": True, "songCount": len(ids), "checks": evidence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url")
    parser.add_argument("--connect-ip")
    parser.add_argument("--release-manifest")
    args = parser.parse_args()
    manifest = {}
    if args.release_manifest:
        from pathlib import Path
        manifest = json.loads(Path(args.release_manifest).read_text())
    print(json.dumps(check(Client(args.base_url, args.connect_ip), manifest.get("songIds"), manifest.get("staticPaths")), sort_keys=True))


if __name__ == "__main__":
    main()
