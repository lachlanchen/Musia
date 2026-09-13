# MiniMax Music 3: installation and Aya Chan song

Update, September 14: the user subsequently requested website publication of
the selected song. See the [publication record](ban-qu-chang-an-website-publication-2026-09-14.md).
The private-audition statements below describe the original generation task.

## Scope

Requested: update the music tools, prioritize MiniMax, and generate a beautiful
Chinese song for Aya Chan's hanfu journey through Xi'an/Chang'an, Lanzhou's Yellow
River and danxia landscapes. No social posting, new video generation or player
recording was requested in this turn.

Song: **半曲长安** (*The Melody I Left in Chang'an*).

The source story has a clear emotional through-line: a guqin melody left
unfinished, a promise to return, courage on the road, and reunion. The song uses
that story rather than a list of locations. Original lyrics and the structured
MiniMax caption are in `ideas-and-inspirations/ban-qu-chang-an/`.

## Source and model updates

- ACE-Step-1.5 was fast-forwarded from
  `6d467e4b5081ccb0abf1ec1bf4fdf9051a2d34b0` to
  `ca1e85fe9430179831e6bc6be790c332190a3866`.
- Existing ACE checkpoints and the untracked `instruction.txt` were preserved.
- Six upstream DCW/seed regression tests passed. This is a code test, not a
  listening comparison or proof that SFT is now better.
- Official MiniMax source: `third_party/MiniMax-Music3`, commit
  `945655064d59b98004dd70002e7eb5c8c6e11373`.
- Diffusers source: `third_party/diffusers-music3`, pinned commit
  `c419dac0152186060246c93a095bc1bfaea342b3`.
- Downloaded and SHA-verified MiniMax checkpoint revision:
  `fbdf52fbaaca799592917417eb05f1899f1255ec`.
- The 24 Diffusers-format files completed on September 14: 28,517,620,698 bytes.
  Large files passed SHA-256; small metadata files passed git-blob SHA-1 checks.
  Do not
  also download the duplicate `qwen_7B/`, `dav.pth` and `flowmatching_vae.pth` copies.

Sources: [official MiniMax source](https://github.com/MiniMax-AI/MiniMax-Music3),
[official Diffusers Music 3 guide](https://huggingface.co/docs/diffusers/main/en/api/pipelines/minimax_music3),
[official model files](https://huggingface.co/MiniMaxAI/MiniMax-Music3/tree/main).

## Reusable commands

```bash
bash scripts/install_minimax_music3.sh --verify-sha256

# Resumable multi-connection transport when Hub/Xet is slow:
conda run --no-capture-output -n musia python scripts/download_minimax_music3.py \
  --verify-sha256 --transport aria2 --endpoint https://hf-mirror.com \
  --modelscope-mirror --workers 8

CUDA_VISIBLE_DEVICES=0 bash scripts/run_minimax_music3.sh \
  --lyrics ideas-and-inspirations/ban-qu-chang-an/lyrics.zh-Hans.txt \
  --caption ideas-and-inspirations/ban-qu-chang-an/minimax-caption.txt \
  --output-dir data/creative_projects/aya-chan-ban-qu-chang-an-minimax-20260913/candidates \
  --duration 240 --seeds 91301 91302 --steps 30 --offload auto

conda run -n musia python scripts/test_minimax_music3.py
```

The last command does not approve a song for release. Candidate folders are
non-overwriting. Output includes the complete native-rate PCM-24 WAV, 320kbps MP3,
input lyric, caption, generation metadata and progress. The generation ceiling is
not an exact duration request. A result at that ceiling needs a tail-cut review.

## Environment and transfer lessons

The usual Musia entry point stays in the `musia` conda environment. Music 3
requires a newer Torch/Transformers/Diffusers combination, so its renderer is
isolated at `.conda/minimax-music3/bin/python`.

On this machine the installer reuses the verified `.conda/moss-music` Python
3.12/Torch 2.9.1+cu128 installation through a **system-site-packages virtualenv
overlay**. New Diffusers, Transformers 5.17.0 and Accelerate 1.12.0 live only in
the overlay. It is not itself a conda environment; use the shell wrapper rather
than `conda run -n minimax-music3`. Do not remove or move the MOSS base while this
overlay depends on it. MOSS remains on its original Transformers version.

On a machine without that base, the installer creates a separate conda prefix
and installs Torch 2.8.0 from PyPI before the other dependencies. A compatible
alternative shared base may be passed in `MUSIA_MINIMAX_BASE_PYTHON`.

The first fresh CUDA install hit repeated timeouts at NVIDIA's wheel host. A
second `uv pip` resolution ignored inherited system-site packages and tried to
download a newer CUDA 13 stack. Both were stopped before installation. Use the
overlay's `python -m pip` for dependencies so the verified base is actually
reused. Do not describe a failed download as an installed package.

Hub/Xet and plain transfers were slow on this shared connection. The downloader
can use aria2 and a mirror, but **metadata and expected hashes always come from
the pinned official Hugging Face revision**. ModelScope URLs are added only when
its advertised file size and SHA-256 match those official weights. Final hashes
are checked locally. Partial `.aria2` files must be resumed, not mistaken for
complete files just because a sparse file has its eventual length.

The official modular index contains Hub component URLs even when loaded from a
local folder. The renderer binds a copy of every component specification to the
verified local folder and operates offline, avoiding accidental duplicate model
downloads. The downloaded index is not edited.

## Musical controls and review

Follow MiniMax's caption format: Global Metadata, Vocal Details, Arrangement.
Use section tags on separate lines. Native Mandarin lyrics remain separate from
the caption, pronunciation notes, internal project story and publishing metadata.

The chorus is repeated deliberately; its `an/ang` vowel family provides open
phrase endings. The bridge makes room for vulnerability before the final chorus.
The caption calls for one adult female voice, breath and sustained vowels, a
consistent melodic motif, a gradual instrumental arc, and a complete ending.
The approximate 78 BPM direction must not become a claimed measured tempo.

### Updated ACE comparison

Two three-minute controls were rendered with the updated ACE code, existing
`acestep-v15-xl-turbo`, eight steps, no thinking LM, and seeds 913101/913102.
The configuration is in the ignored creative project as `ace-control.toml`.
These are **ACE controls, not MiniMax outputs**. The same lyric was used, with
an ACE-appropriate compact caption rather than the longer MiniMax caption.

| Seed | LUFS | True peak | APEX musicality / 5 | APEX naturalness / 5 |
| --- | --- | --- | --- | --- |
| 913101 | -12.7 | -1.0 dBFS | 2.70 | 2.58 |
| 913102 | -12.9 | -0.8 dBFS | 2.75 | 2.63 |

Both pass the signal-health gate and reach a quiet ending. MOSS-Music's analysis
describes coherent female guofeng ballads without obvious noise or abrupt cuts.
Those are model judgments, not a human listening approval. Its generous prose
and the moderate APEX scores illustrate why neither evaluator alone proves a
song is excellent. APEX does not verify the lyrics or forecast real popularity.

Both have Demucs bass/drums/vocals/other plus an instrumental sum, large-v3 ASR,
and estimated beats/chords under `data/runs/ban-qu-chang-an-ace-913101/` and
`data/runs/ban-qu-chang-an-ace-913102/`. The beat tracker reports approximately
152 BPM, plausibly double-time against the intended 78 BPM feel. It is an
estimate, not a confirmed lead sheet.

For 913101, a separated-vocal no-VAD large-v3 pass and independent MOSS lyrics
recover the two closing lines omitted by the initial VAD-based transcript:
`那年未尽的半曲 / 今夜 为你弹完`. No-VAD Whisper also hallucinates composer
credits in the opening; do not include those unsupported names in lyrics or
metadata. The early transcript is not an approved release lyric.

After rendering: objective health check; full large-v3 transcription and
separated-vocal no-VAD pass; independent MOSS-Music analysis/lyrics; account for
every input line and any extra ending. Preserve source words when the sound is
close, but preserve actual omissions, repeats and changed structure. Listening
approval must not be inferred solely from ASR or an automatic score.

## Cover

A new 16:9 cinematic cover was generated with the built-in image tool using this
project's red-hanfu heroine as a visual reference: guqin, monumental Chang'an
walls, a broad river and danxia ridges, with warm lanterns evoking homecoming.
The scene is poetic fantasy, not a documentary claim about geography. The
project-bound copy is under the creative project's `assets/` directory.

## Completed MiniMax auditions, September 14

Both used the original native-Chinese lyric, structured caption, BF16 without
quantization, 30 flow steps and automatic CPU offload on GPU 0 (RTX 4090D).
The 240 s setting was an upper bound; both ended naturally before it.

| Seed | Duration | Render time | LUFS | True peak | APEX musicality / naturalness |
| --- | --- | --- | --- | --- | --- |
| 91301 | 130.519 s | 221.72 s | -14.2 | +0.1 dBFS | 2.75 / 2.55 |
| 91302 | 158.476 s | 298.20 s | -14.9 | -2.1 dBFS | 2.74 / 2.55 |

**91302 is the selected private audition.** Its fuller pacing leaves more room
for the narrative and its export passes the signal-health gate. Neither the
automatic scores nor MOSS's favorable prose prove it is better than ACE. Human
listening approval is still pending.

Seed 91301 exposed an export bug: a -1 dB sample-peak ceiling did not prevent
inter-sample true peaks above zero. The renderer now measures reconstructed true
peak using FFmpeg EBU R128 and applies additional constant attenuation to target
-2 dBFS with a small safety margin. It does not compress or normalize dynamics.
Seed 91302 has -2.3 dB total constant export gain. The earlier seed is preserved
unchanged as evidence and should not be released without fixing its headroom.

Selected package:

`data/creative_projects/aya-chan-ban-qu-chang-an-minimax-20260913/selected/`

Listening file: `ban-qu-chang-an-minimax.mp3`, with embedded new cover and clean
title/artist metadata. Editing file: `ban-qu-chang-an-minimax.wav`, 44.1 kHz
stereo PCM-24. WAV SHA-256:
`ab11dafb5c11624588d9c60c6243f3611c2e8cc3460c7db9d8772b029603b4fe`.

Both MiniMax candidates have four Demucs stems plus instrumental, estimated
beats/chords, large-v3 ASR and independent MOSS review. For the selected candidate
these are in `data/runs/ban-qu-chang-an-minimax-91302/` and the creative project's
`review/minimax-91302/`. Beat tracking estimates approximately 76 BPM. It is not
an independently verified score or exact guitar-learning dataset.

### Complete lyric audit and reusable export

The initial VAD pass missed second-chorus fragments and the complete ending.
Full-mix and isolated-vocal **no-VAD large-v3** passes plus independent MOSS lyric
transcription recovered all 28 lines. Source-close spellings were restored:
别/憋, 渐淡/简单, 半首/伴手, 一半/一伴, 兰州/蓝昼, 丹霞/淡夏, 远山/云山,
可一想/可以像, 漫天/满天, 未尽/未经, 弹完/弹弯. Do not mistake phonetic ASR
errors for the song's intended written wording when the sound is close.

One unresolved difference remains: 城南 versus 城门, around 44.3–50.6 s. Input
and MOSS support 城南; Whisper repeatedly reports 城门. The reviewed text retains
城南 pending listening, explicitly flagged in the manifest. Do not call this a
word-perfect transcription.

The separated-stem ASR invented composer credits during the instrumental intro.
They are unsupported by the other sources and excluded. Seed 91301's initial
ASR also invented duplicated ending lines with zero-duration words; those are
not real repetitions merely because the transcript contains them.

`scripts/export_reviewed_lyrics.py` exports an **explicit reviewed mapping**, not
an unreviewed automatic correction. It checks the audio hash, accounts for every
selected ASR segment, requires matching character counts before transferring
word spans, rejects invalid/zero-duration word anchors, and keeps the original
ASR text as provenance. This first helper supports Mandarin-only vocals; do not
apply it to mixed-language or phonetic-input vocals without adding that support.

```bash
conda run --no-capture-output -n musia python scripts/export_reviewed_lyrics.py \
  --review ideas-and-inspirations/ban-qu-chang-an/review-minimax-91302.json \
  --asr data/creative_projects/aya-chan-ban-qu-chang-an-minimax-20260913/review/minimax-91302/correction/selected-large-v3-no-vad.json \
  --audio data/creative_projects/aya-chan-ban-qu-chang-an-minimax-20260913/candidates/seed-91302/song.wav \
  --output-dir data/creative_projects/aya-chan-ban-qu-chang-an-minimax-20260913/review/minimax-91302/lyrics

conda run -n musia python scripts/test_export_reviewed_lyrics.py
```

Existing export directories are preserved; choose a new directory when revising.
The export contains Chinese/English/Japanese Fun text-track JSON, Chinese pinyin,
Japanese furigana, reviewed plain lyrics, LRC and an audit log. Chinese uses ASR
word spans, not invented evenly spaced character timestamps. Translation tokens
are approximate within each line. No instrumental placeholders are lyric rows.
Some first-word spans may include breaths/rests: **timing is provisional and not
approved for player recording or lip sync**. A public site item was not created.

### Delivery and verification

Nutstore song package:
`/home/lachlan/Nutstore Files/Share/ayachan/2026-09-14-ban-qu-chang-an-song/`.

[LALACHAN handoff](MusiaVideo/ban-qu-chang-an-ayachan-hanfu-handoff-2026-09-14.md)
is mirrored to the sibling LALACHAN repository. Original reference images and the
48.7 s source video remain untouched. This song lasts 158.476 s; a later MV must
be edited to the song or an approved musical excerpt, not forcibly time-scaled.

Verification: eight renderer/downloader unit tests, three reviewed-anchor tests,
six upstream ACE DCW/seed tests, shell syntax checks, full MP3 decode, WAV identity
hash and metadata/stream inspection. The production skill was updated in both
`~/.codex/skills/musia-music-production/` and `../LazySkills/skills/` and passed
the skill validator. Generated media, third-party source and weights remain out
of Git. No second active Musia generation or GUI stack was left running.

## Publication boundary

Initial MiniMax renders are private auditions. The downloaded Community License
has attribution, disclosure and commercial-service conditions; the previous
research records conflicting commercial guidance. Review the applicable license
before commercial distribution or exposing a public generator. This task does
not silently send a candidate to Shipinhao, social platforms or the public music
catalogue. The LALACHAN handoff must identify the actual selected audio and
corrected lyric, not the intended lyric alone.

[Previous source comparison](music-generation-community-update-2026-09-13.md).
