#!/usr/bin/env python3
"""Validate SongGeneration/LeVo 2 JSONL inputs before expensive inference."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


INSTRUMENTAL_LABELS = {
    "intro-short",
    "intro-medium",
    "inst-short",
    "inst-medium",
    "outro-short",
    "outro-medium",
}
LYRIC_LABELS = {"verse", "chorus", "bridge"}
VALID_LABELS = INSTRUMENTAL_LABELS | LYRIC_LABELS
CHINESE_PUNCTUATION = re.compile(r"[，。！？；：、（）【】“”‘’]")
SECTION_PATTERN = re.compile(r"^\[([a-z-]+)](?:\s+(.*))?$")
BPM_PATTERN = re.compile(r"(?:the\s+)?bpm\s+is\s+\d+(?:\.\d+)?\.?", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_jsonl", type=Path)
    parser.add_argument(
        "--backend-dir",
        type=Path,
        default=Path("third_party/SongGeneration-v2"),
    )
    parser.add_argument(
        "--strict-tags",
        action="store_true",
        help="Reject description tags outside the upstream recommended lists.",
    )
    return parser.parse_args()


def load_supported_tags(backend_dir: Path) -> set[str]:
    description_dir = backend_dir / "sample" / "description"
    tags: set[str] = set()
    for name in ("gender.txt", "genre.txt", "emotion.txt", "instrument.txt"):
        path = description_dir / name
        if not path.is_file():
            continue
        tags.update(
            line.strip().casefold()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    return tags


def validate_record(
    record: object,
    line_number: int,
    supported_tags: set[str],
    strict_tags: bool,
) -> tuple[list[str], list[str], str | None]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(record, dict):
        return [f"line {line_number}: record must be a JSON object"], warnings, None

    idx = record.get("idx")
    if not isinstance(idx, str) or not idx.strip():
        errors.append(f"line {line_number}: idx must be a non-empty string")
        idx = None

    lyric = record.get("gt_lyric")
    if not isinstance(lyric, str) or not lyric.strip():
        errors.append(f"line {line_number}: gt_lyric must be a non-empty string")
    else:
        if CHINESE_PUNCTUATION.search(lyric):
            errors.append(
                f"line {line_number}: gt_lyric contains unsupported full-width punctuation"
            )
        sections = [section.strip() for section in lyric.split(";") if section.strip()]
        if not sections:
            errors.append(f"line {line_number}: gt_lyric has no sections")
        for section_index, section in enumerate(sections, start=1):
            match = SECTION_PATTERN.fullmatch(section)
            if not match:
                errors.append(
                    f"line {line_number}, section {section_index}: invalid section syntax"
                )
                continue
            label, text = match.group(1), (match.group(2) or "").strip()
            if label not in VALID_LABELS:
                errors.append(
                    f"line {line_number}, section {section_index}: unknown label [{label}]"
                )
            elif label in INSTRUMENTAL_LABELS and text:
                errors.append(
                    f"line {line_number}, section {section_index}: "
                    f"[{label}] must not contain lyrics"
                )
            elif label in LYRIC_LABELS and not text:
                errors.append(
                    f"line {line_number}, section {section_index}: "
                    f"[{label}] requires lyrics"
                )

    descriptions = record.get("descriptions")
    if descriptions is not None:
        if not isinstance(descriptions, str) or not descriptions.strip():
            errors.append(f"line {line_number}: descriptions must be a non-empty string")
        elif supported_tags:
            unknown = []
            for raw_tag in descriptions.split(","):
                tag = raw_tag.strip().casefold()
                if not tag or tag in supported_tags or BPM_PATTERN.fullmatch(tag):
                    continue
                unknown.append(raw_tag.strip())
            if unknown:
                message = (
                    f"line {line_number}: non-recommended description tags: "
                    + ", ".join(unknown)
                )
                (errors if strict_tags else warnings).append(message)

    if descriptions and record.get("prompt_audio_path"):
        warnings.append(
            f"line {line_number}: descriptions and prompt_audio_path can conflict"
        )
    return errors, warnings, idx


def main() -> int:
    args = parse_args()
    if not args.input_jsonl.is_file():
        print(f"Missing input: {args.input_jsonl}", file=sys.stderr)
        return 2

    supported_tags = load_supported_tags(args.backend_dir)
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    record_count = 0

    for line_number, raw_line in enumerate(
        args.input_jsonl.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        record_count += 1
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
            continue
        record_errors, record_warnings, idx = validate_record(
            record,
            line_number,
            supported_tags,
            args.strict_tags,
        )
        errors.extend(record_errors)
        warnings.extend(record_warnings)
        if idx:
            if idx in seen_ids:
                errors.append(f"line {line_number}: duplicate idx: {idx}")
            seen_ids.add(idx)

    if not record_count:
        errors.append("input contains no records")
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print(
        f"Validated {record_count} SongGeneration v2 record(s); "
        f"{len(warnings)} warning(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
