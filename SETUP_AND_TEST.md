# Setup And Test

This file is the fresh-clone path for Musai. It covers the core local pipeline that other people can run from this repository without downloading the large research backends.

Large generated files are ignored by git:

- `data/open_songs/`
- `data/runs/`
- `.conda/`
- `.cache/`
- `third_party/`
- model weights and audio/video outputs

## Requirements

- Linux or macOS shell
- Conda on `PATH`
- FFmpeg, installed by the bootstrap script through conda
- NVIDIA CUDA GPU recommended for Demucs separation, but CPU can work more slowly

No API key is required for the core smoke test. `DEEPSEEK_API_KEY` or `OPENAI_API_KEY` is only needed for the optional lyric/localization performance scripts.

## One-Command Smoke Test

From a fresh clone:

```bash
git clone https://github.com/lachlanchen/Musai.git
cd Musai
bash scripts/setup_and_smoke_test.sh
```

The script does this:

1. Creates or reuses the `musai` conda environment.
2. Installs the core Python/audio stack.
3. Downloads the open Danny Boy fixture.
4. Runs the Musai pipeline on the first 45 seconds.
5. Writes stems, lyrics, beats, chords, manifest, and report under `data/runs/smoke-danny/`.

Expected outputs:

```text
data/runs/smoke-danny/source/input.wav
data/runs/smoke-danny/stems/bass.wav
data/runs/smoke-danny/stems/drums.wav
data/runs/smoke-danny/stems/vocals.wav
data/runs/smoke-danny/stems/other.wav
data/runs/smoke-danny/stems/instrumental.wav
data/runs/smoke-danny/stems/human_sound.wav
data/runs/smoke-danny/analysis/lyrics.txt
data/runs/smoke-danny/analysis/beats.csv
data/runs/smoke-danny/analysis/chords.csv
data/runs/smoke-danny/manifest.json
data/runs/smoke-danny/REPORT.md
```

Use CUDA explicitly:

```bash
MUSAI_DEMUCS_DEVICE=cuda bash scripts/setup_and_smoke_test.sh
```

Use a different run name:

```bash
MUSAI_SMOKE_RUN_NAME=my-smoke bash scripts/setup_and_smoke_test.sh
```

Validated locally on 2026-06-28 with:

```bash
MUSAI_DEMUCS_DEVICE=cuda \
MUSAI_SMOKE_RUN_NAME=smoke-docs-setup \
MUSAI_SMOKE_MAX_DURATION=30 \
MUSAI_SMOKE_ASR_MODEL=tiny \
bash scripts/setup_and_smoke_test.sh
```

Result:

```text
data/runs/smoke-docs-setup/REPORT.md
data/runs/smoke-docs-setup/stems/{bass,drums,vocals,other,instrumental,human_sound}.wav
data/runs/smoke-docs-setup/analysis/{beats,chords,lyrics}.*
```

## Manual Core Setup

```bash
bash scripts/bootstrap_musai.sh
PYTHONNOUSERSITE=1 conda run -n musai python scripts/download_open_songs.py --id danny-boy-1917
PYTHONNOUSERSITE=1 conda run -n musai python scripts/run_pipeline.py \
  data/open_songs/danny-boy-1917/original.ogg \
  --run-name smoke-danny \
  --max-duration 45 \
  --asr-model tiny
```

## Open-Song Matrix Test

Run several open/free fixtures:

```bash
MAX_DURATION=60 ASR_MODEL=small DEMUCS_DEVICE=cuda scripts/test_open_songs_matrix.sh
```

This writes:

```text
data/runs/test-danny-en-60/
data/runs/test-chinese-vocal-zh-60/
data/runs/test-hotaru-ja-60/
data/runs/test-moli-hua-instrumental-30/
```

The dated test report is:

```text
references/open-song-test-report-2026-06-28.md
```

## Optional Heavy Backends

These are not needed for the core smoke test. They download large codebases and model weights into ignored local directories.

Clone/update research repos:

```bash
bash scripts/download_quality_backends.sh expanded-repos
```

Install SoulX-Singer and weights:

```bash
bash scripts/download_quality_backends.sh soulx
bash scripts/install_quality_envs.sh soulx
```

Verify SoulX wrapper on its bundled Mandarin demo:

```bash
CONTROL=score scripts/run_soulx_svs.sh \
  third_party/SoulX-Singer/example/audio/zh_prompt.mp3 \
  third_party/SoulX-Singer/example/audio/zh_prompt.json \
  third_party/SoulX-Singer/example/audio/zh_target.json \
  data/runs/soulx-wrapper-demo-zh
```

## Dedicated Localization Performance Demo

After the open-song matrix and optional SoulX demo artifacts exist, run:

```bash
MUSAI_LYRIC_PROVIDER=deepseek \
DEEPSEEK_MODEL=deepseek-reasoner \
scripts/run_localization_performance_pipeline.sh
```

This writes:

```text
data/runs/localization-performance-20260628/REPORT.md
data/runs/localization-performance-20260628/localization_performance.json
data/runs/localization-performance-20260628/en-to-zh-danny/target_lyrics_zh.txt
data/runs/localization-performance-20260628/en-to-zh-danny/soulx_target_metadata_zh.json
data/runs/localization-performance-20260628/zh-to-en-molihua/target_lyrics_en.txt
```

Provider options:

```bash
scripts/run_localization_performance_pipeline.sh --provider deepseek --model deepseek-reasoner
scripts/run_localization_performance_pipeline.sh --provider openai --model gpt-5.5
```

The script creates lyric packages and checks existing render artifacts. It does not claim production quality unless the rendered singing passes the intelligibility gate in its report.

## Script Map

| Script | Purpose |
| --- | --- |
| `scripts/setup_and_smoke_test.sh` | Fresh-clone setup plus smoke test. |
| `scripts/bootstrap_musai.sh` | Create/reuse conda env and install core packages. |
| `scripts/download_open_songs.py` | Download free/open fixtures and metadata. |
| `scripts/run_pipeline.py` | Run stems, lyrics, beats, chords, manifest, report. |
| `scripts/test_local_pipeline.sh` | Minimal local smoke test using the existing env. |
| `scripts/test_open_songs_matrix.sh` | EN/ZH/JA open fixture matrix. |
| `scripts/download_quality_backends.sh` | Clone/download optional heavy model backends. |
| `scripts/install_quality_envs.sh` | Create isolated envs for optional heavy backends. |
| `scripts/run_soulx_svs.sh` | Run SoulX-Singer SVS inference. |
| `scripts/soulx_rewrite_metadata.py` | Replace SoulX lyric/phoneme metadata while preserving timing. |
| `scripts/mix_vocal_with_instrumental.sh` | Mix generated vocal with instrumental and normalize loudness. |
| `scripts/run_localization_performance_pipeline.sh` | Dedicated EN/ZH localization performance demo using DeepSeek/OpenAI. |
| `scripts/run_localization_performance_pipeline.py` | Python implementation for the dedicated localization performance demo. |
| `scripts/musai_create.py` | Creative CLI for idea/lyrics/chords/notation/reference-audio song projects. |
| `scripts/musai_studio_web.py` | Local Musai Studio web app. |
| `scripts/start_musai_studio_tmux.sh` | Starts Musai Studio in tmux. |
| `scripts/musai_quality_check.py` | Generated-audio QA: duration, levels, ASR, lyric overlap. |
| `scripts/musai_lyricfit_openai.py` | Optional OpenAI lyric adaptation helper. |

## Current Quality Boundary

The core analysis pipeline is reproducible. It extracts stems, lyrics artifacts, beats, chords, and reports.

The fully automatic same-melody translated singing layer is not production-ready yet. Current open-source backends can render experiments, but high-quality song localization still needs better phrase alignment, corrected note/phoneme timing, and a stricter lyric intelligibility gate.
