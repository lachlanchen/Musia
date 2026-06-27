# Musai Local Setup and Test Report

Date: 2026-06-27

Machine summary:

- GPU visible: NVIDIA GeForce RTX 4090 D, 24 GB VRAM
- Conda available: yes
- Local env created: `musai`
- PyTorch CUDA check: passed
- Generated audio/data location: `data/runs/`
- Third-party source checkouts: `third_party/`

## Installed Local Core

The `musai` conda environment was created and verified with:

- Python 3.10
- FFmpeg
- PyTorch 2.3.0 + CUDA 12.1
- torchaudio 2.3.0
- Demucs
- faster-whisper
- librosa
- soundfile
- OpenAI Python SDK
- pypinyin
- jieba
- phonemizer
- pedalboard
- pyloudnorm

The local pipeline does not require an API key for stem separation, transcription, beat detection, or chord estimation.

## Downloaded Research Sources

The optional research downloader cloned these source repositories into `third_party/`:

- `demucs`
- `whisperx`
- `RMVPE`
- `basic-pitch`
- `YingMusic-Singer`
- `SoulX-Singer`
- `Amphion`
- `DiffSinger`
- `RVC-WebUI`
- `GPT-SoVITS`
- `ACE-Step-1.5`
- `YuE`

Model weights were not auto-downloaded. Many singing and voice-conversion weights are large, gated, or license-sensitive, so they should be added only after checking each project license and access requirements.

## API / Account Checklist

No account is needed for the current local smoke test.

Needed later:

- `OPENAI_API_KEY`: optional, for `scripts/musai_lyricfit_openai.py` and the future Musai LyricFit engine.
- Hugging Face token: optional, for gated model weights.
- RunPod/Modal/AWS/GCP account: optional, for remote GPU workers.
- S3-compatible storage account: optional, for the future web backend.
- Rights/licensing workflow: required before public user uploads or publishing transformed music.

## Open Test Song Downloader

The test-song downloader is:

```bash
PYTHONNOUSERSITE=1 conda run -n musai python scripts/download_open_songs.py --id danny-boy-1917
```

The default catalog entry downloads a Wikimedia Commons recording:

- Local path: `data/open_songs/danny-boy-1917/original.ogg`
- Source page: <https://commons.wikimedia.org/wiki/File:Schumann-Heink_-_Danny_Boy_(Londonderry_air)_(1917).ogg>

The downloader also has a second Commons test entry:

```bash
PYTHONNOUSERSITE=1 conda run -n musai python scripts/download_open_songs.py --id e-scris-pe-tricolor-vocal
```

Always verify a source page before public or commercial use.

## Smoke Test Run

Command:

```bash
PYTHONNOUSERSITE=1 conda run -n musai python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny-120-fixed --max-duration 120 --asr-model base.en --language en --demucs-device cuda
```

Result:

- Status: passed
- Run folder: `data/runs/smoke-danny-120-fixed/`
- Tempo estimate: 129.20 BPM
- Beat count: 257
- Chord segments: 132
- Lyrics status: `ok`

Generated artifacts:

- `source/input.wav`
- `stems/vocals.wav`
- `stems/drums.wav`
- `stems/bass.wav`
- `stems/other.wav`
- `stems/instrumental.wav`
- `stems/human_sound.wav`
- `analysis/beats.json`
- `analysis/beats.csv`
- `analysis/chords.json`
- `analysis/chords.csv`
- `analysis/lyrics.json`
- `analysis/lyrics.txt`
- `manifest.json`
- `REPORT.md`

Notes:

- `stems/human_sound.wav` is an alias of the isolated vocal stem.
- Chords and beats are estimated from `stems/instrumental.wav` when separation succeeds.
- Lyrics are transcribed from `stems/vocals.wav` when separation succeeds.
- The chord estimator is a lightweight baseline. It should be replaced by a stronger chord-recognition model for production.

