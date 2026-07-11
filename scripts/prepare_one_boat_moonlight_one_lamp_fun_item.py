#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pykakasi
from PIL import Image, ImageDraw, ImageFilter
from pypinyin import Style, pinyin


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
MEDIA_ID = "one-boat-moonlight-one-lamp"
PROJECT = ROOT / "data/creative_projects/one-boat-moonlight-one-lamp-20260711"
SELECTED_AUDIO = PROJECT / "selected/one-boat-moonlight-one-lamp-ace-xl-turbo-seed780826.mp3"
ANALYSIS = ROOT / "data/runs/one-boat-moonlight-one-lamp-20260711-analysis"
PUBLIC_AUDIO_NAME = "one-boat-moonlight-one-lamp-ace-xl-turbo-seed780826-20260711.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/one-boat-moonlight-one-lamp-16x9.png"
SELECTED_COVER_SOURCE = ROOT / "website/assets/cover-candidates/one-boat-megastructure-cover-candidate-20260711.png"

KAKASI = pykakasi.kakasi()


LANG = {
    "mul": {"code": "mul", "label": "Mixed", "nativeLabel": "Mixed", "script": "Latn"},
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


def has_kana(text: str) -> bool:
    return any("\u3040" <= char <= "\u30ff" for char in text)


def zh_pinyin(char: str) -> str:
    if not is_cjk(char):
        return ""
    values = pinyin(char, style=Style.TONE3, strict=False, neutral_tone_with_five=True)
    return values[0][0] if values and values[0] else ""


def ja_reading(text: str) -> str:
    if not (is_cjk(text) or has_kana(text)):
        return ""
    converted = KAKASI.convert(text)
    hira = "".join(item.get("hira") or item.get("orig") or "" for item in converted)
    return hira if hira and hira != text else ""


def split_en(text: str) -> list[str]:
    spaced = text
    for mark in [",", ".", "?", "!", ";", ":", "—"]:
        spaced = spaced.replace(mark, f" {mark} ")
    return [part for part in spaced.split() if part]


def split_ja(text: str) -> list[str]:
    parts: list[str] = []
    for item in KAKASI.convert(text):
        orig = item.get("orig") or ""
        if not orig or orig.isspace():
            continue
        if all(ord(char) < 128 for char in orig):
            parts.extend(split_en(orig))
        else:
            parts.append(orig)
    return parts


def split_visible(text: str, code: str) -> list[str]:
    if code in {"en", "mul"}:
        return split_en(text)
    if code == "ja":
        return split_ja(text)
    return [char for char in text if not char.isspace() and char not in "，。！？、；："]


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


def corrected_rows() -> list[tuple[str, float, float, str, str, str, str]]:
    """ASR/listening correction for selected ACE XL Turbo seed 780826.

    Evidence:
    - full mix small ASR from `run_pipeline.py`;
    - large-v3 full mix and separated vocal stem ASR, no VAD;
    - planned phonetic hook lyric and source poem pronunciation guide.

    The render does not sing every planned line. Public lyrics include only
    sound-supported sung lines. Original Chinese poem lines are preserved in
    the `zh-Hans` companion track where the active pinyin line is sound-close;
    no modern Chinese paraphrase is used for the Chinese track.
    """

    return [
        ("l01", 6.10, 11.90, "When love shines across the sea", "When love shines across the sea.", "海を越えて愛が光る", "惟怜一灯影，万里眼中明"),
        ("l02", 13.88, 16.95, "Shang guo sui yuan zhu", "You stayed in the great land by fate.", "上国に縁のまま住む", "上国随缘住"),
        ("l03", 17.00, 20.08, "Lai tu ruo meng xing", "The road here was like a dream.", "来た道は夢のよう", "来途若梦行"),
        ("l04", 20.08, 23.80, "Fu tian cang hai yuan", "The vast sea floats beneath the sky.", "天に浮かぶ蒼い海は遠い", "浮天沧海远"),
        ("l05", 23.80, 26.56, "Fa zhou qing", "The Dharma boat is light.", "法の舟は軽い", "去世法舟轻"),
        ("l06", 26.56, 30.62, "Shui yue tong chan ji", "Water and moon open into Zen silence.", "水の月は禅の静けさへ通じる", "水月通禅寂"),
        ("l07", 30.62, 32.98, "Moon in the water", "Moon in the water.", "水に映る月", "水月通禅寂"),
        ("l08", 33.66, 36.86, "Yu long ting fan sheng", "Fish and dragons hear the sacred chant.", "魚も龍も梵の声を聞く", "鱼龙听梵声"),
        ("l09", 36.86, 40.46, "Haruka Haruka", "Far away, far away.", "はるか、はるか", "扶桑已在渺茫中"),
        ("l10", 40.46, 44.38, "Wei lian yi deng ying", "Only that one lamp-shadow remains dear.", "ただ一つの灯影を惜しむ", "惟怜一灯影"),
        ("l11", 44.38, 47.76, "Wan li yan zhong ming", "Across ten thousand miles it stays bright in the eyes.", "万里の彼方にも目の中で明るい", "万里眼中明"),
        ("l12", 48.44, 51.10, "Fu sang miao mang zhong", "Fusang is already in the haze.", "扶桑は渺茫の中", "扶桑已在渺茫中"),
        ("l13", 51.10, 54.96, "Higashi no higashi e", "Toward the east beyond the east.", "東のさらに東へ", "家在扶桑东更东"),
        ("l14", 68.46, 71.02, "Haruka umi e", "To the far sea.", "遥か海へ", "一船明月一帆风"),
    ]


def build_tracks() -> dict[str, list[dict[str, Any]]]:
    tracks = {"mul": [], "en": [], "ja": [], "zh-Hans": []}
    for row in corrected_rows():
        line_id, start, end, active, en, ja, zh = row
        tracks["mul"].append(make_line(line_id, start, end, active, "mul"))
        tracks["en"].append(make_line(line_id, start, end, en, "en"))
        tracks["ja"].append(make_line(line_id, start, end, ja, "ja"))
        tracks["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans"))
    return tracks


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
    if not SELECTED_AUDIO.exists():
        raise FileNotFoundError(SELECTED_AUDIO)
    target = SONGS / "audio" / PUBLIC_AUDIO_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SELECTED_AUDIO, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def make_cover() -> None:
    target = ROOT / "website" / COVER
    target.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1600, 900
    if SELECTED_COVER_SOURCE.exists():
        source = Image.open(SELECTED_COVER_SOURCE).convert("RGB")
        source_ratio = source.width / source.height
        target_ratio = width / height
        if source_ratio > target_ratio:
            new_width = int(source.height * target_ratio)
            left = (source.width - new_width) // 2
            source = source.crop((left, 0, left + new_width, source.height))
        elif source_ratio < target_ratio:
            new_height = int(source.width / target_ratio)
            top = (source.height - new_height) // 2
            source = source.crop((0, top, source.width, top + new_height))
        source = source.resize((width, height), Image.Resampling.LANCZOS)
        source.save(target, "PNG")
        return

    image = Image.new("RGB", (width, height), "#081527")
    pix = image.load()
    for y in range(height):
        for x in range(width):
            t = y / height
            glow = max(0.0, 1.0 - math.hypot((x - 1210) / 680, (y - 210) / 460))
            r = int(8 + 28 * (1 - t) + 62 * glow)
            g = int(20 + 40 * (1 - t) + 58 * glow)
            b = int(39 + 82 * (1 - t) + 76 * glow)
            pix[x, y] = (r, g, b)

    draw = ImageDraw.Draw(image, "RGBA")
    # Moon and reflection.
    draw.ellipse((1135, 95, 1315, 275), fill=(245, 236, 196, 230))
    draw.ellipse((1185, 65, 1345, 235), fill=(18, 38, 62, 210))
    for i in range(22):
        y = 370 + i * 18
        alpha = max(8, 84 - i * 3)
        draw.rounded_rectangle((980 - i * 9, y, 1370 + i * 3, y + 4), radius=2, fill=(225, 212, 164, alpha))

    # Mountain horizon.
    mountains = [(0, 450), (180, 330), (320, 420), (520, 260), (730, 440), (900, 315), (1110, 430), (1320, 300), (1600, 455), (1600, 900), (0, 900)]
    draw.polygon(mountains, fill=(8, 23, 38, 210))
    draw.polygon([(0, 520), (260, 430), (460, 540), (760, 390), (980, 535), (1260, 420), (1600, 540), (1600, 900), (0, 900)], fill=(6, 18, 30, 230))

    # Sea layers.
    for i in range(34):
        y = 500 + i * 10
        alpha = 36 if i % 3 == 0 else 18
        draw.line((0, y, width, y + math.sin(i) * 5), fill=(110, 160, 190, alpha), width=2)

    # Boat and lamp.
    draw.polygon([(520, 615), (760, 650), (895, 620), (840, 690), (600, 700)], fill=(11, 11, 15, 235))
    draw.line((720, 610, 720, 445), fill=(18, 18, 22, 230), width=5)
    draw.polygon([(725, 450), (725, 610), (835, 590)], fill=(217, 225, 214, 42))
    draw.ellipse((688, 568, 728, 608), fill=(248, 185, 89, 230))
    lamp = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    lamp_draw = ImageDraw.Draw(lamp, "RGBA")
    for radius, alpha in [(120, 24), (72, 44), (34, 88)]:
        lamp_draw.ellipse((708 - radius, 588 - radius, 708 + radius, 588 + radius), fill=(255, 184, 80, alpha))
    image = Image.alpha_composite(image.convert("RGBA"), lamp.filter(ImageFilter.GaussianBlur(16))).convert("RGB")

    image.save(target, "PNG")


def write_tracks(tracks: dict[str, list[dict[str, Any]]]) -> None:
    base = ROOT / "website/data/songs" / MEDIA_ID / "lyrics/mixed-vocal"
    for code, lines in tracks.items():
        write_json(
            base / f"{code}.json",
            {
                "schema": "fun.lazying.media.text-track.v1",
                "version": 1,
                "mediaId": MEDIA_ID,
                "language": LANG[code],
                "lines": lines,
                "provenance": {
                    "vocalSet": "mixed-vocal",
                    "correction": (
                        "Corrected from selected ACE XL Turbo seed 780826 using full-render small ASR, "
                        "large-v3 full-mix ASR, large-v3 separated-vocal ASR without VAD, and the planned "
                        "phonetic hook lyric. Lines not audibly recovered are omitted."
                    ),
                },
            },
        )


def write_manifest(tracks: dict[str, list[dict[str, Any]]]) -> None:
    dur = duration(SELECTED_AUDIO)
    chords = load_chords()
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "一船明月一灯影 · One Boat of Moonlight",
        "localizedTitles": {
            "zh-Hans": "一船明月一灯影",
            "en": "One Boat of Moonlight",
            "ja": "一船の明月、一つの灯影",
        },
        "artist": "Musia",
        "description": "A mixed English, Japanese romaji, and Mandarin pinyin ocean farewell ballad from two Tang poems about a Japanese monk returning east.",
        "caption": "One lamp in the eyes, one boat of moonlight, and one sail of wind returning toward Fusang.",
        "duration": round(dur, 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "一船明月一灯影 · One Boat of Moonlight - Fun Lazying Art",
            "description": "A Musia mixed-language Tang farewell song with corrected synced lyrics, original Chinese poem anchors, translations, pinyin, furigana, and chords.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "Moonlit sea cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": MEDIA_ID,
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
            "key": "D minor planned / detected F major centered with Dm-Bb colors",
            "bpm": 143.555,
            "timeSignature": "4/4",
            "chords": chords,
        },
        "lyricSets": [
            {
                "id": "mixed-vocal",
                "label": "Mixed vocal",
                "languageCode": "mul",
                "tracks": [
                    {"code": "mul", "label": "Mixed", "nativeLabel": "Mixed", "script": "Latn", "features": ["active-vocal"], "path": "lyrics/mixed-vocal/mul.json"},
                    {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn", "features": ["translation"], "path": "lyrics/mixed-vocal/en.json"},
                    {"code": "ja", "label": "Japanese", "nativeLabel": "日本語", "script": "Jpan", "features": ["furigana", "translation"], "path": "lyrics/mixed-vocal/ja.json"},
                    {"code": "zh-Hans", "label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "features": ["pinyin", "translation"], "path": "lyrics/mixed-vocal/zh-Hans.json"},
                ],
            }
        ],
        "textTracks": [
            {"code": "mul", "label": "Mixed", "path": "lyrics/mixed-vocal/mul.json", "default": True},
            {"code": "en", "label": "English", "path": "lyrics/mixed-vocal/en.json"},
            {"code": "ja", "label": "日本語", "path": "lyrics/mixed-vocal/ja.json"},
            {"code": "zh-Hans", "label": "中文", "path": "lyrics/mixed-vocal/zh-Hans.json"},
        ],
        "timeline": {
            "lines": tracks["mul"],
            "chords": chords,
        },
        "provenance": {
            "generator": "ACE-Step 1.5 XL Turbo",
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "selectedSeed": 780826,
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "publicAudio": PUBLIC_AUDIO_NAME,
            "coverSource": str(SELECTED_COVER_SOURCE.relative_to(ROOT)),
            "coverPrompt": (
                "Moonlit ocean, tiny boat with one warm golden lamp, and an immense graceful "
                "ring-gate/lighthouse-city megastructure rising from the water; vast, elegant, "
                "emotional, cover-ready, no text."
            ),
            "correctionPolicy": "Actual audible structure > close intended lyric > ASR guess > translation draft.",
        },
        "artifacts": [
            {"label": "Analysis report", "path": str((ANALYSIS / "REPORT.md").relative_to(ROOT))},
            {"label": "Chords CSV", "path": str((ANALYSIS / "analysis/chords.csv").relative_to(ROOT))},
            {"label": "Beats CSV", "path": str((ANALYSIS / "analysis/beats.csv").relative_to(ROOT))},
            {"label": "Stems", "path": str((ANALYSIS / "stems").relative_to(ROOT))},
        ],
    }
    write_json(ROOT / "website/data/songs" / MEDIA_ID / "manifest.json", manifest)


def update_catalog() -> None:
    path = ROOT / "website/data/catalog.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "一船明月一灯影 · One Boat of Moonlight",
        "artist": "Musia",
        "summary": "A mixed English, Japanese romaji, and Mandarin pinyin Tang ocean farewell ballad about one lamp, one boat of moonlight, and a Japanese monk returning east.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["mul", "en", "zh-Hans", "ja"],
        "tags": ["music", "multilingual", "Tang poetry", "farewell", "ocean", "ACE-Step", "pinyin", "furigana", "chords"],
    }
    items = [existing for existing in catalog["items"] if existing.get("id") != MEDIA_ID]
    items.insert(0, item)
    catalog["items"] = items
    write_json(path, catalog)


def main() -> None:
    ensure_audio()
    make_cover()
    tracks = build_tracks()
    write_tracks(tracks)
    write_manifest(tracks)
    update_catalog()
    print(ROOT / "website/data/songs" / MEDIA_ID / "manifest.json")


if __name__ == "__main__":
    main()
