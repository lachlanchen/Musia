#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pykakasi
from pypinyin import Style, pinyin


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
MEDIA_ID = "liang-zhou-ci-double-original-poem"
PROJECT = ROOT / "data/creative_projects/liang-zhou-ci-double-original-poem-20260704"
SELECTED_MP3 = PROJECT / "selected/liang-zhou-ci-double-original-poem-zh-ace-xl-turbo-seed747323.mp3"
SELECTED_WAV = PROJECT / "selected/liang-zhou-ci-double-original-poem-zh-ace-xl-turbo-seed747323.wav"
ANALYSIS = ROOT / "data/runs/liang-zhou-ci-double-original-poem-7525030-deep-analysis"
PUBLIC_AUDIO_NAME = "liang-zhou-ci-double-original-poem-zh-Hans-ace-xl-turbo-seed747323-20260704.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/liang-zhou-ci-double-original-poem-16x9.png"


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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def duration(path: Path) -> float:
    return float(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)],
            text=True,
        ).strip()
    )


def is_cjk(text: str) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in text)


def zh_pinyin_for(line_text: str, char: str) -> str:
    if not is_cjk(char):
        return ""
    overrides = {
        ("几人回", "几"): "ji3",
        ("万仞山", "仞"): "ren4",
        ("欲饮", "饮"): "yin3",
        ("琵琶", "琵"): "pi2",
        ("琵琶", "琶"): "pa2",
        ("羌笛", "羌"): "qiang1",
    }
    for (needle, target), reading in overrides.items():
        if needle in line_text and char == target:
            return reading
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
    for mark in [",", ".", "?", "!", ";", ":", "—"]:
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
        token = {"text": part, "start": round(start + step * index, 3), "end": round(start + step * (index + 1), 3)}
        if code == "zh-Hans":
            reading = zh_pinyin_for(line["text"], part)
            if reading:
                token["pinyin"] = reading
        elif code == "ja":
            reading = ja_reading(part)
            if reading:
                token["reading"] = reading
        tokens.append(token)
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


def corrected_rows() -> list[tuple[str, float, float, str, str, str]]:
    # Timings come from Demucs-separated vocal large-v3 ASR on the selected
    # seed 747323 render. The public Chinese text preserves original poem
    # lines where ASR drift is sound-close.
    return [
        ("l01", 18.38, 21.66, "黄河远上白云间", "The Yellow River rises toward white clouds.", "黄河は白雲の間へ遠くのぼる"),
        ("l02", 21.66, 25.02, "一片孤城万仞山", "A lonely fortress stands among ten-thousand-fathom mountains.", "一つの孤城が万仞の山に立つ"),
        ("l03", 25.26, 28.06, "羌笛何须怨杨柳", "Why should the Qiang flute lament the willows?", "羌笛はなぜ楊柳を怨むのか"),
        ("l04", 28.32, 30.66, "春风不度玉门关", "The spring wind never crosses Yumen Pass.", "春風は玉門関を越えない"),
        ("l05", 38.60, 39.64, "欲饮琵琶马上催", "Just as we raise the cup, the pipa urges us from horseback.", "飲まんとすれば琵琶が馬上で急かす"),
        ("l06", 39.72, 42.46, "醉卧沙场君莫笑", "If I lie drunk on the battlefield, my lord, do not laugh.", "酔って沙場に伏しても君よ笑うな"),
        ("l07", 42.46, 45.52, "古来征战几人回", "Since ancient times, how many return from war?", "昔から征戦より幾人が帰っただろう"),
        ("l08", 58.94, 61.92, "羌笛何须怨杨柳", "Why should the Qiang flute lament the willows?", "羌笛はなぜ楊柳を怨むのか"),
        ("l09", 62.42, 64.58, "春风不度玉门关", "The spring wind never crosses Yumen Pass.", "春風は玉門関を越えない"),
        ("l10", 64.58, 67.72, "葡萄美酒夜光杯", "Grape wine gleams in a luminous night cup.", "葡萄の美酒は夜光の杯に輝く"),
        ("l11", 67.74, 70.40, "欲饮琵琶马上催", "Just as we raise the cup, the pipa urges us from horseback.", "飲まんとすれば琵琶が馬上で急かす"),
        ("l12", 70.40, 72.90, "醉卧沙场君莫笑", "If I lie drunk on the battlefield, my lord, do not laugh.", "酔って沙場に伏しても君よ笑うな"),
        ("l13", 73.20, 75.22, "古来征战几人回", "Since ancient times, how many return from war?", "昔から征戦より幾人が帰っただろう"),
        ("l14", 75.78, 79.57, "葡萄美酒夜光杯", "Grape wine gleams in a luminous night cup.", "葡萄の美酒は夜光の杯に輝く"),
        ("l15", 79.57, 82.23, "欲饮琵琶马上催", "Just as we raise the cup, the pipa urges us from horseback.", "飲まんとすれば琵琶が馬上で急かす"),
        ("l16", 83.63, 86.57, "醉卧沙场君莫笑", "If I lie drunk on the battlefield, my lord, do not laugh.", "酔って沙場に伏しても君よ笑うな"),
        ("l17", 86.95, 90.37, "古来征战几人回", "Since ancient times, how many return from war?", "昔から征戦より幾人が帰っただろう"),
    ]


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
                "ACE-Step XL Turbo seed 747323. Timings use Demucs-separated vocal large-v3 ASR. "
                "The active Mandarin track restores original Liangzhou Ci poem lines where ASR drift is sound-close; "
                "the omitted first 葡萄美酒夜光杯 in the early hook is not published because the vocal did not clearly recover it."
            ),
        },
    }


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
    if not SELECTED_MP3.exists():
        raise FileNotFoundError(f"Missing selected MP3: {SELECTED_MP3}")
    target = SONGS / "audio" / PUBLIC_AUDIO_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SELECTED_MP3, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def ensure_cover() -> None:
    cover_path = ROOT / "website" / COVER
    cover_path.parent.mkdir(parents=True, exist_ok=True)
    if cover_path.exists():
        return
    raise FileNotFoundError(
        f"Missing public cover: {cover_path}. Generate or copy a no-text 16:9 "
        "AgInTi/image-generation cover that matches the song mood before "
        "publishing the Fun website item."
    )


def write_media_item() -> None:
    ensure_cover()
    media_dir = ROOT / "website/data/songs" / MEDIA_ID
    tracks = build_tracks()
    for code, lines in tracks.items():
        write_json(media_dir / "lyrics/zh-vocal" / f"{code}.json", track(code, lines))

    timeline = [{"id": line["id"], "start": line["start"], "end": line["end"], "text": line["text"]} for line in tracks["zh-Hans"]]
    run_manifest = read_json(ANALYSIS / "manifest.json")
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "凉州词 · 双阕原诗版",
        "localizedTitles": {
            "zh-Hans": "凉州词 · 双阕原诗版",
            "en": "Liangzhou Ci · Two Original Poems",
            "ja": "涼州詞・二首原詩版",
        },
        "artist": "Musia",
        "description": "A frontier-ballad ACE-Step render combining the original Liangzhou Ci lines by Wang Zhihuan and Wang Han, with ASR-audited trilingual lyrics.",
        "caption": "Yellow River clouds, a lonely fortress, luminous wine, pipa, and the sorrow of the border pass.",
        "duration": round(duration(SELECTED_WAV), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "凉州词 · 双阕原诗版 - Fun Lazying Art",
            "description": "Musia ACE frontier ballad from two original Liangzhou Ci poems.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {
                "id": "cover",
                "label": "凉州词 双阕原诗版 cover",
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
            "primaryAudio": {
                "id": "liang-zhou-ci-double-original-poem-zh",
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
        "playback": {"defaultMode": "single"},
        "musical": {
            "key": "D minor requested / detected E minor-centered frontier progression",
            "bpm": round(float(run_manifest.get("tempo_bpm", 184.5703125)), 3),
            "timeSignature": "4/4",
            "chords": load_chords(),
        },
        "lyricSets": [
            {
                "id": "zh-vocal",
                "label": "中文 vocal",
                "languageCode": "zh-Hans",
                "tracks": [
                    {
                        "code": "zh-Hans",
                        "label": "Mandarin Chinese",
                        "nativeLabel": "中文",
                        "script": "Hans",
                        "features": ["pinyin", "active-vocal"],
                        "path": "lyrics/zh-vocal/zh-Hans.json",
                    },
                    {
                        "code": "en",
                        "label": "English",
                        "nativeLabel": "English",
                        "script": "Latn",
                        "features": ["translation"],
                        "path": "lyrics/zh-vocal/en.json",
                    },
                    {
                        "code": "ja",
                        "label": "Japanese",
                        "nativeLabel": "日本語",
                        "script": "Jpan",
                        "features": ["furigana", "translation"],
                        "path": "lyrics/zh-vocal/ja.json",
                    },
                ],
            }
        ],
        "textTracks": [],
        "timeline": {"unit": "seconds", "lines": timeline},
        "artifacts": [],
        "provenance": {
            "createdBy": "Musia",
            "generationProject": "data/creative_projects/liang-zhou-ci-double-original-poem-20260704",
            "audioSource": "ACE-Step 1.5 XL Turbo plain-hook seed 747323, selected from SFT, XL Turbo, base Turbo, and compact rerun candidates.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {
                "selectedAudioLargeV3Overlap": 0.30158730158730157,
                "gate": "selected-review",
                "note": "Separated-vocal ASR recovered the repeated Wang Han hook best; opening Wang Zhihuan quatrain has diction drift.",
            },
            "lyricCorrection": (
                "Active Mandarin text restores original Liangzhou Ci lines where the selected vocal is sound-close. "
                "The first early hook omits 葡萄美酒夜光杯 because separated-vocal ASR did not support a clear line there. "
                "Translations follow the corrected active-vocal line structure."
            ),
            "coverSource": "No-text 16:9 AgInTi/image-generation frontier landscape cover, visually selected for Liangzhou Ci before publication.",
            "publicAudio": PUBLIC_AUDIO_NAME,
        },
    }
    write_json(media_dir / "manifest.json", manifest)

    catalog_path = ROOT / "website/data/catalog.json"
    catalog = read_json(catalog_path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "凉州词 · 双阕原诗版",
        "artist": "Musia",
        "summary": "A frontier-ballad ACE-Step render from two Liangzhou Ci poems, with ASR-audited trilingual lyrics, pinyin, furigana, chords, and beats.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "Tang poetry", "frontier", "Liangzhou Ci", "ACE-Step", "original-poem", "pinyin", "furigana"],
    }
    catalog["items"] = [entry for entry in catalog.get("items", []) if entry.get("id") != MEDIA_ID]
    insert_at = 2 if len(catalog.get("items", [])) >= 2 else len(catalog.get("items", []))
    catalog["items"].insert(insert_at, item)
    write_json(catalog_path, catalog)


def main() -> None:
    ensure_audio()
    write_media_item()
    print(f"https://fun.lazying.art/#{MEDIA_ID}")


if __name__ == "__main__":
    main()
