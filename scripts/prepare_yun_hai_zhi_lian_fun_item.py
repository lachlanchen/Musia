#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from pypinyin import Style, pinyin
import pykakasi


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
MEDIA_ID = "yun-hai-zhi-lian"
PUBLIC_AUDIO_BASE = "https://lazyingart.github.io/MusiaSongs/audio/"


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


SELECTED = ROOT / "data/creative_projects/yun-hai-zhi-lian-20260630/selected"
ASR_RUNS = {
    "zh-vocal": ROOT / "data/runs/yun-hai-zhi-lian-20260630-20260630-171616-analysis/analysis/lyrics.json",
    "en-vocal": ROOT / "data/runs/en-20260630-171226-analysis/analysis/lyrics.json",
    "ja-vocal": ROOT / "data/runs/ja-20260630-171244-analysis/analysis/lyrics.json",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def audio_duration(path: Path) -> float:
    output = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(output)


def split_latin(text: str) -> list[str]:
    return [part for part in text.replace(",", " ,").replace("?", " ?").split() if part]


def is_cjk(char: str) -> bool:
    return "\u3400" <= char <= "\u9fff" or "\u3040" <= char <= "\u30ff"


def zh_pinyin(char: str) -> str:
    if not is_cjk(char):
        return ""
    values = pinyin(char, style=Style.TONE3, strict=False, neutral_tone_with_five=True)
    return values[0][0] if values and values[0] else ""


KAKASI = pykakasi.kakasi()


def ja_reading(text: str) -> str:
    if not any(is_cjk(char) for char in text):
        return ""
    converted = KAKASI.convert(text)
    hira = "".join(item.get("hira") or item.get("orig") or "" for item in converted)
    return hira if hira and hira != text else ""


def distribute_tokens(line: dict[str, Any], code: str) -> list[dict[str, Any]]:
    text = line["text"]
    if code == "en":
        parts = split_latin(text)
    else:
        parts = [char for char in text if not char.isspace()]
    if not parts:
        return []
    start = float(line["start"])
    end = float(line["end"])
    step = (end - start) / len(parts)
    tokens: list[dict[str, Any]] = []
    for index, part in enumerate(parts):
        token = {
            "text": part,
            "start": round(start + step * index, 3),
            "end": round(start + step * (index + 1), 3),
        }
        if code == "zh-Hans":
            reading = zh_pinyin(part)
            if reading:
                token["pinyin"] = reading
        elif code == "ja":
            reading = ja_reading(part)
            if reading:
                token["reading"] = reading
        tokens.append(token)
    return tokens


def make_line(line_id: str, start: float, end: float, text: str, code: str, role: str = "lyric") -> dict[str, Any]:
    line = {
        "id": line_id,
        "start": round(start, 3),
        "end": round(end, 3),
        "text": text,
        "singableText": text,
        "role": role,
    }
    line["tokens"] = distribute_tokens(line, code)
    return line


def track(code: str, vocal_set: str, lines: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "fun.lazying.media.text-track.v1",
        "version": 1,
        "mediaId": MEDIA_ID,
        "language": LANG[code],
        "lines": lines,
        "provenance": {
            "vocalSet": vocal_set,
            "correction": "ASR/STT corrected against prompt references; active vocal track follows that vocal's own recognized structure.",
        },
    }


def build_tracks() -> dict[str, dict[str, list[dict[str, Any]]]]:
    # Active lyrics are intentionally short and based on the selected vocal's
    # own ASR evidence, then corrected only when the prompt phrase is sound-close.
    zh = [
        ("l01", 22.13, 23.67, "我想你", "I miss you", "君を想う"),
        ("l02", 24.73, 30.23, "像风落在你身边", "like wind falling beside you", "風のように君のそばへ"),
        ("l03", 31.01, 36.43, "云海之间，爱是一线", "between clouds and sea, love is one line", "雲海のあいだ 愛はひとすじ"),
        ("l04", 37.63, 42.06, "穿过流年，不改从前", "through the flowing years, still unchanged", "時をこえて 変わらない"),
        ("l05", 46.50, 49.40, "你像在眼前", "you feel close before my eyes", "君は目の前のよう"),
        ("l06", 51.06, 52.56, "千年以后", "after a thousand years", "千年のあとも"),
    ]
    en = [
        ("l01", 18.48, 24.36, "Upon the wind, I find the place", "我乘着风寻找那个地方", "風に乗ってその場所を探す"),
        ("l02", 29.91, 33.01, "A cloud's love is just one line", "云的爱只是一条线", "雲の愛はひとすじ"),
        ("l03", 34.45, 40.23, "through flowing and turning time", "穿过流转的时光", "流れめぐる時をこえて"),
    ]
    ja = [
        ("l01", 3.25, 4.69, "風", "wind", "风"),
        ("l02", 27.98, 33.06, "風に乗せて 心", "I place my heart upon the wind", "把心放在风里"),
        ("l03", 34.06, 39.02, "君のそばへ 届け", "may it reach your side", "送到你的身边"),
        ("l04", 54.88, 57.22, "君へ続く", "it continues to you", "一路通向你"),
    ]

    def make_set(rows: list[tuple[str, float, float, str, str, str]], active: str) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = {"en": [], "zh-Hans": [], "ja": []}
        for row in rows:
            line_id, start, end, active_text, en_text, ja_text_or_zh_text = row
            if active == "zh-Hans":
                texts = {"zh-Hans": active_text, "en": en_text, "ja": ja_text_or_zh_text}
            elif active == "en":
                texts = {"en": active_text, "zh-Hans": en_text, "ja": ja_text_or_zh_text}
            else:
                texts = {"ja": active_text, "en": en_text, "zh-Hans": ja_text_or_zh_text}
            for code, text in texts.items():
                result[code].append(make_line(line_id, start, end, text, code))
        return result

    return {
        "zh-vocal": make_set(zh, "zh-Hans"),
        "en-vocal": make_set(en, "en"),
        "ja-vocal": make_set(ja, "ja"),
    }


def copy_audio() -> dict[str, str]:
    audio_dir = SONGS / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "zh-Hans": "yun-hai-zhi-lian-zh-Hans.mp3",
        "en": "yun-hai-zhi-lian-en.mp3",
        "ja": "yun-hai-zhi-lian-ja.mp3",
    }
    sources = {
        "zh-Hans": SELECTED / "yun-hai-zhi-lian-zh-master-v3.mp3",
        "en": SELECTED / "yun-hai-zhi-lian-en-companion-v2-experimental.mp3",
        "ja": SELECTED / "yun-hai-zhi-lian-ja-companion-v2-experimental.mp3",
    }
    for code, source in sources.items():
        if not source.exists():
            raise FileNotFoundError(source)
        shutil.copy2(source, audio_dir / mapping[code])
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)
    return {code: PUBLIC_AUDIO_BASE + filename for code, filename in mapping.items()}


def load_chords() -> list[dict[str, Any]]:
    path = ROOT / "data/runs/yun-hai-zhi-lian-20260630-20260630-171616-analysis/analysis/chords.csv"
    chords: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            start = float(row["start"])
            end = float(row["end"])
            if end <= 64:
                chords.append({
                    "start": round(start, 3),
                    "end": round(end, 3),
                    "name": row["chord"],
                    "degree": "",
                })
    return chords


def make_cover(path: Path) -> None:
    imagegen_cover = ROOT / "website/assets/covers/yun-hai-zhi-lian-imagegen-16x9.png"
    if imagegen_cover.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(imagegen_cover, path)
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), "#eff8ff")
    px = img.load()
    top = (111, 184, 229)
    mid = (233, 245, 250)
    bottom = (28, 91, 143)
    for y in range(height):
        if y < height * 0.58:
            t = y / (height * 0.58)
            color = tuple(int(top[i] * (1 - t) + mid[i] * t) for i in range(3))
        else:
            t = (y - height * 0.58) / (height * 0.42)
            color = tuple(int(mid[i] * (1 - t) + bottom[i] * t) for i in range(3))
        for x in range(width):
            px[x, y] = color
    draw = ImageDraw.Draw(img, "RGBA")
    for i, cy in enumerate([250, 310, 370]):
        draw.ellipse((120 + i * 210, cy - 55, 520 + i * 210, cy + 80), fill=(255, 255, 255, 92))
    for i in range(10):
        y = 555 + i * 22
        draw.arc((-200, y - 180, 1800, y + 190), 190, 350, fill=(255, 255, 255, 34), width=3)
    draw.polygon([(0, 690), (1600, 565), (1600, 900), (0, 900)], fill=(20, 73, 127, 158))
    draw.line((140, 610, 1460, 505), fill=(255, 255, 255, 142), width=3)
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc", 104)
        sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
    except Exception:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
    draw.text((112, 114), "云海之恋", font=title_font, fill=(20, 56, 95, 245))
    draw.text((120, 254), "Musia", font=sub_font, fill=(20, 56, 95, 210))
    draw.text((120, 304), "Cloud Sea Love", font=sub_font, fill=(20, 56, 95, 190))
    img.save(path)


def build_manifest(audio_urls: dict[str, str], duration: float) -> None:
    media_dir = ROOT / "website/data/songs" / MEDIA_ID
    cover = ROOT / "website/assets/covers/yun-hai-zhi-lian-16x9.png"
    make_cover(cover)

    tracks_by_set = build_tracks()
    for set_id, tracks in tracks_by_set.items():
        for code, lines in tracks.items():
            write_json(media_dir / "lyrics" / set_id / f"{code}.json", track(code, set_id, lines))

    # Use the Chinese master active timing as the top-level fallback timeline.
    timeline_lines = [
        {"id": line["id"], "start": line["start"], "end": line["end"], "text": line["text"]}
        for line in tracks_by_set["zh-vocal"]["zh-Hans"]
    ]

    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "云海之恋",
        "localizedTitles": {
            "zh-Hans": "云海之恋",
            "en": "Cloud Sea Love",
            "ja": "雲海の恋",
        },
        "artist": "Musia",
        "description": "A spacious ocean-and-sky love ballad with Mandarin, English, and Japanese candidate vocals.",
        "caption": "Between cloud and sea, love becomes one line through time.",
        "duration": round(duration, 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "云海之恋 - Fun Lazying Art",
            "description": "A Musia ocean-and-sky love ballad with corrected multilingual lyric sets.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": "assets/covers/yun-hai-zhi-lian-16x9.png",
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {
                "id": "cover",
                "label": "云海之恋 cover",
                "role": "cover",
                "src": "assets/covers/yun-hai-zhi-lian-16x9.png",
                "mime": "image/png",
                "width": 1600,
                "height": 900,
            },
            "poster": {
                "id": "poster",
                "label": "16:9 Poster",
                "role": "poster",
                "src": "assets/covers/yun-hai-zhi-lian-16x9.png",
                "mime": "image/png",
                "width": 1600,
                "height": 900,
            },
            "primaryAudio": {
                "id": "yun-hai-zh",
                "label": "Mandarin vocal",
                "roleLabel": "Vocal",
                "role": "vocal",
                "languageCode": "zh-Hans",
                "languageLabel": "中文",
                "lyricSetId": "zh-vocal",
                "src": audio_urls["zh-Hans"],
                "mime": "audio/mpeg",
            },
            "alternateAudio": [
                {
                    "id": "yun-hai-en",
                    "label": "English vocal",
                    "roleLabel": "Vocal",
                    "role": "vocal",
                    "languageCode": "en",
                    "languageLabel": "English",
                    "lyricSetId": "en-vocal",
                    "src": audio_urls["en"],
                    "mime": "audio/mpeg",
                },
                {
                    "id": "yun-hai-ja",
                    "label": "Japanese vocal",
                    "roleLabel": "Vocal",
                    "role": "vocal",
                    "languageCode": "ja",
                    "languageLabel": "日本語",
                    "lyricSetId": "ja-vocal",
                    "src": audio_urls["ja"],
                    "mime": "audio/mpeg",
                },
            ],
        },
        "musical": {
            "key": "D major / detected A-centered cadence",
            "bpm": 143.55,
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
            },
            {
                "id": "en-vocal",
                "label": "English vocal",
                "languageCode": "en",
                "tracks": [
                    {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn", "features": ["active-vocal"], "path": "lyrics/en-vocal/en.json"},
                    {"code": "zh-Hans", "label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "features": ["pinyin", "translation"], "path": "lyrics/en-vocal/zh-Hans.json"},
                    {"code": "ja", "label": "Japanese", "nativeLabel": "日本語", "script": "Jpan", "features": ["furigana", "translation"], "path": "lyrics/en-vocal/ja.json"},
                ],
            },
            {
                "id": "ja-vocal",
                "label": "日本語 vocal",
                "languageCode": "ja",
                "tracks": [
                    {"code": "ja", "label": "Japanese", "nativeLabel": "日本語", "script": "Jpan", "features": ["furigana", "active-vocal"], "path": "lyrics/ja-vocal/ja.json"},
                    {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn", "features": ["translation"], "path": "lyrics/ja-vocal/en.json"},
                    {"code": "zh-Hans", "label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "features": ["pinyin", "translation"], "path": "lyrics/ja-vocal/zh-Hans.json"},
                ],
            },
        ],
        "timeline": {"unit": "seconds", "lines": timeline_lines},
        "provenance": {
            "createdBy": "Musia",
            "coverPrompt": "Deterministic generated cover: bright sky, cloud sea, blue ocean, one white love line, title 云海之恋.",
            "audioSource": "ACE-Step candidate renders selected from data/creative_projects/yun-hai-zhi-lian-20260630.",
            "lyricCorrection": "Corrected per vocal from each selected audio's own ASR/STT plus prompt references. EN/JP are candidate vocals and are not treated as exact prompt-lyric renders.",
            "asrEvidence": {key: str(value) for key, value in ASR_RUNS.items()},
        },
        "artifacts": [],
    }
    write_json(media_dir / "manifest.json", manifest)


def update_catalog() -> None:
    path = ROOT / "website/data/catalog.json"
    catalog = load_json(path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "云海之恋",
        "artist": "Musia",
        "summary": "A spacious cloud-sea love ballad with Mandarin, English, and Japanese vocals, corrected multilingual lyrics, pinyin, furigana, and chord timing.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": "assets/covers/yun-hai-zhi-lian-16x9.png",
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "love", "cloud-sea", "Mandarin", "English", "Japanese", "pinyin", "furigana"],
    }
    items = [entry for entry in catalog.get("items", []) if entry.get("id") != MEDIA_ID]
    insert_at = 1 if items else 0
    items.insert(insert_at, item)
    catalog["items"] = items
    catalog["defaultMedia"] = MEDIA_ID
    write_json(path, catalog)


def main() -> None:
    audio_urls = copy_audio()
    duration = max(audio_duration(SONGS / "audio/yun-hai-zhi-lian-zh-Hans.mp3"), 64.0)
    build_manifest(audio_urls, duration)
    update_catalog()
    print(ROOT / "website/data/songs" / MEDIA_ID / "manifest.json")


if __name__ == "__main__":
    main()
