#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pykakasi
from PIL import Image, ImageDraw
from pypinyin import Style, pinyin


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
MEDIA_ID = "wei-ji-fen"
PROJECT = ROOT / "data/creative_projects/wei-ji-fen-20260706"
SELECTED_WAV = PROJECT / "selected/wei-ji-fen-zh-ace-xl-turbo-seed760622.wav"
SELECTED_MP3 = PROJECT / "selected/wei-ji-fen-zh-ace-xl-turbo-seed760622.mp3"
ANALYSIS = ROOT / "data/runs/wei-ji-fen-zh-ace-seed760622-analysis"
PUBLIC_AUDIO_NAME = "wei-ji-fen-zh-Hans-ace-xl-turbo-seed760622-20260706.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/wei-ji-fen-16x9.png"

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
    for mark in [",", ".", "?", "!", ";", ":", "—", "'", '"']:
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
        token: dict[str, Any] = {
            "text": part,
            "start": round(start + step * index, 3),
            "end": round(start + step * (index + 1), 3),
        }
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
    # Timings come from the selected ACE XL Turbo seed 760622 large-v3 ASR on
    # the Demucs-separated vocal. Text keeps the intended lyric when ASR is
    # sound-close and the planned word is stronger: 微微琐事 over 微微松弛,
    # 转 over 穿, 角度 over 脚都, and 傅立叶变换 over the garbled ASR phrase.
    return [
        ("l01", 16.02, 19.96, "不要分开，我的心里你还在", "Don't leave; you are still in my heart", "離れないで、心にはまだ君がいる"),
        ("l02", 20.32, 23.10, "微微琐事，落进心海", "Tiny little things fall into the sea of the heart", "小さな出来事が心の海へ落ちる"),
        ("l03", 23.10, 26.26, "一点一点，把我们推开", "Bit by bit, they push us apart", "少しずつ、僕らを遠ざける"),
        ("l04", 29.02, 32.18, "你说爱还在，只是太疲惫", "You say love is still here, just too tired", "愛はまだある、ただ疲れすぎたと君は言う"),
        ("l05", 32.18, 35.10, "我说别沉默，抱紧我一回", "I say don't go silent; hold me once", "黙らないで、もう一度抱きしめてと言う"),
        ("l06", 36.52, 38.92, "会不会好点", "Would it be a little better?", "少しはよくなるかな"),
        ("l07", 40.94, 42.02, "微微，微微", "Tiny by tiny", "少しずつ、少しずつ"),
        ("l08", 42.96, 45.32, "我绕着你转", "I keep orbiting you", "君のまわりを回り続ける"),
        ("l09", 45.32, 48.30, "半径越来越远", "The radius grows farther and farther", "半径はどんどん遠くなる"),
        ("l10", 48.30, 51.18, "角度还不肯散", "The angle still refuses to scatter", "角度はまだ離れようとしない"),
        ("l11", 51.18, 52.70, "傅立叶变换", "A Fourier transform", "フーリエ変換"),
        ("l12", 52.70, 53.44, "拆开了思念", "breaks longing apart", "想いをほどいてしまう"),
        ("l13", 53.44, 57.02, "每一个频率，都喊你一遍", "Every frequency calls your name once", "すべての周波数が君を一度呼ぶ"),
        ("l14", 57.02, 57.92, "微微，微微", "Tiny by tiny", "少しずつ、少しずつ"),
        ("l15", 61.78, 67.29, "最小的痛，也会成海", "Even the smallest pain can become a sea", "いちばん小さな痛みも海になる"),
        ("l16", 69.69, 74.23, "你说爱还在，可是想分开", "You say love is still here, but you want to leave", "愛はまだある、でも離れたいと君は言う"),
        ("l17", 75.17, 79.47, "我的心里，你还在", "In my heart, you are still here", "僕の心には、まだ君がいる"),
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
                "ASR-corrected from ACE XL Turbo seed 760622. The active Mandarin "
                "track follows the actual sung structure and preserves the planned "
                "lyric only where the ASR phrase is sound-close and less musical."
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
    img = Image.new("RGB", (width, height), "#101b2f")
    draw = ImageDraw.Draw(img, "RGBA")

    top = (18, 35, 58)
    mid = (61, 83, 116)
    low = (243, 190, 159)
    for y in range(height):
        if y < height * 0.58:
            t = y / (height * 0.58)
            color = tuple(int(top[i] * (1 - t) + mid[i] * t) for i in range(3))
        else:
            t = (y - height * 0.58) / (height * 0.42)
            color = tuple(int(mid[i] * (1 - t) + low[i] * t) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)

    # Window glow and rain-streaked glass.
    draw.rounded_rectangle((130, 90, 1470, 760), radius=32, fill=(255, 255, 255, 22), outline=(255, 255, 255, 55), width=2)
    for x in range(160, 1450, 72):
        alpha = 22 + (x % 5) * 6
        draw.line((x, 100, x - 62, 760), fill=(255, 255, 255, alpha), width=2)

    # Calculus curves as luminous traces, no readable text.
    curve_color = (145, 229, 255, 150)
    points = []
    for i in range(0, 1120):
        x = 240 + i
        y = 435 + int(96 * __import__("math").sin(i / 88) + 34 * __import__("math").sin(i / 23))
        points.append((x, y))
    draw.line(points, fill=curve_color, width=5)
    points2 = []
    for i in range(0, 980):
        x = 310 + i
        y = 325 + int(70 * __import__("math").cos(i / 77))
        points2.append((x, y))
    draw.line(points2, fill=(255, 196, 218, 115), width=4)

    # Two separated silhouettes.
    for x, y, scale, alpha in [(630, 650, 1.0, 235), (930, 650, 0.96, 220)]:
        draw.ellipse((x - 21 * scale, y - 102 * scale, x + 21 * scale, y - 60 * scale), fill=(11, 18, 32, alpha))
        draw.rounded_rectangle((x - 18 * scale, y - 62 * scale, x + 18 * scale, y + 38 * scale), radius=14, fill=(11, 18, 32, alpha))
        draw.line((x - 6 * scale, y + 36 * scale, x - 28 * scale, y + 88 * scale), fill=(11, 18, 32, alpha), width=int(8 * scale))
        draw.line((x + 6 * scale, y + 36 * scale, x + 28 * scale, y + 88 * scale), fill=(11, 18, 32, alpha), width=int(8 * scale))
        draw.ellipse((x - 62, y + 88, x + 62, y + 104), fill=(11, 18, 32, 42))

    # Soft particles like accumulated small things.
    for i in range(150):
        x = (i * 137) % width
        y = 120 + ((i * 89) % 620)
        r = 1 + (i % 3)
        draw.ellipse((x, y, x + r, y + r), fill=(255, 232, 185, 46 + (i % 4) * 15))

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
        "title": "微积分",
        "artist": "Musia",
        "summary": "A Mandarin breakup ballad where tiny accumulated hurts become calculus, orbit, frequency, and distance.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "Mandarin", "breakup", "calculus", "ACE-Step", "pinyin", "furigana"],
    }
    catalog["items"] = [entry for entry in catalog.get("items", []) if entry.get("id") != MEDIA_ID]
    catalog["items"].insert(0, item)
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
        "title": "微积分",
        "localizedTitles": {
            "zh-Hans": "微积分",
            "en": "Calculus of Us",
            "ja": "微積分の恋",
        },
        "artist": "Musia",
        "description": "A Mandarin ACE-Step breakup ballad with ASR-corrected trilingual lyrics, pinyin, furigana, chords, stems, and beats.",
        "caption": "Tiny everyday hurts accumulate into distance: calculus, orbit, frequency, and a love that still does not want to leave.",
        "duration": round(duration(SELECTED_WAV), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "provenance": {
            "audio": "ACE-Step 1.5 XL Turbo hook-first seed 760622, selected after balanced and compact sweeps.",
            "lyrics": "ASR/STT-corrected Chinese active track; sound-close planned words are preserved where they are more musical and semantically central.",
            "cover": "Generated by scripts/prepare_wei_ji_fen_fun_item.py as a text-free 16:9 calculus breakup cover.",
        },
        "share": {
            "title": "微积分 - Fun Lazying Art",
            "description": "Musia Mandarin calculus breakup ballad.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {
                "id": "cover",
                "label": "微积分 cover",
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
                "id": "wei-ji-fen-zh",
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
            "key": "E minor requested / analysis detects C-Am-G pop movement",
            "bpm": 152.0,
            "timeSignature": "4/4",
            "chords": load_chords(),
        },
        "timeline": {"unit": "seconds", "lines": timeline},
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
                "# 微积分 Selected Version",
                "",
                "- Selected route: ACE-Step 1.5 XL Turbo, hook-first pass.",
                "- Selected seed: `760622`.",
                "- Selected WAV: `selected/wei-ji-fen-zh-ace-xl-turbo-seed760622.wav`.",
                "- Selected MP3: `selected/wei-ji-fen-zh-ace-xl-turbo-seed760622.mp3`.",
                "- Analysis run: `data/runs/wei-ji-fen-zh-ace-seed760622-analysis`.",
                f"- Public audio: `{PUBLIC_AUDIO}`.",
                "",
                "## Lyric Correction",
                "",
                "The balanced and compact ACE sweeps had healthy levels but weak lyric recovery beyond the opening. The selected hook-first render recovers the chorus, tiny-accumulation verse, math bridge, and final breakup line. Public lyrics are corrected against large-v3 ASR from the selected render and preserve planned words only when the sound is close and the planned word is more musical.",
                "",
                "Main public lyric decisions:",
                "",
                "- Keep `微微琐事` over ASR `微微松弛` because the sound is close and it is the song's central image.",
                "- Keep `我绕着你转` over ASR `我绕着你穿`.",
                "- Keep `角度还不肯散` over ASR `脚都还不肯散`.",
                "- Publish `傅立叶变换 / 拆开了思念` over the garbled ASR bridge because the syllable structure and sound are close enough and the intended math image is clearer.",
                "- Omit unsupported planned lines such as `微积分那么难` and `二重积分好奇怪` from the public active track because this selected render did not clearly sing them.",
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
