# 梦游天姥 Production Note

Date: 2026-07-01

## Public Item

- Media id: `meng-you-tian-mu`
- Public URL: `https://fun.lazying.art/#meng-you-tian-mu`
- Visible title: `梦游天姥`
- Artist: `Musia`
- Route: ACE-Step normal-song adaptation, not full original-poem recital.

## Source

The user provided Li Bai's `梦游天姥吟留别`. The source was compressed into a
normal-song lyric because the full poem is too long and dense for reliable ACE
lyric adherence. The song preserves the poem's major arc:

- sea mist and distant Tianmu;
- moonlit ascent and cloud ladder;
- thunder, stone gate, gold terrace, immortals;
- waking from the dream;
- refusal to bow: `安能低眉，安能折腰`.

## Candidate Review

Three ACE candidates were generated:

- Candidate 1: selected. It preserved the poem's dream/thunder/immortal/freedom
  arc best, though ASR required careful correction.
- Candidate 2: rejected. Simpler lyric, but it skipped too much of the intended
  structure.
- Candidate 3: rejected. Short hook route became too sparse and lost the poem
  identity.

Selected audio:

```text
data/creative_projects/meng-you-tian-mu-20260701/ace_outputs/zh/26269f27-43d6-35e3-9b9d-6b85f20477b9.wav
```

Analysis run:

```text
data/runs/meng-you-tian-mu-20260701-20260701-011745-analysis/
```

## Lyric Correction

The website lyric set was corrected from:

- same-audio `large-v3` ASR;
- selected-audio small/medium ASR;
- separated-vocal small/medium ASR;
- no-VAD passes for soft openings and merged phrases;
- the intended adapted lyric as a sound-close reference.

The active Mandarin website lyric uses 22 timed lines. Sound-close intended
phrases such as `天姥`, `安能低眉`, and `安能折腰` were preserved. Prompt lines that
were skipped or too garbled are not published as sung text.

## Website Files

- Manifest:
  `website/data/songs/meng-you-tian-mu/manifest.json`
- Active Mandarin lyrics:
  `website/data/songs/meng-you-tian-mu/lyrics/zh-vocal/zh-Hans.json`
- English translation:
  `website/data/songs/meng-you-tian-mu/lyrics/zh-vocal/en.json`
- Japanese translation:
  `website/data/songs/meng-you-tian-mu/lyrics/zh-vocal/ja.json`
- Cover:
  `website/assets/covers/meng-you-tian-mu-16x9.png`
- Preparation script:
  `scripts/prepare_meng_you_tian_mu_fun_item.py`

## Cover

Generated with the built-in image generation tool, then normalized to 1600x900:

```text
/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/ig_0ff40dcbca0516cf016a43fbcd8d548191a22a32fd11247aec.png
```

Prompt theme: moonlit dream mountain, sea mist, celestial gate, golden palace,
white deer on a green cliff, modern polished album-cover style.

## Validation

Commands run:

```bash
npm run website:validate
node bin/musia.js fun-audit --media-id meng-you-tian-mu
node --check website/app.js
git diff --check
```

Result: passed.
