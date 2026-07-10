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
MEDIA_ID = "gong-bai-tou-snow-we-share"
PROJECT = ROOT / "data/creative_projects/gong-bai-tou-snow-we-share-20260709"
SELECTED_AUDIO = PROJECT / "selected/gong-bai-tou-snow-we-share-ace-xl-turbo-seed790972.mp3"
ANALYSIS = ROOT / "data/runs/gong-bai-tou-snow-we-share-20260709-analysis"
PUBLIC_AUDIO_NAME = "gong-bai-tou-snow-we-share-ace-xl-turbo-seed790972-20260709.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/gong-bai-tou-snow-we-share-16x9.png"
DISPLAY_TITLE = "共白头 · Snow We Share · 雪中回声"
LOCALIZED_TITLES = {
    "zh-Hans": "共白头 · 雪中回声",
    "en": "Snow We Share · Snow Echo",
    "ja": "同じ雪の下で · 雪のこだま",
}
SUMMARY = "A mixed English, Japanese romaji, and Mandarin pinyin snow-memory ballad about shared snow, old longing, and the wish to grow white-haired together."
COVER_SOURCE = Path(
    "/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/"
    "ig_0933499e24356a63016a4f714160088191a5eecb88515843e5.png"
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
    """ASR/listening correction for ACE XL Turbo seed 790972.

    Evidence:
    - small English faster-whisper ASR on the full selected render;
    - the planned mixed phonetic lyric;
    - source couplet meaning from the user.

    Policy: preserve source/planned text when ASR is sound-close, but publish
    only the audible structure. A 2026-07-10 no-VAD medium cross-check recovered
    a soft chorus continuation around 50.7s and clarified that the final
    `Onaji yuki` / `Shiroku nareru kana` / `Ta zhao...` phrases should be
    separate lines rather than one merged mixed-language line.
    """

    return [
        ("l01", 3.18, 6.88, "Hu you gu ren xin shang guo", "An old friend crosses my heart.", "ふと故人が胸をよぎる", "忽有故人心上过", "lyric"),
        ("l02", 7.26, 13.53, "Lights fall soft in the snow", "Lights fall soft in the snow.", "雪の中で光がやわらかく降る", "雪光轻轻落下", "lyric"),
        ("l03", 15.60, 18.46, "Hui shou shan he yi ru dong", "I turn back; mountains and rivers have entered winter.", "振り向けば山河は冬に入る", "回首山河已入冬", "lyric"),
        ("l04", 18.46, 21.98, "Your name still glows", "Your name still glows.", "君の名はまだ光る", "你的名字仍在发光", "lyric"),
        ("l05", 21.98, 27.44, "Tooi hi no koe ga mune ni furu", "A voice from a distant day falls into my heart.", "遠い日の声が胸に降る", "远日的声音落进心里", "lyric"),
        ("l06", 28.40, 31.44, "Furikaereba sekai wa", "When I turn around, the world is...", "振り返れば世界は", "回首时，世界已是", "lyric"),
        ("l07", 31.44, 34.24, "Fuyu no iro ni naru", "...the color of winter.", "冬の色になる", "冬天的颜色", "lyric"),
        ("l08", 34.84, 37.86, "Ta zhao ruo shi tong lin xue", "If one day we share the same snow.", "いつか同じ雪に降られるなら", "他朝若是同淋雪", "lyric"),
        ("l09", 37.86, 41.02, "Ci sheng ye suan gong bai tou", "This life may count as growing old together.", "この一生も共白髪といえる", "此生也算共白头", "lyric"),
        ("l10", 41.02, 44.48, "Hu you gu ren xin shang guo", "An old friend crosses my heart again.", "ふたたび故人が胸をよぎる", "忽有故人心上过", "lyric"),
        ("l11", 44.48, 48.72, "Hui shou shan he yi ru dong", "I turn back; mountains and rivers have entered winter.", "振り向けば山河は冬に入る", "回首山河已入冬", "lyric"),
        ("l12", 50.67, 56.13, "Let our hearts be less alone", "Let our hearts be less alone.", "心を少しだけ孤独でなくして", "愿心不再那么孤单", "lyric"),
        ("l13", 56.13, 63.73, "Ah ah ah ah ah ah", "Ah ah ah.", "ああ、ああ", "啊，啊", "lyric"),
        ("l14", 64.36, 67.00, "Onaji yuki no shita de", "Under the same snow.", "同じ雪の下で", "在同一场雪下", "lyric"),
        ("l15", 67.00, 70.42, "Shiroku nareru kana", "Could we turn white together?", "白くなれるかな", "是否能一起白头", "lyric"),
        ("l16", 70.42, 73.58, "Ta zhao ruo shi tong lin xue", "If one day we share the same snow.", "いつか同じ雪に降られるなら", "他朝若是同淋雪", "lyric"),
        ("l17", 74.42, 78.12, "Ye suan gong bai tou", "It still counts as white hair together.", "それも共白髪といえる", "也算共白头", "lyric"),
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
                "Corrected from ACE XL Turbo seed 790972 using selected-render ASR and the planned mixed "
                "phonetic lyric. Source-close phrases are preserved; prompt lines not audibly recovered are omitted."
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
        "title": DISPLAY_TITLE,
        "localizedTitles": LOCALIZED_TITLES,
        "artist": "Musia",
        "description": SUMMARY,
        "caption": "If we can share one snowfall, maybe this life still counts as growing old together.",
        "duration": round(duration(SELECTED_AUDIO), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": f"{DISPLAY_TITLE} - Fun Lazying Art",
            "description": "A Musia mixed-language snow-memory ballad with synced lyrics, translations, pinyin, furigana, chords, and stems.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "Snow We Share cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": "gong-bai-tou-snow-we-share",
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
            "key": "B minor planned / winter ballad, detected around Bb-Eb modal colors",
            "bpm": round(float(run_manifest.get("tempo_bpm", 73.828125)), 3),
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
            "audioSource": "ACE-Step 1.5 XL Turbo mixed-language hook route, seed 790972, selected after Turbo and SFT sweeps.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {
                "gate": "public-candidate",
                "note": "Selected for usable winter-ballad vocal and recovered mixed hook. The render compresses the prompt; public lyrics match audible structure.",
            },
            "lyricCorrection": (
                "Selected-render small ASR plus 2026-07-10 no-VAD medium ASR on the full mix and vocal stem, "
                "then planned lyric/source cross-check. Close intended forms are preserved; a soft chorus continuation "
                "and split final snow phrases recovered by no-VAD are included in public lyrics."
            ),
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
        "title": DISPLAY_TITLE,
        "artist": "Musia",
        "summary": SUMMARY,
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["mul", "en", "zh-Hans", "ja"],
        "tags": ["music", "multilingual", "winter", "snow", "ACE-Step", "pinyin", "furigana", "chords"],
    }
    items = [existing for existing in catalog["items"] if existing.get("id") != MEDIA_ID]
    items.insert(0, item)
    catalog["items"] = items
    catalog["defaultMedia"] = MEDIA_ID
    write_json(path, catalog)


def write_reference() -> None:
    reference = ROOT / "references/gong-bai-tou-snow-we-share-production-2026-07-09.md"
    reference.write_text(
        "\n".join(
            [
                "# 共白头 · Snow We Share · 雪中回声 Production Note",
                "",
                "## Source",
                "",
                "```text",
                "忽有故人心上过，回首山河已入冬。",
                "他朝若是同淋雪，此生也算共白头。",
                "```",
                "",
                "## Selected Render",
                "",
                "- Route: ACE-Step 1.5 XL Turbo mixed-language route.",
                "- Selected seed: `790972`.",
                "- Selected audio: `data/creative_projects/gong-bai-tou-snow-we-share-20260709/selected/gong-bai-tou-snow-we-share-ace-xl-turbo-seed790972.mp3`.",
                f"- Public audio: `{PUBLIC_AUDIO}`.",
                "- Analysis: `data/runs/gong-bai-tou-snow-we-share-20260709-analysis/`.",
                "- Website manifest: `website/data/songs/gong-bai-tou-snow-we-share/manifest.json`.",
                "",
                "## Generation Attempts",
                "",
                "Three routes were tested:",
                "",
                "- `mixed_hook_xl_turbo`, seeds `790971-790974`: seed `790972` had the best recovered vocal structure.",
                "- `mixed_compact_xl_turbo`, seeds `790981-790984`: simpler lyric, but weaker recovery than seed `790972`.",
                "- `mixed_hook_v2_xl_sft`, seeds `790995-790996`: produced audio but no useful ASR recovery, so it was rejected.",
                "",
                "This follows the Musia rule that SFT is tried when quality matters, but Turbo is kept when it produces the stronger actual song.",
                "",
                "## Model-Facing Lyric Strategy",
                "",
                "The first selected route used Mandarin pinyin and Japanese romaji inside an English-language ACE lyric block. The planned lyric was intentionally sparse, but the selected render still compressed the latter half.",
                "",
                "This public version is now titled with the meaningful suffix `雪中回声 / Snow Echo` so it remains distinguishable from future no-pinyin remakes.",
                "",
                "Future remake rule from the July 10 review: do not feed Mandarin pinyin as the sung lyric for the new version. Use Chinese characters directly, and change `回首山河已入冬` to `回首山河已入秋` only in a newly generated render that actually sings `秋`.",
                "",
                "The public website does not publish the whole planned prompt as if it were sung. It publishes the selected render's audible structure, corrected with source-close forms where ASR was phonetically close.",
                "",
                "2026-07-10 correction: a no-VAD medium ASR pass on both the selected full mix and separated vocal stem recovered a soft chorus continuation after the second `Hui shou shan he yi ru dong`. The previous website lyric jumped from 48.72s to 64.40s and therefore missed audible text. The final snow section was also split more carefully into Japanese and Mandarin-pinyin phrases instead of one merged line.",
                "",
                "## Corrected Active Vocal",
                "",
                "```text",
                "3.18-6.88 Hu you gu ren xin shang guo",
                "7.26-13.53 Lights fall soft in the snow",
                "15.60-18.46 Hui shou shan he yi ru dong",
                "18.46-21.98 Your name still glows",
                "21.98-27.44 Tooi hi no koe ga mune ni furu",
                "28.40-31.44 Furikaereba sekai wa",
                "31.44-34.24 Fuyu no iro ni naru",
                "34.84-37.86 Ta zhao ruo shi tong lin xue",
                "37.86-41.02 Ci sheng ye suan gong bai tou",
                "41.02-44.48 Hu you gu ren xin shang guo",
                "44.48-48.72 Hui shou shan he yi ru dong",
                "50.67-56.13 Let our hearts be less alone",
                "56.13-63.73 Ah ah ah ah ah ah",
                "64.36-67.00 Onaji yuki no shita de",
                "67.00-70.42 Shiroku nareru kana",
                "70.42-73.58 Ta zhao ruo shi tong lin xue",
                "74.42-78.12 Ye suan gong bai tou",
                "```",
                "",
                "Public lyrics contain only sung lyric lines. Instrumental spans are inferred by the player from timing gaps and may show musical-note status in the player, but they are not song-level lyrics.",
                "",
                "Correction packet:",
                "",
                "```text",
                "data/creative_projects/gong-bai-tou-snow-we-share-20260709/correction_packets/old-public-medium-20260710/CORRECTION_PACKET.md",
                "```",
                "",
                "## Website",
                "",
                f"- URL: `https://fun.lazying.art/#{MEDIA_ID}`.",
                "- Active lyric: `website/data/songs/gong-bai-tou-snow-we-share/lyrics/mixed-vocal/mul.json`.",
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
