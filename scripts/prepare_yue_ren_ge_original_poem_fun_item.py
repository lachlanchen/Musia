#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any

import pykakasi
from pypinyin import Style, pinyin


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
MEDIA_ID = "yue-ren-ge-original-poem"
PROJECT = ROOT / "data/creative_projects/yue-ren-ge-original-poem-20260701"
SELECTED_WAV = PROJECT / "selected/yue-ren-ge-original-poem-zh-Hans-ace-20260701.wav"
ANALYSIS = ROOT / "data/runs/yue-ren-ge-original-poem-20260701-hook-analysis"
PUBLIC_AUDIO_NAME = "yue-ren-ge-original-poem-zh-Hans-ace-20260701.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/yue-ren-ge-original-poem-16x9.png"

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
    if char == "搴":
        return "qian1"
    if "追不着" in line_text and char == "着":
        return "zhao2"
    if "王子" in line_text and char == "子":
        return "zi3"
    if "被好" in line_text and char == "被":
        return "pi1"
    if char == "訾":
        return "zi3"
    if "心几烦" in line_text and char == "几":
        return "ji1"
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
    # Hook seed 736361 selected after XL SFT and XL Turbo comparisons. Text is
    # corrected against large-v3 full-mix ASR and the planned poem-only hook.
    # This public track uses a sound-close, context-smooth compromise where the
    # render clearly diverges from strict original text but still carries the
    # poem's emotional meaning.
    return [
        ("l01", 15.98, 18.38, "今夕何夕兮", "What night is this?", "今宵は何という夜か"),
        ("l02", 19.18, 21.64, "牵愁中流", "Longing is drawn through midstream.", "愁いを流れの中へ引いていく"),
        ("l03", 21.64, 25.18, "今日何日兮", "What day is this?", "今日は何という日か"),
        ("l04", 25.18, 28.42, "得遇望之王子", "I meet the prince I have longed for.", "憧れの王子に出会う"),
        ("l05", 32.07, 33.51, "山有木兮", "The mountain has trees.", "山には木があり"),
        ("l06", 33.51, 35.39, "木有枝", "The trees have branches.", "木には枝がある"),
        ("l07", 35.39, 37.87, "心爱君兮", "My heart loves you.", "心は君を愛している"),
        ("l08", 37.87, 40.53, "追不着", "Yet I cannot reach you.", "それでも届かない"),
        ("l09", 40.53, 44.56, "心爱君兮", "My heart loves you.", "心は君を愛している"),
        ("l10", 44.56, 51.08, "今夕何夕兮", "What night is this?", "今宵は何という夜か"),
        ("l11", 51.08, 54.48, "牵愁中流", "Longing is drawn through midstream.", "愁いを流れの中へ引いていく"),
        ("l12", 54.48, 57.96, "今日何日兮", "What day is this?", "今日は何という日か"),
        ("l13", 57.96, 61.32, "得与望之同舟", "To share this boat with the one I behold.", "見つめる人と同じ舟にいる"),
        ("l14", 61.32, 66.47, "蒙羞被好兮", "Ashamed, yet graced by favor.", "恥じながらも寵を受け"),
        ("l15", 66.47, 68.45, "不訾诟耻", "I do not count slander and shame.", "そしりも恥も数えない"),
        ("l16", 69.76, 73.24, "心急烦而不绝兮", "My heart is restless and cannot cease.", "心は焦がれて絶えず"),
        ("l17", 73.24, 75.18, "得知王子", "Because I have come to know the prince.", "王子を知ることができたから"),
        ("l18", 76.50, 78.44, "山有木兮", "The mountain has trees.", "山には木があり"),
        ("l19", 78.44, 80.14, "木有枝", "The trees have branches.", "木には枝がある"),
        ("l20", 80.14, 81.74, "心爱君兮", "My heart loves you.", "心は君を愛している"),
        ("l21", 81.74, 83.32, "追不着", "Yet I cannot reach you.", "それでも届かない"),
        ("l22", 83.32, 84.32, "山有木兮", "The mountain has trees.", "山には木があり"),
        ("l23", 84.32, 87.00, "木有枝", "The trees have branches.", "木には枝がある"),
        ("l24", 87.44, 88.68, "心爱君兮", "My heart loves you.", "心は君を愛している"),
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
                "ACE original-poem hook render selected from XL SFT, XL Turbo single-pass, sectioned, repeated, and hook candidates. "
                "Active Mandarin timing is based on large-v3 ASR from the selected full mix. This revision uses a sound-close, context-smooth lyric "
                "where the render diverges from strict source text: 心爱君兮 is kept because it is consistently audible and beautiful, 君不知 is displayed "
                "as 追不着 where ASR/listening indicate that phrase, and 搴舟中流 is softened to 牵愁中流 because the sung line is closer to 前愁/牵愁 than to the rare source character. "
                "The original 越人歌 remains the source and emotional frame, but the active website lyric follows the selected performance."
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
        "title": "越人歌 · 原诗版",
        "localizedTitles": {"zh-Hans": "越人歌 · 原诗版", "en": "Song of the Yue Boatman · Original Poem", "ja": "越人歌・原詩版"},
        "artist": "Musia",
        "description": "A Musia ACE-Step Mandarin 越人歌 setting with ASR-corrected, sound-close trilingual website lyrics.",
        "caption": "A moonlit boat, hidden longing, and the sung confession 山有木兮，心爱君兮.",
        "duration": round(duration(SELECTED_WAV), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "越人歌 · 原诗版 - Fun Lazying Art",
            "description": "Musia original-poem song version of 越人歌.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "越人歌 原诗版 cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1672, "height": 941},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1672, "height": 941},
            "primaryAudio": {
                "id": "yue-ren-ge-original-poem-zh",
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
            "key": "A minor requested / detected Am-centered progression",
            "bpm": round(float(run_manifest.get("tempo_bpm", 69.837)), 3),
            "timeSignature": "4/4",
            "chords": load_chords(),
        },
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
        "textTracks": [],
        "timeline": {"unit": "seconds", "lines": timeline},
        "artifacts": [],
        "provenance": {
            "createdBy": "Musia",
            "generationProject": "data/creative_projects/yue-ren-ge-original-poem-20260701",
            "audioSource": "ACE-Step 1.5 XL Turbo hook seed 736361, selected after XL SFT and XL Turbo comparisons.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {
                "xlSftInstalled": True,
                "selectedAudioLargeV3Overlap": 0.46296296296296297,
                "selectionReason": "Best practical balance of poem recovery and final-couplet hook clarity.",
                "gate": "selected-with-documented-classical-poem-imperfections",
            },
            "lyricCorrection": (
                "Corrected from selected full-mix large-v3 ASR and the poem-only hook prompt. The active lyric now uses a sound-close compromise "
                "where the render diverges from strict original text, while the production note documents the source poem and correction choices."
            ),
            "coverSource": "/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/ig_0b88aca6cc8e98f5016a4475905be88191ab258691b27b0dea.png",
            "publicAudio": PUBLIC_AUDIO_NAME,
        },
    }
    write_json(media_dir / "manifest.json", manifest)

    catalog_path = ROOT / "website/data/catalog.json"
    catalog = read_json(catalog_path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "越人歌 · 原诗版",
        "artist": "Musia",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "tags": ["song", "pre-qin", "classical-poetry", "ace", "original-poem", "mandarin", "river", "love-song"],
        "languages": ["zh-Hans", "en", "ja"],
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
