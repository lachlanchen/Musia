#!/usr/bin/env python3
"""Upload a genuine native paywall PNG for one approved Musia subscription.

Default: provider readback only. --confirm-upload reserves, uploads, and commits
the exact --sha256 bytes; it never replaces screenshots or submits any review.
The caller must select a genuine, legible native capture for the selected tier.
Existing intents are readback-only, including after an interrupted upload. Do
not remove journals to retry. COMPLETE proves asset processing, not billing QA.

Protocol: https://developer.apple.com/documentation/appstoreconnectapi/uploading-assets-to-app-store-connect
Only documented, unexpired signed store-NNN.blobstore.apple.com URLs are allowed.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import time
from urllib.parse import parse_qs, urlsplit
import zlib

import jwt
import requests
from requests.adapters import HTTPAdapter

from creator_catalog import APP, BUNDLE, GROUP, PLANS, relationship
from storelib import Apple, GuardError, RUNTIME, lock, now, private_file, read_json, require, write_private

KIND = "subscriptionAppStoreReviewScreenshots"
RESOURCE = "/v1/" + KIND
API = "https://api.appstoreconnect.apple.com"
MAX_BYTES = 20 * 1024 * 1024


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9-]{1,100}", value), "Invalid Apple resource ID")
    return value


def isolated_session():
    session = requests.Session()
    session.trust_env = False
    session.auth = None
    session.headers.clear()
    session.cookies.clear()
    session.mount("https://", HTTPAdapter(max_retries=0))
    return session


class ScreenshotAPI(Apple):
    """Reuse Apple inventory/pagination guards without widening its write allowlist."""
    def request(self, method, path, body=None, operation=None):
        route = urlsplit(path)
        require(not route.scheme and not route.netloc and not route.fragment and ".." not in path,
                "Invalid Apple API path")
        allowed_read = (route.path in {"/v1/apps", "/v1/bundleIds", f"/v1/apps/{APP}/subscriptionGroups"}
                        or re.fullmatch(r"/v1/subscriptionGroups/[A-Za-z0-9-]+/subscriptions", route.path)
                        or re.fullmatch(r"/v1/subscriptions/[A-Za-z0-9-]+(?:/appStoreReviewScreenshot)?", route.path))
        require((method == "GET" and allowed_read)
                or (method == "POST" and path == RESOURCE)
                or (method == "PATCH" and re.fullmatch(RESOURCE + r"/[A-Za-z0-9-]+", path)),
                "Only subscription screenshot reservation and commit writes are allowed")
        if method != "GET":
            require(operation is not None, "Screenshot mutation requires durable intent")
            record = read_json(private_file(operation))
            require(record.get("state") == {"POST": "reserve_started", "PATCH": "commit_started"}[method]
                    and record.get("request") == {"method": method, "path": path, "body": body},
                    "Screenshot mutation does not match durable intent")
        token = jwt.encode({"iss": self.cfg["asc_issuer"], "iat": int(time.time()),
                            "exp": int(time.time()) + 300, "aud": "appstoreconnect-v1"},
                           private_file(self.cfg["asc_key_path"]).read_text(), algorithm="ES256",
                           headers={"kid": self.cfg["asc_key_id"]})
        try:
            with isolated_session() as session:
                response = session.request(method, API + path, headers={"Authorization": "Bearer " + token},
                                           **({"json": body} if body is not None else {}),
                                           timeout=(10, 45), allow_redirects=False, verify=True)
            if method == "GET" and route.path.endswith("/appStoreReviewScreenshot") and response.status_code == 404:
                return {"data": None}
            require(response.status_code == (201 if method == "POST" else 200), "Unexpected Apple screenshot HTTP status")
            require(bool(response.content) and len(response.content) <= 2 * 1024 * 1024, "Invalid Apple screenshot response size")
            value = response.json()
            require(isinstance(value, dict) and "data" in value and "errors" not in value, "Invalid Apple screenshot response")
            return value
        except Exception:
            raise GuardError("Apple screenshot response unconfirmed; use readback, never blindly retry") from None


def png_input(path, sha256):
    require(isinstance(sha256, str) and re.fullmatch(r"[0-9a-f]{64}", sha256), "Exact lowercase PNG SHA-256 required")
    path = private_file(Path(path).expanduser().absolute())
    require(path.suffix.lower() == ".png" and 0 < path.stat().st_size <= MAX_BYTES, "Expected bounded private PNG file")
    with path.open("rb") as handle:
        payload = handle.read(MAX_BYTES + 1)
    require(len(payload) <= MAX_BYTES and hashlib.sha256(payload).hexdigest() == sha256, "PNG hash/size mismatch")
    require(payload.startswith(b"\x89PNG\r\n\x1a\n"), "Expected PNG signature")
    offset, has_data = 8, False
    # Validate the PNG container without re-encoding bytes. Apple validates the
    # decoded image during processing; this does not establish capture provenance.
    while offset + 12 <= len(payload):
        length, kind = struct.unpack(">I4s", payload[offset:offset + 8])
        end = offset + length + 12
        require(end <= len(payload), "Truncated PNG chunk")
        data = payload[offset + 8:end - 4]
        crc = struct.unpack(">I", payload[end - 4:end])[0]
        require(zlib.crc32(kind + data) & 0xffffffff == crc, "Invalid PNG chunk checksum")
        if offset == 8:
            require(kind == b"IHDR" and length == 13, "Missing PNG header")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", data)
            depths = {0: {1, 2, 4, 8, 16}, 2: {8, 16}, 3: {1, 2, 4, 8}, 4: {8, 16}, 6: {8, 16}}
            require(width > 0 and height > 0 and width * height <= 25000000 and depth in depths.get(color, set())
                    and compression == filtering == 0 and interlace in {0, 1}, "Unsupported PNG header")
        else:
            require(kind != b"IHDR", "Duplicate PNG header")
        require(kind not in {b"acTL", b"fcTL", b"fdAT"}, "Animated PNG is not a native screenshot")
        if kind == b"IDAT":
            has_data = has_data or length > 0
        if kind == b"IEND":
            require(length == 0 and has_data and end == len(payload), "Invalid PNG end/data")
            return payload
        offset = end
    raise GuardError("Incomplete PNG container")


def subscription(api, tier):
    require(tier in PLANS, "Only Creator and Studio subscriptions are approved")
    require(api.app()["id"] == APP, "Wrong Apple app")
    groups = api.rows(f"/v1/apps/{APP}/subscriptionGroups")
    require(len(groups) == 1 and groups[0]["attributes"]["referenceName"] == GROUP, "Unexpected Musia subscription group")
    gid = identifier(groups[0]["id"])
    products = api.rows(f"/v1/subscriptionGroups/{gid}/subscriptions")
    expected = {f"{BUNDLE}.{t}.monthly" for t in PLANS}
    require(len(products) == 2 and {p["attributes"]["productId"] for p in products} == expected
            and all(p["attributes"]["subscriptionPeriod"] == "ONE_MONTH" for p in products),
            "Expected exactly the two approved monthly Musia subscriptions")
    pid = f"{BUNDLE}.{tier}.monthly"
    selected = next(p for p in products if p["attributes"]["productId"] == pid)
    sid = identifier(selected["id"])
    fresh = api.request("GET", f"/v1/subscriptions/{sid}")["data"]
    require(fresh["id"] == sid and fresh["type"] == "subscriptions"
            and fresh["attributes"]["productId"] == pid and fresh["attributes"]["subscriptionPeriod"] == "ONE_MONTH",
            "Subscription identity changed")
    return fresh


def journal_path(tier):
    require(tier in PLANS, "Unapproved subscription")
    stable = f"{APP}:{BUNDLE}.{tier}.monthly:review-screenshot"
    return RUNTIME / "creator-apple-screenshots" / (hashlib.sha256(stable.encode()).hexdigest() + ".json")


def screenshot(api, sid):
    value = api.request("GET", f"/v1/subscriptions/{sid}/appStoreReviewScreenshot?include=subscription")["data"]
    if value is not None:
        require(value.get("relationships", {}).get("subscription", {}).get("data") == relationship("subscriptions", sid)["data"],
                "Screenshot subscription ownership is unconfirmed")
    return value


def check_screenshot(value, identity, screenshot_id=None):
    require(isinstance(value, dict) and value.get("type") == KIND, "Wrong screenshot resource")
    sid = identifier(value.get("id"))
    require(screenshot_id is None or sid == screenshot_id, "Screenshot reservation changed")
    attrs = value.get("attributes", {})
    require(attrs.get("fileName") == identity["fileName"] and attrs.get("fileSize") == identity["fileSize"],
            "Existing screenshot differs; replacement is not authorized")
    checksum = attrs.get("sourceFileChecksum")
    state = attrs.get("assetDeliveryState", {}).get("state")
    require(state in {"AWAITING_UPLOAD", "UPLOAD_COMPLETE", "COMPLETE", "FAILED"}, "Unknown screenshot processing state")
    require(checksum in {None, identity["md5"]}, "Screenshot checksum mismatch")
    if state in {"UPLOAD_COMPLETE", "COMPLETE"}:
        require(checksum == identity["md5"], "Processed screenshot must have the exact source MD5")
    require(state != "FAILED" and not attrs.get("assetDeliveryState", {}).get("errors"),
            "Screenshot processing failed; no replacement or retry authorized")
    return state


def asset_url(url):
    require(isinstance(url, str) and url.isascii() and not any(ord(c) <= 32 for c in url) and "\\" not in url,
            "Invalid asset URL")
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    require(parsed.scheme == "https" and re.fullmatch(r"store-[0-9]{3}\.blobstore\.apple\.com", host)
            and parsed.netloc in {host, host + ":443"} and not parsed.fragment
            and parsed.path.startswith("/assets-") and not parsed.username and not parsed.password,
            "Only strict HTTPS Apple blobstore asset hosts are allowed")
    query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
    require(all(len(query.get(key, [])) == 1 and query[key][0] for key in ["Signature", "AWSAccessKeyId", "Expires"]),
            "Expected Apple's provider-issued signed upload URL")
    require(re.fullmatch(r"[0-9]{1,12}", query["Expires"][0]) and int(query["Expires"][0]) > time.time(),
            "Expired or invalid signed upload URL")
    return url


def upload_operations(value, payload):
    operations = value.get("attributes", {}).get("uploadOperations")
    require(isinstance(operations, list) and 0 < len(operations) <= 100, "Missing/bounded upload operations required")
    checked = []
    for operation in operations:
        require(operation.get("method") == "PUT", "Only prescribed PUT asset operations are allowed")
        url = asset_url(operation.get("url"))
        offset, length = operation.get("offset"), operation.get("length")
        require(type(offset) is int and type(length) is int and offset >= 0 and length > 0
                and offset + length <= len(payload), "Invalid upload byte range")
        headers = {}
        require(isinstance(operation.get("requestHeaders"), list), "Missing upload headers")
        for header in operation["requestHeaders"]:
            name, value = header.get("name"), header.get("value")
            require(isinstance(name, str) and name.lower() in {"content-type", "content-length", "content-md5"}
                    and name.lower() not in headers and isinstance(value, str) and value.isascii()
                    and not any(ord(c) < 32 or ord(c) == 127 for c in value), "Unsafe or duplicate asset header")
            headers[name.lower()] = value
        require(headers.get("content-type") in {"image/png", "application/octet-stream"}, "Unexpected asset content type")
        require("content-length" not in headers or headers["content-length"] == str(length), "Wrong asset content length")
        md5 = base64.b64encode(hashlib.md5(payload[offset:offset + length], usedforsecurity=False).digest()).decode()
        require("content-md5" not in headers or headers["content-md5"] == md5, "Wrong asset part checksum")
        checked.append({"url": url, "offset": offset, "length": length, "headers": headers})
    checked.sort(key=lambda part: part["offset"])
    end = 0
    for part in checked:
        require(part["offset"] == end, "Upload ranges overlap or leave gaps")
        end += part["length"]
    require(end == len(payload), "Upload operations do not cover the entire PNG")
    return checked


def upload_part(part, payload):
    try:
        with isolated_session() as session:
            response = session.request("PUT", asset_url(part["url"]), headers=part["headers"],
                                       data=payload[part["offset"]:part["offset"] + part["length"]],
                                       timeout=(10, 45), allow_redirects=False, verify=True)
        require(200 <= response.status_code < 300, "Asset upload HTTP failure")
    except Exception:
        raise GuardError("Asset upload unconfirmed; protected journal requires readback, not automatic retry") from None


def upload(tier, png, sha256, confirm=False):
    payload = png_input(png, sha256)
    require(tier in PLANS, "Unapproved subscription")
    with lock("creator-apple-review-screenshot"):
        api = ScreenshotAPI()
        selected = subscription(api, tier)
        sid = selected["id"]
        identity = {"app": APP, "bundle": BUNDLE, "product": selected["attributes"]["productId"], "subscription": sid,
                    "sha256": sha256, "md5": hashlib.md5(payload, usedforsecurity=False).hexdigest(),
                    "fileName": f"musia-{tier}-review-{sha256}.png", "fileSize": len(payload)}
        path = journal_path(tier)
        previous = read_json(private_file(path)) if path.exists() else None
        if previous is not None:
            require(previous.get("schema") == 1 and previous.get("identity") == identity
                    and previous.get("state") in {"reserve_started", "reserved", "upload_started", "part_uploaded",
                                                  "commit_started", "unknown", "processing", "complete"},
                    "Screenshot journal identity mismatch; do not bypass an earlier attempt")
        existing = screenshot(api, sid)
        result = {"app": APP, "product": identity["product"], "sha256": sha256, "processingComplete": False,
                  "appReviewChanged": False, "subscriptionReviewSubmitted": False, "purchasesAuthorized": False}
        if existing is not None:
            state = check_screenshot(existing, identity, previous.get("screenshot_id") if previous else None)
            require(state in {"COMPLETE", "UPLOAD_COMPLETE"}, "Existing reservation requires manual reconciliation; no upload retry")
            if previous and confirm:
                previous.update(state="complete" if state == "COMPLETE" else "processing", at=now(), readback=existing)
                write_private(path, previous)
            return dict(result, state=state, processingComplete=state == "COMPLETE", action="verified_readback")
        require(previous is None, "Previous reservation unconfirmed; readback only, never reserve again")
        require(selected["attributes"].get("state") in {"MISSING_METADATA", "READY_TO_SUBMIT"},
                "Only an unsubmitted subscription draft may receive a new screenshot")
        if not confirm:
            return dict(result, state="plan_only", action="would_reserve")
        record = {"schema": 1, "identity": identity, "state": "reserve_started", "at": now()}
        body = {"data": {"type": KIND, "attributes": {key: identity[key] for key in ["fileName", "fileSize"]},
                         "relationships": {"subscription": relationship("subscriptions", sid)}}}
        record["request"] = {"method": "POST", "path": RESOURCE, "body": body}
        write_private(path, record)
        try:
            reserved = api.request("POST", RESOURCE, body, operation=path)["data"]
            require(check_screenshot(reserved, identity) == "AWAITING_UPLOAD", "Unexpected reservation state")
            record.update(state="reserved", screenshot_id=reserved["id"], reservation=reserved)
            write_private(path, record)
            linked = screenshot(api, sid)
            require(check_screenshot(linked, identity, reserved["id"]) == "AWAITING_UPLOAD", "Reservation readback mismatch")
            parts = upload_operations(reserved, payload)
            # Validate every host/header/range before sending any PNG bytes.
            for index, part in enumerate(parts):
                record.update(state="upload_started", part=index, at=now())
                write_private(path, record)
                upload_part(part, payload)
                record.update(state="part_uploaded", part=index)
                write_private(path, record)
            commit = {"data": {"type": KIND, "id": reserved["id"],
                               "attributes": {"uploaded": True, "sourceFileChecksum": identity["md5"]}}}
            commit_path = RESOURCE + "/" + reserved["id"]
            record.update(state="commit_started", at=now(), request={"method": "PATCH", "path": commit_path, "body": commit})
            write_private(path, record)
            committed = api.request("PATCH", commit_path, commit, operation=path)["data"]
            require(check_screenshot(committed, identity, reserved["id"]) in {"UPLOAD_COMPLETE", "COMPLETE"}, "Commit unconfirmed")
            fresh = screenshot(api, sid)
            state = check_screenshot(fresh, identity, reserved["id"])
            require(state in {"UPLOAD_COMPLETE", "COMPLETE"}, "Commit readback unconfirmed")
            record.update(state="complete" if state == "COMPLETE" else "processing", at=now(), readback=fresh)
            write_private(path, record)
            return dict(result, state=state, processingComplete=state == "COMPLETE", action="uploaded_readback")
        except Exception:
            record.update(state="unknown", at=now())
            write_private(path, record)
            raise GuardError("Screenshot outcome unconfirmed; rerun for readback only, never remove journals to retry") from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", choices=tuple(PLANS), required=True)
    parser.add_argument("--png", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--confirm-upload", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(upload(args.tier, args.png, args.sha256, args.confirm_upload), indent=2))
        return 0
    except Exception as error:
        print(str(error) if isinstance(error, GuardError) else "Invalid screenshot/config/provider input; no retry authorized", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
