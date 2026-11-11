#!/usr/bin/env python3
"""Rebuild the explicitly selected word spans for the I'm a Spy master."""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from export_reviewed_lyrics import sha256, visible
from export_reviewed_japanese_lyrics import reviewed_words

PACK = Path(__file__).resolve().parent
PROJECT = ROOT / "data/creative_projects/im-a-spy-20261111"
REVIEW = PROJECT / "review/111101"
AUDIO = PROJECT / "sweep-serial/batch-111101/9abdfbd3-6eba-1720-8bb5-f377a86cb4da.wav"


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    sources, indexes = {}, {}
    for name, filename in (("stem", "stem-windows.json"), ("mix", "asr-windows.json")):
        raw_path = REVIEW / filename
        raw = read(raw_path)
        segments = []
        for wi, window in enumerate(raw["windows"]):
            for si, segment in enumerate(window["segments"]):
                indexes[name, wi, si] = len(segments)
                segments.append(segment)
        sources[name] = {"status": "ok", "language": "en", "segments": segments,
                         "audioSha256": sha256(AUDIO), "rawEvidenceSha256": sha256(raw_path),
                         "method": "large-v3, no VAD, no lyric prompt, overlapping windows"}
    sources["pipeline"] = read(ROOT / "data/runs/im-a-spy-en-111101/analysis/lyrics.json")
    translations = read(PACK / "meaning-reference.json")
    rows = []

    def anchor(name, wi, si, first=None, last=None):
        segment = si if name == "pipeline" else indexes[name, wi, si]
        result = {"source": name, "segment": segment}
        if first is not None:
            result["words"] = [first, last]
        return result

    def add(text, *anchors, changes=()):
        zh, ja = translations[text]
        row = {"en": text, "zh-Hans": zh, "ja": ja, "anchors": list(anchors),
               "replacements": list(changes)}
        words = []
        for ref in anchors:
            original = sources[ref["source"]]["segments"][ref["segment"]]["words"]
            first, last = ref.get("words", [0, len(original)])
            words.extend(copy.deepcopy(original[first:last]))
        # Case is display editing, not a phonetic substitution or time invention.
        if words[0]["word"].strip()[0].islower() and text[0].isupper():
            row["replacements"].append({"words": [0, 1], "source": words[0]["word"],
                "text": words[0]["word"].strip().capitalize(), "reason": "Sentence-initial capitalization only"})
        for index in range(len(words) - 1):
            if visible(words[index]["word"]).lower() == visible(words[index + 1]["word"]).lower() == "bye":
                row["replacements"].append({"words": [index, index + 2],
                    "source": words[index]["word"] + words[index + 1]["word"],
                    "text": "bye-bye", "reason": "Display the two recognized bye syllables as one hyphenated word, retaining their full span"})
        actual = reviewed_words(row, sources, "en")
        row["reviewedSpan"] = [actual[0]["start"], actual[-1]["end"]]
        rows.append(row)

    s = lambda w, i, first=None, last=None: anchor("stem", w, i, first, last)
    m = lambda w, i, first=None, last=None: anchor("mix", w, i, first, last)
    p = lambda i: anchor("pipeline", None, i)
    add("I'm a spy, I'm a spy", s(0, 0))
    add("Don't you ask me why", s(0, 1, 0, 5))
    add("You are in my eyes", s(0, 1, 5, 10))
    add("I don't know, I don't know", s(0, 2), s(1, 0, 3, 6))
    add("How to let you go", s(1, 0, 6, 11))
    add("I won't tell a lie", s(1, 1, 0, 5))
    add("And I won't just say bye-bye", s(1, 1, 5, 12))
    for segment in (2, 4):
        add("I'm a spy, I'm a spy", s(1, segment, 0, 6))
        add("Don't you ask me why", s(1, segment, 6, 11))
        add("You're the apple of my eye", s(1, segment + 1, 0, 6))
        if segment == 2:
            add("And I won't just say bye-bye", s(1, 3, 6, 13))
        else:
            add("Please, baby, don't you cry", s(1, 5, 6, 11))
    add("I won't lie, I won't lie", s(1, 6, 0, 3), s(2, 0, 3, 6))
    add("Even if the stars collide", s(2, 1))
    add("I won't ever say bye-bye", s(2, 2))
    add("Please, baby, don't you cry", p(16))
    add("I'm a fool, I'm a fool", s(2, 4))
    add("Breaking every rule", s(2, 5))
    add("Trying to play it cool", s(3, 0, 3, 8))
    add("But I'm falling into you", s(3, 1))
    add("I can hide, I can hide", s(3, 2))
    add("Every secret deep inside", s(3, 3))
    add("But whenever you walk by", s(3, 4))
    add("All my secrets come alive", s(3, 5))
    add("If I fly, would you fly?", s(3, 6))
    add("If I hide, would you find me?", s(3, 7))
    add("If I lose my way tonight", p(27))
    add("Would you be my guiding light?", m(4, 1))
    add("I'm a cool guy, don't you cry", s(4, 2))
    add("Take my hand and we can fly", s(4, 3))
    add("I'm a spy, I'm a spy", m(4, 4, 0, 1), s(4, 4, 1, 6))
    add("Don't you ask me why", m(4, 5))
    add("You are always in my eyes", m(4, 6))
    add("Like a diamond in the sky", s(4, 7))
    for ranges in (((4, 10), (10, 15), (15, 21)), ((21, 27), (27, 32), (32, 38))):
        for text, (first, last) in zip(("I won't lie, I won't lie", "I won't leave you behind", "I won't ever say bye-bye"), ranges):
            add(text, s(5, 0, first, last))
    add("Please, baby, don't you cry", s(5, 0, 38, 43), changes=[{
        "words": [2, 4], "source": "don't you", "text": "don't you",
        "reason": "Merge zero-duration 'you' into its positive enclosing ASR phrase; no invented word timing"}])
    add("I'm a spy", m(6, 0, 0, 3))
    add("I'm a spy, I'm a spy", s(6, 0))
    add("Don't you ask me why", s(6, 1))
    add("You're the apple of my eye", s(6, 2))
    add("And I won't say bye-bye", s(6, 3))

    evidence = {}
    for name, payload in sources.items():
        path = REVIEW / f"evidence-{name}.json"
        write(path, payload)
        evidence[name] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
    planned = [line.strip() for line in (PACK / "lyrics.en.txt").read_text().splitlines()
               if line.strip() and not line.startswith("[")]
    omitted = {"Like the stars up in the sky"}
    coverage = [{"input": text,
                 "status": "not-recovered-in-selected-performance" if text in omitted else "represented",
                 "publicLines": [i + 1 for i, row in enumerate(rows) if row["en"] == text]}
                for text in planned]
    if any(not entry["publicLines"] and entry["input"] not in omitted for entry in coverage):
        raise ValueError("Unaccounted planned lyric")
    write(PACK / "reviewed-lyrics.json", {
        "mediaId": "im-a-spy", "title": "我是间谍 · I'm a Spy", "artist": "Musia",
        "vocalSet": "en-vocal", "vocalLanguage": "en", "duration": 184,
        "jaReadingOverrides": {"君": "きみ", "人": "ひと", "通る": "とおる"},
        "audioSha256": sha256(AUDIO), "sources": evidence,
        "independentEvidence": [{"path": str((REVIEW / name).relative_to(ROOT)),
                                 "sha256": sha256(REVIEW / name)}
                                for name in ("moss-lyrics.txt", "outro-focus.json")],
        "reviewStatus": "Selected-audio large-v3 full/stem no-VAD review against intended lyrics; independent MOSS cross-check",
        "timingStatus": "ASR word anchors, approximate boundaries; translations use line-relative highlighting",
        "notes": ["Source-close wording is preserved; changed repeats are reflected in the actual sung structure.",
                  "Independent MOSS and two focused outro windows confirm three spy repetitions, including the extra 168-second hook missed by stem-only ASR.",
                  "The first sky comparison is omitted in this take; do not insert unsung text.",
                  "ASR-only closing credits and zero-duration duplicate outro are excluded.",
                  "Musical quality screening is not a human listening approval."],
        "lines": rows, "plannedCoverage": coverage})
    print(f"Reviewed {len(rows)} lines; accounted for {len(coverage)} planned lines")


if __name__ == "__main__":
    main()
