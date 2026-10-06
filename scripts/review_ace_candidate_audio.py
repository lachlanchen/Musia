#!/usr/bin/env python3
"""Serial signal-health and large ASR screening of a saved ACE candidate manifest.

This is a shortlist tool, not a final lyric correction or musicality verdict.
Finalists still need stem transcription and independent review.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from run_ace_candidate_sweep import audio_digest

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--language", required=True)
    parser.add_argument("--model", default="large-v3")
    parser.add_argument("--apex", action="store_true")
    args = parser.parse_args()
    records = json.loads(args.manifest.read_text())
    for record in records:
        if audio_digest(Path(record["audio"])) != record["sha256"]:
            raise ValueError(f"Candidate changed: {record['seed']}")
    # Child processes finish before ASR is loaded, avoiding concurrent models.
    for record in records:
        out = args.output_dir / str(record["seed"])
        out.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, str(ROOT / "scripts/audio_health_report.py"),
                        record["audio"], str(out)], check=True)
        if args.apex:
            subprocess.run(["bash", str(ROOT / "scripts/run_apex_music_quality.sh"),
                            record["audio"], str(out / "apex.json")], check=True)
    from faster_whisper import WhisperModel
    model = WhisperModel(args.model, device="cuda", compute_type="float16")
    for record in records:
        out = args.output_dir / str(record["seed"])
        segments, info = model.transcribe(
            record["audio"], language=args.language, beam_size=5,
            vad_filter=True, word_timestamps=True, condition_on_previous_text=False,
        )
        rows = [{"start": s.start, "end": s.end, "text": s.text,
                 "words": [{"word": w.word, "start": w.start, "end": w.end,
                            "probability": w.probability} for w in s.words or []]}
                for s in segments]
        doc = {"status": "ok", "audio": record["audio"], "audioSha256": record["sha256"],
               "model": args.model, "language": info.language, "duration": info.duration,
               "mode": "full-mix-vad-no-previous-text", "segments": rows}
        (out / "asr.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
        print(f"Seed {record['seed']}: " + " / ".join(x["text"].strip() for x in rows), flush=True)


if __name__ == "__main__":
    main()
