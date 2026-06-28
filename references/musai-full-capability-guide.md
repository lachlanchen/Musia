# Musai Full Capability Guide

Musai is becoming a local-first music writing and music analysis workstation.

The mental model is:

```text
write a song like writing an article or code
```

A user can start with an idea, lyrics, melody notes, chords, a rough recording, a full song, or a licensed source track. Musai should turn that input into structured artifacts, use AI to refine weak inputs, run local audio models when possible, and save everything needed to regenerate or edit the result.

## Current Capability Map

| Need | Current Musai Route | Main Artifacts |
| --- | --- | --- |
| Analyze an audio file | `musai pipeline` / `scripts/run_pipeline.py` | stems, lyrics, beats, chords, report, manifest |
| Extract four stems | Demucs wrapper | `bass.wav`, `drums.wav`, `vocals.wav`, `other.wav`, `instrumental.wav`, `human_sound.wav` |
| Transcribe lyrics | faster-whisper wrapper | `lyrics.json`, `lyrics.txt` |
| Estimate beats | librosa beat tracking | `beats.json`, `beats.csv` |
| Estimate chords | Musai chroma/chord baseline | `chords.json`, `chords.csv` |
| Create project brief | `musai plan` | `BRIEF.md`, `brief.json`, model configs, commands |
| Generate short singing verse | `musai soulx-verse` | `lyrics.md`, `melody.wav`, `vocal.wav`, `mix.wav`, SoulX metadata |
| Localize a song | analysis pipeline + lyric adaptation + SoulX/YingMusic prep | source artifacts, target lyrics, vocal render, mix |
| Full song generation | ACE-Step / YuE / SongGen style research route | full-song candidates, prompts, configs |
| Music QA / planning | DeepSeek/OpenAI/Codex wrappers | refined lyrics, prompts, quality notes, handoff docs |
| Web studio | `musai studio --tmux` | chat, worker jobs, canvas artifacts, project creation |

## Installed Or Staged Tooling

### Core Environment

Main conda env:

```text
musai
```

Core packages include:

```text
torch
torchaudio
demucs
faster-whisper
librosa
soundfile
numpy
scipy
openai
pypinyin
g2p_en
jieba
phonemizer
pedalboard
pyloudnorm
```

`g2p_en` plus NLTK resources are installed so mixed Mandarin/English singing metadata can be generated for SoulX.

### Local Model Environments

Local project envs under `.conda/`:

```text
.conda/soulxsinger
.conda/moss-music
.conda/songgen
.conda/diffrhythm
.conda/heartmula
```

These are intentionally local and ignored by git.

### Third-Party Repositories

Important staged repos under `third_party/`:

```text
SoulX-Singer
YingMusic-Singer
YingMusic-Singer-Plus
ACE-Step
ACE-Step-1.5
YuE
SongGen
DiffRhythm
HeartMuLa
MOSS-Music
Muzic
Amphion
DiffSinger
OpenVPI-DiffSinger
NNSVS
OpenUtau
RVC-WebUI
GPT-SoVITS
RMVPE
basic-pitch
whisperx
demucs
AudioCraft
stable-audio-tools
Magenta
MERT
MuQ
MuCodec
FunMusic
```

Not every staged repo has a production wrapper yet. Musai’s stable local wrappers today are:

- Demucs/faster-whisper/librosa/chord analysis through `musai pipeline`;
- SoulX vocal rendering through `scripts/run_soulx_svs.sh`;
- short bilingual verse generation through `musai soulx-verse`;
- project planning through `musai plan`;
- chat/worker routing through Musai Studio.

## Audio Analysis Workflow

Use this when the input is an audio file and the goal is to understand it.

```bash
musai pipeline /path/to/song.wav \
  --run-name my-song-analysis \
  --max-duration 120 \
  --asr-model small \
  --language en \
  --demucs-device cuda
```

Equivalent direct Python route:

```bash
PYTHONNOUSERSITE=1 conda run -n musai python scripts/run_pipeline.py /path/to/song.wav \
  --run-name my-song-analysis \
  --max-duration 120 \
  --asr-model small \
  --language en \
  --demucs-device cuda
```

Expected output folder:

```text
data/runs/my-song-analysis/
```

Important artifacts:

```text
source/input.wav
stems/bass.wav
stems/drums.wav
stems/vocals.wav
stems/other.wav
stems/instrumental.wav
stems/human_sound.wav
analysis/lyrics.json
analysis/lyrics.txt
analysis/beats.json
analysis/beats.csv
analysis/chords.json
analysis/chords.csv
manifest.json
REPORT.md
```

The four Demucs stems are:

```text
bass
drums
vocals
other
```

Musai also writes:

```text
instrumental = bass + drums + other
human_sound = vocals
```

## Music Generation Workflow

Musai supports several levels of control.

### Level 1: Idea To Song Brief

Use this when the user has only an idea.

```bash
musai plan \
  --title "Rain Lantern" \
  --idea "A rainy night song about walking home under city lights" \
  --generation-mode full_production \
  --control-level free \
  --provider deepseek
```

Output:

```text
data/creative_projects/<project>/
BRIEF.md
brief.json
lyrics_draft.txt
ace_step_config.toml
SOULX_REQUEST.md
AGINTI_HANDOFF.md
commands.sh
```

### Level 2: Lyrics To Music

Use this when the user already has lyrics.

```bash
musai plan \
  --title "My Lyric Demo" \
  --lyrics-file lyrics.txt \
  --generation-mode full_production \
  --control-level lyrics \
  --provider deepseek
```

Musai should preserve the lyric intent and ask the AI layer to polish only where singability requires it.

### Level 3: Lyrics Plus Chords

Use this when the user has lyrics and harmonic direction.

```bash
musai plan \
  --title "Chord Demo" \
  --lyrics-file lyrics.txt \
  --chords "Dm | Bb | F | C" \
  --generation-mode controlled_song \
  --control-level lyrics_chords \
  --provider deepseek
```

Expected artifacts include a production brief, chord notes, lyrics draft, and backend commands.

### Level 4: Lyrics Plus Melody / Xuanlv / Sheet

Use this when the user has melody, numbered notation, staff notes, a hook rhythm, or a friend’s singing sketch.

```bash
musai plan \
  --title "Melody Controlled Demo" \
  --lyrics-file lyrics.txt \
  --melody "slow rising four-note hook, then a falling answer phrase" \
  --generation-mode controlled_song \
  --control-level melody_sheet \
  --provider deepseek
```

The English wording for `xuanlv` here is:

```text
melody
melodic contour
hook shape
phrase rhythm
note durations
sheet / numbered notation / jianpu
```

### Level 5: Reference Audio To Controlled Song

Use this when the user provides an example recording, a rough voice memo, or a friend’s demo.

```bash
musai plan \
  --title "Reference Controlled Demo" \
  --idea "Keep the feeling of this demo but improve it" \
  --reference-audio /path/to/demo.m4a \
  --analyze-reference \
  --generation-mode controlled_song \
  --control-level reference_audio \
  --provider deepseek
```

Musai analyzes the reference first, then uses the result to create a better generation plan.

## Short Singing Verse With SoulX

Use this when the target is a short sung vocal, a hook, or music for a short film.

```bash
musai soulx-verse \
  --title "Rain Day" \
  --idea "A tender rainy-day musical short film verse mixing Mandarin Chinese and simple English words" \
  --provider deepseek
```

Output folder:

```text
data/soulx_verses/<run>/
```

Artifacts:

```text
lyrics.md
target_metadata.json
melody.wav
vocal.wav
mix.wav
manifest.json
LALACHAN_HANDOFF.md
```

What happens internally:

```text
idea / optional lyrics
-> DeepSeek or OpenAI lyric refinement
-> safety and phoneme validation
-> Mandarin + English phoneme generation
-> score-style note duration and pitch metadata
-> melody guide wav
-> SoulX vocal render
-> vocal-forward mix
-> handoff note
```

A verified example exists locally:

```text
data/soulx_verses/rain-day-bilingual-verse/
```

Main files:

```text
vocal.wav
melody.wav
mix.wav
lyrics.md
LALACHAN_HANDOFF.md
```

This is good for LALACHAN-style musical short films because it gives both audio and subtitle/shot-planning text.

## Song Localization Workflow

Use this when the user owns or has permission for the source song and wants a new-language sung version.

```text
source song
-> rights confirmation
-> stems: bass/drums/vocals/other
-> lyrics and timings
-> beats and chords
-> melody / phrase timing extraction
-> singable lyric adaptation
-> target-language singing vocal
-> mix with instrumental
-> QA
```

Current practical route:

1. Analyze the source:

```bash
musai pipeline /path/to/licensed-song.wav \
  --run-name licensed-song-analysis \
  --language en \
  --demucs-device cuda
```

2. Create a localization project:

```bash
musai plan \
  --title "Licensed Song Chinese Version" \
  --reference-audio /path/to/licensed-song.wav \
  --target-language zh-CN \
  --generation-mode localization \
  --control-level strict_localization \
  --rights-confirmed \
  --provider deepseek \
  --analyze-reference
```

3. Use `SOULX_REQUEST.md` and `commands.sh` from the project folder to prepare or run vocal synthesis.

Current best local singing backend:

```text
SoulX-Singer
```

Best research direction for strict CN/EN lyric replacement:

```text
YingMusic-Singer-Plus
```

## Full Production Generation

Use this when the user wants a new complete song from an idea, lyrics, or style brief.

Current staged full-song backends:

```text
ACE-Step / ACE-Step-1.5
YuE
SongGen
DiffRhythm
HeartMuLa
AudioCraft
stable-audio-tools
```

Practical current route:

```bash
musai plan \
  --title "Original Full Song" \
  --idea "A cinematic rainy day song with a hopeful chorus" \
  --generation-mode full_production \
  --provider deepseek
```

Then inspect:

```text
ace_step_config.toml
commands.sh
BRIEF.md
```

For production quality, keep every candidate as an artifact and run listening checks before accepting it.

## Musai Studio

Start the web studio:

```bash
musai studio --tmux
```

Current URL:

```text
http://127.0.0.1:8766
```

Studio supports:

- chat routing;
- worker routing;
- project creation;
- SoulX Verse generation;
- artifact registration;
- audio/markdown canvas preview;
- setup and model visibility.

The Studio AI layer can use:

```text
DeepSeek
OpenAI
Codex CLI profiles
```

Use the worker mode when the task needs file edits, artifact registration, or longer analysis.

## Artifact Contract

Every serious Musai run should preserve:

```text
manifest.json
README or REPORT.md
lyrics.md or lyrics.txt
audio files
metadata JSON
commands used
model/provider info
quality notes
handoff notes
```

For analysis:

```text
stems/
analysis/
manifest.json
REPORT.md
```

For generation:

```text
lyrics.md
melody.wav or MIDI/metadata
vocal.wav
mix.wav
manifest.json
handoff note
```

For localization:

```text
source stems
source lyrics
target adapted lyrics
target vocal
final mix
QA report
rights/consent flags
```

## Quality Checklist

Before accepting an output:

- vocal is clearly sung, not just speech;
- vocal is not buried in the mix;
- lyrics are intelligible;
- melody and phrase rhythm match the intended control level;
- chords/beats are plausible for the source or generated song;
- generated lyrics are original;
- no unauthorized real-person voice imitation;
- source-song localization has rights confirmed;
- all artifacts and commands are saved.

## Install And Refresh Commands

Core local setup:

```bash
scripts/bootstrap_musai.sh
```

Download or refresh staged model repos:

```bash
scripts/download_quality_backends.sh repos
scripts/download_quality_backends.sh expanded-repos
```

Download major model weights:

```bash
scripts/download_quality_backends.sh all
```

Install local model envs:

```bash
scripts/install_quality_envs.sh all
```

Test local core:

```bash
npm test
scripts/setup_and_smoke_test.sh
scripts/test_open_songs_matrix.sh
```

## What Musai Can Do Now

Musai can currently:

- analyze songs into stems, lyrics, beats, chords, and reports;
- create structured song briefs from ideas, lyrics, chords, melody, and reference audio;
- generate short bilingual SoulX singing packages with lyrics, melody, vocal, and mix files;
- prepare strict localization projects for licensed source songs;
- route AI refinement through DeepSeek/OpenAI/Codex;
- expose this through both CLI and a local web studio;
- package the CLI/web wrapper through npm as `@lazyingart/musai`.

## What Still Needs Care

Musai is powerful but not magic. These areas still need careful engineering and listening:

- long-form SoulX verse/chorus metadata needs better note design and manual correction tools;
- full-song generation backends need more reliable wrappers and QA;
- chord recognition is a useful baseline, not a professional transcription guarantee;
- strict song localization needs better phrase-level timing and lyric alignment;
- commercial/public releases need rights, license, and voice-consent checks.

The important direction is correct: Musai turns music work into editable, inspectable artifacts, so creating a song becomes more like iterating on text or code.

