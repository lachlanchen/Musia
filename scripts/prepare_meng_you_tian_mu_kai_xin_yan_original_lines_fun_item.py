#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pykakasi
from pypinyin import Style, pinyin


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
MEDIA_ID = "meng-you-tian-mu-kai-xin-yan-original-lines"
PROJECT = ROOT / "data/creative_projects/meng-you-tian-mu-kai-xin-yan-original-lines-20260706"
SELECTED_WAV = PROJECT / "selected/meng-you-tian-mu-kai-xin-yan-original-lines-zh-Hans-ace-turbo-seed746204.wav"
SELECTED_MP3 = PROJECT / "selected/meng-you-tian-mu-kai-xin-yan-original-lines-zh-Hans-ace-turbo-seed746204.mp3"
ANALYSIS = ROOT / "data/runs/meng-you-tian-mu-kai-xin-yan-original-lines-20260706-selected-analysis"
PUBLIC_AUDIO_NAME = "meng-you-tian-mu-kai-xin-yan-original-lines-zh-Hans-ace-turbo-seed746204-20260706.mp3"
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


def zh_pinyin_for(line_text: str, char: str) -> str:
    if not is_cjk(char):
        return ""
    overrides = {
        ("魄动", "魄"): "po4",
        ("长嗟", "嗟"): "jie1",
        ("惟觉", "觉"): "jue2",
        ("行乐", "行"): "xing2",
        ("何时还", "还"): "huan2",
        ("须行", "行"): "xing2",
        ("即骑", "骑"): "qi2",
        ("折腰", "折"): "zhe2",
        ("权贵", "权"): "quan2",
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
    # Timings use large-v3 ASR from the selected seed 746204 render. The public
    # text keeps only original poem wording/fragments, preserving source wording
    # where the generated sound is close. Some dense classical phrases remain
    # blurred; this item is therefore labeled as an original-text excerpt.
    return [
        ("l01", 23.54, 26.10, "忽魂悸以魄动", "Suddenly my soul trembles and my spirit stirs.", "忽ち魂は悸き、魄は動く"),
        ("l02", 26.10, 28.90, "恍惊起而长嗟", "In a daze I wake startled and sigh long.", "恍として驚き起き、長く嘆く"),
        ("l03", 28.90, 33.42, "惟觉时之枕席，失向来之烟霞", "Only the waking pillow remains; the former mists and cloudlight are gone.", "目覚めれば枕席のみ、さきほどの煙霞は失われた"),
        ("l04", 34.70, 40.38, "世间行乐亦如此，古来万事", "The pleasures of the world are also like this; since ancient times, all affairs...", "世の楽しみもまたこのようなもの、古来すべての事は"),
        ("l05", 40.38, 43.82, "东流水，别君去兮", "...flow east like water; I leave you and go.", "東へ流れる水、君に別れて去る"),
        ("l06", 43.82, 45.92, "何时还", "When shall I return?", "いつ帰るのだろう"),
        ("l07", 47.26, 51.18, "且放白鹿青崖间", "For now I release the white deer among green cliffs.", "しばし白鹿を青崖の間に放つ"),
        ("l08", 51.18, 55.76, "须行即骑访名山", "When I must go, I will ride out to visit famous mountains.", "行くべき時はすぐ騎って名山を訪ねる"),
        ("l09", 55.76, 60.24, "安能摧眉折腰事权贵", "How could I bow my brows and bend my waist to serve the powerful?", "どうして眉を低くし腰を折って権貴に仕えようか"),
        ("l10", 60.24, 63.20, "使我不得开心颜", "And lose my free and open face?", "それで晴れやかな顔を失うなど"),
        ("l11", 65.22, 73.01, "世间行乐亦如此，古来万事", "The pleasures of the world are also like this; since ancient times, all affairs...", "世の楽しみもまたこのようなもの、古来すべての事は"),
        ("l12", 73.01, 81.72, "安能摧眉折腰事权贵", "How could I bow my brows and bend my waist to serve the powerful?", "どうして眉を低くし腰を折って権貴に仕えようか"),
        ("l13", 81.72, 85.78, "使我不得开心颜", "And lose my free and open face?", "それで晴れやかな顔を失うなど"),
        ("l14", 86.44, 89.54, "惟觉时之枕席，失向来", "Only the waking pillow remains; the former...", "目覚めれば枕席のみ、さきほどの"),
        ("l15", 89.54, 93.16, "之烟霞，别君去兮何时还", "...mists and cloudlight are gone; I leave you, when shall I return?", "煙霞は失われ、君に別れて去ればいつ帰るのか"),
        ("l16", 93.16, 98.35, "且放白鹿青崖间", "For now I release the white deer among green cliffs.", "しばし白鹿を青崖の間に放つ"),
        ("l17", 98.35, 101.07, "须行即骑访名山", "When I must go, I will ride out to visit famous mountains.", "行くべき時はすぐ騎って名山を訪ねる"),
        ("l18", 101.07, 107.04, "安能摧眉折腰事权贵", "How could I bow my brows and bend my waist to serve the powerful?", "どうして眉を低くし腰を折って権貴に仕えようか"),
        ("l19", 107.04, 109.84, "使我不得开心颜", "And lose my free and open face?", "それで晴れやかな顔を失うなど"),
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
                "ACE-Step XL Turbo seed 746204. Timings use large-v3 ASR on the selected full mix. "
                "The active Mandarin track keeps original poem wording/fragments where the sound is close. "
                "The phrase 安能摧眉折腰事权贵 is partially recovered around 权贵 and kept as the intended source phrase; "
                "the item is labeled 原文段 instead of the pure full-poem title."
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
    if not SELECTED_MP3.exists():
        raise FileNotFoundError(f"Missing selected MP3: {SELECTED_MP3}")
    target = SONGS / "audio" / PUBLIC_AUDIO_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SELECTED_MP3, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def write_media_item() -> None:
    if not (ROOT / "website" / COVER).exists():
        raise FileNotFoundError(f"Missing cover: {ROOT / 'website' / COVER}")
    ensure_audio()
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
        "title": "梦游天姥吟留别 · 开心颜原文段",
        "localizedTitles": {
            "zh-Hans": "梦游天姥吟留别 · 开心颜原文段",
            "en": "Dreaming of Tianmu · Kaixinyan Original-Text Excerpt",
            "ja": "夢遊天姥吟留別・開心顔原文段",
        },
        "artist": "Musia",
        "description": "An ACE-Step Mandarin original-text excerpt song from the ending of Li Bai's 梦游天姥吟留别, using only source poem wording and ASR-corrected timing.",
        "caption": "Awakening from cloud-mist splendor, letting the white deer roam, and refusing to bow to power.",
        "duration": round(duration(SELECTED_WAV), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "梦游天姥吟留别 · 开心颜原文段 - Fun Lazying Art",
            "description": "Musia ACE-Step original-text excerpt song from Li Bai's 梦游天姥吟留别.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "梦游天姥吟留别 开心颜原文段 cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": "meng-you-tian-mu-kai-xin-yan-original-lines-zh",
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
            "key": "D minor requested; detected Dm/F/Bb cinematic progression",
            "bpm": round(float(run_manifest.get("tempo_bpm", 161.499)), 3),
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
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "audioSource": "ACE-Step 1.5 XL Turbo, short-line source-text sweep, selected seed 746204.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {
                "selectedSmallAsrOverlap": 0.21333333333333335,
                "gate": "experimental-original-text-excerpt",
            },
            "lyricCorrection": (
                "Corrected 2026-07-06 from large-v3 ASR on the selected full mix and the intended original-text excerpt. "
                "The song preserves source poem wording and fragments only; no modern adaptation lyric is added. "
                "Dense opening diction remains imperfect, so the item is explicitly named 原文段 rather than using the pure poem title."
            ),
            "pronunciationGuide": str((PROJECT / "source/pronunciation-guide.md").relative_to(ROOT)),
            "cover": {
                "src": COVER,
                "source": "Reused the existing no-text 16:9 Tianmu dream-mountain cover for this related poem-excerpt item.",
            },
            "publicAudio": PUBLIC_AUDIO_NAME,
        },
    }
    write_json(media_dir / "manifest.json", manifest)


def update_catalog() -> None:
    path = ROOT / "website/data/catalog.json"
    catalog = read_json(path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "梦游天姥吟留别 · 开心颜原文段",
        "artist": "Musia",
        "summary": "An ACE-Step Mandarin original-text excerpt from Li Bai's 梦游天姥吟留别 ending, with ASR-corrected trilingual lyrics, pinyin, furigana, and chord timing.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "Li Bai", "Tang poetry", "Mandarin", "ACE-Step", "original-text", "excerpt", "pinyin", "furigana"],
    }
    items = [entry for entry in catalog.get("items", []) if entry.get("id") != MEDIA_ID]
    insert_at = next((index for index, entry in enumerate(items) if entry.get("id") == "meng-you-tian-mu-original-poem"), 6)
    items.insert(insert_at, item)
    catalog["items"] = items
    write_json(path, catalog)


def write_project_note() -> None:
    note = PROJECT / "SELECTED_VERSION.md"
    note.write_text(
        "\n".join(
            [
                "# 梦游天姥吟留别 · 开心颜原文段",
                "",
                "- Selected audio: `selected/meng-you-tian-mu-kai-xin-yan-original-lines-zh-Hans-ace-turbo-seed746204.wav`",
                "- Public title: `梦游天姥吟留别 · 开心颜原文段`",
                "- Route: ACE-Step XL Turbo original-text-only excerpt, short-line source text.",
                "- Selected seed: `746204`",
                "- Analysis run: `data/runs/meng-you-tian-mu-kai-xin-yan-original-lines-20260706-selected-analysis`",
                "- Website id: `meng-you-tian-mu-kai-xin-yan-original-lines`",
                "",
                "Candidate summary:",
                "",
                "- seed 746201: rejected, very low ASR recovery.",
                "- seeds 746202-746204: short-line sweep; seed 746204 had strongest source anchors.",
                "- seed 746205 SFT: rejected, introduced unrelated modern ASR.",
                "- seeds 746211-746213 compact: rejected, worse lyric recovery.",
                "",
                "Quality caveat: this is an original-text excerpt experiment. The melody/chord structure is usable, but dense classical diction is imperfect. The public lyric keeps source wording where sound-close and labels the item as `原文段`, not the pure full-poem title.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    write_media_item()
    update_catalog()
    write_project_note()
    print(f"https://fun.lazying.art/#{MEDIA_ID}")


if __name__ == "__main__":
    main()
