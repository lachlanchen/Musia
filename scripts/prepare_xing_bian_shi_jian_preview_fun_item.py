#!/usr/bin/env python3
"""Prepare the unlisted Fun listening preview for 行遍世间."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pykakasi
from pypinyin import Style, pinyin


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
MEDIA_ID = "xing-bian-shi-jian-preview"
PROJECT = ROOT / "data/creative_projects/xing-bian-shi-jian-20260801"
ANALYSIS = ROOT / "data/runs/xing-bian-shi-jian-preview-seed829213-analysis"
CORRECTION = PROJECT / "correction/selected-seed829213/CORRECTION_PACKET.md"
SOURCE_AUDIO = PROJECT / "selected/xing-bian-shi-jian-zh-Hans-ace-xl-turbo-seed829213.mp3"
PUBLIC_AUDIO = "xing-bian-shi-jian-preview-zh-Hans-ace-xl-turbo-seed829213-20260801.mp3"
PUBLIC_BASE = "https://lazyingart.github.io/MusiaSongs/audio/"
COVER = "assets/covers/xing-bian-shi-jian-preview-16x9.png"
COVER_SOURCE = PROJECT / "assets/cover-source-16x9.png"


LANGUAGES = {
    "zh-Hans": {
        "code": "zh-Hans",
        "label": "Mandarin Chinese",
        "nativeLabel": "中文",
        "script": "Hans",
        "pronunciation": "pinyin",
    },
    "en": {
        "code": "en",
        "label": "English",
        "nativeLabel": "English",
        "script": "Latn",
    },
    "ja": {
        "code": "ja",
        "label": "Japanese",
        "nativeLabel": "日本語",
        "script": "Jpan",
        "pronunciation": "furigana",
    },
}


ROWS = [
    (13.68, 17.06, "我走过北方的雪", "I walked through the northern snow.", "北の雪を歩いてきた"),
    (17.06, 20.34, "看潮汐送走长夜", "I watched the tides carry off the long night.", "潮が長い夜を連れ去るのを見た"),
    (20.34, 23.60, "每一盏远去的灯", "Every lamp receding in the distance", "遠ざかる灯りの一つ一つが"),
    (23.60, 26.46, "都像你未说的再见", "Felt like the farewell you never spoke.", "君の言えなかったさよならに見えた"),
    (26.46, 30.22, "我问过沉默的山", "I asked the silent mountains.", "沈黙する山に問いかけ"),
    (30.22, 34.28, "也问过天边的雁", "I asked the geese at the edge of the sky.", "空の果ての雁にも問いかけた"),
    (36.08, 38.94, "若相逢早已写在", "If our meeting was already written", "もし出会いがすでに記され"),
    (38.94, 41.94, "群星转身的一面", "On the far side of the turning stars,", "巡る星の向こうにあるのなら"),
    (41.94, 45.46, "为何还要我穿过", "Why did I still have to cross", "なぜ私はなお越えねばならない"),
    (45.46, 48.26, "这么多年", "All these years?", "これほど長い年月を"),
    (48.26, 51.66, "我行遍世间所有的路", "I walked every road in this world,", "この世のすべての道を歩いた"),
    (51.66, 54.92, "逆着时光，一步一步", "Against time, step after step,", "時に逆らい、一歩ずつ"),
    (54.92, 57.74, "只为今生与你邂逅", "Just to meet you in this life", "ただこの世で君に出会うため"),
    (57.74, 60.06, "在千万人的尽头", "At the end of a million faces.", "数えきれない人の果てで"),
    (60.06, 63.06, "我看尽人间所有日暮", "I watched every sunset in the human world", "人の世のすべての夕暮れを見つめ"),
    (63.06, 66.52, "终于听见你的脚步", "Until I finally heard your footsteps.", "ようやく君の足音を聞いた"),
    (66.52, 69.70, "原来漂泊不是迷途", "Wandering was never a wrong road;", "旅は迷い道ではなかった"),
    (69.70, 72.96, "每一程都通向归宿", "Every journey was leading me home.", "すべての道のりが帰る場所へ続いていた"),
    (72.96, 76.20, "若我们曾经错过", "If we once missed each other,", "もし私たちがすれ違ったのなら"),
    (76.20, 79.14, "就让春天慢一点", "Let spring move a little slower.", "春よ、もう少しゆっくり進んで"),
    (79.14, 82.46, "让我认出你的眼", "Let me recognize your eyes", "君の瞳を見つけさせて"),
    (82.46, 86.24, "像认出故乡的灯", "As I would recognize a lamp from home.", "故郷の灯りを見つけるように"),
    (86.24, 89.04, "我行遍世间所有的路", "I walked every road in this world,", "この世のすべての道を歩いた"),
    (89.60, 92.16, "逆着时光，一步一步", "Against time, step after step,", "時に逆らい、一歩ずつ"),
    (92.16, 95.42, "只为今生与你邂逅", "Just to meet you in this life", "ただこの世で君に出会うため"),
    (95.42, 98.90, "在岁月温柔的尽头", "At the tender end of the years.", "歳月のやさしい果てで"),
    (98.90, 101.98, "我放下沿途所有孤独", "I set down every loneliness along the way", "道すがらの孤独をすべて置き"),
    (101.98, 105.46, "把余生交给你守护", "And entrust the rest of my life to your care.", "残る人生を君に託す"),
    (105.46, 108.68, "从此山海不再遥远", "From now on, mountains and seas are no longer far.", "これから山も海も遠くはない"),
    (108.68, 111.86, "你在身边就是归途", "With you beside me, I am home.", "君がそばにいる、それが帰る場所"),
    (111.86, 115.00, "我行遍世间所有的路", "I walked every road in this world.", "この世のすべての道を歩いた"),
    (117.40, 120.08, "原来，在身边", "You were here beside me all along.", "帰る場所は、ずっとそばにあった"),
]


KAKASI = pykakasi.kakasi()
JA_READING_OVERRIDES = {"雁": "かり"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_cjk(text: str) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in text)


def weighted_tokens(parts: list[tuple[str, str]], start: float, end: float) -> list[dict[str, Any]]:
    weights = [max(1, len(reading or text)) for text, reading in parts]
    total = sum(weights) or 1
    cursor = start
    tokens: list[dict[str, Any]] = []
    for index, ((text, reading), weight) in enumerate(zip(parts, weights)):
        next_cursor = end if index == len(parts) - 1 else cursor + (end - start) * weight / total
        token: dict[str, Any] = {
            "text": text,
            "start": round(cursor, 3),
            "end": round(next_cursor, 3),
        }
        if reading:
            token["reading"] = reading
        tokens.append(token)
        cursor = next_cursor
    return tokens


def zh_tokens(text: str, start: float, end: float) -> list[dict[str, Any]]:
    chars = [char for char in text if not char.isspace()]
    readings = pinyin(text, style=Style.TONE3, strict=False, neutral_tone_with_five=True)
    parts: list[tuple[str, str]] = []
    reading_index = 0
    for char in text:
        if char.isspace():
            continue
        reading = ""
        if reading_index < len(readings):
            candidate = readings[reading_index][0] if readings[reading_index] else ""
            if is_cjk(char) and candidate != char:
                reading = candidate
        parts.append((char, reading))
        reading_index += 1
    if len(parts) != len(chars):
        raise ValueError(f"Chinese tokenization mismatch: {text}")
    tokens = weighted_tokens(parts, start, end)
    for token in tokens:
        if "reading" in token:
            token["pinyin"] = token.pop("reading")
    return tokens


def ja_tokens(text: str, start: float, end: float) -> list[dict[str, Any]]:
    parts: list[tuple[str, str]] = []
    for item in KAKASI.convert(text):
        original = item.get("orig") or ""
        if not original or original.isspace():
            continue
        reading = JA_READING_OVERRIDES.get(original, item.get("hira") or "")
        if not is_cjk(original) or reading == original:
            reading = ""
        parts.append((original, reading))
    return weighted_tokens(parts, start, end)


def en_tokens(text: str, start: float, end: float) -> list[dict[str, Any]]:
    spaced = text
    for mark in [",", ".", "?", "!", ";", ":"]:
        spaced = spaced.replace(mark, f" {mark} ")
    parts = [(part, "") for part in spaced.split() if part]
    return weighted_tokens(parts, start, end)


def tokens_for(text: str, code: str, start: float, end: float) -> list[dict[str, Any]]:
    if code == "zh-Hans":
        return zh_tokens(text, start, end)
    if code == "ja":
        return ja_tokens(text, start, end)
    return en_tokens(text, start, end)


def make_line(line_id: str, start: float, end: float, text: str, code: str) -> dict[str, Any]:
    return {
        "id": line_id,
        "start": round(start, 3),
        "end": round(end, 3),
        "text": text,
        "singableText": text,
        "role": "lyric",
        "tokens": tokens_for(text, code, start, end),
    }


def build_tracks() -> dict[str, list[dict[str, Any]]]:
    tracks = {code: [] for code in LANGUAGES}
    for index, (start, end, zh, en, ja) in enumerate(ROWS, 1):
        line_id = f"l{index:02d}"
        tracks["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans"))
        tracks["en"].append(make_line(line_id, start, end, en, "en"))
        tracks["ja"].append(make_line(line_id, start, end, ja, "ja"))
    return tracks


def track_document(code: str, lines: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "fun.lazying.media.text-track.v1",
        "version": 1,
        "mediaId": MEDIA_ID,
        "language": LANGUAGES[code],
        "lines": lines,
        "provenance": {
            "vocalSet": "zh-vocal",
            "releaseStage": "unlisted-preview",
            "correction": (
                "Line timing follows separated-vocal large-v3 no-VAD ASR evidence. "
                "Sound-close intended Mandarin is preserved where phonetics, "
                "line length, context, and independent MOSS evidence agree. Two "
                "unsung draft lines are omitted and the generated outro is shortened."
            ),
        },
    }


def load_musical() -> dict[str, Any]:
    chord_data = read_json(ANALYSIS / "analysis/chords.json").get("chords", [])
    beat_data = read_json(ANALYSIS / "analysis/beats.json").get("beats", [])
    chords = [
        {
            "start": round(float(item["start"]), 3),
            "end": round(float(item["end"]), 3),
            "name": item.get("chord") or item.get("name") or "N.C.",
            "degree": "",
            "confidence": round(float(item.get("confidence", 0)), 3),
        }
        for item in chord_data
    ]
    beats = [
        {
            "index": int(item.get("index", index)),
            "time": round(float(item["time"]), 3),
        }
        for index, item in enumerate(beat_data)
    ]
    return {
        "key": "D major requested / D-centered analysis",
        "bpm": 73.828,
        "timeSignature": "4/4",
        "chords": chords,
        "beats": beats,
        "chordSource": "Musia analysis-grade chord inference from this exact render",
        "beatSource": "Musia beat analysis from this exact render",
    }


def ensure_public_audio() -> None:
    if not SOURCE_AUDIO.is_file():
        raise FileNotFoundError(SOURCE_AUDIO)
    target = SONGS / "audio" / PUBLIC_AUDIO
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_AUDIO, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def write_media_item() -> None:
    cover_path = ROOT / "website" / COVER
    if not cover_path.is_file():
        raise FileNotFoundError(cover_path)
    if not CORRECTION.is_file():
        raise FileNotFoundError(CORRECTION)

    media_dir = ROOT / "website/data/songs" / MEDIA_ID
    tracks = build_tracks()
    for code, lines in tracks.items():
        write_json(media_dir / "lyrics/zh-vocal" / f"{code}.json", track_document(code, lines))

    musical = load_musical()
    audio_asset = {
        "id": "xing-bian-shi-jian-zh-vocal",
        "label": "中文",
        "selectorLabel": "中文",
        "publicRoleLabel": "Preview",
        "role": "vocal",
        "languageCode": "zh-Hans",
        "languageLabel": "中文",
        "lyricSetId": "zh-vocal",
        "src": PUBLIC_BASE + PUBLIC_AUDIO,
        "mime": "audio/mpeg",
        "musical": musical,
    }
    timeline = [
        {"id": line["id"], "start": line["start"], "end": line["end"], "text": line["text"]}
        for line in tracks["zh-Hans"]
    ]
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "行遍世间 · Preview",
        "localizedTitles": {
            "zh-Hans": "行遍世间 · 试听",
            "en": "Every Road in the World · Preview",
            "ja": "世界のすべての道・プレビュー",
        },
        "artist": "Musia",
        "description": "A traveler crosses snow, tides, mountains, and years, only to discover that every road was leading home.",
        "caption": "Against time, step after step, every road turns toward one long-awaited meeting.",
        "duration": 124.0,
        "canonicalUrl": f"https://fun.lazying.art/?preview=1#{MEDIA_ID}",
        "publication": {
            "visibility": "unlisted",
            "stage": "preview",
            "label": "Listening Preview",
            "listed": False,
            "note": "Direct-link listening preview; excluded from the default library and playback queue.",
        },
        "share": {
            "title": "行遍世间 - Fun Lazying Art",
            "description": "Across snow, tides, and years, every road leads to one long-awaited meeting.",
            "url": f"https://fun.lazying.art/?preview=1#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {
                "id": "cover",
                "label": "行遍世间 cover",
                "role": "cover",
                "src": COVER,
                "mime": "image/png",
                "width": 1600,
                "height": 900,
            },
            "poster": {
                "id": "poster",
                "label": "16:9 Poster",
                "role": "poster",
                "src": COVER,
                "mime": "image/png",
                "width": 1600,
                "height": 900,
            },
            "primaryAudio": audio_asset,
            "alternateAudio": [],
        },
        "musical": musical,
        "textTracks": [],
        "lyricSets": [
            {
                "id": "zh-vocal",
                "label": "中文",
                "languageCode": "zh-Hans",
                "tracks": [
                    {
                        "code": "zh-Hans",
                        "label": "Mandarin Chinese",
                        "nativeLabel": "中文",
                        "script": "Hans",
                        "features": ["active-vocal", "pinyin", "word-highlight"],
                        "path": "lyrics/zh-vocal/zh-Hans.json",
                    },
                    {
                        "code": "en",
                        "label": "English",
                        "nativeLabel": "English",
                        "script": "Latn",
                        "features": ["translation", "rough-highlight"],
                        "path": "lyrics/zh-vocal/en.json",
                    },
                    {
                        "code": "ja",
                        "label": "Japanese",
                        "nativeLabel": "日本語",
                        "script": "Jpan",
                        "features": ["translation", "furigana", "rough-highlight"],
                        "path": "lyrics/zh-vocal/ja.json",
                    },
                ],
            }
        ],
        "timeline": {"unit": "seconds", "lines": timeline},
        "playback": {"defaultMode": "off"},
        "provenance": {
            "createdBy": "Musia",
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "selectedSeed": 829213,
            "quality": {
                "gate": "unlisted-human-listening-preview",
                "note": "Selected after an eight-candidate music-first review; audio health passed and lyrics were corrected from independent full-mix and separated-vocal evidence.",
            },
            "lyricCorrection": str(CORRECTION.relative_to(ROOT)),
            "coverSource": str(COVER_SOURCE.relative_to(ROOT)),
            "publicAudio": PUBLIC_AUDIO,
        },
    }
    write_json(media_dir / "manifest.json", manifest)

    catalog_path = ROOT / "website/data/catalog.json"
    catalog = read_json(catalog_path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "行遍世间 · Preview",
        "artist": "Musia",
        "summary": "Across snow, tides, mountains, and years, every road leads to one long-awaited meeting.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "visibility": "unlisted",
        "releaseStage": "preview",
        "category": "preview",
        "previewLabel": "Listening Preview",
        "previewReason": "Awaiting the user's listening decision before formal publication.",
        "languages": ["zh-Hans", "en", "ja"],
        "tags": [
            "music",
            "preview",
            "unlisted",
            "Mandarin",
            "journey",
            "homecoming",
            "cinematic",
            "pinyin",
            "furigana",
            "chords",
        ],
    }
    catalog["items"] = [entry for entry in catalog.get("items", []) if entry.get("id") != MEDIA_ID]
    catalog["items"].insert(0, item)
    write_json(catalog_path, catalog)


def main() -> None:
    ensure_public_audio()
    write_media_item()
    print(f"https://fun.lazying.art/?preview=1#{MEDIA_ID}")


if __name__ == "__main__":
    main()
