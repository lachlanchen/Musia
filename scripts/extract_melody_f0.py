#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import librosa
import numpy as np


NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def hz_to_note(frequency: float) -> tuple[float | None, str]:
    if not np.isfinite(frequency) or frequency <= 0:
        return None, ""
    midi = float(librosa.hz_to_midi(frequency))
    rounded = int(round(midi))
    octave = rounded // 12 - 1
    name = f"{NOTE_NAMES[rounded % 12]}{octave}"
    return midi, name


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a simple vocal F0/melody guide with librosa.pyin.")
    parser.add_argument("audio", type=Path, help="Input vocal or monophonic guide audio.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--fmin", default="C2")
    parser.add_argument("--fmax", default="C6")
    parser.add_argument("--hop-length", type=int, default=512)
    parser.add_argument("--frame-length", type=int, default=2048)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    y, sr = librosa.load(args.audio, sr=None, mono=True)
    if y.size == 0:
        raise SystemExit("Input audio is empty.")

    f0, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=librosa.note_to_hz(args.fmin),
        fmax=librosa.note_to_hz(args.fmax),
        sr=sr,
        frame_length=args.frame_length,
        hop_length=args.hop_length,
    )
    times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=args.hop_length)

    csv_path = args.output_dir / "melody_f0.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["time", "f0_hz", "midi", "note", "voiced", "probability"])
        writer.writeheader()
        for time, freq, voiced, probability in zip(times, f0, voiced_flag, voiced_prob):
            midi, note = hz_to_note(float(freq)) if np.isfinite(freq) else (None, "")
            writer.writerow(
                {
                    "time": f"{float(time):.6f}",
                    "f0_hz": "" if not np.isfinite(freq) else f"{float(freq):.3f}",
                    "midi": "" if midi is None else f"{midi:.3f}",
                    "note": note,
                    "voiced": bool(voiced),
                    "probability": f"{float(probability):.6f}",
                }
            )

    voiced_values = f0[np.isfinite(f0)]
    summary = {
        "audio": str(args.audio),
        "sample_rate": sr,
        "duration_seconds": float(len(y) / sr),
        "frame_count": int(len(f0)),
        "voiced_frame_count": int(len(voiced_values)),
        "voiced_ratio": float(len(voiced_values) / len(f0)) if len(f0) else 0.0,
        "median_f0_hz": float(np.median(voiced_values)) if len(voiced_values) else None,
        "min_f0_hz": float(np.min(voiced_values)) if len(voiced_values) else None,
        "max_f0_hz": float(np.max(voiced_values)) if len(voiced_values) else None,
        "csv": str(csv_path),
    }
    (args.output_dir / "melody_f0_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(csv_path)


if __name__ == "__main__":
    main()
