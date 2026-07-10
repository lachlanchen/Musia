# 共白头 · Snow We Share · 雪中回声 Production Note

## Source

```text
忽有故人心上过，回首山河已入冬。
他朝若是同淋雪，此生也算共白头。
```

## Selected Render

- Route: ACE-Step 1.5 XL Turbo mixed-language route.
- Selected seed: `790972`.
- Selected audio: `data/creative_projects/gong-bai-tou-snow-we-share-20260709/selected/gong-bai-tou-snow-we-share-ace-xl-turbo-seed790972.mp3`.
- Public audio: `https://lazyingart.github.io/MusiaSongs/audio/gong-bai-tou-snow-we-share-ace-xl-turbo-seed790972-20260709.mp3`.
- Analysis: `data/runs/gong-bai-tou-snow-we-share-20260709-analysis/`.
- Website manifest: `website/data/songs/gong-bai-tou-snow-we-share/manifest.json`.

## Generation Attempts

Three routes were tested:

- `mixed_hook_xl_turbo`, seeds `790971-790974`: seed `790972` had the best recovered vocal structure.
- `mixed_compact_xl_turbo`, seeds `790981-790984`: simpler lyric, but weaker recovery than seed `790972`.
- `mixed_hook_v2_xl_sft`, seeds `790995-790996`: produced audio but no useful ASR recovery, so it was rejected.

This follows the Musia rule that SFT is tried when quality matters, but Turbo is kept when it produces the stronger actual song.

## Model-Facing Lyric Strategy

The first selected route used Mandarin pinyin and Japanese romaji inside an English-language ACE lyric block. The planned lyric was intentionally sparse, but the selected render still compressed the latter half.

This public version is now titled with the meaningful suffix `雪中回声 / Snow Echo` so it remains distinguishable from future no-pinyin remakes.

Future remake rule from the July 10 review: do not feed Mandarin pinyin as the sung lyric for the new version. Use Chinese characters directly, and change `回首山河已入冬` to `回首山河已入秋` only in a newly generated render that actually sings `秋`.

The public website does not publish the whole planned prompt as if it were sung. It publishes the selected render's audible structure, corrected with source-close forms where ASR was phonetically close.

2026-07-10 correction: a no-VAD medium ASR pass on both the selected full mix and separated vocal stem recovered a soft chorus continuation after the second `Hui shou shan he yi ru dong`. The previous website lyric jumped from 48.72s to 64.40s and therefore missed audible text. The final snow section was also split more carefully into Japanese and Mandarin-pinyin phrases instead of one merged line.

## Corrected Active Vocal

```text
3.18-6.88 Hu you gu ren xin shang guo
7.26-13.53 Lights fall soft in the snow
15.60-18.46 Hui shou shan he yi ru dong
18.46-21.98 Your name still glows
21.98-27.44 Tooi hi no koe ga mune ni furu
28.40-31.44 Furikaereba sekai wa
31.44-34.24 Fuyu no iro ni naru
34.84-37.86 Ta zhao ruo shi tong lin xue
37.86-41.02 Ci sheng ye suan gong bai tou
41.02-44.48 Hu you gu ren xin shang guo
44.48-48.72 Hui shou shan he yi ru dong
50.67-56.13 Let our hearts be less alone
56.13-63.73 Ah ah ah ah ah ah
64.36-67.00 Onaji yuki no shita de
67.00-70.42 Shiroku nareru kana
70.42-73.58 Ta zhao ruo shi tong lin xue
74.42-78.12 Ye suan gong bai tou
```

Public lyrics contain only sung lyric lines. Instrumental spans are inferred by the player from timing gaps and may show musical-note status in the player, but they are not song-level lyrics.

Correction packet:

```text
data/creative_projects/gong-bai-tou-snow-we-share-20260709/correction_packets/old-public-medium-20260710/CORRECTION_PACKET.md
```

## Website

- URL: `https://fun.lazying.art/#gong-bai-tou-snow-we-share`.
- Active lyric: `website/data/songs/gong-bai-tou-snow-we-share/lyrics/mixed-vocal/mul.json`.
- Companion tracks: English, Japanese, Mandarin Chinese.
