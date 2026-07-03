# Star Bucks Advanced Guitar Recording To LazyEdit

Video type: Musia / Fun Lazying Art website recording.

Publish targets: YouTube and Instagram only.

Required processing:

- no LazyEdit subtitles;
- burn the existing LazyEdit logo at top-right;
- use the video audio as-is;
- publish category: `musia`;
- this is a video/art-post publish, not a pure music-platform package.

Song metadata:

- Title: Star Bucks
- Artist: Musia
- Site/brand: Fun Lazying Art
- Language: English vocal with visible Chinese and Japanese translation support in the Musia player.
- Style: cinematic ocean-pop / indie anthem, hopeful, moonlit, spacious, resilient.
- Story: a lone sailor leaves the harbor at night, listens to the stars, wind, and waves, sees luminous star-deer crossing the sea, and keeps going through dark water.
- Hook: star-deer swim across midnight waves and remind the sailor to carry on.
- Website: https://fun.lazying.art/#star-bucks
- Data source: `/home/lachlan/ProjectsLFS/Musia/website/data/songs/star-bucks/manifest.json`
- Corrected active lyrics: `/home/lachlan/ProjectsLFS/Musia/website/data/songs/star-bucks/lyrics/en-vocal/en.json`

Suggested viewer-facing title:

```text
Star Bucks | Musia Ocean Anthem with Guitar Chords
```

Suggested description:

```text
Star Bucks is an original Musia ocean anthem on Fun Lazying Art: moonlit water, a lone sailor, luminous star-deer, synced lyrics, chords, and guitar fingering.
```

Suggested tags:

```text
Musia, Fun Lazying Art, original song, AI music, ocean anthem, guitar chords, indie pop, hope, lyrics, Star Bucks
```

LazyEdit command shape:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit
PYTHONNOUSERSITE=1 conda run -n lazyedit python scripts/lazyedit_publish.py \
  --video /home/lachlan/ProjectsLFS/Musia/recorded_videos/star-bucks/star-bucks-advanced-guitar-portrait-4k.mp4 \
  --title "Star Bucks | Musia Ocean Anthem with Guitar Chords" \
  --platforms youtube,instagram \
  --no-burn-subtitles \
  --logo \
  --logo-position top-right \
  --publish-category musia \
  --metadata-prompt-file /home/lachlan/ProjectsLFS/Musia/handoff/lazyedit/2026-07-03-star-bucks-advanced-guitar-video-to-lazyedit.md \
  --no-publish \
  --wait
```

## Publish Result

Published on 2026-07-03 through LazyEdit / AutoPublish.

- Local LazyEdit video id: `437`
- Local LazyEdit publish job id: `261`
- Remote AutoPublish job id: `job-1783011336974-4`
- Platforms: YouTube and Instagram only
- LazyEdit subtitles: disabled
- Logo: enabled, top-right
- Published MP4 source: `/home/lachlan/DiskMech/Projects/lazyedit/DATA/star-bucks-advanced-guitar-portrait-4k/star-bucks-advanced-guitar-portrait-4k_logo.mp4`
- Publish ZIP: `/home/lachlan/DiskMech/Projects/lazyedit/DATA/star-bucks-advanced-guitar-portrait-4k/publish/star-bucks-advanced-guitar-portrait-4k.zip`

Note: a duplicate direct publish request was briefly queued during recovery and
was stopped during the duplicate Instagram start before confirmation. The
remote AutoPublish service was restarted afterward and the queue was verified
empty.

## Subtitle Publish Result

Published again on 2026-07-03 with burned subtitles.

- Local LazyEdit video id: `437`
- Publication session id: `23`
- Remote AutoPublish job id: `job-1783047929968-1`
- Platforms: YouTube and Instagram only
- Subtitle mode: burned, compact English line
- Logo: enabled, top-right
- Published MP4 source: `/home/lachlan/DiskMech/Projects/lazyedit/DATA/star-bucks-advanced-guitar-portrait-4k/publications/session_23/star-bucks-advanced-guitar-portrait-4k_session_23_subtitles_logo.mp4`
- Publish ZIP: `/home/lachlan/DiskMech/Projects/lazyedit/DATA/star-bucks-advanced-guitar-portrait-4k/publications/session_23/publish/star-bucks-advanced-guitar-portrait-4k_session_23.zip`

The first subtitle burn session (`22`) used EN/JA/ZH subtitles and was rejected
for publishing because the subtitle stack covered too much of the guitar
fingering panel. Session `23` uses a compact English subtitle track so the
advanced guitar view stays readable.
