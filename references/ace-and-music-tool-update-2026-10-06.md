# ACE and music tools: 2026-10-06

## Result

Requested: write a Japanese song about Aya travelling in Canada and missing
her, pull Musia, and check for better ACE models/tool updates.

`git pull --ff-only --no-rebase` in Musia completed with **Already up to date**.
It discovered the remote tag `musia-review-0.1.1-2`; no source merge was needed.
Pre-existing tracked changes and untracked work were preserved. ACE was fetched
and then pulled with the same fast-forward-only policy, also already current.
Its untracked `instruction.txt` was left intact.

No new model was downloaded, no Python environment was upgraded, and no audio
was generated in this check. Do not describe this as a benchmark or a new-model
quality win. The new lyric/producer packet is
[楓の向こうで · Beyond the Maples](../ideas-and-inspirations/aya-canada-beyond-the-maples/README.md).

## Official ACE comparison

Live Git fetch and Hugging Face API inventory were checked against local
download metadata, not only search-engine snippets or prior notes.

| Component | Installed / local | Latest observed | Outcome |
| --- | --- | --- | --- |
| ACE-Step-1.5 source | `ca1e85fe9430179831e6bc6be790c332190a3866` | Same, dated 2026-08-29 | Current |
| XL Turbo | `d4a0b288b83ebb7e25a8c0b32c573c22e134e8ee` | Same, dated 2026-04-07 | Current revision |
| XL SFT | `d06de46b4622f781cf07f4a013a67d591ca52819` | Same, dated 2026-04-07 | Current revision |
| 4B planning LM | Not in standard ACE checkpoints | `0a3ec94b557aea7d508da38b31cfe7341f6ff737` | Existing optional model, not a new release |

The official organization returned 20 model repositories. No official XXL,
XXXL, or successor generation checkpoint was found. XL diffusers-format
repositories exist but are not evidence of newly trained, better checkpoints.
This checks metadata revision identity, not a fresh byte-by-byte validation of
the multi-gigabyte installed tensors. The installed 1.7B planner is present,
but its subdirectory has no standalone HF download metadata for this comparison.

Sources: [official model inventory](https://huggingface.co/ACE-Step),
[XL Turbo](https://huggingface.co/ACE-Step/acestep-v15-xl-turbo),
[XL SFT](https://huggingface.co/ACE-Step/acestep-v15-xl-sft),
[source history](https://github.com/ace-step/ACE-Step-1.5/commits/main/).

The important model-aware DCW fix is **already installed**, not a new upgrade
today. Unspecified DCW resolves on for Turbo and off for non-Turbo. This makes
SFT worth a controlled re-test, but does not prove our earlier failed SFT songs
would now outperform Turbo. Keep the known good Turbo route as the control.
[Merged fix](https://github.com/ace-step/ACE-Step-1.5/pull/1273).

## Improvement worth an A/B test

**ScragVAE** is a community decoder fine-tune already supported by our ACE
source, but absent from the standard checkpoint directory. Its author reports
better high-frequency reconstruction and transient detail; those are
author-reported audio-fidelity results, not proof of better composition,
Japanese diction, or emotional singing. It changes decoding, not the planned
melody. The published safetensors file is approximately 644 MB and marked MIT.
No download or audition was performed here.

For a later test, retain the official decoder and compare identical DiT latents
through each decoder at matched loudness. Check vocal grain, sibilance, cymbals,
peaks and the complete ending. Merely hearing a brighter render is not enough
to promote it. The upstream integration exposes
`ACESTEP_VAE_CHECKPOINT=scragvae`; leave it unset for our production control.
The current Musia sweep manifest does not fingerprint a custom decoder, so
record decoder identity explicitly before any such experiment or resumption.

Sources: [author's model card](https://huggingface.co/scragnog/Ace-Step-1.5-ScragVAE),
[upstream integration](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/ALT_VAE.md).

The 4B planning LM is another separate experiment. The selected Musia route
deliberately has `thinking=false` and no lyric/caption rewriting. Downloading a
larger planner while continuing to bypass planning would not itself improve
the output. Change only one axis per comparison and check whether the actual
lyric or structure has been changed.

## Other installed tools checked

| Repository | Local commit | Remote main checked | Result |
| --- | --- | --- | --- |
| MiniMax-Music3 | `945655064d59b98004dd70002e7eb5c8c6e11373` | Same | No source update |
| MOSS-Music | `ad107c7ddaa06de168a0dfbc18d3e1e6a40c0e5e` | Same | No source update |
| whisperx | `8dcdec18039f6f6b10b967c45273f54dd2a1f699` | `771b4a14a9486f8fd5aef18ef49e35d639523dd3` | 3 commits ahead |

These are repository comparisons, not verification of every separately cached
model weight. No blanket upgrade of third_party or pip packages was performed.
The mini audit is intentionally scoped, not an exhaustive survey of every
music model in existence.

WhisperX has a newly merged opt-in interleaved-context feature for batched
transcription and an actionable `punkt_tab` download error. The maintainer
describes context benefits for punctuation/proper nouns. It should be tested
against singing before adoption: context may also reinforce an incorrect
guess. It is not a music-generation upgrade or evidence of perfect timing.
Our core `musia` environment has **faster-whisper 1.2.1**, not an installed
WhisperX distribution, so pulling that checkout alone would not upgrade the
active recognizer. The clone was left unchanged pending a compatibility test.
[Merged context PR](https://github.com/m-bain/whisperX/pull/1474).

Observed core environment: Python 3.10, torch 2.3.0, huggingface-hub 0.36.2,
pykakasi 2.3.0, pypinyin 0.55.0 and Demucs 4.0.1. This is an inventory, not a
recommendation to replace the pinned environments. ACE retains its dedicated
existing `.venv`; MiniMax retains its separate overlay. See the
[September installation record](minimax-music3-setup-and-ayachan-2026-09-13.md)
and [research comparison](music-generation-community-update-2026-09-13.md).

## Local correctness improvement

`scripts/run_ace_candidate_sweep.py` previously hard-coded `vocal_language=zh`.
It now accepts `--language ja|en|zh|unknown`, records language in the resumable
request identity, and refuses to reuse a sweep with a different language.
Old manifests without the language field are correctly interpreted as Chinese.
The default remains Chinese so existing commands keep their behavior.

New `--dry-run` prepares TOML/configuration without loading models or creating
fake audio results. It does not erase a prior candidate manifest. This is a
language-correctness and workflow improvement, not a measured fidelity gain.

Six focused tests passed using ACE's existing Python environment, including
TOML parsing, no inference in dry-run, Chinese backward compatibility,
cross-language resume refusal and preservation of existing results. The first
attempt under the Python 3.10 `musia` env could not import standard-library
`tomllib`; tests were run in ACE's newer interpreter instead, with no package
or environment changes. The actual song dry-run succeeded in `musia`.

The installed ACE source also passed its six focused model-aware DCW and seed
fallback regression tests. These use stub generation handlers, not an audio
benchmark. In total, 12 focused tests passed. No GPU model was loaded or kept
resident by this work.

```bash
third_party/ACE-Step-1.5/.venv/bin/python -m unittest discover \
  -s scripts -p test_run_ace_candidate_sweep.py -v
```

The Japanese packet uses native text, a compact positive caption, six seeds,
156 seconds, 92 BPM, G major, XL Turbo and 8 steps. These are unrendered
directions. The final prepared config directory is
`data/creative_projects/aya-canada-beyond-the-maples-20261006/sweep-v2/`;
the initial dry-run directory is preserved as an earlier lyric draft.
Before public release, run full-song listening and the mandatory
separated-vocal large-ASR/reference/independent-evidence audit; prepare accurate
per-vocal translations, ruby, beats/chords and website data from the actual
selected audio. Do not invent timed lyrics for an unrendered draft.
