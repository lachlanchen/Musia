# 凉州词 · 双阕原诗版 Lyric Correction

Date: 2026-07-05

Media item:

```text
website/data/songs/liang-zhou-ci-double-original-poem/manifest.json
website/data/songs/liang-zhou-ci-double-original-poem/lyrics/zh-vocal/zh-Hans.json
```

Selected audio:

```text
data/creative_projects/liang-zhou-ci-double-original-poem-20260704/selected/liang-zhou-ci-double-original-poem-zh-ace-xl-turbo-seed747323.wav
```

Fresh re-audit:

```text
data/runs/liang-zhou-ci-double-original-poem-selected-large-v3-reaudit-20260705/
```

## Correction

The public website lyric set previously had 17 lines and omitted the early-hook
`葡萄美酒夜光杯` before `欲饮琵琶马上催`.

This was too aggressive. The planned/source lyric for the selected render has an
18-line original-poem structure:

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

葡萄美酒夜光杯
欲饮琵琶马上催
醉卧沙场君莫笑
古来征战几人回
```

Fresh Demucs-separated large-v3 ASR merges the early hook as:

```text
30.66 -> 39.66  大马上催
```

That is not evidence of a true instrumental gap. It is a merged/garbled ASR
segment over the place where the Wang Han quatrain starts. Public lyrics now
preserve the source-supported line and split it as:

```text
30.66 -> 38.60  葡萄美酒夜光杯
38.60 -> 39.66  欲饮琵琶马上催
```

The final repeated hook was also tightened using the fresh ASR boundaries:

```text
75.78 -> 78.86  葡萄美酒夜光杯
78.86 -> 82.23  欲饮琵琶马上催
83.52 -> 86.57  醉卧沙场君莫笑
87.04 -> 90.37  古来征战几人回
```

## Rule Reinforced

For Musia website and Shipinhao Music publication, never use draft lyrics or an
old generator output as the final lyric source. The final source must be the
ASR/listening-corrected active-language website JSON, after a
missing-planned-phrase audit.
