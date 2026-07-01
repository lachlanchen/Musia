# 越人歌 · 原诗版 Production Note

Date: 2026-07-01

Media ID: `yue-ren-ge-original-poem`

Public URL:

```text
https://fun.lazying.art/#yue-ren-ge-original-poem
```

Public audio mirror:

```text
https://lazyingart.github.io/MusiaSongs/audio/yue-ren-ge-original-poem-zh-Hans-ace-20260701.mp3
```

## Source Text

The source poem used for the public lyric track is:

```text
今夕何夕兮，搴舟中流。
今日何日兮，得与王子同舟。
蒙羞被好兮，不訾诟耻。
心几烦而不绝兮，得知王子。
山有木兮木有枝，心悦君兮君不知。
```

Reference URLs checked:

- Wikisource: `https://zh.wikisource.org/wiki/越人歌`
- Poetry reference page found during source check: `https://www.shicile.com/detail/6410299372455`

Variant note:

- Some editions annotate `搴舟中流` with `舟` also written as `洲`.
- Musia uses `舟`, matching the user-provided text and the song image of a boat
  in midstream.

## Pronunciation Prep

Risky classical readings:

| Public text | Intended reading | Private generation hint |
| --- | --- | --- |
| 搴舟 | `qian1 zhou1` | `牵舟` |
| 被好 | `pi1 hao3` | `披好` |
| 不訾 | `bu4 zi3` | `不子` / `不子苟耻` |
| 心几烦 | `xin1 ji1 fan2` | kept as `心几烦` with caption/context |

Public website text restores the original poem where the selected audio is
sound-close. The private ACE lyric file may contain phonetic substitutions.

## Model Scan And Install

ACE-Step 1.5 local checkpoints before this task:

- `acestep-v15-base`
- `acestep-v15-turbo`
- `acestep-v15-xl-turbo`
- `acestep-5Hz-lm-1.7B`

The ACE-Step docs list `acestep-v15-xl-sft` as the highest-quality XL SFT route
for detail-oriented generation, so it was downloaded into:

```text
third_party/ACE-Step-1.5/checkpoints/acestep-v15-xl-sft
```

No XXL/XXXL ACE checkpoint was present in the installed model list. Current
Musia policy is now: try the best practical local model first, but let listening
and ASR decide the final selection.

External model/community check on 2026-07-01:

- official ACE-Step 1.5 docs list the XL family as `xl-base`, `xl-sft`, and
  `xl-turbo`, all using the larger 4B DiT route;
- the `acestep-v15-xl-sft` model card describes XL SFT as the detail-oriented
  SFT route with CFG and 50-step inference;
- the ACE Hugging Face organization shows newer Diffusers-format XL checkpoints,
  but no public ACE XXL/XXXL checkpoint was found;
- community issue/discussion reports include cases where XL SFT has higher
  audio quality but weaker melody/rhythm/lyric coherence than Turbo or older
  routes on specific prompts, so Musia must select by listening and ASR rather
  than model size alone.

## Candidate Results

The single-pass exact poem was too short for ACE. Most candidates produced
instrumental/no-recovered-lyric output or subtitle-like hallucinations.

Important result:

```text
For very short classical poems, repeat original lines into a real song form.
Do not add modern lyrics unless the user asks for adaptation.
```

Candidate summary:

| Route | Model | Seeds | Result |
| --- | --- | --- | --- |
| compact single-pass | `acestep-v15-xl-sft` | `736321`, `736322` | rejected; no lyric recovery / subtitle-style hallucination |
| spacious single-pass | `acestep-v15-xl-sft` | `736301`, `736302` | rejected; no usable poem recovery |
| clean single-pass | `acestep-v15-xl-sft` | `736331`, `736332` | rejected; no ASR lyric recovery |
| sectioned single-pass | `acestep-v15-xl-turbo` | `736341`-`736344` | rejected; only fragments |
| repeated original | `acestep-v15-xl-turbo` | `736351`-`736354` | usable; seed `736352` had best raw overlap |
| repeated hook | `acestep-v15-xl-turbo` | `736361`-`736364` | selected; seed `736361` had better final-couplet recovery |
| repeated original | `acestep-v15-xl-sft` | `736355`, `736356` | rejected; no ASR lyric recovery |

Selected local WAV:

```text
data/creative_projects/yue-ren-ge-original-poem-20260701/selected/yue-ren-ge-original-poem-zh-Hans-ace-20260701.wav
```

Selected source candidate:

```text
data/creative_projects/yue-ren-ge-original-poem-20260701/ace_outputs/zh_xl_turbo_hook/44d78572-c06f-9e03-b8f7-705b65b04318.wav
```

Selected seed:

```text
736361
```

## Analysis Artifacts

Final analysis run:

```text
data/runs/yue-ren-ge-original-poem-20260701-hook-analysis
```

Artifacts:

- stems: `stems/vocals.wav`, `stems/drums.wav`, `stems/bass.wav`, `stems/other.wav`, `stems/instrumental.wav`
- chords: `analysis/chords.csv`, `analysis/chords.json`
- beats: `analysis/beats.csv`, `analysis/beats.json`
- ASR: `analysis/lyrics.json`, `analysis/lyrics.txt`
- report: `REPORT.md`

Detected:

- tempo: `69.84` BPM
- chord center: Am-centered progression
- chord segments: `25`
- beat count: `47`

## Website Correction

Website script:

```text
scripts/prepare_yue_ren_ge_original_poem_fun_item.py
```

Generated website files:

```text
website/data/songs/yue-ren-ge-original-poem/manifest.json
website/data/songs/yue-ren-ge-original-poem/lyrics/zh-vocal/zh-Hans.json
website/data/songs/yue-ren-ge-original-poem/lyrics/zh-vocal/en.json
website/data/songs/yue-ren-ge-original-poem/lyrics/zh-vocal/ja.json
website/assets/covers/yue-ren-ge-original-poem-16x9.png
```

Public audio mirror files:

```text
../MusiaSongs/audio/yue-ren-ge-original-poem-zh-Hans-ace-20260701.mp3
../MusiaSongs/audio.json
```

Correction policy used:

- preserve original text when the selected audio is sound-close;
- restore `心爱君兮` to `心悦君兮` because it is a sound-close ASR substitution
  and the planned lyric requires `悦`;
- restore private hints `牵舟/披好/不子` to public `搴舟/被好/不訾`;
- document that this render is not a perfect classical recitation because ASR
  sometimes hears `君不知` as `追不着`, and the final `君不知` tail is not
  recovered.

### Sound-Close Compromise Revision

After user review, the active website lyric was revised from strict source
restoration to a sound-close, context-smooth sung lyric. The original poem
remains the source and emotional frame, but the website player now follows the
selected performance more honestly where the rendered vocal repeatedly differs
from the classical text.

Important replacements:

| Original/source-restored text | Large-v3 ASR evidence | Published sung compromise | Reason |
| --- | --- | --- | --- |
| `搴舟中流` | `前愁终留` | `牵愁中流` | keeps the river image, matches the audible `qian/chou/zhong/liu` shape, and reads poetically |
| `得与王子同舟` | `得欲望之王子` | `得遇望之王子` | preserves the prince/longing meaning while matching the audible phrase better |
| `得与王子同舟` | `得欲望之同舟` | `得与望之同舟` | keeps the boat image and the audible `wang zhi tong zhou` shape |
| `心悦君兮` | `心爱君兮` | `心爱君兮` | consistently audible, semantically beautiful, and close to the intended confession |
| `君不知` | `追不着` | `追不着` | audible in two repeated hook positions and emotionally coherent as unreachable longing |
| `心几烦而不绝兮` | `心急凡尔不觉兮` | `心急烦而不绝兮` | keeps the source meaning of restless longing while using the clearer sung shape |

This is the preferred policy when the user wants the visible lyric to feel good
with the rendered song:

```text
strict source text only when sound-close
sound-close poetic compromise when the model clearly sang a different phrase
document the compromise instead of pretending the render is exact
```

Validation:

```text
npm run website:validate
node --check website/app.js
PYTHONNOUSERSITE=1 conda run -n musia python scripts/audit_fun_media_item.py --media-id yue-ren-ge-original-poem --strict
```

All passed on 2026-07-01.

## Reusable Lesson

For short ancient poems:

1. Install and test the highest-quality route, but do not assume the largest
   model wins.
2. Avoid forbidden-word lists in ACE captions; short lyrics can cause ACE to
   sing words like subtitle/credit warnings.
3. Use private phonetic substitutions for rare classical characters.
4. If the exact poem is too short, repeat only original poem lines into
   verse/chorus form.
5. Select by final-couplet recovery and emotional center, not only raw overlap.
6. Publish corrected lyrics that match the audio, with provenance for any
   imperfect classical-word recovery.
