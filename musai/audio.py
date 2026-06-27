from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

from .io import ensure_dir


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required but was not found on PATH")


def transcode_input(source: Path, destination: Path, max_duration: float | None = None) -> None:
    require_ffmpeg()
    ensure_dir(destination.parent)
    cmd = ["ffmpeg", "-hide_banner", "-y"]
    if max_duration is not None and max_duration > 0:
        cmd += ["-t", str(max_duration)]
    cmd += ["-i", str(source), "-ac", "2", "-ar", "44100", str(destination)]
    subprocess.run(cmd, check=True)


def load_mono(path: Path, sr: int = 22050) -> tuple[np.ndarray, int]:
    y, actual_sr = librosa.load(path, sr=sr, mono=True)
    return y, actual_sr


def mix_wavs(inputs: list[Path], output: Path) -> None:
    if not inputs:
        raise ValueError("no input wav files supplied")
    ensure_dir(output.parent)

    audio_arrays: list[np.ndarray] = []
    sample_rate: int | None = None
    max_len = 0
    for path in inputs:
        data, sr = sf.read(path, always_2d=True)
        if sample_rate is None:
            sample_rate = sr
        elif sample_rate != sr:
            raise ValueError(f"sample-rate mismatch: {path} has {sr}, expected {sample_rate}")
        audio_arrays.append(data)
        max_len = max(max_len, data.shape[0])

    channels = max(array.shape[1] for array in audio_arrays)
    mix = np.zeros((max_len, channels), dtype=np.float32)
    for array in audio_arrays:
        current = array.astype(np.float32)
        if current.shape[1] == 1 and channels == 2:
            current = np.repeat(current, 2, axis=1)
        padded = np.zeros((max_len, channels), dtype=np.float32)
        padded[: current.shape[0], : current.shape[1]] = current[:, :channels]
        mix += padded

    peak = float(np.max(np.abs(mix))) if mix.size else 0.0
    if peak > 1.0:
        mix /= peak
    sf.write(output, mix, sample_rate or 44100)

