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
MEDIA_ID = "meng-you-tian-mu-yin-liu-bie"
PROJECT = ROOT / "data/creative_projects/meng-you-tian-mu-yin-liu-bie-selected-20260706"
ANALYSIS = ROOT / "data/runs/meng-you-tian-mu-yin-liu-bie-selected-hook-741402-analysis"
SELECTED_WAV = PROJECT / "selected/meng-you-tian-mu-yin-liu-bie-zh-Hans-ace-xl-turbo-hook-seed741402.wav"
SELECTED_MP3 = PROJECT / "selected/meng-you-tian-mu-yin-liu-bie-zh-Hans-ace-xl-turbo-hook-seed741402.mp3"
PUBLIC_AUDIO_NAME = "meng-you-tian-mu-yin-liu-bie-zh-Hans-ace-xl-turbo-hook-seed741402-20260706.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/meng-you-tian-mu-16x9.png"

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
    if "天姥" in line_text and char == "姥":
        return "mu3"
    if char == "难":
        return "nan2"
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
        token = {
            "text": part,
            "start": round(start + step * index, 3),
            "end": round(start + step * (index + 1), 3),
        }
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
    # Timings come from the selected hook render's tiny ASR word anchors.
    # The active Mandarin text preserves the intended poem image only when the
    # sound is close; later prompt lines are omitted because the selected render
    # did not audibly recover them.
    return [
        (
            "l01",
            13.30,
            18.56,
            "海上烟涛，远到难求",
            "Sea mist and waves; the far path is hard to seek.",
            "海の煙る波、遠き道は求めがたい",
        ),
        (
            "l02",
            19.22,
            24.70,
            "有人说天姥山，云霞在尽头",
            "Someone speaks of Mount Tianmu; clouds glow at the horizon.",
            "人は天姥山を語り、雲霞は果てにある",
        ),
        (
            "l03",
            24.70,
            30.28,
            "我乘一夜月，飞过镜湖秋",
            "I ride one night of moonlight, flying across Mirror Lake autumn.",
            "一夜の月に乗り、鏡湖の秋を飛び越える",
        ),
        (
            "l04",
            30.82,
            36.26,
            "月光照着我，送我向山流",
            "Moonlight shines on me and sends me toward the mountain stream.",
            "月光が私を照らし、山の流れへ送る",
        ),
        (
            "l05",
            36.26,
            41.14,
            "梦游天姥山",
            "Dreaming through Mount Tianmu.",
            "天姥山を夢に遊ぶ",
        ),
        (
            "l06",
            41.14,
            43.56,
            "梦到云天外",
            "Dreaming beyond the clouded sky.",
            "雲天の外まで夢見る",
        ),
        (
            "l07",
            44.20,
            47.53,
            "万山为我开",
            "Ten thousand mountains open for me.",
            "万の山が私のために開く",
        ),
        (
            "l08",
            47.53,
            50.71,
            "我心不尘埃",
            "My heart will not become dust.",
            "我が心は塵にならない",
        ),
        (
            "l09",
            53.56,
            55.82,
            "梦游天姥山",
            "Dreaming through Mount Tianmu.",
            "天姥山を夢に遊ぶ",
        ),
        (
            "l10",
            59.56,
            61.14,
            "万山为我开",
            "Ten thousand mountains open for me.",
            "万の山が私のために開く",
        ),
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
                "Corrected from the selected ACE XL Turbo hook render, using the "
                "selected-audio tiny ASR word anchors plus the planned lyric as "
                "reference. The published lyric follows the actual audible "
                "structure: opening image, Tianmu/cloud line, moon-flight line, "
                "moonlight/stream line, and the repeated Tianmu/mountain hook. "
                "Prompt lines after the hook are omitted because this render did "
                "not recover them clearly enough for truthful publication. The "
                "public text keeps 天姥山 with pinyin mu3; the model-facing prompt "
                "used 天母山 only to control pronunciation."
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
        "title": "梦游天姥吟留别",
        "artist": "Musia",
        "summary": "A hook-focused ACE-Step Mandarin art-pop adaptation of Li Bai's dream journey to Tianmu, with corrected trilingual lyric timing and chords.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "Li Bai", "Tang poetry", "Tianmu", "Mandarin", "ACE-Step", "pinyin", "furigana"],
    }
    items = [entry for entry in catalog.get("items", []) if entry.get("id") != MEDIA_ID]
    insert_at = next((index for index, entry in enumerate(items) if entry.get("id") == "meng-you-tian-mu-original-poem"), 6)
    items.insert(insert_at, item)
    catalog["items"] = items
    write_json(catalog_path, catalog)


def write_media_item() -> None:
    ensure_audio()
    if not (ROOT / "website" / COVER).exists():
        raise FileNotFoundError(f"Missing cover: {ROOT / 'website' / COVER}")

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
        "title": "梦游天姥吟留别",
        "localizedTitles": {
            "zh-Hans": "梦游天姥吟留别",
            "en": "Dreaming of Tianmu",
            "ja": "夢遊天姥吟留別",
        },
        "artist": "Musia",
        "description": "A hook-focused Mandarin ACE-Step art-pop adaptation of Li Bai's dream journey to Mount Tianmu, with corrected trilingual lyrics, pinyin, furigana, chords, beats, and stems.",
        "caption": "Sea mist, moon flight, Tianmu, blue clouds, and ten thousand mountains opening in a dream.",
        "duration": round(duration(SELECTED_WAV), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "梦游天姥吟留别 - Fun Lazying Art",
            "description": "Musia hook-focused Mandarin song inspired by Li Bai's dream journey to Tianmu.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {
                "id": "cover",
                "label": "梦游天姥吟留别 cover",
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
                "id": "meng-you-tian-mu-yin-liu-bie-zh",
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
            "key": "D minor requested / analysis detects Dm-Bb-F centered progression",
            "bpm": 161.499,
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
        "provenance": {
            "createdBy": "Musia",
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "audioSource": "ACE-Step 1.5 XL Turbo hook-focused seed 741402.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "lyricCorrection": "Corrected from selected-audio ASR anchors and the intended lyric. The published track omits planned lines that this render skipped or garbled.",
            "coverSource": "Reused the existing text-free 16:9 dream-mountain cover at website/assets/covers/meng-you-tian-mu-16x9.png.",
            "publicAudio": PUBLIC_AUDIO_NAME,
            "pronunciation": "Model-facing prompt used 天母山 to force tian1 mu3 shan1; public lyric restores 天姥山 and pinyin marks 姥 as mu3.",
        },
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
    note = PROJECT / "WEBSITE_ITEM.md"
    note.write_text(
        "\n".join(
            [
                "# 梦游天姥吟留别 Website Item",
                "",
                "- Media id: `meng-you-tian-mu-yin-liu-bie`.",
                "- Public audio: `https://lazyingart.github.io/MusiaSongs/audio/meng-you-tian-mu-yin-liu-bie-zh-Hans-ace-xl-turbo-hook-seed741402-20260706.mp3`.",
                "- Website manifest: `website/data/songs/meng-you-tian-mu-yin-liu-bie/manifest.json`.",
                "- Active lyric source: selected audio ASR anchors plus listening/intended-lyric correction.",
                "",
                "The selected render only clearly recovers the opening and hook sections. The public website lyric therefore follows the audible render instead of publishing all planned prompt lines.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    write_media_item()
    write_note()
    print(ROOT / "website/data/songs" / MEDIA_ID / "manifest.json")


if __name__ == "__main__":
    main()
