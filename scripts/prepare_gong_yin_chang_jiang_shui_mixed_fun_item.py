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
MEDIA_ID = "gong-yin-chang-jiang-shui-mixed"
PROJECT = ROOT / "data/creative_projects/gong-yin-chang-jiang-shui-mixed-20260709"
SELECTED_AUDIO = PROJECT / "selected/gong-yin-chang-jiang-shui-mixed-ace-xl-turbo-seed790904.mp3"
ANALYSIS = ROOT / "data/runs/gong-yin-chang-jiang-shui-mixed-20260709-analysis"
PUBLIC_AUDIO_NAME = "gong-yin-chang-jiang-shui-mixed-ace-xl-turbo-seed790904-20260709.mp3"
PUBLIC_AUDIO = f"https://lazyingart.github.io/MusiaSongs/audio/{PUBLIC_AUDIO_NAME}"
COVER = "assets/covers/gong-yin-chang-jiang-shui-mixed-16x9.png"
COVER_SOURCE = Path(
    "/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/"
    "ig_0d24dd3630bca1cb016a4f2d7908d48191ae5abc734919075a.png"
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
    """ASR/listening correction for selected ACE XL Turbo seed 790904.

    Evidence:
    - Segment-level large-v3 English ASR on the selected vocal stem.
    - Segment-level small ASR from the full selected render.
    - Large-v3 Mandarin ASR as a phonetic cross-check.
    - The compact planned mixed lyric in `lyrics/mixed-hook-phonetic.txt`.

    The selected render compresses the prompt. The public `mul` track includes
    only audible lines. Close source forms are preserved when ASR guessed nearby
    text, such as `Wo zhu`, `Kokoro wa kimi e`, and `Zhi yuan jun xin si wo xin`.
    """

    return [
        ("l01", 0.30, 3.16, "Wo zhu Chang Jiang tou", "I live at the head of the Yangtze.", "私は長江の上流に住む", "我住长江头", "lyric"),
        ("l02", 3.16, 6.94, "You live where the river ends", "You live where the river ends.", "君は川の果てにいる", "你住在江水尽头", "lyric"),
        ("l03", 13.86, 17.12, "Ri ri si jun bu jian jun", "Day after day I miss you but cannot see you.", "日々君を思えど会えない", "日日思君不见君", "lyric"),
        ("l04", 17.12, 20.66, "Still we drink the same water", "Still we drink the same water.", "それでも同じ水を飲む", "我们仍共饮一江水", "lyric"),
        ("l05", 22.24, 25.40, "Onaji kawa no mizu", "The same river water.", "同じ川の水", "同一条河的水", "lyric"),
        ("l06", 28.16, 30.70, "Gong yin Chang Jiang shui", "We drink the Yangtze water together.", "長江の水を共に飲む", "共饮长江水", "lyric"),
        ("l07", 30.70, 33.92, "Same river, same moonlight", "Same river, same moonlight.", "同じ川、同じ月明かり", "同一条河，同一片月光", "lyric"),
        ("l08", 33.92, 36.84, "Kokoro wa kimi e", "My heart goes to you.", "心は君へ向かう", "心与你相连", "lyric"),
        ("l09", 36.84, 41.22, "Zhi yuan jun xin si wo xin", "May your heart be like mine.", "君の心が私の心のようでありますように", "只愿君心似我心", "lyric"),
        ("l10", 41.22, 44.26, "Ci shui ji shi xiu", "When will this water rest?", "この水はいつ休むのか", "此水几时休", "lyric"),
        ("l11", 44.26, 47.08, "Ci hen he shi yi", "When will this longing end?", "この思いはいつ終わるのか", "此恨何时已", "lyric"),
        ("l12", 47.08, 54.06, "When will this river rest, this longing sleep", "When will this river rest, this longing sleep?", "この川はいつ休み、この思いはいつ眠るのか", "此水何时休，此恨何时已", "lyric"),
        ("l13", 54.06, 57.82, "Zhi yuan jun xin si wo xin", "May your heart be like mine.", "君の心が私の心のようでありますように", "只愿君心似我心", "lyric"),
        ("l14", 57.82, 61.20, "Ding bu fu xiang si yi", "I will not betray this longing.", "この相思いを裏切らない", "定不负相思意", "lyric"),
        ("l15", 61.20, 65.95, "Same river, same longing", "Same river, same longing.", "同じ川、同じ想い", "同一条河，同一份相思", "lyric"),
        ("l16", 65.95, 69.80, "Give me all", "Give me all.", "すべてをください", "把一切都给我", "lyric"),
        ("l17", 69.80, 74.04, "♪", "♪", "♪", "♪", "instrumental"),
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
                "Corrected from selected ACE XL Turbo seed 790904 using segment-level large-v3 English ASR on "
                "the vocal stem, full-render small ASR, large-v3 Mandarin ASR cross-check, and the compact planned "
                "mixed lyric. Prompt lines not audibly recovered by the selected render are omitted."
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
        "title": "共饮长江水 · Same River",
        "localizedTitles": {
            "zh-Hans": "共饮长江水",
            "en": "Same River",
            "ja": "同じ川の水",
        },
        "artist": "Musia",
        "description": "A mixed English, Mandarin pinyin, and Japanese romaji river elegy inspired by Li Zhiyi's 我住长江头.",
        "caption": "Two distant banks share one river, one moon, and one faithful longing.",
        "duration": round(duration(SELECTED_AUDIO), 3),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "共饮长江水 · Same River - Fun Lazying Art",
            "description": "A Musia mixed-language river elegy with corrected synced lyrics, translations, pinyin, furigana, chords, and stems.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": COVER,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {"id": "cover", "label": "Moonlit Yangtze cover", "role": "cover", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "poster": {"id": "poster", "label": "16:9 Poster", "role": "poster", "src": COVER, "mime": "image/png", "width": 1600, "height": 900},
            "primaryAudio": {
                "id": "gong-yin-chang-jiang-shui-mixed",
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
            "key": "A minor / moonlit river elegy",
            "bpm": round(float(run_manifest.get("tempo_bpm", 143.5546875)), 3),
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
            "audioSource": "ACE-Step 1.5 XL Turbo mixed-language hook route, seed 790904, selected from a four-seed sweep.",
            "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "quality": {
                "gate": "public-candidate",
                "note": "Clear vocal and graceful river-ballad mood. The render compresses the prompt; public lyrics match audible structure.",
            },
            "lyricCorrection": "Segment-level large-v3 English ASR on selected vocal stem plus full-render small ASR and large-v3 Mandarin cross-check. Close intended forms are preserved; missing prompt lines are documented rather than forced.",
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
        "title": "共饮长江水 · Same River",
        "artist": "Musia",
        "summary": "A mixed English, Japanese romaji, and Mandarin pinyin river elegy inspired by Li Zhiyi's 我住长江头.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": COVER,
        "languages": ["mul", "en", "zh-Hans", "ja"],
        "tags": ["music", "multilingual", "Song poetry", "Li Zhiyi", "ACE-Step", "pinyin", "furigana", "chords"],
    }
    items = [existing for existing in catalog["items"] if existing.get("id") != MEDIA_ID]
    items.insert(0, item)
    catalog["items"] = items
    write_json(path, catalog)


def write_reference() -> None:
    reference = ROOT / "references/gong-yin-chang-jiang-shui-mixed-production-2026-07-09.md"
    reference.write_text(
        "\n".join(
            [
                "# 共饮长江水 · Same River Production Note",
                "",
                "## Source Poem",
                "",
                "The source is Li Zhiyi's Song-dynasty lyric `卜算子·我住长江头`. The canonical opening is `我住长江头，君住长江尾`; the user phrase `君住长江头，我住长江尾` was corrected for source reference.",
                "",
                "```text",
                "我住长江头，君住长江尾。",
                "日日思君不见君，共饮长江水。",
                "此水几时休？此恨何时已？",
                "只愿君心似我心，定不负相思意。",
                "```",
                "",
                "## Selected Render",
                "",
                "- Route: ACE-Step 1.5 XL Turbo mixed-language hook route.",
                "- Seed: `790904`.",
                "- Selected audio: `data/creative_projects/gong-yin-chang-jiang-shui-mixed-20260709/selected/gong-yin-chang-jiang-shui-mixed-ace-xl-turbo-seed790904.mp3`.",
                f"- Public audio: `{PUBLIC_AUDIO}`.",
                "- Analysis: `data/runs/gong-yin-chang-jiang-shui-mixed-20260709-analysis/`.",
                "- Website manifest: `website/data/songs/gong-yin-chang-jiang-shui-mixed/manifest.json`.",
                "",
                "## Generation Recipe",
                "",
                "This song used the hook-led mixed-language ACE route, not a native-character poem-recitation route. The model-facing lyric was written mostly in Latin letters:",
                "",
                "```text",
                "Wo zhu Chang Jiang tou",
                "You live where the river ends",
                "Ri ri si jun bu jian jun",
                "Still we drink the same water",
                "Onaji kawa no mizu",
                "Gong yin Chang Jiang shui",
                "Same river, same moonlight",
                "Kokoro wa kimi e",
                "Zhi yuan jun xin si wo xin",
                "Ci shui ji shi xiu",
                "Ci hen he shi yi",
                "When will this river rest",
                "When will this longing sleep",
                "Zhi yuan jun xin si wo xin",
                "Ding bu fu xiang si yi",
                "Same river, same longing",
                "Kimi o omou",
                "```",
                "",
                "This was intentional. For this ACE-Step mixed EN/JP/ZH route, Mandarin pinyin and Japanese romaji gave the model a clearer phonetic path than mixing English with native Chinese characters and Japanese kana/kanji in the same lyric block. The pronunciation is still not perfect, but the pinyin/romaji route produced better musical continuity, less garbling, and a more singable result than prior mixed native-script attempts.",
                "",
                "Config:",
                "",
                "```text",
                "config_path = \"acestep-v15-xl-turbo\"",
                "task_type = \"text2music\"",
                "duration = 74",
                "bpm = 72",
                "keyscale = \"A minor\"",
                "timesignature = \"4\"",
                "vocal_language = \"en\"",
                "inference_steps = 8",
                "guidance_scale = 1.0",
                "seeds = [790901, 790902, 790903, 790904]",
                "```",
                "",
                "Caption strategy:",
                "",
                "- state the emotional story plainly: two people separated along the Yangtze;",
                "- ask for `mixed English lead with Mandarin pinyin and Japanese romaji`;",
                "- keep arrangement vivid but not crowded: piano, guzheng/pipa color, strings, subtle drums, water ambience, spacious reverb;",
                "- include negative constraints: no crammed words, no clipped endings, no buried vocal, no spoken narration, no real singer imitation.",
                "",
                "Commands:",
                "",
                "```bash",
                "data/creative_projects/gong-yin-chang-jiang-shui-mixed-20260709/commands.sh generate-hook",
                "data/creative_projects/gong-yin-chang-jiang-shui-mixed-20260709/commands.sh quality-hook <candidate.wav>",
                "data/creative_projects/gong-yin-chang-jiang-shui-mixed-20260709/commands.sh analyze <selected.wav>",
                "```",
                "",
                "Candidate selection:",
                "",
                "- `790901`: weak lyric recovery;",
                "- `790902`: recovered only fragments;",
                "- `790903`: mostly gibberish;",
                "- `790904`: best recovery of `Chang Jiang`, `You live where the river ends`, `Ri ri si jun bu jian jun`, `Gong yin Chang Jiang shui`, and the final chorus shape, so it was selected.",
                "",
                "Reusable rule: for mixed EN/JP/ZH ACE songs, use a phonetic active-vocal layer when pronunciation matters. Publish native-language companion tracks as translations, not as the active sung layer, unless the audio clearly sings the native script.",
                "",
                "## Correction Notes",
                "",
                "The selected render compresses the planned prompt. Public lyrics use the actual audible mixed vocal as the active layer and translate that layer into English, Japanese, and Mandarin. Extra prompt lines such as `Every day I miss you`, `Across the river wide`, and `Kimi o omou` were not audibly recovered clearly enough for public timing.",
                "",
                "Close intended forms are preserved where ASR drifted phonetically: `Wo zhu Chang Jiang tou`, `Onaji kawa no mizu`, `Kokoro wa kimi e`, `Zhi yuan jun xin si wo xin`, and `Ci hen he shi yi`.",
                "",
                "2026-07-09 tail correction: user listening found that the earlier `Wo xiang xin` correction was wrong. The ending is `Ding bu fu xiang si yi`, followed by `Same river, same longing`, then a soft English phrase close to `Give me all`. Focused large-v3 ASR on the soft tail hallucinated unrelated text, so the ending was corrected from manual listening plus VAD instead of ASR alone.",
                "",
                "VAD evidence from the separated vocal stem:",
                "",
                "```text",
                "57.50-58.00 rms=0.03536 active",
                "58.00-61.50 rms=0.04009-0.12910 active",
                "61.50-65.95 active sustained vocal",
                "65.95-69.80 active final soft phrase",
                "70.00-74.00 near-silence / fade",
                "```",
                "",
                "Final public tail:",
                "",
                "```text",
                "57.82-61.20 Ding bu fu xiang si yi",
                "61.20-65.95 Same river, same longing",
                "65.95-69.80 Give me all",
                "69.80-74.04 ♪",
                "```",
                "",
                "Before recording or publishing, use the corrected website active lyric JSON as the source of truth and do not use the original prompt lyric.",
                "",
                "## Website",
                "",
                f"- URL: `https://fun.lazying.art/#{MEDIA_ID}`.",
                "- Active lyric: `website/data/songs/gong-yin-chang-jiang-shui-mixed/lyrics/mixed-vocal/mul.json`.",
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
