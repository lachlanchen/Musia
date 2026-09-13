#!/usr/bin/env python3
"""Run a resumable, serial ACE XL Turbo sweep with traceable seed/audio pairs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACE = ROOT / "third_party/ACE-Step-1.5"


def save_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def audio_digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lyrics", type=Path, required=True)
    parser.add_argument("--caption", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--duration", type=int, default=150)
    parser.add_argument("--bpm", type=int, default=104)
    parser.add_argument("--key", default="D minor")
    args = parser.parse_args()
    if len(set(args.seeds)) != len(args.seeds) or not 30 <= args.duration <= 240 or not 40 <= args.bpm <= 240:
        parser.error("Seeds must be unique; duration must be 30..240 seconds and BPM 40..240")
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    lyrics = args.lyrics.read_text(encoding="utf-8").strip()
    caption = args.caption.read_text(encoding="utf-8").strip()
    if not lyrics or not caption:
        parser.error("Empty lyric or caption")
    identity = {"lyrics": lyrics, "caption": caption, "duration": args.duration, "bpm": args.bpm,
                "key": args.key, "seeds": args.seeds,
                "model": "acestep-v15-xl-turbo", "steps": 8,
                "aceCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ACE, text=True).strip()}
    request = out / "request.json"
    if request.exists() and json.loads(request.read_text()) != identity:
        raise ValueError("Preserve this sweep; different inputs require a new output directory")
    save_json(request, identity)
    (out / "lyrics-input.txt").write_text(lyrics + "\n", encoding="utf-8")
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES", "0"),
           "PYTHONNOUSERSITE": "1", "PYTHONUNBUFFERED": "1", "TOKENIZERS_PARALLELISM": "false"}
    results = []
    for offset in range(0, len(args.seeds), 2):
        seeds = args.seeds[offset:offset + 2]
        batch = out / ("batch-" + "-".join(map(str, seeds)))
        batch.mkdir(exist_ok=True)
        completed = batch / "completed.json"
        if completed.exists():
            prior = json.loads(completed.read_text())
            if len(prior) != len(seeds) or {r["seed"] for r in prior} != set(seeds):
                raise ValueError(f"Completed seed manifest is inconsistent: {completed}")
            for record in prior:
                if not Path(record["audio"]).is_file():
                    raise FileNotFoundError(record["audio"])
                if audio_digest(Path(record["audio"])) != record["sha256"]:
                    raise ValueError(f"Completed audio bytes changed: {record['audio']}")
            results.extend(prior)
            continue
        if list(batch.glob("*.wav")):
            raise RuntimeError(f"Unregistered audio exists in {batch}; review it before resuming")
        config = {
            "project_root": str(ACE), "checkpoint_dir": str(ACE / "checkpoints"),
            "save_dir": str(batch), "config_path": identity["model"], "task_type": "text2music",
            "caption": caption, "lyrics": str(out / "lyrics-input.txt"),
            "duration": args.duration, "bpm": args.bpm, "keyscale": args.key,
            "timesignature": "4", "vocal_language": "zh", "thinking": False,
            "use_cot_lyrics": False, "use_cot_caption": False, "use_cot_language": False,
            "use_cot_metas": False, "inference_steps": 8, "guidance_scale": 1.0,
            "use_random_seed": False, "seeds": seeds, "batch_size": len(seeds), "audio_format": "wav",
        }
        config_path = batch / "ace.toml"
        config_path.write_text("\n".join(f"{key} = {json.dumps(value, ensure_ascii=False)}" for key, value in config.items()) + "\n", encoding="utf-8")
        print(f"Generating ACE batch {seeds}", flush=True)
        log = batch / "generation.log"
        with log.open("w", encoding="utf-8") as handle:
            subprocess.run([str(ACE / ".venv/bin/python"), "cli.py", "-c", str(config_path), "--backend", "vllm"],
                           cwd=ACE, env=env, stdout=handle, stderr=subprocess.STDOUT, check=True)
        matches = re.findall(r"\[\d+\] Path: (.+?) \| Seed: (\d+)", log.read_text())
        if {int(seed) for _, seed in matches} != set(seeds):
            raise RuntimeError(f"ACE did not confirm each requested seed; inspect {log}")
        records = []
        for audio, seed in matches:
            path = Path(audio)
            if not path.is_absolute():
                path = ACE / path
            digest = audio_digest(path)
            records.append({"seed": int(seed), "audio": str(path), "sha256": digest})
        save_json(completed, records)
        results.extend(records)
        save_json(out / "candidates.json", results)
        print(f"Completed {seeds}", flush=True)
    save_json(out / "candidates.json", results)
    print(out / "candidates.json", flush=True)


if __name__ == "__main__":
    main()
