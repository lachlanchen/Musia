#!/usr/bin/env python3
"""Apply public Fun Lazying Art song-version naming rules.

Rules:
- ACE standard / selected best version uses the pure song name.
- Older ACE candidates use "ACE Legacy".
- DiffRhythm variants use compact "DR ..." suffixes.
- Lower-quality localization/model-transfer routes keep a method suffix.
"""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any

from pypinyin import Style, pinyin
import pykakasi


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "website/data/catalog.json"
DR_SHORT_ID = "yun-hai-zhi-lian-dr-short"
DR_SHORT_AUDIO = "https://lazyingart.github.io/MusiaSongs/audio/yun-hai-zhi-lian-main-zh-Hans-20260630.mp3"
DR_SHORT_LOCAL_AUDIO = ROOT / "data/creative_projects/yun-hai-zhi-lian-main-20260630/selected/yun-hai-zhi-lian-zh-Hans-diffrhythm-full-160.mp3"
DR_SHORT_ANALYSIS = ROOT / "data/runs/yun-hai-zhi-lian-main-diffrhythm-full-160-analysis"
KAKASI = pykakasi.kakasi()

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

DR_SHORT_ROWS: list[tuple[str, float, float, str, str, str]] = [
    ("l01", 7.70, 11.15, "天蓝蓝", "The sky is blue.", "空は青く"),
    ("l02", 11.15, 18.62, "云在天地间", "Clouds rest between heaven and earth.", "雲は天地の間に"),
    ("l03", 19.78, 23.10, "想念像风一样", "Longing moves like wind.", "想いは風のように"),
    ("l04", 23.78, 27.90, "依偎在你身边", "Leaning close beside you.", "君のそばに寄り添う"),
    ("l05", 28.74, 31.72, "望着那么远", "I gaze so far away.", "遠くを見つめて"),
    ("l06", 32.78, 36.14, "却像在眼前", "Yet it feels before my eyes.", "それでも目の前みたい"),
    ("l07", 36.78, 47.80, "慢慢慢慢，穿过云海", "Slowly, slowly, crossing the sea of clouds.", "ゆっくり雲海を越えて"),
    ("l08", 47.80, 52.26, "落进心里面", "Falling into my heart.", "心の奥へ落ちていく"),
    ("l09", 53.77, 58.34, "我好想来到你身边", "I long to come beside you.", "君のそばへ行きたい"),
    ("l10", 59.18, 62.92, "看清你的容颜", "To see your face clearly.", "その顔を見つめたい"),
    ("l11", 63.87, 67.42, "哪怕隔着山海万千", "Though mountains and seas divide us.", "山も海も隔てても"),
    ("l12", 68.78, 73.06, "也想与你相见", "I still want to meet you.", "それでも君に会いたい"),
    ("l13", 74.30, 76.98, "似水流年", "Years flow like water.", "流れる歳月"),
    ("l14", 78.34, 80.96, "时光轮转", "Time keeps turning.", "時はめぐる"),
    ("l15", 82.30, 84.90, "这一眼", "This one glance.", "この一目"),
    ("l16", 84.90, 88.92, "越过千年不变", "Crosses a thousand years unchanged.", "千年を越えても変わらない"),
    ("l17", 88.92, 92.52, "云海之间", "Between clouds and sea.", "雲海の間で"),
    ("l18", 97.61, 101.19, "我把爱写成一线", "I write love into one line.", "愛を一本の線にして"),
    ("l19", 101.19, 104.61, "牵向你的天边", "Pulling toward your horizon.", "君の空の果てへつなぐ"),
    ("l20", 107.35, 110.99, "你在云的那边", "You are beyond the clouds.", "君は雲の向こう側"),
    ("l21", 110.99, 115.51, "我在海的这边", "I am on this side of the sea.", "僕は海のこちら側"),
    ("l22", 116.11, 119.29, "一念成愿，一望无边", "One thought becomes a wish; one gaze becomes endless.", "一念は願いとなり、一望は果てしない"),
    ("l23", 121.24, 123.88, "越是想靠近", "The more I want to come near.", "近づきたいほど"),
    ("l24", 123.88, 127.70, "也怕渐行渐远", "The more I fear we drift apart.", "離れていくのが怖い"),
    ("l25", 129.56, 131.56, "一生只够遥远", "This life may only hold distance.", "この一生は遠さだけかもしれない"),
    ("l26", 133.54, 138.02, "我也愿把思念留在云海之间", "Still I leave my longing between the clouds and sea.", "それでも想いを雲海に残したい"),
    ("l27", 138.02, 148.44, "云在天地间", "Clouds rest between heaven and earth.", "雲は天地の間に"),
    ("l28", 149.75, 152.81, "我在无尽远方", "I am in the endless distance.", "僕は果てない遠方にいて"),
    ("l29", 153.73, 156.57, "仍想回到你身边", "Still longing to return beside you.", "それでも君のそばへ帰りたい"),
]


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
    line = {"id": line_id, "start": round(start, 3), "end": round(end, 3), "text": text, "singableText": text, "role": "lyric"}
    line["tokens"] = tokens_for(line, code)
    return line


def track(media_id: str, code: str, lines: list[dict[str, Any]], correction: str) -> dict[str, Any]:
    return {
        "schema": "fun.lazying.media.text-track.v1",
        "version": 1,
        "mediaId": media_id,
        "language": LANG[code],
        "lines": lines,
        "provenance": {
            "vocalSet": "zh-vocal",
            "correction": correction,
            "asrRun": str((DR_SHORT_ANALYSIS / "analysis/lyrics.json").relative_to(ROOT)) if media_id == DR_SHORT_ID else "",
        },
    }


def load_chords(path: Path) -> list[dict[str, Any]]:
    chords: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
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


def update_manifest_titles(media_id: str, *, title: str, localized: dict[str, str], share_title: str, description: str | None = None, caption: str | None = None, playback: dict[str, Any] | None = None) -> None:
    path = ROOT / "website/data/songs" / media_id / "manifest.json"
    manifest = read_json(path)
    manifest["title"] = title
    manifest["localizedTitles"] = localized
    if description:
        manifest["description"] = description
    if caption:
        manifest["caption"] = caption
    manifest.setdefault("share", {})["title"] = share_title
    if manifest.get("assets", {}).get("cover", {}).get("label"):
        manifest["assets"]["cover"]["label"] = f"{title} cover"
    if playback is None:
        manifest.pop("playback", None)
    else:
        manifest["playback"] = playback
    write_json(path, manifest)


def write_dr_short_item() -> None:
    media_dir = ROOT / "website/data/songs" / DR_SHORT_ID
    correction = (
        "DiffRhythm 160-second short route. Published timing follows ASR phrase windows from the selected render; "
        "sound-close substitutions such as 像年/想念, 这一夜/这一眼, 我白/我把爱, and 海之间/云海之间 are corrected "
        "back to the intended lyric. Lines not clearly present in the render are not inserted."
    )
    lines_by_code: dict[str, list[dict[str, Any]]] = {"zh-Hans": [], "en": [], "ja": []}
    for line_id, start, end, zh, en, ja in DR_SHORT_ROWS:
        lines_by_code["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans"))
        lines_by_code["en"].append(make_line(line_id, start, end, en, "en"))
        lines_by_code["ja"].append(make_line(line_id, start, end, ja, "ja"))
    for code, lines in lines_by_code.items():
        write_json(media_dir / "lyrics/zh-vocal" / f"{code}.json", track(DR_SHORT_ID, code, lines, correction))

    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": DR_SHORT_ID,
        "kind": "song",
        "title": "云海之恋 · DR Short",
        "localizedTitles": {
            "zh-Hans": "云海之恋 · DR 短版",
            "en": "Cloud Sea Love · DR Short",
            "ja": "雲海の恋・DR短編",
        },
        "artist": "Musia",
        "description": "A DiffRhythm short Mandarin cloud-sea love ballad, corrected against its selected vocal render.",
        "caption": "A compact DiffRhythm route kept for comparison with the ACE standard version.",
        "duration": round(duration(DR_SHORT_LOCAL_AUDIO), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{DR_SHORT_ID}",
        "share": {
            "title": "云海之恋 · DR Short - Fun Lazying Art",
            "description": "A Musia DiffRhythm short cloud-sea love ballad with corrected trilingual lyrics.",
            "url": f"https://fun.lazying.art/#{DR_SHORT_ID}",
            "image": "assets/covers/yun-hai-zhi-lian-16x9.png",
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {
                "id": "cover",
                "label": "云海之恋 · DR Short cover",
                "role": "cover",
                "src": "assets/covers/yun-hai-zhi-lian-16x9.png",
                "mime": "image/png",
                "width": 1600,
                "height": 900,
            },
            "poster": {
                "id": "poster",
                "label": "16:9 Poster",
                "role": "poster",
                "src": "assets/covers/yun-hai-zhi-lian-16x9.png",
                "mime": "image/png",
                "width": 1600,
                "height": 900,
            },
            "primaryAudio": {
                "id": "yun-hai-dr-short-zh",
                "label": "中文",
                "roleLabel": "Vocal",
                "role": "vocal",
                "languageCode": "zh-Hans",
                "languageLabel": "中文",
                "lyricSetId": "zh-vocal",
                "src": DR_SHORT_AUDIO,
                "mime": "audio/mpeg",
            },
            "alternateAudio": [],
        },
        "musical": {
            "key": "detected Eb/Bb center",
            "bpm": 117.45,
            "timeSignature": "4/4",
            "chords": load_chords(DR_SHORT_ANALYSIS / "analysis/chords.csv"),
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
        "timeline": {
            "unit": "seconds",
            "lines": [{"id": line["id"], "start": line["start"], "end": line["end"], "text": line["text"]} for line in lines_by_code["zh-Hans"]],
        },
        "provenance": {
            "createdBy": "Musia",
            "generationProject": "data/creative_projects/yun-hai-zhi-lian-main-20260630",
            "audioSource": "DiffRhythm 1.2 160-second full-lyrics route.",
            "analysisRun": str(DR_SHORT_ANALYSIS.relative_to(ROOT)),
            "lyricCorrection": correction,
            "coverSource": "website/assets/covers/yun-hai-zhi-lian-16x9.png",
            "publicAudio": "yun-hai-zhi-lian-main-zh-Hans-20260630.mp3",
        },
        "artifacts": [
            {
                "id": "analysis-report",
                "label": "Musia DR Short analysis report",
                "kind": "markdown",
                "path": "data/runs/yun-hai-zhi-lian-main-diffrhythm-full-160-analysis/REPORT.md",
            }
        ],
    }
    write_json(media_dir / "manifest.json", manifest)


def update_catalog() -> None:
    catalog = read_json(CATALOG_PATH)
    catalog["defaultMedia"] = "yun-hai-zhi-lian-haifeng-duange"
    upserts: dict[str, dict[str, Any]] = {
        "yun-hai-zhi-lian-haifeng-duange": {
            "id": "yun-hai-zhi-lian-haifeng-duange",
            "kind": "song",
            "title": "云海之恋",
            "artist": "Musia",
            "summary": "The standard ACE-Step Mandarin cloud-sea love ballad with ASR-corrected trilingual lyrics, pinyin, furigana, and chord timing.",
            "manifest": "data/songs/yun-hai-zhi-lian-haifeng-duange/manifest.json",
            "cover": "assets/covers/yun-hai-zhi-lian-haifeng-duange-16x9.png",
            "languages": ["zh-Hans", "en", "ja"],
            "tags": ["music", "love", "cloud-sea", "Mandarin", "ACE-Step", "standard", "pinyin", "furigana"],
        },
        DR_SHORT_ID: {
            "id": DR_SHORT_ID,
            "kind": "song",
            "title": "云海之恋 · DR Short",
            "artist": "Musia",
            "summary": "A compact DiffRhythm Mandarin cloud-sea route with ASR-corrected trilingual lyrics and chord timing.",
            "manifest": f"data/songs/{DR_SHORT_ID}/manifest.json",
            "cover": "assets/covers/yun-hai-zhi-lian-16x9.png",
            "languages": ["zh-Hans", "en", "ja"],
            "tags": ["music", "love", "cloud-sea", "Mandarin", "DiffRhythm", "DR", "short", "pinyin", "furigana"],
        },
        "yun-hai-zhi-lian": {
            "id": "yun-hai-zhi-lian",
            "kind": "song",
            "title": "云海之恋 · DR Full Lyrics",
            "artist": "Musia",
            "summary": "A full-length DiffRhythm Mandarin cloud-sea route with corrected trilingual lyrics, pinyin, furigana, and chord timing.",
            "manifest": "data/songs/yun-hai-zhi-lian/manifest.json",
            "cover": "assets/covers/yun-hai-zhi-lian-16x9.png",
            "languages": ["zh-Hans", "en", "ja"],
            "tags": ["music", "love", "cloud-sea", "Mandarin", "pinyin", "furigana", "DiffRhythm", "DR", "full-lyrics"],
        },
        "yun-hai-zhi-lian-legacy": {
            "id": "yun-hai-zhi-lian-legacy",
            "kind": "song",
            "title": "云海之恋 · ACE Legacy",
            "artist": "Musia",
            "summary": "An earlier ACE-Step cloud-sea love ballad candidate preserved for comparison.",
            "manifest": "data/songs/yun-hai-zhi-lian-legacy/manifest.json",
            "cover": "assets/covers/yun-hai-zhi-lian-16x9.png",
            "languages": ["zh-Hans", "en", "ja"],
            "tags": ["music", "love", "cloud-sea", "ACE-Step", "ACE Legacy", "legacy"],
        },
        "take-care-of-yourself": {
            "id": "take-care-of-yourself",
            "kind": "localized-song",
            "title": "Take Care of Yourself · SoulX Localization",
            "artist": "Musia",
            "summary": "The earlier SoulX/localization-route self-care song with English, Mandarin, and Cantonese vocals.",
            "manifest": "data/songs/take-care-of-yourself/manifest.json",
            "cover": "assets/covers/take-care-of-yourself-16x9.png",
            "languages": ["en", "zh-Hans", "yue-Hant"],
            "tags": ["music", "localized-song", "SoulX", "method-suffix", "hope", "self-care", "Mandarin", "Cantonese"],
        },
        "take-care-of-yourself-hope-version": {
            "id": "take-care-of-yourself-hope-version",
            "kind": "song",
            "title": "Take Care of Yourself",
            "artist": "Musia",
            "summary": "The standard spacious hope song in English, Japanese, and Mandarin, centered on care, courage, and light.",
            "manifest": "data/songs/take-care-of-yourself-hope-version/manifest.json",
            "cover": "assets/covers/take-care-of-yourself-16x9.png",
            "languages": ["en", "ja", "zh-Hans"],
            "tags": ["music", "hope", "self-care", "ACE-Step", "standard", "English", "Japanese", "Mandarin"],
        },
    }
    order_after_one_sky = [
        "yun-hai-zhi-lian-haifeng-duange",
        DR_SHORT_ID,
        "yun-hai-zhi-lian",
        "yun-hai-zhi-lian-legacy",
    ]
    remaining = [item for item in catalog["items"] if item.get("id") not in upserts]
    result: list[dict[str, Any]] = []
    inserted_yunhai = False
    for item in remaining:
        result.append(item)
        if item.get("id") == "one-sky-three-lights-mixed":
            result.extend(upserts[item_id] for item_id in order_after_one_sky)
            inserted_yunhai = True
    if not inserted_yunhai:
        result = [upserts[item_id] for item_id in order_after_one_sky] + result

    take_care_inserted = False
    final: list[dict[str, Any]] = []
    for item in result:
        final.append(item)
        if item.get("id") == "aya-chan-hikari-ame-full-mv":
            final.append(upserts["take-care-of-yourself"])
            final.append(upserts["take-care-of-yourself-hope-version"])
            take_care_inserted = True
    if not take_care_inserted:
        final.extend([upserts["take-care-of-yourself"], upserts["take-care-of-yourself-hope-version"]])
    catalog["items"] = final
    write_json(CATALOG_PATH, catalog)


def main() -> None:
    write_dr_short_item()
    update_manifest_titles(
        "yun-hai-zhi-lian-haifeng-duange",
        title="云海之恋",
        localized={"zh-Hans": "云海之恋", "en": "Cloud Sea Love", "ja": "雲海の恋"},
        share_title="云海之恋 - Fun Lazying Art",
        description="The standard ACE-Step Mandarin cloud-sea love ballad, corrected against its selected vocal render.",
        caption="A cloud-and-sea love song carried by distance, time, and longing.",
        playback={"defaultMode": "single", "reason": "Standard ACE-selected version should loop by default for listening and recording."},
    )
    update_manifest_titles(
        "yun-hai-zhi-lian",
        title="云海之恋 · DR Full Lyrics",
        localized={"zh-Hans": "云海之恋 · DR 完整歌词版", "en": "Cloud Sea Love · DR Full Lyrics", "ja": "雲海の恋・DR完全歌詞版"},
        share_title="云海之恋 · DR Full Lyrics - Fun Lazying Art",
        description="A full-length DiffRhythm Mandarin cloud-sea love ballad with LRC-conditioned lyrics corrected against ASR evidence.",
    )
    update_manifest_titles(
        "yun-hai-zhi-lian-legacy",
        title="云海之恋 · ACE Legacy",
        localized={"zh-Hans": "云海之恋 · ACE Legacy", "en": "Cloud Sea Love · ACE Legacy", "ja": "雲海の恋・ACE Legacy"},
        share_title="云海之恋 · ACE Legacy - Fun Lazying Art",
        description="An earlier ACE-Step ocean-and-sky love ballad candidate with Mandarin, English, and Japanese vocals.",
    )
    update_manifest_titles(
        "take-care-of-yourself",
        title="Take Care of Yourself · SoulX Localization",
        localized={"en": "Take Care of Yourself · SoulX Localization", "zh-Hans": "照顾好自己 · SoulX 本地化", "yue-Hant": "照顧好自己 · SoulX 本地化"},
        share_title="Take Care of Yourself · SoulX Localization - Fun Lazying Art",
        description="The earlier SoulX/localization-route self-care song with English, Mandarin, and Cantonese vocals.",
    )
    update_manifest_titles(
        "take-care-of-yourself-hope-version",
        title="Take Care of Yourself",
        localized={"en": "Take Care of Yourself", "zh-Hans": "照顾好自己", "ja": "自分を大切に"},
        share_title="Take Care of Yourself - Fun Lazying Art",
        description="The standard spacious hope song about care, courage, and the quiet light that helps you continue.",
        playback={"defaultMode": "single", "reason": "Standard ACE-selected version should loop by default for listening and recording."},
    )
    update_catalog()
    print("Applied Fun Lazying Art version naming and playback defaults.")


if __name__ == "__main__":
    # Compatibility entry point; the reviewed bilingual catalog supersedes model suffixes.
    from curate_fun_catalog import main as curate
    raise SystemExit(curate(["--apply"]))
