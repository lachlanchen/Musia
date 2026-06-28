# Aya Chan Hikari Ame - 2026-06-28

This records the local Japanese song package generated for future `../LALACHAN` video work.

## Project

```text
data/creative_projects/aya-chan-hikari-ame-20260628/
```

This folder is ignored by git because it contains generated WAV/MP3 media.

## Selected Audio

```text
data/creative_projects/aya-chan-hikari-ame-20260628/final/aya-chan-hikari-ame-selected.wav
data/creative_projects/aya-chan-hikari-ame-20260628/final/aya-chan-hikari-ame-selected.mp3
```

Cover/poster:

```text
data/creative_projects/aya-chan-hikari-ame-20260628/assets/aya-chan-hikari-ame-cover-16x9.png
```

LALACHAN handoff:

```text
data/creative_projects/aya-chan-hikari-ame-20260628/LALACHAN_SONG_TO_VIDEO_HANDOFF.md
```

Selected version note:

```text
data/creative_projects/aya-chan-hikari-ame-20260628/SELECTED_VERSION.md
```

## Generation

- Backend: ACE-Step 1.5 XL turbo
- Language: Japanese
- Duration: 68 seconds
- BPM: 92
- Key: G major
- Seed: 731028
- Vocal direction: clear upfront young female Japanese vocal; original fictional character theme; no real singer imitation.

Lyrics:

```text
data/creative_projects/aya-chan-hikari-ame-20260628/lyrics/ja.txt
```

Prompt/config:

```text
data/creative_projects/aya-chan-hikari-ame-20260628/PROMPT.md
data/creative_projects/aya-chan-hikari-ame-20260628/ace_ja.toml
```

## Review And Analysis

Selected v1 review:

```text
data/creative_projects/aya-chan-hikari-ame-20260628/reviews/20260628-154234/SONG_REVIEW.md
data/creative_projects/aya-chan-hikari-ame-20260628/reviews/20260628-154234/quality.json
```

Full analysis:

```text
data/runs/aya-chan-hikari-ame-20260628-20260628-154133-analysis/
```

Artifacts:

```text
stems/bass.wav
stems/drums.wav
stems/vocals.wav
stems/other.wav
stems/instrumental.wav
stems/human_sound.wav
analysis/lyrics.json
analysis/lyrics.txt
analysis/beats.csv
analysis/chords.csv
manifest.json
REPORT.md
```

Analysis result:

- Tempo: about 92.29 BPM.
- Beat analysis: 97 beats.
- Chord analysis: 60 chord segments.
- Stems: Demucs completed successfully.

## Candidate Comparison

| Candidate | Result | Decision |
| --- | --- | --- |
| v1, 68s original lyric | ASR recovered partial lyric; best overall current candidate | selected |
| v2, 48s simplified lyric | ASR recovered only the first short phrase | rejected |
| v3, 48s kana-heavy lyric | ASR returned empty text | rejected |

## Quality Caveat

The selected song is usable as a first LALACHAN video reference, but not yet a final professional Japanese lyric-accurate release. The audio levels and music structure are usable; ASR only recovers part of the intended lyric. For a public music release, run a new correction pass with a Japanese-specialized vocal workflow or manually correct the vocal in a DAW.

## Recommended LALACHAN Use

Use the selected MP3 as a timing and emotional reference for a musical short film. Do not ask the video model to render the lyrics as text. Let the video follow the song mood, beat, and phrase changes.
