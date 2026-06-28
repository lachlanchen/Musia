#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from musai.asr import transcribe_with_faster_whisper


def normalize_tokens(text: str, language: str) -> list[str]:
    language = language.lower()
    if language.startswith("zh"):
        return [char for char in text if "\u4e00" <= char <= "\u9fff"]
    if language.startswith("ja"):
        return [
            char
            for char in text
            if "\u3040" <= char <= "\u309f"
            or "\u30a0" <= char <= "\u30ff"
            or "\u4e00" <= char <= "\u9fff"
            or char == "ー"
        ]
    return re.findall(r"[a-z0-9']+", text.lower())


def overlap_score(expected: str, actual: str, language: str) -> float | None:
    expected_tokens = normalize_tokens(expected, language)
    actual_tokens = normalize_tokens(actual, language)
    if not expected_tokens:
        return None
    actual_set = set(actual_tokens)
    return sum(1 for token in expected_tokens if token in actual_set) / len(expected_tokens)


def render_report(data: dict) -> str:
    lines = [
        "# Musai Quality Check",
        "",
        f"- Audio: `{data['audio']}`",
        f"- Language: `{data['language']}`",
        f"- Duration: `{data['duration_seconds']:.3f}` seconds",
        f"- Sample rate: `{data['sample_rate']}`",
        f"- RMS: `{data['rms']:.5f}`",
        f"- Peak: `{data['peak']:.5f}`",
        f"- ASR status: `{data['asr_status']}`",
        f"- Lyric overlap: `{data['lyric_overlap']}`",
        f"- Quality gate: `{data['quality_gate']}`",
        "",
        "## ASR Text",
        "",
        "```text",
        data["asr_text"],
        "```",
        "",
    ]
    if data.get("expected_lyrics"):
        lines += [
            "## Expected Lyrics",
            "",
            "```text",
            data["expected_lyrics"],
            "```",
            "",
        ]
    lines += [
        "## Notes",
        "",
        data["notes"],
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check generated Musai audio for level, duration, ASR text, and lyric overlap.")
    parser.add_argument("audio", type=Path)
    parser.add_argument("--language", default="en")
    parser.add_argument("--expected-lyrics", default="")
    parser.add_argument("--expected-lyrics-file", type=Path)
    parser.add_argument("--asr-model", default="small")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    expected = args.expected_lyrics
    if args.expected_lyrics_file:
        expected = args.expected_lyrics_file.read_text(encoding="utf-8").strip()

    audio = args.audio
    output_dir = args.output_dir or audio.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    data, sample_rate = sf.read(audio, always_2d=True)
    rms = float(np.sqrt(np.mean(data * data))) if data.size else 0.0
    peak = float(np.max(np.abs(data))) if data.size else 0.0
    duration = float(len(data) / sample_rate) if sample_rate else 0.0

    asr = transcribe_with_faster_whisper(audio, model_size=args.asr_model, language=args.language)
    asr_text = (asr.get("text") or "").strip()
    overlap = overlap_score(expected, asr_text, args.language)

    level_ok = rms >= 0.01 and peak <= 0.98
    asr_ok = bool(asr_text)
    lyric_ok = overlap is None or overlap >= 0.35
    quality_gate = "pass" if level_ok and asr_ok and lyric_ok else "review"
    notes = []
    if not level_ok:
        notes.append("Audio level needs review: RMS is too low or peak is too high.")
    if not asr_ok:
        notes.append("ASR did not recover intelligible lyrics.")
    if overlap is not None and overlap < 0.35:
        notes.append("ASR overlap with expected lyrics is low.")
    if not notes:
        notes.append("Basic automated checks passed; still do a human listening pass.")

    result = {
        "audio": str(audio),
        "language": args.language,
        "duration_seconds": duration,
        "sample_rate": sample_rate,
        "rms": rms,
        "peak": peak,
        "asr_status": asr.get("status"),
        "asr_text": asr_text,
        "expected_lyrics": expected,
        "lyric_overlap": overlap,
        "quality_gate": quality_gate,
        "notes": " ".join(notes),
    }
    (output_dir / "quality.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output_dir / "QA.md").write_text(render_report(result), encoding="utf-8")
    print(output_dir / "QA.md")


if __name__ == "__main__":
    main()
