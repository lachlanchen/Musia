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
MEDIA_ID = "xia-ke-xing-original-poem"
PROJECT = ROOT / "data/creative_projects/xia-ke-xing-original-poem-20260701"
SELECTED_WAV = PROJECT / "ace_outputs/zh_corrected_20260701-022423/94467276-ec50-3742-609c-4654c61e4cda.wav"
ANALYSIS = ROOT / "data/runs/xia-ke-xing-original-poem-20260701-20260701-022506-analysis"
PUBLIC_AUDIO_NAME = "xia-ke-xing-original-poem-zh-Hans-ace-20260701.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/xia-ke-xing-original-poem-16x9.png"

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
        ("飒沓如流星", "沓"): "ta4",
        ("事了拂衣去", "了"): "liao3",
        ("千里不留行", "行"): "xing2",
        ("五岳倒为轻", "为"): "wei2",
        ("烜赫大梁城", "烜"): "xuan3",
    }
    if (line_text, char) in overrides:
        return overrides[(line_text, char)]
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
    # Candidate 3 was selected from four exact-poem ACE passes. Timings and line
    # choices are based on vocal-stem medium/large no-VAD ASR plus a large-v3
    # prompted pass. The active text preserves Li Bai's poem only where the
    # rendered syllables support it; omitted, repeated, and mutated lines follow
    # the actual sound instead of the prompt.
    return [
        ("l01", 20.00, 22.72, "赵客缦胡缨", "Zhao knights wear rough Hu tassels.", "趙の侠客は胡の粗い冠紐をまとう"),
        ("l02", 22.72, 25.18, "赵客缦胡缨", "Zhao knights wear rough Hu tassels again.", "趙の侠客はふたたび胡の冠紐をまとう"),
        ("l03", 25.18, 27.24, "吴钩霜雪明", "Their Wu hooks gleam like frost and snow.", "呉鉤は霜雪のように明るい"),
        ("l04", 28.56, 30.35, "银鞍照白马", "Silver saddles shine on white horses.", "銀の鞍が白馬を照らす"),
        ("l05", 30.35, 32.18, "飒沓如流星", "Swift and ringing, like falling stars.", "颯沓として流星のように駆ける"),
        ("l06", 33.14, 34.96, "十步杀一人", "In ten steps, one man falls.", "十歩に一人を斬る"),
        ("l07", 34.96, 37.14, "事了拂衣去", "When the deed is done, he brushes his robe and leaves.", "事が終われば衣を払って去る"),
        ("l08", 37.14, 40.00, "深藏身与名", "Hiding both his body and his name.", "身も名も深く隠す"),
        ("l09", 43.64, 45.82, "脱剑膝前横", "He takes off his sword and lays it across his knees.", "剣を脱ぎ膝前に横たえる"),
        ("l10", 46.62, 48.92, "将炙啖朱亥", "He brings roast meat for Zhu Hai to eat.", "炙り肉を朱亥にすすめる"),
        ("l11", 48.92, 51.34, "持觞劝侯嬴", "Holding a cup, he urges Hou Ying to drink.", "杯を持って侯嬴に勧める"),
        ("l12", 51.34, 53.64, "持觞劝侯嬴", "Holding the cup, he urges Hou Ying again.", "杯を持ち、もう一度侯嬴に勧める"),
        ("l13", 56.26, 59.20, "三杯吐然诺", "After three cups, his pledge is spoken.", "三杯の後、約束を口にする"),
        ("l14", 59.20, 61.82, "五岳倒为轻", "The Five Sacred Peaks become light beside it.", "五岳も倒れて軽しとなる"),
        ("l15", 64.28, 66.55, "眼花耳热后", "When eyes dazzle and ears burn,", "目はくらみ耳は熱した後"),
        ("l16", 66.55, 68.86, "意气素霓生", "His spirit rises like a white rainbow.", "意気は白い虹となって生じる"),
        ("l17", 68.86, 71.34, "救赵挥金槌", "To rescue Zhao, he swings the golden hammer.", "趙を救わんと金槌を振るう"),
        ("l18", 71.34, 75.20, "邯郸先震惊", "Handan is shaken before all others.", "邯鄲はまず震え驚く"),
        ("l19", 76.20, 78.30, "千秋二壮士", "For a thousand autumns, the two heroes remain.", "千秋に二人の壮士あり"),
        ("l20", 78.30, 80.50, "烜赫大梁城", "Their fame blazes through Daliang city.", "大梁の城に赫々と名をあげる"),
        ("l21", 80.50, 83.36, "纵死侠骨香", "Even in death, knightly bones are fragrant.", "たとえ死しても侠骨は香る"),
        ("l22", 83.36, 86.20, "不惭世上英", "They need not blush before the world's heroes.", "世の英傑に恥じることはない"),
        ("l23", 88.80, 91.14, "谁能说孤侠", "Who can speak for the lone knight?", "誰が孤高の侠客を語れるだろう"),
        ("l24", 91.14, 93.96, "白首太仙境", "White hair drifts toward a fairy realm.", "白髪は仙境へと向かう"),
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
                "Original-poem ACE experiment. Candidate 3 selected from four exact-poem renders. "
                "Timings use vocal-stem medium/large no-VAD ASR. The active Mandarin text preserves Li Bai's "
                "original poem where the rendered syllables are sound-close, but the production note documents "
                "that classical diction is imperfect and some lines are weakly recovered."
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
        "title": "侠客行 · 原诗版",
        "localizedTitles": {
            "zh-Hans": "侠客行 · 原诗版",
            "en": "Knight-Errant Ballad · Original Poem",
            "ja": "侠客行・原詩版",
        },
        "artist": "Musia",
        "description": "An ACE-Step original-poem experiment using Li Bai's 侠客行 text as the lyric source, with ASR-audited trilingual website lyrics.",
        "caption": "A white horse, moonlit sword light, and Li Bai's original poem set as a wuxia art song.",
        "duration": round(duration(SELECTED_WAV), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "侠客行 · 原诗版 - Fun Lazying Art",
            "description": "Musia ACE original-poem version of Li Bai's 侠客行.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "侠客行 原诗版 cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": "xia-ke-xing-original-poem-zh",
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
            "key": "D minor requested / detected mixed E minor centered wuxia progression",
            "bpm": round(float(run_manifest.get("tempo_bpm", 86.1328125)), 3),
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
            "generationProject": "data/creative_projects/xia-ke-xing-original-poem-20260701",
            "audioSource": "ACE-Step 1.5 non-XL turbo seed 731903, selected from four exact-poem candidates.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {
                "selectedAudioLargeV3Overlap": 0.25833333333333336,
                "vocalStemMediumOverlap": 0.3333333333333333,
                "vocalStemLargeV3Overlap": 0.31666666666666665,
                "gate": "experimental-review",
            },
            "lyricCorrection": (
                "ASR-realigned original-poem track, updated 2026-07-01 after a large-v3 prompted pass on the separated vocal stem. "
                "The active Mandarin lyric reflects repeated, omitted, and mutated lines in the render: the opening repeats a "
                "赵客缦胡缨-like phrase, 千里不留行 and 闲过信陵饮 are not published as sung lines, 持觞劝侯嬴 repeats, and the "
                "final couplet follows the AI-mutated sound. This render has imperfect classical diction; do not treat it as a perfect commercial master."
            ),
            "coverSource": "/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/ig_0075c3bed0eb0cd1016a440b08763c8191833a70b775131ef6.png",
            "publicAudio": PUBLIC_AUDIO_NAME,
        },
    }
    write_json(media_dir / "manifest.json", manifest)

    catalog_path = ROOT / "website/data/catalog.json"
    catalog = read_json(catalog_path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "侠客行 · 原诗版",
        "artist": "Musia",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "tags": ["song", "li-bai", "tang-poetry", "wuxia", "ace", "original-poem"],
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
