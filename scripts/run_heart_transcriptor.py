#!/usr/bin/env python3
"""Transcribe a separated singing-vocal stem with HeartTranscriptor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
HEARTMULA_SRC = ROOT / "third_party" / "HeartMuLa" / "src"
sys.path.insert(0, str(HEARTMULA_SRC))

from heartlib import HeartTranscriptorPipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument(
        "--model-path",
        type=Path,
        default=ROOT / "third_party" / "HeartMuLa" / "ckpt",
        help=(
            "Checkpoint root containing HeartTranscriptor-oss, or the "
            "HeartTranscriptor-oss directory itself"
        ),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=256,
        help="Tokens per transcription chunk (default: 256; capped at 440)",
    )
    args = parser.parse_args()

    if not args.audio.is_file():
        raise FileNotFoundError(args.audio)
    model_path = args.model_path.resolve()
    if model_path.name == "HeartTranscriptor-oss":
        model_path = model_path.parent
    if not (model_path / "HeartTranscriptor-oss").is_dir():
        raise FileNotFoundError(model_path / "HeartTranscriptor-oss")
    if not torch.cuda.is_available():
        raise RuntimeError("HeartTranscriptor requires a CUDA GPU")
    if args.max_new_tokens < 1:
        raise ValueError("--max-new-tokens must be positive")
    max_new_tokens = min(args.max_new_tokens, 440)

    pipeline = HeartTranscriptorPipeline.from_pretrained(
        str(model_path),
        device=torch.device("cuda:0"),
        dtype=torch.float16,
    )
    with torch.no_grad():
        result = pipeline(
            str(args.audio.resolve()),
            max_new_tokens=max_new_tokens,
            num_beams=2,
            task="transcribe",
            condition_on_prev_tokens=False,
            compression_ratio_threshold=1.8,
            temperature=(0.0, 0.1, 0.2, 0.4),
            logprob_threshold=-1.0,
            no_speech_threshold=0.4,
        )

    payload = {
        "engine": "HeartTranscriptor-oss",
        "audio": str(args.audio.resolve()),
        "result": result,
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(args.output.resolve())
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
