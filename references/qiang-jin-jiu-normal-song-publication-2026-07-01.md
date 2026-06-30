# 将进酒 Normal Song Publication

Date: 2026-07-01

This note records the public Fun Lazying Art publication of the normal-song
version of Li Bai's `将进酒`.

## Public Item

- Media id: `qiang-jin-jiu-normal-song`
- Public URL: `https://fun.lazying.art/#qiang-jin-jiu-normal-song`
- Visible title: `将进酒`
- Artist: `Musia`
- Route: ACE-Step normal-song adaptation, not original-poem recital.

The older item remains separate:

- Media id: `qiang-jin-jiu`
- Visible title: `将进酒 · ACE Poetry Demo`
- Purpose: original-poem / poem-style demo route.

## Selected Audio

- Project: `data/creative_projects/qiang-jin-jiu-normal-song-20260701/`
- Selected source WAV:
  `ace_outputs/zh/6efc268a-3338-d611-f6ac-4d2b60384f49.wav`
- Public MP3:
  `https://lazyingart.github.io/MusiaSongs/audio/qiang-jin-jiu-normal-song-zh-Hans-ace-20260701.mp3`
- Duration: 112 seconds.
- Analysis run:
  `data/runs/qiang-jin-jiu-normal-song-20260701-20260701-004055-analysis/`

## Correction Evidence

The website lyric set was corrected from:

- same-audio large-v3 ASR;
- selected-audio small/medium ASR;
- vocal-stem small/medium ASR;
- no-VAD ASR for soft repeated phrases;
- the intended adapted Chinese lyric as a close-word reference.

The final active Mandarin lyric uses the audible structure of candidate 1. ACE
skipped or garbled several planned prompt sections, so they are not published
as sung lyrics. Close famous/intended phrases such as `将进酒，杯莫停`,
`天生我材必有用`, and `杯莫停` were preserved where ASR produced sound-close
variants.

## Website Files

- Manifest:
  `website/data/songs/qiang-jin-jiu-normal-song/manifest.json`
- Active Mandarin lyrics:
  `website/data/songs/qiang-jin-jiu-normal-song/lyrics/zh-vocal/zh-Hans.json`
- English translation:
  `website/data/songs/qiang-jin-jiu-normal-song/lyrics/zh-vocal/en.json`
- Japanese translation:
  `website/data/songs/qiang-jin-jiu-normal-song/lyrics/zh-vocal/ja.json`
- Cover:
  `website/assets/covers/qiang-jin-jiu-normal-song-16x9.png`
- Preparation script:
  `scripts/prepare_qiang_jin_jiu_normal_fun_item.py`

## Validation

Commands run:

```bash
npm run website:validate
node bin/musia.js fun-audit --media-id qiang-jin-jiu-normal-song
node --check website/app.js
git diff --check
```

Result: passed.
