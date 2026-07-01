# 晴天路 Production Note

Date: 2026-07-01

## Request

User requested an original song for `蜀道难` and asked to update the website.

This item is not the Li Bai poem text and not a direct adapted-poem render. It
is an original Musia Mandarin song inspired by the emotional world of
`蜀道难`: an impossible mountain road, fear, darkness, and choosing to keep
walking toward clear sky.

## Song

Title:

```text
晴天路
```

Core lyric idea:

```text
路再难也要走
心不要低头
黑夜被风吹散
梦越过山尽头
```

Original lyric source:

```text
data/creative_projects/shu-dao-nan-original-song-20260701/lyrics/zh-direct-clear.txt
```

Producer brief:

```text
data/creative_projects/shu-dao-nan-original-song-20260701/source/producer-brief.md
```

## Generation

Route: ACE-Step 1.5 XL Turbo original Mandarin song.

Attempts:

- `ace_zh.toml`, seeds `735501`, `735502`: first modern original lyric pass.
- `ace_zh_direct_clear.toml`, seeds `735601`-`735604`: shorter direct-clear lyric pass.

Selection:

- Rejected seed `735602` despite better vocal-stem overlap because large-v3
  evidence found audible `作词/作曲/编曲` style leakage in the vocal stem and
  selected-audio transcript.
- Selected seed `735601` because the full-mix no-VAD transcript had no intro
  credit leakage and preserved the main song structure.
- Trimmed selected seed `735601` at `84.5s` to remove a generated
  `Amara.org` outro.

Selected audio:

```text
data/creative_projects/shu-dao-nan-original-song-20260701/selected/qing-tian-lu-zh-Hans-ace-20260701-trimmed.wav
```

## Analysis

Analysis run:

```text
data/runs/shu-dao-nan-qing-tian-lu-20260701-analysis/
```

Artifacts include:

- `stems/vocals.wav`
- `stems/drums.wav`
- `stems/bass.wav`
- `stems/other.wav`
- `stems/instrumental.wav`
- `analysis/chords.json`
- `analysis/beats.json`
- `analysis/lyrics.json`

Detected tempo: about `152 BPM`.

## Lyric Correction

Correction packet:

```text
data/creative_projects/shu-dao-nan-original-song-20260701/correction_packets/seed-735601-trimmed-large-v3/CORRECTION_PACKET.md
```

Important correction choices:

- Use the trimmed full-mix large-v3 no-VAD transcript as the main evidence.
- Cross-check with vocal-stem ASR and the prompt lyric.
- Do not publish stem-only `作词/作曲/演唱` hallucinations because the selected
  full mix did not recover them.
- Do not publish the removed `Amara.org` outro.
- Publish only the lyric lines actually represented in the selected audio;
  skipped prompt lines remain unpublished.

Quality note:

This is usable as an original Musia song candidate and cleaner than the rejected
candidate with credit leakage, but it still required correction. Some prompt
lines were skipped or changed by ACE, so the public lyric track follows the
selected audio rather than the draft lyric.

## Website

Media id:

```text
shu-dao-nan-qing-tian-lu
```

Website files:

- `scripts/prepare_shu_dao_nan_qing_tian_lu_fun_item.py`
- `website/data/songs/shu-dao-nan-qing-tian-lu/manifest.json`
- `website/data/songs/shu-dao-nan-qing-tian-lu/lyrics/zh-vocal/zh-Hans.json`
- `website/data/songs/shu-dao-nan-qing-tian-lu/lyrics/zh-vocal/en.json`
- `website/data/songs/shu-dao-nan-qing-tian-lu/lyrics/zh-vocal/ja.json`
- `website/assets/covers/shu-dao-nan-qing-tian-lu-16x9.png`

Public audio mirror:

```text
../MusiaSongs/audio/shu-dao-nan-qing-tian-lu-zh-Hans-ace-20260701.mp3
https://lazyingart.github.io/MusiaSongs/audio/shu-dao-nan-qing-tian-lu-zh-Hans-ace-20260701.mp3
```

Fun URL:

```text
https://fun.lazying.art/#shu-dao-nan-qing-tian-lu
```

Validation:

```bash
npm run website:validate
node --check website/app.js
node bin/musia.js fun-audit --media-id shu-dao-nan-qing-tian-lu --strict
git diff --check -- scripts/prepare_shu_dao_nan_qing_tian_lu_fun_item.py references/shu-dao-nan-qing-tian-lu-production-2026-07-01.md website/data/catalog.json website/data/songs/shu-dao-nan-qing-tian-lu website/assets/covers/shu-dao-nan-qing-tian-lu-16x9.png
git -C ../MusiaSongs diff --check -- audio.json audio/shu-dao-nan-qing-tian-lu-zh-Hans-ace-20260701.mp3
```

Result: all passed locally.

