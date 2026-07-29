#!/usr/bin/env python3
"""Measure objective health signals for a generated song."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--silence-db", type=float, default=-50.0)
    return parser.parse_args()


def linear_to_db(value: float) -> float:
    return 20.0 * math.log10(max(value, 1e-12))


def edge_silence_seconds(
    audio: np.ndarray,
    sample_rate: int,
    threshold_db: float,
    from_end: bool,
) -> float:
    window = max(1, round(sample_rate * 0.1))
    mono = np.mean(audio, axis=1)
    if from_end:
        mono = mono[::-1]
    silent_samples = 0
    for start in range(0, len(mono), window):
        block = mono[start : start + window]
        if not len(block):
            break
        rms = float(np.sqrt(np.mean(np.square(block, dtype=np.float64))))
        if linear_to_db(rms) > threshold_db:
            break
        silent_samples += len(block)
    return silent_samples / sample_rate


def ebur128_metrics(audio: Path) -> dict[str, float | None]:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i",
        str(audio),
        "-filter_complex",
        "ebur128=peak=true:framelog=quiet",
        "-f",
        "null",
        "-",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    output = result.stderr

    def last_float(pattern: str) -> float | None:
        matches = re.findall(pattern, output)
        return float(matches[-1]) if matches else None

    return {
        "integrated_lufs": last_float(r"I:\s+(-?\d+(?:\.\d+)?)\s+LUFS"),
        "loudness_range_lu": last_float(r"LRA:\s+(\d+(?:\.\d+)?)\s+LU"),
        "true_peak_dbfs": last_float(r"Peak:\s+(-?\d+(?:\.\d+)?)\s+dBFS"),
        "ffmpeg_status": result.returncode,
    }


def render_markdown(report: dict) -> str:
    metric_lines = [
        ("Duration", f"{report['duration_seconds']:.3f} s"),
        ("Sample rate", f"{report['sample_rate']} Hz"),
        ("Channels", str(report["channels"])),
        ("Integrated loudness", f"{report['integrated_lufs']} LUFS"),
        ("Loudness range", f"{report['loudness_range_lu']} LU"),
        ("True peak", f"{report['true_peak_dbfs']} dBFS"),
        ("Sample peak", f"{report['sample_peak_dbfs']:.3f} dBFS"),
        ("RMS", f"{report['rms_dbfs']:.3f} dBFS"),
        ("Clipping fraction", f"{report['clipping_fraction']:.8f}"),
        ("Leading silence", f"{report['leading_silence_seconds']:.3f} s"),
        ("Trailing silence", f"{report['trailing_silence_seconds']:.3f} s"),
        ("Final 100 ms RMS", f"{report['final_100ms_rms_dbfs']:.3f} dBFS"),
        ("Maximum DC offset", f"{report['max_abs_dc_offset']:.8f}"),
        ("Non-finite samples", str(report["nonfinite_samples"])),
        ("Gate", report["quality_gate"]),
    ]
    lines = [
        "# Audio Health Report",
        "",
        f"- Audio: `{report['audio']}`",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    lines.extend(f"| {name} | {value} |" for name, value in metric_lines)
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report["notes"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    if not args.audio.is_file():
        print(f"Missing audio: {args.audio}", file=sys.stderr)
        return 2
    args.output_dir.mkdir(parents=True, exist_ok=True)
    audio, sample_rate = sf.read(
        args.audio,
        dtype="float32",
        always_2d=True,
    )
    if not sample_rate or not len(audio):
        print("Audio is empty or has no sample rate.", file=sys.stderr)
        return 1

    finite_mask = np.isfinite(audio)
    nonfinite_samples = int(audio.size - np.count_nonzero(finite_mask))
    safe_audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)
    absolute = np.abs(safe_audio)
    sample_peak = float(np.max(absolute))
    rms = float(np.sqrt(np.mean(np.square(safe_audio, dtype=np.float64))))
    clipping_fraction = float(np.mean(absolute >= 0.999))
    final_count = min(len(safe_audio), max(1, round(sample_rate * 0.1)))
    final_rms = float(
        np.sqrt(np.mean(np.square(safe_audio[-final_count:], dtype=np.float64)))
    )
    dc_offsets = np.mean(safe_audio, axis=0)
    ffmpeg_metrics = ebur128_metrics(args.audio)

    notes: list[str] = []
    failures: list[str] = []
    if nonfinite_samples:
        failures.append("Audio contains NaN or infinite samples.")
    if clipping_fraction > 0.0001:
        failures.append("More than 0.01% of samples are at clipping level.")
    if ffmpeg_metrics["true_peak_dbfs"] is not None:
        if ffmpeg_metrics["true_peak_dbfs"] > -0.1:
            failures.append("True peak is too close to or above full scale.")
    if abs(float(np.max(np.abs(dc_offsets)))) > 0.01:
        failures.append("DC offset exceeds 0.01.")
    if linear_to_db(final_rms) > -30.0:
        notes.append("The final 100 ms is still loud; inspect for a hard cut.")
    else:
        notes.append("The file reaches a quiet ending level.")
    if clipping_fraction == 0.0:
        notes.append("No samples reached the clipping threshold.")
    notes.extend(failures)

    report = {
        "audio": str(args.audio.resolve()),
        "duration_seconds": len(audio) / sample_rate,
        "sample_rate": sample_rate,
        "channels": int(audio.shape[1]),
        "sample_peak_dbfs": linear_to_db(sample_peak),
        "rms_dbfs": linear_to_db(rms),
        "clipping_fraction": clipping_fraction,
        "leading_silence_seconds": edge_silence_seconds(
            safe_audio,
            sample_rate,
            args.silence_db,
            from_end=False,
        ),
        "trailing_silence_seconds": edge_silence_seconds(
            safe_audio,
            sample_rate,
            args.silence_db,
            from_end=True,
        ),
        "final_100ms_rms_dbfs": linear_to_db(final_rms),
        "max_abs_dc_offset": float(np.max(np.abs(dc_offsets))),
        "nonfinite_samples": nonfinite_samples,
        **ffmpeg_metrics,
        "quality_gate": "review" if failures else "pass",
        "notes": notes,
    }
    json_path = args.output_dir / "audio-health.json"
    markdown_path = args.output_dir / "AUDIO_HEALTH.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    print(markdown_path)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
