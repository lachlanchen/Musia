# Fun Player Full-Song Demo - 2026-06-28

This note records the `Rain Day Full Song` website demo added to Fun Lazying Art.

## Website Paths

- Catalog item: `rain-day-full-song-trilingual`
- Manifest: `website/data/songs/rain-day-full-song-trilingual/manifest.json`
- English lyrics: `website/data/songs/rain-day-full-song-trilingual/lyrics/en.json`
- Chinese lyrics: `website/data/songs/rain-day-full-song-trilingual/lyrics/zh-Hans.json`
- Japanese lyrics: `website/data/songs/rain-day-full-song-trilingual/lyrics/ja.json`
- English audio: `website/assets/audio/rain-day-full-song-en.mp3`
- Chinese audio: `website/assets/audio/rain-day-full-song-zh.mp3`
- Japanese audio: `website/assets/audio/rain-day-full-song-ja.mp3`
- Cover: `website/assets/covers/rain-day-full-song-16x9.png`
- README screenshot: `website/assets/images/musai-fun-player-full-song.png`

The catalog default remains the short SoulX trilingual verse:

```text
rain-day-bilingual-verse
```

The full song is selectable through the media library and searchable by title, language, and tags.

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
- lyric language selection: multi-select, defaulting to all available tracks.

This fixes the earlier confusion where the right lyric carousel appeared to show only one language even when the media item had multiple text tracks.
