#!/usr/bin/env python3
"""Prepare the unlisted Fun preview item for 洛水照影."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pykakasi
from pypinyin import Style, pinyin


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
MEDIA_ID = "luoshui-zhaoying-preview"
PROJECT = ROOT / "data/creative_projects/luoshui-zhaoying-20260729"
COVER = "assets/covers/luoshui-zhaoying-preview-16x9.png"
COVER_SOURCE = (
    "/home/lachlan/.codex/generated_images/"
    "019f0842-25ba-7bd2-9d4b-0b1c60d8a951/call_nyNBuGPLt4c3kp5drSN83oJ0.png"
)
PUBLIC_BASE = "https://lazyingart.github.io/MusiaSongs/audio/"

VERSIONS = {
    "music-first": {
        "label": "Music First",
        "selectorLabel": "Music First",
        "seed": 829213,
        "audio": PROJECT / "selected/01-luoshui-zhaoying-music-first-seed829213.mp3",
        "publicName": "luoshui-zhaoying-preview-music-first-seed829213-20260729.mp3",
        "analysis": ROOT / "data/runs/luoshui-zhaoying-preview-music-first-analysis",
        "bpm": 73.828,
        "key": "D minor requested / Dm-centered analysis",
        "rows": [
            (14.40, 17.22, "洛水初明", "Dawn lights the Luoshui.", "洛水に朝の光が差す"),
            (17.22, 20.16, "风动微尘", "The wind stirs the finest dust.", "風が微かな塵を揺らす"),
            (22.22, 25.06, "我隔千重雾", "A thousand veils of mist lie between us.", "幾重の霧を隔て"),
            (25.06, 27.74, "看见你转身", "I see you turn around.", "振り向く君を見た"),
            (28.82, 31.68, "云遮一轮月", "Clouds veil a single moon.", "雲が一輪の月を隠す"),
            (31.68, 34.96, "雪落一场春", "Snow falls into a season of spring.", "雪はひとひらの春に降る"),
            (34.96, 37.90, "你从波光里", "You emerge from the shimmering water.", "水のきらめきから君が現れ"),
            (37.90, 40.66, "一步走近", "One step closer.", "一歩近づく"),
            (41.80, 45.46, "凌波而来，又随风去", "You cross the waves, then leave with the wind.", "波を渡って来て、風と去る"),
            (46.88, 50.36, "一眼惊鸿，一生难寻", "One startling glimpse, then a lifetime of searching.", "驚くほど美しい一目、生涯探し続ける"),
            (50.36, 55.26, "此心留在洛水，千里不肯忘记", "My heart stays by the Luoshui; across a thousand li, it will not forget.", "心は洛水に残り、千里を隔てても忘れない"),
            (57.88, 60.06, "袖间兰香", "The fragrance of orchids lingers in your sleeve.", "袖に蘭の香り"),
            (61.30, 63.38, "梦里星辰", "Stars shine within the dream.", "夢に星々が輝く"),
            (63.38, 66.40, "你未说离别", "You never spoke the word farewell.", "別れを告げないまま"),
            (66.40, 68.38, "我已知缘起", "I already know where our fate begins.", "縁の始まりを知った"),
            (69.34, 71.68, "若梦可以停", "If only the dream could stop here.", "夢をここで止められるなら"),
            (75.68, 77.92, "若人神有岸", "If there were a shore between mortal and divine.", "人と神の間に岸があるなら"),
            (77.92, 79.88, "愿渡尽光阴", "I would cross all of time.", "時のすべてを渡ろう"),
            (85.58, 89.34, "凌波而来，又随风去", "You cross the waves, then leave with the wind.", "波を渡って来て、風と去る"),
            (90.26, 94.08, "轻云蔽月，回雪沾衣", "Light cloud veils the moon; whirling snow brushes your robe.", "淡い雲が月を隠し、舞う雪が衣に触れる"),
            (94.08, 96.12, "此心留在洛水", "My heart stays by the Luoshui.", "心は洛水に残る"),
            (97.04, 100.64, "千里仍照见你", "A thousand li away, I can still see you.", "千里の彼方でも君が見える"),
        ],
        "correction": (
            "Corrected from separated-vocal large-v3 no-VAD ASR, full-mix ASR, "
            "MOSS-Music blind transcription, and the planned lyric. Sound-close "
            "source phrases were preserved; the omitted 愿长夜不醒 line was not "
            "inserted. Music-first timing is independent from the alternate render."
        ),
    },
    "lyric-first": {
        "label": "Lyrics First",
        "selectorLabel": "Lyrics First",
        "seed": 812401,
        "audio": PROJECT / "selected/02-luoshui-zhaoying-lyric-first-seed812401.mp3",
        "publicName": "luoshui-zhaoying-preview-lyric-first-seed812401-20260729.mp3",
        "analysis": ROOT / "data/runs/luoshui-zhaoying-preview-lyric-first-analysis",
        "bpm": 76.0,
        "key": "D minor requested / Dm-centered analysis",
        "rows": [
            (13.30, 16.26, "洛水初明", "Dawn lights the Luoshui.", "洛水に朝の光が差す"),
            (17.28, 19.50, "风动微尘", "The wind stirs the finest dust.", "風が微かな塵を揺らす"),
            (20.68, 22.46, "我隔千重雾", "A thousand veils of mist lie between us.", "幾重の霧を隔て"),
            (22.46, 25.50, "看见你转身", "I see you turn around.", "振り向く君を見た"),
            (25.50, 29.08, "云遮一轮月", "Clouds veil a single moon.", "雲が一輪の月を隠す"),
            (29.08, 31.78, "雪落一场春", "Snow falls into a season of spring.", "雪はひとひらの春に降る"),
            (31.78, 35.88, "你从波光里", "You emerge from the shimmering water.", "水のきらめきから君が現れ"),
            (35.88, 38.62, "一步一步走近", "Step by step, you draw near.", "一歩ずつ近づく"),
            (42.18, 44.34, "凌波而来", "You come across the waves.", "波を渡って来る"),
            (44.34, 45.88, "又随风去", "Then leave with the wind.", "そして風と去る"),
            (45.88, 47.46, "一眼惊鸿", "One startling, radiant glimpse.", "ひと目の鮮やかな面影"),
            (47.46, 49.26, "一生难寻", "A lifetime could not find it again.", "生涯探しても見つからない"),
            (49.26, 52.42, "此心留在洛水", "My heart stays by the Luoshui.", "心は洛水に残る"),
            (52.42, 54.84, "千里不成名", "Across a thousand li, no name remains.", "千里を隔て、名も残らず"),
            (54.84, 59.10, "千里不肯忘记", "Across a thousand li, it still refuses to forget.", "千里を隔てても忘れない"),
            (60.66, 62.26, "袖间兰香", "The fragrance of orchids lingers in your sleeve.", "袖に蘭の香り"),
            (62.82, 66.00, "眸里星辰", "Stars gather in your eyes.", "瞳に星々が宿る"),
            (66.00, 69.08, "你未说离别", "You never spoke the word farewell.", "別れを告げないまま"),
            (69.08, 72.40, "我已知缘尽", "I already know our fate has reached its end.", "縁の終わりを知っていた"),
            (72.96, 75.94, "若梦可以停", "If only the dream could stop here.", "夢をここで止められるなら"),
            (75.94, 79.26, "愿长夜不醒", "May the long night never wake.", "長い夜から覚めませんように"),
            (79.26, 83.18, "若人神有岸", "If there were a shore between mortal and divine.", "人と神の間に岸があるなら"),
            (83.18, 85.46, "愿渡尽光阴", "I would cross all of time.", "時のすべてを渡ろう"),
            (85.46, 88.22, "凌波而来", "You come across the waves.", "波を渡って来る"),
            (88.22, 89.82, "又随风去", "Then leave with the wind.", "そして風と去る"),
            (89.82, 91.50, "轻云蔽月", "Light cloud veils the moon.", "淡い雲が月を隠す"),
            (91.50, 93.20, "回雪沾衣", "Whirling snow brushes your robe.", "舞う雪が衣に触れる"),
            (93.20, 96.28, "此心留在洛水", "My heart stays by the Luoshui.", "心は洛水に残る"),
            (96.28, 99.42, "千里仍照见你", "A thousand li away, I can still see you.", "千里の彼方でも君が見える"),
        ],
        "correction": (
            "Corrected independently from this render's separated-vocal large-v3 "
            "normal/no-VAD ASR, MOSS-Music blind transcription, and planned lyric. "
            "Close phonetic substitutions were restored to the stronger intended "
            "Chinese; the extra 千里不成名 phrase remains because two evidence routes "
            "found an additional sung phrase before 千里不肯忘记."
        ),
    },
}

LANGUAGES = {
    "zh-Hans": {
        "code": "zh-Hans",
        "label": "Mandarin Chinese",
        "nativeLabel": "中文",
        "script": "Hans",
        "pronunciation": "pinyin",
    },
    "en": {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn"},
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


def is_cjk(text: str) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in text)


def split_visible(text: str, code: str) -> list[str]:
    if code == "en":
        spaced = text
        for mark in [",", ".", "?", "!", ";", ":"]:
            spaced = spaced.replace(mark, f" {mark} ")
        return [part for part in spaced.split() if part]
    return [char for char in text if not char.isspace()]


def zh_reading(line_text: str, char: str) -> str:
    if not is_cjk(char):
        return ""
    if "千重雾" in line_text and char == "重":
        return "chong2"
    values = pinyin(char, style=Style.TONE3, strict=False, neutral_tone_with_five=True)
    return values[0][0] if values and values[0] else ""


def ja_reading(char: str) -> str:
    if not is_cjk(char):
        return ""
    converted = KAKASI.convert(char)
    reading = "".join(part.get("hira") or part.get("orig") or "" for part in converted)
    return reading if reading and reading != char else ""


def tokens_for(text: str, code: str, start: float, end: float) -> list[dict[str, Any]]:
    parts = split_visible(text, code)
    if not parts:
        return []
    step = (end - start) / len(parts)
    tokens: list[dict[str, Any]] = []
    for index, part in enumerate(parts):
        token: dict[str, Any] = {
            "text": part,
            "start": round(start + step * index, 3),
            "end": round(start + step * (index + 1), 3),
        }
        if code == "zh-Hans":
            reading = zh_reading(text, part)
            if reading:
                token["pinyin"] = reading
        elif code == "ja":
            reading = ja_reading(part)
            if reading:
                token["reading"] = reading
        tokens.append(token)
    return tokens


def make_line(line_id: str, start: float, end: float, text: str, code: str) -> dict[str, Any]:
    return {
        "id": line_id,
        "start": round(start, 3),
        "end": round(end, 3),
        "text": text,
        "singableText": text,
        "role": "lyric",
        "tokens": tokens_for(text, code, start, end),
    }


def build_tracks(version_id: str, version: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    tracks = {code: [] for code in LANGUAGES}
    for index, (start, end, zh, en, ja) in enumerate(version["rows"], 1):
        line_id = f"l{index:02d}"
        tracks["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans"))
        tracks["en"].append(make_line(line_id, start, end, en, "en"))
        tracks["ja"].append(make_line(line_id, start, end, ja, "ja"))
    return tracks


def track_document(version_id: str, code: str, lines: list[dict[str, Any]]) -> dict[str, Any]:
    version = VERSIONS[version_id]
    return {
        "schema": "fun.lazying.media.text-track.v1",
        "version": 1,
        "mediaId": MEDIA_ID,
        "language": LANGUAGES[code],
        "lines": lines,
        "provenance": {
            "vocalSet": version_id,
            "releaseStage": "unlisted-preview",
            "correction": version["correction"],
        },
    }


def load_musical(version: dict[str, Any]) -> dict[str, Any]:
    chord_data = read_json(version["analysis"] / "analysis/chords.json").get("chords", [])
    beat_data = read_json(version["analysis"] / "analysis/beats.json").get("beats", [])
    chords = [
        {
            "start": round(float(item["start"]), 3),
            "end": round(float(item["end"]), 3),
            "name": item.get("chord") or item.get("name") or "N.C.",
            "degree": "",
            "confidence": round(float(item.get("confidence", 0)), 3),
        }
        for item in chord_data
    ]
    beats = [
        {
            "index": int(item.get("index", index)),
            "time": round(float(item["time"]), 3),
        }
        for index, item in enumerate(beat_data)
    ]
    return {
        "key": version["key"],
        "bpm": version["bpm"],
        "timeSignature": "4/4",
        "chords": chords,
        "beats": beats,
        "chordSource": "Musia analysis-grade chord inference from this exact render",
        "beatSource": "Musia beat analysis from this exact render",
    }


def ensure_public_audio() -> None:
    for version in VERSIONS.values():
        source = version["audio"]
        if not source.exists():
            raise FileNotFoundError(source)
        target = SONGS / "audio" / version["publicName"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def asset(version_id: str, version: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"luoshui-{version_id}",
        "label": version["label"],
        "selectorLabel": version["selectorLabel"],
        "publicRoleLabel": "Preview",
        "role": "vocal",
        "languageCode": "zh-Hans",
        "languageLabel": version["label"],
        "lyricSetId": version_id,
        "src": PUBLIC_BASE + version["publicName"],
        "mime": "audio/mpeg",
        "musical": load_musical(version),
    }


def write_media_item() -> None:
    cover_path = ROOT / "website" / COVER
    if not cover_path.exists():
        raise FileNotFoundError(cover_path)

    media_dir = ROOT / "website/data/songs" / MEDIA_ID
    built_tracks: dict[str, dict[str, list[dict[str, Any]]]] = {}
    lyric_sets: list[dict[str, Any]] = []
    for version_id, version in VERSIONS.items():
        built_tracks[version_id] = build_tracks(version_id, version)
        for code, lines in built_tracks[version_id].items():
            write_json(
                media_dir / "lyrics" / version_id / f"{code}.json",
                track_document(version_id, code, lines),
            )
        lyric_sets.append(
            {
                "id": version_id,
                "label": version["label"],
                "languageCode": "zh-Hans",
                "tracks": [
                    {
                        "code": "zh-Hans",
                        "label": "Mandarin Chinese",
                        "nativeLabel": "中文",
                        "script": "Hans",
                        "features": ["active-vocal", "pinyin", "word-highlight"],
                        "path": f"lyrics/{version_id}/zh-Hans.json",
                    },
                    {
                        "code": "en",
                        "label": "English",
                        "nativeLabel": "English",
                        "script": "Latn",
                        "features": ["translation", "rough-highlight"],
                        "path": f"lyrics/{version_id}/en.json",
                    },
                    {
                        "code": "ja",
                        "label": "Japanese",
                        "nativeLabel": "日本語",
                        "script": "Jpan",
                        "features": ["translation", "furigana", "rough-highlight"],
                        "path": f"lyrics/{version_id}/ja.json",
                    },
                ],
            }
        )

    primary_id = "music-first"
    primary = VERSIONS[primary_id]
    primary_asset = asset(primary_id, primary)
    alternate_assets = [
        asset(version_id, version)
        for version_id, version in VERSIONS.items()
        if version_id != primary_id
    ]
    timeline = [
        {
            "id": line["id"],
            "start": line["start"],
            "end": line["end"],
            "text": line["text"],
        }
        for line in built_tracks[primary_id]["zh-Hans"]
    ]
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "洛水照影 · Preview",
        "localizedTitles": {
            "zh-Hans": "洛水照影 · 试听",
            "en": "Reflections on the Luoshui · Preview",
            "ja": "洛水の面影・プレビュー",
        },
        "artist": "Musia",
        "description": "An unlisted two-candidate listening preview of an original cinematic Mandarin Luoshui ballad.",
        "caption": "Across moonlit water, one reflected figure approaches and disappears with the wind.",
        "duration": 108.0,
        "canonicalUrl": f"https://fun.lazying.art/?preview=1#{MEDIA_ID}",
        "publication": {
            "visibility": "unlisted",
            "stage": "preview",
            "label": "Unlisted Preview",
            "listed": False,
            "note": "Direct-link listening candidate; excluded from the default catalog and playback queue.",
        },
        "share": {
            "title": "洛水照影 · Preview - Fun Lazying Art",
            "description": "Compare the Music First and Lyrics First listening candidates for Musia's original Luoshui ballad.",
            "url": f"https://fun.lazying.art/?preview=1#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {
                "id": "cover",
                "label": "洛水照影 preview cover",
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
            "primaryAudio": primary_asset,
            "alternateAudio": alternate_assets,
        },
        "musical": primary_asset["musical"],
        "textTracks": [],
        "lyricSets": lyric_sets,
        "timeline": {"unit": "seconds", "lines": timeline},
        "playback": {"defaultMode": "off"},
        "provenance": {
            "createdBy": "Musia",
            "generationProject": "data/creative_projects/luoshui-zhaoying-20260729",
            "audioSource": "ACE-Step 1.5 XL Turbo seed sweep; music-first seed 829213 and lyric-first seed 812401.",
            "analysisRuns": {
                version_id: str(version["analysis"].relative_to(ROOT))
                for version_id, version in VERSIONS.items()
            },
            "quality": {
                "gate": "unlisted-human-listening-preview",
                "note": "Both renders passed signal health. Each lyric set was corrected independently from separated-vocal large-v3 and MOSS evidence.",
            },
            "lyricCorrection": {
                version_id: version["correction"]
                for version_id, version in VERSIONS.items()
            },
            "coverSource": COVER_SOURCE,
            "coverPrompt": (
                "Moonlit Luoshui river through an immense ancient Chinese celestial "
                "megastructure, with a distant original figure walking across ripples; "
                "cinematic 16:9 concept art, no text or real singer likeness."
            ),
            "publicAudio": {
                version_id: version["publicName"]
                for version_id, version in VERSIONS.items()
            },
        },
    }
    write_json(media_dir / "manifest.json", manifest)

    catalog_path = ROOT / "website/data/catalog.json"
    catalog = read_json(catalog_path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "洛水照影 · Preview",
        "artist": "Musia",
        "summary": "An unlisted two-candidate preview for choosing between stronger musical expression and fuller lyric coverage.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "visibility": "unlisted",
        "releaseStage": "preview",
        "category": "preview",
        "previewLabel": "Listening Preview",
        "previewReason": "Awaiting human selection of the Music First or Lyrics First master.",
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "preview", "unlisted", "Mandarin", "Luoshui", "cinematic", "ACE-Step", "pinyin", "furigana", "chords"],
    }
    catalog["items"] = [entry for entry in catalog.get("items", []) if entry.get("id") != MEDIA_ID]
    catalog["items"].insert(0, item)
    write_json(catalog_path, catalog)


def main() -> None:
    ensure_public_audio()
    write_media_item()
    print(f"https://fun.lazying.art/?preview=1#{MEDIA_ID}")


if __name__ == "__main__":
    main()
