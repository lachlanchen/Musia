---
name: musia-music-production
description: Use when generating, correcting, reviewing, documenting, publishing, or handing off original music in Musia, including idea-to-song, lyrics-to-song, melody/chord-controlled songs, ACE-Step/YuE/SoulX route selection, vocal quality checks, song review reports, Fun Lazying Art website publishing, per-vocal lyric sets, and LALACHAN song-first video handoffs.
---

# Musia Music Production

Use this skill for original song creation and review. For strict same-song localization, also use `musia-song-localization`.

## Default Repo

```text
/home/lachlan/ProjectsLFS/Musia
```

## Core Rule

Do not accept a generated song just because a WAV exists. A usable song needs:

- audible sung vocal;
- healthy levels;
- coherent tempo/chord analysis;
- saved lyrics and prompt;
- review report;
- human listening pass when the result matters.

Quality comes before same-melody control. If a same-score/same-F0 route makes
the vocal, pronunciation, phrasing, or arrangement worse, label that render
experimental and leave it out of the public/final path. Regenerate with the
best full-song model instead, even if EN/JP/ZH end up as independent high-quality
versions rather than one perfectly shared melody.

Planned lyrics are intent, not truth. After generation, use listening and ASR/STT evidence to decide what the render actually sang. If the rendered vocal differs from the planned lyric, document the mismatch and publish lyrics/timing that match the audio.

Avoid real singer imitation or voice cloning unless the user owns or has explicit consent.

## Beautiful Song Standard

Before generating, write a compact producer brief with:

- emotional arc;
- short singable lyric lines;
- duration, language, key/BPM when known;
- arrangement and vocal direction;
- negative instructions such as no clipped endings, no buried vocal, and no real-singer imitation.

Prefer fewer stronger lines over dense poetry. For Chinese/Japanese, reduce pronunciation risk by using natural, short phrases and correcting after ASR/listening.

Do not cram words into the song just to preserve every detail. Use musical
space: 留白, held vowels, rests, repeated hooks, and breath-friendly pauses.
Some lines should be sparse and some can be fuller; the goal is a proper fit
to the melody and emotion, not the fewest words and not the most words.

Before generating or accepting EN/JP/ZH lyrics, do an LLM lyric-quality pass
when an API/model is available. Use OpenAI, DeepSeek, or a strong Codex/GPT-5.5
reasoning pass to check:

- rhythm fit: short singable phrases, line length, phrase stress, and likely breath points;
- musical space / 留白: whether a line should hold notes, leave rests, or repeat a simple hook instead of adding more words;
- rhyme / 押韵: English end rhyme or slant rhyme, Chinese rhyme groups, Japanese vowel/mora echoes;
- language-specific fit: English stress, Chinese tone comfort and natural wording, Japanese mora flow and particles;
- emotional clarity: the lyric should say something concrete and singable, not just be poetic filler.

Revise lyrics before generation if the LLM flags awkward rhythm, weak rhyme, overlong lines, or unnatural CJK wording.

## Fast Workflow

Create a song package:

```bash
musia song init \
  --title "Song Title" \
  --idea "short concept" \
  --vocal-language ja \
  --lyrics-file lyrics.txt \
  --genre "cinematic J-pop" \
  --style "piano, warm strings, gentle drums" \
  --voice-notes "clear upfront young female vocal, no real singer imitation"
```

Generate:

```bash
data/creative_projects/<song-id>/commands.sh generate
```

Review:

```bash
data/creative_projects/<song-id>/commands.sh review
```

If the review shows quiet vocals, wrong language, clipped endings, or poor lyric recovery, do not publish as final. Run a correction pass or label it as experimental.

Correct:

```bash
musia song correct \
  --project-dir data/creative_projects/<song-id> \
  --issues "vocal unclear or endings clipped" \
  --caption-extra "clearer vocal, fewer words per line" \
  --lyrics-file corrected-lyrics.txt
```

Handoff to LALACHAN:

```bash
musia song handoff \
  --project-dir data/creative_projects/<song-id> \
  --audio data/creative_projects/<song-id>/final/selected.mp3 \
  --cover data/creative_projects/<song-id>/assets/cover-16x9.png
```

## Reusable Script

Primary script:

```text
scripts/musia_song_workbench.py
```

It supports:

```text
init
review
correct
handoff
find-audio
```

Generated song folders are intentionally ignored by git:

```text
data/creative_projects/<song-id>/
```

## Model Routing

- Idea/lyrics to full song: ACE-Step 1.5 first.
- Vocal-only controlled short hook: SoulX if language metadata is supported.
- Strict source-song localization: Demucs/analysis plus YingMusic/SoulX prep, not full-song generation.
- Same melody is optional when it hurts quality. Prefer high-quality independent ACE/YuE language renders over low-quality same-score vocals.
- If Japanese/Chinese lyric accuracy is poor: shorten lines, reduce kanji ambiguity, increase vocal clarity in caption, try new seed/model, or use a specialized vocal workflow.
- For mixed EN/ZH/JP full-song demos on local open models, prefer one active `mul` sung/phonetic lyric track. If native CJK script collapses or garbles, use pinyin/romaji in the sung input and display native Chinese/Japanese as translations with pinyin/furigana. Document this as a phonetic render, not native-script singing.

## Website Publishing Rule

For `fun.lazying.art`, use the `musia-fun-website-item` publication workflow before calling a website item finished. Use shared `textTracks[]` only when all playable vocals truly sing the same line structure. If English, Chinese, and Japanese renders are independent or imperfect, create per-vocal `lyricSets[]`:

```text
lyrics/en-vocal/en.json
lyrics/en-vocal/zh-Hans.json
lyrics/en-vocal/ja.json
lyrics/zh-vocal/en.json
lyrics/zh-vocal/zh-Hans.json
lyrics/zh-vocal/ja.json
lyrics/ja-vocal/en.json
lyrics/ja-vocal/zh-Hans.json
lyrics/ja-vocal/ja.json
```

The active vocal owns timing and exact word highlighting. Other languages in the same set are translations of that vocal's actual sung lines and may rough-highlight corresponding tokens inside the same current `line.id`.

Correct every public lyric set from at least two evidence sources: ASR/STT from the actual vocal plus input/reference lyrics, second ASR, or manual listening. Add pinyin for Mandarin, furigana readings for Japanese kanji, and Jyutping readings for Cantonese. Run the publication audit:

```bash
musia fun-audit --media-id <media-id>
```

The Fun player should keep public song playback clean: native-language dropdown labels, a two-line KTV lyric carousel, visible current-chord highlighting, and capture mode for videos. To record a share clip with the original audio muxed directly, run:

```bash
musia fun-record --media-id <media-id> --skip-intro
```

For a mixed-language vocal, use:

```text
lyrics/mixed-vocal/mul.json
lyrics/mixed-vocal/en.json
lyrics/mixed-vocal/zh-Hans.json
lyrics/mixed-vocal/ja.json
```

## References

Read only as needed:

```text
references/musia-song-generation-and-website-runbook.md
references/fun-website-item-preparation.md
references/musia-song-workbench.md
references/lalachan-song-first-video-workflow.md
references/musia-full-capability-guide.md
references/musia-creative-studio.md
references/musia-website-json-format.md
```
