#!/usr/bin/env python3
from __future__ import annotations

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
MEDIA_ID = "best-am-i"
PROJECT = ROOT / "data/creative_projects/best-am-i-20260712"
ANALYSIS = ROOT / "data/runs/best-am-i-20260712-analysis"
SELECTED_MP3 = PROJECT / "selected/best-am-i-mixed-ace-xl-turbo-seed812401.mp3"
SELECTED_WAV = PROJECT / "selected/best-am-i-mixed-ace-xl-turbo-seed812401.wav"
PUBLIC_AUDIO_NAME = "best-am-i-mixed-ace-xl-turbo-seed812401-20260712.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/best-am-i-16x9.png"
COVER_SOURCE = Path(
    "/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/"
    "ig_02a348b19ca3f962016a531567298481909c58ed5626f8a703.png"
)
CORRECTION_PACKET = PROJECT / "correction_packets/selected-seed812401-20260712-121122/CORRECTION_PACKET.md"

LANG = {
    "mul": {"code": "mul", "label": "Mixed", "nativeLabel": "Mixed", "script": "Latn+Hans+Jpan"},
    "en": {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn"},
    "zh-Hans": {"code": "zh-Hans", "label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "pronunciation": "pinyin"},
    "ja": {"code": "ja", "label": "Japanese", "nativeLabel": "日本語", "script": "Jpan", "pronunciation": "furigana"},
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
    for mark in [",", ".", "?", "!", ";", ":"]:
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
    if code == "en":
        return split_en(text)
    if code == "ja":
        return split_ja(text)
    if code == "mul":
        parts: list[str] = []
        current = ""
        for char in text:
            if char.isspace():
                if current:
                    parts.append(current)
                    current = ""
            elif is_cjk(char) or "\u3040" <= char <= "\u30ff" or char in ",.!?;:":
                if current:
                    parts.append(current)
                    current = ""
                parts.append(char)
            else:
                current += char
        if current:
            parts.append(current)
        return parts
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
        japanese_context = code == "ja" or (code == "mul" and has_kana(line["text"]))
        if code == "zh-Hans" or (code == "mul" and is_cjk(part) and not japanese_context):
            reading = zh_pinyin(part)
            if reading:
                token["pinyin"] = reading
        if japanese_context:
            reading = ja_reading(part)
            if reading:
                token["reading"] = reading
        tokens.append(token)
    return tokens


def make_line(line_id: str, start: float, end: float, text: str, code: str) -> dict[str, Any]:
    line = {"id": line_id, "start": round(start, 3), "end": round(end, 3), "text": text, "singableText": text, "role": "lyric"}
    line["tokens"] = tokens_for(line, code)
    return line


def corrected_rows() -> list[tuple[str, float, float, str, str, str, str]]:
    """ASR/listening correction for selected ACE XL Turbo seed 812401.

    Evidence: full-mix and Demucs vocal-stem ASR, with normal and no-VAD
    medium/large-v3 checks. The selected render sings a compact version and
    stops around 60s. Unsung draft bridge lines are intentionally omitted.
    Sound-close prompt forms are restored when they are more musical than the
    ASR guess, especially `Best am I`, `Wo shi tian xia di yi deng`,
    `Mada ikeru`, and `Dare ni mo mienai namida`.
    """

    return [
        ("l01", 0.00, 5.08, "Best am I, I am still becoming", "Best am I, I am still becoming", "私は最高、まだ変わり続けている", "我是最好的我，我仍在成为"),
        ("l02", 5.08, 10.32, "Wo shi tian xia di yi deng", "I am first-rate under heaven", "私は天下一等", "我是天下第一等"),
        ("l03", 11.00, 12.82, "Mada ikeru", "I can still go on", "まだ行ける", "我还能继续"),
        ("l04", 12.82, 16.32, "I was small under the sky", "I was small under the sky", "空の下で小さかった", "我曾在天空下很渺小"),
        ("l05", 16.32, 18.82, "Still I kept a little flame", "Still I kept a little flame", "それでも小さな炎を守った", "仍守着一点火光"),
        ("l06", 18.82, 21.00, "Dare ni mo mienai namida", "Tears no one can see", "誰にも見えない涙", "谁也看不见的眼泪"),
        ("l07", 21.52, 23.34, "Ye li you guang zai", "There is light in the night", "夜にも光がある", "夜里有光在"),
        ("l08", 23.34, 26.30, "I do not need a crown", "I do not need a crown", "冠はいらない", "我不需要王冠"),
        ("l09", 26.30, 29.10, "I only need my name", "I only need my name", "必要なのは私の名前だけ", "我只需要自己的名字"),
        ("l10", 29.10, 33.56, "Tada koko ni tatsu, I rise, I shine", "I stand right here, I rise, I shine", "ただここに立つ、I rise, I shine", "我就站在这里，升起，发光"),
        ("l11", 33.56, 37.66, "Best am I, best am I, best am I", "Best am I, best am I, best am I", "私は最高、私は最高、私は最高", "我是最好的我，最好的我，最好的我"),
        ("l12", 37.66, 40.28, "Wo shi tian xia di yi deng", "I am first-rate under heaven", "私は天下一等", "我是天下第一等"),
        ("l13", 40.28, 45.26, "Mune no hikari mada kienai, I am still becoming", "The light in my heart has not gone out; I am still becoming", "胸の光まだ消えない、私はまだ変わり続けている", "心里的光还没熄灭，我仍在成为"),
        ("l14", 45.78, 49.00, "Best am I, best am I", "Best am I, best am I", "私は最高、私は最高", "我是最好的我，最好的我"),
        ("l15", 49.00, 51.58, "Wo you wo de di yi deng", "I have my own first place", "私には私の一等がある", "我有我的第一等"),
        ("l16", 51.58, 54.72, "I rise, I shine", "I rise, I shine", "私は昇り、輝く", "我升起，我发光"),
        ("l17", 54.72, 56.78, "I am not done", "I am not done", "まだ終わっていない", "我还没有结束"),
        ("l18", 56.78, 60.16, "I am still becoming", "I am still becoming", "私はまだ変わり続けている", "我仍在成为"),
    ]


def build_tracks() -> dict[str, list[dict[str, Any]]]:
    lines = {"mul": [], "en": [], "zh-Hans": [], "ja": []}
    for line_id, start, end, active, en, ja, zh in corrected_rows():
        lines["mul"].append(make_line(line_id, start, end, active, "mul"))
        lines["en"].append(make_line(line_id, start, end, en, "en"))
        lines["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans"))
        lines["ja"].append(make_line(line_id, start, end, ja, "ja"))
    return lines


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
                "Corrected from selected ACE XL Turbo seed 812401 using full-mix and vocal-stem "
                "medium/large-v3 ASR, including no-VAD passes. Planned lines after the rendered ending "
                "are omitted. Sound-close intended wording is restored where stronger than ASR guesses."
            ),
            "correctionPacket": str(CORRECTION_PACKET.relative_to(ROOT)),
        },
    }


def load_chords() -> list[dict[str, Any]]:
    raw = read_json(ANALYSIS / "analysis/chords.json").get("chords", [])
    total = duration(SELECTED_MP3)
    detected: list[dict[str, Any]] = []
    for item in raw:
        start = max(0.0, min(total, float(item["start"])))
        end = max(start, min(total, float(item["end"])))
        if end - start < 0.05:
            continue
        chord = {"start": round(start, 3), "end": round(end, 3), "name": item.get("chord") or item.get("name") or "N.C.", "degree": ""}
        if detected and detected[-1]["name"] == chord["name"] and abs(detected[-1]["end"] - chord["start"]) < 0.08:
            detected[-1]["end"] = chord["end"]
        else:
            detected.append(chord)
    if detected and detected[-1]["end"] < total:
        detected[-1]["end"] = round(total, 3)
    return detected


def ensure_audio() -> None:
    if not SELECTED_MP3.exists():
        raise FileNotFoundError(f"Missing selected audio: {SELECTED_MP3}")
    target = SONGS / "audio" / PUBLIC_AUDIO_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SELECTED_MP3, target)
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
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "Best Am I · 我是天下第一等",
        "localizedTitles": {"en": "Best Am I", "zh-Hans": "我是天下第一等", "ja": "Best Am I"},
        "artist": "Musia",
        "description": "A mixed English, Mandarin pinyin, and Japanese romaji motivational art-pop anthem about self-belief without arrogance.",
        "caption": "A small voice steps into the light and chooses to keep becoming.",
        "duration": round(duration(SELECTED_MP3), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "Best Am I · 我是天下第一等 - Fun Lazying Art",
            "description": "A Musia mixed-language anthem with corrected synced lyrics, translations, pinyin, furigana, chords, and stems.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "Best Am I cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": "best-am-i-mixed",
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
        "musical": {"key": "detected D major / pop modal center", "bpm": 117.45383522727273, "timeSignature": "4/4", "chords": load_chords()},
        "textTracks": [],
        "lyricSets": [
            {
                "id": "mixed-vocal",
                "label": "Mixed vocal",
                "languageCode": "mul",
                "tracks": [
                    {"code": "mul", "label": "Mixed", "nativeLabel": "Mixed", "script": "Latn+Hans+Jpan", "features": ["active-vocal"], "path": "lyrics/mixed-vocal/mul.json"},
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
            "audioSource": "ACE-Step 1.5 XL Turbo compact mixed-language anthem route, seed 812401.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {
                "gate": "public-candidate",
                "note": "Selected after rejecting longer dense routes and XL SFT. Website lyrics are corrected to the rendered compact vocal.",
            },
            "lyricCorrection": str(CORRECTION_PACKET.relative_to(ROOT)),
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
        "title": "Best Am I · 我是天下第一等",
        "artist": "Musia",
        "summary": "A mixed English, Mandarin pinyin, and Japanese romaji motivational art-pop anthem about self-belief and becoming.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["mul", "en", "zh-Hans", "ja"],
        "tags": ["music", "multilingual", "anthem", "self-belief", "ACE-Step", "pinyin", "furigana", "chords"],
    }
    items = [existing for existing in catalog["items"] if existing.get("id") != MEDIA_ID]
    items.insert(0, item)
    catalog["items"] = items
    write_json(path, catalog)


def write_reference() -> None:
    reference = ROOT / "references/best-am-i-production-2026-07-12.md"
    existing = reference.read_text(encoding="utf-8") if reference.exists() else "# Best Am I Production Note\n"
    addition = f"""

## Website Publication

- Media ID: `{MEDIA_ID}`
- URL: `https://fun.lazying.art/#{MEDIA_ID}`
- Manifest: `website/data/songs/{MEDIA_ID}/manifest.json`
- Active lyric: `website/data/songs/{MEDIA_ID}/lyrics/mixed-vocal/mul.json`
- Public audio: `{PUBLIC_AUDIO}`
- Public audio file: `../MusiaSongs/audio/{PUBLIC_AUDIO_NAME}`
- Cover: `website/{COVER}`
- Cover source: `{COVER_SOURCE}`
- Correction packet: `{CORRECTION_PACKET.relative_to(ROOT)}`

The public lyric set contains 18 sung lines only. The selected render ends its
vocal around `60.16s`; draft lines after that are not published as lyrics. The
active mixed line keeps intended sound-close forms such as `Best am I`,
`Wo shi tian xia di yi deng`, `Mada ikeru`, and `Dare ni mo mienai namida`
instead of awkward ASR guesses.
"""
    if "## Website Publication" not in existing:
        reference.write_text(existing.rstrip() + "\n" + addition.lstrip(), encoding="utf-8")


def main() -> None:
    ensure_audio()
    make_cover()
    write_media_item()
    update_catalog()
    write_reference()
    print(ROOT / "website/data/songs" / MEDIA_ID / "manifest.json")


if __name__ == "__main__":
    main()
