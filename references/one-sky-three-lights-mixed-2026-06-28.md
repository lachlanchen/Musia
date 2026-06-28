# One Sky, Three Lights Mixed-Language Song

Date: 2026-06-28

Public URL:

```text
https://fun.lazying.art/#one-sky-three-lights-mixed
```

## Goal

Create a smooth mixed-language Musai song and use it to validate translation-word highlighting in the Fun Lazying Art player.

The intended language design is:

```text
English lead phrases
Japanese romaji sung phrases
Mandarin pinyin sung phrases
native Japanese and Chinese displayed in the website
English, Chinese, and Japanese translations highlighted from the active mixed-vocal line
```

## Accepted Audio

Accepted render:

```text
data/creative_projects/one-sky-three-lights-mixed-20260628/ace_outputs/mixed_phonetic/e4ff93f6-e2ad-9710-b014-e0b0ded999cd.wav
```

Committed website MP3:

```text
website/assets/audio/one-sky-three-lights-mixed.mp3
```

Model route:

```text
ACE-Step 1.5 XL turbo
```

The accepted lyric input uses English plus Japanese romaji and Mandarin pinyin. This was more reliable than feeding native CJK script into a single English-conditioned mixed render.

## Rejected Attempts

Native CJK mixed ACE renders were musically usable but did not follow the later Mandarin/Japanese lyrics reliably:

```text
data/creative_projects/one-sky-three-lights-mixed-20260628/ace_outputs/mixed_xl/
data/creative_projects/one-sky-three-lights-mixed-20260628/ace_outputs/mixed_unknown_v2/
```

SongGen mixed-pro was also tested with phonetic lyrics through:

```text
scripts/run_songgen_mixed.py
```

It reached generation, but the output was rejected because the WAV was 23.86 seconds, mono 16 kHz, and saturated at 0 dB. The SongGen runner remains useful for future debugging, but this render was not published.

After that failed test, the runner was changed to default to float32 and to require explicit `--low-cpu-mem-usage` for the low-memory path.

## Quality / Analysis

Accepted render checks:

```text
Duration: 64.000 seconds
Sample rate: 48000 Hz stereo
Mean volume: -15.5 dB
Peak: -1.0 dB
Tempo: 86.13 BPM
Chord segments: 40
Quality gate: pass
```

Analysis run:

```text
data/runs/one-sky-three-lights-ace-phonetic-analysis/
```

Artifacts produced locally:

```text
stems/vocals.wav
stems/drums.wav
stems/bass.wav
stems/other.wav
stems/human_sound.wav
stems/instrumental.wav
analysis/beats.csv
analysis/beats.json
analysis/chords.csv
analysis/chords.json
analysis/lyrics.json
analysis/lyrics.txt
REPORT.md
```

Quality report:

```text
data/creative_projects/one-sky-three-lights-mixed-20260628/reviews/ace_phonetic/QA.md
```

ASR recovered the main phrase structure but not every word perfectly. The website lyric JSON corrects obvious ASR errors against the planned phonetic lyric while keeping the detected line timing.

## Website Assets

Committed:

```text
website/data/songs/one-sky-three-lights-mixed/manifest.json
website/data/songs/one-sky-three-lights-mixed/lyrics/mixed-vocal/mul.json
website/data/songs/one-sky-three-lights-mixed/lyrics/mixed-vocal/en.json
website/data/songs/one-sky-three-lights-mixed/lyrics/mixed-vocal/zh-Hans.json
website/data/songs/one-sky-three-lights-mixed/lyrics/mixed-vocal/ja.json
website/assets/audio/one-sky-three-lights-mixed.mp3
website/assets/covers/one-sky-three-lights-16x9.png
```

Cover source:

```text
/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/ig_09b1d3ca27fa59c0016a40ee5115448191a3cf4d6354f5699f.png
```

Cover prompt summary:

```text
16:9 premium album cover for One Sky, Three Lights; twilight city and calm sea; three elegant streams of light crossing into one sky; no text.
```

## Translation Highlight Rule

The active vocal track owns line timing. For this song the active track is `mul`.

When the active mixed line is current:

```text
mul token highlight = active sung word/phrase timing
en/zh/ja token highlight = rough token timing inside the same line id
```

This is intentionally simple and robust. It does not require exact word-to-word cross-language alignment. It only requires all selected translation tracks to share the same `line.id` inside the active lyric set.

For future mixed-language songs:

1. Publish the actual sung language or phonetic track as the active track.
2. Publish translations in the same `lyricSets[]` group.
3. Use the same `line.id` for corresponding meaning lines.
4. Let the active line timing drive all displayed translation highlights.
5. Correct obvious ASR errors, but do not pretend a missing or garbled line was sung perfectly.
