#!/usr/bin/env python3
"""Score a generated song with the local APEX aesthetic-quality model."""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch
from transformers import AutoConfig, AutoModel, AutoProcessor


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "third_party" / "APEX"
DEFAULT_MERT = DEFAULT_MODEL / "mert-v1-95m"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--mert-dir", type=Path, default=DEFAULT_MERT)
    parser.add_argument(
        "--device",
        choices=("auto", "cuda", "cpu"),
        default="auto",
        help="Inference device (default: CUDA when available).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.audio.is_file():
        print(f"Missing audio: {args.audio}", file=sys.stderr)
        return 2
    for path, label in ((args.model_dir, "APEX"), (args.mert_dir, "MERT")):
        if not (path / "config.json").is_file():
            print(f"Missing {label} model: {path}", file=sys.stderr)
            return 2

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    config = AutoConfig.from_pretrained(
        args.model_dir,
        trust_remote_code=True,
    )
    config.mert_model_name = str(args.mert_dir.resolve())
    model = AutoModel.from_pretrained(
        args.model_dir,
        config=config,
        trust_remote_code=True,
        device_map=None,
        low_cpu_mem_usage=False,
        ignore_mismatched_sizes=True,
    )
    # Newer Transformers initializes APEX's checkpoint-missing nested MERT
    # parameters after APEXModel.__init__, replacing the weights loaded there
    # with zeros. Reload the verified local encoder after the APEX head.
    model.mert = AutoModel.from_pretrained(
        args.mert_dir,
        trust_remote_code=True,
        device_map=None,
        low_cpu_mem_usage=False,
    )
    model.mert_processor = AutoProcessor.from_pretrained(
        args.mert_dir,
        trust_remote_code=True,
    )
    model.target_sr = model.mert_processor.sampling_rate
    model.mert.eval()
    for parameter in model.mert.parameters():
        parameter.requires_grad = False
    # MERT-v1-95M targets Transformers 4.24. Its all-ones attention mask
    # produces NaNs in newer Hubert encoder code, while omitting that no-op
    # mask keeps every hidden state finite.
    model.mert_processor.return_attention_mask = False
    model = model.to(device)
    predictions = model.predict(str(args.audio.resolve()))
    non_finite = [
        name
        for name, value in predictions.items()
        if not math.isfinite(float(value))
    ]
    if non_finite:
        print(
            "APEX produced non-finite predictions: " + ", ".join(non_finite),
            file=sys.stderr,
        )
        return 1
    payload = {
        "audio": str(args.audio.resolve()),
        "model": "amaai-lab/apex",
        "mert": "m-a-p/MERT-v1-95M",
        "device": device,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "predictions": predictions,
        "interpretation": (
            "APEX is a learned ranking signal, not a substitute for lyric, "
            "signal-health, or human listening review."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
