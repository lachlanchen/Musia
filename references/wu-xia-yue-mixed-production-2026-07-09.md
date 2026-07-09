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
07.08-11.24 Moon over the gorge
12.00-14.50 Kawa no kaze
16.12-22.82 I am small in the silver light
22.82-25.60 Yue zhao Wu Xia jian fang jing
25.60-29.70 I may fly under endless sky
29.70-32.22 Shan si fu yu yi su jing
32.22-36.04 I may fly under endless sky
36.04-39.46 Shan si fu yu yi su jing
39.46-41.62 River wind, carry me
41.62-44.84 Jiang feng qian fang guo
45.42-47.92 Hyakunen no yume
47.92-50.58 Bai nian sui bo qu
52.92-55.86 Moon over Wu Xia
55.86-58.54 Everything is still
58.54-66.72 I am small, I am free, but my heart can't feel
```

The first public draft was too poetic in several rows. On 2026-07-09 it was corrected again using selected-render small ASR, selected/vocal-stem large-v3 English ASR, Mandarin large-v3 cross-check packets, and user review. The active mixed track now follows the heard phonetic surface more tightly: the opening `Moon over the gorge` and `Kawa no kaze` are restored, `qian feng` became `jian fang`, `shen si fu you yi su qing` became `shan si fu yu yi su jing`, `qian fan` became `qian fang`, and the final line follows the ASR-supported `can't feel` rather than the planned `can feel`.

Correction packets:

- `data/creative_projects/wu-xia-yue-mixed-20260709/correction_packets/selected-large-v3-20260709/CORRECTION_PACKET.md`
- `data/creative_projects/wu-xia-yue-mixed-20260709/correction_packets/selected-large-v3-zh-20260709/CORRECTION_PACKET.md`

The render drops the drafted bridge/outro and some final source-line repeats. Public lyrics contain only sung lyric lines. Instrumental spans are inferred by the player from timing gaps and may show musical-note status in the player, but they are not song-level lyrics.

## Cover Rule

A fresh cover was generated specifically for this song using only the current song imagery: moonlit Wu Gorge, silent peaks, Yangtze river, distant sails, a tiny human figure, and a vast lonely hopeful mood. No older song cover or stale prompt was reused.

## Website

- URL: `https://fun.lazying.art/#wu-xia-yue-mixed`.
- Default audio/language: `Mixed` (`languageCode: mul`).
- Active lyric: `website/data/songs/wu-xia-yue-mixed/lyrics/mixed-vocal/mul.json`.
- Companion tracks: English, Japanese, Mandarin Chinese.
