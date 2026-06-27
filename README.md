# Musai

Musai is an AI song-localization prototype. The local MVP takes a song file and produces analysis artifacts:

- vocal, drums, bass, and other stems through Demucs when available
- an instrumental mix and a `human_sound.wav` vocal alias
- lyrics/transcription output when ASR is available, or a supplied lyric reference
- beat grid and tempo estimate
- simple Chordify-style chord segments
- a run manifest and Markdown report

The larger product direction is documented in `references/`.

## Local Quick Start

```bash
bash scripts/bootstrap_musai.sh
PYTHONNOUSERSITE=1 conda run -n musai python scripts/download_open_songs.py --id danny-boy-1917
PYTHONNOUSERSITE=1 conda run -n musai python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny --max-duration 45 --asr-model tiny
```

Results are written to:

```text
data/runs/<run-name>/
```

## Core Pipeline

```text
song input
-> optional trim/transcode
-> Demucs 4-stem separation
-> vocals/human sound extraction
-> instrumental mix
-> ASR or reference lyrics
-> beat tracking
-> chord estimation
-> manifest + report
```

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/bootstrap_musai.sh` | Create/install the `musai` conda env. |
| `scripts/download_open_songs.py` | Download test songs from free/open sources. |
| `scripts/run_pipeline.py` | Run the local analysis pipeline on one song. |
| `scripts/test_local_pipeline.sh` | Download a sample and run a smoke test. |
| `scripts/install_research_repos.sh` | Shallow-clone optional research repositories into `third_party/`. |
| `scripts/musai_lyricfit_openai.py` | Optional OpenAI-powered lyric adaptation helper. |

## Notes

The chord detector is a lightweight local baseline, not a replacement for a production Chordify-grade model. It is good enough for an MVP artifact and regression tests.

Full singing synthesis with YingMusic-Singer-Plus or SoulX-Singer is staged as a research integration because those projects have larger model-weight and environment requirements.
