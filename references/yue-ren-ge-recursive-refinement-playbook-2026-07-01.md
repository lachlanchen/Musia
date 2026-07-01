# 越人歌 Recursive Refinement Playbook

Date: 2026-07-01

Song: `越人歌 · 原诗版`

Website:

```text
https://fun.lazying.art/#yue-ren-ge-original-poem
```

This note records the full method behind the successful `越人歌 · 原诗版`
render: how it became musical, why the lyric alignment was better than earlier
poem attempts, what still mismatches slightly, and how to repeat the process for
future high-quality Musia songs.

## Result Summary

Final selected local WAV:

```text
data/creative_projects/yue-ren-ge-original-poem-20260701/selected/yue-ren-ge-original-poem-zh-Hans-ace-20260701.wav
```

Final source candidate:

```text
data/creative_projects/yue-ren-ge-original-poem-20260701/ace_outputs/zh_xl_turbo_hook/44d78572-c06f-9e03-b8f7-705b65b04318.wav
```

Public audio mirror:

```text
https://lazyingart.github.io/MusiaSongs/audio/yue-ren-ge-original-poem-zh-Hans-ace-20260701.mp3
```

Website data:

```text
website/data/songs/yue-ren-ge-original-poem/manifest.json
website/data/songs/yue-ren-ge-original-poem/lyrics/zh-vocal/zh-Hans.json
website/data/songs/yue-ren-ge-original-poem/lyrics/zh-vocal/en.json
website/data/songs/yue-ren-ge-original-poem/lyrics/zh-vocal/ja.json
website/assets/covers/yue-ren-ge-original-poem-16x9.png
```

Analysis artifacts:

```text
data/runs/yue-ren-ge-original-poem-20260701-hook-analysis/
```

Reusable pack generator added:

```text
scripts/prepare_ace_poem_refinement_pack.py
```

## Core Philosophy

The success did not come from asking ACE to "sing this poem perfectly" once.
The success came from treating generation as a recursive creative loop:

```text
source truth
-> pronunciation truth
-> private model-facing simplification
-> multiple musical layouts
-> model sweep
-> ASR/listening rejection
-> hook-focused regeneration
-> truthful website correction
-> method update
```

The priority order is:

```text
beautiful melody
> smooth audible vocal
> emotional hook recovery
> truthful lyric timing
> literal full-text coverage
```

For a public website or music-publishing package, the final lyric JSON must
match the actual selected audio. The prompt lyric is intent, not proof.

ASR is also not absolute truth. The final correction uses this hierarchy:

```text
actual audible structure
> sound-close poetic compromise
> close intended original poem text
> ASR guess
> draft translation
```

The first publication restored more original text where the sound was close.
After user listening feedback, the active lyric was revised to a stronger
sound-close compromise where the render clearly sang a different but meaningful
phrase. For example, `心悦君兮` is now displayed as `心爱君兮`, and repeated
`君不知` positions are displayed as `追不着`. This makes the player feel closer
to the actual song while preserving the poem's emotional frame.

Rule:

```text
restore source when the sung phrase is close enough
compromise poetically when the model clearly sang another useful phrase
document every compromise
```

## Why This Worked

### 1. The poem was short, so it needed musical form

`越人歌` is much shorter than a modern song. A single exact pass gave ACE too
little structure. Several candidates produced weak lyric recovery or
subtitle-like hallucinations.

The breakthrough was:

```text
repeat only original poem lines
emphasize the final couplet as the hook
do not add modern words
```

This gave ACE enough repeated phrase material to create a coherent melody while
still staying faithful to the user's "原诗版" request.

### 2. The hook was emotionally central

The strongest line is:

```text
山有木兮木有枝，心悦君兮君不知。
```

The selected route made this line the musical anchor. That helped both melody
and audience resonance. A good poem-song generation needs one emotional center;
otherwise the model may wander through the text without a memorable contour.

### 3. Public text and model-facing text were separated

The public poem remains:

```text
搴舟中流
蒙羞被好兮
不訾诟耻
```

The private ACE-facing lyric used easier sound controls:

```text
牵舟中流
蒙羞披好兮
不子诟耻
```

This is not changing the public lyric. It is a pronunciation-control layer.
After generation, the public website restores the original characters when the
audio is sound-close enough.

This separation is important:

```text
public lyric = literature / website / user-facing truth
private lyric = model-control input
```

### 4. The prompt was positive and compact

Earlier attempts across Musia showed that long negative lists can leak into
audio, especially for short poems. The successful prompt did not overload the
caption with words like "subtitle", "credit", or "watermark" repeatedly.

Good prompt shape:

```text
Cinematic Mandarin Chinese ancient love art song.
Moonlit river, small boat, hidden longing, beautiful tender confession.
Clear upfront expressive female Mandarin vocal.
Melodic full-song phrasing.
Natural classical diction.
Final chorus centered on 心悦君兮 君不知.
The lyric uses only original 越人歌 words repeated as musical form.
Arrangement: guqin, pipa, xiao, soft strings, warm piano, restrained drums.
A minor, 72 BPM, 4/4.
```

The prompt tells the model what to do, not a long list of failure modes.

### 5. The largest model did not win automatically

`acestep-v15-xl-sft` was downloaded and tested because quality matters. For
this poem, it did not produce the best lyric recovery. The selected candidate
used:

```text
model: acestep-v15-xl-turbo
route: repeated hook
seed: 736361
duration: 100s
bpm: 72
key: A minor
```

Rule:

```text
install and test the best model, but select by evidence
```

Evidence means melody, vocal smoothness, hook recovery, ASR, and listening.
Model size is not a substitute for reviewing the actual song.

## Candidate Matrix

The selected project tried these routes:

| Route | Model | Result |
| --- | --- | --- |
| compact single-pass | `acestep-v15-xl-sft` | rejected; weak/no lyric recovery |
| spacious single-pass | `acestep-v15-xl-sft` | rejected; not enough poem structure |
| clean single-pass | `acestep-v15-xl-sft` | rejected; no reliable lyric recovery |
| sectioned single-pass | `acestep-v15-xl-turbo` | rejected; fragments only |
| repeated original | `acestep-v15-xl-turbo` | usable; improved text structure |
| repeated hook | `acestep-v15-xl-turbo` | selected; best hook recovery and musicality |
| repeated original | `acestep-v15-xl-sft` | rejected; poorer recovery for this case |

The lesson is not "always use Turbo." The lesson is "always run a real
candidate matrix when the song matters."

## Recursive Refinement Loop

### Pass 0: Source and intent

Record:

- source text;
- edition or variant;
- user intent;
- must-preserve lines;
- allowed adaptation level.

For `越人歌`, the adaptation level was strict: original poem words only, but
original lines could repeat to become a song.

### Pass 1: Pronunciation prep

Create `source/pronunciation-guide.md`.

For `越人歌`, risky readings were:

| Public text | Intended reading | Private control |
| --- | --- | --- |
| 搴舟 | `qian1 zhou1` | `牵舟` |
| 被好 | `pi1 hao3` | `披好` |
| 不訾 | `bu4 zi3` | `不子` |
| 心几烦 | `xin1 ji1 fan2` | keep and audit |

Use `pypinyin` as a baseline, but manually correct classical readings.

### Pass 2: Lyric layout matrix

Prepare multiple lyric layouts before generation:

```text
original exact
phonetic-control exact
sectioned
repeated original
repeated hook
```

For short poems, the repeated-hook route is often the best starting point.
It gives the model enough phrase repetitions to form a song.

### Pass 3: Model sweep

Run at least:

```text
XL SFT repeated hook
XL Turbo repeated hook
XL Turbo repeated original
```

Use XL SFT first when available, but keep Turbo as a serious candidate. Do not
discard a candidate just because the model name looks smaller or faster.

### Pass 4: Automated review

Run:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/musia_quality_check.py \
  AUDIO.wav \
  --language zh \
  --expected-lyrics-file PROJECT/lyrics/original-public.txt \
  --asr-model large-v3 \
  --output-dir PROJECT/reviews/CANDIDATE-large
```

ASR overlap does not need to be perfect for classical poetry, but it must
recover the real structure or the hook. Reject candidates with:

- no sung vocal;
- hidden/buried vocal;
- subtitle/credit hallucination;
- unrelated language;
- no recoverable central phrase;
- broken or clipped endings.

### Pass 5: Listening arbitration

Human listening decides the subtle cases:

- Is the melody memorable?
- Does the vocal feel like a continuous performance?
- Is the hook emotionally clear?
- Are ASR errors close to the intended poem?
- Is the mismatch acceptable and documentable?

This is where `越人歌` won: the melody and vocal were smooth, and the central
hook was strong enough to keep even with a small lyric mismatch.

### Pass 6: Full analysis

Run:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py \
  SELECTED.wav \
  --run-name yue-ren-ge-original-poem-20260701-hook-analysis \
  --max-duration 120 \
  --asr-model large-v3 \
  --language zh \
  --demucs-device cuda
```

This produces:

```text
stems/vocals.wav
stems/drums.wav
stems/bass.wav
stems/other.wav
stems/instrumental.wav
analysis/chords.csv
analysis/beats.csv
analysis/lyrics.json
REPORT.md
```

### Pass 7: Website truth correction

Write the website JSON from the selected audio, not from the planned lyric
alone.

For `越人歌`, the active Mandarin website track:

```text
website/data/songs/yue-ren-ge-original-poem/lyrics/zh-vocal/zh-Hans.json
```

uses:

- actual line timings from ASR/listening;
- pinyin per character;
- original poem text restored where sound-close;
- sound-close compromise wording where the rendered vocal consistently differs
  and the compromise is clearer, beautiful, and emotionally coherent;
- translations aligned to the corrected active lyric lines.

### Pass 8: Document the imperfections

Do not hide small mismatches. Record them in the production note:

```text
references/yue-ren-ge-original-poem-production-2026-07-01.md
```

The goal is honest publication, not pretending the model was perfect.

## New Reusable Script

Use the new pack generator for future short classical poem songs:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/prepare_ace_poem_refinement_pack.py \
  --title "越人歌" \
  --poem-file poem.txt \
  --project-id yue-ren-ge-next-experiment \
  --hook "山有木兮木有枝，心悦君兮君不知。" \
  --substitution "搴舟=牵舟" \
  --substitution "被好=披好" \
  --substitution "不訾=不子" \
  --duration 100 \
  --bpm 72 \
  --keyscale "A minor"
```

It creates:

```text
PROJECT/source/source-poem.md
PROJECT/source/pronunciation-guide.md
PROJECT/lyrics/original-public.txt
PROJECT/lyrics/phonetic-control.txt
PROJECT/lyrics/repeated-original-public.txt
PROJECT/lyrics/repeated-original-control.txt
PROJECT/lyrics/repeated-hook-public.txt
PROJECT/lyrics/repeated-hook-control.txt
PROJECT/lyrics/sectioned-public.txt
PROJECT/lyrics/sectioned-control.txt
PROJECT/configs/ace_xl_sft_repeated_hook.toml
PROJECT/configs/ace_xl_turbo_repeated_hook.toml
PROJECT/configs/ace_xl_turbo_repeated_original.toml
PROJECT/REFINEMENT_PLAN.md
PROJECT/commands.sh
```

Then run:

```bash
cd PROJECT
./commands.sh generate-sft
./commands.sh quality
./commands.sh generate-turbo-hook
./commands.sh quality
./commands.sh generate-turbo-original
./commands.sh quality
```

Only run full analysis after choosing a finalist:

```bash
./commands.sh analyze
```

## Tool Inventory

Generation:

- `third_party/ACE-Step-1.5/cli.py`
- `acestep-v15-xl-sft`
- `acestep-v15-xl-turbo`

Preparation:

- `scripts/prepare_ace_poem_refinement_pack.py`
- `pypinyin`
- manual classical-pronunciation audit

Review:

- `scripts/musia_quality_check.py`
- Whisper large-v3 ASR
- manual listening

Analysis:

- `scripts/run_pipeline.py`
- Demucs stem separation
- chord and beat extraction
- `ffmpeg` / `ffprobe`

Website:

- per-song prepare script, such as
  `scripts/prepare_yue_ren_ge_original_poem_fun_item.py`;
- `scripts/audit_fun_media_item.py`;
- `npm run website:validate`;
- `../MusiaSongs/audio/*.mp3`;
- `website/data/songs/<media-id>/manifest.json`;
- `website/data/songs/<media-id>/lyrics/<vocal-set>/<lang>.json`.

Documentation and memory:

- `references/yue-ren-ge-original-poem-production-2026-07-01.md`;
- `references/ace-poem-song-beauty-and-lyric-alignment-method-2026-07-01.md`;
- this playbook;
- `musia-music-production` skill in both local Codex skills and `../LazySkills`.

## Quality Checklist For Future Masterpiece Attempts

Before generation:

- [ ] Source text verified.
- [ ] User intent captured: adapted song or original-poem song.
- [ ] Hook chosen.
- [ ] Rare characters and polyphones audited.
- [ ] Public lyric separated from private model-control lyric.
- [ ] Candidate matrix planned before spending GPU time.

During generation:

- [ ] Try the best installed model first.
- [ ] Also run a practical fallback model.
- [ ] Use at least three seeds/routes when the song matters.
- [ ] Avoid long negative prompt lists.
- [ ] Keep vocal clear and forward.

After generation:

- [ ] Reject beautiful but unintelligible candidates.
- [ ] Reject candidates with no hook recovery.
- [ ] Keep a candidate only if the mismatch can be honestly corrected.
- [ ] Run large-v3 ASR on the finalist.
- [ ] Listen to separated vocal when uncertain.
- [ ] Correct website lyrics from actual audio.
- [ ] Document model, seed, route, mismatch, and final decision.

## Practical Rule

For future Musia poem songs, the best method is not:

```text
poem -> one prompt -> accept output
```

The best method is:

```text
poem -> source/pronunciation -> several lyric layouts -> several model routes
-> ASR/listening selection -> correction -> website truth -> skill update
```

That is the reusable `越人歌` lesson.
