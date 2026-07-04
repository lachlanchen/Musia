# 凉州词 · 双阕原诗版 Production Note

Date: 2026-07-04

Project:

```text
data/creative_projects/liang-zhou-ci-double-original-poem-20260704/
```

Selected render:

```text
data/creative_projects/liang-zhou-ci-double-original-poem-20260704/selected/liang-zhou-ci-double-original-poem-zh-ace-xl-turbo-seed747323.mp3
data/creative_projects/liang-zhou-ci-double-original-poem-20260704/selected/liang-zhou-ci-double-original-poem-zh-ace-xl-turbo-seed747323.wav
```

Deep analysis:

```text
data/runs/liang-zhou-ci-double-original-poem-7525030-deep-analysis/
```

Key artifacts:

```text
data/runs/liang-zhou-ci-double-original-poem-7525030-deep-analysis/stems/vocals.wav
data/runs/liang-zhou-ci-double-original-poem-7525030-deep-analysis/stems/drums.wav
data/runs/liang-zhou-ci-double-original-poem-7525030-deep-analysis/stems/bass.wav
data/runs/liang-zhou-ci-double-original-poem-7525030-deep-analysis/stems/other.wav
data/runs/liang-zhou-ci-double-original-poem-7525030-deep-analysis/analysis/chords.csv
data/runs/liang-zhou-ci-double-original-poem-7525030-deep-analysis/analysis/beats.csv
data/runs/liang-zhou-ci-double-original-poem-7525030-deep-analysis/analysis/lyrics.json
```

Website:

```text
https://fun.lazying.art/#liang-zhou-ci-double-original-poem
website/data/songs/liang-zhou-ci-double-original-poem/manifest.json
website/assets/covers/liang-zhou-ci-double-original-poem-16x9.png
```

## Lyric Source

Public lyrics use only original poem lines:

```text
黄河远上白云间
一片孤城万仞山
羌笛何须怨杨柳
春风不度玉门关

葡萄美酒夜光杯
欲饮琵琶马上催
醉卧沙场君莫笑
古来征战几人回

羌笛何须怨杨柳
春风不度玉门关
葡萄美酒夜光杯
欲饮琵琶马上催
醉卧沙场君莫笑
古来征战几人回
```

## What Worked

The selected candidate came from `acestep-v15-xl-turbo`, seed `747323`, using
a 96-second public-original hook form. The slower `acestep-v15-xl-sft` route
was tried first but rejected because large-v3 ASR did not recover usable poem
lyrics. The compact 88-second route improved brevity but lost too much text.

Best local rule from this run:

```text
For short classical poems, run XL/SFT if requested, but select by actual
vocal-separated ASR and listening evidence. The nominally larger model is not
automatically the best poem-song model.
```

## Remaining Caveat

This is a usable demo candidate, not a perfect original-poem master. Separated
ASR recovered the structure and repeated hook but showed diction drift:

```text
葡萄美酒也光悲 / 语音琵琶马上催 / 醉莫沙场君莫笑 / 古来征战几人会
```

Public lyrics restore these to the original lines because the sounds are close
and the original text is the artistic target. The opening quatrain is weaker and
should be manually listened before public release.

## Cover And Recording

The public cover is a no-text 16:9 AgInTi/image-generation frontier landscape:
moonlit pass, long river, luminous wine cup, and pipa. Do not regenerate this
item with the old procedural placeholder cover.

For portrait publication recording, use the Musia default lyrics-and-fingering
style:

```text
4K portrait
upper player/cover/header
lower current trilingual lyrics
guitar chord fingering below
start slightly before the first vocal, not exactly on the syllable
```

The first lyric line starts at `18.38s`. A smoother recording start is around
`16.50s`, or another nearby musical lead-in selected by listening.
