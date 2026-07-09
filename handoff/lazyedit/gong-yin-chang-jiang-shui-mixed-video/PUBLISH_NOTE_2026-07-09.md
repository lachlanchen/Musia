# 共饮长江水 · Same River Video Publish Note

Date: 2026-07-09

## Result

Published the corrected Musia portrait player video through LazyEdit and remote
AutoPublish.

Platforms:

- Shipinhao video
- Instagram
- YouTube
- Douyin

LazyEdit:

- Video ID: `465`
- Publication session: `43`
- Publish job: `292`
- Remote AutoPublish job: `job-1783587685696-6`
- Remote ZIP: `gong-yin-chang-jiang-shui-mixed-lyrics-guitar-portrait-4k-realtime-corrected_session_43.zip`
- Status: `done`

## Source Video

Local:

```text
/home/lachlan/ProjectsLFS/Musia/recorded_videos/gong-yin-chang-jiang-shui-mixed/gong-yin-chang-jiang-shui-mixed-lyrics-guitar-portrait-4k-realtime-corrected.mp4
```

Nutstore sync:

```text
/home/lachlan/Nutstore Files/Projects/Musia/gong-yin-chang-jiang-shui-mixed-lyrics-guitar-portrait-4k-realtime-corrected.mp4
```

Media facts:

```text
width=2160
height=3840
duration=74.000s
audio=present
size=103M
sha256=f1ebc03029ae9974a985c4277c538021c2b561b2ca32b1dcc6f65037d8195085
```

## Corrected Lyric Source

Use the corrected website active lyric JSON as the source of truth:

```text
/home/lachlan/ProjectsLFS/Musia/website/data/songs/gong-yin-chang-jiang-shui-mixed/lyrics/mixed-vocal/mul.json
```

Final corrected tail:

```text
54.06-57.82 Zhi yuan jun xin si wo xin
57.82-61.20 Ding bu fu xiang si yi
61.20-65.95 Same river, same longing
65.95-69.80 Give me all
69.80-74.04 ♪
```

Companion translations are in:

```text
website/data/songs/gong-yin-chang-jiang-shui-mixed/lyrics/mixed-vocal/en.json
website/data/songs/gong-yin-chang-jiang-shui-mixed/lyrics/mixed-vocal/ja.json
website/data/songs/gong-yin-chang-jiang-shui-mixed/lyrics/mixed-vocal/zh-Hans.json
```

Validation before recording:

```bash
node bin/musia.js fun-validate
node bin/musia.js fun-audit --media-id gong-yin-chang-jiang-shui-mixed
```

Both passed.

## Recording Command

Used the fast realtime recorder, not the slow deterministic frame renderer:

```bash
PYTHONNOUSERSITE=1 conda run --no-capture-output -n musia python scripts/record_fun_player_realtime.py \
  --media-id gong-yin-chang-jiang-shui-mixed \
  --output recorded_videos/gong-yin-chang-jiang-shui-mixed/gong-yin-chang-jiang-shui-mixed-lyrics-guitar-portrait-4k-realtime-corrected.mp4 \
  --width 2160 --height 3840 \
  --css-width 1080 --css-height 1920 \
  --device-scale-factor 2 \
  --fps 24 \
  --start 0 \
  --duration 74 \
  --multilingual-lyrics \
  --advanced \
  --no-guitar-focus \
  --lyrics-guitar \
  --publication-layout \
  --capture-clock \
  --crf 12 \
  --preset ultrafast
```

## Publish Command

The first LazyEdit publish attempt used unsupported alias `sph`; the video was
processed correctly but platform submission failed. The accepted video platform
names are `shipinhao`, `instagram`, `youtube`, and `douyin`.

Successful publish reused `video_id=465` and submitted with `--no-process`:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit
python scripts/lazyedit_publish.py \
  --video-id 465 \
  --title '共饮长江水 · Same River - Musia' \
  --source musia \
  --platforms shipinhao,instagram,youtube,douyin \
  --publish-category musia \
  --youtube-playlist Musia \
  --shipinhao-collection Musia \
  --metadata-prompt-file /home/lachlan/ProjectsLFS/Musia/temp/gong-yin-chang-jiang-shui-mixed/VIDEO_METADATA_BRIEF.md \
  --no-correct-subtitles \
  --no-burn-subtitles \
  --logo --logo-position top-right \
  --no-process \
  --new-run \
  --publish \
  --wait \
  --guided-monitor \
  --publish-timeout 1800 \
  --poll-seconds 10
```

Metadata was listener-facing only: song title, Musia artist, Li Zhiyi/Yangtze
context, and the river-longing mood. It did not include ASR/VAD/pipeline/debug
details.

## Music Publish Status

This note covers the video publish only. Shipinhao Music has not been published
yet for this corrected lyric pass. When publishing music, use the corrected
website active lyric JSON above, not the original prompt.
