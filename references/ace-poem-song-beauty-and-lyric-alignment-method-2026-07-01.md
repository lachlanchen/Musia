# ACE Poem Song Beauty And Lyric Alignment Method

Date: 2026-07-01

This note records the practical method behind the recent Musia classical-poem
songs that sounded good and aligned well with their lyrics:

- `侠客行` adapted normal song;
- `将进酒` normal song;
- `梦游天姥` normal song;
- `侠客行 · 原诗版`, the original-poem experiment.

The goal is repeatable: generate a beautiful song first, then publish only
lyrics and timing that match the actual rendered audio.

Detailed `越人歌` case study and recursive-refinement playbook:

```text
references/yue-ren-ge-recursive-refinement-playbook-2026-07-01.md
```

Reusable pack generator for future classical-poem experiments:

```text
scripts/prepare_ace_poem_refinement_pack.py
```

## Core Rule

Use this priority order:

```text
beautiful song > clear sung vocal > truthful lyric alignment > literal text coverage
```

Prompt lyrics are a target, not proof. The selected audio must be audited with
ASR, separated vocal listening, and the planned lyric before it becomes website
data or a music-publishing package.

ASR is evidence, but not a judge. Keep the intended lyric when it is:

- phonetically close to the audio;
- stronger in grammar and context;
- supported by manual listening.

Override the planned lyric when the audio clearly skips, repeats, merges,
reorders, or changes the line.

## Route 1: Adapted Normal Song

Use this as the default when the user wants a beautiful song.

This route produced the strongest results for the normal versions of
`侠客行`, `将进酒`, and `梦游天姥`.

Pipeline:

```text
public-domain poem / user text
-> source and pronunciation check
-> modern singable adaptation
-> compact producer brief
-> ACE full-song generation
-> candidate listening and review
-> stem separation + ASR correction
-> website data and public audio mirror
```

Writing rules:

- preserve the poem's spirit, emotional arc, famous images, and signature lines;
- do not force every original line into the song;
- rewrite into verse, pre-chorus, chorus, bridge, and outro when useful;
- use short breath-friendly lines;
- allow 留白: rests, held vowels, repeated hooks, and quiet space;
- avoid dense strings of rare classical words when pronunciation matters;
- prefer concrete images over explanation.

Good lyric density for ACE-style short songs:

```text
80-120 seconds
about 30-45 short CJK lyric lines
average 4-7 CJK characters per short line
about 150-280 total CJK lyric characters for a compact song
```

This is a target, not a rule. If the model skips lines, simplify. If the song
feels empty, add a stronger hook or a short repeated phrase.

Producer brief shape:

```text
Title
Language
Duration and rough BPM
Emotional arc
Arrangement
Vocal direction
Negative instructions
Lyrics
```

Useful vocal direction:

```text
Clear upfront expressive Mandarin female vocal, melodic full-song phrasing,
natural diction, spacious breath, no real singer imitation, no clipped endings,
vocal slightly above the mix.
```

Arrangement should help the words, not cover them. For classical poetry, use
Chinese color carefully: pipa, guqin, dizi, strings, drums, and cinematic
reverb are useful, but keep the vocal clear during dense lyric sections.

## Route 2: Original Poem Experiment

Use this only when the user explicitly wants the exact original poem as the
lyric source.

This route produced the usable `侠客行 · 原诗版`, but it also showed the risk:
ACE can skip, merge, or garble dense classical text.

Pipeline:

```text
original poem only
-> source verification
-> pronunciation guide
-> multiple ACE candidates
-> reject candidates with poor ASR recovery
-> choose the clearest candidate
-> publish as original-poem / experiment only after audit
```

Rules:

- do not add modern hooks unless the user allows adaptation;
- write a pinyin guide before generation;
- manually check polyphonic and classical readings;
- try both dense couplet layout and phrase-sheet layout;
- test XL and non-XL / turbo variants when diction changes;
- reject candidates where ASR and listening recover almost no poem structure;
- label the item honestly, such as `Original Poem` or `ACE Poetry Demo`.

Observed lesson from `侠客行 · 原诗版`:

- XL turbo can sound polished but may lose intelligible poem text;
- a simpler non-XL/turbo route can sometimes preserve more diction;
- phrase-sheet formatting does not automatically improve recovery;
- publish only after stem-ASR and listening agree enough to justify the text.

## Pronunciation Prep

Before generation:

1. Verify the source text from a trusted source or local reference.
2. Run a pinyin baseline.
3. Manually inspect risky characters and names.
4. Save a pronunciation guide in the project.
5. Add the risky readings into the model-facing brief when needed.

Examples from the Li Bai work:

```text
将进酒: qiang1 jin1 jiu3
飒沓: sa4 ta4
事了: shi4 liao3
不留行: bu4 liu2 xing2
将炙: jiang1 zhi4
五岳倒为轻: wu3 yue4 dao4 wei2 qing1
烜赫: xuan3 he4
```

For normal-song adaptation, it is usually better to preserve a famous phrase
only if it is singable and likely to be pronounced correctly. Otherwise, keep
the image and emotion with simpler modern wording.

## Candidate Strategy

Generate more than one candidate when the song matters.

For adapted normal songs:

- start with ACE-Step XL/turbo quality;
- keep one clear full-song prompt;
- if the vocal is buried, clipped, or too dense, run a correction pass with
  clearer vocal and fewer words;
- choose by listening first, then by ASR evidence.

For exact poem experiments:

- very short poems may be too sparse for ACE as a one-pass lyric; if a
  single-pass render produces no ASR recovery or credit/subtitle hallucinations,
  repeat only original poem lines into verse/chorus form instead of adding
  modern text;
- long poems should not automatically be sung end-to-end. When the goal is a
  beautiful original-text song, first choose the most 朗朗上口, emotionally
  central, and musically rhyme-friendly original phrases, then reorganize those
  exact poem lines into verse / pre-chorus / chorus / bridge form. Repeating a
  strong couplet is allowed and often preferred when it improves melody, memory,
  押韵, and audience resonance;
- preserve the public text of the selected lines when using this route. The
  creative act is selection, ordering, repetition, and musical pacing, not
  rewriting the poem into modern lyrics;
- avoid putting forbidden-word lists in short-poem captions because the model
  can sing those warning words; use positive style/vocal instructions and keep
  pronunciation hints compact;
- the largest model is not always the selected model. Install and test the best
  available route, but choose by actual lyric recovery, hook clarity, and
  listening evidence. For `越人歌`, XL SFT was installed and tested, but XL
  Turbo repeated-hook seed `736361` was selected because it recovered more of
  the poem and the `心悦君兮` hook.
- keep a model-watch note per serious generation. As of 2026-07-01, the public
  ACE-Step 1.5 family exposes XL base/SFT/turbo routes and newer Diffusers XL
  checkpoints, but no public ACE XXL/XXXL checkpoint was found. Community
  reports show that XL SFT can be cleaner but less coherent for some lyric
  prompts, so final selection must be evidence-based.

- generate at least three candidates with different density/layout settings;
- include one simpler arrangement with the vocal very exposed;
- reject beautiful-but-unintelligible candidates;
- keep the best candidate only if the public label can honestly describe it.

Selection criteria:

```text
1. Does the song move emotionally?
2. Is the vocal audible and musical?
3. Does ASR recover the main structure?
4. Do manual listening and planned lyrics explain ASR errors?
5. Are skipped/repeated lines corrected in the final JSON?
6. Would the website player show the truth?
```

## Long-Poem Original-Text Selection Route

Use this when the user wants the poem's original language, but the source is too
long or uneven to become a beautiful song if sung linearly.

The method:

```text
long poem
-> identify the emotional spine
-> rank original lines by musicality and memorability
-> select the most singable lines
-> repeat the strongest hook/couplet
-> arrange into song form
-> generate candidates
-> ASR/listening correction
```

What to look for:

- 朗朗上口 / 啷啷上口: lines with clean mouth-feel, clear vowels, and natural
  phrase endings;
- 合乎音韵: repeated vowel/rhyme colors, balanced tones, parallel structure,
  and lines that can sit on melody without rushing;
- emotional center: a line that tells the listener why the song matters;
- image clarity: one or two vivid images are stronger than ten dense allusions;
- hook potential: a couplet that still feels powerful after two or three
  repetitions.

Allowed transformations while still calling it an original-text route:

```text
select original lines
repeat original lines
change order for song form
split a long line across breath points
omit less musical sections
```

Not allowed unless the route is explicitly "adapted":

```text
replace the poem with modern paraphrase
add new explanatory lyrics
invent a chorus not present in the source
```

Good structure:

```text
[Verse]
selected opening image
selected motion/conflict line

[Pre-Chorus]
line that raises emotional tension

[Chorus]
strongest original couplet
strongest original couplet repeated

[Bridge]
contrasting original image or philosophical turn

[Final Chorus]
strongest original couplet
short selected closing line
```

This route is the long-poem counterpart of the `越人歌` lesson: repetition is
not filler when it makes the original text become music.

## Lyric Correction Routine

Run a deep correction before website or LazyEdit/music publishing.

Recommended command pattern:

```bash
PYTHONNOUSERSITE=1 conda run --no-capture-output -n musia python \
  scripts/build_lyric_correction_packet.py \
  --title "Song Title" \
  --audio SELECTED.wav \
  --vocal-stem data/runs/<analysis-run>/stems/vocals.wav \
  --expected-lyrics data/creative_projects/<song>/lyrics/selected.txt \
  --language zh \
  --models large-v3 \
  --output-dir data/creative_projects/<song>/corrections/deep-large-YYYYMMDD
```

Use small/medium ASR as cross-checks, not final authority.

Correction policy:

- active vocal language owns timing;
- translations are based on the corrected active lyric, not the prompt draft;
- preserve intended words when they are sound-close and contextually right;
- add audible short phrases that ASR swallowed;
- remove planned lines that the audio did not sing;
- show repeated lines if the audio repeats them;
- document uncertainty in the production note.

For classical poems, keep the poem text where the rendered syllables are close
enough and the context is clear. Do not invent clean text that is not supported
by the audio.

## Website Preparation

After selecting and correcting a render:

```text
selected WAV
-> 320k public MP3 in ../MusiaSongs/audio/
-> ../MusiaSongs/audio.json
-> website/data/songs/<media-id>/manifest.json
-> website/data/songs/<media-id>/lyrics/zh-vocal/zh-Hans.json
-> website/data/songs/<media-id>/lyrics/zh-vocal/en.json
-> website/data/songs/<media-id>/lyrics/zh-vocal/ja.json
-> website/assets/covers/<media-id>-16x9.png
```

Validation:

```bash
npm run website:validate
node bin/musia.js fun-audit --media-id <media-id>
node --check website/app.js
git diff --check
```

Live checks:

```bash
curl -fsSL https://fun.lazying.art/data/songs/<media-id>/manifest.json
curl -fsSI -L https://lazyingart.github.io/MusiaSongs/audio/<file>.mp3
```

## Naming Rules

Use clean labels so the catalog remains understandable:

- adapted ACE standard version: plain title, for example `将进酒`;
- older ACE candidate: `ACE Legacy`;
- exact original poem route: `Original Poem` or `Original Poem Demo`;
- poem-recitation style: `ACE Poetry Demo`;
- DiffRhythm variants: `DR Short` or `DR Full Lyrics`;
- lower-quality localization/SVC routes: include the method suffix.

Only the selected standard ACE version should have the pure song name.

## Example Outcomes

`侠客行` adapted normal song:

- route: adapted normal song;
- result: smoother and more musical than exact poem forcing;
- lesson: preserve iconic wuxia images and hook, not every couplet.

`将进酒` normal song:

- route: adapted normal song;
- result: better than poem-recitation demo;
- lesson: famous phrases can be preserved when they work as hooks.

`梦游天姥` normal song:

- route: compressed normal-song adaptation;
- result: preserved the dream, thunder, immortals, waking, and freedom arc;
- lesson: a very long poem needs structural compression to sing well.

`侠客行 · 原诗版`:

- route: exact original poem experiment;
- result: good enough to publish with caveat, but still has small
  inconsistencies;
- lesson: exact poem route is possible, but it is not the default beautiful-song
  route.

## Definition Of Done

A poem song is ready only when all of these are true:

- selected candidate has been listened to;
- vocals are audible and emotionally convincing;
- lyrics were corrected against ASR plus listening;
- source/provenance and pronunciation decisions are documented;
- pinyin/furigana/translation data is based on corrected lyrics;
- website validation and Fun audit pass;
- generated audio remains in ignored data or MusiaSongs, not committed into the
  main repo;
- public title suffix honestly describes the route.
