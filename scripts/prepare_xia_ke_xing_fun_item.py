#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from pypinyin import Style, pinyin
import pykakasi


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
MEDIA_ID = "xia-ke-xing"
PROJECT = ROOT / "data/creative_projects/xia-ke-xing-20260630"
SELECTED_WAV = PROJECT / "ace_outputs/zh_corrected_20260630-231230/5f973ed3-5012-047c-e4e4-736d1b72c4c2.wav"
SELECTED_MP3 = PROJECT / "selected/xia-ke-xing-zh-Hans-ace-20260630.mp3"
ANALYSIS = ROOT / "data/runs/xia-ke-xing-20260630-20260630-231322-analysis"
PUBLIC_AUDIO_NAME = "xia-ke-xing-zh-Hans-ace-20260630.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"

LANG = {
    "en": {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn"},
    "zh-Hans": {
        "code": "zh-Hans",
        "label": "Mandarin Chinese",
        "nativeLabel": "中文",
        "script": "Hans",
        "pronunciation": "pinyin",
    },
    "ja": {
        "code": "ja",
        "label": "Japanese",
        "nativeLabel": "日本語",
        "script": "Jpan",
        "pronunciation": "furigana",
    },
}

KAKASI = pykakasi.kakasi()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def duration(path: Path) -> float:
    return float(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)],
            text=True,
        ).strip()
    )


def is_cjk(text: str) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in text)


def zh_pinyin(char: str) -> str:
    if not is_cjk(char):
        return ""
    values = pinyin(char, style=Style.TONE3, strict=False, neutral_tone_with_five=True)
    return values[0][0] if values and values[0] else ""


def ja_reading(text: str) -> str:
    if not is_cjk(text):
        return ""
    converted = KAKASI.convert(text)
    hira = "".join(item.get("hira") or item.get("orig") or "" for item in converted)
    return hira if hira and hira != text else ""


def split_en(text: str) -> list[str]:
    spaced = text
    for mark in [",", ".", "?", "!", ";", ":"]:
        spaced = spaced.replace(mark, f" {mark} ")
    return [part for part in spaced.split() if part]


def split_visible(text: str, code: str) -> list[str]:
    if code == "en":
        return split_en(text)
    return [char for char in text if not char.isspace()]


def tokens_for(line: dict[str, Any], code: str) -> list[dict[str, Any]]:
    parts = split_visible(line["text"], code)
    if not parts:
        return []
    start = float(line["start"])
    end = float(line["end"])
    step = (end - start) / len(parts)
    tokens: list[dict[str, Any]] = []
    for index, part in enumerate(parts):
        item = {"text": part, "start": round(start + step * index, 3), "end": round(start + step * (index + 1), 3)}
        if code == "zh-Hans":
            reading = zh_pinyin(part)
            if reading:
                item["pinyin"] = reading
        elif code == "ja":
            reading = ja_reading(part)
            if reading:
                item["reading"] = reading
        tokens.append(item)
    return tokens


def make_line(line_id: str, start: float, end: float, text: str, code: str) -> dict[str, Any]:
    line = {
        "id": line_id,
        "start": round(start, 3),
        "end": round(end, 3),
        "text": text,
        "singableText": text,
        "role": "lyric",
    }
    line["tokens"] = tokens_for(line, code)
    return line


def track(code: str, lines: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "fun.lazying.media.text-track.v1",
        "version": 1,
        "mediaId": MEDIA_ID,
        "language": LANG[code],
        "lines": lines,
        "provenance": {
            "vocalSet": "zh-vocal",
            "correction": (
                "Mandarin active lyrics corrected from same-vocal small ASR plus the intended Li Bai adaptation. "
                "Sound-close ASR variants such as 夏可熏 are corrected to 侠客行 because the hook is phonetically "
                "close and context/title support the intended phrase. Unsung or unclear final-chorus prompt lines "
                "are intentionally omitted from the public lyric timing."
            ),
        },
    }


def corrected_rows() -> list[tuple[str, float, float, str, str, str]]:
    return [
        ("l01", 0.50, 5.20, "长风起，白马行", "The long wind rises; the white horse rides.", "長風が起ち、白馬は駆ける"),
        ("l02", 7.57, 8.77, "月下剑光明", "Sword light shines beneath the moon.", "月下に剣の光が冴える"),
        ("l03", 10.53, 12.23, "照我少年心", "It lights the young heart in me.", "若き心を照らしている"),
        ("l04", 25.20, 27.34, "吴钩明，霜雪清", "The Wu hook gleams, clear as frost and snow.", "呉鉤は明るく、霜雪のように澄む"),
        ("l05", 27.86, 29.34, "银鞍照白马", "A silver saddle shines on the white horse.", "銀の鞍が白馬を照らす"),
        ("l06", 29.34, 31.52, "一闪如流星", "One flash, like a falling star.", "一閃、流星のように"),
        ("l07", 32.62, 33.74, "三杯酒", "Three cups of wine.", "三杯の酒"),
        ("l08", 33.74, 35.30, "一诺定", "One promise is settled.", "一つの約束が決まる"),
        ("l09", 35.86, 37.26, "千里走人间", "A thousand miles through the world.", "千里の人の世を行く"),
        ("l10", 37.26, 39.76, "不留姓名", "Leaving no name behind.", "名を残さずに"),
        ("l11", 39.76, 43.52, "风雷近，马蹄轻", "Wind and thunder draw near; hoofbeats are light.", "風雷は近く、馬蹄は軽い"),
        ("l12", 44.08, 46.06, "夜过邯郸城", "Night passes over Handan city.", "夜は邯鄲の城を越える"),
        ("l13", 49.36, 50.66, "侠客行", "Ballad of a roaming knight.", "侠客の歌"),
        ("l14", 51.04, 53.26, "侠客行", "Ballad of a roaming knight.", "侠客の歌"),
        ("l15", 53.26, 54.94, "侠客行", "Ballad of a roaming knight.", "侠客の歌"),
        ("l16", 56.99, 57.47, "拂衣去", "He brushes his robe and leaves.", "衣を払って去る"),
        ("l17", 58.69, 60.89, "深藏身与名", "Hiding both body and name.", "身も名も深く隠す"),
        ("l18", 61.39, 62.63, "侠客行", "Ballad of a roaming knight.", "侠客の歌"),
        ("l19", 62.85, 64.61, "侠客行", "Ballad of a roaming knight.", "侠客の歌"),
        ("l20", 64.61, 66.35, "长风吹白马", "The long wind blows across the white horse.", "長風が白馬を吹き抜ける"),
        ("l21", 66.77, 69.75, "月下吴钩明", "Under the moon, the Wu hook gleams.", "月下に呉鉤が明るい"),
        ("l22", 72.09, 74.83, "人间风雪深", "The world is deep with wind and snow.", "人の世は風雪深い"),
        ("l23", 79.98, 82.50, "不为身后名", "Not for a name after death.", "死後の名のためではなく"),
        ("l24", 82.50, 84.46, "只为一诺真", "Only for a promise kept true.", "ただ真実の約束のために"),
    ]


def build_tracks() -> dict[str, list[dict[str, Any]]]:
    lines = {"zh-Hans": [], "en": [], "ja": []}
    for line_id, start, end, zh, en, ja in corrected_rows():
        lines["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans"))
        lines["en"].append(make_line(line_id, start, end, en, "en"))
        lines["ja"].append(make_line(line_id, start, end, ja, "ja"))
    return lines


def load_chords() -> list[dict[str, Any]]:
    chords: list[dict[str, Any]] = []
    with (ANALYSIS / "analysis/chords.csv").open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            chords.append(
                {
                    "start": round(float(row["start"]), 3),
                    "end": round(float(row["end"]), 3),
                    "name": row["chord"],
                    "degree": "",
                }
            )
    return chords


def ensure_audio() -> None:
    if not SELECTED_WAV.exists():
        raise FileNotFoundError(SELECTED_WAV)
    SELECTED_MP3.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(SELECTED_WAV),
            "-vn",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(SELECTED_MP3),
        ],
        check=True,
    )
    target = SONGS / "audio" / PUBLIC_AUDIO_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SELECTED_MP3, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def copy_cover() -> str:
    target = ROOT / f"website/assets/covers/{MEDIA_ID}-16x9.png"
    if not target.exists():
        fallback = ROOT / "website/assets/covers/one-sky-three-lights-16x9.png"
        if not fallback.exists():
            raise FileNotFoundError(f"Missing cover: {target}")
        shutil.copy2(fallback, target)
    return f"assets/covers/{MEDIA_ID}-16x9.png"


def write_media_item() -> None:
    media_dir = ROOT / "website/data/songs" / MEDIA_ID
    cover = copy_cover()
    tracks = build_tracks()
    for code, lines in tracks.items():
        write_json(media_dir / "lyrics/zh-vocal" / f"{code}.json", track(code, lines))
    timeline = [{"id": line["id"], "start": line["start"], "end": line["end"], "text": line["text"]} for line in tracks["zh-Hans"]]
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "侠客行",
        "localizedTitles": {
            "zh-Hans": "侠客行",
            "en": "Knight-Errant Ballad",
            "ja": "侠客行",
        },
        "artist": "Musia",
        "description": "An ACE-Step Mandarin wuxia theme adapted from Li Bai's public-domain poem, with ASR-corrected trilingual lyrics.",
        "caption": "White horse, moonlit sword light, and a promise kept beyond fame.",
        "duration": round(duration(SELECTED_MP3), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "侠客行 - Fun Lazying Art",
            "description": "A Musia ACE-Step Mandarin wuxia theme adapted from Li Bai with corrected trilingual lyrics.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": cover,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "侠客行 cover", "role": "cover", "src": cover, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": cover, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": "xia-ke-xing-zh",
                "label": "中文",
                "roleLabel": "Vocal",
                "role": "vocal",
                "languageCode": "zh-Hans",
                "languageLabel": "中文",
                "lyricSetId": "zh-vocal",
                "src": PUBLIC_AUDIO,
                "mime": "audio/mpeg",
            },
            "alternateAudio": [],
        },
        "musical": {
            "key": "D minor requested / detected C-Gm-Eb centered progression",
            "bpm": 60.09265988372093,
            "timeSignature": "4/4",
            "chords": load_chords(),
        },
        "textTracks": [],
        "lyricSets": [
            {
                "id": "zh-vocal",
                "label": "中文 vocal",
                "languageCode": "zh-Hans",
                "tracks": [
                    {"code": "zh-Hans", "label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "features": ["pinyin", "active-vocal"], "path": "lyrics/zh-vocal/zh-Hans.json"},
                    {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn", "features": ["translation"], "path": "lyrics/zh-vocal/en.json"},
                    {"code": "ja", "label": "Japanese", "nativeLabel": "日本語", "script": "Jpan", "features": ["furigana", "translation"], "path": "lyrics/zh-vocal/ja.json"},
                ],
            }
        ],
        "timeline": {"unit": "seconds", "lines": timeline},
        "provenance": {
            "createdBy": "Musia",
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "audioSource": "ACE-Step 1.5 XL Turbo seed 731535, selected from multiple tested Chinese adaptation candidates.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {"asrOverlap": 0.21604938271604937, "gate": "review"},
            "lyricCorrection": "ASR/listening-oriented correction. The song is an adapted theme, not a complete sung recital of every line in Li Bai's poem. Final-chorus prompt lines after 一诺真 were not recovered clearly and are omitted.",
            "coverSource": cover,
            "publicAudio": PUBLIC_AUDIO_NAME,
        },
        "artifacts": [],
    }
    write_json(media_dir / "manifest.json", manifest)


def update_catalog() -> None:
    path = ROOT / "website/data/catalog.json"
    catalog = read_json(path)
    new_item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "侠客行",
        "artist": "Musia",
        "summary": "An ACE-Step Mandarin wuxia theme adapted from Li Bai's public-domain poem, with ASR-corrected trilingual lyrics, pinyin, furigana, and chord timing.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": f"assets/covers/{MEDIA_ID}-16x9.png",
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "wuxia", "Li Bai", "Mandarin", "ACE-Step", "poetry", "pinyin", "furigana"],
    }
    items = [item for item in catalog["items"] if item.get("id") != MEDIA_ID]
    insert_at = next((index + 1 for index, item in enumerate(items) if item.get("id") == catalog.get("defaultMedia")), 1)
    items.insert(insert_at, new_item)
    catalog["items"] = items
    write_json(path, catalog)


def main() -> None:
    ensure_audio()
    write_media_item()
    update_catalog()
    print(ROOT / "website/data/songs" / MEDIA_ID / "manifest.json")


if __name__ == "__main__":
    main()
