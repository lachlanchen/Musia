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
MEDIA_ID = "chi-le-ge-original-poem"
PROJECT = ROOT / "data/creative_projects/chi-le-ge-original-poem-20260706"
SELECTED_WAV = PROJECT / "selected/chi-le-ge-original-poem-zh-Hans-ace-xl-turbo-seed748143.wav"
SELECTED_MP3 = PROJECT / "selected/chi-le-ge-original-poem-zh-Hans-ace-xl-turbo-seed748143.mp3"
ANALYSIS = ROOT / "data/runs/chi-le-ge-original-poem-20260706-selected-analysis"
PUBLIC_AUDIO_NAME = "chi-le-ge-original-poem-zh-Hans-ace-xl-turbo-seed748143-20260706.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/chi-le-ge-original-poem-16x9.png"

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
        ("敕勒", "敕"): "chi4",
        ("敕勒", "勒"): "le4",
        ("穹庐", "穹"): "qiong2",
        ("穹庐", "庐"): "lu2",
        ("笼盖", "笼"): "long3",
        ("四野", "野"): "ya3",
        ("野茫茫", "野"): "ya3",
        ("见牛羊", "见"): "xian4",
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
    # Timings come from large-v3 ASR on the selected seed 748143 render.
    # The opening couplets diverged from the source poem, so the public active
    # vocal lyric uses ASR-close text there. The clearer later hook preserves
    # the original poem wording, with 野 annotated as ya3 per user correction.
    return [
        (
            "l01",
            0.50,
            3.10,
            "天擦穿云霞",
            "The sky brushes through cloud and rosy haze.",
            "空が雲霞をかすめて抜ける",
        ),
        (
            "l02",
            3.40,
            7.56,
            "天似秋露，盖丝颜",
            "The sky seems like autumn dew, veiling a silk-bright color.",
            "空は秋の露のように、絹めいた色を覆う",
        ),
        (
            "l03",
            14.63,
            19.91,
            "坠落船，云山下",
            "A falling boat under clouded mountains.",
            "落ちゆく舟が雲の山の下にある",
        ),
        (
            "l04",
            21.37,
            26.83,
            "天似秋露，露盖丝颜",
            "The sky seems like autumn dew; dew veils a silk-bright color.",
            "空は秋の露のように、露が絹めいた色を覆う",
        ),
        (
            "l05",
            27.45,
            30.17,
            "天苍苍，野茫茫",
            "The sky is vast; the wilds are boundless.",
            "空は蒼く、野は茫々としている",
        ),
        (
            "l06",
            30.27,
            33.63,
            "风吹草低，见牛羊",
            "Wind bends the grass low, revealing cattle and sheep.",
            "風が草を低く吹き、牛と羊が見える",
        ),
        (
            "l07",
            55.66,
            58.70,
            "天苍苍，野茫茫",
            "The sky is vast; the wilds are boundless.",
            "空は蒼く、野は茫々としている",
        ),
        (
            "l08",
            58.72,
            65.54,
            "风吹草低，见牛羊",
            "Wind bends the grass low, revealing cattle and sheep.",
            "風が草を低く吹き、牛と羊が見える",
        ),
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
                "ACE-Step seed 748143. Timings use large-v3 ASR on the selected vocal. "
                "Public Mandarin preserves the original poem wording where the sound is close; "
                "the later hook is clearer than the opening couplets."
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
        "title": "敕勒歌 · 原文版",
        "localizedTitles": {
            "zh-Hans": "敕勒歌 · 原文版",
            "en": "Chile Song · Original Poem Version",
            "ja": "敕勒歌・原文版",
        },
        "artist": "Musia",
        "description": "A northern grassland folk-song render of 敕勒歌 using only original poem lines with repetition and ASR-corrected timing.",
        "caption": "Sky like a felt tent, endless wilds, wind bending the grass until cattle and sheep appear.",
        "duration": round(duration(SELECTED_WAV), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "敕勒歌 · 原文版 - Fun Lazying Art",
            "description": "Musia ACE-Step grassland folk render from the original 敕勒歌 lines.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "敕勒歌 grassland cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": "chi-le-ge-original-poem-zh",
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
            "key": "D major requested; detected Am/Bm/D/A/Em movement",
            "bpm": round(float(run_manifest.get("tempo_bpm", 143.5546875)), 3),
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
        "artifacts": [
            {"label": "Stems", "path": str((ANALYSIS / "stems").relative_to(ROOT))},
            {"label": "Chords CSV", "path": str((ANALYSIS / "analysis/chords.csv").relative_to(ROOT))},
            {"label": "Beats CSV", "path": str((ANALYSIS / "analysis/beats.csv").relative_to(ROOT))},
            {"label": "ASR JSON", "path": str((ANALYSIS / "analysis/lyrics.json").relative_to(ROOT))},
        ],
        "provenance": {
            "createdBy": "Musia",
            "generationProject": str(PROJECT.relative_to(ROOT)),
            "audioSource": "ACE-Step 1.5 XL Turbo, coupled original-poem route, selected seed 748143.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {
                "selectedMediumAsrOverlap": 0.2835820895522388,
                "gate": "review-original-poem",
            },
            "lyricCorrection": (
                "Corrected 2026-07-06 from large-v3 ASR and the original 敕勒歌 source text. "
                "The opening couplets are now published as ASR-close text because the render diverges from the source; "
                "the later 天苍苍/风吹草低 hook is clearer. 见 is published with pinyin xian4 and 野 with pinyin ya3."
            ),
            "pronunciationGuide": str((PROJECT / "source/pronunciation-guide.md").relative_to(ROOT)),
            "cover": {
                "src": COVER,
                "source": "Generated no-text 16:9 grassland cover via image generation; cropped to 1600x900.",
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
        "title": "敕勒歌 · 原文版",
        "artist": "Musia",
        "summary": "A northern grassland ACE-Step render from the original 敕勒歌 lines, with ASR-corrected trilingual lyrics, pinyin, furigana, chords, and beats.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "classical-poetry", "northern-dynasties", "grassland", "Mandarin", "ACE-Step", "original-poem", "pinyin", "furigana"],
    }
    items = [entry for entry in catalog.get("items", []) if entry.get("id") != MEDIA_ID]
    anchor = next((index for index, entry in enumerate(items) if entry.get("id") == "liang-zhou-ci-double-original-poem"), 4)
    items.insert(anchor + 1, item)
    catalog["items"] = items
    write_json(path, catalog)


def write_project_notes() -> None:
    selected = PROJECT / "SELECTED_VERSION.md"
    selected.write_text(
        "\n".join(
            [
                "# 敕勒歌 · 原文版",
                "",
                "- Selected audio: `selected/chi-le-ge-original-poem-zh-Hans-ace-xl-turbo-seed748143.wav`",
                "- Public audio: `../MusiaSongs/audio/chi-le-ge-original-poem-zh-Hans-ace-xl-turbo-seed748143-20260706.mp3`",
                "- Website id: `chi-le-ge-original-poem`",
                "- Selected model: `acestep-v15-xl-turbo`",
                "- Selected seed: `748143`",
                "- Route: coupled original poem lines with private pronunciation controls.",
                "- Analysis run: `data/runs/chi-le-ge-original-poem-20260706-selected-analysis`",
                "",
                "Candidate summary:",
                "",
                "- XL Turbo private-control line route seeds 748120-748123: rejected except 748121 had partial recovery.",
                "- XL Turbo public-text route seeds 748131-748134: rejected; low recovery.",
                "- XL Turbo coupled-control route seeds 748141-748144: selected 748143 as best available.",
                "- XL SFT coupled-public seeds 748151-748152: rejected; one candidate sang unrelated outro text.",
                "- v15 Turbo simple-control seeds 748161-748164: rejected; lower recovery than 748143.",
                "",
                "Lyric correction policy:",
                "",
                "- Opening couplets use ASR-close text because the render diverged from the source.",
                "- `见牛羊` is published with pinyin `xian4 niu2 yang2`.",
                "- `野` is published with pinyin `ya3` per the corrected reading.",
                "- The later hook remains the clearest source-poem section.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    reference = ROOT / "references/chi-le-ge-original-poem-production-2026-07-06.md"
    reference.write_text(
        "\n".join(
            [
                "# 敕勒歌 Original Poem Song Production",
                "",
                "Generated for Musia on 2026-07-06.",
                "",
                "## Source",
                "",
                "```text",
                "敕勒川，阴山下。",
                "天似穹庐，笼盖四野。",
                "天苍苍，野茫茫，",
                "风吹草低见牛羊。",
                "```",
                "",
                "## Pronunciation Controls",
                "",
                "- Public `敕勒川`; private control `赤乐川` to encourage `chi4 le4 chuan1`.",
                "- Public/source `笼盖四野`; private control `拢盖四野` to encourage `long3 gai4 si4 ya3`.",
                "- Public `见牛羊`; private control `现牛羊`, restored publicly with pinyin `xian4 niu2 yang2`.",
                "- `野` is annotated as `ya3` in the public lyric tracks.",
                "",
                "## Selected Render",
                "",
                "- Model: `acestep-v15-xl-turbo`.",
                "- Seed: `748143`.",
                "- Audio: `data/creative_projects/chi-le-ge-original-poem-20260706/selected/chi-le-ge-original-poem-zh-Hans-ace-xl-turbo-seed748143.wav`.",
                "- Website id: `chi-le-ge-original-poem`.",
                "- Public URL: `https://fun.lazying.art/#chi-le-ge-original-poem`.",
                "",
                "## Audit",
                "",
                "The selected render was chosen from 18 candidates. Medium-ASR overlap was highest for seed `748143` at `0.2836`. Large-v3 ASR confirms the later hook `天苍苍，野茫茫 / 风吹草低，见牛羊` is the clearest part. On 2026-07-07 the opening couplets were changed from source-restored text to ASR-close text because the audio diverges too much from the poem there. This item should not be treated as a perfect exact poem recitation.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    write_media_item()
    update_catalog()
    write_project_notes()
    print(f"https://fun.lazying.art/#{MEDIA_ID}")


if __name__ == "__main__":
    main()
