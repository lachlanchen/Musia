#!/usr/bin/env python3
"""Export reviewed Japanese lyrics with source-bound ASR spans and translations.

This does not correct lyrics automatically. A review selects exact ASR words;
every replacement must name its source text and explain the editorial decision.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import re
from pathlib import Path

from export_reviewed_lyrics import sha256, visible

LANGUAGES = {
    "ja": {"code": "ja", "label": "Japanese", "nativeLabel": "日本語", "script": "Jpan", "pronunciation": "furigana"},
    "en": {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn"},
    "zh-Hans": {"code": "zh-Hans", "label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "pronunciation": "pinyin"},
}


def reviewed_words(row, sources):
    words = []
    for ref in row["anchors"]:
        segment = sources[ref["source"]]["segments"][ref["segment"]]
        first, last = ref.get("words", [0, len(segment["words"])])
        if not 0 <= first < last <= len(segment["words"]):
            raise ValueError("ASR word selection is outside its source segment")
        words.extend(copy.deepcopy(segment["words"][first:last]))
    previous = -1.0
    for word in words:
        start, end = word["start"], word["end"]
        if not all(map(math.isfinite, [start, end])) or start < previous - 0.025 or end < start:
            raise ValueError(f"Invalid ASR word span: {word}")
        previous = end
    replacements = sorted(row.get("replacements", []), key=lambda r: r["words"][0])
    last_end = 0
    for change in replacements:
        first, last = change["words"]
        if not last_end <= first < last <= len(words):
            raise ValueError("Overlapping or invalid replacement span")
        source = "".join(visible(w["word"]) for w in words[first:last])
        if source != visible(change["source"]) or not change.get("reason") or not visible(change["text"]):
            raise ValueError("Replacement needs matching ASR evidence, nonempty text, and a reason")
        last_end = last
    for change in reversed(replacements):
        first, last = change["words"]
        words[first:last] = [{"word": visible(change["text"]), "start": words[first]["start"],
                              "end": words[last - 1]["end"], "reviewReason": change["reason"]}]
    # A zero-length ASR subtoken is valid only inside an explicit reviewed merge.
    if any(word["end"] <= word["start"] for word in words):
        raise ValueError("Zero-length ASR tokens need an explicit positive-span reviewed merge")
    if "".join(visible(w["word"]) for w in words) != visible(row["ja"]):
        raise ValueError(f"Corrected Japanese does not match reviewed anchors: {row['ja']}")
    return words


def japanese_tokens(words, kakasi, overrides):
    # Keep ASR word bounds; only subdivision inside an ASR span is approximate.
    chars = []
    for word in words:
        text = visible(word["word"])
        for i, char in enumerate(text):
            step = (word["end"] - word["start"]) / len(text)
            chars.append((char, word["start"] + step * i, word["start"] + step * (i + 1)))
    text = "".join(c[0] for c in chars)
    parts = kakasi.convert(text)
    tokens, offset = [], 0
    for part in parts:
        count = len(part["orig"])
        token = {"text": part["orig"], "start": round(chars[offset][1], 3),
                 "end": round(chars[offset + count - 1][2], 3), "alignment": "reviewed-asr-span-approximation"}
        if re.search(r"[\u3400-\u9fff]", token["text"]):
            token["reading"] = overrides.get(token["text"], part["hira"])
        tokens.append(token)
        offset += count
    if offset != len(chars):
        raise ValueError("Japanese tokenizer changed source text")
    return tokens


def chinese_tokens(text, overrides):
    from pypinyin import Style, lazy_pinyin

    readings = lazy_pinyin(text, style=Style.TONE3, neutral_tone_with_five=True,
                          errors=lambda span: list(span))
    tokens = [{"text": char, **({"pinyin": reading} if re.search(r"[\u3400-\u9fff]", char) else {})}
              for char, reading in zip(text, readings)]
    for item in overrides:
        index = item["index"]
        if not 0 <= index < len(tokens) or tokens[index]["text"] != item["text"]:
            raise ValueError("Chinese reading override does not match its source character")
        if not re.fullmatch(r"[a-zv]+[1-5]", item["pinyin"]):
            raise ValueError("Chinese reading override must be tone-number pinyin")
        tokens[index]["pinyin"] = item["pinyin"]
    return tokens


def export(review, sources, audio, output):
    if sha256(audio) != review["audioSha256"]:
        raise ValueError("Selected audio changed after lyric review")
    for name, source in sources.items():
        if source.get("status") != "ok" or source.get("language") != "ja":
            raise ValueError(f"Invalid Japanese ASR evidence: {name}")
    import pykakasi

    kakasi = pykakasi.kakasi()
    tracks = {code: [] for code in LANGUAGES}
    previous = -1.0
    for index, row in enumerate(review["lines"], 1):
        words = reviewed_words(row, sources)
        start, end = words[0]["start"], words[-1]["end"]
        if start < previous - 0.025 or end > review["duration"] + 0.05:
            raise ValueError(f"Invalid line {index}: {start}-{end}, previous end {previous}")
        previous = end
        for code in LANGUAGES:
            text = row[code]
            if code == "ja":
                tokens = japanese_tokens(words, kakasi, review.get("jaReadingOverrides", {}))
            else:
                tokens = ([{"text": word} for word in text.split()] if code == "en"
                          else chinese_tokens(text, row.get("zhPinyinOverrides", [])))
                for i, token in enumerate(tokens):
                    token.update(start=round(start + (end - start) * i / len(tokens), 3),
                                 end=round(start + (end - start) * (i + 1) / len(tokens), 3),
                                 alignment="translation-line-relative-approximation")
            tracks[code].append({"id": f"l{index:02d}", "start": round(start, 3), "end": round(end, 3),
                                 "text": text, "role": "lyric", "tokens": tokens})
    output.mkdir(parents=True, exist_ok=True)
    for code, lines in tracks.items():
        payload = {"schema": "fun.lazying.media.text-track.v1", "version": 1, "mediaId": review["mediaId"],
                   "language": LANGUAGES[code], "lines": lines,
                   "provenance": {"vocalSet": review["vocalSet"], "audioSha256": review["audioSha256"],
                                  "correction": review["reviewStatus"], "timing": review["timingStatus"],
                                  "releaseStage": "published", "notes": review["notes"]}}
        (output / f"{code}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    (output / "lyrics.reviewed.txt").write_text("\n".join(x["ja"] for x in review["lines"]) + "\n")
    lrc = [f"[ti:{review['title']}]", "[ar:Musia]"]
    for row in tracks["ja"]:
        minutes, seconds = divmod(row["start"], 60)
        lrc.append(f"[{int(minutes):02d}:{seconds:05.2f}]{row['text']}")
    (output / "lyrics.reviewed.lrc").write_text("\n".join(lrc) + "\n")
    return tracks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_text())
    sources = {}
    for name, entry in review["sources"].items():
        path = Path(entry["path"])
        if sha256(path) != entry["sha256"]:
            raise ValueError(f"ASR evidence changed: {name}")
        sources[name] = json.loads(path.read_text())
    export(review, sources, args.audio, args.output_dir)
    print(args.output_dir)


if __name__ == "__main__":
    main()
