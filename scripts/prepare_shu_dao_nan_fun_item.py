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
MEDIA_ID = "shu-dao-nan"
PROJECT = ROOT / "data/creative_projects/shu-dao-nan-20260701"
SELECTED_WAV = PROJECT / "ace_outputs/zh-v2-clear/91355521-1698-0d9d-06c8-c1f7d004c80e.wav"
ANALYSIS = ROOT / "data/runs/shu-dao-nan-20260701-735202-analysis"
PUBLIC_AUDIO_NAME = "shu-dao-nan-zh-Hans-ace-20260701.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/shu-dao-nan-16x9.png"

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
    if char == "蜀":
        return "shu3"
    if char == "难":
        return "nan2"
    if char == "栈":
        return "zhan4"
    if char == "还" and "何时还" in line_text:
        return "huan2"
    if char == "乐" and "云乐" in line_text:
        return "le4"
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
        item = {"text": part, "start": round(start + step * index, 3), "end": round(start + step * (index + 1), 3)}
        if code == "zh-Hans":
            reading = zh_pinyin_for(line["text"], part)
            if reading:
                item["pinyin"] = reading
        elif code == "ja":
            reading = ja_reading(part)
            if reading:
                item["reading"] = reading
        tokens.append(item)
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
        ("l01", 22.54, 25.06, "山高入云端", "The mountain rises into the clouds.", "山は高く雲の端へ入る"),
        ("l02", 25.06, 26.96, "古道挂天边", "The old road hangs at the edge of the sky.", "古道は空の果てに掛かる"),
        ("l03", 26.96, 28.56, "风从秦川起", "Wind rises from Qin plains.", "風は秦川から起こる"),
        ("l04", 28.56, 30.32, "吹过四万年", "It blows across forty thousand years.", "四万年を吹き渡る"),
        ("l05", 30.32, 32.44, "石栈连天去", "Stone plank roads climb into the sky.", "石桟は天へ連なって行く"),
        ("l06", 32.44, 34.26, "回川卷狂澜", "Turning rivers roll wild waves.", "逆巻く川は荒波を巻く"),
        ("l07", 34.26, 36.22, "黄鹤飞不过", "Even yellow cranes cannot fly across.", "黄鶴さえ飛び越えられない"),
        ("l08", 36.22, 37.78, "我仍向前", "Still I move forward.", "それでも私は前へ進む"),
        ("l09", 38.52, 40.16, "青泥路盘盘", "The Qingni road coils and coils.", "青泥の道は幾重にも巡る"),
        ("l10", 40.16, 41.92, "百步绕千山", "A hundred steps wind around a thousand peaks.", "百歩は千の山を巡る"),
        ("l11", 41.92, 43.16, "抬头星辰近", "I look up, and stars are close.", "見上げれば星辰は近い"),
        ("l12", 43.16, 46.96, "低头是深渊", "I look down, and there is abyss.", "見下ろせば深淵がある"),
        ("l13", 46.96, 49.30, "蜀道难", "The Shu road is hard.", "蜀道は険しい"),
        ("l14", 50.16, 53.06, "难于上青天", "Harder than climbing the blue sky.", "青天へ上るより難しい"),
        ("l15", 54.88, 56.72, "蜀道难", "The Shu road is hard.", "蜀道は険しい"),
        ("l16", 61.14, 63.46, "悲鸟绕古木", "Sad birds circle ancient trees.", "悲しき鳥は古木を巡る"),
        ("l17", 63.46, 65.26, "子规啼夜月", "The cuckoo cries under the night moon.", "子規は夜の月に啼く"),
        ("l18", 65.26, 67.22, "问君何时还", "I ask when you will return.", "君はいつ帰るのかと問う"),
        ("l19", 67.22, 69.14, "心已越峰巅", "The heart has crossed the mountain crest.", "心はすでに峰を越えた"),
        ("l20", 69.14, 71.04, "剑阁高又险", "Jianmen Pass is high and perilous.", "剣閣は高くまた険しい"),
        ("l21", 71.04, 72.94, "一夫守万关", "One guard can hold ten thousand gates.", "一夫が万の関を守る"),
        ("l22", 72.94, 74.74, "锦城虽云乐", "Though Jincheng is said to be joyful.", "錦城は楽しいと言われても"),
        ("l23", 74.74, 76.94, "不如早回山", "Better to return early to the mountains.", "早く山へ帰るに及ばない"),
        ("l24", 77.52, 79.38, "蜀道难", "The Shu road is hard.", "蜀道は険しい"),
        ("l25", 79.38, 81.64, "难于上青天", "Harder than climbing the blue sky.", "青天へ上るより難しい"),
        ("l26", 81.64, 85.26, "侧身西望，心潮万千", "Turning west, my heart surges in ten thousand waves.", "身を傾け西を望み、心は万千に波立つ"),
        ("l27", 85.26, 89.08, "若能望见晴天", "If only I can see the clear sky.", "もし晴天を望めるなら"),
        ("l28", 89.08, 93.86, "走过险路，仍要见晴天", "After the dangerous road, I still want to see clear sky.", "険しい道を越えても、なお晴天を見たい"),
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
                "Active Mandarin lyrics corrected from the selected audio and separated vocal large-v3 ASR. "
                "Sound-close ASR substitutions are corrected to the intended Li Bai adaptation when context and "
                "pronunciation support the phrase; unsupported dense prompt lines were omitted or merged."
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
        "title": "蜀道难",
        "localizedTitles": {"zh-Hans": "蜀道难", "en": "The Hard Road to Shu", "ja": "蜀道難"},
        "artist": "Musia",
        "description": "An ACE-Step Mandarin normal-song adaptation of Li Bai's 蜀道难, corrected against the selected vocal's own ASR evidence.",
        "caption": "A vast xianxia ballad about cliffs, sky roads, and walking forward through impossible mountains.",
        "duration": round(duration(SELECTED_WAV), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "蜀道难 - Fun Lazying Art",
            "description": "A Musia Mandarin adaptation of Li Bai's 蜀道难 with corrected trilingual lyrics.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "蜀道难 cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1672, "height": 941},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1672, "height": 941},
            "primaryAudio": {
                "id": "shu-dao-nan-zh",
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
            "key": "D minor requested / detected A-F#m-D centered progression",
            "bpm": round(float(run_manifest.get("tempo_bpm", 129.19921875)), 3),
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
            "audioSource": "ACE-Step 1.5 XL Turbo v2-clear candidate seed 735202.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {"vocalStemLargeV3Overlap": 0.4308510638297872, "selectedLargeV3Overlap": 0.2925531914893617, "gate": "review-with-correction"},
            "lyricCorrection": "Corrected from selected/vocal-stem large-v3 ASR and no-VAD passes. The public lyrics use ASR timing and preserve intended phrases where substitutions are sound-close and context-supported.",
            "sourcePoem": str((PROJECT / "source/source-poem.md").relative_to(ROOT)),
            "coverSource": "Generated 16:9 cover with Codex image generation; original saved under ~/.codex/generated_images.",
            "publicAudio": PUBLIC_AUDIO_NAME,
        },
        "artifacts": [],
    }
    write_json(media_dir / "manifest.json", manifest)


def update_catalog() -> None:
    path = ROOT / "website/data/catalog.json"
    catalog = read_json(path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "蜀道难",
        "artist": "Musia",
        "summary": "A cinematic ACE-Step Mandarin normal-song adaptation of Li Bai's 蜀道难, with ASR-corrected trilingual lyrics, pinyin, furigana, and chord timing.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "Li Bai", "Tang poetry", "Mandarin", "ACE-Step", "xianxia", "pinyin", "furigana"],
    }
    items = [existing for existing in catalog["items"] if existing.get("id") != MEDIA_ID]
    insert_at = next((index + 1 for index, existing in enumerate(items) if existing.get("id") == "meng-you-tian-mu"), 5)
    items.insert(insert_at, item)
    catalog["items"] = items
    write_json(path, catalog)


def main() -> None:
    ensure_audio()
    write_media_item()
    update_catalog()
    print(ROOT / "website/data/songs" / MEDIA_ID / "manifest.json")


if __name__ == "__main__":
    main()

