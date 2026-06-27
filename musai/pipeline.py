from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .asr import transcribe_with_faster_whisper
from .audio import load_mono, transcode_input
from .chords import estimate_beats, estimate_chords
from .io import ensure_dir, read_text_optional, write_csv, write_json
from .separation import normalize_stem_layout, run_demucs


def _artifact(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def run_pipeline(
    input_path: Path,
    output_root: Path,
    run_name: str | None = None,
    lyrics_ref: Path | None = None,
    max_duration: float | None = None,
    skip_separation: bool = False,
    skip_asr: bool = False,
    asr_model: str = "tiny",
    language: str | None = None,
    demucs_device: str | None = None,
) -> dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    if run_name is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        run_name = f"{input_path.stem}-{stamp}"

    run_dir = ensure_dir(output_root / run_name)
    source_dir = ensure_dir(run_dir / "source")
    analysis_dir = ensure_dir(run_dir / "analysis")
    stems_dir = ensure_dir(run_dir / "stems")

    input_wav = source_dir / "input.wav"
    transcode_input(input_path, input_wav, max_duration=max_duration)

    artifacts: dict[str, str] = {"input_wav": _artifact(input_wav, run_dir)}
    steps: dict[str, Any] = {}

    stem_paths: dict[str, Path] = {}
    if not skip_separation:
        try:
            raw_stems = run_demucs(input_wav, run_dir / "_demucs", device=demucs_device)
            stem_paths = normalize_stem_layout(raw_stems, stems_dir)
            artifacts.update({f"stem_{name}": _artifact(path, run_dir) for name, path in stem_paths.items()})
            steps["separation"] = {"status": "ok", "engine": "demucs"}
        except Exception as exc:
            steps["separation"] = {"status": "failed", "engine": "demucs", "error": str(exc)}

    vocal_audio = stem_paths.get("vocals", input_wav)
    music_audio = stem_paths.get("instrumental", input_wav)
    y, sr = load_mono(music_audio)
    tempo, beats = estimate_beats(y, sr)
    chords = estimate_chords(y, sr, beats)

    beats_rows = [{"index": beat.index, "time": f"{beat.time:.3f}"} for beat in beats]
    chords_rows = [
        {
            "start": f"{segment.start:.3f}",
            "end": f"{segment.end:.3f}",
            "chord": segment.chord,
            "confidence": f"{segment.confidence:.3f}",
        }
        for segment in chords
    ]

    beats_json = analysis_dir / "beats.json"
    beats_csv = analysis_dir / "beats.csv"
    chords_json = analysis_dir / "chords.json"
    chords_csv = analysis_dir / "chords.csv"
    write_json(beats_json, {"tempo_bpm": tempo, "beats": [asdict(beat) for beat in beats]})
    write_csv(beats_csv, beats_rows, ["index", "time"])
    write_json(chords_json, {"chords": [asdict(segment) for segment in chords]})
    write_csv(chords_csv, chords_rows, ["start", "end", "chord", "confidence"])
    artifacts.update(
        {
            "beats_json": _artifact(beats_json, run_dir),
            "beats_csv": _artifact(beats_csv, run_dir),
            "chords_json": _artifact(chords_json, run_dir),
            "chords_csv": _artifact(chords_csv, run_dir),
        }
    )

    lyrics_text = read_text_optional(lyrics_ref)
    lyrics_result: dict[str, Any]
    if skip_asr:
        lyrics_result = {
            "status": "skipped",
            "engine": None,
            "text": lyrics_text or "",
            "reference_lyrics_used": lyrics_text is not None,
            "segments": [],
        }
    elif lyrics_text:
        lyrics_result = {
            "status": "reference_only",
            "engine": None,
            "text": lyrics_text,
            "reference_lyrics_used": True,
            "segments": [],
        }
    else:
        lyrics_result = transcribe_with_faster_whisper(vocal_audio, model_size=asr_model, language=language)

    lyrics_json = analysis_dir / "lyrics.json"
    lyrics_txt = analysis_dir / "lyrics.txt"
    write_json(lyrics_json, lyrics_result)
    lyrics_txt.write_text((lyrics_result.get("text") or "").strip() + "\n", encoding="utf-8")
    artifacts.update({"lyrics_json": _artifact(lyrics_json, run_dir), "lyrics_txt": _artifact(lyrics_txt, run_dir)})

    if lyrics_ref is not None:
        copied = source_dir / "lyrics_reference.txt"
        shutil.copy2(lyrics_ref, copied)
        artifacts["lyrics_reference"] = _artifact(copied, run_dir)

    manifest = {
        "run_name": run_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": str(input_path),
        "max_duration": max_duration,
        "music_analysis_audio": _artifact(music_audio, run_dir),
        "vocal_analysis_audio": _artifact(vocal_audio, run_dir),
        "tempo_bpm": tempo,
        "beat_count": len(beats),
        "chord_segment_count": len(chords),
        "lyrics_status": lyrics_result.get("status"),
        "steps": steps,
        "artifacts": artifacts,
    }

    manifest_path = run_dir / "manifest.json"
    report_path = run_dir / "REPORT.md"
    write_json(manifest_path, manifest)
    report_path.write_text(_render_report(manifest, chords_rows, lyrics_result), encoding="utf-8")
    artifacts["manifest"] = _artifact(manifest_path, run_dir)
    artifacts["report"] = _artifact(report_path, run_dir)
    manifest["artifacts"] = artifacts
    write_json(manifest_path, manifest)
    return manifest


def _render_report(manifest: dict[str, Any], chord_rows: list[dict[str, str]], lyrics: dict[str, Any]) -> str:
    top_chords = chord_rows[:32]
    lines = [
        f"# Musai Run: {manifest['run_name']}",
        "",
        f"- Input: `{manifest['input']}`",
        f"- Tempo: `{manifest['tempo_bpm']:.2f}` BPM",
        f"- Beats: `{manifest['beat_count']}`",
        f"- Chord segments: `{manifest['chord_segment_count']}`",
        f"- Lyrics status: `{manifest['lyrics_status']}`",
        "",
        "## Artifacts",
        "",
    ]
    for key, value in sorted(manifest["artifacts"].items()):
        lines.append(f"- `{key}`: `{value}`")

    lines += ["", "## First Chord Segments", ""]
    if top_chords:
        lines += ["| Start | End | Chord | Confidence |", "| --- | --- | --- | --- |"]
        for row in top_chords:
            lines.append(f"| {row['start']} | {row['end']} | {row['chord']} | {row['confidence']} |")
    else:
        lines.append("No chord segments detected.")

    text = (lyrics.get("text") or "").strip()
    lines += ["", "## Lyrics / Transcription", ""]
    lines.append(text if text else "No lyrics text available.")
    lines.append("")
    return "\n".join(lines)
