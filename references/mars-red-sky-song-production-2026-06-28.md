# Small Under the Red Sky Production Note

Date: 2026-06-28

Media id: `mars-red-sky-trilingual`

Public website URL:

```text
https://fun.lazying.art/#mars-red-sky-trilingual
```

## Goal

Create an original trilingual song about a human standing in a vast Mars desert, feeling small against the universe while still finding courage to move forward.

The intended emotional axis is:

```text
vast -> lonely -> humbled -> sad -> encouraged -> forward motion
```

## Website Assets

Committed website assets:

```text
website/data/songs/mars-red-sky-trilingual/manifest.json
website/data/songs/mars-red-sky-trilingual/lyrics/en-vocal/en.json
website/data/songs/mars-red-sky-trilingual/lyrics/en-vocal/zh-Hans.json
website/data/songs/mars-red-sky-trilingual/lyrics/en-vocal/ja.json
website/data/songs/mars-red-sky-trilingual/lyrics/zh-vocal/en.json
website/data/songs/mars-red-sky-trilingual/lyrics/zh-vocal/zh-Hans.json
website/data/songs/mars-red-sky-trilingual/lyrics/zh-vocal/ja.json
website/data/songs/mars-red-sky-trilingual/lyrics/ja-vocal/en.json
website/data/songs/mars-red-sky-trilingual/lyrics/ja-vocal/zh-Hans.json
website/data/songs/mars-red-sky-trilingual/lyrics/ja-vocal/ja.json
website/assets/audio/mars-red-sky-en.mp3
website/assets/audio/mars-red-sky-zh.mp3
website/assets/audio/mars-red-sky-ja.mp3
website/assets/covers/mars-red-sky-16x9.png
```

The short rain verse was removed from `website/data/catalog.json`, so the visible catalog now keeps full-song items only.

## Generation

Model route:

```text
ACE-Step 1.5 XL turbo local checkpoint
```

Local source run folder, not committed because it is large:

```text
data/creative_projects/mars-red-sky-trilingual-20260628/
```

Generated WAVs:

```text
data/creative_projects/mars-red-sky-trilingual-20260628/ace_outputs/en_xl/9d190e3a-5524-0190-83dd-c2cf70b3fc99.wav
data/creative_projects/mars-red-sky-trilingual-20260628/ace_outputs/zh_xl/e7e521b7-c6dd-16b3-9778-ddff65dcd895.wav
data/creative_projects/mars-red-sky-trilingual-20260628/ace_outputs/ja_xl/a16c1baa-e05e-00e1-9834-339c7f252f81.wav
```

All three renders are 82 seconds. The vocals are independent full-song generations with shared production direction, not strict stem-level localization of one backing track. This gives more musical quality than the short line-by-line vocal demo, but some lyric pronunciation remains imperfect.

## Lyrics

English vocal version:

```text
Red sand over my boots
A blue sun falls through dust
I am a breath beside the canyon
But still I rise, still I trust
Stars are silent, wide and cold
They do not answer, they make room
Stars are silent, wide and cold
They do not answer, they make room
Small under the red sky
I lift my heart and move
Even when the dark is endless, a spark becomes a road
Small under the red sky
I hear tomorrow call
If the universe is wider, then my courage must be tall
```

Mandarin vocal version:

```text
红沙盖过脚印
蓝日落进风尘
我在峡谷旁像一粒微光
仍要抬头向前奔
群星无声 又冷又远
不回答 却给我天
红色天空下 我如此渺小
也把心火举得高
黑夜再辽阔
红色天空下 听明天呼啸
一步一步不退逃
宇宙越广大 我越要燃烧
```

Japanese vocal version:

```text
赤い砂が足跡を消す
青い夕陽が風に沈む
峡谷のそば 小さな火でも
顔を上げて前へ進む
星は黙る 冷たく遠く
答えなくても 空をくれる
赤い空の下で 小さな僕は
胸の火を高く掲げる
星の砂が道になる
赤い空の下で 明日が呼ぶ
宇宙が広いほど 勇気は燃える
```

Each vocal language has its own trilingual lyric set. The translations intentionally allow small differences because the generated vocal phrasing differs per language.

## Analysis Runs

Musai analysis runs:

```text
data/runs/mars-red-sky-en-analysis/
data/runs/mars-red-sky-zh-analysis/
data/runs/mars-red-sky-ja-analysis/
```

Each run generated:

```text
stems/vocals.wav
stems/drums.wav
stems/bass.wav
stems/other.wav
stems/human_sound.wav
stems/instrumental.wav
analysis/beats.csv
analysis/beats.json
analysis/chords.csv
analysis/chords.json
analysis/lyrics.json
analysis/lyrics.txt
```

The website uses the detected chord timelines and ASR-guided lyric timing from these runs. Active word highlighting is enabled only for the current vocal language; the other two displayed languages are translations with pinyin or furigana.

## Cover

Cover prompt summary:

```text
16:9 cinematic Mars desert album cover, vast Martian desert at blue sunset,
Valles-Marineris-like canyon, tiny human silhouette with warm chest light,
red dust and blue twilight, hopeful and lonely, no text
```

Generated source image:

```text
/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/ig_0a8479b370a1a6c1016a40e0853248819189f1930869a86a77.png
```

Committed web cover:

```text
website/assets/covers/mars-red-sky-16x9.png
```

## Checks

Commands run:

```text
npm run website:validate
node --check website/app.js
npm run check
npm run smoke
git diff --check
```

Browser smoke screenshots:

```text
/tmp/musai-mars-site-final.png
/tmp/musai-mars-mobile.png
```
