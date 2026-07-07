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
MEDIA_ID = "the-babiest"
PROJECT = ROOT / "data/creative_projects/the-babiest-20260707"
SELECTED_AUDIO = PROJECT / "selected/the-babiest-mixed-ace-xl-turbo-seed770711.mp3"
ANALYSIS = ROOT / "data/runs/the-babiest-20260707-seed770711-analysis"
PUBLIC_AUDIO_NAME = "the-babiest-mixed-ace-xl-turbo-seed770711-20260707.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/the-babiest-16x9.png"
COVER_SOURCE = Path(
    "/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/"
    "ig_0392de60964c20f7016a4d0484a0548191a1ff63e71e693dd0.png"
)

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
    """ASR/listening correction for selected ACE XL Turbo seed 770711.

    The model follows the opening, verse, pre-chorus, and first chorus well,
    then ends before the planned bridge/final chorus. The public track omits
    unsung planned lines. Sound-close intended forms are preserved for phrases
    such as `Wo shi baby`, `tiny tonight`, `Man man bao jin wo`, and
    `Chiisana heart`; clear model-language changes are published as sung.
    """

    return [
        ("l01", 0.27, 2.31, "Tell a secret", "Tell a secret", "秘密を教えるね", "告诉你一个秘密"),
        ("l02", 2.31, 5.49, "I am a baby", "I am a baby", "私はベイビー", "我是 baby"),
        ("l03", 5.49, 8.49, "Wo shi baby", "I am a baby", "私はベイビー", "我是 baby"),
        ("l04", 8.49, 10.77, "Call me baby", "Call me baby", "ベイビーって呼んで", "叫我 baby"),
        ("l05", 10.77, 15.93, "I try to be brave, but I am tiny tonight", "I try to be brave, but I am tiny tonight", "強がるけれど 今夜は小さい私", "我努力勇敢，可今晚我很小很小"),
        ("l06", 15.93, 18.45, "Man man bao jin wo", "Hold me slowly and close", "ゆっくり強く抱きしめて", "慢慢抱紧我"),
        ("l07", 18.45, 20.97, "Say it is all right", "Say it is all right", "大丈夫だと言って", "告诉我没关系"),
        ("l08", 20.97, 25.35, "I hide in your light", "I hide in your light", "あなたの光に隠れる", "我躲进你的光里"),
        ("l09", 25.35, 27.15, "I want to cry a little", "I want to cry a little", "ちょっとだけ泣きたい", "我有点想哭"),
        ("l10", 27.15, 31.11, "I want to cry a little", "I want to cry a little", "ちょっとだけ泣きたい", "我有点想哭"),
        ("l11", 31.11, 34.51, "Hold me one more time", "Hold me one more time", "もう一度抱きしめて", "再抱我一次"),
        ("l12", 34.51, 37.47, "Baby, baby, don't let go", "Baby, baby, don't let go", "ベイビー 離さないで", "Baby，baby，别放手"),
        ("l13", 37.47, 38.57, "It's alright", "It's alright", "大丈夫", "没关系"),
        ("l14", 38.57, 40.17, "Tell me so", "Tell me so", "そう言って", "这样告诉我"),
        ("l15", 40.17, 42.59, "Don't smile, just love me", "Don't smile, just love me", "笑わずに ただ愛して", "别笑我，只爱我"),
        ("l16", 42.59, 43.69, "Soft and low", "Soft and low", "やさしく低く", "轻轻地，低低地"),
        ("l17", 45.05, 47.63, "I am a baby", "I am a baby", "私はベイビー", "我是 baby"),
        ("l18", 47.63, 49.17, "The babiest baby", "The babiest baby", "いちばんベイビー", "最 baby 的 baby"),
        ("l19", 49.17, 50.35, "Call me baby", "Call me baby", "ベイビーって呼んで", "叫我 baby"),
        ("l20", 50.35, 51.49, "Call me maybe", "Call me maybe", "たぶん呼んで", "也许就这样叫我"),
        ("l21", 53.65, 56.49, "In your arms I can breathe", "In your arms I can breathe", "あなたの腕で息ができる", "在你怀里我能呼吸"),
        ("l22", 56.49, 57.95, "I am a baby", "I am a baby", "私はベイビー", "我是 baby"),
        ("l23", 57.95, 59.47, "The babiest baby", "The babiest baby", "いちばんベイビー", "最 baby 的 baby"),
        ("l24", 59.47, 61.89, "Chiisana heart", "Tiny little heart", "ちいさな heart", "小小的心"),
        ("l25", 61.89, 62.89, "Still crazy", "Still crazy", "まだ crazy", "仍然 crazy"),
        ("l26", 62.89, 64.19, "Tell a secret", "Tell a secret", "秘密を教えるね", "告诉你一个秘密"),
        ("l27", 64.19, 65.39, "I am safe", "I am safe", "私は安全だよ", "我很安全"),
        ("l28", 65.39, 66.87, "When you call me baby", "When you call me baby", "あなたがベイビーと呼ぶ時", "当你叫我 baby"),
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
                "Corrected from the selected ACE XL Turbo seed 770711 vocal using same-render medium ASR, "
                "the planned mixed-language lyric, and sound-close correction. Unsung planned bridge/final-chorus lines "
                "are intentionally omitted from the public timing."
            ),
        },
    }


def build_tracks() -> dict[str, list[dict[str, Any]]]:
    lines = {"mul": [], "en": [], "zh-Hans": [], "ja": []}
    for line_id, start, end, active, en, ja, zh in corrected_rows():
        lines["mul"].append(make_line(line_id, start, end, active, "mul"))
        lines["en"].append(make_line(line_id, start, end, en, "en"))
        lines["zh-Hans"].append(make_line(line_id, start, end, zh, "zh-Hans"))
        lines["ja"].append(make_line(line_id, start, end, ja, "ja"))
    return lines


def load_chords() -> list[dict[str, Any]]:
    raw = read_json(ANALYSIS / "analysis/chords.json").get("chords", [])
    total = duration(SELECTED_AUDIO)
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
    if not SELECTED_AUDIO.exists():
        raise FileNotFoundError(f"Missing selected audio: {SELECTED_AUDIO}")
    target = SONGS / "audio" / PUBLIC_AUDIO_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SELECTED_AUDIO, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)


def make_cover() -> None:
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
        "title": "The Babiest",
        "localizedTitles": {"en": "The Babiest", "zh-Hans": "最 Baby 的 Baby", "ja": "ザ・ベイビエスト"},
        "artist": "Musia",
        "description": "A cute mixed English, Mandarin, and Japanese ACE-Step bedroom-pop song about admitting you still want to be called baby.",
        "caption": "A tiny brave heart asks to be held, named gently, and allowed to rest.",
        "duration": round(duration(SELECTED_AUDIO), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "The Babiest - Fun Lazying Art",
            "description": "A Musia mixed-language bedroom-pop song with corrected synced lyrics, translations, pinyin, furigana, chords, and stems.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "The Babiest cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": "the-babiest-mixed",
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
        "musical": {"key": "detected D major / pop modal center", "bpm": 92.28515625, "timeSignature": "4/4", "chords": load_chords()},
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
            "audioSource": "ACE-Step XL Turbo mixed-language hook route, seed 770711, selected after rejecting the long first sweep for weak lyric recovery.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {"gate": "public-candidate", "note": "Mixed-language ACE render has clear vocal and chorus; lyrics are corrected to the actual sung structure."},
            "lyricCorrection": "Medium ASR on selected render plus planned lyric. Unsung planned lines are omitted.",
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
        "title": "The Babiest",
        "artist": "Musia",
        "summary": "A cute mixed English, Mandarin, and Japanese bedroom-pop song with corrected synced lyrics and chord timing.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["mul", "en", "zh-Hans", "ja"],
        "tags": ["music", "multilingual", "ACE-Step", "bedroom-pop", "pinyin", "furigana", "chords"],
    }
    items = [existing for existing in catalog["items"] if existing.get("id") != MEDIA_ID]
    items.insert(0, item)
    catalog["items"] = items
    write_json(path, catalog)


def write_reference() -> None:
    reference = ROOT / "references/the-babiest-production-2026-07-07.md"
    reference.write_text(
        "\n".join(
            [
                "# The Babiest Production Note",
                "",
                "## Selected Render",
                "",
                "- Route: ACE-Step 1.5 XL Turbo mixed-language hook route.",
                "- Seed: `770711`.",
                "- Selected audio: `data/creative_projects/the-babiest-20260707/selected/the-babiest-mixed-ace-xl-turbo-seed770711.mp3`.",
                f"- Public audio: `{PUBLIC_AUDIO}`.",
                "- Analysis: `data/runs/the-babiest-20260707-seed770711-analysis/`.",
                "",
                "## Correction Policy",
                "",
                "The long first sweep was rejected because ASR only recovered fragments. The hook-led sweep was selected because it recovered the opening, verse, pre-chorus, and chorus with a clear vocal. The website lyric track is corrected from the selected render's medium ASR plus the planned lyric. Unsung bridge/final-chorus prompt lines are omitted instead of being forced into subtitles.",
                "",
                "Sound-close intended forms are preserved where the recognizer guessed awkward text: `Wo shi baby`, `tiny tonight`, `Man man bao jin wo`, `Bie xiao wo` / `Don't smile`, and `Chiisana heart`.",
                "",
                "## Website",
                "",
                f"- URL: `https://fun.lazying.art/#{MEDIA_ID}`.",
                "- Manifest: `website/data/songs/the-babiest/manifest.json`.",
                "- Active lyric: `website/data/songs/the-babiest/lyrics/mixed-vocal/mul.json`.",
                "- Translations: English, Japanese, and Mandarin tracks in the same lyric set.",
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
