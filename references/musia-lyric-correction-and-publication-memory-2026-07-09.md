# Musia Lyric Correction And Publication Memory

Date: 2026-07-09

This note records the reusable lesson from `共饮长江水 · Same River`.

## Rule

Public Musia lyrics must match the selected audio, not the prompt and not one
ASR pass. ASR is evidence, but listening, user correction, VAD/waveform energy,
and the planned lyric must be reconciled before recording, website publishing,
LazyEdit video publishing, or Shipinhao Music packaging.

## Soft Tail Policy

Song endings and mixed-language tails are high-risk:

- ASR can stop early even when the separated vocal still has energy.
- Focused ASR can hallucinate unrelated text on soft tails.
- English or Japanese phrases can sit inside a timing gap between recognized
  Chinese/pinyin lines.
- User listening corrections are strong evidence when they are sound-close and
  supported by context.

For `共饮长江水 · Same River`, the final corrected tail is:

```text
54.06-57.82 Zhi yuan jun xin si wo xin
57.82-61.20 Ding bu fu xiang si yi
61.20-65.95 Same river, same longing
65.95-69.80 Give me all
69.80-74.04 ♪
```

The wrong intermediate guesses `Wo xiang xin` and `Same, same longing` were
removed after listening and VAD checks.

## Required Closeout

After a lyric correction:

1. Patch the active vocal JSON and every companion translation track.
2. Patch the manifest timeline and generator script if one exists.
3. Update the production note under `references/`.
4. Run:

```bash
node bin/musia.js fun-validate
node bin/musia.js fun-audit --media-id <media-id>
```

5. Commit and push the website update.
6. Wait for GitHub Pages deployment.
7. Fetch the live `fun.lazying.art/data/songs/...` JSON and verify the corrected
   lines are served before recording, publishing, or reporting completion.

## Recording And Publishing

For normal 4K portrait Musia player clips, use the realtime recorder with
`--publication-layout --capture-clock`. The slower deterministic recorder is for
debug/special visual renders, not the default fast publication path.

For LazyEdit video CLI publishes, use full platform names:

```text
shipinhao,instagram,youtube,douyin
```

Do not pass `sph,ins,y2b` to `scripts/lazyedit_publish.py --platforms`; those
aliases can fail at the LazyEdit CLI layer after processing has already run.

For Shipinhao Music or any pure-music handoff, use the corrected website active
lyric JSON. Never use the original prompt lyric or stale ASR draft.
