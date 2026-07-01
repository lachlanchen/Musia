#!/usr/bin/env python3
"""Prepare experimental DiffRhythm poem-song draft items for Fun Lazying Art.

These items are intentionally marked as DR drafts. They expose useful
generation candidates without replacing polished ACE-Step standard songs.
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from pypinyin import Style, pinyin

try:
    import pykakasi
except Exception:  # pragma: no cover - optional local helper
    pykakasi = None


ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT.parent / "MusiaSongs"
SONGS_AUDIO = SONGS / "audio"
WEBSITE = ROOT / "website"
AUDIO_BASE = "https://lazyingart.github.io/MusiaSongs/audio/"
AUDIO_CACHE_VERSION = "20260701-dr"
MANIFEST_SCHEMA = "fun.lazying.media.manifest.v1"
TEXT_SCHEMA = "fun.lazying.media.text-track.v1"


@dataclass(frozen=True)
class Line:
    id: str
    start: float
    end: float
    zh: str
    en: str
    ja: str


@dataclass(frozen=True)
class DraftItem:
    media_id: str
    title: str
    localized_titles: dict[str, str]
    description: str
    caption: str
    source_audio: Path
    analysis_dir: Path
    source_cover: str
    target_cover: str
    audio_name: str
    tempo_note: str
    lines: list[Line]
    tags: list[str]
    insert_after: str


SHU_LINES = [
    Line("l01", 2.26, 4.70, "蜀道之难", "The road to Shu is hard.", "蜀への道は険しい。"),
    Line("l02", 7.08, 9.66, "难于上青天", "Harder than climbing the blue sky.", "青天へ登るより難しい。"),
    Line("l03", 11.28, 14.10, "噫吁嚱", "Ah, a cry of awe.", "ああ、驚きの嘆き。"),
    Line("l04", 14.10, 19.42, "危乎高哉", "How perilous, how high.", "なんと危うく高いことか。"),
    Line("l05", 20.42, 24.25, "蜀道之难", "The road to Shu is hard.", "蜀への道は険しい。"),
    Line("l06", 24.25, 29.26, "难于上青天", "Harder than climbing the blue sky.", "青天へ登るより難しい。"),
    Line("l07", 30.30, 36.20, "上有六龙回日之高标", "Above, high peaks turn back the sun's six dragons.", "上には太陽の六龍を返す高峰。"),
    Line("l08", 36.20, 42.95, "下有冲波逆折之回川", "Below, broken torrents twist backward through the gorge.", "下には逆巻く波と折れ返る川。"),
    Line("l09", 42.95, 47.80, "又闻子规啼夜月", "Again the cuckoo cries beneath the night moon.", "また夜月にほととぎすが啼く。"),
    Line("l10", 47.80, 52.04, "愁空山", "Grief fills the empty mountains.", "愁いが空山に満ちる。"),
    Line("l11", 52.04, 56.80, "愁空山", "Grief fills the empty mountains.", "愁いが空山に満ちる。"),
    Line("l12", 56.80, 61.20, "连峰去天不盈尺", "Linked peaks fall less than a foot from heaven.", "連なる峰は天まで一尺もない。"),
    Line("l13", 61.20, 66.20, "枯松倒挂倚绝壁", "Withered pines hang upside down from sheer cliffs.", "枯松は絶壁に逆さに掛かる。"),
    Line("l14", 66.20, 71.70, "飞湍瀑流争喧豗", "Flying rapids and waterfalls roar against each other.", "飛ぶ急流と滝が轟き競う。"),
    Line("l15", 71.70, 76.80, "砯崖转石万壑雷", "Stones crash from cliffs like thunder through ten thousand ravines.", "崖を打つ石は万谷の雷となる。"),
    Line("l16", 76.80, 87.00, "锦城虽云乐，不如早还家", "Though Brocade City is called joyful, better to return home soon.", "錦城は楽しいと言えども、早く帰るに及ばない。"),
]

XING_LINES = [
    Line("l01", 2.74, 7.40, "长风破浪会有时", "Someday the long wind will break the waves.", "いつか長風は波を破る。"),
    Line("l02", 8.66, 13.46, "直挂云帆济沧海", "I will raise cloudlike sails and cross the vast sea.", "雲の帆を高く掲げ、蒼海を渡る。"),
    Line("l03", 14.40, 17.60, "行路难", "The road is hard.", "道は険しい。"),
    Line("l04", 17.60, 20.80, "行路难", "The road is hard.", "道は険しい。"),
    Line("l05", 20.80, 24.30, "多歧路", "So many branching paths.", "分かれ道は多い。"),
    Line("l06", 24.30, 28.60, "今安在", "Where is the way now?", "いま道はどこにある。"),
    Line("l07", 31.00, 36.40, "金樽清酒斗十千", "Fine wine in golden cups costs ten thousand a measure.", "金の杯の清酒は一斗十千。"),
    Line("l08", 36.40, 42.70, "玉盘珍羞直万钱", "Rare dishes on jade plates are worth ten thousand coins.", "玉の皿の珍味は万銭に値する。"),
    Line("l09", 42.70, 48.10, "停杯投箸不能食", "I stop my cup, throw down chopsticks, and cannot eat.", "杯を止め、箸を投げ、食べられない。"),
    Line("l10", 48.10, 53.80, "拔剑四顾心茫然", "I draw my sword and look around, my heart bewildered.", "剣を抜き四方を見れば、心は茫然。"),
    Line("l11", 53.80, 59.00, "欲渡黄河冰塞川", "I would cross the Yellow River, but ice blocks the stream.", "黄河を渡ろうにも氷が川を塞ぐ。"),
    Line("l12", 59.00, 65.00, "将登太行雪满山", "I would climb Taihang, but snow covers the mountains.", "太行に登ろうにも雪が山を満たす。"),
    Line("l13", 65.00, 70.20, "闲来垂钓碧溪上", "At ease I fish beside the blue stream.", "閑かに碧い渓に釣り糸を垂れる。"),
    Line("l14", 70.20, 76.00, "忽复乘舟梦日边", "Then again I dream of sailing by the sun.", "ふとまた舟に乗り日の辺を夢見る。"),
    Line("l15", 76.00, 79.40, "行路难", "The road is hard.", "道は険しい。"),
    Line("l16", 79.40, 82.80, "行路难", "The road is hard.", "道は険しい。"),
    Line("l17", 82.80, 86.80, "多歧路", "So many branching paths.", "分かれ道は多い。"),
    Line("l18", 86.80, 92.00, "今安在", "Where is the way now?", "いま道はどこにある。"),
]


ITEMS = [
    DraftItem(
        media_id="shu-dao-nan-original-text-dr-draft",
        title="蜀道难 · 原文重组 DR Draft",
        localized_titles={
            "zh-Hans": "蜀道难 · 原文重组 DR Draft",
            "en": "Hard Road to Shu - Original Text DR Draft",
            "ja": "蜀道難・原文再構成 DR Draft",
        },
        description=(
            "An experimental DiffRhythm draft that reorganizes Li Bai source lines. "
            "The lyric track is source-close and ASR-audited, but this is not a final polished ACE render."
        ),
        caption="Experimental DR draft: original-text fragments, source-close lyrics, and extracted chords.",
        source_audio=ROOT / "data/creative_projects/shu-dao-nan-original-text-dr-20260701/selected/shu-dao-nan-original-text-dr-hook-95-b-draft.mp3",
        analysis_dir=ROOT / "data/runs/shu-dao-nan-original-text-dr-hook-95-b-analysis",
        source_cover="assets/covers/shu-dao-nan-16x9.png",
        target_cover="assets/covers/shu-dao-nan-original-text-dr-draft-16x9.png",
        audio_name="shu-dao-nan-original-text-dr-draft-zh-Hans-dr-20260701.mp3",
        tempo_note="detected 198.77 BPM; experimental DiffRhythm draft",
        lines=SHU_LINES,
        tags=["music", "Li Bai", "Tang poetry", "Mandarin", "DiffRhythm", "DR", "draft", "original-text"],
        insert_after="shu-dao-nan-qing-tian-lu",
    ),
    DraftItem(
        media_id="xing-lu-nan-original-poem-draft",
        title="行路难 · 原文重组 DR Draft",
        localized_titles={
            "zh-Hans": "行路难 · 原文重组 DR Draft",
            "en": "Hard Is the Road - Original Text DR Draft",
            "ja": "行路難・原文再構成 DR Draft",
        },
        description=(
            "An experimental DiffRhythm draft that starts from Li Bai's hope-first original-poem ordering. "
            "The lyric track follows the source text where the sound is close and stays marked as draft."
        ),
        caption="Experimental DR draft: hope-first Li Bai source lines with corrected website timing.",
        source_audio=ROOT / "data/creative_projects/xing-lu-nan-original-poem-20260701/selected/xing-lu-nan-original-poem-hope-first-draft.mp3",
        analysis_dir=ROOT / "data/runs/xing-lu-nan-original-poem-hope-first-draft-analysis",
        source_cover="assets/covers/qiang-jin-jiu-normal-song-16x9.png",
        target_cover="assets/covers/xing-lu-nan-original-poem-draft-16x9.png",
        audio_name="xing-lu-nan-original-poem-draft-zh-Hans-dr-20260701.mp3",
        tempo_note="detected 172.27 BPM; experimental DiffRhythm draft",
        lines=XING_LINES,
        tags=["music", "Li Bai", "Tang poetry", "Mandarin", "DiffRhythm", "DR", "draft", "original-poem"],
        insert_after="shu-dao-nan-original-text-dr-draft",
    ),
]


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return round(float(result.stdout.strip()), 3)


def image_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return image.size
    except Exception:
        return (1600, 900)


def split_units(text: str, code: str) -> list[str]:
    if code in {"zh-Hans", "ja"}:
        return [char for char in text if not char.isspace()]
    parts: list[str] = []
    token = ""
    for char in text:
        if char.isalnum() or char == "'":
            token += char
        else:
            if token:
                parts.append(token)
                token = ""
            if not char.isspace():
                parts.append(char)
    if token:
        parts.append(token)
    return parts or [text]


def timed_tokens(text: str, start: float, end: float, code: str) -> list[dict]:
    units = split_units(text, code)
    step = (end - start) / max(len(units), 1)
    tokens = []
    for index, unit in enumerate(units):
        token_start = round(start + index * step, 3)
        token_end = round(start + (index + 1) * step, 3)
        token = {"text": unit, "start": token_start, "end": token_end}
        if code == "zh-Hans" and "\u4e00" <= unit <= "\u9fff":
            reading = pinyin(unit, style=Style.TONE3, heteronym=False, errors="ignore")
            if reading and reading[0]:
                token["pinyin"] = reading[0][0]
            if unit == "长" and text.startswith("长风"):
                token["pinyin"] = "chang2"
            if unit == "行" and index > 0 and units[index - 1] == "太":
                token["pinyin"] = "hang2"
        elif code == "ja" and pykakasi and "\u4e00" <= unit <= "\u9fff":
            reading = pykakasi.kakasi().convert(unit)
            if reading:
                hira = reading[0].get("hira")
                if hira and hira != unit:
                    token["reading"] = hira
        tokens.append(token)
    return tokens


def language_meta(code: str) -> dict:
    if code == "zh-Hans":
        return {
            "code": "zh-Hans",
            "label": "Mandarin Chinese",
            "nativeLabel": "中文",
            "script": "Hans",
            "pronunciation": "pinyin",
        }
    if code == "ja":
        return {
            "code": "ja",
            "label": "Japanese",
            "nativeLabel": "日本語",
            "script": "Jpan",
            "pronunciation": "furigana",
        }
    return {"code": "en", "label": "English", "nativeLabel": "English", "script": "Latn"}


def make_track(item: DraftItem, code: str) -> dict:
    field = {"zh-Hans": "zh", "en": "en", "ja": "ja"}[code]
    lines = []
    for line in item.lines:
        text = getattr(line, field)
        lines.append(
            {
                "id": line.id,
                "start": line.start,
                "end": line.end,
                "text": text,
                "singableText": text,
                "role": "lyric" if code == "zh-Hans" else "translation",
                "tokens": timed_tokens(text, line.start, line.end, code),
            }
        )
    return {
        "schema": TEXT_SCHEMA,
        "version": 1,
        "mediaId": item.media_id,
        "language": language_meta(code),
        "lines": lines,
        "provenance": {
            "status": "draft",
            "method": "source-close ASR/listening correction",
            "note": "The active Mandarin line keeps source text when the generated sound is close; this item is not final polish.",
        },
    }


def load_chords(path: Path) -> list[dict]:
    csv_path = path / "analysis/chords.csv"
    chords = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            chords.append(
                {
                    "start": round(float(row["start"]), 3),
                    "end": round(float(row["end"]), 3),
                    "name": row["chord"],
                    "confidence": round(float(row.get("confidence") or 0), 3),
                }
            )
    return chords


def copy_assets(item: DraftItem) -> tuple[str, int, int]:
    SONGS_AUDIO.mkdir(parents=True, exist_ok=True)
    if not item.source_audio.exists():
        raise SystemExit(f"missing source audio: {item.source_audio}")
    shutil.copy2(item.source_audio, SONGS_AUDIO / item.audio_name)

    source_cover = WEBSITE / item.source_cover
    target_cover = WEBSITE / item.target_cover
    if not source_cover.exists():
        raise SystemExit(f"missing cover: {source_cover}")
    target_cover.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_cover, target_cover)
    width, height = image_size(target_cover)
    return item.target_cover, width, height


def update_catalog(item: DraftItem) -> None:
    path = WEBSITE / "data/catalog.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    items = [entry for entry in catalog["items"] if entry.get("id") != item.media_id]
    entry = {
        "id": item.media_id,
        "kind": "song",
        "title": item.title,
        "artist": "Musia",
        "summary": item.description,
        "manifest": f"data/songs/{item.media_id}/manifest.json",
        "cover": item.target_cover,
        "languages": ["zh-Hans", "en", "ja"],
        "tags": item.tags,
    }
    insert_at = len(items)
    for index, existing in enumerate(items):
        if existing.get("id") == item.insert_after:
            insert_at = index + 1
            break
    items.insert(insert_at, entry)
    catalog["items"] = items
    write_json(path, catalog)


def write_item(item: DraftItem) -> None:
    cover_src, width, height = copy_assets(item)
    duration = ffprobe_duration(SONGS_AUDIO / item.audio_name)
    media_dir = WEBSITE / "data/songs" / item.media_id
    lyrics_dir = media_dir / "lyrics/zh-vocal"

    for code in ["zh-Hans", "en", "ja"]:
        write_json(lyrics_dir / f"{code}.json", make_track(item, code))

    chords = load_chords(item.analysis_dir)
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "version": 1,
        "id": item.media_id,
        "kind": "song",
        "title": item.title,
        "localizedTitles": item.localized_titles,
        "artist": "Musia",
        "description": item.description,
        "caption": item.caption,
        "duration": duration,
        "canonicalUrl": f"https://fun.lazying.art/#{item.media_id}",
        "status": "experimental-draft",
        "share": {
            "title": f"{item.title} - Fun Lazying Art",
            "description": item.description,
            "url": f"https://fun.lazying.art/#{item.media_id}",
            "image": cover_src,
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {
                "id": "cover",
                "label": f"{item.title} cover",
                "role": "cover",
                "src": cover_src,
                "mime": "image/png",
                "width": width,
                "height": height,
            },
            "poster": {
                "id": "poster",
                "label": "16:9 Poster",
                "role": "poster",
                "src": cover_src,
                "mime": "image/png",
                "width": width,
                "height": height,
            },
            "primaryAudio": {
                "id": "zh-dr-draft",
                "label": "中文",
                "roleLabel": "Vocal",
                "role": "vocal",
                "languageCode": "zh-Hans",
                "languageLabel": "中文",
                "lyricSetId": "zh-vocal",
                "src": f"{AUDIO_BASE}{item.audio_name}?v={AUDIO_CACHE_VERSION}",
                "mime": "audio/mpeg",
            },
            "alternateAudio": [],
        },
        "musical": {
            "key": "detected from draft audio",
            "bpm": item.tempo_note,
            "timeSignature": "4/4",
            "chords": chords,
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
                        "features": ["pinyin", "active-vocal", "draft-correction"],
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
        "timeline": {
            "unit": "seconds",
            "lines": [
                {"id": line.id, "start": line.start, "end": line.end, "text": line.zh}
                for line in item.lines
            ],
        },
        "provenance": {
            "modelRoute": "DiffRhythm draft",
            "sourceAudio": str(item.source_audio.relative_to(ROOT)),
            "analysisRun": str(item.analysis_dir.relative_to(ROOT)),
            "coverSource": item.source_cover,
            "lyricsPolicy": "source-close correction against ASR/listening; draft items must stay labeled DR Draft",
        },
    }
    write_json(media_dir / "manifest.json", manifest)
    update_catalog(item)


def main() -> None:
    for item in ITEMS:
        write_item(item)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)
    print("Prepared draft Fun website items:")
    for item in ITEMS:
        print(f"- {item.media_id}: {WEBSITE / 'data/songs' / item.media_id / 'manifest.json'}")


if __name__ == "__main__":
    main()
