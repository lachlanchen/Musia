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
MEDIA_ID = "ku-chao-qing-heng-mixed"
PROJECT = ROOT / "data/creative_projects/ku-chao-qing-heng-mixed-20260708"
SELECTED_AUDIO = PROJECT / "selected/ku-chao-qing-heng-mixed-ace-xl-turbo-seed780824.mp3"
ANALYSIS = ROOT / "data/runs/ku-chao-qing-heng-mixed-20260708-seed780824-analysis"
PUBLIC_AUDIO_NAME = "ku-chao-qing-heng-mixed-ace-xl-turbo-seed780824-20260708.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/ku-chao-qing-heng-mixed-16x9.png"
COVER_SOURCE = Path(
    "/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/"
    "ig_0f31e2965e443d1d016a4e6fd187448191ae9596707e9bf706.png"
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


def zh_pinyin_for(line_text: str, char: str) -> str:
    if not is_cjk(char):
        return ""
    overrides = {
        ("日本晁卿辞帝都", "日"): "ri4",
        ("日本晁卿辞帝都", "本"): "ben3",
        ("日本晁卿辞帝都", "晁"): "chao2",
        ("日本晁卿辞帝都", "卿"): "qing1",
        ("日本晁卿辞帝都", "衡"): "heng2",
        ("日本晁卿辞帝都", "辞"): "ci2",
        ("日本晁卿辞帝都", "帝"): "di4",
        ("日本晁卿辞帝都", "都"): "du1",
        ("征帆一片绕蓬壶", "征"): "zheng1",
        ("征帆一片绕蓬壶", "帆"): "fan1",
        ("征帆一片绕蓬壶", "蓬"): "peng2",
        ("征帆一片绕蓬壶", "壶"): "hu2",
        ("明月不归沉碧海", "沉"): "chen2",
        ("白云愁色满苍梧", "愁"): "chou2",
        ("白云愁色满苍梧", "苍"): "cang1",
        ("白云愁色满苍梧", "梧"): "wu2",
    }
    for (needle, target), reading in overrides.items():
        if needle in line_text and char == target:
            return reading
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
            reading = zh_pinyin_for(line["text"], part)
            if reading:
                token["pinyin"] = reading
        elif code == "ja" and (is_cjk(part) or has_kana(part)):
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
    """Corrected active timing for seed 780824.

    Evidence:
    - `data/runs/ku-chao-qing-heng-mixed-20260708-seed780824-analysis/analysis/lyrics.json`
      from the selected same-render ASR.
    - `reviews/selected-seed780824-medium-en/QA.md` as a weaker cross-check.
    - Intended compact hook lyric in `lyrics/mixed-hook-phonetic.txt`.

    The selected audio is a phonetic mixed render. The active `mul` track keeps
    pinyin/romaji/English where ACE sang them. The Chinese public track is not
    a literal translation of every companion line; it is a source-poem anchor
    that uses only Li Bai's original lines, per the user's constraint.
    """

    return [
        ("l01", 6.32, 8.38, "Haruka umi e", "To the distant sea", "遥か海へ", "征帆一片绕蓬壶"),
        ("l02", 9.06, 11.52, "One sail fades into blue", "One sail fades into blue", "一つの帆が青へ消える", "征帆一片绕蓬壶"),
        ("l03", 12.94, 15.88, "Ri ben Chao Qing ci di du", "Chao Qingheng leaves the imperial city", "晁卿衡は帝都を辞す", "日本晁卿辞帝都"),
        ("l04", 16.32, 18.98, "Zheng fan yi pian rao Peng Hu", "One expedition sail circles Penghu", "征帆一片、蓬壺をめぐる", "征帆一片绕蓬壶"),
        ("l05", 19.48, 21.70, "Haruka umi e", "To the distant sea", "遥か海へ", "征帆一片绕蓬壶"),
        ("l06", 22.42, 24.88, "Sail away, my friend", "Sail away, my friend", "さらば、友よ", "日本晁卿辞帝都"),
        ("l07", 27.54, 30.16, "Ming yue bu gui chen bi hai", "The bright moon will not return, sunk in the blue sea", "明月は帰らず碧海に沈む", "明月不归沉碧海"),
        ("l08", 31.00, 31.28, "Moon", "Moon", "月", "明月不归沉碧海"),
        ("l09", 35.24, 37.18, "Tsuki wa kaeranu", "The moon will not return", "月は帰らない", "明月不归沉碧海"),
        ("l10", 39.28, 41.56, "Ming yue bu gui chen bi hai", "The bright moon will not return, sunk in the blue sea", "明月は帰らず碧海に沈む", "明月不归沉碧海"),
        ("l11", 43.06, 44.98, "Bai yun chou se man Cang Wu", "White clouds fill Cangwu with sorrow", "白雲の愁色、蒼梧に満つ", "白云愁色满苍梧"),
        ("l12", 46.06, 48.50, "Moon over the blue sea", "Moon over the blue sea", "青い海の月", "明月不归沉碧海"),
        ("l13", 48.84, 50.20, "Shiroi kumo", "White clouds", "白い雲", "白云愁色满苍梧"),
        ("l14", 50.78, 53.78, "Kanashimi no iro", "The color of grief", "悲しみの色", "白云愁色满苍梧"),
        ("l15", 57.72, 60.20, "Zheng fan yi pian rao Peng Hu", "One sail circles Penghu", "征帆一片、蓬壺をめぐる", "征帆一片绕蓬壶"),
        ("l16", 62.15, 64.39, "Ri ben Chao Qing ci di du", "Chao Qingheng leaves the city", "晁卿衡は帝都を辞す", "日本晁卿辞帝都"),
        ("l17", 64.89, 66.81, "Far beyond the waves", "Far beyond the waves", "波の彼方へ", "征帆一片绕蓬壶"),
        ("l18", 67.59, 69.73, "I still call your name", "I still call your name", "なお君の名を呼ぶ", "日本晁卿辞帝都"),
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
                "Corrected from selected ACE XL Turbo seed 780824 using same-render small ASR, "
                "medium ASR cross-check, and the compact hook prompt. The active mul track is a "
                "phonetic performance layer; zh-Hans uses only original Li Bai source lines as requested."
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
        "title": "哭晁卿衡 · Moon Over The Blue Sea",
        "localizedTitles": {
            "zh-Hans": "哭晁卿衡 · 碧海明月",
            "en": "Moon Over The Blue Sea",
            "ja": "碧海の月",
        },
        "artist": "Musia",
        "description": "A mixed English, Japanese romaji, and Mandarin pinyin ACE-Step ocean elegy from Li Bai's original poem 哭晁卿衡.",
        "caption": "One sail leaves the Tang capital; the moon sinks into the blue sea and white clouds carry sorrow.",
        "duration": round(duration(SELECTED_AUDIO), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "哭晁卿衡 · Moon Over The Blue Sea - Fun Lazying Art",
            "description": "A Musia mixed-language Li Bai ocean elegy with corrected synced lyrics, pinyin, furigana, chords, and stems.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {
                "id": "cover",
                "label": "Moonlit sea cover",
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
                "id": "ku-chao-qing-heng-mixed",
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
            "key": "detected A minor / modal ocean elegy",
            "bpm": round(float(run_manifest.get("tempo_bpm", 143.5546875)), 3),
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
                    {
                        "code": "mul",
                        "label": "Mixed",
                        "nativeLabel": "Mixed",
                        "script": "Latn",
                        "features": ["active-vocal"],
                        "path": "lyrics/mixed-vocal/mul.json",
                    },
                    {
                        "code": "en",
                        "label": "English",
                        "nativeLabel": "English",
                        "script": "Latn",
                        "features": ["translation"],
                        "path": "lyrics/mixed-vocal/en.json",
                    },
                    {
                        "code": "ja",
                        "label": "Japanese",
                        "nativeLabel": "日本語",
                        "script": "Jpan",
                        "features": ["furigana", "translation"],
                        "path": "lyrics/mixed-vocal/ja.json",
                    },
                    {
                        "code": "zh-Hans",
                        "label": "Mandarin Chinese",
                        "nativeLabel": "中文",
                        "script": "Hans",
                        "features": ["pinyin", "source-anchor"],
                        "path": "lyrics/mixed-vocal/zh-Hans.json",
                    },
                ],
            }
        ],
        "timeline": {"unit": "seconds", "lines": timeline},
        "playback": {"defaultMode": "single"},
        "provenance": {
            "createdBy": "Musia",
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "audioSource": "ACE-Step 1.5 XL Turbo hook-led phonetic mixed route, seed 780824. Original-character and SFT sweeps were rejected for weak lyric recovery.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {
                "gate": "public-candidate",
                "note": "Phonetic mixed-language render. Usable melody/vocal structure; public Chinese track preserves Li Bai original lines only.",
            },
            "lyricCorrection": "Same-render small ASR plus medium ASR cross-check and prompt lyric. Unsung final hook lines after 69.73s are omitted from active timing.",
            "coverSource": str(COVER_SOURCE),
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
        "title": "哭晁卿衡 · Moon Over The Blue Sea",
        "artist": "Musia",
        "summary": "A mixed English, Japanese romaji, and Mandarin pinyin Li Bai ocean elegy with source-only Chinese poem anchors.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["mul", "en", "zh-Hans", "ja"],
        "tags": ["music", "multilingual", "Tang poetry", "Li Bai", "ACE-Step", "pinyin", "furigana", "chords"],
    }
    items = [existing for existing in catalog["items"] if existing.get("id") != MEDIA_ID]
    items.insert(0, item)
    catalog["items"] = items
    write_json(path, catalog)


def update_reference() -> None:
    reference = ROOT / "references/ku-chao-qing-heng-mixed-production-2026-07-08.md"
    existing = reference.read_text(encoding="utf-8") if reference.exists() else ""
    selected = "\n".join(
        [
            "",
            "## Selected Render",
            "",
            "- Route: ACE-Step 1.5 XL Turbo hook-led phonetic mixed route.",
            "- Seed: `780824`.",
            "- Selected audio: `data/creative_projects/ku-chao-qing-heng-mixed-20260708/selected/ku-chao-qing-heng-mixed-ace-xl-turbo-seed780824.mp3`.",
            f"- Public audio: `{PUBLIC_AUDIO}`.",
            "- Analysis: `data/runs/ku-chao-qing-heng-mixed-20260708-seed780824-analysis/`.",
            "- Website manifest: `website/data/songs/ku-chao-qing-heng-mixed/manifest.json`.",
            "",
            "Original-character route notes: the native CJK mixed sweep produced very weak lyric recovery. SFT hook comparison produced generic outro chatter. The selected Turbo hook route recovered the main pinyin/romaji/English shape best.",
            "",
            "Correction compromise: active `mul` lyrics are phonetic because that is what the selected audio sings. The `zh-Hans` track uses only original Li Bai poem lines as source anchors, not modern Chinese paraphrase.",
            "",
        ]
    )
    if "## Selected Render" in existing:
        existing = existing.split("## Selected Render", 1)[0].rstrip() + selected
    else:
        existing = existing.rstrip() + selected
    reference.write_text(existing, encoding="utf-8")


def main() -> None:
    ensure_audio()
    make_cover()
    write_media_item()
    update_catalog()
    update_reference()
    print(ROOT / "website/data/songs" / MEDIA_ID / "manifest.json")


if __name__ == "__main__":
    main()
