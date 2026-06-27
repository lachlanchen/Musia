from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import librosa
import numpy as np


NOTE_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


@dataclass(frozen=True)
class Beat:
    index: int
    time: float


@dataclass(frozen=True)
class ChordSegment:
    start: float
    end: float
    chord: str
    confidence: float


def _profile(root: int, kind: str) -> np.ndarray:
    profile = np.zeros(12, dtype=np.float32)
    if kind == "maj":
        intervals = [(0, 1.0), (4, 0.85), (7, 0.8)]
    elif kind == "min":
        intervals = [(0, 1.0), (3, 0.85), (7, 0.8)]
    elif kind == "dim":
        intervals = [(0, 1.0), (3, 0.8), (6, 0.7)]
    else:
        raise ValueError(f"unknown chord kind: {kind}")

    for interval, weight in intervals:
        profile[(root + interval) % 12] = weight
    profile /= np.linalg.norm(profile) + 1e-8
    return profile


def _templates() -> list[tuple[str, np.ndarray]]:
    items: list[tuple[str, np.ndarray]] = []
    for root, name in enumerate(NOTE_NAMES):
        items.append((name, _profile(root, "maj")))
        items.append((f"{name}m", _profile(root, "min")))
    return items


TEMPLATES = _templates()


def estimate_beats(y: np.ndarray, sr: int) -> tuple[float, list[Beat]]:
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
    tempo_value = float(np.asarray(tempo).reshape(-1)[0])
    times = librosa.frames_to_time(beat_frames, sr=sr)

    if len(times) < 2:
        duration = librosa.get_duration(y=y, sr=sr)
        step = 60.0 / max(tempo_value, 80.0)
        times = np.arange(0.0, max(duration, step), step)

    beats = [Beat(index=i, time=float(t)) for i, t in enumerate(times)]
    return tempo_value, beats


def _best_chord(chroma_vector: np.ndarray) -> tuple[str, float]:
    if not np.any(chroma_vector > 0):
        return "N", 0.0
    vector = chroma_vector.astype(np.float32)
    vector /= np.linalg.norm(vector) + 1e-8
    best_name = "N"
    best_score = -1.0
    for name, template in TEMPLATES:
        score = float(np.dot(vector, template))
        if score > best_score:
            best_name = name
            best_score = score
    if best_score < 0.35:
        return "N", max(best_score, 0.0)
    return best_name, best_score


def estimate_chords(y: np.ndarray, sr: int, beats: Iterable[Beat]) -> list[ChordSegment]:
    beat_list = list(beats)
    if not beat_list:
        return []

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, bins_per_octave=36)
    chroma_times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr)
    duration = librosa.get_duration(y=y, sr=sr)

    boundaries = [beat.time for beat in beat_list]
    if boundaries[0] > 0.05:
        boundaries.insert(0, 0.0)
    if boundaries[-1] < duration:
        boundaries.append(duration)

    raw: list[ChordSegment] = []
    for start, end in zip(boundaries, boundaries[1:]):
        if end <= start:
            continue
        mask = (chroma_times >= start) & (chroma_times < end)
        if not np.any(mask):
            continue
        vector = np.mean(chroma[:, mask], axis=1)
        chord, confidence = _best_chord(vector)
        raw.append(ChordSegment(float(start), float(end), chord, float(confidence)))

    return collapse_chords(raw)


def collapse_chords(segments: Iterable[ChordSegment]) -> list[ChordSegment]:
    collapsed: list[ChordSegment] = []
    for segment in segments:
        if not collapsed or collapsed[-1].chord != segment.chord:
            collapsed.append(segment)
            continue
        previous = collapsed[-1]
        merged_confidence = max(previous.confidence, segment.confidence)
        collapsed[-1] = ChordSegment(
            start=previous.start,
            end=segment.end,
            chord=previous.chord,
            confidence=merged_confidence,
        )
    return collapsed
