#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from openai import OpenAI


SYSTEM_PROMPT = """You are Musai LyricFit, a lyric-localization assistant.
Return singable target-language lyric candidates that preserve meaning, emotion, phrase duration, syllable count, and rhyme where possible.
Do not output copyrighted source lyrics beyond the user-provided excerpt. Return JSON only."""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate singable lyric adaptation candidates with OpenAI.")
    parser.add_argument("--phrase-json", type=Path, required=True, help="JSON phrase constraints.")
    parser.add_argument("--target-language", default="zh-CN")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set. Add it to your shell or .env before running this helper.")

    phrase = json.loads(args.phrase_json.read_text(encoding="utf-8"))
    client = OpenAI()
    response = client.responses.create(
        model=args.model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "target_language": args.target_language,
                        "phrase": phrase,
                        "required_output": {
                            "literal": "literal meaning translation",
                            "candidates": [
                                {
                                    "style": "singable/pop/poetic/shorter",
                                    "text": "target lyric",
                                    "syllable_estimate": 0,
                                    "rhyme_note": "short note",
                                    "fit_rationale": "short note",
                                }
                            ],
                        },
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(response.output_text + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()

