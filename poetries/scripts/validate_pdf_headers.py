#!/usr/bin/env python3
"""Validate local poetry PDF targets listed in poetries/poetry_pdf_targets.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--catalog",
        default="poetries/poetry_pdf_targets.json",
        help="Path to the Musia poetry PDF target catalog.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any target is missing or invalid.",
    )
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    repo_root = catalog_path.resolve().parents[1]
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    missing: list[Path] = []
    invalid: list[Path] = []
    valid: list[Path] = []

    for target in catalog["targets"]:
        path = repo_root / target["local_path"]
        if not path.exists():
            missing.append(path)
            print(f"MISSING {target['id']}: {path}")
            continue
        header = path.read_bytes()[:4]
        if header != b"%PDF":
            invalid.append(path)
            print(f"INVALID {target['id']}: {path} header={header!r}")
            continue
        valid.append(path)
        print(f"OK {target['id']}: {path} bytes={path.stat().st_size}")

    print()
    print(f"valid={len(valid)} missing={len(missing)} invalid={len(invalid)}")

    if args.strict and (missing or invalid):
        return 1
    if invalid:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
