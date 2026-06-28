#!/usr/bin/env python3
"""Run the local SongGen mixed-pro backend for Musai song experiments.

SongGen's released processor tokenizes lyrics as English phonetics, so for
Mandarin/Japanese experiments use pinyin/romaji in the sung lyric and publish
native-script subtitles separately.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf
import torch


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHECKPOINT = ROOT / "third_party" / "SongGen" / "checkpoints" / "SongGen_mixed_pro"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lyrics-file", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--max-new-tokens", type=int, default=1500)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=628915)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--dtype", choices=["float32", "float16"], default="float32")
    parser.add_argument("--low-cpu-mem-usage", action="store_true")
    args = parser.parse_args()

    # Import after argument parsing so `--help` does not require the heavy env.
    from songgen import SongGenMixedForConditionalGeneration, SongGenProcessor

    checkpoint = Path(args.checkpoint).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    lyrics = Path(args.lyrics_file).expanduser().read_text(encoding="utf-8")

    torch.manual_seed(args.seed)
    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but not available.")

    device = torch.device(args.device)
    load_kwargs = {
        "attn_implementation": "sdpa",
        "torch_dtype": torch.float16 if args.dtype == "float16" else torch.float32,
    }
    if args.low_cpu_mem_usage:
        try:
            import accelerate  # noqa: F401

            load_kwargs["low_cpu_mem_usage"] = True
        except ImportError:
            raise SystemExit("--low-cpu-mem-usage requires accelerate in the SongGen environment.")
    model = SongGenMixedForConditionalGeneration.from_pretrained(str(checkpoint), **load_kwargs).to(device)
    model.eval()
    processor = SongGenProcessor(str(checkpoint), device)
    model_inputs = processor(text=args.prompt, lyrics=lyrics, separate=False)

    with torch.inference_mode():
        generation = model.generate(
            **model_inputs,
            do_sample=True,
            top_p=args.top_p,
            temperature=args.temperature,
            max_new_tokens=args.max_new_tokens,
        )
    audio = generation.detach().cpu().numpy().squeeze()
    audio = np.asarray(audio, dtype=np.float32)
    sf.write(output, audio, model.config.sampling_rate)
    print(output)


if __name__ == "__main__":
    main()
