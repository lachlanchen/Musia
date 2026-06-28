#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

import numpy as np
from g2p_en import G2p
from pypinyin import Style, pinyin


ROOT = Path(__file__).resolve().parents[1]
PHONE_SET = ROOT / "third_party" / "SoulX-Singer" / "soulxsinger" / "utils" / "phoneme" / "phone_set.json"

PHRASES = [
    {
        "id": "l01",
        "start": 0.94,
        "end": 6.78,
        "ja": "きらめく森のむこう",
        "ja_reading": "kirameku mori no mukou",
        "en": "bright woods wake under a soft morning sky",
        "zh-Hans": "微光森林晨风醒来",
        "yue-Hant": "微光森林晨風醒來",
    },
    {
        "id": "l02",
        "start": 6.78,
        "end": 11.16,
        "ja": "朝がいま目をさます",
        "ja_reading": "asa ga ima me wo samasu",
        "en": "new morning opens its eyes for you",
        "zh-Hans": "清晨此刻睁开眼",
        "yue-Hant": "清晨此刻睜開眼",
    },
    {
        "id": "l03",
        "start": 12.32,
        "end": 17.30,
        "ja": "こわれた空に虹がかかる",
        "ja_reading": "kowareta sora ni niji ga kakaru",
        "en": "broken skies open into a bridge of rainbows",
        "zh-Hans": "破碎天空架起彩虹",
        "yue-Hant": "破碎天空架起彩虹",
    },
    {
        "id": "l04",
        "start": 18.02,
        "end": 23.52,
        "ja": "小さな胸はふるえてる",
        "ja_reading": "chiisana mune wa furueteru",
        "en": "small hearts still tremble yet keep holding on",
        "zh-Hans": "小小心仍轻轻颤抖",
        "yue-Hant": "小小心仍輕輕顫抖",
    },
    {
        "id": "l05",
        "start": 23.52,
        "end": 28.68,
        "ja": "迷う夜でも手をはなさず",
        "ja_reading": "mayou yoru demo te wo hanasazu",
        "en": "lost nights can never make us let go",
        "zh-Hans": "迷失夜里也别放手",
        "yue-Hant": "迷失夜裡也別放手",
    },
    {
        "id": "l06",
        "start": 30.06,
        "end": 34.28,
        "ja": "君の声だけ信じて",
        "ja_reading": "kimi no koe dake shinjite",
        "en": "trust the quiet voice that stays inside you",
        "zh-Hans": "相信心中那道声音",
        "yue-Hant": "相信心中那道聲音",
    },
    {
        "id": "l07",
        "start": 35.76,
        "end": 40.15,
        "ja": "暗い道にも朝はくる",
        "ja_reading": "kurai michi ni mo asa wa kuru",
        "en": "even dark roads find the morning",
        "zh-Hans": "再暗的路也有清晨",
        "yue-Hant": "再暗嘅路也有清晨",
    },
    {
        "id": "l08",
        "start": 40.15,
        "end": 45.99,
        "ja": "胸のひかりが君を守る",
        "ja_reading": "mune no hikari ga kimi wo mamoru",
        "en": "the light inside your chest will guard you",
        "zh-Hans": "心中光芒会守护你",
        "yue-Hant": "心中光芒會守護你",
    },
    {
        "id": "l09",
        "start": 45.99,
        "end": 51.85,
        "ja": "涙は地図になり",
        "ja_reading": "namida wa chizu ni nari",
        "en": "falling tears become maps when gates open wide",
        "zh-Hans": "眼泪变地图门开启",
        "yue-Hant": "眼淚變地圖門開啟",
    },
    {
        "id": "l10",
        "start": 51.85,
        "end": 56.50,
        "ja": "風を信じて進めるよ",
        "ja_reading": "kaze wo shinjite susumeru yo",
        "en": "trust the wind and keep moving forward now",
        "zh-Hans": "相信风带你向前走",
        "yue-Hant": "相信風帶你向前走",
    },
]

YUE_PHONE = {
    "微": "mei4",
    "光": "gwong1",
    "森": "sam1",
    "林": "lam4",
    "晨": "san4",
    "風": "fung1",
    "醒": "sing2",
    "來": "loi4",
    "清": "cing1",
    "此": "ci2",
    "刻": "hak1",
    "睜": "zaang1",
    "開": "hoi1",
    "眼": "ngaan5",
    "破": "po3",
    "碎": "seoi3",
    "天": "tin1",
    "空": "hung1",
    "架": "gaa3",
    "起": "hei2",
    "彩": "coi2",
    "虹": "hung4",
    "小": "siu2",
    "心": "sam1",
    "仍": "jing4",
    "輕": "hing1",
    "顫": "zin3",
    "抖": "dau2",
    "迷": "mai4",
    "失": "sat1",
    "夜": "je6",
    "裡": "leoi5",
    "也": "jaa5",
    "別": "bit6",
    "放": "fong3",
    "手": "sau2",
    "相": "soeng1",
    "信": "seon3",
    "中": "zung1",
    "那": "naa5",
    "道": "dou6",
    "聲": "sing1",
    "音": "jam1",
    "再": "zoi3",
    "暗": "am3",
    "嘅": "ge3",
    "路": "lou6",
    "有": "jau5",
    "芒": "mong4",
    "會": "wui6",
    "守": "sau2",
    "護": "wu6",
    "你": "nei5",
    "淚": "leoi6",
    "變": "bin3",
    "地": "dei6",
    "圖": "tou4",
    "門": "mun4",
    "啟": "kai2",
    "帶": "daai3",
    "向": "hoeng3",
    "前": "cin4",
    "走": "zau2",
}

LANGS = {
    "en": {"label": "English", "nativeLabel": "English", "script": "Latn", "source_key": "en"},
    "zh-Hans": {"label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "source_key": "zh-Hans"},
    "yue-Hant": {"label": "Cantonese", "nativeLabel": "廣東話", "script": "Hant", "source_key": "yue-Hant"},
}


def load_phone_set() -> set[str]:
    phones = json.loads(PHONE_SET.read_text(encoding="utf-8"))
    return set(phones.keys() if isinstance(phones, dict) else phones)


def load_f0(path: Path) -> list[tuple[float, float]]:
    rows: list[tuple[float, float]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                rows.append((float(row["time"]), float(row["f0_hz"])))
            except ValueError:
                continue
    return rows


def hz_to_midi(frequency: float) -> int:
    if frequency <= 0:
        return 0
    return int(round(69 + 12 * math.log2(frequency / 440.0)))


def midi_to_hz(note: int) -> float:
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def f0_to_slots(f0_rows: list[tuple[float, float]], start: float, end: float, slots: int) -> list[int]:
    fallback = [64, 65, 67, 69, 67, 65, 64, 62]
    result: list[int] = []
    span = max(0.001, end - start)
    for slot_index in range(slots):
        a = start + span * slot_index / slots
        b = start + span * (slot_index + 1) / slots
        values = [freq for time, freq in f0_rows if a <= time < b and 90 <= freq <= 1200]
        if values:
            note = hz_to_midi(float(np.median(values)))
            result.append(max(50, min(76, note)))
        else:
            result.append(fallback[slot_index % len(fallback)])
    return result


def tokenize_english(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text.lower())


def tokenize_cjk(text: str) -> list[str]:
    return [char for char in text if "\u4e00" <= char <= "\u9fff" or char == "嘅"]


def en_phones(word: str) -> str:
    phones = [p for p in G2p()(word) if re.fullmatch(r"[A-Z]+[0-2]?", p)]
    if not phones:
        raise ValueError(f"No English phones for {word}")
    return "en_" + "-".join(phones)


def zh_phone(char: str) -> str:
    py = pinyin(char, style=Style.TONE3, heteronym=False, neutral_tone_with_five=True)[0][0]
    return "zh_" + py.replace("ü", "u:").replace("v", "u:")


def yue_phone(char: str) -> str:
    phone = YUE_PHONE.get(char)
    if not phone:
        raise ValueError(f"Missing Cantonese phone mapping for {char}")
    return "yue_" + phone


def tokens_and_phones(language: str, text: str) -> tuple[list[str], list[str]]:
    if language == "en":
        tokens = tokenize_english(text)
        return tokens, [en_phones(token) for token in tokens]
    if language == "zh-Hans":
        tokens = tokenize_cjk(text)
        return tokens, [zh_phone(token) for token in tokens]
    if language == "yue-Hant":
        tokens = tokenize_cjk(text)
        return tokens, [yue_phone(token) for token in tokens]
    raise ValueError(language)


def validate_phones(phones: list[str], phone_set: set[str]) -> None:
    missing: list[str] = []
    for phone_group in phones:
        if phone_group == "<SP>":
            continue
        parts = phone_group.split("-")
        prefix = ""
        if parts and "_" in parts[0]:
            prefix = parts[0].split("_", 1)[0] + "_"
        for index, phone in enumerate(parts):
            if index > 0 and prefix and "_" not in phone:
                phone = prefix + phone
            if phone not in phone_set:
                missing.append(phone)
    if missing:
        raise ValueError(f"Phones missing from SoulX phone_set: {sorted(set(missing))}")


def note_frames(duration: float, pitch: int, sample_rate: int = 24000, hop_size: int = 480) -> list[float]:
    frames = max(1, int(round(duration * sample_rate / hop_size)))
    if pitch <= 0:
        return [0.0] * frames
    base = midi_to_hz(pitch)
    return [round(base * (1.0 + 0.004 * math.sin(i * 0.5)), 1) for i in range(frames)]


def build_metadata(language: str, f0_rows: list[tuple[float, float]], phone_set: set[str]) -> list[dict]:
    items: list[dict] = []
    source_key = LANGS[language]["source_key"]
    for phrase in PHRASES:
        tokens, phones = tokens_and_phones(language, phrase[source_key])
        validate_phones(phones, phone_set)
        start = float(phrase["start"])
        end = float(phrase["end"])
        total = max(0.8, end - start)
        lead = min(0.28, total * 0.08)
        tail = min(0.28, total * 0.08)
        available = max(0.2, total - lead - tail)
        base = available / len(tokens)
        durations = [lead]
        for i, _token in enumerate(tokens):
            value = base
            if i == len(tokens) - 1:
                value += min(0.18, base * 0.35)
            elif len(tokens) > 1:
                value -= min(0.18 / (len(tokens) - 1), base * 0.1)
            durations.append(max(0.08, value))
        durations.append(tail)
        scale = total / sum(durations)
        durations = [round(value * scale, 3) for value in durations]
        pitches = [0] + f0_to_slots(f0_rows, start, end, len(tokens)) + [0]
        note_type = [1] + [2] * len(tokens) + [1]
        if len(note_type) > 2:
            note_type[-2] = 3
        f0: list[float] = []
        for duration, pitch in zip(durations, pitches):
            f0.extend(note_frames(duration, pitch))
        items.append(
            {
                "index": phrase["id"],
                "language": {"en": "English", "zh-Hans": "Mandarin", "yue-Hant": "Cantonese"}[language],
                "time": [int(round(start * 1000)), int(round(end * 1000))],
                "duration": " ".join(f"{value:.3f}" for value in durations),
                "text": " ".join(["<SP>"] + tokens + ["<SP>"]),
                "phoneme": " ".join(["<SP>"] + phones + ["<SP>"]),
                "note_pitch": " ".join(str(value) for value in pitches),
                "note_type": " ".join(str(value) for value in note_type),
                "f0": " ".join(f"{value:.1f}" for value in f0),
                "musia_phrase": phrase,
            }
        )
    return items


def write_text_tracks(output_dir: Path) -> None:
    phrase_map = {
        "schema": "musia.same_score_phrase_map.v1",
        "source": "take-care-of-yourself Japanese romaji guide",
        "phrases": PHRASES,
    }
    (output_dir / "phrase_map.json").write_text(json.dumps(phrase_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for language, meta in LANGS.items():
        key = meta["source_key"]
        lines = [f"{phrase['id']}: {phrase[key]}" for phrase in PHRASES]
        (output_dir / f"lyrics_{language}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create same-score SoulX target metadata for EN/ZH/YUE localizations.")
    parser.add_argument("--f0-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    f0_rows = load_f0(args.f0_csv)
    phone_set = load_phone_set()
    write_text_tracks(args.output_dir)
    for language in LANGS:
        metadata = build_metadata(language, f0_rows, phone_set)
        out = args.output_dir / f"soulx_target_{language}.json"
        out.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(out)


if __name__ == "__main__":
    main()
