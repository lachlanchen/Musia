# EN/ZH/JP Music Model Repos

Checked: 2026-06-28.

Goal: identify strong GitHub/open-source candidates for Musai's core promise: beautiful music generation and music localization across English, Chinese, and Japanese.

## Practical Ranking For Musai

| Rank | Repo / Tool | Best Musai Use | Notes |
| --- | --- | --- | --- |
| 1 | SoulX-Singer | Same-melody singing synthesis, mainly Mandarin/English/Cantonese | Best local strict-localization candidate when MIDI/F0 and lyric metadata are ready. |
| 2 | YingMusic-Singer-Plus | Lyric manipulation and CN/EN singing edit | Closest open-source direction for changing lyrics while preserving melody guidance. |
| 3 | ACE-Step 1.5 | Beautiful full-song alternative and fast experiments | Strong local generator; treat outputs as reinterpretations unless arrangement is preserved. |
| 4 | YuE | Lyrics-to-full-song generation | Strong long-form lyrics-to-song model; useful for Chinese/English full songs and references. |
| 5 | HeartMuLa | Multilingual full-song alternatives | Useful for EN/ZH/JP/KR/ES experiments and ComfyUI workflows. |
| 6 | SongGeneration / LeVo 2 | Watchlist for commercial-grade full-song generation | Public GitHub page/search cache exists, but `git clone` and `gh api` returned 404 from this machine on 2026-06-28. Do not automate until a cloneable URL is confirmed. |
| 7 | FunMusic / InspireMusic | Alibaba/Tongyi long-form text-to-music and continuation | Good Chinese-company research stack; currently strongest for music generation/continuation, with song generation models listed. |
| 8 | DiffRhythm | Fast full-song generation baseline | Good for quick comparison, less strict for original-song localization. |
| 9 | SongGen | Text-to-song research baseline | Useful for comparative experiments, especially short prompt/lyrics tests. |
| 10 | MOSS-Music | Music understanding and QA | Use for lyrics ASR, structure, chord/key/tempo reasoning, and render QA. |

## Chinese / China-Linked Company And Lab Repos

| Repo | Organization | Role | Why It Matters |
| --- | --- | --- | --- |
| `FunAudioLLM/FunMusic` | Alibaba Tongyi / FunAudioLLM | InspireMusic toolkit for music/song/audio generation | Long-form, high-quality text-to-music and continuation; repo says it is built around autoregressive transformer plus flow matching and Qwen2.5-style backbone. |
| `tencent-ailab/MuQ` | Tencent AI Lab | Music understanding representation | MuQ and MuQ-MuLan are useful for music-text retrieval, tagging, QA, and style/quality scoring; MuQ-MuLan supports English and Chinese text. |
| `tencent-ailab/MuCodec` | Tencent AI Lab | Music codec | Useful as a research codec reference for high-fidelity reconstruction/tokenization, not a direct Musai product backend. |
| `tencent-ailab/SongGeneration` | Tencent AI Lab | LeVo / SongGeneration | Public page says LeVo 2 supports multilingual lyrics including zh/en/ja, separate vocal/accompaniment generation, and 4m30s songs, but clone/API were unavailable locally. |
| `open-mmlab/Amphion` | OpenMMLab | Audio/music/speech generation toolkit | Good research framework for SVS, TTS, VC, vocoders, and evaluation. |
| `ASLP-lab/DiffRhythm` | ASLP Lab | Fast full-song generation | Chinese-named DiffRhythm/谛韵, open diffusion-based song generation. |
| `ASLP-lab/YingMusic-Singer-Plus` | ASLP Lab | Controllable singing voice synthesis/editing | High relevance for lyric manipulation and melody-guided singing. |
| `OpenMOSS/MOSS-Music` | OpenMOSS / MOSI.AI / Shanghai Innovation Institute | Music understanding | Directly targets lyrics ASR, captioning, structure, chord/key/tempo reasoning, and music QA. |
| `HeartMuLa/heartlib` | HeartMuLa | Full-song generation | Useful multilingual full-song model family with EN/ZH/JP support in community workflows. |
| `RVC-Project/Retrieval-based-Voice-Conversion-WebUI` | RVC ecosystem | Singing voice conversion | Useful only after a good sung vocal exists; not a lyric-changing singer by itself. |
| `RVC-Boss/GPT-SoVITS` | RVC ecosystem | Voice cloning/TTS | Useful for speech/voice references and timbre experiments, not final singing localization by itself. |

## Microsoft Muzic

`microsoft/muzic` is still worth cloning. It is not a modern full-song audio generator, but it contains valuable symbolic music and lyric-melody work:

- MusicBERT: symbolic music understanding.
- MuseCoco: text-to-symbolic-music generation through musical attributes.
- ReLyMe: lyric-to-melody constraints, tested on English and Chinese song datasets.
- SongMASS / TeleMelody / DeepRapper: useful older generation baselines.
- MusicAgent: useful architecture reference for an agentic music toolchain.

For Musai, Muzic is most useful for **planning and constraint checking**, not final audio rendering.

## Japanese-Focused And JP-Compatible Stack

| Repo / Tool | Role | Notes |
| --- | --- | --- |
| `openutau/OpenUtau` | Open singing synthesis platform | Best open editor/front-end ecosystem for Japanese voicebank workflows. |
| `nnsvs/nnsvs` | Neural singing synthesis toolkit | Research-friendly; NNSVS has been used for multiple languages and is strong for Japanese SVS workflows. |
| `openvpi/DiffSinger` | Advanced DiffSinger implementation | Better maintained practical SVS stack than the original academic repo for some workflows. |
| `MoonInTheRiver/DiffSinger` | Original DiffSinger code | Good baseline and paper reference. |
| `ACE-Step-1.5`, `YuE`, `HeartMuLa`, `SongGeneration-v2` | Full-song multilingual generation | Use for Japanese full-song inspiration, not strict same-arrangement localization. |

## General Global Repos Still Worth Keeping

| Repo | Use |
| --- | --- |
| `facebookresearch/audiocraft` | MusicGen / AudioCraft for controllable instrumental or melody-conditioned music generation. |
| `Stability-AI/stable-audio-tools` | Conditional audio generation and reference implementation for high-quality audio diffusion. |
| `magenta/magenta` | Older but useful symbolic music generation and prototyping tools. |
| `yizhilll/MERT` | Acoustic music understanding model for embeddings and downstream scoring. |

## What To Download Automatically

Safe to clone as code only:

```bash
bash scripts/download_quality_backends.sh expanded-repos
```

Do not automatically download every weight. Some models are tens of GB, some licenses need manual review, and some links move quickly. Keep weights under ignored folders such as `third_party/`, `.cache/`, or model-specific ignored paths.

## Product Direction

For "beautiful music", use two tracks:

1. **Strict localization track:** Demucs stems -> corrected MIDI/F0 -> singable EN/ZH/JP lyrics -> SoulX/YingMusic/pro synth vocal -> mix with `bass + drums + other`.
2. **Beautiful reinterpretation track:** Adapted lyrics + style prompt -> ACE-Step/YuE/HeartMuLa/FunMusic/SongGeneration -> clearly label as a new/inspired version unless it preserves the original arrangement.

The strict localization track is the Musai differentiator. The full-song models are valuable for quality targets, demos, and alternate creative versions.

## Official Links

- SoulX-Singer: https://github.com/Soul-AILab/SoulX-Singer
- YingMusic-Singer-Plus: https://github.com/ASLP-lab/YingMusic-Singer-Plus
- ACE-Step 1.5: https://github.com/ace-step/ACE-Step-1.5
- YuE: https://github.com/multimodal-art-projection/YuE
- HeartMuLa: https://github.com/HeartMuLa/heartlib
- SongGeneration / LeVo: https://github.com/tencent-ailab/SongGeneration
- FunMusic / InspireMusic: https://github.com/FunAudioLLM/FunMusic
- DiffRhythm: https://github.com/ASLP-lab/DiffRhythm
- SongGen: https://github.com/LiuZH-19/SongGen
- MOSS-Music: https://github.com/OpenMOSS/MOSS-Music
- Microsoft Muzic: https://github.com/microsoft/muzic
- MuQ: https://github.com/tencent-ailab/MuQ
- MuCodec: https://github.com/tencent-ailab/MuCodec
- Amphion: https://github.com/open-mmlab/Amphion
- OpenUtau: https://github.com/openutau/OpenUtau
- NNSVS: https://github.com/nnsvs/nnsvs
- OpenVPI DiffSinger: https://github.com/openvpi/DiffSinger
- Original DiffSinger: https://github.com/MoonInTheRiver/DiffSinger
- AudioCraft: https://github.com/facebookresearch/audiocraft
- Stable Audio Tools: https://github.com/Stability-AI/stable-audio-tools
- Magenta: https://github.com/magenta/magenta
- MERT: https://github.com/yizhilll/MERT
