# High-Quality Vocal Backends

Goal: improve Musai vocal quality beyond the current YingMusic proof-of-concept.

Checked: 2026-06-27.

For the broader EN/ZH/JP repo map, including Chinese-company models and Microsoft Muzic, see `references/en-zh-jp-music-model-repos.md`.

## Best Strict Localization Route

For the highest-quality "same song, new language" output:

1. Extract original stems with Demucs.
2. Extract/correct the vocal melody as MIDI/F0.
3. Use a professional singing synth for Mandarin vocals.
4. Mix the rendered Mandarin vocal with original `bass`, `drums`, and `other`.

Best production tools:

- Synthesizer V Studio 2 Pro: professional singing synth, Mandarin/Cantonese support, paid/trial.
- ACE Studio: MIDI + lyrics to studio-quality AI vocals, Windows/macOS desktop app, paid/free entry points.

Strict localization needs MIDI/F0 plus phrase-level Chinese lyrics. Full-song generators can sound better than a bad singing-synthesis attempt, but they usually change arrangement, timing, or melody, so they should not be treated as the main Musai path.

## Best Open-Source / Local Candidates

- SoulX-Singer: best next strict localization backend to test. Supports F0/MIDI-conditioned high-quality zero-shot singing and SVC.
- YingMusic-Singer-Plus: closest open-source model to lyric replacement with melody guidance; still needs more setup/testing for production quality.
- ACE-Step 1.5: best local full-song/new-song generator. Good for "inspired Chinese version", not exact original stems.
- YuE: high-quality lyrics-to-song model, strong for full songs but heavy on 24 GB GPUs.
- HeartMuLa: 2026 open-source full-song generator with released 3B checkpoints and HeartCodec; useful for Chinese full-song alternatives.
- FunMusic / InspireMusic: Alibaba/Tongyi long-form music/song/audio generation stack; useful for Chinese-company model comparison.
- Microsoft Muzic: symbolic music understanding/generation and lyric-melody constraint research; useful for planning and scoring, not final audio.
- Tencent MuQ: music understanding and music-text embedding model; useful for scoring/search and English/Chinese text-music alignment.
- DiffRhythm: fast full-song generation; useful for experiments, not strict stem-preserving localization.
- SongGen: text-to-song research model with optional reference voice; useful for short tests.
- MOSS-Music: music understanding model for lyrics ASR, chord/key/tempo reasoning, timestamped chord transcription, and structure analysis.

## Downloaded / Staged Locally

The repo downloader covers:

- SoulX-Singer code and model weights.
- SoulX-Singer preprocessing models.
- ACE-Step 1.5 code and models via the project downloader.
- DiffRhythm v1.2 full and VAE checkpoints.
- SongGen mixed and dual-track checkpoints plus X-Codec.
- YuE minimal local set: XCodec mini, 7B stage-1 Chinese CoT model, 1B stage-2 general model.
- HeartMuLa model config, HeartMuLa 3B checkpoint, and HeartCodec checkpoint.
- MOSS-Music 8B Instruct and Thinking checkpoints.

Commercial/trial tools are not downloaded through unofficial mirrors. Their official links are saved in `downloads/pro-vocal-tools/OFFICIAL_TRIAL_AND_PAID_LINKS.md`.

## Local Download Script

Use:

```bash
bash scripts/download_quality_backends.sh core
```

For all staged research models:

```bash
bash scripts/download_quality_backends.sh all
```

For heavier YuE models only:

```bash
bash scripts/download_quality_backends.sh yue-minimal
```

All new Hugging Face downloads are directed to `.cache/huggingface` inside this repo to avoid filling `/home`.

## Local Env Installer

Use isolated environments, not the main `musai` or `lazyedit` env:

```bash
bash scripts/install_quality_envs.sh soulx
bash scripts/install_quality_envs.sh ace-step
bash scripts/install_quality_envs.sh songgen
bash scripts/install_quality_envs.sh diffrhythm
bash scripts/install_quality_envs.sh heartmula
bash scripts/install_quality_envs.sh moss-music
```

The envs live in `.conda/` under this repo and pip cache lives in `.cache/pip`.

MOSS-Music needs its conda FFmpeg, PyTorch, TorchCodec, and NVIDIA library paths together. Run it through:

```bash
bash scripts/run_moss_music_env.sh .conda/moss-music/bin/python -c "import torchcodec; print('torchcodec ok')"
```

SoulX-Singer is a cloned repo rather than an installed Python package. The installer writes a `.pth` entry into `.conda/soulxsinger`; the wrapper also sets `PYTHONPATH`:

```bash
bash scripts/run_soulx_env.sh .conda/soulxsinger/bin/python -c "import soulxsinger; print('soulx ok')"
```

## Practical Quality Order

1. **Best possible vocal quality:** Synthesizer V Studio 2 Pro or ACE Studio with hand-corrected MIDI and Chinese lyrics.
2. **Best local strict-localization test:** SoulX-Singer with corrected MIDI/metadata, then mix with Demucs `bass`, `drums`, `other`.
3. **Best local full-song alternative:** ACE-Step 1.5 XL or YuE when exact original arrangement is less important.
4. **Best local analysis assistant:** MOSS-Music for chord/key/tempo/lyrics understanding and QA.
5. **Research comparison:** HeartMuLa, DiffRhythm, and SongGen.

## Official Sources

- SoulX-Singer: https://github.com/Soul-AILab/SoulX-Singer
- YingMusic-Singer-Plus: https://github.com/ASLP-lab/YingMusic-Singer
- ACE-Step 1.5: https://github.com/ace-step/ACE-Step-1.5
- DiffRhythm: https://github.com/ASLP-lab/DiffRhythm
- SongGen: https://github.com/LiuZH-19/SongGen
- YuE: https://github.com/multimodal-art-projection/YuE
- HeartMuLa: https://github.com/HeartMuLa/heartlib
- MOSS-Music: https://github.com/OpenMOSS/MOSS-Music
- FunMusic / InspireMusic: https://github.com/FunAudioLLM/FunMusic
- Microsoft Muzic: https://github.com/microsoft/muzic
- MuQ: https://github.com/tencent-ailab/MuQ
- MuCodec: https://github.com/tencent-ailab/MuCodec
- Synthesizer V free trial: https://dreamtonics.com/download-free-trials/
- ACE Studio download: https://acestudio.ai/download/
