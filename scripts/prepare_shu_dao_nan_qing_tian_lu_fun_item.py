#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pykakasi
from pypinyin import Style, pinyin


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
MEDIA_ID = "shu-dao-nan-qing-tian-lu"
PROJECT = ROOT / "data/creative_projects/shu-dao-nan-original-song-20260701"
SELECTED_WAV = PROJECT / "selected/qing-tian-lu-zh-Hans-ace-20260701-trimmed.wav"
ANALYSIS = ROOT / "data/runs/shu-dao-nan-qing-tian-lu-20260701-analysis"
PUBLIC_AUDIO_NAME = "shu-dao-nan-qing-tian-lu-zh-Hans-ace-20260701.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/shu-dao-nan-qing-tian-lu-16x9.png"

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
    return [
        ("l01", 12.36, 14.72, "山风过肩", "Mountain wind crosses my shoulder.", "山風が肩を越える"),
        ("l02", 14.72, 18.18, "云在脚边", "Clouds are beside my feet.", "雲は足もとにある"),
        ("l03", 19.00, 21.70, "旧路弯弯", "The old road bends and bends.", "古い道は幾重にも曲がる"),
        ("l04", 21.70, 24.36, "看不见终点", "I cannot see the end.", "終わりは見えない"),
        ("l05", 25.00, 27.48, "有人说别走", "Someone says, do not go.", "誰かが行くなと言う"),
        ("l06", 27.48, 30.70, "前方太遥远", "The road ahead is too far.", "前方はあまりに遠い"),
        ("l07", 30.70, 36.62, "我把害怕放进心里面", "I put my fear inside my heart.", "怖さを胸の奥へしまう"),
        ("l08", 49.52, 52.10, "夜鸟飞远", "Night birds fly far away.", "夜の鳥が遠くへ飛ぶ"),
        ("l09", 52.10, 54.92, "月落桥边", "The moon falls beside the bridge.", "月は橋のほとりに落ちる"),
        ("l10", 55.80, 58.06, "照我向云间", "It lights me toward the clouds.", "それは私を雲の間へ照らす"),
        ("l11", 59.10, 61.06, "不是不怕", "It is not that I am unafraid.", "怖くないわけではない"),
        ("l12", 61.94, 64.14, "只想到天破", "I only think of breaking through the sky.", "ただ空を破ることを思う"),
        ("l13", 64.70, 67.24, "路再难也要走", "However hard the road is, I must walk.", "道がどれほど険しくても歩く"),
        ("l14", 67.78, 70.26, "眼中还有尽头", "There is still an end in sight.", "目にはまだ果てが見える"),
        ("l15", 70.26, 73.70, "心不要低头", "Heart, do not lower your head.", "心よ、うつむかないで"),
        ("l16", 74.28, 76.54, "黑夜被风吹散", "The night is scattered by the wind.", "夜は風に吹き散らされる"),
        ("l17", 76.54, 79.76, "梦越过山尽头", "The dream crosses beyond the mountain's end.", "夢は山の果てを越えていく"),
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
                "Active Mandarin lyrics corrected from trimmed full-mix large-v3 no-VAD ASR, "
                "cross-checked with the vocal stem and prompt lyric. The selected full mix was "
                "trimmed before a generated Amara outro. Stem-only credit hallucinations were not "
                "published because they were not recovered from the selected full mix."
            ),
        },
    }


def build_tracks() -> dict[str, list[dict[str, Any]]]:
    lines = {"zh-Hans": [], "en": [], "ja": []}
    for row in corrected_rows():
        line_id, start, end, zh, en, ja = row
        lines["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans"))
        lines["en"].append(make_line(line_id, start, end, en, "en"))
        lines["ja"].append(make_line(line_id, start, end, ja, "ja"))
    return lines


def load_chords() -> list[dict[str, Any]]:
    raw = read_json(ANALYSIS / "analysis/chords.json").get("chords", [])
    return [
        {
            "start": round(float(item["start"]), 3),
            "end": round(float(item["end"]), 3),
            "name": item.get("chord") or item.get("name") or "N.C.",
            "degree": "",
        }
        for item in raw
    ]


def ensure_audio() -> None:
    if not SELECTED_WAV.exists():
        raise FileNotFoundError(f"Missing selected WAV: {SELECTED_WAV}")
    target = SONGS / "audio" / PUBLIC_AUDIO_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(SELECTED_WAV),
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "320k",
            str(target),
        ],
        check=True,
    )
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def write_media_item() -> None:
    cover_path = ROOT / "website" / COVER
    if not cover_path.exists():
        raise FileNotFoundError(f"Missing cover: {cover_path}")
    media_dir = ROOT / "website/data/songs" / MEDIA_ID
    tracks = build_tracks()
    for code, lines in tracks.items():
        write_json(media_dir / "lyrics/zh-vocal" / f"{code}.json", track(code, lines))
    timeline = [{"id": line["id"], "start": line["start"], "end": line["end"], "text": line["text"]} for line in tracks["zh-Hans"]]
    run_manifest = read_json(ANALYSIS / "manifest.json")
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "晴天路",
        "localizedTitles": {"zh-Hans": "晴天路", "en": "Road to Clear Sky", "ja": "晴天への道"},
        "artist": "Musia",
        "description": "An original Mandarin Musia song inspired by 蜀道难: a hopeful clear-sky road through impossible mountains.",
        "caption": "A compact xianxia ballad about fear, cliffs, and walking until the night opens.",
        "duration": round(duration(SELECTED_WAV), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "晴天路 - Fun Lazying Art",
            "description": "An original Musia song inspired by 蜀道难, with corrected trilingual lyrics.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "晴天路 cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1672, "height": 941},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1672, "height": 941},
            "primaryAudio": {
                "id": "qing-tian-lu-zh",
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
            "key": "D minor requested / detected A-Dm-Bb centered progression",
            "bpm": round(float(run_manifest.get("tempo_bpm", 151.99908088235293)), 3),
            "timeSignature": "4/4",
            "chords": load_chords(),
        },
        "textTracks": [],
        "lyricSets": [
            {
                "id": "zh-vocal",
                "label": "中文 vocal",
                "languageCode": "zh-Hans",
                "tracks": [
                    {"code": "zh-Hans", "label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "features": ["pinyin", "active-vocal"], "path": "lyrics/zh-vocal/zh-Hans.json"},
                    {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn", "features": ["translation"], "path": "lyrics/zh-vocal/en.json"},
                    {"code": "ja", "label": "Japanese", "nativeLabel": "日本語", "script": "Jpan", "features": ["furigana", "translation"], "path": "lyrics/zh-vocal/ja.json"},
                ],
            }
        ],
        "timeline": {"unit": "seconds", "lines": timeline},
        "provenance": {
            "createdBy": "Musia",
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "audioSource": "ACE-Step 1.5 XL Turbo direct-clear seed 735601, trimmed at 84.5s to remove generated outro.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {"vocalStemLargeV3Overlap": 0.47770700636942676, "gate": "pass-with-correction"},
            "lyricCorrection": "Corrected from trimmed selected audio large-v3 no-VAD ASR, vocal stem ASR, and the intended direct-clear lyric.",
            "coverSource": "Generated 16:9 cover with Codex image generation; original saved under ~/.codex/generated_images.",
            "publicAudio": PUBLIC_AUDIO_NAME,
        },
        "artifacts": [],
    }
    write_json(media_dir / "manifest.json", manifest)


def update_catalog() -> None:
    path = ROOT / "website/data/catalog.json"
    catalog = read_json(path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "晴天路",
        "artist": "Musia",
        "summary": "An original Mandarin clear-sky road song inspired by 蜀道难, with ASR-corrected trilingual lyrics, pinyin, furigana, and chord timing.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "original", "Mandarin", "ACE-Step", "xianxia", "hope", "pinyin", "furigana"],
    }
    items = [existing for existing in catalog["items"] if existing.get("id") != MEDIA_ID]
    insert_at = next((index + 1 for index, existing in enumerate(items) if existing.get("id") == "shu-dao-nan"), 7)
    items.insert(insert_at, item)
    catalog["items"] = items
    write_json(path, catalog)


def main() -> None:
    ensure_audio()
    write_media_item()
    update_catalog()
    print(ROOT / "website/data/songs" / MEDIA_ID / "manifest.json")


if __name__ == "__main__":
    main()

