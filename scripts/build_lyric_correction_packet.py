#!/usr/bin/env python3
"""Build an ASR evidence packet for correcting generated song lyrics."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WHISPER_LANGUAGE_ALIASES = {
    "zh-hans": "zh",
    "zh-hant": "zh",
    "mandarin": "zh",
    "cmn": "zh",
    "yue-hant": "yue",
    "yue-hans": "yue",
    "cantonese": "yue",
}


def normalize_whisper_language(language: str) -> str:
    return WHISPER_LANGUAGE_ALIASES.get(language.lower(), language)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def transcribe_no_vad(audio: Path, model_size: str, language: str) -> dict[str, Any]:
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:  # pragma: no cover - dependency-dependent
        return {"status": "not_available", "engine": "faster-whisper", "model": model_size, "error": str(exc), "text": "", "segments": []}

    model = WhisperModel(model_size, device="auto", compute_type="auto")
    segments, info = model.transcribe(
        str(audio),
        language=normalize_whisper_language(language),
        beam_size=10,
        vad_filter=False,
        word_timestamps=True,
        condition_on_previous_text=False,
    )
    out_segments: list[dict[str, Any]] = []
    text_parts: list[str] = []
    for segment in segments:
        text = segment.text.strip()
        text_parts.append(text)
        out_segments.append(
            {
                "id": segment.id,
                "start": float(segment.start),
                "end": float(segment.end),
                "text": text,
                "words": [
                    {
                        "start": None if word.start is None else float(word.start),
                        "end": None if word.end is None else float(word.end),
                        "word": word.word,
                        "probability": None if word.probability is None else float(word.probability),
                    }
                    for word in (segment.words or [])
                ],
            }
        )
    return {
        "status": "ok",
        "engine": "faster-whisper",
        "mode": "no-vad",
        "model": model_size,
        "language": info.language,
        "language_probability": float(info.language_probability),
        "duration": float(info.duration),
        "text": " ".join(text_parts).strip(),
        "segments": out_segments,
    }


def run_quality_check(audio: Path, expected_lyrics: Path, language: str, model: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "env",
        "PYTHONNOUSERSITE=1",
        "conda",
        "run",
        "--no-capture-output",
        "-n",
        "musia",
        "python",
        "scripts/musia_quality_check.py",
        str(audio),
        "--language",
        language,
        "--asr-model",
        model,
        "--expected-lyrics-file",
        str(expected_lyrics),
        "--output-dir",
        str(output_dir),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)
    return output_dir / "QA.md"


def compact_segments(result: dict[str, Any]) -> str:
    lines = []
    for segment in result.get("segments", []):
        lines.append(f"{segment.get('start', 0):7.2f}-{segment.get('end', 0):7.2f} {segment.get('text', '').strip()}")
    return "\n".join(lines) if lines else "(no segments)"


def render_packet(args: argparse.Namespace, outputs: list[tuple[str, Path]], no_vad_results: list[tuple[str, dict[str, Any], Path]]) -> str:
    lines = [
        f"# Lyric Correction Packet - {args.title}",
        "",
        f"Created: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Inputs",
        "",
        f"- Audio: `{args.audio}`",
        f"- Language: `{args.language}`",
        f"- Expected/reference lyric: `{args.expected_lyrics}`",
    ]
    if args.vocal_stem:
        lines.append(f"- Vocal stem: `{args.vocal_stem}`")
    lines += [
        "",
        "## Evidence Files",
        "",
    ]
    for label, path in outputs:
        lines.append(f"- {label}: `{path}`")
    for label, _result, path in no_vad_results:
        lines.append(f"- {label}: `{path}`")
    lines += [
        "",
        "## No-VAD ASR Text",
        "",
    ]
    for label, result, _path in no_vad_results:
        lines += [
            f"### {label}",
            "",
            "```text",
            result.get("text", "").strip() or "(empty)",
            "```",
            "",
            "Segments:",
            "",
            "```text",
            compact_segments(result),
            "```",
            "",
        ]
    lines += [
        "## Correction Rules",
        "",
        "Use this packet to correct website and publishing lyrics:",
        "",
        "1. Treat the selected audio as the truth source, not the prompt.",
        "2. Use normal ASR for recognized anchors and word timings.",
        "3. Use no-VAD ASR to catch soft openings, outros, repeated CJK lines, and phrases inside long ASR gaps.",
        "4. If no-VAD ASR hears sound-close variants such as `天来了` for `天蓝蓝`, keep the intended lyric only when listening and context support it.",
        "5. If multiple ASR passes consistently hear a different phrase, update the lyric to match the rendered song or mark the render experimental.",
        "6. Update every translation track in the same lyric set with the same line ids and timing.",
        "7. Document any skipped prompt lines and any restored ASR-swallowed phrases in `references/`.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--expected-lyrics", type=Path, required=True)
    parser.add_argument("--language", default="zh")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--vocal-stem", type=Path)
    parser.add_argument("--models", nargs="+", default=["small", "medium"], help="faster-whisper model sizes for normal and no-VAD ASR.")
    parser.add_argument("--skip-normal-asr", action="store_true")
    parser.add_argument("--skip-no-vad", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[tuple[str, Path]] = []
    no_vad_results: list[tuple[str, dict[str, Any], Path]] = []

    if not args.skip_normal_asr:
        for model in args.models:
            qa = run_quality_check(args.audio, args.expected_lyrics, args.language, model, args.output_dir / f"selected-{model}")
            outputs.append((f"selected audio normal ASR {model}", qa))
            if args.vocal_stem:
                stem_qa = run_quality_check(args.vocal_stem, args.expected_lyrics, args.language, model, args.output_dir / f"vocal-stem-{model}")
                outputs.append((f"vocal stem normal ASR {model}", stem_qa))

    if not args.skip_no_vad:
        for model in args.models:
            selected = transcribe_no_vad(args.audio, model, args.language)
            selected_path = args.output_dir / f"selected-{model}-no-vad.json"
            write_json(selected_path, selected)
            no_vad_results.append((f"selected audio no-VAD ASR {model}", selected, selected_path))
            if args.vocal_stem:
                stem = transcribe_no_vad(args.vocal_stem, model, args.language)
                stem_path = args.output_dir / f"vocal-stem-{model}-no-vad.json"
                write_json(stem_path, stem)
                no_vad_results.append((f"vocal stem no-VAD ASR {model}", stem, stem_path))

    packet = render_packet(args, outputs, no_vad_results)
    write_text(args.output_dir / "CORRECTION_PACKET.md", packet)
    print(args.output_dir / "CORRECTION_PACKET.md")


if __name__ == "__main__":
    main()
