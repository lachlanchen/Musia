#!/usr/bin/env python3
"""Run HeartMuLa with a stable SoundFile/FFmpeg audio export path."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from types import MethodType
from typing import Any

import soundfile as sf
import torch


ROOT = Path(__file__).resolve().parents[1]
HEARTMULA_SRC = ROOT / "third_party" / "HeartMuLa" / "src"
sys.path.insert(0, str(HEARTMULA_SRC))

from heartlib import HeartMuLaGenPipeline  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a song with HeartMuLa and export it reliably."
    )
    parser.add_argument("--lyrics", type=Path, required=True)
    parser.add_argument("--tags", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--model-path",
        type=Path,
        default=ROOT / "third_party" / "HeartMuLa" / "ckpt",
    )
    parser.add_argument("--version", default="3B")
    parser.add_argument("--max-audio-length-ms", type=int, default=180_000)
    parser.add_argument("--topk", type=int, default=50)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--cfg-scale", type=float, default=1.5)
    parser.add_argument("--mula-device", default="cuda:0")
    parser.add_argument("--codec-device", default="cuda:0")
    parser.add_argument("--mula-dtype", choices=("bfloat16", "float16"), default="bfloat16")
    parser.add_argument(
        "--codec-dtype",
        choices=("float32", "bfloat16"),
        default="float32",
    )
    parser.add_argument(
        "--no-lazy-load",
        action="store_true",
        help="Keep both models resident. This usually requires two GPUs.",
    )
    return parser.parse_args()


def torch_dtype(name: str) -> torch.dtype:
    return {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }[name]


def write_audio(waveform: torch.Tensor, sample_rate: int, output: Path) -> None:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    samples = waveform.detach().to(torch.float32).cpu().numpy()
    if samples.ndim == 2:
        samples = samples.T

    suffix = output.suffix.lower()
    if suffix in {".wav", ".flac"}:
        subtype = "PCM_24"
        sf.write(output, samples, sample_rate, subtype=subtype)
        return
    if suffix != ".mp3":
        raise ValueError("Output must end in .wav, .flac, or .mp3")

    with tempfile.TemporaryDirectory(prefix="musia-heartmula-") as temp_dir:
        intermediate = Path(temp_dir) / "generated.wav"
        sf.write(intermediate, samples, sample_rate, subtype="PCM_24")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(intermediate),
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "0",
                str(output),
            ],
            check=True,
        )


def stable_postprocess(
    pipeline: HeartMuLaGenPipeline,
    model_outputs: dict[str, Any],
    save_path: str,
) -> None:
    frames = model_outputs["frames"].to(pipeline.codec_device)
    waveform = pipeline.codec.detokenize(frames)
    pipeline._unload()
    write_audio(waveform, 48_000, Path(save_path))


def main() -> int:
    args = parse_args()
    for path in (args.lyrics, args.tags, args.model_path):
        if not path.exists():
            raise FileNotFoundError(path)
    if not torch.cuda.is_available():
        raise RuntimeError("HeartMuLa generation requires a CUDA GPU")

    pipeline = HeartMuLaGenPipeline.from_pretrained(
        str(args.model_path.resolve()),
        device={
            "mula": torch.device(args.mula_device),
            "codec": torch.device(args.codec_device),
        },
        dtype={
            "mula": torch_dtype(args.mula_dtype),
            "codec": torch_dtype(args.codec_dtype),
        },
        version=args.version,
        lazy_load=not args.no_lazy_load,
    )
    pipeline.postprocess = MethodType(stable_postprocess, pipeline)

    with torch.no_grad():
        pipeline(
            {
                "lyrics": str(args.lyrics.resolve()),
                "tags": str(args.tags.resolve()),
            },
            max_audio_length_ms=args.max_audio_length_ms,
            save_path=str(args.output.resolve()),
            topk=args.topk,
            temperature=args.temperature,
            cfg_scale=args.cfg_scale,
        )

    print(f"Generated music saved to {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
