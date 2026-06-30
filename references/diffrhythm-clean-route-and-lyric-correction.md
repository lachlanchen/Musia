# DiffRhythm Clean Route And Lyric Correction

Date: 2026-06-30

## Why This Exists

The `云海之恋` work exposed two repeatable problems:

1. A full DiffRhythm render can follow an LRC well, but may hallucinate credits
   or extra outro words unless the prompt is explicit.
2. ASR can miss real sung material, especially soft CJK openings/outros and
   repeated color words such as `天蓝蓝 / 海蓝蓝`.

The fix is not to trust either the prompt or ASR blindly. The route should
generate with a clean prompt, then correct lyrics from several evidence sources:

```text
selected audio
same-vocal ASR
vocal-stem ASR when stems exist
no-VAD ASR for swallowed openings/outros
input/reference lyric
manual listening
```

Use this priority:

```text
actual audible structure > close intended lyric > ASR guess > translation draft
```

## Reusable Scripts

### DiffRhythm Clean Route

Script:

```text
scripts/run_diffrhythm_clean_route.py
```

Purpose:

- create a repeatable project folder under `data/creative_projects/`;
- copy source lyrics;
- create a simple LRC from plain lyrics or copy an existing hand-timed LRC;
- add a clean DiffRhythm prompt suffix;
- write `commands.sh`, `route.json`, and `ROUTE.md`;
- optionally run DiffRhythm, quality check, and full Musia analysis.

Prepared-only example:

```bash
PYTHONNOUSERSITE=1 conda run --no-capture-output -n musia python scripts/run_diffrhythm_clean_route.py \
  --title "云海之恋" \
  --lyrics-file data/creative_projects/yun-hai-zhi-lian-diffrhythm-full-20260630/lyrics/zh_full.txt \
  --language zh \
  --audio-length 285 \
  --vocal-start 8 \
  --tail-margin 8 \
  --style-prompt "cinematic Mandarin ballad, vast sky and ocean atmosphere, emotional clear female vocal, piano, soft strings, spacious reverb, beautiful and longing" \
  --output-name clean
```

Run generation and QA:

```bash
PYTHONNOUSERSITE=1 conda run --no-capture-output -n musia python scripts/run_diffrhythm_clean_route.py \
  --title "云海之恋" \
  --lrc-file data/creative_projects/yun-hai-zhi-lian-diffrhythm-full-20260630/lyrics/yun_hai_zhi_lian_full_285.lrc \
  --language zh \
  --audio-length 285 \
  --style-prompt "cinematic Mandarin ballad, vast sky and ocean atmosphere, emotional clear female vocal, piano, soft strings, spacious reverb, beautiful and longing" \
  --output-name clean \
  --run \
  --review
```

Run generation, QA, and full analysis:

```bash
PYTHONNOUSERSITE=1 conda run --no-capture-output -n musia python scripts/run_diffrhythm_clean_route.py \
  --title "云海之恋" \
  --lrc-file data/creative_projects/yun-hai-zhi-lian-diffrhythm-full-20260630/lyrics/yun_hai_zhi_lian_full_285.lrc \
  --language zh \
  --audio-length 285 \
  --style-prompt "cinematic Mandarin ballad, vast sky and ocean atmosphere, emotional clear female vocal, piano, soft strings, spacious reverb, beautiful and longing" \
  --output-name clean \
  --run \
  --review \
  --analyze
```

The generated `ROUTE.md` records the exact DiffRhythm command and the
acceptance checklist.

### Lyric Correction Packet

Script:

```text
scripts/build_lyric_correction_packet.py
```

Purpose:

- run normal ASR on selected audio;
- run normal ASR on a vocal stem when available;
- run no-VAD ASR on both files to catch soft or swallowed material;
- write a single `CORRECTION_PACKET.md` with ASR text and segment timing.

Example using the `云海之恋 · 海风短歌` selected audio:

```bash
PYTHONNOUSERSITE=1 conda run --no-capture-output -n musia python scripts/build_lyric_correction_packet.py \
  --title "云海之恋 · 海风短歌" \
  --audio data/creative_projects/yun-hai-zhi-lian-haifeng-duange-20260630/selected/yun-hai-zhi-lian-haifeng-duange-zh-Hans-ace-20260630.mp3 \
  --vocal-stem data/runs/yun-hai-zhi-lian-haifeng-duange-20260630-analysis/stems/vocals.wav \
  --expected-lyrics data/creative_projects/yun-hai-zhi-lian-haifeng-duange-20260630/lyrics/zh.txt \
  --language zh \
  --models base small medium \
  --output-dir data/creative_projects/yun-hai-zhi-lian-haifeng-duange-20260630/reviews/lyric-correction-packet
```

Use this packet before preparing website data or a LazyEdit/Shipinhao music
handoff. The publisher should receive the corrected website lyric JSON, not the
raw prompt lyric.

## DiffRhythm Clean Prompt

Always append the clean suffix for text-prompt DiffRhythm routes:

```text
Only sing the supplied LRC lyrics. No spoken words, no credits, no songwriter names, no artist names, no extra intro words, no extra outro words, no watermark, no distortion, clear lead vocal, smooth full-song phrasing, natural breath, no clipped final syllables.
```

This was added after the first `云海之恋` full render produced a credit-like tail
similar to `词曲 李宗盛`. The second render with the clean prompt was selected.

If using `--ref-audio-path`, DiffRhythm does not accept a simultaneous
`--ref-prompt`, so the clean constraints must be documented and checked during
review rather than injected as style text.

## Lyric Correction Routine

For every public song or recording:

1. Run normal ASR on the selected mix.
2. If stems exist, run normal ASR on `stems/vocals.wav`.
3. Run no-VAD ASR when the first or last sung line may be missing, or when an
   ASR segment contains a long timing gap.
4. Compare against the input/reference lyric.
5. Restore a planned lyric only when:
   - ASR produced a sound-close variant;
   - the phrase fits the timing gap;
   - listening or user feedback supports it.
6. Change the lyric away from the prompt when multiple ASR passes consistently
   hear a different phrase and the sound supports the change.
7. Update all text tracks in the same lyric set with identical `line.id`,
   `start`, and `end` values.
8. Update the manifest timeline and the production note.
9. Run:

```bash
npm run website:validate
node bin/musia.js fun-audit --media-id <media-id>
node --check website/app.js
git diff --check
```

10. Push and wait for Pages deploy before telling the user the website is fixed.

## Yun Hai Duange Lesson

The first published `云海之恋 · 海风短歌` lyric JSON started at:

```text
17.76 云在天地间
```

Deeper no-VAD ASR later recovered the real opening as variants:

```text
天来了 海来了
天烂烂 海烂烂
```

Together with listening feedback, those were corrected to:

```text
14.68-16.20 天蓝蓝
16.20-17.78 海蓝蓝
```

The same issue happened at the outro:

```text
72.64-74.20 天蓝蓝
74.20-75.76 海蓝蓝
```

Therefore, no-VAD ASR is now part of the routine whenever a song begins or ends
with soft, repeated, or highly vowel-like CJK phrases.

## Website Rule

The website item is not finished until corrected data exists here:

```text
website/data/songs/<media-id>/manifest.json
website/data/songs/<media-id>/lyrics/<vocal-set>/<active-lang>.json
website/data/songs/<media-id>/lyrics/<vocal-set>/<translation-lang>.json
```

For Musia songs, all public publishing paths should reuse those corrected JSON
files. Do not publish the raw generated prompt lyrics as subtitles or music
platform lyrics.
