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
MEDIA_ID = "qiang-jin-jiu-original-poem"
PROJECT = ROOT / "data/creative_projects/qiang-jin-jiu-original-poem-20260701"
SELECTED_WAV = PROJECT / "ace_outputs/zh_sectioned_xl_more/20ea2127-e90d-f93c-77ed-26e210a5316d.wav"
ANALYSIS = ROOT / "data/runs/qiang-jin-jiu-original-poem-20260701-20260701-075731-analysis"
PUBLIC_AUDIO_NAME = "qiang-jin-jiu-original-poem-zh-Hans-ace-20260701.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/qiang-jin-jiu-16x9.png"

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
JA_READING_OVERRIDES = {
    "馔": "せん",
    "饌": "せん",
}


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
    if line_text.startswith("朝如") and char == "朝" and index == 0:
        return "zhao1"
    if index > 0 and line_text[index - 1 : index + 1] == "白发" and char == "发":
        return "fa4"
    if line_text.startswith("烹羊宰牛且为乐") and char == "为":
        return "wei2"
    if line_text.startswith("烹羊宰牛且为乐") and char == "乐":
        return "le4"
    if line_text.startswith("请君为我") and char == "为":
        return "wei4"
    if line_text.startswith("千金散尽还复来") and char == "还":
        return "huan2"
    if line_text.startswith("陈王昔时宴平乐") and char == "乐":
        return "le4"
    if line_text.startswith("斗酒") and char == "斗":
        return "dou3"
    if char == "馔":
        return "zhuan4"
    if char == "谑":
        return "xue4"
    if line_text.startswith("呼儿将出") and char == "将":
        return "jiang1"
    if line_text.startswith("与尔") and char == "与":
        return "yu3"
    values = pinyin(char, style=Style.TONE3, strict=False, neutral_tone_with_five=True)
    return values[0][0] if values and values[0] else ""


def ja_reading(text: str) -> str:
    if not is_cjk(text):
        return ""
    if text in JA_READING_OVERRIDES:
        return JA_READING_OVERRIDES[text]
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
    # Selected seed 732206 is the best exact-poem-as-lyrics candidate. These
    # timings are corrected from large-v3 ASR on both selected audio and the
    # separated vocal stem. The text preserves Li Bai's original wording when
    # the rendered sound is close; repeated/mutated sections follow the audio.
    return [
        ("l01", 19.94, 27.68, "君不见黄河之水天上来", "Do you not see the Yellow River's waters descending from the sky?", "見よ、黄河の水が天より来る"),
        ("l02", 28.68, 32.30, "奔流到海不复回", "Rushing to the sea, never to return.", "奔流して海へ至り、二度と帰らない"),
        ("l03", 33.24, 37.14, "君不见高堂明镜悲白发", "Do you not see the bright mirror in the high hall grieving over white hair?", "高堂の明鏡が白髪を悲しむのを見よ"),
        ("l04", 37.14, 40.60, "朝如青丝暮成雪", "At dawn black as silk, by dusk turned to snow.", "朝は青き糸、暮れには雪となる"),
        ("l05", 40.60, 44.26, "人生得意须尽欢", "When life is proud, take joy to the full.", "人生得意の時は歓びを尽くせ"),
        ("l06", 44.26, 48.22, "莫使金樽空对月", "Do not let the golden cup face the moon empty.", "金の盃を空しく月に向けるな"),
        ("l07", 49.36, 52.24, "天生我材必有用", "Heaven made my talent; it must have its use.", "天が我が才を生んだ、必ず用いられる"),
        ("l08", 52.24, 55.68, "莫使金樽空对月", "Do not let the golden cup face the moon empty.", "金の盃を空しく月に向けるな"),
        ("l09", 55.68, 59.70, "天生我材必有用", "Heaven made my talent; it must have its use.", "天が我が才を生んだ、必ず用いられる"),
        ("l10", 59.70, 63.40, "千金散尽还复来", "A thousand gold pieces spent will return again.", "千金は散じ尽くしてもまた戻る"),
        ("l11", 64.04, 67.20, "烹羊宰牛且为乐", "Cook lamb, slaughter oxen, and take delight.", "羊を煮、牛を屠って楽しもう"),
        ("l12", 67.80, 71.12, "会须一饮三百杯", "We must drink three hundred cups.", "必ず三百杯を飲もう"),
        ("l13", 71.12, 73.04, "岑夫子", "Master Cen.", "岑夫子よ"),
        ("l14", 73.90, 79.08, "丹丘生，将进酒，杯莫停", "Danqiu my friend, bring in the wine; let the cup not stop.", "丹丘生よ、酒を勧めよう、杯を止めるな"),
        ("l15", 83.70, 88.36, "将进酒，杯莫停", "Bring in the wine; let the cup not stop.", "酒を勧めよう、杯を止めるな"),
        ("l16", 90.66, 93.12, "与君歌一曲", "I sing one song for you.", "君のために一曲歌おう"),
        ("l17", 93.12, 97.00, "请君为我倾耳听", "Please lean your ear and listen to me.", "どうか耳を傾けて聞いてほしい"),
        ("l18", 98.00, 101.50, "钟鼓馔玉不足贵", "Bells, drums, and jade banquets are not worth prizing.", "鐘鼓と饌玉は貴ぶに足りない"),
        ("l19", 101.50, 105.16, "但愿长醉不愿醒", "I only wish to stay long drunk, never wishing to wake.", "ただ長く酔い、醒めたくない"),
        ("l20", 105.16, 108.86, "古来圣贤皆寂寞", "Since ancient times, sages and worthies have all been lonely.", "古来、聖賢は皆寂寞としている"),
        ("l21", 108.86, 112.86, "惟有饮者留其名", "Only drinkers leave their names behind.", "ただ飲む者だけが名を残す"),
        ("l22", 113.44, 117.32, "陈王昔时宴平乐", "Long ago Prince Chen feasted at Pingle.", "陳王は昔、平楽で宴を開いた"),
        ("l23", 117.32, 121.64, "陈王昔时宴平乐", "Long ago Prince Chen feasted at Pingle again.", "陳王はふたたび平楽の宴へ戻る"),
        ("l24", 121.64, 125.28, "斗酒十千恣欢谑", "Wine by the peck, ten thousand coins, freely laughing and jesting.", "斗酒十千、歓謔をほしいままにした"),
        ("l25", 125.28, 129.36, "主人何为言少钱", "Host, why speak of having too little money?", "主人よ、なぜ金が少ないと言うのか"),
        ("l26", 129.36, 133.36, "径须沽取对君酌", "Just buy wine at once, and pour it for you.", "ただちに買い求め、君と酌もう"),
        ("l27", 133.36, 139.20, "五花马，千金裘", "The dappled horse, the thousand-gold fur robe.", "五花の馬、千金の裘"),
        ("l28", 153.36, 157.48, "五花马，千金裘", "The dappled horse, the thousand-gold fur robe.", "五花の馬、千金の裘"),
        ("l29", 162.12, 166.20, "呼儿将出换美酒", "Call the boy to bring them out and trade them for fine wine.", "童を呼び、持ち出して美酒に替えよう"),
        ("l30", 169.18, 174.94, "与尔同销万古愁", "Together with you, I will dissolve ten thousand ages of sorrow.", "君とともに万古の愁いを消そう"),
        ("l31", 175.48, 177.82, "万古愁", "Ten thousand ages of sorrow.", "万古の愁い"),
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
                "New original-poem candidate, not the older ACE Poetry Demo. "
                "Active Mandarin text was corrected from the selected audio and vocal-stem large-v3 no-VAD ASR, "
                "then cross-checked against the requested Li Bai poem and pronunciation guide. "
                "The render repeats 莫使金樽/天生我材, repeats 陈王昔时宴平乐, and skips or garbles part of the final exchange; "
                "the website timeline follows the actual sound rather than the prompt order."
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
            "-vn",
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
        "title": "将进酒 · 原诗版",
        "localizedTitles": {
            "zh-Hans": "将进酒 · 原诗版",
            "en": "Bring In the Wine · Original Poem",
            "ja": "将進酒・原詩版",
        },
        "artist": "Musia",
        "description": "A new ACE-Step Mandarin song render that treats Li Bai's original 将进酒 poem as the lyric source, with same-audio ASR-corrected timing.",
        "caption": "The Yellow River, the moonlit cup, and Li Bai's heroic tenderness sung as an original-poem art song.",
        "duration": round(duration(SELECTED_WAV), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "将进酒 · 原诗版 - Fun Lazying Art",
            "description": "Musia ACE-Step original-poem version of Li Bai's 将进酒.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "将进酒 原诗版 cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": "qiang-jin-jiu-original-poem-zh",
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
            "key": "Requested D minor; detected Ab/Eb/Cm/Fm/Gm movement in analysis",
            "bpm": round(float(run_manifest.get("tempo_bpm", 123.046875)), 3),
            "timeSignature": "4/4",
            "chords": load_chords(),
        },
        "lyricSets": [
            {
                "id": "zh-vocal",
                "label": "中文 vocal",
                "languageCode": "zh-Hans",
                "tracks": [
                    {
                        "code": "zh-Hans",
                        "label": "Mandarin Chinese",
                        "nativeLabel": "中文",
                        "script": "Hans",
                        "features": ["pinyin", "active-vocal"],
                        "path": "lyrics/zh-vocal/zh-Hans.json",
                    },
                    {
                        "code": "en",
                        "label": "English",
                        "nativeLabel": "English",
                        "script": "Latn",
                        "features": ["translation"],
                        "path": "lyrics/zh-vocal/en.json",
                    },
                    {
                        "code": "ja",
                        "label": "Japanese",
                        "nativeLabel": "日本語",
                        "script": "Jpan",
                        "features": ["furigana", "translation"],
                        "path": "lyrics/zh-vocal/ja.json",
                    },
                ],
            }
        ],
        "textTracks": [],
        "timeline": {"unit": "seconds", "lines": timeline},
        "artifacts": [],
        "provenance": {
            "createdBy": "Musia",
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "audioSource": "ACE-Step 1.5 XL Turbo sectioned original-poem route, seed 732206; selected from six exact-poem candidates.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {
                "quickSmallAsrOverlap": 0.36363636363636365,
                "selectedLargeV3NoVadOverlap": 0.4090909090909091,
                "vocalStemLargeV3NoVadOverlap": 0.38636363636363635,
                "gate": "pass-with-caveats",
            },
            "lyricCorrection": (
                "Deep-corrected 2026-07-01 using large-v3 no-VAD ASR on selected audio and the separated vocal stem. "
                "This is the newer exact-poem candidate, not the old ACE Poetry Demo. The visible lyric preserves the original poem where the sound is close, "
                "but reflects the rendered repeats and omits unsupported garbled phrases. The no-VAD ASR also reported a likely hallucinated intro credit; it is not shown as poem lyric."
            ),
            "lyricCorrectionEvidence": [
                str((PROJECT / "corrections/deep-large-selected-732206/CORRECTION_PACKET.md").relative_to(ROOT)),
                str((PROJECT / "corrections/deep-large-selected-732206/selected-large-v3-no-vad.json").relative_to(ROOT)),
                str((PROJECT / "corrections/deep-large-selected-732206/vocal-stem-large-v3-no-vad.json").relative_to(ROOT)),
            ],
            "pronunciationGuide": str((PROJECT / "source/pronunciation-guide.md").relative_to(ROOT)),
            "coverSource": COVER,
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
        "title": "将进酒 · 原诗版",
        "artist": "Musia",
        "summary": "A new ACE-Step Mandarin original-poem version of Li Bai's 将进酒, with ASR-corrected trilingual lyrics, pinyin, furigana, and chord timing.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "Li Bai", "Tang poetry", "Mandarin", "ACE-Step", "original-poem", "pinyin", "furigana"],
    }
    items = [entry for entry in catalog.get("items", []) if entry.get("id") != MEDIA_ID]
    insert_at = next((index for index, entry in enumerate(items) if entry.get("id") == "qiang-jin-jiu"), len(items))
    items.insert(insert_at, item)
    catalog["items"] = items
    write_json(path, catalog)


def main() -> None:
    ensure_audio()
    write_media_item()
    update_catalog()
    print(f"https://fun.lazying.art/#{MEDIA_ID}")


if __name__ == "__main__":
    main()
