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
MEDIA_ID = "kagirohi-to-hana"
PROJECT = ROOT / "data/creative_projects/kagirohi-to-hana-20260701"
SELECTED_WAV = PROJECT / "selected/kagirohi-to-hana-ja-ace-20260701.wav"
ANALYSIS = ROOT / "data/runs/kagirohi-to-hana-20260701-selected-analysis"
PUBLIC_AUDIO_NAME = "kagirohi-to-hana-ja-ace-20260701.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/kagirohi-to-hana-16x9.png"
COVER_SOURCE = Path(
    "/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/"
    "ig_089711b3c858c776016a44c117ebfc819184691047b01ca2b7.png"
)

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

JA_READING_OVERRIDES = {
    "東": "ひむがし",
    "野": "の",
    "立": "た",
    "見": "み",
    "月": "つき",
    "茜": "あかね",
    "紫": "むらさき",
    "標": "しめ",
    "行": "ゆ",
    "君": "きみ",
    "袖": "そで",
    "吾": "あ",
    "恋": "こ",
    "簾": "すだれ",
    "動": "うご",
    "秋": "あき",
    "風": "かぜ",
    "吹": "ふ",
    "久": "ひさ",
    "方": "かた",
    "光": "ひかり",
    "春": "はる",
    "日": "ひ",
    "心": "こころ",
    "花": "はな",
    "散": "ち",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ffprobe_duration(path: Path) -> float:
    return float(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)],
            text=True,
        ).strip()
    )


def image_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return image.width, image.height
    except Exception:
        return 1536, 864


def is_cjk(text: str) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in text)


def zh_pinyin(char: str) -> str:
    if not is_cjk(char):
        return ""
    values = pinyin(char, style=Style.TONE3, strict=False, neutral_tone_with_five=True)
    return values[0][0] if values and values[0] else ""


def ja_reading(text: str) -> str:
    if text in JA_READING_OVERRIDES:
        return JA_READING_OVERRIDES[text]
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
        token: dict[str, Any] = {
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
    line: dict[str, Any] = {
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
    # Selected render: XL Turbo short-kana seed 741214. The website lyric is
    # source-sensitive: preserve the original waka line when ASR and timing are
    # sound-close; omit planned lines that are not represented in the selected
    # audio. This avoids turning the page into a planned-lyrics fiction.
    return [
        ("l01", 0.34, 3.54, "東の野に", "In the eastern field", "东方原野"),
        ("l02", 3.54, 7.66, "かぎろひの立つ見えて", "I see the dawn glow rise", "晨曦升起"),
        ("l03", 7.66, 10.90, "かへり見すれば", "When I look back", "回首望去"),
        ("l04", 10.90, 13.72, "あかねさす", "Madder-red light", "茜色映照"),
        ("l05", 13.72, 16.36, "紫野行き", "Through the purple fields", "行过紫野"),
        ("l06", 16.84, 19.24, "標野行き", "Through the marked fields", "行过标野"),
        ("l07", 19.72, 22.26, "君が袖振る", "You wave your sleeve", "你挥动衣袖"),
        ("l08", 23.28, 25.50, "君待つと", "Waiting for you", "我等待着你"),
        ("l09", 25.58, 28.36, "吾が恋ひをれば", "As I remain in longing", "在恋慕中停留"),
        ("l10", 28.44, 31.10, "簾動かし", "The blind stirs", "帘子轻轻摇动"),
        ("l11", 31.30, 34.16, "秋の風吹く", "Autumn wind blows", "秋风吹来"),
        ("l12", 35.26, 36.98, "久方の", "From the far bright sky", "久远天光"),
        ("l13", 36.98, 40.30, "光のどけき", "The light is so calm", "光影如此安宁"),
        ("l14", 40.30, 43.06, "久方の", "From the far bright sky", "久远天光"),
        ("l15", 43.06, 45.26, "光のどけき", "The light is so calm", "光影如此安宁"),
        ("l16", 46.42, 48.82, "春の日に", "On this spring day", "春日里"),
        ("l17", 48.98, 51.24, "しづ心なく", "My heart cannot be still", "心不能静"),
        ("l18", 51.24, 53.76, "花の散るらむ", "Why do blossoms fall?", "花为何散落"),
    ]


def build_tracks() -> dict[str, list[dict[str, Any]]]:
    lines = {"ja": [], "zh-Hans": [], "en": []}
    for line_id, start, end, ja, en, zh in corrected_rows():
        lines["ja"].append(make_line(line_id, start, end, ja, "ja"))
        lines["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans"))
        lines["en"].append(make_line(line_id, start, end, en, "en"))
    return lines


def track(code: str, lines: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "fun.lazying.media.text-track.v1",
        "version": 1,
        "mediaId": MEDIA_ID,
        "language": LANG[code],
        "lines": lines,
        "provenance": {
            "vocalSet": "ja-vocal",
            "correction": (
                "Selected Japanese ACE-Step render corrected with large-v3 ASR on the full mix, "
                "large-v3 ASR on separated vocals, planned kana lyrics, and the source waka text. "
                "Original text is preserved where sound and phrase length are close; planned lines not "
                "actually recovered in the selected audio are omitted from the public timing track."
            ),
        },
    }


def load_chords() -> list[dict[str, Any]]:
    raw_path = ANALYSIS / "analysis/chords.json"
    if raw_path.exists():
        raw = read_json(raw_path).get("chords", [])
        return [
            {
                "start": round(float(item["start"]), 3),
                "end": round(float(item["end"]), 3),
                "name": item.get("chord") or item.get("name") or "N.C.",
                "degree": "",
            }
            for item in raw
        ]
    chords: list[dict[str, Any]] = []
    with (ANALYSIS / "analysis/chords.csv").open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            chords.append({"start": round(float(row["start"]), 3), "end": round(float(row["end"]), 3), "name": row["chord"], "degree": ""})
    return chords


def ensure_audio() -> None:
    if not SELECTED_WAV.exists():
        raise FileNotFoundError(f"Missing selected WAV: {SELECTED_WAV}")
    target = SONGS / "audio" / PUBLIC_AUDIO_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(SELECTED_WAV), "-codec:a", "libmp3lame", "-b:a", "320k", str(target)],
        check=True,
    )
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def ensure_cover() -> tuple[int, int]:
    target = ROOT / "website" / COVER
    target.parent.mkdir(parents=True, exist_ok=True)
    if COVER_SOURCE.exists():
        shutil.copy2(COVER_SOURCE, target)
    if not target.exists():
        raise FileNotFoundError(f"Missing cover: {target}")
    return image_size(target)


def write_media_item() -> None:
    width, height = ensure_cover()
    media_dir = ROOT / "website/data/songs" / MEDIA_ID
    tracks = build_tracks()
    for code, lines in tracks.items():
        write_json(media_dir / "lyrics/ja-vocal" / f"{code}.json", track(code, lines))

    timeline = [{"id": line["id"], "start": line["start"], "end": line["end"], "text": line["text"]} for line in tracks["ja"]]
    run_manifest = read_json(ANALYSIS / "manifest.json")
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "かぎろひと花",
        "localizedTitles": {"ja": "かぎろひと花", "zh-Hans": "晨曦与花", "en": "Dawnlight and Blossoms"},
        "artist": "Musia",
        "description": "A Musia Japanese waka art-pop setting built only from selected Manyoshu and Kokin Wakashu source lines.",
        "caption": "Dawn glow, a sleeve in the purple fields, autumn wind, and spring blossoms.",
        "duration": round(ffprobe_duration(SELECTED_WAV), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "かぎろひと花 - Fun Lazying Art",
            "description": "A Musia Japanese waka song with ASR-corrected trilingual lyrics.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "かぎろひと花 cover", "role": "cover", "src": COVER, "mime": "image/png", "width": width, "height": height},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": width, "height": height},
            "primaryAudio": {
                "id": "kagirohi-to-hana-ja",
                "label": "日本語",
                "roleLabel": "Vocal",
                "role": "vocal",
                "languageCode": "ja",
                "languageLabel": "日本語",
                "lyricSetId": "ja-vocal",
                "src": PUBLIC_AUDIO,
                "mime": "audio/mpeg",
            },
            "alternateAudio": [],
        },
        "playback": {"defaultMode": "single"},
        "musical": {
            "key": "G major requested / detected G-centered progression",
            "bpm": round(float(run_manifest.get("tempo_bpm", 83.354)), 3),
            "timeSignature": "4/4",
            "chords": load_chords(),
        },
        "lyricSets": [
            {
                "id": "ja-vocal",
                "label": "日本語 vocal",
                "languageCode": "ja",
                "tracks": [
                    {"code": "ja", "label": "Japanese", "nativeLabel": "日本語", "script": "Jpan", "features": ["furigana", "active-vocal"], "path": "lyrics/ja-vocal/ja.json"},
                    {"code": "zh-Hans", "label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "features": ["pinyin", "translation"], "path": "lyrics/ja-vocal/zh-Hans.json"},
                    {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn", "features": ["translation"], "path": "lyrics/ja-vocal/en.json"},
                ],
            }
        ],
        "textTracks": [],
        "timeline": {"unit": "seconds", "lines": timeline},
        "artifacts": [],
        "provenance": {
            "createdBy": "Musia",
            "generationProject": "data/creative_projects/kagirohi-to-hana-20260701",
            "audioSource": "ACE-Step 1.5 XL Turbo short-kana seed 741214, selected after XL SFT, normal Japanese, kana, romaji, compact-hook, and two-hook comparisons.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {
                "xlSftInstalled": True,
                "selectedAudioLargeV3Overlap": 0.6519337016574586,
                "selectionReason": "Best ASR recovery and practical melodic continuity among tested waka layouts; public lyric omits unrecovered planned lines.",
                "gate": "selected-with-documented-waka-source-text-corrections",
            },
            "lyricCorrection": (
                "Corrected from selected full-mix large-v3 ASR, separated-vocal large-v3 ASR, planned kana control lyric, and source waka text. "
                "The public lyric preserves original Manyoshu/Kokin wording where sound-close and does not publish lines the selected render skipped."
            ),
            "coverPrompt": "16:9 album cover, elegant Japanese waka art-pop song, dawn eastern field, kagirohi glow, sinking moon, spring blossoms, no text.",
            "coverSource": str(COVER_SOURCE),
            "publicAudio": PUBLIC_AUDIO_NAME,
        },
    }
    write_json(media_dir / "manifest.json", manifest)

    catalog_path = ROOT / "website/data/catalog.json"
    catalog = read_json(catalog_path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "かぎろひと花",
        "artist": "Musia",
        "summary": "A Japanese waka art-pop song from selected Manyoshu and Kokin Wakashu lines, with ASR-corrected trilingual lyrics.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["ja", "zh-Hans", "en"],
        "tags": ["music", "Japanese", "waka", "Manyoshu", "Kokin Wakashu", "ACE-Step", "furigana", "pinyin"],
    }
    catalog["items"] = [entry for entry in catalog.get("items", []) if entry.get("id") != MEDIA_ID]
    insert_at = 1 if catalog.get("items") else 0
    catalog["items"].insert(insert_at, item)
    write_json(catalog_path, catalog)


def main() -> None:
    ensure_audio()
    write_media_item()
    print(f"https://fun.lazying.art/#{MEDIA_ID}")


if __name__ == "__main__":
    main()
