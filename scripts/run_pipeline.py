#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from musai.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Musai local song analysis pipeline.")
    parser.add_argument("input", type=Path, help="Input audio file.")
    parser.add_argument("--output-root", type=Path, default=Path("data/runs"), help="Directory for run outputs.")
    parser.add_argument("--run-name", default=None, help="Stable run name. Defaults to input name plus timestamp.")
    parser.add_argument("--lyrics-ref", type=Path, default=None, help="Optional reference lyrics text file.")
    parser.add_argument("--max-duration", type=float, default=None, help="Trim input to this many seconds before analysis.")
    parser.add_argument("--skip-separation", action="store_true", help="Skip Demucs stem separation.")
    parser.add_argument("--skip-asr", action="store_true", help="Skip ASR transcription.")
    parser.add_argument("--asr-model", default="tiny", help="faster-whisper model size, e.g. tiny/base/small.")
    parser.add_argument("--language", default=None, help="Optional ASR language code.")
    parser.add_argument("--demucs-device", default=None, help="Optional Demucs device, e.g. cuda or cpu.")
    args = parser.parse_args()

    manifest = run_pipeline(
        input_path=args.input,
        output_root=args.output_root,
        run_name=args.run_name,
        lyrics_ref=args.lyrics_ref,
        max_duration=args.max_duration,
        skip_separation=args.skip_separation,
        skip_asr=args.skip_asr,
        asr_model=args.asr_model,
        language=args.language,
        demucs_device=args.demucs_device,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
