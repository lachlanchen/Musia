# 你是一只猪 Production Notes - 2026-06-29

## Goal

Generate a playful but resonant comfort song from the lyric idea:

```text
你是一只猪
```

Cultural titles:

| Language | Title | Reason |
| --- | --- | --- |
| zh-Hans | 你是一只猪 | Direct, funny, teasing, memorable. |
| en | You Little Piggy | Affectionate in English; avoids the harsher literal title. |
| ja | きみはこぶた | Cute and intimate in Japanese. |

## Selected Local Outputs

Generated audio is intentionally under ignored `data/` paths.

```text
data/creative_projects/ni-shi-yi-zhi-zhu-20260629/selected/ni-shi-yi-zhi-zhu-zh-master.wav
data/creative_projects/ni-shi-yi-zhi-zhu-20260629/selected/you-little-piggy-en.wav
data/creative_projects/ni-shi-yi-zhi-zhu-20260629/selected/kimi-wa-kobuta-ja.wav
```

Selected lyrics:

```text
data/creative_projects/ni-shi-yi-zhi-zhu-20260629/selected/lyrics.zh-Hans.master.txt
data/creative_projects/ni-shi-yi-zhi-zhu-20260629/selected/lyrics.en.txt
data/creative_projects/ni-shi-yi-zhi-zhu-20260629/selected/lyrics.ja.txt
```

Source idea folder:

```text
ideas-and-inspirations/xiao-xiao-zhu/
```

## Website Publication

Fun Lazying Art media ID:

```text
xiao-xiao-zhu-trilingual
```

Website URL:

```text
https://fun.lazying.art/#xiao-xiao-zhu-trilingual
```

Website data:

```text
website/data/songs/xiao-xiao-zhu-trilingual/manifest.json
website/data/songs/xiao-xiao-zhu-trilingual/lyrics/zh-vocal/
website/data/songs/xiao-xiao-zhu-trilingual/lyrics/en-vocal/
website/data/songs/xiao-xiao-zhu-trilingual/lyrics/ja-vocal/
website/assets/covers/xiao-xiao-zhu-16x9.png
```

Public audio repo:

```text
https://github.com/lazyingart/MusiaSongs
```

Public audio URLs:

```text
https://lazyingart.github.io/MusiaSongs/audio/xiao-xiao-zhu-zh-Hans.mp3
https://lazyingart.github.io/MusiaSongs/audio/xiao-xiao-zhu-en.mp3
https://lazyingart.github.io/MusiaSongs/audio/xiao-xiao-zhu-ja.mp3
```

Publication checks:

```text
npm run website:validate
musia fun-audit --media-id xiao-xiao-zhu-trilingual --strict
node --check website/app.js
git diff --check
```

All checks passed locally on 2026-06-29.

## Pipeline Used

1. Wrote Chinese, English, and Japanese singable lyrics.
2. Generated Mandarin first with ACE-Step.
3. Ran Musia review and analysis for stems, beats, chords, lyrics, and F0.
4. Corrected the Mandarin lyric density because the first render was too word-heavy.
5. Selected the second Mandarin correction as the master.
6. Ran the master-companion pipeline with DeepSeek writer/finalizer and OpenAI reviewer.
7. Manually corrected English/Japanese lyrics because the automatic companion package inherited ASR mistakes from the Mandarin transcript.
8. Rendered English and Japanese soft companions, prioritizing beauty over strict melody sameness.
9. Reviewed each candidate with Musia ASR and analysis.

## Quality Lessons

- Leave space. The first Mandarin lyric was emotionally good but too dense for the model.
- ASR evidence is useful but should not override the intended lyric when the sound is close.
- Do not feed ASR mistakes directly into target-language lyrics. In this run, `不赶路` was misread into anger-like wording, so the companion lyrics were manually corrected.
- English handled the soft-companion route well on the first pass.
- Japanese improved when using kana-heavy lyrics, but too much duration created filler. The selected Japanese version used a shorter duration to reduce filler.
- Same melody should remain optional. For this song, quality-first companions were better than strict same-melody synthesis.

## Reviews And Analysis

Reviews:

```text
data/creative_projects/ni-shi-yi-zhi-zhu-20260629/reviews/20260629-192414/SONG_REVIEW.md
data/creative_projects/ni-shi-yi-zhi-zhu-20260629/companions/en/reviews/20260629-193403/SONG_REVIEW.md
data/creative_projects/ni-shi-yi-zhi-zhu-20260629/companions/ja/reviews/20260629-193836/SONG_REVIEW.md
```

Analysis runs:

```text
data/runs/ni-shi-yi-zhi-zhu-20260629-20260629-192414-analysis
data/runs/en-20260629-193403-analysis
data/runs/ja-20260629-193836-analysis
```

Master-companion package:

```text
data/creative_projects/ni-shi-yi-zhi-zhu-20260629/master-companion-zh-to-en-ja
```
