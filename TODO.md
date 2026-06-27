# Musai TODO

## Done in this local scaffold

- [x] Create local project structure.
- [x] Add conda bootstrap installer.
- [x] Add open/free song downloader.
- [x] Add song analysis pipeline.
- [x] Add beat and chord extraction baseline.
- [x] Add Demucs stem separation hook.
- [x] Add ASR hook through `faster-whisper`.
- [x] Add optional OpenAI lyric adaptation helper.
- [x] Add research repository downloader.
- [x] Add git ignore rules for generated audio, weights, and secrets.
- [x] Create and verify `musai` conda environment.
- [x] Download a Wikimedia Commons test recording.
- [x] Run a local smoke test that produced stems, beats, chords, and lyrics.
- [x] Shallow-clone research source repositories into `third_party/`.

## Register / configure later

- [ ] Add `OPENAI_API_KEY` to `.env` if lyric adaptation should call OpenAI.
- [ ] Create a Hugging Face account/token if gated singing model weights require it.
- [ ] Download/check singing model weights after license review.
- [ ] Check model licenses before commercial use: YingMusic-Singer-Plus, SoulX-Singer, RVC, GPT-SoVITS, ACE-Step, YuE.
- [ ] Decide whether voice cloning is allowed in v1. Recommended: only user-consented or licensed voices.
- [ ] Choose S3-compatible storage for generated stems and mixes.
- [ ] Add PostgreSQL and Redis when the FastAPI backend starts.
- [ ] Add rights/ownership confirmation to the future upload UI.

## Next engineering steps

- [ ] Replace the baseline chord detector with a stronger chord-recognition model or plugin.
- [ ] Add phrase-level lyric segmentation from ASR timestamps.
- [ ] Add `Musai LyricFit` deterministic scoring for syllable count, rhyme, and tone-melody fit.
- [ ] Integrate Basic Pitch or another note extractor for melody skeleton output.
- [ ] Add YingMusic-Singer-Plus in an isolated GPU worker.
- [ ] Add SoulX-Singer as a second singing synthesis backend.
- [ ] Add a FastAPI job API and RQ/Redis worker.
- [ ] Add a Next.js + wavesurfer.js player/editor.
- [ ] Add provenance metadata and private-by-default project permissions.

## Local-first test target

The current smoke test should produce:

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
- `REPORT.md`
- `manifest.json`
