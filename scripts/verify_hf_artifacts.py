#!/usr/bin/env python3
"""Verify selected local Hugging Face artifacts against repository metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_id", help="Hugging Face model repository ID")
    parser.add_argument("local_dir", type=Path)
    parser.add_argument("paths", nargs="+", help="Repository-relative file paths")
    parser.add_argument(
        "--sha256",
        action="store_true",
        help="Hash every artifact in addition to checking its size",
    )
    args = parser.parse_args()

    api_url = f"https://huggingface.co/api/models/{args.repo_id}?blobs=true"
    with urllib.request.urlopen(api_url, timeout=60) as response:
        metadata = json.load(response)
    siblings = {item["rfilename"]: item for item in metadata.get("siblings", [])}

    failures: list[str] = []
    results: list[dict[str, object]] = []
    for remote_path in args.paths:
        info = siblings.get(remote_path)
        local_path = args.local_dir / remote_path
        result: dict[str, object] = {
            "path": remote_path,
            "local_path": str(local_path.resolve()),
        }
        if info is None:
            failures.append(f"{remote_path}: absent from repository metadata")
            result["status"] = "metadata-missing"
            results.append(result)
            continue
        if not local_path.is_file():
            failures.append(f"{remote_path}: local file is missing")
            result["status"] = "missing"
            results.append(result)
            continue
        if local_path.with_name(local_path.name + ".aria2").exists():
            failures.append(f"{remote_path}: aria2 control file shows an incomplete download")
            result["status"] = "incomplete"
            results.append(result)
            continue

        expected_size = int(info.get("size") or info.get("lfs", {}).get("size") or 0)
        actual_size = local_path.stat().st_size
        result.update(expected_size=expected_size, actual_size=actual_size)
        if expected_size and actual_size != expected_size:
            failures.append(
                f"{remote_path}: size {actual_size} does not match {expected_size}"
            )
            result["status"] = "size-mismatch"
            results.append(result)
            continue

        expected_hash = info.get("lfs", {}).get("sha256")
        if args.sha256 and expected_hash:
            actual_hash = sha256(local_path)
            result.update(expected_sha256=expected_hash, actual_sha256=actual_hash)
            if actual_hash != expected_hash:
                failures.append(f"{remote_path}: SHA-256 mismatch")
                result["status"] = "hash-mismatch"
                results.append(result)
                continue

        result["status"] = "ok"
        results.append(result)

    print(json.dumps({"repo_id": args.repo_id, "files": results}, indent=2))
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
