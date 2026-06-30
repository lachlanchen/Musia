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
MEDIA_ID = "meng-you-tian-mu"
PROJECT = ROOT / "data/creative_projects/meng-you-tian-mu-20260701"
SELECTED_WAV = PROJECT / "ace_outputs/zh/26269f27-43d6-35e3-9b9d-6b85f20477b9.wav"
ANALYSIS = ROOT / "data/runs/meng-you-tian-mu-20260701-20260701-011745-analysis"
PUBLIC_AUDIO_NAME = "meng-you-tian-mu-zh-Hans-ace-20260701.mp3"
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


def zh_pinyin_for(line_text: str, index: int, char: str) -> str:
    if not is_cjk(char):
        return ""
    if "天姥" in line_text and char == "姥":
        return "mu3"
    if line_text.startswith("安能") and char == "能":
        return "neng2"
    if line_text.startswith("列缺") and char == "缺":
        return "que1"
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
        ("l01", 12.18, 17.60, "海上烟涛，远道难求", "Sea mist and waves, a far road hard to find.", "海の煙る波、遠き道は求めがたい"),
        ("l02", 17.60, 23.00, "越人说天姥，云霞明灭在心头", "People of Yue speak of Tianmu; cloudlight flickers in my heart.", "越の人は天姥を語り、雲霞が胸に明滅する"),
        ("l03", 23.30, 29.30, "青云梯上，海日初升", "On the ladder of blue clouds, the sea sun begins to rise.", "青雲の梯に上れば、海の日が昇り始める"),
        ("l04", 29.86, 35.30, "天鸡一声，千岩都回声", "One cry of the heavenly rooster, and a thousand cliffs answer.", "天鶏の一声に、千の岩がこだまする"),
        ("l05", 35.30, 38.30, "梦过天姥，梦到云深处", "I dream past Tianmu, into the deep clouds.", "天姥を夢に越え、雲深き所へ至る"),
        ("l06", 38.82, 43.28, "霓为风马，万山为我开路", "Rainbow and wind become my horse; ten thousand mountains open my road.", "虹と風は我が馬となり、万山が道を開く"),
        ("l07", 43.28, 46.58, "梦过天姥，醒来仍不负", "I dream past Tianmu; waking, I still do not betray it.", "天姥を夢に越え、醒めてもなお裏切らない"),
        ("l08", 46.58, 49.34, "安能低眉，安能折腰", "How could I lower my brow, how could I bend my waist?", "どうして眉を伏せ、腰を折れようか"),
        ("l09", 49.34, 52.68, "换我开心颜", "If it costs me my free and happy face.", "それで私の晴れやかな顔を失うなら"),
        ("l10", 54.74, 57.90, "熊咆龙吟，震动岩泉", "Bears roar, dragons sing, shaking the rock springs.", "熊は咆え、龍は吟じ、岩泉を震わせる"),
        ("l11", 57.90, 60.48, "云青青欲雨", "Green-dark clouds are ready to rain.", "青々たる雲は雨を含む"),
        ("l12", 60.48, 63.50, "水烟漫过山巅", "Water smoke drifts over the mountain peak.", "水煙が山の頂を越えて広がる"),
        ("l13", 63.50, 66.02, "列缺霹雳，石门忽然开", "Lightning and thunder; the stone gate suddenly opens.", "稲妻と雷鳴、石門がたちまち開く"),
        ("l14", 66.02, 69.18, "日月照金台，仙人纷纷来", "Sun and moon light the golden terrace; immortals descend in waves.", "日月が金の台を照らし、仙人が次々と来る"),
        ("l15", 69.18, 73.12, "忽然魂动，长叹醒来", "Suddenly my soul trembles; with a long sigh I wake.", "ふと魂が震え、長く嘆いて目覚める"),
        ("l16", 73.12, 78.74, "枕席还在，烟霞已不在", "The pillow and mat remain; the mist and cloudlight are gone.", "枕席はまだあり、煙霞はもうない"),
        ("l17", 78.74, 82.86, "梦过天姥，梦到天地外", "I dream past Tianmu, beyond heaven and earth.", "天姥を夢に越え、天地の外へ至る"),
        ("l18", 82.86, 86.16, "世间万事，东流入海", "All worldly things flow east into the sea.", "世の万事は東へ流れて海へ入る"),
        ("l19", 86.16, 88.36, "我心不尘埃", "My heart will not become dust.", "我が心は塵にはならない"),
        ("l20", 88.36, 91.74, "梦过天姥，白鹿青崖在", "I dream past Tianmu; the white deer waits by green cliffs.", "天姥を夢に越え、白鹿は青崖にいる"),
        ("l21", 91.74, 94.22, "安能低眉，安能折腰", "How could I lower my brow, how could I bend my waist?", "どうして眉を伏せ、腰を折れようか"),
        ("l22", 94.22, 97.10, "让我不得开心颜", "If it leaves me unable to smile freely.", "それで心から笑えなくなるなら"),
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
                "Candidate 1 selected because it preserved the poem's dream, thunder, immortals, and freedom arc. "
                "Active Mandarin lines were corrected using large-v3 ASR, selected/vocal-stem small and medium ASR, "
                "and no-VAD passes. Sound-close intended phrases such as 天姥, 安能低眉, and 安能折腰 are preserved; "
                "unsupported skipped prompt lines are omitted."
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
        "title": "梦游天姥",
        "localizedTitles": {
            "zh-Hans": "梦游天姥",
            "en": "Dreaming of Tianmu",
            "ja": "夢遊天姥",
        },
        "artist": "Musia",
        "description": "An ACE-Step Mandarin normal-song adaptation inspired by Li Bai's 梦游天姥吟留别, with ASR-corrected trilingual lyrics.",
        "caption": "A moonlit dream mountain opens into thunder, immortals, and the freedom to never bow.",
        "duration": round(duration(SELECTED_WAV), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "梦游天姥 - Fun Lazying Art",
            "description": "A Musia Mandarin normal-song adaptation of Li Bai's dream journey to Mount Tianmu.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "梦游天姥 cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": "meng-you-tian-mu-zh",
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
            "key": "D minor requested / detected Am-F-Bb-Dm centered progression",
            "bpm": round(float(run_manifest.get("tempo_bpm", 172.265625)), 3),
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
            "audioSource": "ACE-Step 1.5 XL Turbo candidate 1 from the 梦游天姥 normal-song adaptation workflow.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {"selectedCandidate": 1, "largeV3Overlap": 0.08256880733944955, "vocalStemSmallOverlap": 0.5825688073394495},
            "lyricCorrection": "Corrected from selected-audio large-v3 ASR plus vocal-stem small/medium and no-VAD ASR. The active lyric follows the audible structure, with sound-close intended classical phrases restored.",
            "coverSource": "/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/ig_0ff40dcbca0516cf016a43fbcd8d548191a22a32fd11247aec.png",
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
        "title": "梦游天姥",
        "artist": "Musia",
        "summary": "A cinematic ACE-Step Mandarin normal-song adaptation of Li Bai's dream journey to Mount Tianmu, with corrected trilingual lyrics, pinyin, furigana, and chord timing.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "Li Bai", "Tang poetry", "Mandarin", "ACE-Step", "xianxia", "pinyin", "furigana"],
    }
    items = [item for item in catalog["items"] if item.get("id") != MEDIA_ID]
    insert_at = next((index for index, item in enumerate(items) if item.get("id") == "qiang-jin-jiu-normal-song"), 3)
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
