#!/usr/bin/env python3
"""Prepare the Fun Lazying Art website item for 你是一只猪."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter
from pypinyin import Style, pinyin


ROOT = Path(__file__).resolve().parents[1]
SONGS_ROOT = ROOT.parent / "MusiaSongs"
MEDIA_ID = "xiao-xiao-zhu-trilingual"
ITEM_DIR = ROOT / "website" / "data" / "songs" / MEDIA_ID
COVER_PATH = ROOT / "website" / "assets" / "covers" / "xiao-xiao-zhu-16x9.png"
PUBLIC_AUDIO_BASE = "https://lazyingart.github.io/MusiaSongs/audio/"


SELECTED = ROOT / "data" / "creative_projects" / "ni-shi-yi-zhi-zhu-20260629" / "selected"


VOCALS: dict[str, dict[str, Any]] = {
    "zh-vocal": {
        "language": "zh-Hans",
        "label": "Mandarin vocal",
        "asset_id": "xiao-xiao-zhu-zh",
        "audio_src": SELECTED / "ni-shi-yi-zhi-zhu-zh-master.wav",
        "mp3_name": "xiao-xiao-zhu-zh-Hans.mp3",
        "analysis": ROOT / "data" / "runs" / "ni-shi-yi-zhi-zhu-20260629-20260629-192414-analysis",
        "lyrics": {
            "zh-Hans": [
                "你是一只猪 一只小小猪",
                "怎么笑得像云朵 睡醒还会饿",
                "我也想停住 不赶路",
                "把世界关小声 躲进你小屋",
                "小小猪 我想做只小小猪",
                "没有作业 没有工作 今晚只想被照顾",
                "小小猪 小小猪",
                "借我一点小幸福",
                "有人唱歌 有人摸摸",
                "哦哦 不用赶路",
                "闹钟太会哭 消息催着读",
                "我说没事还不错 心里有点苦",
                "不是不长大 只是喘口气",
                "笨笨地快乐 也算很努力",
                "小小猪 我想做只小小猪",
                "吃得很多 睡得很熟 梦里没有辛苦",
                "小小猪 小小猪",
                "抱着我的小小猪",
                "世界很重 心很软 今晚慢慢呼",
                "哦哦哦 小小猪",
                "哦哦哦 小小猪",
            ],
            "en": [
                "You are a piggy, a tiny little piggy",
                "How do you smile like a cloud and wake up hungry?",
                "I want to stop, no more running",
                "Turn the world down, hide in your tiny room",
                "Little piggy, I want to be a little piggy",
                "No homework, no work, just held close tonight",
                "Little piggy, little piggy",
                "Lend me one small happiness",
                "Someone sings, someone pats me",
                "Oh oh, no more running",
                "Alarms cry too much, messages keep calling",
                "I say I am okay, but my heart feels tired",
                "I am not refusing growing, just catching breath",
                "Silly joy is still doing my best",
                "Little piggy, I want to be a little piggy",
                "Eat a lot, sleep so deep, no pain in dreams",
                "Little piggy, little piggy",
                "Holding my little piggy",
                "The world is heavy, the heart is soft, breathe slow tonight",
                "Oh oh oh, little piggy",
                "Oh oh oh, little piggy",
            ],
            "ja": [
                "きみはこぶた ちいさなこぶた",
                "雲みたいに笑って 目覚めてもおなかすく",
                "僕も止まりたい 急がない",
                "世界を小さくして 小さな部屋へ",
                "こぶた 僕もこぶたになりたい",
                "宿題も仕事もない 今夜は抱きしめて",
                "こぶた こぶた",
                "小さなしあわせ貸して",
                "歌を聴いて なでられて",
                "おお 急がない",
                "時計が泣いて メールが呼んでる",
                "大丈夫って笑うけど 心は少し疲れた",
                "大人がいやじゃない ただ息をしたい",
                "不器用な幸せも ちゃんと頑張ってる",
                "こぶた 僕もこぶたになりたい",
                "いっぱい食べて 深く眠る 夢に苦しみはない",
                "こぶた こぶた",
                "小さなこぶたを抱いて",
                "世界は重い 心はやわい 今夜はゆっくり息をする",
                "おおお こぶた",
                "おおお こぶた",
            ],
        },
    },
    "en-vocal": {
        "language": "en",
        "label": "English vocal",
        "asset_id": "xiao-xiao-zhu-en",
        "audio_src": SELECTED / "you-little-piggy-en.wav",
        "mp3_name": "xiao-xiao-zhu-en.mp3",
        "analysis": ROOT / "data" / "runs" / "en-20260629-193403-analysis",
        "lyrics": {
            "en": [
                "But you are a piggy, a tiny little piggy",
                "How do you smile like a cloud and wake up hungry?",
                "I wanna stop now, no more running",
                "Turn the world down softly in your tiny room",
                "Little piggy, little piggy",
                "I wanna be a little piggy",
                "No homework, no work tonight",
                "Just let me be held close",
                "Little piggy, little piggy",
                "Lend me one small happiness",
                "Someone sings and someone pats me",
                "No more running, no more tears",
                "Alarms keep calling, messages pile up",
                "I say I am okay, but I am a little tired",
                "I am not refusing growing",
                "I just need one breath",
                "Silly joy is still trying",
                "That is also doing my best",
                "Little piggy, little piggy",
                "I wanna be a little piggy",
                "Eat a lot and sleep so deep",
                "No pain inside my dreams",
                "Little piggy, little piggy",
                "Hold my little piggy",
                "The world is heavy, heart is soft",
                "Tonight I breathe slow",
                "Little piggy",
            ],
            "zh-Hans": [
                "可是你是一只小猪 一只小小猪",
                "你怎么笑得像云朵 醒来还会饿",
                "我想停下来 不再赶路",
                "把世界轻轻调小 躲进你的小房间",
                "小小猪 小小猪",
                "我想做只小小猪",
                "今晚没有作业 没有工作",
                "就让我被抱紧",
                "小小猪 小小猪",
                "借我一点小幸福",
                "有人唱歌 有人摸摸",
                "不再赶路 不再流泪",
                "闹钟一直叫 消息堆成堆",
                "我说我没事 其实有点累",
                "我不是不想长大",
                "我只是需要喘口气",
                "笨笨的快乐也在努力",
                "这也算我的尽力",
                "小小猪 小小猪",
                "我想做只小小猪",
                "吃得很多 睡得很熟",
                "梦里没有疼痛",
                "小小猪 小小猪",
                "抱着我的小小猪",
                "世界很重 心很软",
                "今晚慢慢呼吸",
                "小小猪",
            ],
            "ja": [
                "でもきみはこぶた ちいさなこぶた",
                "雲みたいに笑って 目覚めてもおなかすく",
                "僕は止まりたい もう走らない",
                "世界をそっと小さくして きみの部屋へ",
                "こぶた こぶた",
                "僕もこぶたになりたい",
                "宿題も仕事もない夜",
                "ただ抱きしめてほしい",
                "こぶた こぶた",
                "小さなしあわせ貸して",
                "歌を聴いて なでられて",
                "急がない 泣かない",
                "時計が鳴って メールが積もる",
                "大丈夫って言うけど 少し疲れた",
                "大人がいやじゃない",
                "ただ息をしたい",
                "不器用な幸せも頑張ってる",
                "それも僕の精一杯",
                "こぶた こぶた",
                "僕もこぶたになりたい",
                "いっぱい食べて 深く眠る",
                "夢に痛みはない",
                "こぶた こぶた",
                "小さなこぶたを抱いて",
                "世界は重い 心はやわい",
                "今夜はゆっくり息をする",
                "こぶた",
            ],
        },
    },
    "ja-vocal": {
        "language": "ja",
        "label": "Japanese vocal",
        "asset_id": "xiao-xiao-zhu-ja",
        "audio_src": SELECTED / "kimi-wa-kobuta-ja.wav",
        "mp3_name": "xiao-xiao-zhu-ja.mp3",
        "analysis": ROOT / "data" / "runs" / "ja-20260629-193836-analysis",
        "lyrics": {
            "ja": [
                "君はこぶた 小さなこぶた",
                "雲のように笑って またお腹がすく",
                "僕もとまりたい もう走らない",
                "世界を小さくして ふうっと眠ろう",
                "こぶた こぶた 僕もこぶたになりたい",
                "宿題も仕事もない 今夜は抱きしめて",
                "こぶた こぶた 小さな幸せ",
                "歌を聴いて 撫でられて",
                "急がない 泣かない",
                "時計が呼んでる メールが積もってる",
                "大丈夫って笑うけど 本当は少し疲れた",
                "大人がいやじゃない ただ息をしたい",
                "不器用な幸せも ちゃんと頑張ってる",
                "こぶた こぶた 僕もこぶたになりたい",
                "いっぱい食べて 深く眠る 夢に苦しみはない",
                "こぶた こぶた 小さなこぶたを抱いて",
                "世界は重い 心はやわい 今夜はゆっくり眠ろう",
                "こぶた 僕も小さなこぶた",
            ],
            "en": [
                "You are a piggy, a tiny little piggy",
                "Smiling like a cloud, hungry when you wake",
                "I want to stop too, no more running",
                "Make the world small and drift to sleep",
                "Little piggy, little piggy, I want to be a little piggy",
                "No homework, no work, hold me close tonight",
                "Little piggy, little piggy, one small happiness",
                "Listening to songs and being patted",
                "No rushing, no crying",
                "The clock is calling, messages are piling up",
                "I smile and say I am okay, but I am tired",
                "I do not hate growing up, I just want to breathe",
                "Awkward happiness is trying hard too",
                "Little piggy, little piggy, I want to be a little piggy",
                "Eat a lot and sleep deep, no pain in dreams",
                "Little piggy, little piggy, holding a tiny pig",
                "The world is heavy, the heart is soft, sleep slowly tonight",
                "Little piggy, I am a tiny piggy too",
            ],
            "zh-Hans": [
                "你是小猪 一只小小猪",
                "像云朵一样笑着 醒来还是会饿",
                "我也想停住 不再奔跑",
                "把世界变小 轻轻睡去",
                "小小猪 小小猪 我也想做小小猪",
                "没有作业 没有工作 今晚抱抱我",
                "小小猪 小小猪 一点小幸福",
                "听你唱歌 被你摸摸",
                "不赶路 不哭了",
                "时钟在叫 消息堆起来",
                "我笑着说没事 其实有点累",
                "不是讨厌长大 只是想呼吸",
                "笨拙的幸福也在努力",
                "小小猪 小小猪 我也想做小小猪",
                "吃得很多 深深睡去 梦里没有痛苦",
                "小小猪 小小猪 抱着小小猪",
                "世界很重 心很软 今晚慢慢睡",
                "小小猪 我也是小小猪",
            ],
        },
    },
}


LANG_META = {
    "en": {"label": "English", "nativeLabel": "English", "script": "Latn"},
    "zh-Hans": {"label": "Mandarin Chinese", "nativeLabel": "中文", "script": "Hans", "pronunciation": "pinyin"},
    "ja": {"label": "Japanese", "nativeLabel": "日本語", "script": "Jpan", "pronunciation": "furigana"},
}


JA_READINGS = {
    "君": "きみ",
    "小": "こ",
    "豚": "ぶた",
    "雲": "くも",
    "笑": "わら",
    "腹": "なか",
    "空": "す",
    "僕": "ぼく",
    "走": "はし",
    "世": "せ",
    "界": "かい",
    "眠": "ねむ",
    "宿": "しゅく",
    "題": "だい",
    "仕": "し",
    "事": "ごと",
    "今": "こん",
    "夜": "や",
    "抱": "だ",
    "幸": "しあわ",
    "歌": "うた",
    "聴": "き",
    "撫": "な",
    "急": "いそ",
    "泣": "な",
    "時": "と",
    "計": "けい",
    "呼": "よ",
    "積": "つ",
    "大": "だい",
    "丈": "じょう",
    "夫": "ぶ",
    "本": "ほん",
    "当": "とう",
    "少": "すこ",
    "疲": "つか",
    "人": "と",
    "息": "いき",
    "不": "ぶ",
    "器": "き",
    "用": "よう",
    "頑": "がん",
    "張": "ば",
    "食": "た",
    "深": "ふか",
    "夢": "ゆめ",
    "苦": "くる",
    "重": "おも",
    "心": "こころ",
    "部": "へ",
    "屋": "や",
    "言": "い",
    "痛": "いた",
    "鳴": "な",
    "精": "せい",
    "一": "いっ",
    "杯": "ぱい",
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_chords(run_dir: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with (run_dir / "analysis" / "chords.csv").open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "start": round(float(row["start"]), 3),
                    "end": round(float(row["end"]), 3),
                    "name": row["chord"],
                    "degree": "",
                    "confidence": round(float(row.get("confidence") or 0), 3),
                }
            )
    return rows if limit is None else rows[:limit]


def segments_for(run_dir: Path) -> list[dict[str, Any]]:
    return load_json(run_dir / "analysis" / "lyrics.json")["segments"]


def manifest_for(run_dir: Path) -> dict[str, Any]:
    return load_json(run_dir / "manifest.json")


def even_times(start: float, end: float, count: int) -> list[tuple[float, float]]:
    if count <= 0:
        return []
    step = (end - start) / count
    return [(round(start + i * step, 3), round(start + (i + 1) * step, 3)) for i in range(count)]


def en_tokens(text: str, start: float, end: float) -> list[dict[str, Any]]:
    parts = re.findall(r"[A-Za-z0-9']+|[^\w\s]", text)
    words = [part for part in parts if re.search(r"[A-Za-z0-9']", part)]
    times = even_times(start, end, len(words))
    result = []
    time_i = 0
    for part in parts:
        if re.search(r"[A-Za-z0-9']", part):
            token_start, token_end = times[time_i]
            result.append({"text": part, "start": token_start, "end": token_end})
            time_i += 1
    return result


def zh_tokens(text: str, start: float, end: float) -> list[dict[str, Any]]:
    chars = [char for char in text if "\u3400" <= char <= "\u9fff"]
    times = even_times(start, end, len(chars))
    result = []
    for char, (token_start, token_end) in zip(chars, times):
        py = pinyin(char, style=Style.TONE3, heteronym=False, neutral_tone_with_five=True)[0][0]
        result.append({"text": char, "start": token_start, "end": token_end, "pinyin": py})
    return result


def ja_tokens(text: str, start: float, end: float) -> list[dict[str, Any]]:
    chars = [char for char in text if not char.isspace()]
    times = even_times(start, end, len(chars))
    result = []
    for char, (token_start, token_end) in zip(chars, times):
        item: dict[str, Any] = {"text": char, "start": token_start, "end": token_end}
        if "\u3400" <= char <= "\u9fff":
            item["reading"] = JA_READINGS.get(char, char)
        result.append(item)
    return result


def tokens_for(code: str, text: str, start: float, end: float) -> list[dict[str, Any]]:
    if code == "en":
        return en_tokens(text, start, end)
    if code.startswith("zh"):
        return zh_tokens(text, start, end)
    if code == "ja":
        return ja_tokens(text, start, end)
    return []


def build_track(vocal_id: str, language: str) -> dict[str, Any]:
    spec = VOCALS[vocal_id]
    segments = segments_for(spec["analysis"])
    texts = spec["lyrics"][language]
    if len(texts) != len(segments):
        raise SystemExit(f"{vocal_id}/{language}: {len(texts)} texts for {len(segments)} segments")
    meta = dict(LANG_META[language])
    meta["code"] = language
    lines = []
    for index, (segment, text) in enumerate(zip(segments, texts), 1):
        start = round(float(segment["start"]), 3)
        end = round(float(segment["end"]), 3)
        lines.append(
            {
                "id": f"{vocal_id[:2]}-{index:03d}",
                "start": start,
                "end": end,
                "text": text,
                "singableText": text,
                "role": "active-vocal-lyric" if language == spec["language"] else "translation",
                "tokens": tokens_for(language, text, start, end),
            }
        )
    return {
        "schema": "fun.lazying.media.text-track.v1",
        "version": 1,
        "mediaId": MEDIA_ID,
        "language": meta,
        "notes": (
            "ASR/STT corrected against selected Musia render and intended lyric. "
            "Active vocal timing uses the selected render's analysis segments; translations share line IDs for rough highlighting."
        ),
        "provenance": {
            "source": "Musia selected render",
            "analysisRun": str(spec["analysis"].relative_to(ROOT)),
            "policy": "actual audible structure > close intended lyric > ASR guess > translation draft",
        },
        "lines": lines,
    }


def convert_audio() -> None:
    audio_dir = SONGS_ROOT / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    for spec in VOCALS.values():
        src = spec["audio_src"]
        dst = audio_dir / spec["mp3_name"]
        if not src.exists():
            raise SystemExit(f"missing selected audio: {src}")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(src),
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "192k",
                str(dst),
            ],
            check=True,
        )
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS_ROOT, check=True)


def draw_cover() -> None:
    COVER_PATH.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), "#fff7ec")
    draw = ImageDraw.Draw(image, "RGBA")
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(255 * (1 - t) + 255 * t)
        g = int(247 * (1 - t) + 220 * t)
        b = int(236 * (1 - t) + 196 * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    for cx, cy, rx, ry, color in [
        (330, 180, 330, 115, (255, 255, 255, 145)),
        (1290, 185, 390, 135, (255, 255, 255, 130)),
        (1130, 720, 460, 135, (255, 255, 255, 115)),
    ]:
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=color)
    blanket = [(260, 570), (420, 430), (780, 390), (1120, 470), (1320, 630), (1160, 770), (600, 790)]
    draw.polygon(blanket, fill=(126, 196, 220, 245))
    draw.line(blanket + [blanket[0]], fill=(78, 132, 160, 180), width=7)
    draw.ellipse((545, 285, 1045, 650), fill=(255, 181, 198, 255), outline=(180, 96, 118, 220), width=7)
    draw.ellipse((875, 395, 1020, 505), fill=(246, 136, 162, 255), outline=(170, 86, 110, 180), width=5)
    draw.ellipse((905, 430, 930, 460), fill=(130, 70, 90, 255))
    draw.ellipse((965, 430, 990, 460), fill=(130, 70, 90, 255))
    draw.ellipse((655, 390, 690, 425), fill=(70, 52, 68, 255))
    draw.ellipse((805, 375, 840, 410), fill=(70, 52, 68, 255))
    draw.arc((700, 420, 800, 500), 10, 170, fill=(112, 64, 86, 220), width=6)
    draw.polygon([(620, 315), (675, 190), (750, 332)], fill=(255, 170, 190, 255), outline=(170, 90, 112, 220))
    draw.polygon([(835, 315), (910, 190), (965, 332)], fill=(255, 170, 190, 255), outline=(170, 90, 112, 220))
    draw.ellipse((350, 665, 500, 745), fill=(247, 218, 139, 255), outline=(154, 116, 64, 180), width=5)
    draw.line((405, 690, 575, 615), fill=(116, 88, 48, 230), width=14)
    draw.line((454, 702, 512, 675), fill=(116, 88, 48, 230), width=6)
    draw.line((454, 718, 520, 688), fill=(116, 88, 48, 230), width=6)
    for x, y, size in [(180, 335, 16), (250, 290, 9), (1240, 330, 13), (1370, 410, 8), (1060, 260, 10)]:
        draw.ellipse((x - size, y - size, x + size, y + size), fill=(255, 205, 83, 210))
    image = image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=3))
    image.save(COVER_PATH)


def build_manifest() -> None:
    ITEM_DIR.mkdir(parents=True, exist_ok=True)
    for vocal_id in VOCALS:
        for language in ("en", "zh-Hans", "ja"):
            track = build_track(vocal_id, language)
            write_json(ITEM_DIR / "lyrics" / vocal_id / f"{language}.json", track)

    primary = VOCALS["zh-vocal"]
    primary_manifest = manifest_for(primary["analysis"])

    def audio_asset(vocal_id: str) -> dict[str, Any]:
        spec = VOCALS[vocal_id]
        run_manifest = manifest_for(spec["analysis"])
        lang = spec["language"]
        native = LANG_META[lang]["nativeLabel"]
        return {
            "id": spec["asset_id"],
            "label": spec["label"],
            "roleLabel": "Vocal",
            "role": "vocal",
            "languageCode": lang,
            "languageLabel": LANG_META[lang]["label"],
            "languageNativeLabel": native,
            "lyricSetId": vocal_id,
            "src": PUBLIC_AUDIO_BASE + spec["mp3_name"],
            "mime": "audio/mpeg",
            "musical": {
                "key": "A major / detected guide",
                "bpm": round(float(run_manifest["tempo_bpm"]), 2),
                "timeSignature": "4/4",
                "chords": read_chords(spec["analysis"]),
            },
        }

    lyric_sets = []
    for vocal_id, spec in VOCALS.items():
        lyric_sets.append(
            {
                "id": vocal_id,
                "label": spec["label"],
                "languageCode": spec["language"],
                "tracks": [
                    {
                        "code": "en",
                        "label": "English",
                        "nativeLabel": "English",
                        "script": "Latn",
                        "features": ["translation", "rough-highlight"] if spec["language"] != "en" else ["active-vocal", "word-highlight"],
                        "path": f"lyrics/{vocal_id}/en.json",
                    },
                    {
                        "code": "zh-Hans",
                        "label": "Mandarin Chinese",
                        "nativeLabel": "中文",
                        "script": "Hans",
                        "features": ["translation", "pinyin", "rough-highlight"] if spec["language"] != "zh-Hans" else ["active-vocal", "pinyin", "word-highlight"],
                        "path": f"lyrics/{vocal_id}/zh-Hans.json",
                    },
                    {
                        "code": "ja",
                        "label": "Japanese",
                        "nativeLabel": "日本語",
                        "script": "Jpan",
                        "features": ["translation", "furigana", "rough-highlight"] if spec["language"] != "ja" else ["active-vocal", "furigana", "word-highlight"],
                        "path": f"lyrics/{vocal_id}/ja.json",
                    },
                ],
            }
        )

    zh_timeline = build_track("zh-vocal", "zh-Hans")["lines"]
    manifest = {
        "schema": "fun.lazying.media.manifest.v1",
        "version": 1,
        "id": MEDIA_ID,
        "kind": "song",
        "title": "你是一只猪",
        "localizedTitles": {
            "zh-Hans": "你是一只猪",
            "en": "You Little Piggy",
            "ja": "きみはこぶた",
        },
        "artist": "Musia",
        "subtitle": "Cute comfort bedroom-pop song in Mandarin, English, and Japanese",
        "description": "A playful but resonant Musia song about wanting to become a small happy pig for one night: no homework, no work, just warmth and rest.",
        "caption": "A tiny piggy song for tired people who need one soft night.",
        "duration": max(load_json(spec["analysis"] / "analysis" / "lyrics.json")["duration"] for spec in VOCALS.values()),
        "canonicalUrl": f"https://fun.lazying.art/#{MEDIA_ID}",
        "share": {
            "title": "你是一只猪 / You Little Piggy - Fun Lazying Art",
            "description": "A cute Musia comfort song with Mandarin, English, and Japanese vocals.",
            "url": f"https://fun.lazying.art/#{MEDIA_ID}",
            "image": "assets/covers/xiao-xiao-zhu-16x9.png",
            "siteName": "Fun Lazying Art",
        },
        "assets": {
            "cover": {
                "id": "cover",
                "label": "你是一只猪 cover",
                "role": "cover",
                "src": "assets/covers/xiao-xiao-zhu-16x9.png",
                "mime": "image/png",
                "width": 1600,
                "height": 900,
            },
            "poster": {
                "id": "poster",
                "label": "16:9 poster",
                "role": "poster",
                "src": "assets/covers/xiao-xiao-zhu-16x9.png",
                "mime": "image/png",
                "width": 1600,
                "height": 900,
            },
            "primaryAudio": audio_asset("zh-vocal"),
            "alternateAudio": [audio_asset("en-vocal"), audio_asset("ja-vocal")],
        },
        "musical": {
            "key": "A major / detected guide",
            "bpm": round(float(primary_manifest["tempo_bpm"]), 2),
            "timeSignature": "4/4",
            "chords": read_chords(primary["analysis"]),
        },
        "lyricSets": lyric_sets,
        "timeline": {
            "unit": "seconds",
            "lines": [
                {"id": line["id"], "start": line["start"], "end": line["end"], "sourceText": line["text"]}
                for line in zh_timeline
            ],
        },
        "provenance": {
            "createdBy": "Musia",
            "project": "data/creative_projects/ni-shi-yi-zhi-zhu-20260629",
            "productionNote": "references/xiao-xiao-zhu-production-2026-06-29.md",
            "cover": {
                "source": "AI image generation prompt plus local fallback render",
                "prompt": "Tiny round pig curled in a soft blanket cloud, ukulele and notebook, bright tidy modern 16:9 album cover, no text.",
            },
            "lyricPolicy": "Per-vocal lyric sets. Active timing from actual selected render ASR segments, corrected with intended lyrics where sound-close and structurally compatible.",
        },
        "artifacts": [
            {
                "id": "production-note",
                "label": "Production notes",
                "href": "https://github.com/lachlanchen/Musia/blob/main/references/xiao-xiao-zhu-production-2026-06-29.md",
            },
            {
                "id": "idea-folder",
                "label": "Idea and lyrics",
                "href": "https://github.com/lachlanchen/Musia/tree/main/ideas-and-inspirations/xiao-xiao-zhu",
            },
        ],
    }
    write_json(ITEM_DIR / "manifest.json", manifest)


def update_catalog() -> None:
    path = ROOT / "website" / "data" / "catalog.json"
    catalog = load_json(path)
    item = {
        "id": MEDIA_ID,
        "kind": "song",
        "title": "你是一只猪",
        "artist": "Musia",
        "summary": "A cute, slightly whiny comfort song with Mandarin, English, and Japanese vocals, synced lyrics, pinyin, furigana, and chord timing.",
        "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
        "cover": "assets/covers/xiao-xiao-zhu-16x9.png",
        "languages": ["zh-Hans", "en", "ja"],
        "tags": ["music", "cute", "comfort", "bedroom-pop", "Mandarin", "English", "Japanese", "pinyin", "furigana"],
    }
    items = [entry for entry in catalog["items"] if entry.get("id") != MEDIA_ID]
    insert_at = 1 if items else 0
    items.insert(insert_at, item)
    catalog["items"] = items
    write_json(path, catalog)


def main() -> None:
    convert_audio()
    draw_cover()
    build_manifest()
    update_catalog()
    print(f"prepared website item {MEDIA_ID}")
    print(f"manifest: {ITEM_DIR / 'manifest.json'}")
    print(f"cover: {COVER_PATH}")
    print(f"audio repo: {SONGS_ROOT / 'audio'}")


if __name__ == "__main__":
    main()
