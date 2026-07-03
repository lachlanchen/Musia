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
MEDIA_ID = "animal-no-di-liu-gan"
PROJECT = ROOT / "data/creative_projects/animals-di-liu-gan-mixed-20260703"
SELECTED_AUDIO = PROJECT / "selected/animal-no-di-liu-gan-mixed-ace-turbo-seed-747304.mp3"
ANALYSIS = ROOT / "data/runs/animal-no-di-liu-gan-mixed-seed-747304-analysis"
PUBLIC_AUDIO_NAME = "animal-no-di-liu-gan-mixed-ace-turbo-seed-747304-20260703.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/animal-no-di-liu-gan-16x9.png"

LANG = {
    "mul": {"code": "mul", "label": "Mixed", "nativeLabel": "Mixed", "script": "Latn+Hans+Jpan"},
    "en": {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn"},
    "zh-Hans": {"code": "zh-Hans", "label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "pronunciation": "pinyin"},
    "ja": {"code": "ja", "label": "Japanese", "nativeLabel": "日本語", "script": "Jpan", "pronunciation": "furigana"},
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
    if code == "mul":
        parts: list[str] = []
        current = ""
        for char in text:
            if char.isspace():
                if current:
                    parts.append(current)
                    current = ""
            elif is_cjk(char) or "\u3040" <= char <= "\u30ff":
                if current:
                    parts.append(current)
                    current = ""
                parts.append(char)
            elif char in ",.!?;:":
                if current:
                    parts.append(current)
                    current = ""
                parts.append(char)
            else:
                current += char
        if current:
            parts.append(current)
        return parts
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
        if code in {"zh-Hans", "mul"}:
            reading = zh_pinyin(part)
            if reading:
                token["pinyin"] = reading
        if code == "ja":
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


def corrected_rows() -> list[tuple[str, float, float, str, str, str, str]]:
    """Audible structure from selected ACE XL Turbo seed 747304.

    These rows follow the full same-render ASR timing from
    data/runs/animal-no-di-liu-gan-mixed-seed-747304-analysis/analysis/lyrics.json.
    The active lyric preserves the intended lyric only when it is sound-close
    and structurally supported by ASR/listening; otherwise it follows the
    generated vocal.
    """

    return [
        ("l01", 0.02, 0.76, "Yeah", "Yeah", "Yeah", "Yeah"),
        ("l02", 6.06, 13.72, "Running barefoot through a neon rain", "Running barefoot through a neon rain", "赤足でネオンの雨を駆ける", "赤脚跑过霓虹雨"),
        ("l03", 13.72, 16.56, "Every heartbeat knows my name", "Every heartbeat knows my name", "鼓動は私の名を知っている", "每一次心跳都知道我的名字"),
        ("l04", 16.56, 19.14, "风吹过城市的墙", "Wind blows across the city wall", "風が街の壁を吹き抜ける", "风吹过城市的墙"),
        ("l05", 19.14, 21.78, "我听见森林在呼唤", "I hear the forest calling", "森が呼んでいるのを聞く", "我听见森林在呼唤"),
        ("l06", 21.78, 24.44, "不是迷路，不是逃亡", "Not lost, not running away", "迷子でも逃亡でもない", "不是迷路，不是逃亡"),
        ("l07", 24.44, 27.08, "心灵唤醒来的方向", "The heart wakes toward its way", "心が目覚める方角へ", "心灵唤醒来的方向"),
        ("l08", 27.08, 30.42, "夜の匂いがする 胸の奥", "The night has a scent deep in my chest", "夜の匂いがする 胸の奥", "夜的气息在胸口深处"),
        ("l09", 30.42, 33.78, "胸の奥で光る 怖くないよ", "A light glows inside; I am not afraid", "胸の奥で光る 怖くないよ", "心底发光，不再害怕"),
        ("l10", 33.78, 36.56, "まだ見えない明日へ", "Toward a tomorrow still unseen", "まだ見えない明日へ", "走向还看不见的明天"),
        ("l11", 39.18, 41.06, "I trust my sixth sense", "I trust my sixth sense", "第六感を信じる", "我相信我的第六感"),
        ("l12", 41.86, 44.76, "野性在心里燃烧", "Wildness burns inside my heart", "野性が心で燃えている", "野性在心里燃烧"),
        ("l13", 44.76, 47.10, "I dance with my defense", "I dance with my defense", "守りながら踊る", "我与防备共舞"),
        ("l14", 48.06, 50.84, "No crown, no golden cage", "No crown, no golden cage", "冠も黄金の檻もいらない", "没有王冠，也没有金色牢笼"),
        ("l15", 64.01, 68.32, "傷ついた日も 夢を抱いて", "Even on wounded days, I hold a dream", "傷ついた日も 夢を抱いて", "受伤的日子里，也抱着梦"),
        ("l16", 69.04, 71.66, "小さな獣が 心を守る", "A small animal protects my heart", "小さな獣が 心を守る", "小小的兽守护着心"),
        ("l17", 71.66, 73.98, "I rise with innocence", "I rise with innocence", "無垢なまま立ち上がる", "我带着纯真站起"),
        ("l18", 73.98, 77.66, "誰も I trust my sixth sense", "No one can take my sixth sense", "誰も 第六感は奪えない", "谁也夺不走我的第六感"),
        ("l19", 79.04, 81.22, "但我知道，我知道", "But I know, I know", "でもわかっている", "但我知道，我知道"),
        ("l20", 81.90, 83.98, "My wild heart is in love", "My wild heart is in love", "野生の心は恋をしている", "我的野心正在爱里"),
    ]


def track(code: str, lines: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "fun.lazying.media.text-track.v1",
        "version": 1,
        "mediaId": MEDIA_ID,
        "language": LANG[code],
        "lines": lines,
        "provenance": {
            "vocalSet": "mixed-vocal",
            "correction": (
                "Corrected from the selected ACE XL Turbo seed 747304 vocal using same-render faster-whisper "
                "small ASR in zh/en/auto modes and the intended lyric only where pronunciation and structure were close. "
                "The published timing follows all 20 ASR-supported vocal segments through 83.98s."
            ),
        },
    }


def build_tracks() -> dict[str, list[dict[str, Any]]]:
    lines = {"mul": [], "en": [], "zh-Hans": [], "ja": []}
    for line_id, start, end, active, en, ja, zh in corrected_rows():
        lines["mul"].append(make_line(line_id, start, end, active, "mul"))
        lines["en"].append(make_line(line_id, start, end, en, "en"))
        lines["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans"))
        lines["ja"].append(make_line(line_id, start, end, ja, "ja"))
    return lines


def load_chords() -> list[dict[str, Any]]:
    raw_path = ANALYSIS / "analysis/chords.json"
    if raw_path.exists():
        raw = read_json(raw_path).get("chords", [])
        source = [
            {
                "start": float(item["start"]),
                "end": float(item["end"]),
                "name": item.get("chord") or item.get("name") or "N.C.",
                "confidence": float(item.get("confidence") or 1.0),
            }
            for item in raw
        ]
    else:
        source = []

    if not source:
        return []

    # The detector emits beat-level chord changes. For the website's guitar
    # fingering panel, show stable two-bar blocks so the current chord moves in
    # time without flickering every half second.
    window = 5.2
    total = duration(SELECTED_AUDIO)
    smoothed: list[dict[str, Any]] = []
    start = 0.0
    while start < total - 0.05:
        end = min(total, start + window)
        scores: dict[str, float] = {}
        for chord in source:
            overlap = max(0.0, min(end, chord["end"]) - max(start, chord["start"]))
            if overlap <= 0:
                continue
            scores[chord["name"]] = scores.get(chord["name"], 0.0) + overlap * chord["confidence"]
        name = max(scores.items(), key=lambda item: item[1])[0] if scores else (smoothed[-1]["name"] if smoothed else "N.C.")
        if smoothed and smoothed[-1]["name"] == name:
            smoothed[-1]["end"] = round(end, 3)
        else:
            smoothed.append({"start": round(start, 3), "end": round(end, 3), "name": name, "degree": ""})
        start = end
    return smoothed


def ensure_audio() -> None:
    if not SELECTED_AUDIO.exists():
        raise FileNotFoundError(f"Missing selected audio: {SELECTED_AUDIO}")
    target = SONGS / "audio" / PUBLIC_AUDIO_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SELECTED_AUDIO, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def make_cover() -> None:
    cover_path = ROOT / "website" / COVER
    if cover_path.exists():
        return

    # Fallback only. The public cover is an image-generated, text-free asset
    # committed at website/assets/covers/animal-no-di-liu-gan-16x9.png.
    # Keep this fallback text-free so reruns never leak title text onto a
    # music-publish cover.
    cover_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), "#111827")
    draw = ImageDraw.Draw(img, "RGBA")

    for y in range(height):
        t = y / (height - 1)
        r = int(18 * (1 - t) + 36 * t)
        g = int(25 * (1 - t) + 88 * t)
        b = int(43 * (1 - t) + 90 * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    for i in range(90):
        x = (i * 167) % width
        y = 40 + ((i * 97) % 470)
        radius = 1 + ((i * 5) % 3)
        alpha = 70 + ((i * 23) % 150)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(215, 238, 255, alpha))

    moon = (1240, 178)
    for radius, alpha in [(128, 28), (86, 70), (56, 230)]:
        draw.ellipse((moon[0] - radius, moon[1] - radius, moon[0] + radius, moon[1] + radius), fill=(244, 248, 255, alpha))

    # Neon city wall.
    base_y = 620
    for idx, x in enumerate(range(0, width + 80, 80)):
        h = 110 + ((idx * 53) % 210)
        color = (29 + idx * 9 % 80, 160 + idx * 7 % 70, 170 + idx * 11 % 60, 145)
        draw.rounded_rectangle((x - 14, base_y - h, x + 48, base_y), radius=8, fill=color)
        for wy in range(int(base_y - h + 18), base_y - 8, 34):
            draw.rectangle((x + 2, wy, x + 16, wy + 12), fill=(255, 232, 138, 120))

    # Abstract animal sixth-sense silhouette.
    cx, cy = 670, 500
    draw.ellipse((cx - 180, cy - 78, cx + 160, cy + 76), fill=(247, 247, 220, 210))
    draw.ellipse((cx + 105, cy - 128, cx + 218, cy - 18), fill=(247, 247, 220, 210))
    for dx in [-110, -42, 54, 112]:
        draw.line([(cx + dx, cy + 50), (cx + dx - 32, cy + 192)], fill=(247, 247, 220, 210), width=12)
    for side in [-1, 1]:
        base = (cx + 192, cy - 104)
        draw.line([base, (base[0] + side * 42, base[1] - 92)], fill=(255, 248, 219, 230), width=9)
        draw.line([(base[0] + side * 24, base[1] - 56), (base[0] + side * 76, base[1] - 64)], fill=(255, 248, 219, 200), width=6)

    for radius, alpha in [(112, 85), (62, 180), (24, 245)]:
        draw.ellipse((cx + 22 - radius, cy - radius, cx + 22 + radius, cy + radius), fill=(48, 237, 225, alpha))
    for offset, color in [(0, (45, 237, 225, 180)), (26, (237, 72, 173, 150)), (-30, (246, 209, 83, 145))]:
        draw.arc((cx - 330 + offset, cy - 280, cx + 460 + offset, cy + 260), 198, 340, fill=color, width=8)
    img.save(cover_path)


def write_media_item() -> None:
    media_dir = ROOT / "website/data/songs" / MEDIA_ID
    tracks = build_tracks()
    for code, lines in tracks.items():
        write_json(media_dir / "lyrics/mixed-vocal" / f"{code}.json", track(code, lines))

    timeline = [{"id": line["id"], "start": line["start"], "end": line["end"], "text": line["text"]} for line in tracks["mul"]]
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "Animal の 第六感",
        "localizedTitles": {"en": "Animal's Sixth Sense", "zh-Hans": "动物的第六感", "ja": "アニマルの第六感"},
        "artist": "Musia",
        "description": "A Musia mixed-language ACE-Step hook about animal intuition, neon rain, city walls, forest calling, and the sixth sense.",
        "caption": "Neon rain, a forest call, and the animal instinct that points the soul forward.",
        "duration": round(duration(SELECTED_AUDIO), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "Animal の 第六感 - Fun Lazying Art",
            "description": "A Musia mixed-language sixth-sense hook with corrected lyrics, translations, chords, and guitar fingering.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "Animal の 第六感 cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": "animal-no-di-liu-gan-mixed",
                "label": "Mixed",
                "roleLabel": "Vocal",
                "role": "vocal",
                "languageCode": "mul",
                "languageLabel": "Mixed",
                "lyricSetId": "mixed-vocal",
                "src": PUBLIC_AUDIO,
                "mime": "audio/mpeg",
            },
            "alternateAudio": [],
        },
        "musical": {
            "key": "detected A minor / modal pop center",
            "bpm": 92.28515625,
            "timeSignature": "4/4",
            "chords": load_chords(),
        },
        "textTracks": [],
        "lyricSets": [
            {
                "id": "mixed-vocal",
                "label": "Mixed vocal",
                "languageCode": "mul",
                "tracks": [
                    {"code": "mul", "label": "Mixed", "nativeLabel": "Mixed", "script": "Latn+Hans+Jpan", "features": ["active-vocal", "pinyin"], "path": "lyrics/mixed-vocal/mul.json"},
                    {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn", "features": ["translation"], "path": "lyrics/mixed-vocal/en.json"},
                    {"code": "zh-Hans", "label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "features": ["pinyin", "translation"], "path": "lyrics/mixed-vocal/zh-Hans.json"},
                    {"code": "ja", "label": "Japanese", "nativeLabel": "日本語", "script": "Jpan", "features": ["furigana", "translation"], "path": "lyrics/mixed-vocal/ja.json"},
                ],
            }
        ],
        "timeline": {"unit": "seconds", "lines": timeline},
        "playback": {"defaultMode": "single"},
        "provenance": {
            "createdBy": "Musia",
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "audioSource": "ACE-Step XL Turbo zh-biased mixed-language seed 747304 selected after rejecting native-CJK, latin-hook, and SFT candidates with poor lyric recovery.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {"gate": "experimental-public", "note": "Mixed-language ACE render is publishable as an imperfect but musical mixed hook."},
            "lyricCorrection": "Full same-render ASR timing from data/runs/animal-no-di-liu-gan-mixed-seed-747304-analysis/analysis/lyrics.json plus intended lyric where sound-close.",
            "coverSource": "Image generation, 16:9 text-free cover: fox-like animal intuition between neon rain city and glowing forest.",
            "publicAudio": PUBLIC_AUDIO_NAME,
        },
        "artifacts": [
            {"label": "Analysis report", "path": str((ANALYSIS / "REPORT.md").relative_to(ROOT))},
            {"label": "Chords", "path": str((ANALYSIS / "analysis/chords.csv").relative_to(ROOT))},
            {"label": "Stems", "path": str((ANALYSIS / "stems").relative_to(ROOT))},
        ],
    }
    write_json(media_dir / "manifest.json", manifest)


def update_catalog() -> None:
    path = ROOT / "website/data/catalog.json"
    catalog = read_json(path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "Animal の 第六感",
        "artist": "Musia",
        "summary": "A mixed-language sixth-sense hook with corrected lyrics, translations, chords, and guitar fingering.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["mul", "en", "zh-Hans", "ja"],
        "tags": ["music", "multilingual", "sixth-sense", "ACE-Step", "guitar", "chords", "pinyin", "furigana"],
    }
    items = [existing for existing in catalog["items"] if existing.get("id") != MEDIA_ID]
    insert_at = 1
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
