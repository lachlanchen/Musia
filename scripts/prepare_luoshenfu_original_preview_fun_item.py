#!/usr/bin/env python3
"""Prepare the formal Fun release for 洛神赋 · 原文选段.

The filename is retained for compatibility with the earlier preview workflow.
"""

from __future__ import annotations

import filecmp
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pykakasi
from pypinyin import Style, pinyin


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
MEDIA_ID = "luoshenfu-original-excerpt-preview"
PROJECT = ROOT / "data/creative_projects/luoshenfu-original-excerpt-preview-20260729"
ANALYSIS_SOURCE = PROJECT / "analysis/source-seed729403"
ANALYSIS_V2 = ROOT / "data/runs/luoshenfu-pronunciation-v2-seed729403-analysis"
AUDIO_SOURCE = PROJECT / "selected/luoshenfu-original-excerpt-seed729403.mp3"
AUDIO_V2 = PROJECT / "selected/luoshenfu-original-excerpt-pronunciation-v2-seed729403.mp3"
PUBLIC_NAME_SOURCE = (
    "luoshenfu-original-excerpt-zh-Hans-ace-xl-turbo-seed729403-20260729.mp3"
)
PUBLIC_NAME_V2 = (
    "luoshenfu-original-excerpt-pronunciation-v2-zh-Hans-"
    "ace-xl-turbo-seed729403-20260730.mp3"
)
PUBLIC_BASE = "https://lazyingart.github.io/MusiaSongs/audio/"
COVER = "assets/covers/luoshenfu-original-excerpt-preview-16x9.png"
COVER_SOURCE = (
    "/home/lachlan/.codex/generated_images/"
    "019f0842-25ba-7bd2-9d4b-0b1c60d8a951/call_3TfPoLAlsEjwQn2r9DJ11qDM.png"
)


ROWS = [
    (14.84, 17.92, "秾纤得衷", "Fullness and grace in perfect balance.", "豊かさも細さもほどよく"),
    (17.92, 21.16, "修短合度", "Her stature meets the ideal measure.", "背丈も理想の姿にかなう"),
    (21.16, 23.49, "肩若削成", "Shoulders shaped as if carved.", "肩は彫り出したよう"),
    (23.49, 25.82, "腰如约素", "A waist like bundled white silk.", "腰は白絹を束ねたよう"),
    (25.82, 27.49, "延颈秀项", "A long neck and graceful nape.", "長い首とうるわしいうなじ"),
    (27.49, 29.16, "皓质呈露", "Luminous skin is revealed.", "白く輝く肌があらわになる"),
    (29.82, 31.18, "飘忽若神", "She drifts as if divine.", "神のようにふわりと漂い"),
    (31.18, 32.54, "体迅飞凫", "Swift as a flying waterbird.", "飛ぶ水鳥のようにすばやい"),
    (32.54, 34.24, "云髻峨峨", "Her cloudlike coiffure rises high.", "雲のような髪は高く結われ"),
    (34.24, 35.94, "修眉联娟", "Long brows curve delicately.", "長い眉は美しく弧を描く"),
    (35.94, 37.62, "丹唇外朗", "Vermilion lips shine.", "朱の唇は明るく輝き"),
    (37.62, 39.30, "皓齿内鲜", "Bright teeth gleam within.", "白い歯は内にきらめく"),
    (39.30, 40.96, "明眸善睐", "Clear eyes glance with grace.", "澄んだ瞳は美しく流れ"),
    (40.96, 42.62, "靥辅承权", "Dimples rest beside her cheeks.", "えくぼは頬に寄り添う"),
    (42.62, 44.62, "瑰姿艳逸", "Rare beauty, radiant and free.", "稀なる姿は華やかで"),
    (44.62, 46.62, "仪静体闲", "Serene in bearing and unhurried in form.", "佇まいは静かで優雅"),
    (47.92, 50.35, "翩若惊鸿", "Light as a startled swan.", "舞う姿は驚く鴻のよう"),
    (50.35, 52.80, "婉若游龙", "Graceful as a wandering dragon.", "しなやかさは遊ぶ龍のよう"),
    (52.80, 56.02, "荣曜秋菊", "Radiant as autumn chrysanthemums.", "秋の菊のように輝き"),
    (56.02, 59.24, "华茂春松", "Flourishing as spring pines.", "春の松のように華やぐ"),
    (59.80, 67.60, "髣髴兮若轻云之蔽月", "Like light cloud veiling the moon.", "淡い雲が月を覆うよう"),
    (67.60, 71.00, "飘飖兮若流风之回雪", "Like flowing wind returning the snow.", "流れる風が雪を舞い返すよう"),
    (71.00, 72.85, "翩若惊鸿", "Light as a startled swan.", "舞う姿は驚く鴻のよう"),
    (72.85, 74.70, "婉若游龙", "Graceful as a wandering dragon.", "しなやかさは遊ぶ龍のよう"),
    (74.70, 76.96, "荣曜秋菊", "Radiant as autumn chrysanthemums.", "秋の菊のように輝き"),
    (76.96, 79.22, "华茂春松", "Flourishing as spring pines.", "春の松のように華やぐ"),
    (81.38, 84.40, "披罗衣之璀粲兮", "She wears shimmering gauze.", "きらめく薄絹をまとい"),
    (84.40, 87.56, "珥瑶碧之华琚", "Jade earrings and splendid pendants.", "碧玉の耳飾りを揺らす"),
    (87.56, 89.58, "戴金翠之首饰", "Gold and kingfisher adorn her hair.", "金と翠の髪飾りを戴き"),
    (89.58, 91.54, "缀明珠以耀躯", "Bright pearls illuminate her form.", "明珠がその姿を照らす"),
    (91.54, 93.44, "践远游之文履", "Her feet tread patterned Far-Wanderer shoes.", "文様ある遠遊の履を踏み"),
    (93.44, 95.06, "曳雾绡之轻裾", "Mist-silk hems trail lightly.", "霧の薄絹の裾を引く"),
    (95.06, 96.36, "芳泽无加", "No fragrance need be added.", "香りを添える必要もなく"),
    (96.36, 99.56, "铅华弗御", "No powdered ornament touches her.", "白粉の装いさえ用いない"),
    (100.52, 103.22, "翩若惊鸿", "Light as a startled swan.", "舞う姿は驚く鴻のよう"),
    (103.22, 106.04, "婉若游龙", "Graceful as a wandering dragon.", "しなやかさは遊ぶ龍のよう"),
    (106.04, 109.82, "荣曜秋菊", "Radiant as autumn chrysanthemums.", "秋の菊のように輝き"),
    (109.82, 113.60, "华茂春松", "Flourishing as spring pines.", "春の松のように華やぐ"),
    (113.60, 117.82, "髣髴兮若轻云之蔽月", "Like light cloud veiling the moon.", "淡い雲が月を覆うよう"),
    (117.82, 123.58, "飘飖兮若流风之回雪", "Like flowing wind returning the snow.", "流れる風が雪を舞い返すよう"),
]

# Candidate-specific timing for the same-seed pronunciation-control render.
# Boundaries combine full-mix and separated-vocal large-v3 word anchors with
# MOSS-Music's independent structure pass. The final extra 飘飖兮 is audible
# and therefore remains as its own public line.
ROWS_V2 = [
    (15.86, 18.92, "秾纤得衷", "Fullness and grace in perfect balance.", "豊かさも細さもほどよく"),
    (19.15, 21.61, "修短合度", "Her stature meets the ideal measure.", "背丈も理想の姿にかなう"),
    (22.53, 24.07, "肩若削成", "Shoulders shaped as if carved.", "肩は彫り出したよう"),
    (24.07, 25.77, "腰如约素", "A waist like bundled white silk.", "腰は白絹を束ねたよう"),
    (25.77, 27.21, "延颈秀项", "A long neck and graceful nape.", "長い首とうるわしいうなじ"),
    (27.21, 29.17, "皓质呈露", "Luminous skin is revealed.", "白く輝く肌があらわになる"),
    (29.17, 30.83, "飘忽若神", "She drifts as if divine.", "神のようにふわりと漂い"),
    (30.83, 32.51, "体迅飞凫", "Swift as a flying waterbird.", "飛ぶ水鳥のようにすばやい"),
    (32.51, 34.13, "云髻峨峨", "Her cloudlike coiffure rises high.", "雲のような髪は高く結われ"),
    (34.13, 35.85, "修眉联娟", "Long brows curve delicately.", "長い眉は美しく弧を描く"),
    (35.85, 37.53, "丹唇外朗", "Vermilion lips shine.", "朱の唇は明るく輝き"),
    (37.53, 39.19, "皓齿内鲜", "Bright teeth gleam within.", "白い歯は内にきらめく"),
    (39.19, 40.83, "明眸善睐", "Clear eyes glance with grace.", "澄んだ瞳は美しく流れ"),
    (40.83, 42.57, "靥辅承权", "Dimples rest beside her cheeks.", "えくぼは頬に寄り添う"),
    (42.57, 44.57, "瑰姿艳逸", "Rare beauty, radiant and free.", "稀なる姿は華やかで"),
    (44.57, 46.59, "仪静体闲", "Serene in bearing and unhurried in form.", "佇まいは静かで優雅"),
    (47.89, 49.21, "翩若惊鸿", "Light as a startled swan.", "舞う姿は驚く鴻のよう"),
    (49.64, 52.58, "婉若游龙", "Graceful as a wandering dragon.", "しなやかさは遊ぶ龍のよう"),
    (52.83, 54.21, "荣曜秋菊", "Radiant as autumn chrysanthemums.", "秋の菊のように輝き"),
    (54.21, 55.93, "华茂春松", "Flourishing as spring pines.", "春の松のように華やぐ"),
    (64.20, 67.75, "髣髴兮若轻云之蔽月", "Like light cloud veiling the moon.", "淡い雲が月を覆うよう"),
    (67.75, 70.93, "飘飖兮若流风之回雪", "Like flowing wind returning the snow.", "流れる風が雪を舞い返すよう"),
    (70.93, 72.83, "翩若惊鸿", "Light as a startled swan.", "舞う姿は驚く鴻のよう"),
    (72.83, 74.57, "婉若游龙", "Graceful as a wandering dragon.", "しなやかさは遊ぶ龍のよう"),
    (74.57, 76.39, "荣曜秋菊", "Radiant as autumn chrysanthemums.", "秋の菊のように輝き"),
    (76.97, 79.29, "华茂春松", "Flourishing as spring pines.", "春の松のように華やぐ"),
    (81.35, 84.21, "披罗衣之璀粲兮", "She wears shimmering gauze.", "きらめく薄絹をまとい"),
    (84.21, 87.57, "珥瑶碧之华琚", "Jade earrings and splendid pendants.", "碧玉の耳飾りを揺らす"),
    (87.57, 89.97, "戴金翠之首饰", "Gold and kingfisher adorn her hair.", "金と翠の髪飾りを戴き"),
    (89.97, 91.63, "缀明珠以耀躯", "Bright pearls illuminate her form.", "明珠がその姿を照らす"),
    (91.63, 93.29, "践远游之文履", "Her feet tread patterned Far-Wanderer shoes.", "文様ある遠遊の履を踏み"),
    (93.29, 95.07, "曳雾绡之轻裾", "Mist-silk hems trail lightly.", "霧の薄絹の裾を引く"),
    (95.07, 96.57, "芳泽无加", "No fragrance need be added.", "香りを添える必要もなく"),
    (96.57, 98.43, "铅华弗御", "No powdered ornament touches her.", "白粉の装いさえ用いない"),
    (101.02, 104.07, "翩若惊鸿", "Light as a startled swan.", "舞う姿は驚く鴻のよう"),
    (104.07, 106.32, "婉若游龙", "Graceful as a wandering dragon.", "しなやかさは遊ぶ龍のよう"),
    (106.32, 110.20, "荣曜秋菊", "Radiant as autumn chrysanthemums.", "秋の菊のように輝き"),
    (110.20, 114.07, "华茂春松", "Flourishing as spring pines.", "春の松のように華やぐ"),
    (114.22, 117.80, "髣髴兮若轻云之蔽月", "Like light cloud veiling the moon.", "淡い雲が月を覆うよう"),
    (117.80, 119.92, "飘飖兮", "She drifts and sways.", "ひらひらと揺らめき"),
    (121.54, 126.74, "飘飖兮若流风之回雪", "Like flowing wind returning the snow.", "流れる風が雪を舞い返すよう"),
]

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

PINYIN_OVERRIDES = {
    "秾": "nong2",
    "纤": "xian1",
    "得": "de2",
    "削": "xue1",
    "约": "yue1",
    "露": "lu4",
    "凫": "fu2",
    "鲜": "xian1",
    "靥": "ye4",
    "曜": "yao4",
    "髣": "fang3",
    "髴": "fu2",
    "飖": "yao2",
    "珥": "er3",
    "琚": "ju1",
    "绡": "xiao1",
    "裾": "ju1",
    "铅": "qian1",
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


def zh_reading(char: str) -> str:
    if char in PINYIN_OVERRIDES:
        return PINYIN_OVERRIDES[char]
    if not is_cjk(char):
        return ""
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
            reading = zh_reading(part)
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


def build_tracks(rows: list[tuple[float, float, str, str, str]]) -> dict[str, list[dict[str, Any]]]:
    tracks = {code: [] for code in LANGUAGES}
    for index, (start, end, zh, en, ja) in enumerate(rows, 1):
        line_id = f"l{index:02d}"
        tracks["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans"))
        tracks["en"].append(make_line(line_id, start, end, en, "en"))
        tracks["ja"].append(make_line(line_id, start, end, ja, "ja"))
    return tracks


def track_document(
    code: str,
    lines: list[dict[str, Any]],
    vocal_set: str,
    correction: str,
) -> dict[str, Any]:
    return {
        "schema": "fun.lazying.media.text-track.v1",
        "version": 1,
        "mediaId": MEDIA_ID,
        "language": LANGUAGES[code],
        "lines": lines,
        "provenance": {
            "vocalSet": vocal_set,
            "releaseStage": "formal-release",
            "correction": correction,
        },
    }


def load_musical(analysis: Path, bpm: float) -> dict[str, Any]:
    chord_data = read_json(analysis / "analysis/chords.json").get("chords", [])
    beat_data = read_json(analysis / "analysis/beats.json").get("beats", [])
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
        {"index": int(item.get("index", index)), "time": round(float(item["time"]), 3)}
        for index, item in enumerate(beat_data)
    ]
    return {
        "key": "D minor requested / Dm-centered analysis",
        "bpm": bpm,
        "timeSignature": "4/4",
        "chords": chords,
        "beats": beats,
        "chordSource": "Musia analysis-grade chord inference from this exact render",
        "beatSource": "Musia beat analysis from this exact render",
    }


def ensure_public_audio() -> None:
    pairs = (
        (AUDIO_SOURCE, PUBLIC_NAME_SOURCE),
        (AUDIO_V2, PUBLIC_NAME_V2),
    )
    changed = False
    for source, public_name in pairs:
        if not source.is_file():
            raise FileNotFoundError(source)
        target = SONGS / "audio" / public_name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or not filecmp.cmp(source, target, shallow=False):
            shutil.copy2(source, target)
            changed = True
    if changed:
        subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def write_media_item() -> None:
    cover_path = ROOT / "website" / COVER
    if not cover_path.is_file():
        raise FileNotFoundError(cover_path)

    tracks = build_tracks(ROWS)
    tracks_v2 = build_tracks(ROWS_V2)
    media_dir = ROOT / "website/data/songs" / MEDIA_ID
    source_correction = (
        "Corrected from the source lyric, separated-vocal and full-mix "
        "faster-whisper large-v3 normal/no-VAD passes, and MOSS-Music blind "
        "transcription. All source lines are accounted for; sound-close ASR "
        "substitutions retain Cao Zhi's verified text."
    )
    v2_correction = (
        "Corrected independently from the pronunciation-control render using "
        "full-mix and separated-vocal faster-whisper large-v3 normal/no-VAD "
        "passes plus MOSS-Music blind transcription. Public spelling restores "
        "Cao Zhi's source where the sound remains close; the audible extra final "
        "飘飖兮 repetition is retained."
    )
    for code, lines in tracks.items():
        write_json(
            media_dir / "lyrics/zh-vocal" / f"{code}.json",
            track_document(code, lines, "zh-vocal", source_correction),
        )
    for code, lines in tracks_v2.items():
        write_json(
            media_dir / "lyrics/pronunciation-v2" / f"{code}.json",
            track_document(code, lines, "pronunciation-v2", v2_correction),
        )

    musical = load_musical(ANALYSIS_SOURCE, 71.777)
    musical_v2 = load_musical(ANALYSIS_V2, 71.777)
    audio_asset = {
        "id": "luoshenfu-original-zh",
        "label": "Source A",
        "selectorLabel": "原字首版",
        "role": "vocal",
        "languageCode": "zh-Hans",
        "languageLabel": "中文 · 原字首版",
        "lyricSetId": "zh-vocal",
        "src": PUBLIC_BASE + PUBLIC_NAME_SOURCE,
        "mime": "audio/mpeg",
        "musical": musical,
    }
    audio_asset_v2 = {
        "id": "luoshenfu-pronunciation-v2",
        "label": "Pronunciation V2",
        "selectorLabel": "读音优化 V2",
        "role": "vocal",
        "languageCode": "zh-Hans",
        "languageLabel": "中文 · 读音优化 V2",
        "lyricSetId": "pronunciation-v2",
        "src": PUBLIC_BASE + PUBLIC_NAME_V2,
        "mime": "audio/mpeg",
        "musical": musical_v2,
    }
    timeline = [
        {"id": line["id"], "start": line["start"], "end": line["end"], "text": line["text"]}
        for line in tracks_v2["zh-Hans"]
    ]
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "洛神赋 · 原文选段",
        "localizedTitles": {
            "zh-Hans": "洛神赋 · 原文选段",
            "en": "Luoshen Fu · Original Excerpt",
            "ja": "洛神賦・原文抄",
        },
        "artist": "Musia",
        "description": (
            "Cao Zhi's original Luoshenfu lines carried by two luminous, "
            "cinematic Mandarin performances."
        ),
        "caption": "Light cloud veils the moon; flowing wind turns the returning snow.",
        "duration": 136.0,
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "洛神赋 · 原文选段 - Musia",
            "description": "An original cinematic Mandarin setting of selected lines from Cao Zhi's Luoshenfu.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {
                "id": "cover",
                "label": "洛神赋 original excerpt cover",
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
            "primaryAudio": audio_asset_v2,
            "alternateAudio": [audio_asset],
        },
        "musical": musical_v2,
        "textTracks": [],
        "lyricSets": [
            {
                "id": "zh-vocal",
                "label": "Source A",
                "languageCode": "zh-Hans",
                "tracks": [
                    {
                        "code": "zh-Hans",
                        "label": "Mandarin Chinese",
                        "nativeLabel": "中文",
                        "script": "Hans",
                        "features": ["active-vocal", "pinyin", "word-highlight"],
                        "path": "lyrics/zh-vocal/zh-Hans.json",
                    },
                    {
                        "code": "en",
                        "label": "English",
                        "nativeLabel": "English",
                        "script": "Latn",
                        "features": ["translation", "rough-highlight"],
                        "path": "lyrics/zh-vocal/en.json",
                    },
                    {
                        "code": "ja",
                        "label": "Japanese",
                        "nativeLabel": "日本語",
                        "script": "Jpan",
                        "features": ["translation", "furigana", "rough-highlight"],
                        "path": "lyrics/zh-vocal/ja.json",
                    },
                ],
            },
            {
                "id": "pronunciation-v2",
                "label": "Pronunciation V2",
                "languageCode": "zh-Hans",
                "tracks": [
                    {
                        "code": "zh-Hans",
                        "label": "Mandarin Chinese",
                        "nativeLabel": "中文",
                        "script": "Hans",
                        "features": ["active-vocal", "pinyin", "word-highlight"],
                        "path": "lyrics/pronunciation-v2/zh-Hans.json",
                    },
                    {
                        "code": "en",
                        "label": "English",
                        "nativeLabel": "English",
                        "script": "Latn",
                        "features": ["translation", "rough-highlight"],
                        "path": "lyrics/pronunciation-v2/en.json",
                    },
                    {
                        "code": "ja",
                        "label": "Japanese",
                        "nativeLabel": "日本語",
                        "script": "Jpan",
                        "features": ["translation", "furigana", "rough-highlight"],
                        "path": "lyrics/pronunciation-v2/ja.json",
                    },
                ],
            }
        ],
        "timeline": {"unit": "seconds", "lines": timeline},
        "playback": {"defaultMode": "single"},
        "provenance": {
            "createdBy": "Musia",
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "audioSource": (
                "ACE-Step 1.5 XL Turbo same-seed A/B: exact-source Source A and "
                "selective private pronunciation-control V2, seed 729403."
            ),
            "analysisRuns": [
                str(ANALYSIS_SOURCE.relative_to(ROOT)),
                str(ANALYSIS_V2.relative_to(ROOT)),
            ],
            "sourceText": "Cao Zhi, 洛神赋; selected public-domain original lines.",
            "quality": {
                "gate": "formal-public-release",
                "candidateCount": 14,
                "health": "pass",
                "apex": {
                    "coherence": 2.915,
                    "musicality": 2.800,
                    "memorability": 2.839,
                    "clarity": 2.666,
                    "naturalness": 2.571,
                },
                "note": (
                    "Source A and Pronunciation V2 were selected from independent "
                    "four-candidate XL Turbo sweeps after signal health, APEX, "
                    "separated-vocal large-v3, no-VAD, and MOSS-Music review."
                ),
            },
            "lyricCorrection": (
                "Each audio asset owns an independent lyric set and timing map. "
                "Source-close recognition errors retain the original poem; V2 "
                "also retains its audible extra final 飘飖兮 repetition."
            ),
            "coverSource": COVER_SOURCE,
            "coverPrompt": (
                "Luoshui river through a luminous jade-and-silver celestial "
                "megastructure, light cloud veiling the moon, returning snow, "
                "and one small original robed figure crossing the water; no text."
            ),
            "publicAudio": [PUBLIC_NAME_SOURCE, PUBLIC_NAME_V2],
        },
    }
    write_json(media_dir / "manifest.json", manifest)

    catalog_path = ROOT / "website/data/catalog.json"
    catalog = read_json(catalog_path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "洛神赋 · 原文选段",
        "artist": "Musia",
        "summary": "Two cinematic Mandarin settings of selected original lines from Cao Zhi's Luoshenfu.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["zh-Hans", "en", "ja"],
        "tags": [
            "music",
            "Mandarin",
            "classical Chinese",
            "洛神赋",
            "曹植",
            "ACE-Step",
            "pinyin",
            "furigana",
            "chords",
        ],
    }
    catalog["items"] = [entry for entry in catalog.get("items", []) if entry.get("id") != MEDIA_ID]
    catalog["items"].insert(0, item)
    write_json(catalog_path, catalog)


def main() -> None:
    ensure_public_audio()
    write_media_item()
    print(f"https://fun.lazying.art/#{MEDIA_ID}")


if __name__ == "__main__":
    main()
