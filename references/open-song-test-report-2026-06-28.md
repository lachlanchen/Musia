# Open Song Test Report - 2026-06-28

This report records the local Musai test pass on free/open audio fixtures. Large generated audio, downloaded source media, model checkpoints, and third-party repositories are intentionally kept out of git.

## Machine / Environment

- Repo: `/home/lachlan/ProjectsLFS/Musai`
- Core env: `musai`
- Quality envs present: `.conda/soulxsinger`, `.conda/diffrhythm`, `.conda/heartmula`, `.conda/moss-music`, `.conda/songgen`
- GPU path used: CUDA
- Main pipeline: Demucs + faster-whisper + librosa chord/beat baseline
- Singing tests: YingMusic-Singer-Plus path from the existing `yingmusic` env, and SoulX-Singer from `.conda/soulxsinger`

## Reproducible Install Commands

Core Musai env:

```bash
bash scripts/bootstrap_musai.sh
```

Optional research/backend code and model assets:

```bash
bash scripts/download_quality_backends.sh expanded-repos
bash scripts/download_quality_backends.sh soulx
bash scripts/install_quality_envs.sh soulx
```

The SoulX env needed these extra packages during this test pass:

```bash
PYTHONNOUSERSITE=1 .conda/soulxsinger/bin/python -m pip install "lightning>=2.2,<3" fiddle cloudpickle
```

`scripts/install_quality_envs.sh soulx` now installs those packages.

## Open / Free Test Songs Downloaded

Run:

```bash
PYTHONNOUSERSITE=1 conda run -n musai python scripts/download_open_songs.py --all
```

Downloaded locally:

| ID | Local audio | Source / rights note |
| --- | --- | --- |
| `danny-boy-1917` | `data/open_songs/danny-boy-1917/original.ogg` | Wikimedia Commons public-domain/free-media page. |
| `chinese-vocal-ensemble` | `data/open_songs/chinese-vocal-ensemble/original.ogg` | Wikimedia Commons public-domain/pre-1972 sound-recording page. |
| `e-scris-pe-tricolor-vocal` | `data/open_songs/e-scris-pe-tricolor-vocal/original.ogg` | Wikimedia Commons free-media page. |
| `hotaru-no-hikari` | `data/open_songs/hotaru-no-hikari/original.ogg` | Wikimedia Commons public-domain self-dedication page. |
| `moli-hua-ks-synth` | `data/open_songs/moli-hua-ks-synth/original.opus` | Wikimedia Commons CC0 page; instrumental/synth fixture. |

`sakura-sakura-vocal-synth` is in the catalog but hit Wikimedia HTTP 429 during this pass. The downloader now continues through individual failures and reports them.

## Analysis Pipeline Test

Run:

```bash
MAX_DURATION=60 ASR_MODEL=small DEMUCS_DEVICE=cuda scripts/test_open_songs_matrix.sh
```

Outputs:

| Run | Input | Tempo | Beats | Chord Segments | Lyrics Status | Output Directory |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `test-danny-en-60` | English 1917 vocal recording | `129.20` | `126` | `67` | `ok`, but ASR text poor | `data/runs/test-danny-en-60/` |
| `test-chinese-vocal-zh-60` | Early Chinese vocal/instrumental recording | `76.00` | `79` | `69` | `ok`, but ASR text poor | `data/runs/test-chinese-vocal-zh-60/` |
| `test-hotaru-ja-60` | Japanese vocal/guitar recording | `143.55` | `142` | `102` | `ok`, but ASR text empty | `data/runs/test-hotaru-ja-60/` |
| `test-moli-hua-instrumental-30` | CC0 Mo Li Hua synth/instrumental | `136.00` | `50` | `32` | `skipped` | `data/runs/test-moli-hua-instrumental-30/` |

Each run produced:

```text
source/input.wav
stems/bass.wav
stems/drums.wav
stems/vocals.wav
stems/other.wav
stems/instrumental.wav
stems/human_sound.wav
analysis/beats.json
analysis/beats.csv
analysis/chords.json
analysis/chords.csv
analysis/lyrics.json
analysis/lyrics.txt
manifest.json
REPORT.md
```

Important quality note: stem separation, beat extraction, chord extraction, and artifact writing passed. Raw ASR did not pass a serious lyric-quality gate on these old/noisy/open recordings. For real localization, provide reference lyrics or use a stronger alignment path.

## Full-Song Analysis

An earlier full Danny Boy analysis exists:

```text
data/runs/full-danny-217/
```

It contains full-length stems, beats, chords, lyrics artifacts, and reports. The ASR text is not reliable enough to drive lyric adaptation without a reference lyric file.

## Chinese Localization Outputs

Existing first-verse package:

```text
data/runs/danny-boy-zh-localization/localization/zh-CN/
```

Important files:

| Artifact | Path |
| --- | --- |
| Original target lyrics | `data/runs/danny-boy-zh-localization/localization/zh-CN/target_lyrics.txt` |
| YingMusic target text | `data/runs/danny-boy-zh-localization/localization/zh-CN/target_text_yingmusic.txt` |
| YingMusic vocal | `data/runs/danny-boy-zh-localization/localization/zh-CN/localized_vocal_zh-CN.wav` |
| YingMusic mix | `data/runs/danny-boy-zh-localization/localization/zh-CN/final_mix_zh-CN_first_verse.wav` |
| SoulX target lyrics v1 | `data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_target_lyrics_v1.txt` |
| SoulX target metadata v1 | `data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_target_zh_metadata.json` |
| SoulX vocal, best experimental pass | `data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_localized_vocal_zh-CN_first_verse.wav` |
| SoulX same-music mix, best experimental pass | `data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_final_mix_zh-CN_first_verse.wav` |
| SoulX MP3 preview | `data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_final_mix_zh-CN_first_verse.mp3` |

SoulX target lyric v1:

```text
丹尼风笛声声呼唤越过山谷越高山夏日远玫瑰凋落我仍痴等你再归来
```

SoulX generation command:

```bash
CONTROL=melody scripts/run_soulx_svs.sh \
  third_party/SoulX-Singer/example/audio/zh_prompt.mp3 \
  third_party/SoulX-Singer/example/audio/zh_prompt.json \
  data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_target_zh_metadata.json \
  data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_render_zh_melody
```

Mix command:

```bash
scripts/mix_vocal_with_instrumental.sh \
  data/runs/danny-boy-zh-localization/localization/zh-CN/synthesis_inputs/instrumental_first_verse.wav \
  data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_render_zh_melody/generated.wav \
  data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_final_mix_zh-CN_first_verse.wav \
  data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_final_mix_zh-CN_first_verse.mp3
```

## Vocal Quality Gate

SoulX itself passed its own Mandarin demo:

```text
data/runs/soulx-demo-zh/generated.wav
```

The Musai wrapper also passed the same style of demo invocation:

```bash
CONTROL=score scripts/run_soulx_svs.sh \
  third_party/SoulX-Singer/example/audio/zh_prompt.mp3 \
  third_party/SoulX-Singer/example/audio/zh_prompt.json \
  third_party/SoulX-Singer/example/audio/zh_target.json \
  data/runs/soulx-wrapper-demo-zh
```

A faster-whisper Mandarin check recognized the demo as:

```text
像我这样懦弱的人 凡事都要留几分
```

The Danny Boy Chinese render did not pass the same quality bar. The best SoulX experimental pass was audible and Chinese-like, but faster-whisper recovered only partial/incorrect Mandarin from the mixed output:

```text
暂逸归生生怀怨怨的很善 日月玫瑰掉落我只等你乖
```

Decision: keep this as an experimental artifact, not a final production-quality localized song.

## What Worked

- Downloaded several open/free fixtures and stored source metadata.
- Generated bass, drums, vocals, other, instrumental, and human_sound stems.
- Generated beat and chord artifacts for each test run.
- Verified SoulX model inference works locally on CUDA.
- Built a practical SoulX metadata rewrite helper for Mandarin lyric replacement.
- Produced a first-verse Mandarin experimental same-music mix.

## What Did Not Yet Meet The Bar

- Raw ASR on old/noisy public-domain recordings is poor.
- English SoulX preprocessing is blocked by a NeMo/Torch mismatch:

```text
ImportError: cannot import name 'SequenceParallel' from 'torch.distributed.tensor.parallel'
```

- Automatic same-melody Chinese lyric replacement is not production quality yet. It needs corrected note/phoneme alignment, better phrase segmentation, or a backend such as YingMusic-Singer-Plus running on cleaner inputs.

## Next Engineering Steps

1. Add reference-lyrics mode to the test matrix for public-domain/traditional songs.
2. Add phrase-level alignment instead of one long 30-token SoulX metadata segment.
3. Use manual MIDI/note correction for the first verse before rerendering.
4. Add objective checks: ASR target match, vocal loudness, F0 correlation, and duration alignment.
5. Keep ACE-Step/YuE/FunMusic for beautiful reinterpretation mode, not strict same-song localization.
