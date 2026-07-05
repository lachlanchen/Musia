#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw
from pypinyin import Style, pinyin
import pykakasi


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
MEDIA_ID = "sha-sha"
PROJECT = ROOT / "data/creative_projects/sha-sha-20260705"
SELECTED_MP3 = PROJECT / "selected/sha-sha-zh-ace-xl-turbo-seed750531.mp3"
SELECTED_WAV = PROJECT / "selected/sha-sha-zh-ace-xl-turbo-seed750531.wav"
ANALYSIS = ROOT / "data/runs/sha-sha-f641-balanced-analysis"
PUBLIC_AUDIO_NAME = "sha-sha-zh-Hans-ace-xl-turbo-seed750531-20260705.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/sha-sha-16x9.png"


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


def zh_pinyin_for(char: str) -> str:
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
            reading = zh_pinyin_for(part)
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
    # ACE XL Turbo seed 750531 render. Text preserves the prompt lyric when the
    # sound is close and more beautiful; it follows ASR when the model clearly
    # repeated, skipped, or restructured a phrase.
    return [
        ("l01", 12.11, 17.07, "沙沙，沙沙，大海的沙", "Sha sha, sha sha, the sand of the sea", "さらさら、さらさら、海の砂"),
        ("l02", 18.03, 24.35, "沙漠的沙，沙漠的沙，数不尽它", "Desert sand, desert sand, too many grains to count", "砂漠の砂、砂漠の砂、数えきれない"),
        ("l03", 25.25, 30.19, "你牵着我，沿着浪花", "You hold my hand along the waves", "君が手を取り、波のそばを歩く"),
        (
            "l04",
            30.19,
            40.81,
            "风吹到千叶海边，轻指楼兰姑娘面庞",
            "The wind blows from Chiba's shore and brushes Loulan's girl's face",
            "千葉の海辺から風が吹き、楼蘭の少女の頬に触れる",
        ),
        ("l05", 40.81, 44.05, "你笑着说，世界很大", "You smile and say the world is wide", "君は笑って言う、世界は広いね"),
        ("l06", 44.05, 48.41, "可此刻只装得下，我们俩", "But this moment only holds the two of us", "でも今は、僕ら二人だけで満ちている"),
        ("l07", 55.99, 58.47, "夕阳落在肩上", "Sunset rests on our shoulders", "夕日が肩に落ちる"),
        ("l08", 58.47, 64.57, "沙沙，沙沙，海浪说悄悄话", "Sha sha, sha sha, the waves whisper", "さらさら、さらさら、波が内緒話をする"),
        ("l09", 64.57, 70.37, "沙沙，沙沙，太阳慢慢落下", "Sha sha, sha sha, the sun slowly goes down", "さらさら、さらさら、太陽がゆっくり沈む"),
    ]


def make_tracks() -> dict[str, list[dict[str, Any]]]:
    tracks: dict[str, list[dict[str, Any]]] = {"zh-Hans": [], "en": [], "ja": []}
    for line_id, start, end, zh, en, ja in corrected_rows():
        tracks["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans"))
        tracks["en"].append(make_line(line_id, start, end, en, "en"))
        tracks["ja"].append(make_line(line_id, start, end, ja, "ja"))
    return tracks


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
                "ASR/listening-corrected from ACE XL Turbo seed 750531. "
                "The prompt was treated as intent, while the active lyric follows "
                "the actual sung structure. Sound-close ASR substitutions such as "
                "傻傻->沙沙, 到海->大海, 入不尽->数不尽, 楼栏->楼兰 were restored "
                "to the more beautiful planned text."
            ),
        },
    }


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


def make_cover(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), "#f8d7a4")
    px = img.load()
    sky_top = (114, 169, 213)
    sky_low = (252, 185, 117)
    sea_top = (62, 146, 174)
    sea_low = (248, 199, 138)
    sand = (216, 173, 116)
    for y in range(height):
        if y < 440:
            t = y / 440
            color = tuple(int(sky_top[i] * (1 - t) + sky_low[i] * t) for i in range(3))
        elif y < 650:
            t = (y - 440) / 210
            color = tuple(int(sea_top[i] * (1 - t) + sea_low[i] * t) for i in range(3))
        else:
            t = (y - 650) / 250
            color = tuple(int(sea_low[i] * (1 - t) + sand[i] * t) for i in range(3))
        for x in range(width):
            px[x, y] = color

    draw = ImageDraw.Draw(img, "RGBA")
    sun_x, sun_y, sun_r = 1130, 350, 92
    for r in range(170, 20, -8):
        alpha = max(4, int(50 * (1 - r / 170)))
        draw.ellipse((sun_x - r, sun_y - r, sun_x + r, sun_y + r), fill=(255, 219, 142, alpha))
    draw.ellipse((sun_x - sun_r, sun_y - sun_r, sun_x + sun_r, sun_y + sun_r), fill=(255, 220, 139, 235))

    for offset, alpha in [(0, 70), (36, 45), (74, 28), (120, 20)]:
        y = 522 + offset
        draw.arc((-180, y - 150, 1780, y + 170), 5, 175, fill=(255, 255, 255, alpha), width=7)

    # Subtle desert mirage on the far horizon.
    draw.polygon([(0, 470), (210, 428), (420, 468), (650, 420), (900, 470), (0, 470)], fill=(234, 192, 133, 74))
    draw.polygon([(740, 470), (980, 430), (1240, 470), (1600, 430), (1600, 470)], fill=(221, 170, 112, 68))

    # Two small walking silhouettes and reflection shadows.
    for x, scale in [(735, 1.0), (785, 0.92)]:
        y = 680
        draw.ellipse((x - 11 * scale, y - 58 * scale, x + 11 * scale, y - 36 * scale), fill=(47, 55, 65, 230))
        draw.line((x, y - 36 * scale, x - 7 * scale, y + 16 * scale), fill=(47, 55, 65, 230), width=int(8 * scale))
        draw.line((x - 6 * scale, y + 14 * scale, x - 26 * scale, y + 50 * scale), fill=(47, 55, 65, 220), width=int(6 * scale))
        draw.line((x - 4 * scale, y + 14 * scale, x + 16 * scale, y + 50 * scale), fill=(47, 55, 65, 220), width=int(6 * scale))
        draw.line((x - 5 * scale, y - 14 * scale, x - 28 * scale, y + 5 * scale), fill=(47, 55, 65, 210), width=int(5 * scale))
        draw.ellipse((x - 38, y + 54, x + 52, y + 66), fill=(55, 48, 41, 38))

    # Fine sand sparkle.
    for i in range(130):
        x = (i * 137) % width
        y = 665 + ((i * 53) % 190)
        alpha = 28 + (i % 5) * 10
        draw.ellipse((x, y, x + 2, y + 2), fill=(255, 243, 190, alpha))

    img.save(path)


def ensure_audio() -> None:
    if not SELECTED_MP3.exists():
        raise FileNotFoundError(f"Missing selected MP3: {SELECTED_MP3}")
    target = SONGS / "audio" / PUBLIC_AUDIO_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SELECTED_MP3, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def update_catalog() -> None:
    catalog_path = ROOT / "website/data/catalog.json"
    catalog = read_json(catalog_path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "沙沙",
        "artist": "Musia",
        "summary": "A soft Mandarin beach-sunset song about sea sand, desert sand, Chiba wind, Loulan dream, and two people walking home.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "Mandarin", "beach", "sunset", "ACE-Step", "pinyin", "furigana"],
    }
    catalog["items"] = [entry for entry in catalog.get("items", []) if entry.get("id") != MEDIA_ID]
    insert_at = 0
    # Keep the current default song first; add this new song right after the
    # first few headline items.
    catalog["items"].insert(insert_at, item)
    write_json(catalog_path, catalog)


def write_media_item() -> None:
    ensure_audio()
    cover_path = ROOT / "website" / COVER
    make_cover(cover_path)

    media_dir = ROOT / "website/data/songs" / MEDIA_ID
    tracks = make_tracks()
    for code, lines in tracks.items():
        write_json(media_dir / "lyrics/zh-vocal" / f"{code}.json", track(code, lines))

    timeline = [{"id": line["id"], "start": line["start"], "end": line["end"], "text": line["text"]} for line in tracks["zh-Hans"]]
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "沙沙",
        "localizedTitles": {
            "zh-Hans": "沙沙",
            "en": "Sha Sha",
            "ja": "さらさら",
        },
        "artist": "Musia",
        "description": "A soft Mandarin ACE-Step beach-sunset ballad with ASR-audited trilingual lyrics, pinyin, furigana, chords, stems, and beats.",
        "caption": "Sea sand, desert sand, Chiba sea wind, Loulan dream, and two people watching the sun by the waves.",
        "duration": round(duration(SELECTED_WAV), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "沙沙 - Fun Lazying Art",
            "description": "Musia soft Mandarin beach-sunset song.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {
                "id": "cover",
                "label": "沙沙 cover",
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
                "id": "sha-sha-zh",
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
            "key": "F major requested / analysis detects A-minor-centered pop progression",
            "bpm": 161.5,
            "timeSignature": "4/4",
            "chords": load_chords(),
        },
        "timeline": {"lines": timeline},
        "textTracks": [],
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
        "artifacts": {
            "project": str(PROJECT.relative_to(ROOT)),
            "selectedWav": str(SELECTED_WAV.relative_to(ROOT)),
            "selectedMp3": str(SELECTED_MP3.relative_to(ROOT)),
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "stems": {
                "vocals": str((ANALYSIS / "stems/vocals.wav").relative_to(ROOT)),
                "drums": str((ANALYSIS / "stems/drums.wav").relative_to(ROOT)),
                "bass": str((ANALYSIS / "stems/bass.wav").relative_to(ROOT)),
                "other": str((ANALYSIS / "stems/other.wav").relative_to(ROOT)),
                "instrumental": str((ANALYSIS / "stems/instrumental.wav").relative_to(ROOT)),
            },
            "beats": str((ANALYSIS / "analysis/beats.csv").relative_to(ROOT)),
            "chords": str((ANALYSIS / "analysis/chords.csv").relative_to(ROOT)),
            "asr": str((ANALYSIS / "analysis/lyrics.json").relative_to(ROOT)),
        },
    }
    write_json(media_dir / "manifest.json", manifest)
    update_catalog()


def write_note() -> None:
    note = PROJECT / "SELECTED_VERSION.md"
    note.write_text(
        "\n".join(
            [
                "# 沙沙 Selected Version",
                "",
                "- Selected route: ACE-Step 1.5 XL Turbo, front-vocal balanced pass.",
                "- Selected seed: `750531`.",
                "- Selected WAV: `selected/sha-sha-zh-ace-xl-turbo-seed750531.wav`.",
                "- Selected MP3: `selected/sha-sha-zh-ace-xl-turbo-seed750531.mp3`.",
                "- Analysis run: `data/runs/sha-sha-f641-balanced-analysis`.",
                "- Public audio: `https://lazyingart.github.io/MusiaSongs/audio/sha-sha-zh-Hans-ace-xl-turbo-seed750531-20260705.mp3`.",
                "",
                "## Lyric Correction",
                "",
                "The first long Turbo sweep, the compact sweep, and SFT pass were rejected or treated as weaker because ASR recovered too little lyric or unrelated text. The selected render recovers the core beach-song structure. Public lyrics are corrected against Demucs-separated vocal ASR and preserve the planned lyric only for sound-close substitutions.",
                "",
                "Main public lyric changes:",
                "",
                "- Keep `沙沙` instead of ASR `傻傻` because the sound is close and `沙沙` is the title/hook.",
                "- Keep `大海的沙` instead of ASR `到海的沙`.",
                "- Follow audio repetition: `沙漠的沙，沙漠的沙，数不尽它` instead of the planned `好多的沙` line.",
                "- Keep `轻指楼兰姑娘面庞` instead of ASR `倾着楼栏姑娘面旁` because the sound is close and the planned phrase is more beautiful.",
                "- Omitted planned lines that were not recovered by ASR/listening evidence are not shown on the public website lyric track.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    write_media_item()
    write_note()
    print(ROOT / f"website/data/songs/{MEDIA_ID}/manifest.json")


if __name__ == "__main__":
    main()
