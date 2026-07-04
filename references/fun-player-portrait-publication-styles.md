# Fun Player Portrait Publication Styles

Use these standard styles when recording Musia player videos for publication.

## Styles

```text
lyrics-only
  Top: full-width Fun Lazying Art / Musia player.
  Bottom: current multilingual lyric block only.
  Use when the publication is mainly a lyric video or language-learning clip.

fingering-only
  Top: full-width player.
  Bottom: chord carousel and large guitar fingering.
  Use when the publication is mainly a chord/guitar demonstration.

lyrics+fingering
  Top: full-width player.
  Bottom: current multilingual lyric block, then guitar fingering in the
  remaining portrait space.
  Use when the lyric layout is already good but the lower capture has unused
  room.
```

## Realtime 4K Commands

Lyrics only:

```bash
PYTHONNOUSERSITE=1 conda run --no-capture-output -n musia python scripts/record_fun_player_realtime.py \
  --media-id <media-id> \
  --asset-id <asset-id> \
  --output recorded_videos/<media-id>/<name>-lyrics.mp4 \
  --duration <seconds> \
  --multilingual-lyrics \
  --no-advanced \
  --no-guitar-focus
```

Fingering only:

```bash
PYTHONNOUSERSITE=1 conda run --no-capture-output -n musia python scripts/record_fun_player_realtime.py \
  --media-id <media-id> \
  --asset-id <asset-id> \
  --output recorded_videos/<media-id>/<name>-fingering.mp4 \
  --duration <seconds> \
  --advanced \
  --guitar-focus
```

Lyrics plus fingering:

```bash
PYTHONNOUSERSITE=1 conda run --no-capture-output -n musia python scripts/record_fun_player_realtime.py \
  --media-id <media-id> \
  --asset-id <asset-id> \
  --output recorded_videos/<media-id>/<name>-lyrics-guitar.mp4 \
  --duration <seconds> \
  --multilingual-lyrics \
  --advanced \
  --no-guitar-focus \
  --lyrics-guitar
```

## Layout Rule

Do not change lyric content to make room for fingering. Preserve the corrected
lyrics and timing. Use otherwise empty portrait space first; reduce type only
when text genuinely overflows.

