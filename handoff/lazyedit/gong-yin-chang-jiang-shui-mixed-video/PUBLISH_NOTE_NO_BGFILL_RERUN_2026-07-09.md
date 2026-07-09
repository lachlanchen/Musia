# 共饮长江水 · Same River Native Portrait No-Bgfill Rerun

Date: 2026-07-09

## Result

Recorded and republished a native portrait Musia player video without portrait
bg-fill.

Platforms:

- Shipinhao video
- Instagram
- YouTube
- Douyin

LazyEdit:

- Video ID: `466`
- Publication session: `44`
- Publish job: `293`
- Remote AutoPublish job: `job-1783589234999-7`
- Remote ZIP: `gong-yin-chang-jiang-shui-mixed-lyrics-guitar-portrait-4k-native-nobgfill_session_44.zip`
- Status: `done`

## Source Video

Local:

```text
/home/lachlan/ProjectsLFS/Musia/recorded_videos/gong-yin-chang-jiang-shui-mixed/gong-yin-chang-jiang-shui-mixed-lyrics-guitar-portrait-4k-native-nobgfill.mp4
```

Nutstore:

```text
/home/lachlan/Nutstore Files/Projects/Musia/gong-yin-chang-jiang-shui-mixed-lyrics-guitar-portrait-4k-native-nobgfill.mp4
```

Media facts:

```text
width=2160
height=3840
duration=74.000s
audio=present
size=98M
sha256=62f2f86f45d8171310f11b654adac9bbec2cb0d2eb6c4fd973b7459e239bd75d
```

## Important Setting

This run used native portrait recording and explicitly disabled LazyEdit portrait
bg-fill:

```text
--no-portrait-blur-fill
```

The LazyEdit session config confirmed:

```json
"portraitBlurFill": {
  "enabled": false
}
```

Use this pattern for Musia Fun-player portrait recordings. Bg-fill should only
be used when converting non-portrait source videos, and then only with
foreground geometry that respects the source aspect ratio.

## Recording Command

```bash
PYTHONNOUSERSITE=1 conda run --no-capture-output -n musia python scripts/record_fun_player_realtime.py \
  --media-id gong-yin-chang-jiang-shui-mixed \
  --output recorded_videos/gong-yin-chang-jiang-shui-mixed/gong-yin-chang-jiang-shui-mixed-lyrics-guitar-portrait-4k-native-nobgfill.mp4 \
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

```bash
python scripts/lazyedit_publish.py \
  --video /home/lachlan/ProjectsLFS/Musia/recorded_videos/gong-yin-chang-jiang-shui-mixed/gong-yin-chang-jiang-shui-mixed-lyrics-guitar-portrait-4k-native-nobgfill.mp4 \
  --expect-sha256 62f2f86f45d8171310f11b654adac9bbec2cb0d2eb6c4fd973b7459e239bd75d \
  --expect-duration 74 \
  --duration-tolerance 0.5 \
  --expect-min-size-mb 90 \
  --expect-max-size-mb 120 \
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
  --no-portrait-blur-fill \
  --process \
  --new-run \
  --publish \
  --wait \
  --guided-monitor \
  --publish-timeout 1800 \
  --poll-seconds 10
```

Notes:

- Instagram crop was set to Original.
- Shipinhao collection `Musia` was not available in the live UI, so publishing
  continued without collection selection.
- YouTube playlist `Musia` creation/selection was attempted but the upload
  continued without playlist selection because the Studio dropdown did not expose
  it reliably.
