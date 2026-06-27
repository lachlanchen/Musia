from __future__ import annotations

from pathlib import Path
from typing import Any


def transcribe_with_faster_whisper(audio_path: Path, model_size: str = "tiny", language: str | None = None) -> dict[str, Any]:
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:  # pragma: no cover - dependency-dependent
        return {
            "status": "not_available",
            "engine": "faster-whisper",
            "error": str(exc),
            "text": "",
            "segments": [],
        }

    model = WhisperModel(model_size, device="auto", compute_type="auto")
    segments, info = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=5,
        vad_filter=True,
        word_timestamps=True,
    )

    serialized_segments: list[dict[str, Any]] = []
    text_parts: list[str] = []
    for segment in segments:
        text = segment.text.strip()
        text_parts.append(text)
        serialized_segments.append(
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
        "model": model_size,
        "language": info.language,
        "language_probability": float(info.language_probability),
        "duration": float(info.duration),
        "text": " ".join(text_parts).strip(),
        "segments": serialized_segments,
    }

