# Musai Creative Studio

Musai now has a creation layer in addition to the existing localization and analysis pipeline.

Use it when the input is:

- only an idea
- rough or finished lyrics
- lyrics plus chords
- staff notation, numbered notation, MIDI-note sketches, or rhythm notes
- a recorded demo from a friend or labmate
- a reference song whose rhythm/chords/stems should guide a new song
- a song to localize into another language

## Model Routing

| Situation | First Route | Why |
| --- | --- | --- |
| Idea only | DeepSeek/OpenAI brief -> ACE-Step 1.5 | Expand concept, lyrics, style, then generate a complete song. |
| Lyrics only | DeepSeek/OpenAI lyric refinement -> ACE-Step 1.5 | Make lyrics more singable before audio generation. |
| Lyrics + chords | DeepSeek/OpenAI producer brief -> ACE-Step 1.5 | Preserve harmony while creating arrangement and vocal direction. |
| Lyrics + notation | DeepSeek/OpenAI brief -> ACE-Step 1.5, then optional pro synth | Keep melody/rhythm notes visible in the prompt and handoff. |
| Reference audio | Musai analysis -> DeepSeek/OpenAI brief -> ACE-Step 1.5 | Extract stems, beats, chords, and lyrics first. |
| Strict same-song localization | Demucs/analysis -> SoulX-Singer/YingMusic | Preserve arrangement; still needs corrected phrase/note metadata for high quality. |
| Beautiful new song inspired by material | ACE-Step 1.5, then compare SongGen/YuE/DiffRhythm/HeartMuLa | Full-song models are better for new music than exact localization. |

## CLI

List model roles:

```bash
scripts/musai_create.py models
```

Create a project from idea, lyrics, chords, and notation:

```bash
PYTHONNOUSERSITE=1 conda run -n musai python scripts/musai_create.py plan \
  --title "Labmate Memory Demo" \
  --idea "A warm song about a friend who turned rough lyrics into notation and a singable demo." \
  --lyrics-file lyrics.txt \
  --chords "Verse: C G Am F | Chorus: F G C Am" \
  --notation "4/4, simple rising verse melody, chorus opens higher" \
  --genre "acoustic pop ballad" \
  --style "piano, soft strings, warm human vocal" \
  --mood "nostalgic and hopeful" \
  --language en \
  --vocal-language en \
  --duration 90 \
  --provider deepseek
```

Create a project from a reference recording and analyze it immediately:

```bash
PYTHONNOUSERSITE=1 conda run -n musai python scripts/musai_create.py plan \
  --title "Reference Based Song" \
  --idea "Use the rhythm and chord feeling from my demo, but write a new song." \
  --reference-audio /path/to/demo.wav \
  --analyze-reference \
  --provider deepseek
```

Each project is written under:

```text
data/creative_projects/<project-id>/
```

Important files:

```text
project.json
BRIEF.md
brief.json
lyrics_draft.txt
ace_step_config.toml
commands.sh
AGINTI_HANDOFF.md
```

Run ACE-Step for a project:

```bash
data/creative_projects/<project-id>/commands.sh ace
```

Run ACE-Step in tmux:

```bash
data/creative_projects/<project-id>/commands.sh ace-tmux
```

Check the first ACE-Step WAV output:

```bash
data/creative_projects/<project-id>/commands.sh qa-ace
```

Or check any generated audio directly:

```bash
PYTHONNOUSERSITE=1 conda run -n musai python scripts/musai_quality_check.py \
  path/to/output.wav \
  --language en \
  --expected-lyrics-file data/creative_projects/<project-id>/lyrics_draft.txt \
  --output-dir data/creative_projects/<project-id>
```

## Web App

Start Musai Studio in tmux:

```bash
scripts/start_musai_studio_tmux.sh
```

Default URL, if available:

```text
http://127.0.0.1:8765
```

If that port is busy, the starter picks the next free port and prints the actual URL.

The web app can create projects from idea, lyrics, chords, notation, and reference audio paths. It also lists project briefs and command files.

## AgInTiFlow Handoff

Every creative project includes `AGINTI_HANDOFF.md`. It contains a Codex/AgInTiFlow prompt like:

```bash
codex -m gpt-5.5 -c model_reasoning_effort="high" -s danger-full-access -a never --cd /home/lachlan/ProjectsLFS/Musai "Inspect PROJECT_DIR, run the Musai commands, improve lyrics/prompt quality, generate or review audio outputs, and update the project report with evidence."
```

Use this when you want AgInTiFlow or a Codex 5.5 high-reasoning session to refine lyrics, run long GPU jobs, or judge output quality.

## Quality Policy

Accept a song only when:

- the lead vocal is clearly sung and audible
- lyrics are intelligible in the target language
- the output follows the supplied idea, chords, notation, or reference rhythm
- the final mix is not clipped or buried
- the project folder records prompts, model configs, outputs, and QA notes

For strict localization, do not call a file final unless phrase timing, melody, target-language lyrics, and listening/ASR checks all pass.

## Local Validation

Validated on 2026-06-28:

- `scripts/musai_create.py models` lists local/API model roles.
- `scripts/musai_create.py plan` created DeepSeek and offline project folders.
- `scripts/start_musai_studio_tmux.sh` started the web app on `http://127.0.0.1:8766` because `8765` was already occupied.
- The web API created a project from a JSON payload.
- ACE-Step 1.5 generated a 30-second WAV from the web smoke project.
- `scripts/musai_quality_check.py` measured the ACE output and correctly marked it `review` because ASR did not recover the expected lyrics.

The ACE smoke output proves the backend can generate audio locally, but it is not accepted as a high-quality vocal song. Use the QA gate to reject weak generations and rerun with richer lyrics/prompts/seeds.
