# Music generation update: 2026-09-13

## Recommendation

There are worthwhile updates since the July Luoshenfu research. First compare
the existing ACE production baseline against current ACE with corrected SFT
defaults. Then audition MiniMax Music 3 for complete-song quality and YuE2 for
composition control. Keep the successful ACE XL Turbo workflow as the reference
until a challenger wins a full-song listening comparison.

This is the pre-update research snapshot. The subsequent
[MiniMax installation and Aya Chan production record](minimax-music3-setup-and-ayachan-2026-09-13.md)
documents the actual upgrades, verified downloads and generated comparison audio.
During this initial source and local-installation review, no model weights were downloaded,
no environment or generation code was updated, and no new audio was generated.
New-model quality below means a reason to test, not a Musia listening verdict.

## Installation Before The Update

The standard local ACE checkout is `third_party/ACE-Step-1.5`:

| Component | Local evidence | Upstream check |
| --- | --- | --- |
| ACE source | `6d467e4b5081ccb0abf1ec1bf4fdf9051a2d34b0`, committed 2026-06-26 | `ca1e85fe9430179831e6bc6be790c332190a3866`, committed 2026-08-29; 15 commits ahead |
| XL Turbo | Download metadata revision `d4a0b288b83ebb7e25a8c0b32c573c22e134e8ee` | Same official model revision |
| XL SFT | Download metadata revision `d06de46b4622f781cf07f4a013a67d591ca52819` | Same official model revision |
| Planning LM | `acestep-5Hz-lm-1.7B` exists in the standard checkpoint directory | Official 4B planner is available; it is not in that directory |

The checkpoint comparison used local Hugging Face download metadata and live
official repository metadata. It was not a fresh hash scan of every large tensor
file. No official ACE XXL/XXXL or successor generation checkpoint was found in the
ACE-Step model listing. Diffusers-format checkpoints are packaging alternatives,
not evidence of newly trained weights.

Sources: [exact ACE source comparison](https://github.com/ace-step/ACE-Step-1.5/compare/6d467e4b5081ccb0abf1ec1bf4fdf9051a2d34b0...ca1e85fe9430179831e6bc6be790c332190a3866),
[official model inventory](https://huggingface.co/api/models?author=ACE-Step&limit=100&full=true),
[XL Turbo model card](https://huggingface.co/ACE-Step/acestep-v15-xl-turbo).

Local production evidence is in
[the Luoshenfu production record](luoshenfu-original-excerpt-preview-production-2026-07-29.md).
It records XL Turbo, ten candidates including SFT comparisons, and the later V2
pronunciation correction. The July evidence supports Turbo as our baseline; it
does not establish that every SFT implementation or future model is inferior.

The July research note described ACE as Apache 2.0. The current official ACE
repository and XL Turbo model card identify MIT. Preserve precise code and model
license identities in future installation records.

## ACE: the most immediate improvement to test

[PR 1273](https://github.com/ace-step/ACE-Step-1.5/pull/1273), merged August 16,
changes the default for the optional DCW sampler correction: enabled for Turbo,
disabled for non-Turbo models, unless explicitly overridden. The fix targets
distorted/noisy Base and SFT output. The initiating
[issue 1259](https://github.com/ace-step/ACE-Step-1.5/issues/1259) was observed on
Apple Silicon, while the merged default-resolution change covers shared generation
entry points.

The pre-update checkout declared `dcw_enabled: bool = True` in:

- `third_party/ACE-Step-1.5/acestep/inference.py:148`
- `third_party/ACE-Step-1.5/acestep/core/generation/handler/service_generate.py:54`
- `third_party/ACE-Step-1.5/acestep/core/generation/handler/service_generate_execute.py:83`

Inference: this is a plausible contributor to our earlier SFT failures, worth a
controlled NVIDIA test. It is not a proven retrospective explanation. Compare
identical SFT weights, input, seed and settings with DCW explicitly off before
concluding that the model itself cannot sing well. Keep the successful Turbo
configuration as the listening control.

Also relevant:

- [PR 1284](https://github.com/ace-step/ACE-Step-1.5/pull/1284) adds optional loading
  of a requested model rather than silently choosing the primary model. The flag
  is opt-in and some failures still fall back. Musia must verify the actual loaded
  model for every benchmark, not just the requested model name.
- [PR 1305](https://github.com/ace-step/ACE-Step-1.5/pull/1305) prevents cover-only
  settings from affecting other tasks.
- The source comparison also includes seed handling, memory preflight and KV-cache
  fixes. These improve reliability; they do not prove better melodies.

The 4B planning LM is another optional A/B axis after the code comparison. Change
one variable at a time so a planner change cannot be confused with a sampler fix.

## New models worth auditioning

### MiniMax Music 3: complete-song production

Released August 13, after our previous research. Official weights and inference
implementations are available. Its emphasis on evolving arrangements and expressive
vocals makes it a strong candidate for our female ballads and mixed-language pop.
That priority is an engineering judgment, not a local quality result.
[Official launch](https://www.minimax.io/blog/minimax-music-3-0-next-generation-open-weights-production-ready-versatile-music-model).

It combines an 8B global language model, a smaller local model and a flow-based
audio renderer. Lyrics and musical direction are separate inputs. Its documented
caption format describes global musical attributes, vocal delivery and arrangement
development. Use this model-specific format instead of assuming ACE's compact
caption is optimal for every backend.
[Official repository](https://github.com/MiniMax-AI/MiniMax-Music3).

The current Diffusers implementation documents roughly 23 GB BF16 VRAM, with
offloading options. It exposes native 44.1 kHz stereo; the reference server
resamples to 32 kHz. Preserve the implementation's actual sample rate. Section
tags must occupy their own lines: text following a leading tag on the same line
can be discarded. Requested duration is an upper bound, not guaranteed coverage.
[Diffusers implementation guide](https://huggingface.co/docs/diffusers/main/en/api/pipelines/minimax_music3).

There is useful counterevidence: a listener reported that the Chinese demo
omitted four final phrases and substituted two others, while praising its sound.
Another reported garbled output in a particular Windows/5090 environment. These
are individual reports, not established failure rates, but they directly reinforce
our need to audit complete vocals and endings.
[Chinese lyric omissions](https://huggingface.co/MiniMaxAI/MiniMax-Music3/discussions/15),
[runtime report](https://huggingface.co/MiniMaxAI/MiniMax-Music3/discussions/21).

Publication terms need resolving before adopting it for Shipinhao Music. The model's
Community License includes commercial-product attribution, a revenue threshold,
public AI disclosure and service obligations. Comfy's September 1 guidance says
local commercial work requires a commercial license. These documents do not give
a sufficiently unambiguous permission conclusion for our use. Keep the exact
downloaded license and obtain clarification or the appropriate commercial coverage
before commercial deployment; private auditioning can be considered separately.
[Model license](https://huggingface.co/MiniMaxAI/MiniMax-Music3/blob/main/LICENSE),
[current Comfy guidance](https://support.comfy.org/articles/6065098425-minimax-commercial-licensing-who-needs-a-license-and-how-to-get-one).

### YuE2: inspectable composition and companion versions

The official model repository was created September 9, with community release
activity September 10. It supports editable ABC melody/chord plans, full songs and
score-conditioned reinterpretation. This closely matches our master-companion
idea. Official requirements include a 24 GB GPU, and output is 48 kHz stereo.
[Model and runtime](https://huggingface.co/m-a-p/YuE2-3B).

Its September 12 author-run benchmark is promising, but compare protocols:
best-of-eight selection is not one-shot performance. The model card reports
phoneme error rates of 8.44% for standard YuE2 and 9.79% for best-of-eight, versus
7.46% for its ACE baseline. Higher musicality does not guarantee better lyrics;
the table also does not establish parity with our exact local ACE configuration.
These are automatic author-reported results, not an independent human ranking.
[Evaluation protocol](https://huggingface.co/m-a-p/YuE2-3B#benchmarks).

The repository now supplies explicit planning, semantic generation, synthesis and
decoding stages. A future Musia adapter can retain the plan as an artifact, review
it, then feed the edited plan into audio rendering. The original YuE implementation
is preserved on the upstream `YuE-v1` branch, so do not blindly pull current `main`
into Musia's existing YuE-v1 installation.
[Official code and generation workflow](https://github.com/multimodal-art-projection/YuE).

Early user testing reports that BPM and harmonic input guide rather than rigidly
lock the performance. This is preliminary evidence, but means Atlas must still
analyze the actual rendered audio. Japanese appears in the public demo language
selection according to the language discussion; native Japanese and mixed EN/JA/ZH
quality remain unverified here.
[Score-control report](https://huggingface.co/m-a-p/YuE2-3B/discussions/8),
[language discussion](https://huggingface.co/m-a-p/YuE2-3B/discussions/7).

Code is Apache 2.0, but model weights are CC BY-NC 4.0. The public question about
monetizing generated music had no maintainer clarification in the retrieved
discussion. Treat it as a private noncommercial research candidate for now, without
assuming the code license authorizes our commercial generation workflow.
[Model license](https://huggingface.co/m-a-p/YuE2-3B/blob/main/LICENSE),
[output-use question](https://huggingface.co/m-a-p/YuE2-3B/discussions/5).

### SheetSage2: potentially valuable for Atlas

This companion release extracts melody, chords, beats, key and structure. It
exports ABC, separate vocal/instrumental melody MIDI, chord MIDI and timed events.
That is a better-shaped candidate interface for Atlas than pitch contours alone.
Its reported benchmarks are task-dependent, not perfect. Cross-check transcription
against audible notes, existing pitch tracking and beat/chord analysis before
teaching it to a learner. Its weights also carry CC BY-NC 4.0.
[Official model and examples](https://huggingface.co/m-a-p/SheetSage2).

### Stable Audio 3: instrumentals and score textures

Small and Medium weights are available, with variable-duration generation,
continuation and editing. The documented interface centers on audio descriptions;
there is no equivalent evidence here for strict EN/JA/ZH sung-lyric control. My
recommended role is instrumental music, sound design and MV scoring experiments.
Access requires accepting the model's terms.
[Model card](https://huggingface.co/stabilityai/stable-audio-3-medium),
[official library](https://github.com/Stability-AI/stable-audio-3).

HeartMuLa's official inventory still has 3B-family checkpoints and no released 7B
checkpoint. The Qwen official model search returned no Music-named checkpoint.
Do not confuse the Qwen-Music paper or unrelated third-party uploads with an
official runnable release. Earlier LeVo/HeartMuLa comparisons remain recorded in
[the July study](luoshenfu-frontier-model-research-2026-07-29.md).
[HeartMuLa inventory](https://huggingface.co/api/models?author=HeartMuLa&limit=100&full=true),
[Qwen Music search](https://huggingface.co/api/models?author=Qwen&search=music&limit=100).

## Useful community engineering

[audio.cpp](https://github.com/0xShug0/audio.cpp) supports ACE and MiniMax Music 3,
with YuE2 on its development branch at the time checked. It could simplify runtime
management. Its author provides concrete quantization/speed measurements, but those
are not evidence of improved musical quality or of parity on our computer. Start
quality comparisons from the official full-precision implementation and compare
alternative runtimes afterward.
[MiniMax measurements](https://huggingface.co/MiniMaxAI/MiniMax-Music3/discussions/24),
[YuE2 measurements](https://huggingface.co/m-a-p/YuE2-3B/discussions/3).

[ComfyUI MiniMax Music Production Toolkit](https://github.com/jplenio/ComfyUI-MiniMax-Music-Production-Toolkit)
packages prompt preparation, export and audio processing. Its arrangement workflow
is worth reviewing. Enhancement/mastering should be auditioned at matched loudness;
it cannot repair a missing lyric or guarantee a better melody.

## Proposed Musia comparison

This is the next experiment, not work already executed:

1. Freeze three familiar briefs: Luoshenfu V2 for classical Chinese, Aya Chan
   Hikari Ame for Japanese, and Best Am I for mixed-language pop. Preserve the
   exact old inputs and selected audio as references.
2. Run current ACE Turbo and SFT comparisons with actual loaded-model identity
   recorded. Use the corrected SFT defaults. Initially keep planner, lyrics,
   seeds and durations fixed; test the 4B planner separately.
3. Use the same artistic intent for MiniMax and YuE2, adapted to each model's
   documented input contract. Start with four candidates per route, expand to
   eight only for promising routes. Report yield and listening results, not just
   the strongest ten seconds from the best candidate.
4. Retain raw masters and loudness-matched audition copies. Check audio health,
   vocal presence, first entrance, phrase transitions and the entire ending.
5. Separate vocals; run large ASR and independent MOSS/HeartTranscriptor evidence.
   Account for every planned line, including repeated and soft final phrases.
   Preserve beautiful source wording when the sound and syllable count are close.
6. Choose primarily by melody, expressive singing, coherence and replay value.
   Treat ASR as evidence, not an aesthetic score. Distinguish runtime corruption
   from a disappointing composition before changing the model or prompt.
7. For score-driven tests, compare the intended ABC with the actual audio before
   using notes or chord timing in Atlas. A generated plan is not a transcript.
8. Promote only reviewed, appropriately licensed results to Preview, followed by
   corrected per-vocal multilingual lyrics, timing, ruby and the usual website
   checks. No automatic public release of research-only candidates.

Read-only hardware check found two RTX 4090 D GPUs, each about 24 GB, and 125 GiB
host RAM with about 67 GiB available. These are individual GPUs, not one pooled
48 GB device. Official single-24-GB routes look feasible, subject to actual runtime
validation. Before any future generation, repeat RAM, GPU, project-process, tmux
and port checks; run one Musia model-generation job at a time and reuse verified
weights. Preserve `musia` as the normal entry point and isolate only genuinely
incompatible backend dependencies.

## Revisions observed

These identify what was checked, not an installed upgrade:

| Artifact | Revision |
| --- | --- |
| ACE upstream source | `ca1e85fe9430179831e6bc6be790c332190a3866` |
| MiniMax Music 3 HF | `fbdf52fbaaca799592917417eb05f1899f1255ec` |
| YuE2-3B HF | `29b3558dd46954a0cd9021dc76d5c91864a0f1c7` |
| HeartMuLa HNY HF | `41f6fc68490e11dc43fdabaa6b5767946408c903` |

Dates and inventories came from the live GitHub/Hugging Face APIs; technical claims
were checked against official cards, code, documentation and identifiable
first-hand community reports. Search-engine relative dates were not used as release
dates. Sources can change after this review. No new-model listening test was
performed in this research turn.
