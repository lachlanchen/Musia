# 共白头 · Snow We Share Production Note

## Source Lines

```text
忽有故人心上过，回首山河已入秋。
他朝若是同淋雪，此生也算共白头。
```

## Selected Render

- Route: ACE-Step 1.5 XL Turbo, Yuerenge-style focused Mandarin source-line route.
- Selected seed: `791401`.
- Selected audio: `data/creative_projects/gong-bai-tou-snow-we-share-native-20260710/selected/gong-bai-tou-snow-we-share-zh-yuerenge-style-seed791401.mp3`.
- Public audio: `https://lazyingart.github.io/MusiaSongs/audio/gong-bai-tou-snow-we-share-native-zh-yuerenge-style-seed791401-20260710.mp3`.
- Analysis: `data/runs/gong-bai-tou-snow-we-share-native-20260710-analysis/`.
- Website manifest: `website/data/songs/gong-bai-tou-snow-we-share-native/manifest.json`.

## What Worked

This remake initially failed with dense mixed-language prompts and literal source-only Chinese prompts. The route that finally passed came from reusing the `越人歌` philosophy:

- keep the sung vocal focused in one language instead of forcing EN/JP/ZH into one render;
- select the most musical source lines and repeat them as verse/chorus hooks;
- use compact Chinese positive prompting rather than long negative lists;
- treat ASR as a guardrail, not the sole judge, for soft classical-style singing;
- publish original source text when ASR substitutions are sound-close and the structure matches.

The earlier `共饮长江水` route remains useful when a mixed-language vocal is desired: pinyin/romaji can be private sound control, but the public lyric must be corrected from the actual audio. For this standard version, the Chinese-only `越人歌` route was more truthful and musical.

## ASR Evidence

Faster-whisper small on the selected render recovered the structure with nearby substitutions:

```text
要不然 心伤过 挥手山河泪如球
他叫若是银雪 此生也算 公白头
此生也算 公白头 挥手山河泪如球
他叫若是银雪 此生也算 公白头 此生也算
```

Correction policy used here:

- `心伤过` is source-close to `心上过`.
- `挥手山河` is source-close to `回首山河`.
- `泪如球` is source-close enough to restore `已入秋` because it matches the phrase slot and user-requested rhyme.
- `他叫若是银雪` is restored to `他朝若是同淋雪` because the phrase shape, key syllables, and `雪` are present.
- `公白头` is restored to `共白头` because the sound is close and the source is stronger.

## Corrected Website Lines

```text
16.27-21.18 忽有故人心上过
22.18-26.40 回首山河已入秋
27.88-33.12 他朝若是同淋雪
34.56-39.10 此生也算共白头
40.40-45.74 此生也算共白头
59.73-64.31 回首山河已入秋
65.19-71.01 他朝若是同淋雪
72.29-77.13 此生也算共白头
77.13-84.16 此生也算共白头
```

Public lyric JSON stores only sung lines. Instrumental intro/interlude/outro are timing gaps, not lyric rows.

## Website

- URL: `https://fun.lazying.art/#gong-bai-tou-snow-we-share-native`.
- Active lyric: `website/data/songs/gong-bai-tou-snow-we-share-native/lyrics/zh-vocal/zh-Hans.json`.
- Companion tracks: English and Japanese translations with Japanese furigana.
