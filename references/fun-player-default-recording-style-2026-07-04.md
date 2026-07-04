# Fun Player Default Recording Style

Date: 2026-07-04

This is the default Musia publication recording style unless the user asks for
another layout.

## Visual Layout

- 4K portrait output, normally `2160x3840`.
- Upper area: Fun Lazying Art / Musia header, cover/player, song title, artist,
  and concise song description.
- Lower area: current two KTV-style lyric lines in the selected active language,
  plus aligned translations for English, Japanese, and Chinese when available.
- Advanced block below lyrics: current chord plus guitar fingering diagram.
- Do not show the full lyric sheet in publication captures unless requested.

## Timing Rule

Start from the vocal section, but do not cut exactly on the first sung syllable.
Use a small musical lead-in before the first lyric line so the entrance feels
smooth. For example, when the first lyric starts at `18.38s`, use `16.50s` or
another nearby stable downbeat/lead-in point after listening.

The recorder start time and the muxed audio start time must be identical. This
keeps the highlighted lyrics, chords, fingering, and burned-in audio aligned.

## Default Command Shape

Use the realtime recorder for publication captures that need multilingual
lyrics and guitar fingering:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/record_fun_player_realtime.py \
  --media-id <media-id> \
  --asset-id <asset-id> \
  --output recorded_videos/<media-id>/<media-id>-<lang>-lyrics-guitar-portrait-4k.mp4 \
  --width 2160 --height 3840 \
  --css-width 1080 --css-height 1920 \
  --device-scale-factor 2 \
  --fps 24 \
  --start <smooth-vocal-lead-in-seconds> \
  --duration <remaining-duration-from-start> \
  --multilingual-lyrics \
  --advanced \
  --no-guitar-focus \
  --lyrics-guitar \
  --crf 12 \
  --preset ultrafast
```

## Cover Rule

For public songs, use a visually selected AgInTi/image-generation cover:

- 16:9 PNG, no text, logo, or watermark;
- matched to the song mood, place, instrument, and emotional color;
- visually inspected before committing and recording;
- referenced in `manifest.provenance.coverSource`.

Do not rely on procedural placeholder covers for public website items.

## Validation

Before recording:

```bash
node bin/musia.js fun-validate
node bin/musia.js fun-audit --media-id <media-id> --strict
node --check website/app.js
```

After recording:

```bash
ffprobe -v error -show_entries stream=codec_type,width,height,duration \
  -of default=nw=1 recorded_videos/<media-id>/<file>.mp4
```

The final MP4 should also be copied or synced to:

```text
/home/lachlan/Nutstore Files/Projects/Musia/
```
