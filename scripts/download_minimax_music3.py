#!/usr/bin/env python3
"""Download only the official Diffusers-format Music 3 components, resumably."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "MiniMaxAI/MiniMax-Music3"
REVISION = "fbdf52fbaaca799592917417eb05f1899f1255ec"
COMPONENTS = (
    "condition_encoder", "language_model", "rvq_depth_decoder", "scheduler",
    "tokenizer", "transformer", "vocoder",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default=REVISION)
    parser.add_argument("--model-dir", type=Path, default=ROOT / "third_party/MiniMax-Music3/checkpoints/diffusers")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--verify-sha256", action="store_true")
    parser.add_argument("--transport", choices=["hub", "aria2"], default="hub")
    parser.add_argument("--endpoint", default="https://huggingface.co", help="Download transport only; metadata/hashes always come from the official Hub")
    parser.add_argument("--modelscope-mirror", action="store_true", help="Add hash-matched official ModelScope URLs to aria2 downloads")
    args = parser.parse_args()
    os.environ.setdefault("HF_HOME", str(ROOT / ".cache/huggingface"))
    from huggingface_hub import HfApi, snapshot_download

    info = HfApi().model_info(MODEL_ID, revision=args.revision, files_metadata=True)
    selected = [item for item in info.siblings if item.rfilename in {"LICENSE", "README.md", "modular_model_index.json"}
                or item.rfilename.split("/", 1)[0] in COMPONENTS]
    print(f"Downloading {MODEL_ID}@{info.sha}: {len(selected)} files, {sum(f.size or 0 for f in selected) / 1e9:.2f} GB", flush=True)
    if args.transport == "hub":
        snapshot_download(MODEL_ID, revision=info.sha, local_dir=args.model_dir,
                          allow_patterns=[item.rfilename for item in selected], max_workers=args.workers,
                          endpoint=args.endpoint)
    else:
        scope_files = {}
        if args.modelscope_mirror:
            import requests
            response = requests.get("https://modelscope.cn/api/v1/models/MiniMax/MiniMax-Music3/repo/files",
                                    params={"Revision": "master", "Recursive": "true"}, timeout=30)
            response.raise_for_status()
            scope_files = {item["Path"]: item for item in response.json()["Data"]["Files"]}
        args.model_dir.mkdir(parents=True, exist_ok=True)
        inputs = []
        for item in selected:
            path = args.model_dir.resolve() / item.rfilename
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.is_file() and path.stat().st_size == item.size and not Path(str(path) + ".aria2").exists():
                continue
            urls = [f"{args.endpoint.rstrip('/')}/{MODEL_ID}/resolve/{info.sha}/{item.rfilename}"]
            mirror = scope_files.get(item.rfilename)
            if item.lfs and mirror and mirror.get("Sha256") == item.lfs.sha256 and mirror.get("Size") == item.size:
                urls.insert(0, f"https://modelscope.cn/models/MiniMax/MiniMax-Music3/resolve/master/{item.rfilename}")
            inputs.extend(["\t".join(urls),
                           f"  dir={path.parent}", f"  out={path.name}"])
            if item.lfs:
                inputs.append(f"  checksum=sha-256={item.lfs.sha256}")
        input_file = args.model_dir / ".musia-aria2-input.txt"
        input_file.write_text("\n".join(inputs) + "\n")
        if inputs:
            subprocess.run(["aria2c", "--input-file", str(input_file), "--continue=true",
                            "--auto-file-renaming=false", "--file-allocation=none", "--split=16",
                            "--max-connection-per-server=16", f"--max-concurrent-downloads={args.workers}",
                            "--min-split-size=4M", "--summary-interval=30", "--console-log-level=warn",
                            "--show-console-readout=false", "--download-result=full", "--max-tries=10", "--retry-wait=3"], check=True)
    records = []
    for item in selected:
        path = args.model_dir / item.rfilename
        if not path.is_file() or path.stat().st_size != item.size:
            raise RuntimeError(f"Incomplete download: {path}")
        expected = getattr(item.lfs, "sha256", None) if item.lfs else None
        verified = False
        if args.verify_sha256 and expected:
            digest = sha256_file(path)
            if digest != expected:
                raise RuntimeError(f"Checksum mismatch: {path}")
            verified = True
        if args.verify_sha256 and not expected and item.blob_id:
            payload = path.read_bytes()
            digest = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
            if digest != item.blob_id:
                raise RuntimeError(f"Git blob checksum mismatch: {path}")
        records.append({"path": item.rfilename, "bytes": item.size, "expected_sha256": expected, "sha256_verified": verified})
    manifest = {"model_id": MODEL_ID, "revision": info.sha, "format": "diffusers-modular",
                "checked_at": datetime.now(timezone.utc).isoformat(), "files": records,
                "license": "LICENSE", "commercial_release_review_required": True}
    (args.model_dir / "musia-download.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Verified download manifest: {args.model_dir / 'musia-download.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
