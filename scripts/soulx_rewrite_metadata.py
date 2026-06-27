#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pypinyin import Style, pinyin


def chinese_chars(text: str) -> list[str]:
    return [char for char in text if "\u4e00" <= char <= "\u9fff"]


def char_to_soulx_phone(char: str) -> str:
    py = pinyin(char, style=Style.TONE3, heteronym=False, neutral_tone_with_five=True)[0][0]
    return "zh_" + py.replace("ü", "u:").replace("v", "u:")


def rewrite_item(item: dict, target_text: str) -> dict:
    text_tokens = item["text"].split()
    sung_positions = [index for index, token in enumerate(text_tokens) if token != "<SP>"]
    chars = chinese_chars(target_text)
    if len(chars) != len(sung_positions):
        raise ValueError(
            f"target Chinese character count ({len(chars)}) must match metadata sung-token count ({len(sung_positions)})"
        )

    new_text_tokens = list(text_tokens)
    new_phone_tokens = item["phoneme"].split()
    if len(new_phone_tokens) != len(text_tokens):
        raise ValueError("metadata text/phoneme token counts differ")

    for char, position in zip(chars, sung_positions):
        new_text_tokens[position] = char
        new_phone_tokens[position] = char_to_soulx_phone(char)

    rewritten = dict(item)
    rewritten["language"] = "Mandarin"
    rewritten["text"] = " ".join(new_text_tokens)
    rewritten["phoneme"] = " ".join(new_phone_tokens)
    rewritten["musai_target_text"] = target_text
    return rewritten


def main() -> None:
    parser = argparse.ArgumentParser(description="Rewrite SoulX metadata with Mandarin target lyrics while preserving note/F0 timing.")
    parser.add_argument("--input", type=Path, required=True, help="Input SoulX metadata JSON.")
    parser.add_argument("--target-text", required=True, help="Mandarin target lyric text. Chinese character count must match non-<SP> tokens.")
    parser.add_argument("--output", type=Path, required=True, help="Output metadata JSON.")
    args = parser.parse_args()

    items = json.loads(args.input.read_text(encoding="utf-8"))
    if not items:
        raise SystemExit("input metadata is empty")

    rewritten = [rewrite_item(items[0], args.target_text)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rewritten, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
