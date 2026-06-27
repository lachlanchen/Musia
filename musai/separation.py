from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from .audio import mix_wavs
from .io import ensure_dir


STEM_NAMES = ["vocals", "drums", "bass", "other"]


def has_demucs() -> bool:
    return shutil.which("demucs") is not None


def run_demucs(input_wav: Path, output_dir: Path, model: str = "htdemucs", device: str | None = None) -> dict[str, Path]:
    ensure_dir(output_dir)
    cmd = [sys.executable, "-m", "demucs.separate", "-n", model, "-o", str(output_dir)]
    if device:
        cmd += ["-d", device]
    cmd.append(str(input_wav))
    subprocess.run(cmd, check=True)

    song_dir = output_dir / model / input_wav.stem
    stems: dict[str, Path] = {}
    for name in STEM_NAMES:
        path = song_dir / f"{name}.wav"
        if path.exists():
            stems[name] = path
    if "vocals" not in stems:
        raise RuntimeError(f"Demucs did not create expected stems under {song_dir}")
    return stems


def normalize_stem_layout(raw_stems: dict[str, Path], target_dir: Path) -> dict[str, Path]:
    ensure_dir(target_dir)
    normalized: dict[str, Path] = {}
    for name, source in raw_stems.items():
        target = target_dir / f"{name}.wav"
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        normalized[name] = target

    if "vocals" in normalized:
        human = target_dir / "human_sound.wav"
        shutil.copy2(normalized["vocals"], human)
        normalized["human_sound"] = human

    accompaniment_parts = [normalized[name] for name in ("drums", "bass", "other") if name in normalized]
    if accompaniment_parts:
        instrumental = target_dir / "instrumental.wav"
        mix_wavs(accompaniment_parts, instrumental)
        normalized["instrumental"] = instrumental

    return normalized

