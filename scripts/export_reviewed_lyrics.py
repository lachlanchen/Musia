#!/usr/bin/env python3
"""Export a manually reviewed Mandarin ASR mapping as audition lyric artifacts.

This is not an automatic lyric corrector. Every selected segment needs review.
Changed character counts require an explicit, source-bound phrase-span override;
such overrides retain the original span and do not invent syllable timestamps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path


def visible(text: str) -> str:
    return "".join(c for c in text if not c.isspace() and not unicodedata.category(c).startswith("P"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def map_words(segment: dict, corrected: str, overrides: dict | None = None) -> list[dict]:
    words = [word for word in segment["words"] if visible(word["word"])]
    overrides = overrides or {}
    for index, override in overrides.items():
        if not index.isdigit() or int(index) >= len(words):
            raise ValueError("Invalid reviewed ASR word index")
        if override["source"] != words[int(index)]["word"] or not override.get("reason", "").strip():
            raise ValueError("Word-span override needs matching source evidence and a review reason")
        if not visible(override["text"]):
            raise ValueError("An override cannot erase a recognized word")
    counts = [len(visible(overrides.get(str(i), {}).get("text", word["word"]))) for i, word in enumerate(words)]
    text = visible(corrected)
    if sum(counts) != len(text):
        raise ValueError(f"Review needs explicit re-alignment: {segment['text']} -> {corrected}")
    tokens, offset = [], 0
    previous_end = 0.0
    for i, word in enumerate(words):
        count = counts[i]
        start, end = float(word["start"]), float(word["end"])
        if not all(map(math.isfinite, (start, end))) or start < previous_end - 0.02 or end <= start:
            raise ValueError(f"Invalid/duplicate ASR word timing: {word}")
        tokens.append({"text": text[offset:offset + count], "start": start, "end": end,
                       "alignment": "asr-word-span", "sourceText": word["word"]})
        if str(i) in overrides:
            if tokens[-1]["text"] != visible(overrides[str(i)]["text"]):
                raise ValueError("Reviewed word-span replacement differs from the corrected line")
            tokens[-1].update(alignment="source-reviewed-asr-phrase-span",
                              reviewReason=overrides[str(i)]["reason"])
        offset += count
        previous_end = end
    return tokens


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--asr", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_text())
    asr = json.loads(args.asr.read_text())
    if sha256(args.audio) != review["audioSha256"]:
        raise ValueError("The reviewed lyric belongs to a different audio file")
    if asr.get("status") != "ok" or len(review["lines"]) != len(asr["segments"]):
        raise ValueError("Every selected ASR segment needs an explicit review entry")
    if args.output_dir.exists():
        raise FileExistsError("Preserve the existing review export; choose a new output directory")
    from pypinyin import Style, lazy_pinyin, load_phrases_dict
    import pykakasi

    load_phrases_dict({"弹完": [["tán"], ["wán"]], "长安": [["cháng"], ["ān"]]})
    for phrase, readings in review.get("zhReadingOverrides", {}).items():
        if len(phrase) != len(readings):
            raise ValueError(f"Chinese reading override must match character count: {phrase}")
        load_phrases_dict({phrase: [[reading] for reading in readings]})
    kakasi = pykakasi.kakasi()
    proper = {"長安": "ちょうあん", "蘭州": "らんしゅう", "黄河": "こうが", "丹霞": "たんか"}
    proper.update(review.get("jaReadingOverrides", {}))
    proper_pattern = "(" + "|".join(re.escape(word) for word in sorted(proper, key=len, reverse=True)) + ")"
    languages = {
        "zh-Hans": {"code": "zh-Hans", "label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "pronunciation": "pinyin"},
        "en": {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn"},
        "ja": {"code": "ja", "label": "Japanese", "nativeLabel": "日本語", "script": "Jpan", "pronunciation": "furigana"},
    }
    tracks = {code: [] for code in languages}
    audit = []
    for index, (row, segment) in enumerate(zip(review["lines"], asr["segments"]), 1):
        if not re.fullmatch(r"[\u3400-\u9fff]+", visible(row["text"])):
            raise ValueError("This exporter supports native Mandarin lines, not mixed/phonetic source vocals")
        tokens = map_words(segment, row["text"], row.get("wordTextOverrides"))
        readings = lazy_pinyin(visible(row["text"]), style=Style.TONE3, neutral_tone_with_five=True)
        offset = 0
        for token in tokens:
            count = len(token["text"])
            token["pinyin"] = " ".join(readings[offset:offset + count])
            offset += count
        start, end = tokens[0]["start"], tokens[-1]["end"]
        if end > asr["duration"] + 0.05:
            raise ValueError("Lyric timing extends beyond the audio")
        for code in languages:
            text = row["text"] if code == "zh-Hans" else row[code]
            translated = []
            if code == "ja":
                for part in re.split(proper_pattern, text):
                    if part in proper:
                        translated.append({"text": part, "reading": proper[part]})
                    else:
                        for word in kakasi.convert(part):
                            token = {"text": word["orig"]}
                            if re.search(r"[一-龯]", word["orig"]):
                                token["reading"] = word["hira"]
                            translated.append(token)
            elif code == "en":
                translated = [{"text": word} for word in text.split()]
            for i, token in enumerate(translated):
                token.update(start=start + (end - start) * i / len(translated),
                             end=start + (end - start) * (i + 1) / len(translated),
                             alignment="translation-line-relative-approximation")
            tracks[code].append({"id": f"l{index:02d}", "start": start, "end": end, "text": text,
                                 "role": "lyric", "tokens": tokens if code == "zh-Hans" else translated})
        audit.append({"id": f"l{index:02d}", "asr": segment["text"], "reviewed": row["text"],
                      "start": start, "end": end, "changed": visible(segment["text"]) != visible(row["text"])})
    args.output_dir.mkdir(parents=True)
    for code, lines in tracks.items():
        doc = {"schema": "fun.lazying.media.text-track.v1", "version": 1, "mediaId": review["mediaId"],
               "language": languages[code], "lines": lines,
               "provenance": {"vocalSet": review["vocalSet"], "releaseStage": "private-audition",
                              "audioSha256": review["audioSha256"], "correction": review["reviewStatus"],
                              "timing": review["timingStatus"], "notes": review["notes"]}}
        (args.output_dir / f"{code}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    (args.output_dir / "lyrics.reviewed.txt").write_text("\n".join(row["text"] for row in review["lines"]) + "\n")
    lrc = [f"[ti:{review['title']}]", f"[ar:{review['artist']}]"]
    for line in tracks["zh-Hans"]:
        minutes, seconds = divmod(line["start"], 60)
        lrc.append(f"[{int(minutes):02}:{seconds:05.2f}]{line['text']}")
    (args.output_dir / "lyrics.reviewed.lrc").write_text("\n".join(lrc) + "\n")
    (args.output_dir / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
