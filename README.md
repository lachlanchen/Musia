[English](README.md) · [العربية](i18n/README.ar.md) · [Español](i18n/README.es.md) · [Français](i18n/README.fr.md) · [日本語](i18n/README.ja.md) · [한국어](i18n/README.ko.md) · [Tiếng Việt](i18n/README.vi.md) · [中文 (简体)](i18n/README.zh-Hans.md) · [中文（繁體）](i18n/README.zh-Hant.md) · [Deutsch](i18n/README.de.md) · [Русский](i18n/README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# Musai

*AI song localization: extract the human voice, stems, lyrics, beats, and chords from a song, then prepare the path toward singable multilingual re-singing.*

[![Website](https://img.shields.io/badge/Website-lazying.art-0EA5E9?style=for-the-badge)](https://lazying.art)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](environment.yml)
[![CUDA](https://img.shields.io/badge/CUDA-tested-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](references/local-setup-and-test-report.md)
[![Sponsor](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)

Musai is a local-first research prototype for AI music localization. The current MVP takes an input song, separates it into the four Demucs stems `bass`, `drums`, `vocals`, and `other`, creates an `instrumental` mix, aliases the vocal as `human_sound`, transcribes lyrics, estimates beats, and produces Chordify-style chord segments.

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## What It Produces

```text
input song
-> source/input.wav
-> stems/bass.wav
-> stems/drums.wav
-> stems/vocals.wav
-> stems/other.wav
-> stems/instrumental.wav
-> stems/human_sound.wav
-> analysis/lyrics.json + lyrics.txt
-> analysis/beats.json + beats.csv
-> analysis/chords.json + chords.csv
-> manifest.json + REPORT.md
```

`instrumental.wav` is mixed from `bass + drums + other`. `human_sound.wav` is the isolated `vocals.wav` stem.

## Current Contents

| Path | Purpose |
| --- | --- |
| [`musai/`](musai/) | Local Python analysis toolkit. |
| [`scripts/bootstrap_musai.sh`](scripts/bootstrap_musai.sh) | Creates the conda environment and installs the local stack. |
| [`scripts/download_open_songs.py`](scripts/download_open_songs.py) | Downloads free/open test songs. |
| [`scripts/run_pipeline.py`](scripts/run_pipeline.py) | Runs separation, transcription, beats, chords, and report generation. |
| [`scripts/install_research_repos.sh`](scripts/install_research_repos.sh) | Shallow-clones optional research repositories into `third_party/`. |
| [`scripts/download_quality_backends.sh`](scripts/download_quality_backends.sh) | Downloads high-quality research backends and model weights into ignored local folders. |
| [`scripts/install_quality_envs.sh`](scripts/install_quality_envs.sh) | Creates isolated repo-local conda/uv environments for large singing and music models. |
| [`scripts/run_soulx_env.sh`](scripts/run_soulx_env.sh) | Runs SoulX-Singer with the cloned repo on `PYTHONPATH`. |
| [`scripts/run_moss_music_env.sh`](scripts/run_moss_music_env.sh) | Runs MOSS-Music with the required FFmpeg, TorchCodec, and CUDA library paths. |
| [`scripts/musai_lyricfit_openai.py`](scripts/musai_lyricfit_openai.py) | Optional OpenAI-powered lyric adaptation helper. |
| [`references/`](references/) | Architecture, deep research, and local setup notes. |
| [`TODO.md`](TODO.md) | Build checklist and next engineering steps. |

## Quick Start

```bash
bash scripts/bootstrap_musai.sh
PYTHONNOUSERSITE=1 conda run -n musai python scripts/download_open_songs.py --id danny-boy-1917
PYTHONNOUSERSITE=1 conda run -n musai python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny --max-duration 45 --asr-model tiny
```

Results are written to:

```text
data/runs/<run-name>/
```

Generated audio, downloaded songs, model weights, and third-party clones are ignored by git.

## Local Validation

The local smoke test on an open Wikimedia Commons recording passed on a machine with an NVIDIA RTX 4090 D:

```bash
PYTHONNOUSERSITE=1 conda run -n musai python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny-120-fixed --max-duration 120 --asr-model base.en --language en --demucs-device cuda
```

Recorded result:

- Four stems: `bass`, `drums`, `vocals`, `other`
- Additional audio: `instrumental`, `human_sound`
- Tempo estimate: `129.20 BPM`
- Beat count: `257`
- Chord segments: `132`
- Lyrics status: `ok`

See [`references/local-setup-and-test-report.md`](references/local-setup-and-test-report.md).

## High-Quality Backends

The local machine has staged heavier research backends for better vocal quality and music understanding:

- Strict song localization: SoulX-Singer and YingMusic-Singer-Plus.
- Full-song alternatives: ACE-Step 1.5, YuE, DiffRhythm, SongGen, HeartMuLa.
- Music understanding and QA: MOSS-Music.

See [`references/high-quality-vocal-backends.md`](references/high-quality-vocal-backends.md) and [`references/local-quality-backend-install-status.md`](references/local-quality-backend-install-status.md).

For the broader EN/ZH/JP model map, including Chinese-company repos and Microsoft Muzic, see [`references/en-zh-jp-music-model-repos.md`](references/en-zh-jp-music-model-repos.md).

## Architecture Direction

Musai is not only translation plus TTS. The intended full pipeline is:

```text
song upload
-> rights / ownership check
-> vocal + instrumental separation
-> lyrics transcription
-> word / phoneme timing
-> melody / pitch extraction
-> singable lyric adaptation
-> AI singing synthesis
-> optional voice/timbre conversion
-> mixing + mastering
-> music-player interface
```

The current repository implements the first local analysis layer. Singing synthesis with YingMusic-Singer-Plus, SoulX-Singer, and related models is staged as a research integration because those models require larger weights, license checks, and separate GPU-worker packaging.

## Citation

If you use Musai in research, cite the repository. GitHub reads [CITATION.cff](CITATION.cff) and shows a **Cite this repository** panel on the repo page.

```bibtex
@software{chen_musai_2026,
  author = {Chen, Lachlan},
  title = {Musai: Local-first AI song localization and music analysis},
  year = {2026},
  url = {https://github.com/lachlanchen/Musai}
}
```

## Status

Musai is early research software. The local pipeline works for testing and artifact generation, but the chord detector is a lightweight baseline and the singable re-singing layer is not production-ready yet. Use songs you own, public-domain songs, licensed songs, or creator-uploaded material.
