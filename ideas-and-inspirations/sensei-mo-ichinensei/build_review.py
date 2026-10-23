"""Reproduce explicit lyric edits against hash-bound, unprompted ASR evidence."""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from export_reviewed_lyrics import sha256, visible
from export_reviewed_japanese_lyrics import reviewed_words

PACK = Path(__file__).resolve().parent
PROJECT = ROOT / "data/creative_projects/sensei-mo-ichinensei-20261023"
REVIEW = PROJECT / "review/102314"
AUDIO = PROJECT / "sweep-pronunciation/batch-102313-102314/d2581e1f-452e-5eca-e6c3-59d7fe7d4b5a.wav"
EXPECTED_AUDIO = "bc465e163692027af4162649bee867e42620cfe6cdcc233abe5ce7d635dab4c5"


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build():
    assert sha256(AUDIO) == EXPECTED_AUDIO
    assert (REVIEW / "moss-final-chorus-ja.txt").is_file(), "Independent final-chorus transcription required"
    meanings = json.loads((PACK / "meaning-reference.json").read_text())["lines"]
    sources, indices, source_refs = {}, {}, {}
    for name, filename in (("full", "asr-windows.json"), ("stem", "stem-windows.json"),
                           ("focused", "focused-windows.json")):
        raw_path = REVIEW / filename
        raw = json.loads(raw_path.read_text())
        flattened = {"status": "ok", "language": "ja", "model": raw["model"],
                     "rawSource": str(raw_path.relative_to(ROOT)), "rawSha256": sha256(raw_path), "segments": []}
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
        row = {"anchors": anchors, "ja": text or ja, "en": en or english,
               "zh-Hans": zh or chinese, "referenceLine": reference}
        selected = []
        for anchor in anchors:
            words = sources[anchor["source"]]["segments"][anchor["segment"]]["words"]
            start, end = anchor.get("words", (0, len(words)))
            selected.extend(words[start:end])
        row["replacements"] = [
            {"words": [first, last], "source": "".join(visible(w["word"]) for w in selected[first:last]),
             "text": replacement, "reason": reason} for first, last, replacement, reason in changes]
        reviewed_words(row, sources)
        lines.append(row)

    spelling = "Same pronunciation; restore the intended native Japanese orthography."
    close = "Sound-close source/context correction cross-checked against independent passes, not a claim of perfect diction."
    add(1, "focused", 0, 0, changes=[(0, 2, "内定", close), (5, 6, "三", spelling)])
    add(2, "focused", 0, 1, changes=[(0, 1, "四", close)])
    add(3, "full", 1, 0, (2, 11), changes=[(5, 6, "四", close)])
    add(4, "full", 1, 1)
    add(5, "full", 1, 2)
    add(6, "stem", 1, 1, (6, 15))
    add(7, "full", 1, 4)
    add(8, "full", 1, 5, changes=[(0, 2, "おなか", spelling)])
    add(9, "full", 1, 6, (0, 4), extra=[("full", 2, 0, (4, 7))])
    add(10, "full", 2, 0, (7, 16))
    add(11, "full", 2, 1, (0, 10), changes=[(8, 10, "ゆこう", spelling)])
    add(12, "full", 2, 1, (10, 18))
    add(13, "full", 2, 2, (0, 2), changes=[(0, 2, "せんせいせんせい", spelling)])
    add(14, "full", 2, 2, (2, 7), changes=[(0, 1, "わたし", spelling)])
    add(15, "full", 2, 2, (7, 16))
    add(16, "stem", 2, 3, (9, 16))
    add(17, "stem", 3, 0, (2, 4), changes=[(0, 2, "せんせいせんせい", spelling)])
    add(18, "stem", 3, 0, (4, 10))
    add(19, "full", 3, 2, changes=[(3, 5, "ひとつ", spelling)])
    add(20, "stem", 3, 1, (10, 21), changes=[(2, 7, "どうしてに会", close), (9, 11, "ゆこう", spelling)])
    add(21, "full", 3, 4, changes=[(0, 2, "きれい", spelling), (5, 8, "予定表", close)])
    add(22, "stem", 3, 2, (8, 19))
    add(23, "full", 3, 6)
    add(24, "full", 3, 7, changes=[(6, 9, "ひと休み", spelling)])
    add(25, "full", 3, 8)
    add(26, "full", 4, 0, (6, 13), changes=[(0, 1, "となり", spelling)])
    add(27, "full", 4, 1)
    add(28, "full", 4, 2)
    add(29, "full", 4, 3, changes=[(0, 2, "ひとり", spelling)])
    add(30, "full", 4, 4, changes=[(0, 1, "となり", spelling)])
    add(31, "full", 4, 5)
    add(32, "full", 4, 6)
    add(33, "full", 4, 7, changes=[(5, 6, "わたし", spelling)])
    add(34, "full", 4, 8, changes=[(9, 11, "ゆこう", spelling)])
    add(35, "full", 4, 9)
    add(36, "full", 4, 10, text="今日の甘さを忘れずに")
    add(37, "full", 4, 11, changes=[(0, 2, "せんせいせんせい", spelling)])
    add(38, "full", 5, 0, (2, 7), changes=[(0, 1, "わたし", spelling)])
    add(39, "stem", 5, 1)
    add(40, "full", 5, 2, text="わたしの今日なんか",
        en="This day of mine...", zh="属于我的今天……",
        changes=[(0, 1, "わたし", spelling)])
    add(None, "stem", 6, 0, text="今日の涙も忘れたら",
        en="If I let go of today's tears", zh="若把今天的眼泪也放下")
    add(37, "stem", 6, 1, (0, 2), changes=[(0, 2, "せんせいせんせい", spelling)])
    add(38, "full", 6, 1, (2, 7), changes=[(0, 1, "わたし", spelling)])
    add(41, "full", 6, 2, (0, 2), changes=[(0, 2, "せんせいせんせい", spelling)])
    add(18, "full", 6, 2, (2, 8))
    add(43, "full", 6, 3, changes=[(4, 5, "あと", spelling)])
    add(44, "full", 6, 4, changes=[(0, 1, "わたし", spelling), (8, 10, "ゆこう", spelling)])
    add(45, "full", 7, 0, (0, 3), changes=[(0, 2, "あや", close)])
    add(46, "full", 7, 0, (3, 15), changes=[(3, 6, "ちょっと", close), (6, 8, "背筋", close)])
    add(47, "stem", 7, 1, changes=[(0, 3, "はい", spelling)])
    add(48, "full", 7, 2, changes=[(5, 8, "はじめまして", close)])

    review = {
        "mediaId": "sensei-mo-ichinensei", "title": "せんせいも一年生 · A Beginner, Even Now",
        "vocalSet": "ja-vocal", "audioSha256": EXPECTED_AUDIO, "duration": 240,
        "releaseStage": "published",
        "reviewStatus": "Selected-audio large-v3 full-mix and vocal-stem no-VAD windows, focused CPU rechecks and independent final-chorus MOSS evidence. Human listening approval not claimed.",
        "timingStatus": "Selected-audio ASR word anchors; within-word subdivision and translation highlighting are approximate.",
        "notes": "Preserve source-close Japanese, but retain the actual final-chorus fragment and extra tear line. The final chorus repeats 明日もまだ未完成 rather than the planned 世界はまだ未完成. No instrumental or recognizer-credit rows. Unclear diction remains an editorial uncertainty, not a certified transcription.",
        "jaReadingOverrides": {
            "内定": "ないてい", "三度": "さんど", "四度目": "よんどめ", "特任": "とくにん",
            "助教": "じょきょう", "四文字": "よんもじ", "四": "よん", "千葉": "ちば", "付箋": "ふせん",
            "一年生": "いちねんせい", "明日": "あした", "今日": "きょう", "昨日": "きのう",
            "風": "かぜ", "声": "こえ", "背筋": "せすじ", "歩幅": "ほはば", "椅子": "いす",
            "未来": "みらい", "夕焼け": "ゆうやけ", "涙": "なみだ", "表": "ひょう",
            "深呼吸": "しんこきゅう", "日": "ひ", "私": "わたし", "指": "ゆび", "先": "さき"
        },
        "sources": source_refs, "lines": lines,
        "independentEvidence": {
            "path": str((REVIEW / "moss-final-chorus-ja.txt").relative_to(ROOT)),
            "sha256": sha256(REVIEW / "moss-final-chorus-ja.txt"), "scope": [140, 195],
            "cropSha256": sha256(REVIEW / "final-chorus-vocals.wav")
        }
    }
    write(PACK / "reviewed-lyrics.json", review)
    coverage = []
    for i, (ja, _, _) in enumerate(meanings, 1):
        rows = [j for j, row in enumerate(lines, 1) if row["referenceLine"] == i]
        status = "source-close retained"
        if i == 40:
            status = "changed fragment; not replaced with the absent planned sentence"
        elif i == 42:
            status = "not observed; final chorus repeats source line 18 instead"
        elif i == 36:
            status = "retained with audible particle wo instead of mo"
        coverage.append({"referenceLine": i, "text": ja, "outputRows": rows, "decision": status})
    write(PACK / "lyric-coverage.json", {"audioSha256": EXPECTED_AUDIO, "lines": coverage,
          "extraRows": [i for i, row in enumerate(lines, 1) if row["referenceLine"] is None]})
    print(f"Prepared {len(lines)} rows; export independently validates all timing and source hashes")


if __name__ == "__main__":
    build()
