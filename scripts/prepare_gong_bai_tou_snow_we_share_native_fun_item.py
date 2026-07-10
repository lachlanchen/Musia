#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pykakasi
from PIL import Image
from pypinyin import Style, pinyin


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
MEDIA_ID = "gong-bai-tou-snow-we-share-native"
PROJECT = ROOT / "data/creative_projects/gong-bai-tou-snow-we-share-native-20260710"
SELECTED_AUDIO = PROJECT / "selected/gong-bai-tou-snow-we-share-zh-yuerenge-style-seed791401.mp3"
ANALYSIS = ROOT / "data/runs/gong-bai-tou-snow-we-share-native-20260710-analysis"
PUBLIC_AUDIO_NAME = "gong-bai-tou-snow-we-share-native-zh-yuerenge-style-seed791401-20260710.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/gong-bai-tou-snow-we-share-native-16x9.png"
COVER_SOURCE = Path(
    "/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/"
    "ig_020334d34d5a6efa016a50f64653748191a03f213e5438eca2.png"
)

DISPLAY_TITLE = "共白头 · Snow We Share"
LOCALIZED_TITLES = {
    "zh-Hans": "共白头",
    "en": "Snow We Share",
    "ja": "同じ雪の下で",
}
SUMMARY = (
    "A source-line Mandarin autumn-and-snow ballad using only the poem lines: "
    "忽有故人心上过，回首山河已入秋，他朝若是同淋雪，此生也算共白头。"
)

LANG = {
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
    if code == "en":
        return split_en(text)
    if code == "ja":
        return split_ja(text)
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
    """ASR/listening correction for ACE XL Turbo seed 791401.

    The selected render is a Yuerenge-style source-line route. Faster-whisper
    hears nearby substitutions such as `挥手/回首`, `泪如秋/已入秋`, and
    `公白头/共白头`. The line count, phrase contour, and meaning are
    source-close, so the public lyric preserves the original source text.
    """

    return [
        ("l01", 16.27, 21.18, "忽有故人心上过", "An old friend crosses my heart.", "ふと故人が胸をよぎる。"),
        ("l02", 22.18, 26.40, "回首山河已入秋", "I turn back; mountains and rivers have entered autumn.", "振り向けば山河は秋に入る。"),
        ("l03", 27.88, 33.12, "他朝若是同淋雪", "If someday we share the falling snow.", "いつか同じ雪に濡れるなら。"),
        ("l04", 34.56, 39.10, "此生也算共白头", "This life may still count as growing old together.", "この一生も共白髪といえる。"),
        ("l05", 40.40, 45.74, "此生也算共白头", "This life may still count as growing old together.", "この一生も共白髪といえる。"),
        ("l06", 59.73, 64.31, "回首山河已入秋", "I turn back; mountains and rivers have entered autumn.", "振り向けば山河は秋に入る。"),
        ("l07", 65.19, 71.01, "他朝若是同淋雪", "If someday we share the falling snow.", "いつか同じ雪に濡れるなら。"),
        ("l08", 72.29, 77.13, "此生也算共白头", "This life may still count as growing old together.", "この一生も共白髪といえる。"),
        ("l09", 77.13, 84.16, "此生也算共白头", "This life may still count as growing old together.", "この一生も共白髪といえる。"),
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
                "Corrected from the selected Chinese render using same-audio ASR, "
                "the source poem, and the Musia source-close policy. No instrumental "
                "placeholder rows are stored as lyrics."
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
    if not SELECTED_AUDIO.exists():
        raise FileNotFoundError(f"Missing selected audio: {SELECTED_AUDIO}")
    target = SONGS / "audio" / PUBLIC_AUDIO_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SELECTED_AUDIO, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def make_cover() -> None:
    if not COVER_SOURCE.exists():
        raise FileNotFoundError(f"Missing generated cover source: {COVER_SOURCE}")
    target = ROOT / "website" / COVER
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(COVER_SOURCE) as source:
        source = source.convert("RGB")
        target_ratio = 16 / 9
        width, height = source.size
        current = width / height
        if current > target_ratio:
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            source = source.crop((left, 0, left + new_width, height))
        elif current < target_ratio:
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            source = source.crop((0, top, width, top + new_height))
        source.resize((1600, 900), Image.Resampling.LANCZOS).save(target)


def write_media_item() -> None:
    media_dir = ROOT / "website/data/songs" / MEDIA_ID
    tracks = build_tracks()
    for code, lines in tracks.items():
        write_json(media_dir / "lyrics/zh-vocal" / f"{code}.json", track(code, lines))

    timeline = [
        {"id": line["id"], "start": line["start"], "end": line["end"], "text": line["text"]}
        for line in tracks["zh-Hans"]
    ]
    run_manifest = read_json(ANALYSIS / "manifest.json")
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": DISPLAY_TITLE,
        "localizedTitles": LOCALIZED_TITLES,
        "artist": "Musia",
        "description": SUMMARY,
        "caption": "If one day we share the same snow, this life may still count as growing old together.",
        "duration": round(duration(SELECTED_AUDIO), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": f"{DISPLAY_TITLE} - Fun Lazying Art",
            "description": "A Musia source-line Mandarin autumn-and-snow ballad with synced lyrics, translations, pinyin, furigana, chords, and stems.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {
                "id": "cover",
                "label": "Snow We Share cover",
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
                "id": "gong-bai-tou-snow-we-share-native-zh",
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
        "musical": {
            "key": "B minor planned / detected A major with modal shifts",
            "bpm": round(float(run_manifest.get("tempo_bpm", 152.0)), 3),
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
        "playback": {"defaultMode": "single"},
        "provenance": {
            "createdBy": "Musia",
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "audioSource": "ACE-Step 1.5 XL Turbo Yuerenge-style Chinese source-line route, seed 791401.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {
                "gate": "public-candidate",
                "note": (
                    "Same-audio ASR passed the automated gate but produced source-close substitutions. "
                    "Public lyrics restore the original source lines where phrase count and sound are close."
                ),
            },
            "lyricCorrection": (
                "Faster-whisper small ASR on the selected render plus source-line cross-check. "
                "Instrumental gaps are not encoded as lyric rows."
            ),
            "coverSource": str(COVER_SOURCE),
            "publicAudio": PUBLIC_AUDIO_NAME,
        },
        "artifacts": {
            "project": str(PROJECT.relative_to(ROOT)),
            "selectedWav": str((PROJECT / "selected/gong-bai-tou-snow-we-share-zh-yuerenge-style-seed791401.wav").relative_to(ROOT)),
            "selectedMp3": str(SELECTED_AUDIO.relative_to(ROOT)),
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


def update_catalog() -> None:
    path = ROOT / "website/data/catalog.json"
    catalog = read_json(path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": DISPLAY_TITLE,
        "artist": "Musia",
        "summary": SUMMARY,
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "Mandarin", "autumn", "snow", "ACE-Step", "pinyin", "furigana", "chords"],
    }
    items = [existing for existing in catalog["items"] if existing.get("id") != MEDIA_ID]
    items.insert(0, item)
    catalog["items"] = items
    catalog["defaultMedia"] = MEDIA_ID
    write_json(path, catalog)


def write_reference() -> None:
    reference = ROOT / "references/gong-bai-tou-snow-we-share-native-production-2026-07-10.md"
    reference.write_text(
        "\n".join(
            [
                "# 共白头 · Snow We Share Production Note",
                "",
                "## Source Lines",
                "",
                "```text",
                "忽有故人心上过，回首山河已入秋。",
                "他朝若是同淋雪，此生也算共白头。",
                "```",
                "",
                "## Selected Render",
                "",
                "- Route: ACE-Step 1.5 XL Turbo, Yuerenge-style focused Mandarin source-line route.",
                "- Selected seed: `791401`.",
                "- Selected audio: `data/creative_projects/gong-bai-tou-snow-we-share-native-20260710/selected/gong-bai-tou-snow-we-share-zh-yuerenge-style-seed791401.mp3`.",
                f"- Public audio: `{PUBLIC_AUDIO}`.",
                "- Analysis: `data/runs/gong-bai-tou-snow-we-share-native-20260710-analysis/`.",
                "- Website manifest: `website/data/songs/gong-bai-tou-snow-we-share-native/manifest.json`.",
                "",
                "## What Worked",
                "",
                "This remake initially failed with dense mixed-language prompts and literal source-only Chinese prompts. The route that finally passed came from reusing the `越人歌` philosophy:",
                "",
                "- keep the sung vocal focused in one language instead of forcing EN/JP/ZH into one render;",
                "- select the most musical source lines and repeat them as verse/chorus hooks;",
                "- use compact Chinese positive prompting rather than long negative lists;",
                "- treat ASR as a guardrail, not the sole judge, for soft classical-style singing;",
                "- publish original source text when ASR substitutions are sound-close and the structure matches.",
                "",
                "The earlier `共饮长江水` route remains useful when a mixed-language vocal is desired: pinyin/romaji can be private sound control, but the public lyric must be corrected from the actual audio. For this standard version, the Chinese-only `越人歌` route was more truthful and musical.",
                "",
                "## ASR Evidence",
                "",
                "Faster-whisper small on the selected render recovered the structure with nearby substitutions:",
                "",
                "```text",
                "要不然 心伤过 挥手山河泪如球",
                "他叫若是银雪 此生也算 公白头",
                "此生也算 公白头 挥手山河泪如球",
                "他叫若是银雪 此生也算 公白头 此生也算",
                "```",
                "",
                "Correction policy used here:",
                "",
                "- `心伤过` is source-close to `心上过`.",
                "- `挥手山河` is source-close to `回首山河`.",
                "- `泪如球` is source-close enough to restore `已入秋` because it matches the phrase slot and user-requested rhyme.",
                "- `他叫若是银雪` is restored to `他朝若是同淋雪` because the phrase shape, key syllables, and `雪` are present.",
                "- `公白头` is restored to `共白头` because the sound is close and the source is stronger.",
                "",
                "## Corrected Website Lines",
                "",
                "```text",
                "16.27-21.18 忽有故人心上过",
                "22.18-26.40 回首山河已入秋",
                "27.88-33.12 他朝若是同淋雪",
                "34.56-39.10 此生也算共白头",
                "40.40-45.74 此生也算共白头",
                "59.73-64.31 回首山河已入秋",
                "65.19-71.01 他朝若是同淋雪",
                "72.29-77.13 此生也算共白头",
                "77.13-84.16 此生也算共白头",
                "```",
                "",
                "Public lyric JSON stores only sung lines. Instrumental intro/interlude/outro are timing gaps, not lyric rows.",
                "",
                "## Website",
                "",
                f"- URL: `https://fun.lazying.art/#{MEDIA_ID}`.",
                "- Active lyric: `website/data/songs/gong-bai-tou-snow-we-share-native/lyrics/zh-vocal/zh-Hans.json`.",
                "- Companion tracks: English and Japanese translations with Japanese furigana.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    ensure_audio()
    make_cover()
    write_media_item()
    update_catalog()
    write_reference()
    print(ROOT / "website/data/songs" / MEDIA_ID / "manifest.json")


if __name__ == "__main__":
    main()
