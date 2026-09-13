#!/usr/bin/env python3
"""Generate traceable MiniMax Music 3 candidates without modifying ACE defaults."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import math
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def export_gain(peak: float) -> float:
    if not math.isfinite(peak) or peak <= 0:
        raise ValueError("The generated waveform is silent or has an invalid peak")
    return min(1.0, 10 ** (-1 / 20) / peak)


def true_peak_gain(measured_dbfs: float, target_dbfs: float = -2.0) -> float:
    if not math.isfinite(measured_dbfs):
        raise ValueError("Invalid measured true peak")
    return 10 ** (min(0.0, target_dbfs - measured_dbfs - 0.1) / 20)


def validate_lyrics(text: str) -> str:
    text = text.strip()
    if not text:
        raise ValueError("Lyrics are empty")
    for number, line in enumerate(text.splitlines(), 1):
        if re.match(r"^\s*\[[^\]]+\]\s*\S", line):
            raise ValueError(f"Line {number}: section tags must be on their own line; Music 3 drops text after a tag")
    if not any(line.strip() and not line.strip().startswith("[") for line in text.splitlines()):
        raise ValueError("Lyrics contain section tags but no words")
    return text + "\n"


def local_config(model_dir: Path) -> dict:
    config = json.loads((model_dir / "modular_model_index.json").read_text())
    config = copy.deepcopy(config)
    # The official modular index names Hub repos even when loaded from a local
    # directory. Bind every component locally to avoid a second weight download.
    for value in config.values():
        if isinstance(value, list) and len(value) == 3 and isinstance(value[2], dict):
            value[2]["pretrained_model_name_or_path"] = str(model_dir.resolve())
            value[2]["revision"] = None
    return config


def verify_download_manifest(model_dir: Path) -> dict:
    manifest_path = model_dir / "musia-download.json"
    if not manifest_path.is_file():
        raise RuntimeError("Model download is not verified; run download_minimax_music3.py --verify-sha256 first")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("model_id") != "MiniMaxAI/MiniMax-Music3" or not manifest.get("files"):
        raise RuntimeError("Invalid Music 3 download manifest")
    for item in manifest["files"]:
        path = model_dir / item["path"]
        if not path.resolve().is_relative_to(model_dir.resolve()):
            raise RuntimeError("Model manifest path escapes its directory")
        if not path.is_file() or path.stat().st_size != item["bytes"] or Path(str(path) + ".aria2").exists():
            raise RuntimeError(f"Incomplete model component: {item['path']}")
        if item.get("expected_sha256") and not item.get("sha256_verified"):
            raise RuntimeError(f"Unverified model component: {item['path']}")
    return manifest


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lyrics", required=True, type=Path)
    parser.add_argument("--caption", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--model-dir", type=Path, default=ROOT / "third_party/MiniMax-Music3/checkpoints/diffusers")
    parser.add_argument("--seeds", nargs="+", type=int, default=[91301])
    parser.add_argument("--duration", type=float, default=180)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--offload", choices=["auto", "none", "group"], default="auto")
    args = parser.parse_args()
    if not 1 <= args.duration <= 300 or args.steps < 1:
        parser.error("Duration must be 1..300 seconds, and steps positive")
    if len(args.seeds) != len(set(args.seeds)):
        parser.error("Duplicate seeds would overwrite candidates")
    lyrics = validate_lyrics(args.lyrics.read_text(encoding="utf-8"))
    caption = args.caption.read_text(encoding="utf-8").strip()
    if not caption:
        parser.error("Caption is empty")
    manifest = verify_download_manifest(args.model_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for seed in args.seeds:
        if (args.output_dir / f"seed-{seed}").exists():
            raise FileExistsError(f"Preserve previous candidate: seed-{seed}; use a new output directory")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    import numpy as np
    import soundfile as sf
    import torch
    from diffusers import ComponentsManager, MiniMaxMusic3ModularPipeline

    if not torch.cuda.is_available():
        raise RuntimeError("This wrapper requires a CUDA GPU")
    torch.set_num_threads(8)
    torch.cuda.set_device(args.device)
    free, total = torch.cuda.mem_get_info(args.device)
    print(f"GPU {args.device}: {free / 2**30:.1f}/{total / 2**30:.1f} GiB free", flush=True)
    if free < 22 * 2**30 and args.offload != "group":
        raise RuntimeError("Need at least 22 GiB free VRAM, or explicitly use --offload group")
    manager = ComponentsManager()
    if args.offload != "none":
        manager.enable_auto_cpu_offload(device=args.device)
    pipe = MiniMaxMusic3ModularPipeline(
        modular_config_dict=local_config(args.model_dir), components_manager=manager)
    print("Loading local BF16 components", flush=True)
    pipe.load_components(dtype=torch.bfloat16, local_files_only=True)
    if args.offload == "none":
        pipe.to(args.device)
    elif args.offload == "group":
        from diffusers.hooks.group_offloading import apply_group_offloading
        apply_group_offloading(pipe.language_model, onload_device=torch.device(args.device),
                               offload_type="leaf_level", use_stream=True)
    versions = {name: importlib.metadata.version(name) for name in ("torch", "diffusers", "transformers", "accelerate")}
    for seed in args.seeds:
        output = args.output_dir / f"seed-{seed}"
        output.mkdir()
        (output / "lyrics-input.txt").write_text(lyrics, encoding="utf-8")
        (output / "caption.txt").write_text(caption + "\n", encoding="utf-8")
        record = {
            "backend": "MiniMax-Music3", "model_revision": manifest["revision"],
            "versions": versions, "seed": seed, "audio_duration_upper_bound": args.duration,
            "num_inference_steps": args.steps, "dtype": "bfloat16", "offload": args.offload,
            "device": args.device, "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "generating", "ai_generated": True, "publication_status": "private-candidate",
            "lyrics_audit_status": "pending", "listening_review_status": "pending",
        }
        write_json(output / "generation.json", record)
        started = time.monotonic()
        calls = 0

        def progress_hook(module, inputs, result):
            nonlocal calls
            calls += 1
            if calls % 250 == 0:
                progress = {"stage": "autoregressive", "approx_audio_seconds": (calls - 1) / 25,
                            "elapsed_seconds": round(time.monotonic() - started, 1)}
                write_json(output / "progress.json", progress)
                print(f"seed {seed}: {progress}", flush=True)

        hook = pipe.language_model.model.register_forward_hook(progress_hook)
        try:
            print(f"Generating seed {seed}, upper limit {args.duration}s", flush=True)
            with torch.inference_mode():
                samples = pipe(prompt=caption, lyrics=lyrics, audio_duration=args.duration,
                               num_inference_steps=args.steps,
                               generator=torch.Generator(args.device).manual_seed(seed), output="audios")[0]
            if isinstance(samples, torch.Tensor):
                samples = samples.float().cpu().numpy()
            samples = np.asarray(samples)
            if samples.ndim != 2 or samples.shape[0] != 2 or not samples.shape[1] or not np.isfinite(samples).all():
                raise RuntimeError("Invalid or non-finite stereo waveform")
            raw_peak = float(np.max(np.abs(samples)))
            gain = export_gain(raw_peak)
            samples = samples * gain
            wav = output / "song.wav"
            sf.write(wav, samples.T, pipe.sampling_rate, subtype="PCM_24")
            # Sample-peak headroom does not bound reconstructed inter-sample
            # peaks. Use constant attenuation, not dynamic loudness processing.
            from audio_health_report import ebur128_metrics
            measured = ebur128_metrics(wav)
            if measured["ffmpeg_status"] or measured["true_peak_dbfs"] is None:
                raise RuntimeError("Could not measure the export's true peak")
            extra_gain = true_peak_gain(measured["true_peak_dbfs"])
            if extra_gain < 1:
                samples *= extra_gain
                gain *= extra_gain
                sf.write(wav, samples.T, pipe.sampling_rate, subtype="PCM_24")
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-n", "-i", str(wav),
                            "-c:a", "libmp3lame", "-b:a", "320k", str(output / "song.mp3")], check=True)
            with wav.open("rb") as handle:
                sha = hashlib.file_digest(handle, "sha256").hexdigest()
            actual = samples.shape[1] / pipe.sampling_rate
            record.update(status="generated-awaiting-review", sample_rate=pipe.sampling_rate,
                          duration_seconds=actual, wav_sha256=sha,
                          raw_sample_peak=raw_peak, export_gain_db=20 * math.log10(gain),
                          sample_export_true_peak_dbfs=measured["true_peak_dbfs"], true_peak_target_dbfs=-2.0,
                          duration_limit_reached=actual >= args.duration - 1,
                          elapsed_seconds=round(time.monotonic() - started, 2))
            print(f"Saved {wav} ({actual:.2f}s)", flush=True)
        except Exception as error:
            record.update(status="failed", error=f"{type(error).__name__}: {error}")
            raise
        finally:
            hook.remove()
            write_json(output / "generation.json", record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
