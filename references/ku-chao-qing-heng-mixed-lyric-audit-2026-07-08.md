# Ku Chao Qing Heng Mixed Lyric Audit

Date: 2026-07-08

Song: `哭晁卿衡 · Moon Over The Blue Sea`

Selected audio:

```text
data/creative_projects/ku-chao-qing-heng-mixed-20260708/selected/ku-chao-qing-heng-mixed-ace-xl-turbo-seed780824.mp3
```

Website item:

```text
website/data/songs/ku-chao-qing-heng-mixed/manifest.json
website/data/songs/ku-chao-qing-heng-mixed/lyrics/mixed-vocal/
```

## Failure Found

The first correction pass trusted the ASR segment list too much. Mixed-language
ASR recognized:

```text
Moon
Tsuki wa kaeranu
```

but the planned lyric and listening supported an English line in the timing gap:

```text
Moonlight will not return to me
```

That line must be represented as its own timed line between `Moon` and
`Tsuki wa kaeranu`.

The same pass also changed a repeated poem-pinyin line:

```text
Zheng fan yi pian rao Peng Hu
```

into a modern Chinese translation. That is wrong when the active line is
clearly the poem pinyin. The Chinese companion track should preserve the source
poem for poem-pinyin lines:

```text
征帆一片绕蓬壶
```

## Corrected Coverage

| ID | Timing | Active mixed vocal | Chinese companion rule |
| --- | --- | --- | --- |
| l01 | 6.32-8.38 | Haruka umi e | Translate to `遥向大海` |
| l02 | 9.06-11.52 | One sail fades into blue | Translate to `一叶帆影淡入蓝海` |
| l03 | 12.94-15.88 | Ri ben Chao Qing ci di du | Preserve poem: `日本晁卿辞帝都` |
| l04 | 16.32-18.98 | Zheng fan yi pian rao Peng Hu | Preserve poem: `征帆一片绕蓬壶` |
| l05 | 19.48-21.70 | Haruka umi e | Translate to `遥向大海` |
| l06 | 22.42-24.88 | Sail away, my friend | Translate to `远航吧，我的朋友` |
| l07 | 27.54-30.16 | Ming yue bu gui chen bi hai | Preserve poem: `明月不归沉碧海` |
| l08 | 31.00-31.28 | Moon | Translate to `明月` |
| l09 | 31.28-35.24 | Moonlight will not return to me | Translate to `月光不会回到我身边` |
| l10 | 35.24-37.18 | Tsuki wa kaeranu | Translate to `月不归来` |
| l11 | 39.28-41.56 | Ming yue bu gui chen bi hai | Preserve poem: `明月不归沉碧海` |
| l12 | 43.06-44.98 | Bai yun chou se man Cang Wu | Preserve poem: `白云愁色满苍梧` |
| l13 | 46.06-48.50 | Moon over the blue sea | Translate to `碧海上的明月` |
| l14 | 48.84-50.20 | Shiroi kumo | Translate to `白云` |
| l15 | 50.78-53.78 | Kanashimi no iro | Translate to `悲伤的颜色` |
| l16 | 57.72-60.20 | Zheng fan yi pian rao Peng Hu | Preserve poem: `征帆一片绕蓬壶` |
| l17 | 62.15-64.39 | Ri ben Chao Qing ci di du | Preserve poem: `日本晁卿辞帝都` |
| l18 | 64.89-66.81 | Far beyond the waves | Translate to `远在浪涛之外` |
| l19 | 67.59-69.73 | I still call your name | Translate to `我仍呼唤你的名字` |

## Reusable Rule

Before recording or publishing any Musia song, especially mixed-language songs:

1. Print the planned/reference lyric and corrected active track side by side.
2. Account for every planned line as kept, sound-close corrected, split,
   merged, omitted-not-audible, or translation-only.
3. Inspect timing gaps between ASR segments; a real sung line can live entirely
   inside a gap.
4. For poem-pinyin active lines, preserve the source poem in Chinese companion
   tracks.
5. For English/Japanese active lines, translate the actual active line instead
   of repeating poem anchors.
6. Do not record, publish, or package Shipinhao Music until this coverage check
   passes.

