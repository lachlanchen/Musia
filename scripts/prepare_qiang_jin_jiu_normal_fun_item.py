#!/usr/bin/env python3
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
MEDIA_ID = "qiang-jin-jiu-normal-song"
PROJECT = ROOT / "data/creative_projects/qiang-jin-jiu-normal-song-20260701"
SELECTED_WAV = PROJECT / "ace_outputs/zh/6efc268a-3338-d611-f6ac-4d2b60384f49.wav"
ANALYSIS = ROOT / "data/runs/qiang-jin-jiu-normal-song-20260701-20260701-004055-analysis"
PUBLIC_AUDIO_NAME = "qiang-jin-jiu-normal-song-zh-Hans-ace-20260701.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"

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


def zh_pinyin_for(line_text: str, index: int, char: str) -> str:
    if not is_cjk(char):
        return ""
    if line_text.startswith("将进酒") and char == "将" and index == 0:
        return "qiang1"
    if line_text.startswith("白发") and char == "发":
        return "fa4"
    if char == "材":
        return "cai2"
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
            reading = zh_pinyin_for(line["text"], index, part)
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
        ("l01", 13.74, 15.78, "黄河从天来", "The Yellow River comes from the sky.", "黄河は天から来る"),
        ("l02", 15.78, 17.74, "月光落满台", "Moonlight fills the terrace.", "月光が舞台を満たす"),
        ("l03", 17.74, 19.28, "一杯敬风雪", "One cup to wind and snow.", "一杯を風雪へ捧げる"),
        ("l04", 19.28, 20.82, "一杯敬尘埃", "One cup to dust and earth.", "一杯を塵埃へ捧げる"),
        ("l05", 20.82, 22.38, "白发照明镜", "White hair shines in the bright mirror.", "白髪が明鏡に映る"),
        ("l06", 22.38, 23.94, "少年还在怀", "The young heart is still in my chest.", "少年の心は今も胸にある"),
        ("l07", 23.94, 26.17, "别问归不归", "Do not ask whether I return.", "帰るかどうかは問わないで"),
        ("l08", 26.17, 28.4, "今夜花正开", "Tonight the flowers are opening.", "今夜、花が咲いている"),
        ("l09", 28.4, 31.41, "人生有几回", "How many chances does life give?", "人生に何度こんな時があるだろう"),
        ("l10", 31.41, 34.42, "敢把梦点燃", "Dare to set the dream alight.", "夢を燃やす勇気を持つ"),
        ("l11", 34.42, 37.13, "千金散尽后", "After all the gold is spent.", "千金を散じ尽くした後も"),
        ("l12", 37.13, 39.84, "我仍向云山", "I still turn toward clouded mountains.", "なお雲の山へ向かう"),
        ("l13", 39.84, 42.7, "将进酒，杯莫停", "Bring in the wine; let the cup not stop.", "酒を勧めよう、杯を止めるな"),
        ("l14", 42.7, 46.48, "让长风吹醒我的心", "Let the long wind wake my heart.", "長風よ、私の心を吹き覚ませ"),
        ("l15", 46.48, 48.96, "天生我材必有用", "Heaven made my gifts for a purpose.", "天が授けた才には必ず用がある"),
        ("l16", 48.96, 53.38, "一身孤勇也多情", "Alone and brave, yet full of feeling.", "孤勇を抱きながら情も深い"),
        ("l17", 53.38, 56.44, "钟鼓不必贵", "Bells and drums need not be prized.", "鐘鼓を貴ぶ必要はない"),
        ("l18", 56.44, 59.68, "明月最慷慨", "The bright moon is the most generous.", "明月こそ最もおおらかだ"),
        ("l19", 59.68, 61.4, "圣贤多寂寞", "Sages are often lonely.", "聖賢は多く寂しい"),
        ("l20", 61.4, 65.86, "饮者留名来", "Drinkers leave their names behind.", "飲む者が名を残す"),
        ("l21", 65.86, 68.44, "若天地问我", "If heaven and earth ask me.", "もし天地が私に問うなら"),
        ("l22", 69.16, 71.94, "为何还不醒", "Why I still do not wake.", "なぜまだ醒めないのかと"),
        ("l23", 71.94, 74.28, "我笑说人间", "I smile and speak of the human world.", "私は笑って人の世を語る"),
        ("l24", 74.28, 77.6, "有你便有星", "With you, there are stars.", "君がいれば星がある"),
        ("l25", 77.6, 80.44, "将进酒，杯莫停", "Bring in the wine; let the cup not stop.", "酒を勧めよう、杯を止めるな"),
        ("l26", 80.44, 83.9, "让黄河奔过我胸襟", "Let the Yellow River surge through my chest.", "黄河よ、胸の内を駆け抜けろ"),
        ("l27", 83.9, 86.3, "天生我材必有用", "Heaven made my gifts for a purpose.", "天が授けた才には必ず用がある"),
        ("l28", 86.3, 89.1, "千回百转", "Through a thousand turns.", "幾度も巡り"),
        ("l29", 89.1, 93.48, "仍相信", "Still I believe.", "それでも信じている"),
        ("l30", 93.48, 96.46, "杯莫停", "Let the cup not stop.", "杯を止めるな"),
        ("l31", 96.46, 99.44, "杯莫停", "Let the cup not stop.", "杯を止めるな"),
        ("l32", 99.44, 102.91, "愿此心", "May this heart.", "この心が"),
        ("l33", 102.91, 106.38, "永不平", "Never be still.", "いつまでも鎮まらぬように"),
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
                "Normal-song candidate 1 corrected from same-audio large-v3 ASR, selected/vocal-stem "
                "small and medium ASR, no-VAD passes, and the intended adapted lyric. Prompt sections "
                "that the render skipped or garbled beyond recoverability are not published as sung text."
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
    chords = []
    for item in raw:
        chords.append(
            {
                "start": round(float(item["start"]), 3),
                "end": round(float(item["end"]), 3),
                "name": item.get("chord") or item.get("name") or "N.C.",
                "degree": "",
            }
        )
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


def copy_cover() -> str:
    source = ROOT / "website/assets/covers/qiang-jin-jiu-16x9.png"
    target = ROOT / f"website/assets/covers/{MEDIA_ID}-16x9.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.exists():
        shutil.copy2(source, target)
    elif not target.exists():
        raise FileNotFoundError(f"Missing cover source: {source}")
    return f"assets/covers/{MEDIA_ID}-16x9.png"


def write_media_item() -> None:
    media_dir = ROOT / "website/data/songs" / MEDIA_ID
    cover = copy_cover()
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
        "title": "将进酒",
        "localizedTitles": {
            "zh-Hans": "将进酒",
            "en": "Bring In the Wine",
            "ja": "将進酒",
        },
        "artist": "Musia",
        "description": "An ACE-Step Mandarin normal-song adaptation inspired by Li Bai's 将进酒, corrected against the selected audio's own ASR evidence.",
        "caption": "Heroic wine, Yellow River moonlight, and a heart that refuses to go quiet.",
        "duration": round(duration(SELECTED_WAV), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "将进酒 - Fun Lazying Art",
            "description": "A Musia Mandarin normal-song adaptation of 将进酒 with corrected trilingual lyrics.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": cover,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "将进酒 cover", "role": "cover", "src": cover, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": cover, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": "qiang-jin-jiu-normal-zh",
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
            "key": "D minor requested / detected Dm-F-Am centered progression",
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
            "audioSource": "ACE-Step 1.5 XL Turbo candidate 1 from the normal-song 将进酒 adaptation workflow.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {"asrOverlap": 0.49377593360995853, "gate": "pass"},
            "lyricCorrection": "Corrected from same-audio large-v3 ASR plus selected/vocal-stem small and medium no-VAD ASR. The active lyrics follow the audible structure of the selected render, not the full prompt.",
            "coverSource": cover,
            "publicAudio": PUBLIC_AUDIO_NAME,
        },
        "artifacts": [],
    }
    write_json(media_dir / "manifest.json", manifest)


def update_catalog() -> None:
    path = ROOT / "website/data/catalog.json"
    catalog = read_json(path)
    new_item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "将进酒",
        "artist": "Musia",
        "summary": "The normal-song ACE-Step Mandarin adaptation of Li Bai's 将进酒, with corrected trilingual lyrics, pinyin, furigana, and chord timing.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": f"assets/covers/{MEDIA_ID}-16x9.png",
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "Li Bai", "Tang poetry", "Mandarin", "ACE-Step", "normal-song", "pinyin", "furigana"],
    }
    items = [item for item in catalog["items"] if item.get("id") != MEDIA_ID]
    insert_at = next((index for index, item in enumerate(items) if item.get("id") == "qiang-jin-jiu"), 3)
    items.insert(insert_at, new_item)
    catalog["items"] = items
    write_json(path, catalog)


def main() -> None:
    ensure_audio()
    write_media_item()
    update_catalog()
    print(ROOT / "website/data/songs" / MEDIA_ID / "manifest.json")


if __name__ == "__main__":
    main()
