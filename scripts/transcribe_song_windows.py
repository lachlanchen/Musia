#!/usr/bin/env python3
"""Cross-check disputed sung phrases without VAD or prompt-lyric conditioning."""

import argparse
import json
from pathlib import Path

import soundfile as sf
from faster_whisper import WhisperModel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--language", required=True)
    parser.add_argument("--model", default="large-v3")
    parser.add_argument("--window", nargs=2, type=float, action="append", required=True)
    args = parser.parse_args()
    import librosa

    audio, sr = sf.read(args.audio, dtype="float32", always_2d=True)
    mono = librosa.resample(audio.mean(axis=1), orig_sr=sr, target_sr=16000)
    model = WhisperModel(args.model, device="cuda", compute_type="float16")
    output = {"audio": str(args.audio), "model": args.model, "language": args.language,
              "vad": False, "prompt": None, "windows": []}
    for start, end in args.window:
        if not 0 <= start < end <= len(mono) / 16000:
            raise ValueError("Window is outside the source audio")
        segments, _ = model.transcribe(mono[int(start * 16000):int(end * 16000)], language=args.language,
                                      vad_filter=False, condition_on_previous_text=False,
                                      beam_size=10, word_timestamps=True)
        rows = []
        for segment in segments:
            rows.append({"start": round(segment.start + start, 3), "end": round(segment.end + start, 3),
                         "text": segment.text, "words": [
                             {"word": w.word, "start": round(w.start + start, 3), "end": round(w.end + start, 3),
                              "probability": w.probability} for w in segment.words or []]})
        output["windows"].append({"start": start, "end": end, "segments": rows})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
