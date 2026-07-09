# 巫峡月 · Moon Over Wu Gorge Production Note

## Source

```text
月照巫峡千峰寂，身似蜉蝣一粟轻。
江风送尽千帆过，百年浮沉随波去。
```

## Selected Render

- Route: ACE-Step 1.5 XL Turbo mixed-language route.
- Selected seed: `791111` from the cleaner v2 sweep.
- Selected audio: `data/creative_projects/wu-xia-yue-mixed-20260709/selected/wu-xia-yue-mixed-ace-xl-turbo-seed791111.mp3`.
- Public audio: `https://lazyingart.github.io/MusiaSongs/audio/wu-xia-yue-mixed-ace-xl-turbo-seed791111-20260709.mp3`.
- Analysis: `data/runs/wu-xia-yue-mixed-20260709-analysis/`.
- Website manifest: `website/data/songs/wu-xia-yue-mixed/manifest.json`.

## Attempts

- First sweep used denser poem-pinyin lines. ASR recovery was weak.
- Second sweep used clearer English lead lines, shorter pinyin hooks, and shorter Japanese romaji color lines.
- Seed `791111` was selected because it recovered `I am small in the silver light`, the Wu Xia phrase, the mayfly image, river wind, and the final small-heart line more coherently than the other checked candidates.

## Corrected Active Vocal

```text
15.02-23.03 I am small in the silver light
23.03-26.03 Yue zhao Wu Xia qian feng ji
26.59-30.51 A mayfly under endless sky, shen si
30.51-32.33 Fu you yi su qing
32.33-37.11 A mayfly under endless sky, shen si
37.11-39.17 Fu you yi su qing
39.55-41.79 River wind, carry me
41.79-45.55 Jiang feng qian fan guo
45.55-50.65 Hyakunen no yume, bai nian sui bo qu
52.99-56.25 Moon over Wu Xia
56.25-58.73 Everything is still
58.73-66.27 I am small, but my heart carries
```

The render dropped the planned outro and some final source-line repeats. Public lyrics follow the actual selected audio, with instrumental spans represented as `♪`.

## Cover Rule

A fresh cover was generated specifically for this song using only the current song imagery: moonlit Wu Gorge, silent peaks, Yangtze river, distant sails, a tiny human figure, and a vast lonely hopeful mood. No older song cover or stale prompt was reused.

## Website

- URL: `https://fun.lazying.art/#wu-xia-yue-mixed`.
- Default audio/language: `Mixed` (`languageCode: mul`).
- Active lyric: `website/data/songs/wu-xia-yue-mixed/lyrics/mixed-vocal/mul.json`.
- Companion tracks: English, Japanese, Mandarin Chinese.
