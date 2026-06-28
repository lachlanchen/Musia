# Fun Player Full-Song Demo - 2026-06-28

This note records the `Rain Day Full Song` website demo added to Fun Lazying Art.

## Website Paths

- Catalog item: `rain-day-full-song-trilingual`
- Manifest: `website/data/songs/rain-day-full-song-trilingual/manifest.json`
- English vocal lyric set: `website/data/songs/rain-day-full-song-trilingual/lyrics/en-vocal/`
- Chinese vocal lyric set: `website/data/songs/rain-day-full-song-trilingual/lyrics/zh-vocal/`
- Japanese vocal lyric set: `website/data/songs/rain-day-full-song-trilingual/lyrics/ja-vocal/`
- English audio: `website/assets/audio/rain-day-full-song-en.mp3`
- Chinese audio: `website/assets/audio/rain-day-full-song-zh.mp3`
- Japanese audio: `website/assets/audio/rain-day-full-song-ja.mp3`
- Cover: `website/assets/covers/rain-day-full-song-16x9.png`
- README screenshot: `website/assets/images/musai-fun-player-full-song.png`

The catalog currently hides the short SoulX verse and defaults to:

```text
mars-red-sky-trilingual
```

The full song is selectable through the media library and searchable by title, language, and tags.

## Analysis Retiming

After generation, each website MP3 was run back through the Musai analysis pipeline:

```text
data/runs/generated-rain-day-full-en-analysis/
data/runs/generated-rain-day-full-zh-analysis/
data/runs/generated-rain-day-full-ja-analysis/
data/runs/generated-rain-day-short-zh-analysis/
```

The public lyric tracks were then retimed from the detected sung phrases:

- English full song: detected around `78.30` BPM.
- Chinese full song: detected at double-time `151.99` BPM, displayed as the normalized musical pulse near `76` BPM.
- Japanese full song: detected around `76.00` BPM.
- Short SoulX Mandarin verse: detected around `112.35` BPM; the website keeps this as analysis provenance while preserving the original creative key/phrase concept.

The full-song website manifest now uses per-vocal `lyricSets`. This is important because the English, Chinese, and Japanese files are separate generated renders, not one strict same-stems localization pass. Each vocal render owns a separate trilingual display:

```text
en-vocal: English-led timing with Chinese/Japanese translations
zh-vocal: Mandarin-led timing with Japanese/English translations
ja-vocal: Japanese-led timing with Chinese/English translations
```

This avoids the earlier bug where the Mandarin render's timeline was reused for English, leaving the first visible Mandarin/Japanese lines without English text.

The displayed chord row is a simplified analysis-derived D minor progression from the cleanest full-song chord pass:

```text
Dm -> Bb -> F -> Dm -> Bb -> F -> Dm -> ...
```

The row is intentionally compact so it works as a single horizontal chord carousel above the current lyric card.

## Generation

Working run folder:

```text
data/creative_projects/rain-day-full-trilingual-20260628/
```

The final website MP3s were selected from these local WAV candidates:

| Language | Selected source WAV | Model | QA |
| --- | --- | --- | --- |
| English | `ace_outputs/en/d8e99df2-c52f-6336-d874-a3c95cf2c302.wav` | `acestep-v15-turbo` | pass |
| Chinese | `ace_outputs/zh_xl/8aeb1dc3-a205-3352-8455-1a23c255c2b8.wav` | `acestep-v15-xl-turbo` | pass |
| Japanese | `ace_outputs/ja_xl/ac655572-724f-3ab1-cfd1-192d8f6e36a4.wav` | `acestep-v15-xl-turbo` | pass |

These are full-song generation candidates, not strict same-stems localization renders. They should be treated as a polished creative demo path for idea/lyrics-to-song, while strict localization still requires extracted stems, corrected melody/F0, target-language singing synthesis, and mixing.

## QA

Commands used:

```bash
PYTHONNOUSERSITE=1 conda run -n musai python scripts/musai_quality_check.py AUDIO \
  --language LANG \
  --expected-lyrics-file data/creative_projects/rain-day-full-trilingual-20260628/lyrics/LANG.txt \
  --output-dir data/creative_projects/rain-day-full-trilingual-20260628/qa_LANG
```

Automated QA checked duration, sample rate, peak/RMS level, ASR availability, and lyric overlap where practical. Human listening is still required before calling a render production-grade.

## UI Change

The player now separates:

- audio/vocal render selection: single-select, because only one render can play at a time;
- lyric language selection: multi-select, defaulting to all available tracks;
- media selection: a collapsible left drawer opened by the header menu button;
- search: icon-only in the header; opening it also opens the media drawer;
- chords: one single-row horizontal carousel at the top of the lyric panel.

This fixes the earlier confusion where the right lyric carousel appeared to show only one language even when the media item had multiple text tracks.

## Current Limitation

The generated audio quality is good enough for a public demo, but the analysis shows that some generated vocals do not sing every prompt-planned line exactly. The website lyrics now favor each render's detected sung phrase timing and natural localized lyric text. A true production localization should regenerate or manually correct the vocal until ASR, human listening, lyric timing, and chord/melody checks all agree.
