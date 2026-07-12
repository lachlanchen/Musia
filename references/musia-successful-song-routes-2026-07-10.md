# Musia Successful Song Routes

Date: 2026-07-10

This note records the routes that produced the strongest Musia songs so future
work starts from proven patterns instead of inventing new weak prompts.

## Quality Priority

Use this order when a song matters:

```text
beautiful melody and vocal
> coherent emotional hook
> truthful lyric timing
> source-text coverage
> strict same-melody or exact prompt fidelity
```

If a route hurts the melody or vocal, do not publish it as the standard version.
Keep it as a draft, label the method, and return to the closest successful ACE
route.

## Route A: Short Classical Source, Original Text

Example:

```text
越人歌 · 原诗版
```

Why it worked:

- selected the most musical original lines;
- repeated the strongest couplet as the hook;
- used private pronunciation simplification only when needed;
- restored original text when sound, phrase length, and context were close;
- corrected the website from ASR plus listening instead of raw prompt lyrics.

Reusable rule:

```text
original words + musical selection + repetition + conservative source restoration
```

Use this route for short ancient poems or source-sensitive lines where the user
wants the original text to remain beautiful.

## Route B: Mixed EN/JP/ZH Phonetic Hook

Examples:

```text
共饮长江水 · Same River
共白头 · Snow We Share · 雪中回声
巫峡月 · Moon Over Wu Gorge
哭晁卿衡 · Moon Over The Blue Sea
```

Why it worked:

- active sung layer used English plus Mandarin pinyin and Japanese romaji when
  native mixed script caused garbling;
- public native Chinese/Japanese/English tracks were treated as companion
  translations of the actual sung layer;
- lyrics were sparse enough for ACE to leave musical space;
- final text was corrected against ASR, VAD gaps, and manual listening.

Reusable rule:

```text
phonetic active vocal for mixed-language sound control
native-language companion tracks for meaning and display
corrected website JSON as the only publish lyric source
```

Use this route for EN/JP/ZH mixed pop songs when melody and audience feel matter
more than native-script pronunciation purity.

## Route C: Adapted Classical Poem Song

Examples:

```text
侠客行
将进酒
蜀道难
梦游天姥吟留别 adapted versions
```

Why it worked:

- the poem was rewritten or reorganized into a normal song shape;
- iconic original images and lines were preserved;
- the prompt stayed compact and positive;
- ACE XL/Turbo candidate sweeps were selected by listening plus lyric recovery.

Reusable rule:

```text
spirit and iconic lines > forced full-poem recitation
```

Use this route when the user wants a beautiful song inspired by a poem, not an
academic recitation.

## Route D: English-Led Mixed Emotional Song

Examples:

```text
共饮长江水 · Same River
The good old 共白头 · Snow We Share · 雪中回声
```

Why it worked:

- English gave ACE a stable lead-vocal scaffold;
- Mandarin pinyin and Japanese romaji appeared as short emotional hooks, not
  dense blocks;
- the arrangement was simple: piano/strings/light percussion/spacious reverb;
- no crammed words, no spoken narration, no real-singer imitation.

Reusable producer brief skeleton:

```text
Emotional bilingual/trilingual ballad, English lead with Mandarin pinyin and
Japanese romaji hooks, clear upfront vocal, sparse piano, warm strings, light
drums, spacious reverb, intimate and cinematic, no clipped endings, no buried
vocal, no spoken narration, no real singer imitation.
```

## Route E: Compact Mixed Anthem

Example:

```text
Best Am I · 我是天下第一等
```

Why it worked:

- dense mixed-language drafts failed even when audio levels were healthy;
- the successful render used a compact XL Turbo lyric with fewer unique lines,
  repeated hook phrases, and one language phrase per line;
- pinyin/romaji acted as private sound control for the active mixed vocal;
- XL SFT was tested but rejected because it hallucinated generic video-outro
  text;
- the final website lyric used the selected audio's compact sung structure
  rather than the longer draft prompt.

Reusable rule:

```text
public native lyric for meaning
-> compact ACE-facing mixed performance lyric
-> XL Turbo seed sweep
-> medium/large-v3 full-mix + vocal-stem ASR
-> publish only corrected active-vocal JSON
```

Use this route for motivational, pop, cute, or emotional mixed EN/ZH/JP songs
where the user values beauty and lyric accuracy but does not require every draft
line to be sung.

## Correction Discipline

For every public song:

1. Build or collect ASR on the exact selected audio and, when possible, the
   separated vocal stem.
2. Run no-VAD or focused tail checks for soft endings, long gaps, and mixed
   language lines.
3. Compare planned lyric to corrected active vocal line by line.
4. Preserve source text when word count and sound are close.
5. Change text only when the model clearly changed structure, omitted a phrase,
   repeated a phrase, or sang different sounds.
6. Update every companion language track with the same line ids and timings.
7. Use the corrected website active-vocal JSON for recording, LazyEdit video
   publishing, and Shipinhao Music.

## Negative Lessons

- Do not keep retrying a newly invented route when the first result is noisy,
  gibberish, or weak. Return to the closest successful project.
- Do not use DiffRhythm as a final beautiful-song route unless the user accepts
  it as a draft; its alignment may be useful but melody/vocal quality has been
  weaker.
- Do not pass internal conversation, pipeline notes, or correction caveats to
  platform metadata. Metadata is for listeners.
- Do not add instrumental `♪` rows to lyric JSON. Instrumental spans are UI
  state inferred from gaps.

## Current Snow We Share Correction

The old public `共白头 · Snow We Share · 雪中回声` remains the usable version. The
new July 10 no-pinyin remake is not promoted as the standard because the user
found it low quality.

The old public render was corrected on 2026-07-10 using no-VAD ASR:

```text
data/creative_projects/gong-bai-tou-snow-we-share-20260709/correction_packets/old-public-medium-20260710/CORRECTION_PACKET.md
```

Recovered active lines:

```text
50.67-56.13 Let our hearts be less alone
56.13-63.73 Ah ah ah ah ah ah
67.00-70.42 Shiroku nareru kana
70.42-73.58 Ta zhao ruo shi tong lin xue
```
