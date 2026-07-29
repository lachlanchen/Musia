#!/usr/bin/env python3
"""Prepare the unlisted Fun preview for 洛神赋 · 原文选段."""

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
MEDIA_ID = "luoshenfu-original-excerpt-preview"
PROJECT = ROOT / "data/creative_projects/luoshenfu-original-excerpt-preview-20260729"
ANALYSIS = PROJECT / "analysis/source-seed729403"
AUDIO = PROJECT / "selected/luoshenfu-original-excerpt-seed729403.mp3"
PUBLIC_NAME = "luoshenfu-original-excerpt-zh-Hans-ace-xl-turbo-seed729403-20260729.mp3"
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


def build_tracks() -> dict[str, list[dict[str, Any]]]:
    tracks = {code: [] for code in LANGUAGES}
    for index, (start, end, zh, en, ja) in enumerate(ROWS, 1):
        line_id = f"l{index:02d}"
        tracks["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans"))
        tracks["en"].append(make_line(line_id, start, end, en, "en"))
        tracks["ja"].append(make_line(line_id, start, end, ja, "ja"))
    return tracks


def track_document(code: str, lines: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "fun.lazying.media.text-track.v1",
        "version": 1,
        "mediaId": MEDIA_ID,
        "language": LANGUAGES[code],
        "lines": lines,
        "provenance": {
            "vocalSet": "zh-vocal",
            "releaseStage": "unlisted-preview",
            "correction": (
                "Corrected from the source lyric, separated-vocal and full-mix "
                "faster-whisper large-v3 normal/no-VAD passes, and MOSS-Music "
                "blind transcription. All source lines are accounted for; "
                "sound-close ASR substitutions retain Cao Zhi's verified text."
            ),
        },
    }


def load_musical() -> dict[str, Any]:
    chord_data = read_json(ANALYSIS / "analysis/chords.json").get("chords", [])
    beat_data = read_json(ANALYSIS / "analysis/beats.json").get("beats", [])
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
        "bpm": 71.777,
        "timeSignature": "4/4",
        "chords": chords,
        "beats": beats,
        "chordSource": "Musia analysis-grade chord inference from the selected render",
        "beatSource": "Musia beat analysis from the selected render",
    }


def ensure_public_audio() -> None:
    if not AUDIO.is_file():
        raise FileNotFoundError(AUDIO)
    target = SONGS / "audio" / PUBLIC_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(AUDIO, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def write_media_item() -> None:
    cover_path = ROOT / "website" / COVER
    if not cover_path.is_file():
        raise FileNotFoundError(cover_path)

    tracks = build_tracks()
    media_dir = ROOT / "website/data/songs" / MEDIA_ID
    for code, lines in tracks.items():
        write_json(media_dir / "lyrics/zh-vocal" / f"{code}.json", track_document(code, lines))

    musical = load_musical()
    audio_asset = {
        "id": "luoshenfu-original-zh",
        "label": "Original Text",
        "selectorLabel": "中文原文",
        "publicRoleLabel": "Preview",
        "role": "vocal",
        "languageCode": "zh-Hans",
        "languageLabel": "中文",
        "lyricSetId": "zh-vocal",
        "src": PUBLIC_BASE + PUBLIC_NAME,
        "mime": "audio/mpeg",
        "musical": musical,
    }
    timeline = [
        {"id": line["id"], "start": line["start"], "end": line["end"], "text": line["text"]}
        for line in tracks["zh-Hans"]
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
        "description": "Cao Zhi's original Luoshenfu lines carried by a new luminous, cinematic Mandarin melody.",
        "caption": "Light cloud veils the moon; flowing wind turns the returning snow.",
        "duration": 134.0,
        "canonicalUrl": f"https://fun.lazying.art/?preview=1#{MEDIA_ID}",
        "publication": {
            "visibility": "unlisted",
            "stage": "preview",
            "label": "Unlisted Preview",
            "listed": False,
            "note": "Direct-link listening preview; excluded from the default catalog and playback queue.",
        },
        "share": {
            "title": "洛神赋 · 原文选段 - Musia",
            "description": "An original cinematic Mandarin setting of selected lines from Cao Zhi's Luoshenfu.",
            "url": f"https://fun.lazying.art/?preview=1#{MEDIA_ID}",
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
            "primaryAudio": audio_asset,
            "alternateAudio": [],
        },
        "musical": musical,
        "textTracks": [],
        "lyricSets": [
            {
                "id": "zh-vocal",
                "label": "Original Text",
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
            }
        ],
        "timeline": {"unit": "seconds", "lines": timeline},
        "playback": {"defaultMode": "off"},
        "provenance": {
            "createdBy": "Musia",
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "audioSource": "ACE-Step 1.5 XL Turbo, exact-source sweep, seed 729403.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "sourceText": "Cao Zhi, 洛神赋; selected public-domain original lines.",
            "quality": {
                "gate": "unlisted-human-listening-preview",
                "candidateCount": 10,
                "health": "pass",
                "apex": {
                    "coherence": 2.915,
                    "musicality": 2.800,
                    "memorability": 2.839,
                    "clarity": 2.666,
                    "naturalness": 2.571,
                },
                "note": (
                    "Selected over seven other XL Turbo candidates and two rejected "
                    "XL SFT challengers after signal health, APEX, separated-vocal "
                    "large-v3, no-VAD, and MOSS-Music review."
                ),
            },
            "lyricCorrection": (
                "Every planned source line is accounted for. Timing combines "
                "large-v3 no-VAD anchors with MOSS-Music phrase boundaries; "
                "source-close recognition errors retain the original poem."
            ),
            "coverSource": COVER_SOURCE,
            "coverPrompt": (
                "Luoshui river through a luminous jade-and-silver celestial "
                "megastructure, light cloud veiling the moon, returning snow, "
                "and one small original robed figure crossing the water; no text."
            ),
            "publicAudio": PUBLIC_NAME,
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
        "summary": "An unlisted original-text listening preview built from Cao Zhi's Luoshenfu.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "visibility": "unlisted",
        "releaseStage": "preview",
        "category": "preview",
        "previewLabel": "Listening Preview",
        "previewReason": "Awaiting listener confirmation before a normal catalog release.",
        "languages": ["zh-Hans", "en", "ja"],
        "tags": [
            "music",
            "preview",
            "unlisted",
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
    print(f"https://fun.lazying.art/?preview=1#{MEDIA_ID}")


if __name__ == "__main__":
    main()
