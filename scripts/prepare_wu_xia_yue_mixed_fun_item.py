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
MEDIA_ID = "wu-xia-yue-mixed"
PROJECT = ROOT / "data/creative_projects/wu-xia-yue-mixed-20260709"
SELECTED_AUDIO = PROJECT / "selected/wu-xia-yue-mixed-ace-xl-turbo-seed791111.mp3"
ANALYSIS = ROOT / "data/runs/wu-xia-yue-mixed-20260709-analysis"
PUBLIC_AUDIO_NAME = "wu-xia-yue-mixed-ace-xl-turbo-seed791111-20260709.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/wu-xia-yue-mixed-16x9.png"
COVER_SOURCE = Path(
    "/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/"
    "ig_0933499e24356a63016a4f8747a1dc8191a4073a32c1752405.png"
)

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
        elif code == "ja" and (is_cjk(part) or has_kana(part)):
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
    line["tokens"] = tokens_for(line, code)
    return line


def corrected_rows() -> list[tuple[str, float, float, str, str, str, str, str]]:
    """ASR/listening correction for ACE XL Turbo seed 791111.

    Evidence:
    - selected-render small ASR from `run_pipeline.py`;
    - v2 planned mixed lyric;
    - source couplet supplied by the user.

    The render keeps the English smallness hook, approximates the Chinese poem
    pinyin, repeats the mayfly line, and drops the drafted outro. Public lyrics
    follow that actual structure.
    """

    return [
        ("i01", 0.00, 15.02, "♪", "♪", "♪", "♪", "instrumental"),
        ("l01", 15.02, 23.03, "I am small in the silver light", "I am small in the silver light.", "銀の光の中で、私は小さい", "我在银色月光里如此渺小", "lyric"),
        ("l02", 23.03, 26.03, "Yue zhao Wu Xia qian feng ji", "Moonlight shines on Wu Gorge; a thousand peaks are still.", "月は巫峡を照らし、千の峰は静まる", "月照巫峡千峰寂", "lyric"),
        ("l03", 26.59, 30.51, "A mayfly under endless sky, shen si", "A mayfly under the endless sky; this body is like a mayfly.", "果てない空の下の蜉蝣、この身もまた蜉蝣のよう", "身似蜉蝣，在无尽天幕下", "lyric"),
        ("l04", 30.51, 32.33, "Fu you yi su qing", "A mayfly, light as one grain.", "蜉蝣、一粒の粟ほど軽い", "蜉蝣一粟轻", "lyric"),
        ("l05", 32.33, 37.11, "A mayfly under endless sky, shen si", "A mayfly under the endless sky; this body is like a mayfly.", "果てない空の下の蜉蝣、この身もまた蜉蝣のよう", "身似蜉蝣，在无尽天幕下", "lyric"),
        ("l06", 37.11, 39.17, "Fu you yi su qing", "A mayfly, light as one grain.", "蜉蝣、一粒の粟ほど軽い", "蜉蝣一粟轻", "lyric"),
        ("l07", 39.55, 41.79, "River wind, carry me", "River wind, carry me.", "川風よ、私を運んで", "江风啊，带我远去", "lyric"),
        ("l08", 41.79, 45.55, "Jiang feng qian fan guo", "River wind sends a thousand sails past.", "川風は千の帆を送り過ぎる", "江风送尽千帆过", "lyric"),
        ("l09", 45.55, 50.65, "Hyakunen no yume, bai nian sui bo qu", "A hundred-year dream drifts away with the waves.", "百年の夢は波へ流れていく", "百年浮沉随波去", "lyric"),
        ("i02", 50.65, 52.99, "♪", "♪", "♪", "♪", "instrumental"),
        ("l10", 52.99, 56.25, "Moon over Wu Xia", "Moon over Wu Gorge.", "巫峡の上の月", "月照巫峡", "lyric"),
        ("l11", 56.25, 58.73, "Everything is still", "Everything is still.", "すべてが静まり返る", "万物俱寂", "lyric"),
        ("l12", 58.73, 66.27, "I am small, but my heart carries", "I am small, but my heart carries on.", "私は小さい、それでも心は運んでいく", "我很渺小，但心仍向前", "lyric"),
        ("i03", 66.27, 76.00, "♪", "♪", "♪", "♪", "instrumental"),
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
                "Corrected from selected ACE XL Turbo seed 791111 using selected-render ASR and the planned "
                "mixed phonetic lyric. Source-close Chinese pinyin forms are preserved where ASR is phonetically close."
            ),
        },
    }


def build_tracks() -> dict[str, list[dict[str, Any]]]:
    lines = {"mul": [], "en": [], "zh-Hans": [], "ja": []}
    for line_id, start, end, active, en, ja, zh, role in corrected_rows():
        lines["mul"].append(make_line(line_id, start, end, active, "mul", role))
        lines["en"].append(make_line(line_id, start, end, en, "en", role))
        lines["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans", role))
        lines["ja"].append(make_line(line_id, start, end, ja, "ja", role))
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
        write_json(media_dir / "lyrics/mixed-vocal" / f"{code}.json", track(code, lines))

    timeline = [{"id": line["id"], "start": line["start"], "end": line["end"], "text": line["text"]} for line in tracks["mul"]]
    run_manifest = read_json(ANALYSIS / "manifest.json")
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "巫峡月 · Moon Over Wu Gorge",
        "localizedTitles": {
            "zh-Hans": "巫峡月",
            "en": "Moon Over Wu Gorge",
            "ja": "巫峡の月",
        },
        "artist": "Musia",
        "description": "A mixed English, Mandarin pinyin, and Japanese moonlit river-gorge ballad about human smallness, passing sails, and a heart that keeps moving.",
        "caption": "Moon over Wu Gorge, a thousand silent peaks, and one small life drifting with the river wind.",
        "duration": round(duration(SELECTED_AUDIO), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "巫峡月 · Moon Over Wu Gorge - Fun Lazying Art",
            "description": "A Musia mixed-language moonlit gorge ballad with corrected synced lyrics, translations, pinyin, furigana, chords, and stems.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "Moonlit Wu Gorge cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": "wu-xia-yue-mixed",
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
            "key": "D minor planned / detected Dm-Bb-F modal colors",
            "bpm": round(float(run_manifest.get("tempo_bpm", 151.99908088235293)), 3),
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
                    {"code": "mul", "label": "Mixed", "nativeLabel": "Mixed", "script": "Latn", "features": ["active-vocal"], "path": "lyrics/mixed-vocal/mul.json"},
                    {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn", "features": ["translation"], "path": "lyrics/mixed-vocal/en.json"},
                    {"code": "ja", "label": "Japanese", "nativeLabel": "日本語", "script": "Jpan", "features": ["furigana", "translation"], "path": "lyrics/mixed-vocal/ja.json"},
                    {"code": "zh-Hans", "label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "features": ["pinyin", "translation"], "path": "lyrics/mixed-vocal/zh-Hans.json"},
                ],
            }
        ],
        "timeline": {"unit": "seconds", "lines": timeline},
        "playback": {"defaultMode": "single"},
        "provenance": {
            "createdBy": "Musia",
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "audioSource": "ACE-Step 1.5 XL Turbo mixed-language route, seed 791111, selected from two sweeps.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {
                "gate": "public-candidate",
                "note": "Selected for the clearest mixed-vocal recovery in the second sweep. Public lyrics follow the actual sung structure.",
            },
            "lyricCorrection": "Selected-render small ASR plus planned lyric/source couplet cross-check; source-close pinyin forms preserved.",
            "coverSource": str(COVER_SOURCE),
            "coverPrompt": "Moonlit Wu Gorge, silent peaks, Yangtze river, distant sails, tiny human figure, vast lonely hopeful Chinese art-pop cover.",
            "publicAudio": PUBLIC_AUDIO_NAME,
        },
        "artifacts": [
            {"label": "Analysis report", "path": str((ANALYSIS / "REPORT.md").relative_to(ROOT))},
            {"label": "Chords", "path": str((ANALYSIS / "analysis/chords.csv").relative_to(ROOT))},
            {"label": "Beats", "path": str((ANALYSIS / "analysis/beats.csv").relative_to(ROOT))},
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
        "title": "巫峡月 · Moon Over Wu Gorge",
        "artist": "Musia",
        "summary": "A mixed English, Japanese romaji, and Mandarin pinyin moonlit gorge ballad.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["mul", "en", "zh-Hans", "ja"],
        "tags": ["music", "multilingual", "Wu Gorge", "moon", "river", "ACE-Step", "pinyin", "furigana", "chords"],
    }
    items = [existing for existing in catalog["items"] if existing.get("id") != MEDIA_ID]
    items.insert(0, item)
    catalog["items"] = items
    write_json(path, catalog)


def write_reference() -> None:
    reference = ROOT / "references/wu-xia-yue-mixed-production-2026-07-09.md"
    reference.write_text(
        "\n".join(
            [
                "# 巫峡月 · Moon Over Wu Gorge Production Note",
                "",
                "## Source",
                "",
                "```text",
                "月照巫峡千峰寂，身似蜉蝣一粟轻。",
                "江风送尽千帆过，百年浮沉随波去。",
                "```",
                "",
                "## Selected Render",
                "",
                "- Route: ACE-Step 1.5 XL Turbo mixed-language route.",
                "- Selected seed: `791111` from the cleaner v2 sweep.",
                "- Selected audio: `data/creative_projects/wu-xia-yue-mixed-20260709/selected/wu-xia-yue-mixed-ace-xl-turbo-seed791111.mp3`.",
                f"- Public audio: `{PUBLIC_AUDIO}`.",
                "- Analysis: `data/runs/wu-xia-yue-mixed-20260709-analysis/`.",
                "- Website manifest: `website/data/songs/wu-xia-yue-mixed/manifest.json`.",
                "",
                "## Attempts",
                "",
                "- First sweep used denser poem-pinyin lines. ASR recovery was weak.",
                "- Second sweep used clearer English lead lines, shorter pinyin hooks, and shorter Japanese romaji color lines.",
                "- Seed `791111` was selected because it recovered `I am small in the silver light`, the Wu Xia phrase, the mayfly image, river wind, and the final small-heart line more coherently than the other checked candidates.",
                "",
                "## Corrected Active Vocal",
                "",
                "```text",
                "15.02-23.03 I am small in the silver light",
                "23.03-26.03 Yue zhao Wu Xia qian feng ji",
                "26.59-30.51 A mayfly under endless sky, shen si",
                "30.51-32.33 Fu you yi su qing",
                "32.33-37.11 A mayfly under endless sky, shen si",
                "37.11-39.17 Fu you yi su qing",
                "39.55-41.79 River wind, carry me",
                "41.79-45.55 Jiang feng qian fan guo",
                "45.55-50.65 Hyakunen no yume, bai nian sui bo qu",
                "52.99-56.25 Moon over Wu Xia",
                "56.25-58.73 Everything is still",
                "58.73-66.27 I am small, but my heart carries",
                "```",
                "",
                "The render dropped the planned outro and some final source-line repeats. Public lyrics follow the actual selected audio, with instrumental spans represented as `♪`.",
                "",
                "## Cover Rule",
                "",
                "A fresh cover was generated specifically for this song using only the current song imagery: moonlit Wu Gorge, silent peaks, Yangtze river, distant sails, a tiny human figure, and a vast lonely hopeful mood. No older song cover or stale prompt was reused.",
                "",
                "## Website",
                "",
                f"- URL: `https://fun.lazying.art/#{MEDIA_ID}`.",
                "- Default audio/language: `Mixed` (`languageCode: mul`).",
                "- Active lyric: `website/data/songs/wu-xia-yue-mixed/lyrics/mixed-vocal/mul.json`.",
                "- Companion tracks: English, Japanese, Mandarin Chinese.",
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

