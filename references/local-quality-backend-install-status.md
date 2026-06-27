# Local Quality Backend Install Status

Checked: 2026-06-27.

This file records the repo-local state for the high-quality Musai backends. Model weights, cloned research repositories, conda environments, and caches are ignored by git.

## Verified Environments

| Backend | Env path | Status |
| --- | --- | --- |
| SoulX-Singer | `.conda/soulxsinger` | Verified import stack with CUDA on NVIDIA GeForce RTX 4090 D through `scripts/run_soulx_env.sh`. |
| ACE-Step 1.5 | `third_party/ACE-Step-1.5/.venv` | Verified `torch 2.10.0+cu128`, CUDA, and `acestep` import. |
| SongGen | `.conda/songgen` | Verified `torch 2.3.0+cu118`, `flash_attn 2.6.1`, and `songgen 0.1`. |
| DiffRhythm | `.conda/diffrhythm` | Verified `torch 2.6.0+cu124`, CUDA, torchaudio, librosa, and phonemizer. |
| HeartMuLa | `.conda/heartmula` | Verified `torch 2.10.0+cu128`, CUDA, and `heartlib` import. |
| MOSS-Music | `.conda/moss-music` | Verified `torch 2.9.1+cu128`, CUDA, and `torchcodec 0.9.1+cu128` through `scripts/run_moss_music_env.sh`. |

## Local Model Inventory

| Backend | Local path | Size |
| --- | --- | --- |
| SoulX-Singer | `third_party/SoulX-Singer/pretrained_models` | 12G |
| ACE-Step 1.5 | `third_party/ACE-Step-1.5/checkpoints` | 28G |
| SongGen checkpoints | `third_party/SongGen/checkpoints` | 11G |
| SongGen XCodec | `third_party/SongGen/songgen/xcodec_wrapper/xcodec_infer/ckpts/general_more` | 3.4G |
| YuE checkpoints | `third_party/YuE/checkpoints` | 16G |
| YuE XCodec | `third_party/YuE/inference/xcodec_mini_infer` | 1.8G |
| DiffRhythm | `third_party/DiffRhythm/checkpoints` | 3.3G |
| HeartMuLa | `third_party/HeartMuLa/ckpt` | 21G |
| MOSS-Music | `third_party/MOSS-Music/weights` | 34G |

## Expanded Code-Only Repo Inventory

Checked: 2026-06-28. These are shallow code clones under ignored `third_party/`; they do not include large model weights unless a repository itself vendors small assets.

| Repo | Local path | Size |
| --- | --- | --- |
| Microsoft Muzic | `third_party/Muzic` | 354M |
| Alibaba FunMusic / InspireMusic | `third_party/FunMusic` | 6.7M |
| Tencent MuQ | `third_party/MuQ` | 1.9M |
| Tencent MuCodec | `third_party/MuCodec` | 226M |
| MERT | `third_party/MERT` | 544K |
| OpenVPI DiffSinger | `third_party/OpenVPI-DiffSinger` | 5.7M |
| NNSVS | `third_party/NNSVS` | 31M |
| OpenUtau | `third_party/OpenUtau` | 95M |
| AudioCraft | `third_party/AudioCraft` | 22M |
| Stable Audio Tools | `third_party/stable-audio-tools` | 2.7M |
| Magenta | `third_party/Magenta` | 45M |
| YingMusic-Singer-Plus | `third_party/YingMusic-Singer-Plus` | 229M |

## Local Env Sizes

| Path | Size |
| --- | --- |
| `.conda/soulxsinger` | 6.4G |
| `third_party/ACE-Step-1.5/.venv` | 7.6G |
| `.conda/songgen` | 6.9G |
| `.conda/diffrhythm` | 6.6G |
| `.conda/heartmula` | 7.9G |
| `.conda/moss-music` | 8.4G |
| `.cache/pip` | 15G |

## Official Desktop Trial Installers

Official Windows/macOS installers are staged in `downloads/pro-vocal-tools/` for manual use on compatible systems:

| Tool | File |
| --- | --- |
| ACE Studio | `ACE_Studio_Installer_2.0.0_33_x64.exe` |
| Synthesizer V Studio 2 Pro | `svstudio2-pro-setup-latest.exe` |
| Synthesizer V Studio 2 Pro | `svstudio2-pro-setup-latest.pkg` |

The installer binaries are ignored by git. The official links file is committed.

## Run Helpers

```bash
bash scripts/download_quality_backends.sh all
bash scripts/install_quality_envs.sh all
bash scripts/run_soulx_env.sh .conda/soulxsinger/bin/python -c "import soulxsinger; print('soulx ok')"
bash scripts/run_moss_music_env.sh .conda/moss-music/bin/python -c "import torchcodec; print('torchcodec ok')"
```

## Production Next Step

The local machine now has the model assets and Python environments needed to test better generation. The next work is integration, not more downloading:

1. Prepare phrase-timed Mandarin lyrics with corrected syllable counts.
2. Convert extracted vocal melody to clean MIDI/F0.
3. Run a 20-40 second SoulX-Singer or professional-synth vocal render.
4. Mix that Mandarin vocal with the original `bass`, `drums`, and `other` stems.
5. Accept a render only if the vocal is clearly sung, audible, natural Chinese, and rhythmically aligned.
