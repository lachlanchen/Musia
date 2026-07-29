#!/usr/bin/env python3
"""Run local MOSS-Music analysis for independent generated-song QA."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import soundfile as sf
import torch
import torchaudio


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "third_party" / "MOSS-Music"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.modeling_moss_music import MossMusicModel  # noqa: E402
from src.processing_moss_music import MossMusicProcessor  # noqa: E402


TASK_PROMPTS = {
    "lyrics": (
        "请逐字转录音频中实际唱出的全部歌词，并给出尽可能准确的时间戳。"
        "保留重复、漏唱、错唱和语言切换；不要润色，不要依据常识补全，"
        "不要把纯器乐段写成歌词。只输出转录结果。"
    ),
    "analysis": (
        "请按时间顺序分析这首歌的曲式、旋律情绪、演唱、配器、节奏、"
        "高潮与结尾完整性，并指出噪声、爆音、突兀剪切或人声被伴奏掩盖的区段。"
        "区分可观察事实与主观判断。"
    ),
    "chords": (
        "请转录这首歌的调性、拍号、速度和带时间戳的和弦进行。"
        "不确定处明确标注，不要猜造不存在的和弦变化。"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", choices=("instruct", "thinking"), default="thinking")
    parser.add_argument("--task", choices=tuple(TASK_PROMPTS), default="lyrics")
    parser.add_argument("--prompt", help="Override the task prompt.")
    parser.add_argument("--max-new-tokens", type=int, default=2048)
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=50)
    return parser.parse_args()


def load_audio_without_torchcodec(path: Path, sample_rate: int):
    audio, source_rate = sf.read(path, dtype="float32", always_2d=True)
    waveform = torch.from_numpy(audio.mean(axis=1))
    if source_rate != sample_rate:
        waveform = torchaudio.functional.resample(
            waveform,
            orig_freq=source_rate,
            new_freq=sample_rate,
        )
    return waveform.cpu().numpy()


def main() -> int:
    args = parse_args()
    if not args.audio.is_file():
        print(f"Missing audio: {args.audio}", file=sys.stderr)
        return 2
    model_name = (
        "MOSS-Music-8B-Thinking"
        if args.model == "thinking"
        else "MOSS-Music-8B-Instruct"
    )
    model_path = BACKEND_DIR / "weights" / model_name
    if not (model_path / "config.json").is_file():
        print(f"Missing MOSS-Music model: {model_path}", file=sys.stderr)
        return 2
    if not torch.cuda.is_available():
        print("MOSS-Music analysis requires CUDA on this workstation.", file=sys.stderr)
        return 2

    prompt = args.prompt or TASK_PROMPTS[args.task]
    model = MossMusicModel.from_pretrained(
        model_path,
        trust_remote_code=True,
        dtype="auto",
        device_map="cuda:0",
    )
    model.eval()
    processor = MossMusicProcessor.from_pretrained(
        model_path,
        trust_remote_code=True,
        enable_time_marker=True,
    )
    raw_audio = load_audio_without_torchcodec(args.audio, processor.config.mel_sr)
    inputs = processor(text=prompt, audios=[raw_audio], return_tensors="pt")
    inputs = inputs.to(model.device)
    if inputs.get("audio_data") is not None:
        inputs["audio_data"] = inputs["audio_data"].to(model.dtype)
    inputs["audio_input_mask"] = inputs["input_ids"] == processor.audio_token_id

    generation_args: dict[str, object] = {
        "max_new_tokens": args.max_new_tokens,
        "do_sample": args.sample,
        "num_beams": 1,
        "use_cache": True,
    }
    if args.sample:
        generation_args.update(
            temperature=args.temperature,
            top_p=args.top_p,
            top_k=args.top_k,
        )
    with torch.inference_mode():
        generated_ids = model.generate(**inputs, **generation_args)

    input_length = inputs["input_ids"].shape[1]
    raw_text = processor.decode(
        generated_ids[0, input_length:],
        skip_special_tokens=True,
    ).strip()
    text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text + "\n", encoding="utf-8")
    metadata_path = args.output.with_suffix(args.output.suffix + ".json")
    metadata = {
        "audio": str(args.audio.resolve()),
        "model": model_name,
        "task": args.task,
        "prompt": prompt,
        "sample": args.sample,
        "max_new_tokens": args.max_new_tokens,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output": str(args.output.resolve()),
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
