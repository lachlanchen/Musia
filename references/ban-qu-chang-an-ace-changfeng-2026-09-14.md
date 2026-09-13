# 半曲长安: ACE 长风 version

## User direction

The first published song was MiniMax-Music3 seed 91302, not ACE. The user found
it insufficiently beautiful and requested a similar-lyric ACE version with
distinguishable suffixes, then specified **更燃、更上头**.

Keep the old recording available as `半曲长安 · MiniMax`. The new recording is
`半曲长安 · ACE · 长风`. Never overwrite the old audio or recycle its timings.
This is another arrangement/performance, not a same-melody localization.

## Production brief

Return to the proven `acestep-v15-xl-turbo`, 8-step non-thinking route used for
successful Musia songs including 越人歌. Reuse compact positive conditioning,
an emotionally clear repeated hook, and a seed sweep. The model family is
familiar, but beauty remains a listening judgment, not a model-name guarantee.

104 BPM guofeng pop-rock: galloping bass, propulsive drums, pipa, guitars and
sweeping strings. Warm clear female verses, a soaring repeated chorus, a
half-time bridge and a complete resolution. Bring the title hook forward into
the opening. Preserve the original Chang'an/Yellow River/danxia/homecoming
imagery, keep Mandarin characters, and leave phrase space rather than cramming.

The chorus ends with `把那半首 为你弹响` for an open, strong `ang` vowel;
the final intimate `今夜 为你弹完` resolves the promise. The bridge is shortened
to two hopeful lines. This is an original lyric, not an original-poem constraint.

Inputs:
`ideas-and-inspirations/ban-qu-chang-an/lyrics.ace-changfeng.zh-Hans.txt` and
`ace-changfeng-caption.txt`.

## Reproduce the sweep

```bash
PYTHONNOUSERSITE=1 CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n musia \
  python scripts/run_ace_candidate_sweep.py \
  --lyrics ideas-and-inspirations/ban-qu-chang-an/lyrics.ace-changfeng.zh-Hans.txt \
  --caption ideas-and-inspirations/ban-qu-chang-an/ace-changfeng-caption.txt \
  --output-dir data/creative_projects/ban-qu-chang-an-ace-changfeng-20260914/sweep \
  --seeds 914101 914102 914103 914104 914105 914106 --duration 150 --bpm 104
```

The runner serializes two-seed batches, freezes input/model identity, retains
logs and records exact seed/audio hashes. A prior complete batch is reused on
resume; conflicting inputs or unregistered partial outputs stop the run.

After generation: signal-health screening, APEX shortlist as a ranking hint,
independent MOSS review, large-v3 vocal/full-mix ASR, source-close lyric
correction, translations/ruby, exact-render beats/chords and website checks.
No recording or social/music-platform publication was requested in this turn.

## Second arrangement pass

All six 150-second candidates passed the signal-health gate. Seeds 914103 and
914105 ranked highest in that batch on APEX musicality (2.80/2.78 out of 5),
but MOSS described both as restrained ballads. MOSS's prose is not a reliable
listening verdict: its time ranges and instrumental descriptions require
cross-checking, and it can hallucinate technical faults. Nonetheless, the
user's energetic direction warranted a clearer second brief rather than
selecting solely by a learned quality score.

The second pass keeps the same 28 native-Chinese lyric lines, changes the
opening section tag from Intro to Chorus, removes gentle/half-time emphasis
from the caption, foregrounds drums/guitar/pipa, and targets 118 BPM / 138 s.
Seeds: 914201-914204, still XL Turbo with 8 steps and no thinking/LM rewrite.
This is a regeneration, not a speed-up of the earlier audio.

```bash
PYTHONNOUSERSITE=1 CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n musia \
  python scripts/run_ace_candidate_sweep.py \
  --lyrics ideas-and-inspirations/ban-qu-chang-an/lyrics.ace-changfeng-anthem.zh-Hans.txt \
  --caption ideas-and-inspirations/ban-qu-chang-an/ace-changfeng-anthem-caption.txt \
  --output-dir data/creative_projects/ban-qu-chang-an-ace-changfeng-20260914/anthem-sweep \
  --seeds 914201 914202 914203 914204 --duration 138 --bpm 118
```

Operational notes: use `PYTHONNOUSERSITE=1` with the conda environment; an
obsolete user-site pykakasi otherwise shadows the working dependency. In shell
loops, pass `</dev/null` to FFmpeg/model child commands so they cannot consume
the loop's input rows. The generation runner revalidates completed audio hashes
before resuming, and rejects changed input identity or ambiguous partial output.

`run_pipeline.py --lyrics-ref` currently stores a reference-only lyric result,
so it is not an ASR correction pass. For actual recognition omit that argument
and run the correction packet separately with the reference lyric.

## Selected rendition

Selected **914203**, XL Turbo 8 steps, no LM rewriting. Duration **138 s**,
native stereo 48 kHz, target 118 BPM, measured beat-tracker tempo 117.454 BPM.
The final choice favors the more forward second arrangement and better lyric
retention over the slightly higher APEX score of first-pass 914103.
The opening hook begins immediately, followed by an instrumental fill; this
was generated in the new arrangement, not achieved by speeding up old audio.

| Seed group | Coherence | Musicality | Memorability | Outcome |
| --- | --- | --- | --- | --- |
| 914103, first pass | 2.95 | 2.80 | 2.87 | Higher ranking, more restrained brief |
| 914105, first pass | 2.94 | 2.78 | 2.84 | Retained private candidate |
| 914201, second pass | 2.92 | 2.73 | 2.85 | Repeated pre-chorus and compressed chorus text |
| 914202, second pass | 2.89 | 2.70 | 2.82 | More text drift/repeats |
| **914203, second pass** | **2.91** | **2.72** | **2.84** | Selected for website audition |
| 914204, second pass | 2.90 | 2.68 | 2.84 | More missing chorus content |

APEX numbers are five-point learned ranking signals, not a beauty certificate.
Human listening approval is pending. MOSS's analysis prose repeatedly describes
generic piano ballads and approximate 100 BPM even where beat analysis shows
117.454 BPM; its alleged noise locations are not treated as verified faults.
Do not promise a masterpiece from these automated checks alone.

Both selected WAV and the 320 kb/s MP3 pass signal health: -12.7 LUFS,
-1.0 dBFS true peak, no clipped/non-finite samples, 6.2 LU loudness range,
and a quiet ending with 2.7 seconds of trailing silence. Do not compress or
speed it up merely to imply excitement.

Local selected package:
`data/creative_projects/ban-qu-chang-an-ace-changfeng-20260914/selected/`

- `ban-qu-chang-an-ace-changfeng.wav`: original selected PCM audio.
- `ban-qu-chang-an-ace-changfeng.mp3`: public playback copy with embedded cover.
- `lyrics-final/`: reviewed ZH/EN/JA JSON, TXT, LRC and audit decisions.
- `manifest.json`: exact audio hashes, model/seed, selection and analysis paths.

Stems, 249 detected beats and 106 chord segments are under
`data/runs/ban-qu-chang-an-ace-914203/`. Chords/key/meter remain analysis-grade,
not a musician-verified lead sheet; the website and Atlas must not imply otherwise.

## Lyric decisions

Evidence: large-v3 normal separated-vocal ASR, large-v3 no-VAD on both the full
mix and vocal stem, original native lyric, and independent MOSS transcription.
The review file is versioned at
`ideas-and-inspirations/ban-qu-chang-an/ace-changfeng-914203-review.json`.

All 28 planned line positions are accounted for. Lines 1-24 and 26-28 retain
the source wording after source-close spelling correction. Line 25 is a real
structural change: the second chorus sings only `等我回来`, not the whole
planned `等我归来 坐在你身旁`. All three public tracks translate that shorter
line. The first chorus still includes the full line.

Preserve `半首琴声`, `城墙`, `晚霞`, `一曲未尽`, `灯火渐淡`, `认得`,
`丹霞`, `远山`, `半曲`, and `弹完` where recognizers produce phonetically
nearby but less coherent text. Do not turn `伴手`/`伴奏`, `淡夏`, or `贪婪`
into literal published lyrics. Some consonants in the performance are soft;
source-informed correction does not claim the synthesis pronounced every word
perfectly.

Opening `长安`: both Whisper passes merge the name into `肠`, while the
independent transcription and later repetitions support the intended name.
The exporter now permits an **explicit source-bound reviewed phrase override**.
It retains that ASR span as one `长安` token and labels the timing approximate;
it does not invent separate syllable times. Every override needs the exact
recognized source string and a reason. Unit tests cover stale evidence and
zero-duration words. Unreviewed count changes still fail.

MOSS's later timestamps drift by several seconds, so only full-mix large-v3
word anchors drive the public timing. No instrumental rows are added. Mandarin
pinyin is checked against the corrected native lyric, including `弹响 tán
xiǎng`, `一曲未尽 yì qǔ wèi jìn`, and `半曲 bàn qǔ`. Japanese proper names
and ambiguous readings are explicitly reviewed, including `長安 ちょうあん`,
`丹霞 たんか`, `年 とし`, and `留める とめる`.

## Cover and publication

Fresh 16:9 artwork was generated with the built-in image tool and visually
reviewed. Saved at `website/assets/covers/ban-qu-chang-an-ace-changfeng-16x9.png`.
Prompt: an adult woman in crimson Tang-inspired hanfu and a gold hair ornament
strides into a strong wind on colossal Chang'an city walls, carrying a guqin;
red Danxia mountains and the luminous Yellow River recede beneath a golden dawn
and cyan sky. Heroic romantic journey/homecoming; clear human focal point,
immense architectural scale, no text, logo or watermark. This uses the current
adult-woman hanfu story, not Aya's older figurine identity.

New public item: https://fun.lazying.art/#ban-qu-chang-an-ace-changfeng

Old item retained: https://fun.lazying.art/#ban-qu-chang-an

Names are `半曲长安 · ACE · 长风` and `半曲长安 · MiniMax`; the old media ID,
audio and timings stay intact. The catalog default is unchanged. The explicit
user request for model/version suffixes overrides the usual pure-name ACE rule.

Rebuild using `scripts/prepare_ban_qu_chang_an_ace_fun_item.py`, then run
`musia atlas-build --media-id ban-qu-chang-an-ace-changfeng`, strict Fun audit,
and Fun validation. Audio is committed only in `../MusiaSongs` (commit
`263b6db`), never in the main Musia repository. Model weights remain local.

`scripts/test_ban_qu_chang_an_website.py` now accepts `--media-id` and
`--output-dir`, derives checkpoints from each actual lyric track, and validates
desktop/mobile playback, seeking, current-word and chord movement, ruby,
cover load, and horizontal overflow. Run it locally after audio Pages is ready,
then again with `--live` after the Fun deploy. It verifies player mechanics,
not musical or linguistic correctness.

## Release verification

Musia publication commit: `134cf7c`. Website Pages run `34789685817` succeeded.
MusiaSongs Pages built commit `263b6db`; an MP3 range request returned HTTP 206
with exactly the requested 64 bytes. Both repos were pushed to `main`.

Five exporter tests passed; strict audits passed for both song items and full
Fun validation passed. Local and live browser tests passed at 1440x1000 and
390x844: playback clock, real MP3 seeking, lyric IDs/word highlights at 1.18,
47.88, 84.86 and 127.84 seconds, current chord visibility/movement, cover/ruby,
and no horizontal overflow. Smooth chord scrolling is allowed to settle before
the screenshot check; checking only the existence of an `.active` class was
insufficient. Test browser contexts and the ephemeral local server were closed.

Live EN/JA/ZH lyric JSON was fetched and compared structurally to the local
reviewed files: all 28 lines matched, including the shortened line 25 in each
language. The old live title is `半曲长安 · MiniMax`. Screenshots and JSON test
evidence remain under the new project's `review/website/` directory.
