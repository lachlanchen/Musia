"""Rebuild this song's explicit editorial decisions from immutable ASR evidence.

This recipe is a human-readable review record, not automatic lyric correction.
Run from the Musia root with the musia Python environment.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from export_reviewed_lyrics import sha256, visible
from export_reviewed_japanese_lyrics import reviewed_words

PACK = Path(__file__).resolve().parent
PROJECT = ROOT / "data/creative_projects/aya-brave-in-paris-20261015"
REVIEW = PROJECT / "review/101513"
AUDIO = PROJECT / "sweep-roomier/batch-101513-101514/0b211c1c-11e8-26ea-0c2f-5b7eb5cc3dff.wav"
EXPECTED_AUDIO = "d4c630b04c325fad57e151ed8b50dc1d86ff943b181093c90aad8be10ed7179c"


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build():
    if sha256(AUDIO) != EXPECTED_AUDIO:
        raise ValueError("Selected audio differs from the reviewed candidate")
    if not (REVIEW / "moss-vocal-ja.txt").is_file():
        raise ValueError("Independent MOSS evidence must exist before packaging")
    meanings = json.loads((PACK / "meaning-reference.json").read_text())["lines"]
    sources, indices, source_refs = {}, {}, {}
    for name, filename in (("full", "asr-windows.json"), ("stem", "stem-windows.json")):
        raw_path = REVIEW / filename
        raw = json.loads(raw_path.read_text())
        flattened = {"status": "ok", "language": "ja", "model": raw["model"],
                     "rawSource": str(raw_path.relative_to(ROOT)), "rawSha256": sha256(raw_path),
                     "segments": []}
        indices[name] = {}
        for wi, window in enumerate(raw["windows"]):
            for si, segment in enumerate(window["segments"]):
                indices[name][wi, si] = len(flattened["segments"])
                flattened["segments"].append(copy.deepcopy(segment))
        path = REVIEW / f"{name}-flat.json"
        write(path, flattened)
        sources[name] = flattened
        source_refs[name] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
    lines = []

    def add(reference, source, wi, si, span=None, changes=(), extra=(), text=None, en=None, zh=None):
        ja, english, chinese = meanings[reference - 1] if reference else (text, en, zh)
        anchors = [{"source": source, "segment": indices[source][wi, si]}]
        if span is not None:
            anchors[0]["words"] = list(span)
        for esource, ew, es, espan in extra:
            anchors.append({"source": esource, "segment": indices[esource][ew, es], "words": list(espan)})
        row = {"anchors": anchors, "ja": text or ja, "en": en or english, "zh-Hans": zh or chinese,
               "referenceLine": reference}
        pinyin_fixes = {2: [("片", "pian4")], 3: [("璃", "li5")], 4: [("得", "de5")],
                        18: [("识", "shi5")], 20: [("着", "zhe5")], 22: [("地", "de5")],
                        24: [("片", "pian4")], 34: [("识", "shi5")]}
        if reference in pinyin_fixes:
            row["zhPinyinOverrides"] = [
                {"index": row["zh-Hans"].index(char), "text": char, "pinyin": reading}
                for char, reading in pinyin_fixes[reference]
            ]
        selected = []
        for anchor in anchors:
            words = sources[anchor["source"]]["segments"][anchor["segment"]]["words"]
            start, end = anchor.get("words", (0, len(words)))
            selected.extend(words[start:end])
        if changes:
            row["replacements"] = [
                {"words": [first, last], "source": "".join(visible(w["word"]) for w in selected[first:last]),
                 "text": replacement, "reason": reason}
                for first, last, replacement, reason in changes
            ]
        reviewed_words(row, sources)
        lines.append(row)

    spelling = "Same pronunciation, source orthography; do not replace natural Japanese with a recognizer homophone."
    close = "Preserve the sound-close source using full/stem recognition, Japanese context and the independent transcription; diction is not certified perfect."
    add(1, "stem", 0, 0, changes=[(0, 3, "ルーヴル", spelling)])
    add(2, "stem", 0, 1)
    add(3, "stem", 0, 2)
    add(4, "stem", 0, 3, changes=[(0, 2, "まぶしく", spelling)])
    add(5, "stem", 1, 1)
    add(6, "stem", 1, 2, changes=[(0, 2, "ひとつ", spelling)])
    add(7, "stem", 1, 3)
    add(8, "stem", 1, 4)
    add(9, "stem", 1, 5, changes=[(0, 1, "ヴェ", spelling)])
    add(10, "full", 1, 6, changes=[(3, 4, "が", close), (6, 8, "つかむ", spelling)])
    add(11, "stem", 2, 0, span=(0, 9), changes=[(4, 7, "パリ", close)])
    add(12, "stem", 2, 0, span=(9, 18), changes=[(3, 4, "勇気", close), (5, 7, "羽", spelling)])
    add(13, "stem", 2, 1, span=(0, 7))
    add(14, "stem", 2, 1, span=(7, 17))
    add(15, "stem", 2, 2, span=(0, 7))
    add(16, "stem", 2, 2, span=(7, 16))
    add(17, "stem", 2, 3, span=(0, 9), changes=[(4, 6, "急", close)])
    add(18, "full", 3, 2)
    add(19, "full", 3, 3, changes=[(0, 5, "凱旋門の下", close)])
    add(20, "full", 3, 4)
    add(21, "full", 3, 5, changes=[(5, 8, "灯り", spelling)])
    add(22, "full", 3, 6)
    add(23, "full", 4, 0, span=(0, 6), changes=[(0, 2, "ひとり", spelling), (3, 6, "夕ごはん", spelling)])
    add(24, "full", 4, 0, span=(6, 12))
    add(25, "full", 4, 1, span=(0, 6), changes=[(0, 2, "きれい", spelling), (5, 6, "あと", spelling)])
    add(26, "full", 4, 1, span=(6, 13))
    add(27, "stem", 4, 0, changes=[(4, 5, "パリ", close)])
    add(28, "stem", 4, 1,
        changes=[(5, 6, "が", "Preserve the audible courage repetition; normalize a weak connecting particle, not the whole repeated phrase."),
                 (9, 11, "羽", spelling)],
        text="小さな勇気が勇気が羽になる", en="A little courage, courage turns to wings", zh="小小的勇气，勇气长成了翅膀")
    add(29, "stem", 4, 2)
    add(30, "stem", 4, 3, changes=[(9, 11, "よ", "Merge the prolonged final yo and its echo within the original ASR span; not an extra sentence.")])
    add(31, "stem", 4, 4)
    add(32, "stem", 4, 5)
    add(33, "full", 5, 4, changes=[(4, 5, "急", close)])
    add(34, "stem", 4, 7)
    add(35, "full", 5, 6, changes=[(0, 3, "おみやげ", spelling)])
    add(36, "stem", 5, 0, span=(7, 16))
    add(None, "stem", 5, 1, text="聞かせてね", en="Tell me, won't you?", zh="再讲给我听吧")

    review = {
        "mediaId": "aya-brave-in-paris", "title": "パリへ、ひとつの勇気 · Brave in Paris",
        "vocalSet": "ja-vocal", "audioSha256": EXPECTED_AUDIO, "duration": 188,
        "releaseStage": "published",
        "reviewStatus": "Source cross-checked with selected-audio large-v3 full-mix/stem no-VAD windows and independent MOSS transcription. Owner approved the song for publication on 2026-10-15; Chinese name corrected to 阿芽.",
        "timingStatus": "Selected-audio ASR word anchors; within-word subdivision and translation highlighting are approximate.",
        "notes": "All 36 source lines accounted for. Preserve the actual courage repetition and the extra final 聞かせてね. Sound-close landmark/name and homophone recognition errors are restored conservatively. Instrumental spans and nonlexical breaths are gaps, never lyric placeholders. No human-certified pronunciation or score.",
        "jaReadingOverrides": {"君": "きみ", "朝": "あさ", "写真": "しゃしん", "言葉": "ことば",
                               "昨日": "きのう", "石畳": "いしだたみ", "庭": "にわ", "風": "かぜ",
                               "勇気": "ゆうき", "羽": "はね", "冒険": "ぼうけん", "笑顔": "えがお",
                               "帰る": "かえる", "日": "ひ", "急が": "いそが", "凱旋門": "がいせんもん",
                               "下": "した", "座": "ざ", "灯り": "あかり", "胸": "むね",
                               "一枚": "いちまい", "内緒": "ないしょ", "声": "こえ", "旅": "たび"},
        "sources": source_refs, "lines": lines,
        "independentEvidence": {"path": str((REVIEW / "moss-vocal-ja.txt").relative_to(ROOT)),
                                "sha256": sha256(REVIEW / "moss-vocal-ja.txt")},
    }
    write(PACK / "reviewed-lyrics.json", review)
    print(f"Prepared {len(lines)} reviewed lines; export still validates timing and audio hash")


if __name__ == "__main__":
    build()
