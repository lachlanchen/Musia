# Musai Song Workbench

`scripts/musai_song_workbench.py` is the reusable path for generating, correcting, reviewing, and handing off original songs.

Use it when the goal is:

- idea or lyrics to a full song;
- a controlled song package with prompts, lyrics, model config, and commands;
- QA after generation;
- a correction pass after the first render;
- a LALACHAN/Xiaoyunque video handoff from a finished song.

## Create A Song Project

```bash
musai song init \
  --title "Aya Chan Hikari Ame" \
  --idea "A warm Japanese theme song for Aya Chan." \
  --character "Aya Chan, female red panda figurine" \
  --vocal-language ja \
  --genre "cinematic J-pop character theme" \
  --style "sparkling piano, warm strings, gentle drums" \
  --mood "tender, brave, magical, hopeful" \
  --voice-notes "clear upfront young female vocal, no real singer imitation" \
  --duration 68 \
  --bpm 92 \
  --keyscale "G major" \
  --lyrics-file lyrics.txt
```

Output:

```text
data/creative_projects/<song-id>/
  PROMPT.md
  REVIEW_CHECKLIST.md
  LALACHAN_HANDOFF.md
  LALACHAN_SONG_TO_VIDEO_HANDOFF.md
  song_spec.json
  ace_<lang>.toml
  commands.sh
  lyrics/<lang>.txt
```

## Generate

```bash
data/creative_projects/<song-id>/commands.sh generate
```

or:

```bash
data/creative_projects/<song-id>/commands.sh generate-tmux
```

ACE-Step WAV outputs are written under:

```text
data/creative_projects/<song-id>/ace_outputs/
```

## Review

```bash
data/creative_projects/<song-id>/commands.sh review
```

This runs:

- `scripts/musai_quality_check.py` for duration, level, ASR, and lyric overlap;
- `scripts/run_pipeline.py` for Demucs stems, lyrics, beats, chords, and manifest.

Review output:

```text
data/creative_projects/<song-id>/reviews/<timestamp>/QA.md
data/creative_projects/<song-id>/reviews/<timestamp>/quality.json
data/creative_projects/<song-id>/reviews/<timestamp>/SONG_REVIEW.md
data/runs/<song-id>-<timestamp>-analysis/
```

## Correct

Use correction when the vocal is quiet, lyric recovery is poor, phrase endings are clipped, or the style is wrong.

```bash
musai song correct \
  --project-dir data/creative_projects/<song-id> \
  --issues "lyrics are unclear and final words are clipped" \
  --caption-extra "Very clear upfront vocal, fewer words per line" \
  --lyrics-file corrected-lyrics.txt \
  --seed 731077 \
  --duration 48
```

Output:

```text
data/creative_projects/<song-id>/corrections/<timestamp>/
  CORRECTION_PLAN.md
  ace_<lang>_corrected.toml
  <lang>.txt
```

Run the corrected config:

```bash
cd third_party/ACE-Step-1.5
.venv/bin/python cli.py -c /abs/path/to/ace_<lang>_corrected.toml --backend vllm
```

## Handoff To LALACHAN

```bash
musai song handoff \
  --project-dir data/creative_projects/<song-id> \
  --audio data/creative_projects/<song-id>/final/song.mp3 \
  --cover data/creative_projects/<song-id>/assets/cover-16x9.png
```

This writes:

```text
LALACHAN_SONG_TO_VIDEO_HANDOFF.md
```

Use that from `../LALACHAN` when generating a video from a finished song.

## Quality Rule

Do not accept a song only because a model produced a file. A usable song needs:

- audible vocal;
- healthy levels;
- coherent tempo and chords;
- lyrics good enough for the purpose;
- human listening approval;
- a saved review report.

For public release, prefer another correction pass when ASR overlap is low or when the user expects lyric accuracy.
