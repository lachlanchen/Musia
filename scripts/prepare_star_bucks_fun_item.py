#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pykakasi
from PIL import Image, ImageDraw, ImageFont
from pypinyin import Style, pinyin


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
MEDIA_ID = "star-bucks"
PROJECT = ROOT / "data/creative_projects/star-bucks-ace-turbo-sweep-20260702"
SELECTED_AUDIO = PROJECT / "selected/star-bucks-en-current-primary.mp3"
ANALYSIS = ROOT / "data/runs/star-bucks-ace-turbo-seed-743103-analysis"
PUBLIC_AUDIO_NAME = "star-bucks-en-ace-turbo-seed-743103-20260703.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/star-bucks-16x9.png"

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
    """Audible structure from the selected vocal, corrected against large-v3 ASR.

    The selected ACE render omits the planned outro. It sings the chorus with a
    few stretched/sustained words, so these timings use the 2026-07-03
    large-v3 selected-audio + vocal-stem correction packet instead of the older
    base ASR line split.
    """

    return [
        ("l01", 0.00, 3.54, "Moon on the water", "水上月光", "水面に映る月"),
        ("l02", 5.60, 8.68, "I sail alone", "我独自航行", "ひとりで帆を上げる"),
        ("l03", 9.90, 13.67, "I left the harbor late at night", "我在深夜离开港口", "夜更けに港を離れた"),
        ("l04", 13.67, 15.86, "The stars were guiding me", "群星为我引路", "星たちが導いてくれた"),
        ("l05", 15.86, 18.03, "The waves said breathe", "海浪说，呼吸", "波は息をしてと言った"),
        ("l06", 19.03, 21.38, "The wind said hold on", "风说，坚持住", "風は踏みとどまれと言った"),
        ("l07", 21.38, 24.00, "And do not fear the sea", "不要害怕这片海", "海を恐れないで"),
        ("l08", 24.00, 28.23, "I saw bright antlers in the foam", "我看见浪沫里明亮的鹿角", "泡の中に光る角を見た"),
        ("l09", 28.23, 31.02, "Like fire above the blue", "像蓝色天际上的火", "青の上で燃える火のように"),
        ("l10", 31.02, 34.76, "They ran across the midnight tide", "它们奔过午夜的潮汐", "真夜中の潮を駆け抜けた"),
        ("l11", 34.76, 37.66, "And showed me what to do", "也告诉我该怎么走", "進む道を教えてくれた"),
        ("l12", 37.66, 39.08, "Star bucks", "星鹿啊", "星の鹿よ"),
        ("l13", 40.62, 41.56, "Star bucks", "星鹿啊", "星の鹿よ"),
        ("l14", 41.56, 43.70, "Swimming through the sea", "在海中向前游", "海を泳いでゆく"),
        ("l15", 44.60, 49.50, "Hooves of light on midnight waves", "光的蹄印踏过午夜浪", "光のひづめが夜の波を渡る"),
        ("l16", 49.50, 52.34, "Still running next to me", "仍在我身旁奔跑", "今も私のそばを走る"),
        ("l17", 52.34, 58.52, "Star bucks, carry on my dear", "星鹿啊，亲爱的，继续向前", "星の鹿よ、どうか進み続けて"),
        ("l18", 58.80, 61.70, "If they can cross the darkest water", "若它们能越过最黑的海水", "いちばん暗い水を越えられるなら"),
        ("l19", 62.55, 64.78, "I can make it here", "我也能抵达这里", "私もここへ辿り着ける"),
    ]


def track(code: str, lines: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "fun.lazying.media.text-track.v1",
        "version": 1,
        "mediaId": MEDIA_ID,
        "language": LANG[code],
        "lines": lines,
        "provenance": {
            "vocalSet": "en-vocal",
            "correction": (
                "Active English lyrics corrected from the selected ACE Turbo vocal using selected-audio large-v3 ASR, "
                "separated-vocal large-v3 ASR, no-VAD segment anchors, and the intended lyric only where pronunciation/context stayed close. "
                "Dropped planned outro lines are not published because the selected audio does not sing them."
            ),
        },
    }


def build_tracks() -> dict[str, list[dict[str, Any]]]:
    lines = {"en": [], "zh-Hans": [], "ja": []}
    for row in corrected_rows():
        line_id, start, end, en, zh, ja = row
        lines["en"].append(make_line(line_id, start, end, en, "en"))
        lines["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans"))
        lines["ja"].append(make_line(line_id, start, end, ja, "ja"))
    return lines


def load_chords() -> list[dict[str, Any]]:
    raw = read_json(ANALYSIS / "analysis/chords.json").get("chords", [])
    return [
        {
            "start": round(float(item["start"]), 3),
            "end": round(float(item["end"]), 3),
            "name": item.get("chord") or item.get("name") or "N.C.",
            "degree": "",
        }
        for item in raw
    ]


def ensure_audio() -> None:
    if not SELECTED_AUDIO.exists():
        raise FileNotFoundError(f"Missing selected audio: {SELECTED_AUDIO}")
    target = SONGS / "audio" / PUBLIC_AUDIO_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SELECTED_AUDIO, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def make_cover() -> None:
    cover_path = ROOT / "website" / COVER
    cover_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), "#06172b")
    draw = ImageDraw.Draw(img, "RGBA")

    for y in range(height):
        t = y / (height - 1)
        r = int(6 * (1 - t) + 10 * t)
        g = int(23 * (1 - t) + 92 * t)
        b = int(43 * (1 - t) + 116 * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    for i in range(120):
        x = (i * 137) % width
        y = 32 + ((i * 83) % 360)
        a = 70 + ((i * 19) % 150)
        radius = 1 + ((i * 7) % 3)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(210, 232, 255, a))

    moon_center = (1280, 170)
    for radius, alpha in [(120, 30), (82, 58), (58, 230)]:
        draw.ellipse(
            (
                moon_center[0] - radius,
                moon_center[1] - radius,
                moon_center[0] + radius,
                moon_center[1] + radius,
            ),
            fill=(236, 248, 255, alpha),
        )

    horizon = 560
    for band in range(8):
        y = horizon + band * 32
        color = (30, 149, 178, 80 - band * 6)
        points = []
        for x in range(-50, width + 80, 40):
            wave = math.sin((x / 92) + band * 0.9) * (16 + band * 1.8)
            points.append((x, y + wave))
        draw.line(points, fill=color, width=4)

    def deer(cx: int, cy: int, scale: float, alpha: int) -> None:
        body = (cx - 72 * scale, cy - 22 * scale, cx + 66 * scale, cy + 24 * scale)
        draw.ellipse(body, fill=(196, 232, 255, alpha))
        draw.ellipse((cx + 42 * scale, cy - 55 * scale, cx + 86 * scale, cy - 14 * scale), fill=(196, 232, 255, alpha))
        for dx in [-44, -10, 32, 58]:
            draw.line([(cx + dx * scale, cy + 14 * scale), (cx + (dx - 24) * scale, cy + 82 * scale)], fill=(196, 232, 255, alpha), width=max(2, int(5 * scale)))
        for side in [-1, 1]:
            base = (cx + 72 * scale, cy - 50 * scale)
            draw.line([base, (base[0] + side * 30 * scale, base[1] - 48 * scale)], fill=(232, 248, 255, alpha), width=max(2, int(4 * scale)))
            draw.line([(base[0] + side * 18 * scale, base[1] - 28 * scale), (base[0] + side * 55 * scale, base[1] - 35 * scale)], fill=(232, 248, 255, alpha), width=max(2, int(3 * scale)))

    deer(590, 470, 1.25, 185)
    deer(850, 520, 0.82, 130)

    title_font = font(82)
    sub_font = font(34)
    draw.text((90, 92), "Star Bucks", fill=(240, 249, 255, 250), font=title_font)
    draw.text((96, 190), "Moonlit ocean anthem by Musia", fill=(172, 221, 234, 230), font=sub_font)
    draw.text((96, 780), "Fun Lazying Art", fill=(220, 242, 248, 210), font=sub_font)
    img.save(cover_path)


def write_media_item() -> None:
    media_dir = ROOT / "website/data/songs" / MEDIA_ID
    tracks = build_tracks()
    for code, lines in tracks.items():
        write_json(media_dir / "lyrics/en-vocal" / f"{code}.json", track(code, lines))

    timeline = [{"id": line["id"], "start": line["start"], "end": line["end"], "text": line["text"]} for line in tracks["en"]]
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "Star Bucks",
        "localizedTitles": {"en": "Star Bucks", "zh-Hans": "星鹿之海", "ja": "星の鹿"},
        "artist": "Musia",
        "description": "An original English Musia ocean anthem about a lone sailor, stars, luminous deer, and refusing to give up.",
        "caption": "Moon on the water, star-deer in the tide, and a small human heart still carrying on.",
        "duration": round(duration(SELECTED_AUDIO), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "Star Bucks - Fun Lazying Art",
            "description": "An original Musia ocean anthem with corrected lyrics, translations, chords, and guitar fingering.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "Star Bucks cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": "star-bucks-en",
                "label": "English",
                "roleLabel": "Vocal",
                "role": "vocal",
                "languageCode": "en",
                "languageLabel": "English",
                "lyricSetId": "en-vocal",
                "src": PUBLIC_AUDIO,
                "mime": "audio/mpeg",
            },
            "alternateAudio": [],
        },
        "musical": {
            "key": "detected D/F# minor centered ocean-pop progression",
            "bpm": 80.75,
            "timeSignature": "4/4",
            "chords": load_chords(),
        },
        "textTracks": [],
        "lyricSets": [
            {
                "id": "en-vocal",
                "label": "English vocal",
                "languageCode": "en",
                "tracks": [
                    {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn", "features": ["active-vocal"], "path": "lyrics/en-vocal/en.json"},
                    {"code": "zh-Hans", "label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "features": ["pinyin", "translation"], "path": "lyrics/en-vocal/zh-Hans.json"},
                    {"code": "ja", "label": "Japanese", "nativeLabel": "日本語", "script": "Jpan", "features": ["furigana", "translation"], "path": "lyrics/en-vocal/ja.json"},
                ],
            }
        ],
        "timeline": {"unit": "seconds", "lines": timeline},
        "playback": {"defaultMode": "single"},
        "provenance": {
            "createdBy": "Musia",
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "audioSource": "ACE-Step XL Turbo seed 743103 selected after rejecting noisy SFT/vocal-hook candidates.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {"largeV3LyricOverlap": 0.7647058823529411, "gate": "pass"},
            "lyricCorrection": "Corrected from selected full-mix and separated-vocal large-v3 ASR plus no-VAD segment anchors. The active text follows the audible render; planned outro lines are omitted because the selected audio does not sing them.",
            "correctionPacket": "data/creative_projects/star-bucks-ace-turbo-sweep-20260702/correction_packets/selected-large-v3-20260703/CORRECTION_PACKET.md",
            "coverSource": "Procedural 16:9 cover generated by scripts/prepare_star_bucks_fun_item.py.",
            "publicAudio": PUBLIC_AUDIO_NAME,
        },
        "artifacts": [],
    }
    write_json(media_dir / "manifest.json", manifest)


def update_catalog() -> None:
    path = ROOT / "website/data/catalog.json"
    catalog = read_json(path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "Star Bucks",
        "artist": "Musia",
        "summary": "An original English ocean anthem about a sailor, luminous star-deer, and carrying on, with corrected lyrics, translations, chords, and guitar fingering.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["en", "zh-Hans", "ja"],
        "tags": ["music", "English", "ocean", "hope", "ACE-Step", "guitar", "chords", "pinyin", "furigana"],
    }
    items = [existing for existing in catalog["items"] if existing.get("id") != MEDIA_ID]
    default_id = catalog.get("defaultMedia")
    insert_at = next((index + 1 for index, existing in enumerate(items) if existing.get("id") == default_id), 1)
    items.insert(insert_at, item)
    catalog["items"] = items
    write_json(path, catalog)


def main() -> None:
    ensure_audio()
    make_cover()
    write_media_item()
    update_catalog()
    print(ROOT / "website/data/songs" / MEDIA_ID / "manifest.json")


if __name__ == "__main__":
    main()
