# MusiaVideo

MusiaVideo is the song-first bridge from Musia to LALACHAN/Xiaoyunque MV generation.

The practical idea is simple:

```text
Musia song or 15s hook
-> reviewed audio reference and lyrics/beat intent
-> Xiaoyunque visual MV with LALACHAN character references
-> optional ffmpeg audio replacement so the final video uses the exact Musia track
```

This is feasible now with the local repos. Musia can create and review song/audio assets. LALACHAN already has the controlled browser/noVNC workflow for Xiaoyunque on CDP port `9222` with profile `~/.cache/xyq-chrome`.

## Current Best Route

Use Musia as the authority for music. Use Xiaoyunque as the authority for video imagery.

1. Create or select a Musia song section.
2. Export a 15s MV pack.
3. Upload the pack audio plus LALACHAN reference images in the controlled browser.
4. Generate `沉浸式短片`, usually `15s`, `4:3`.
5. If Xiaoyunque changes the audio, replace the video audio with the Musia audio reference.

## Full MV vs Chorus Cut

Use this research note when deciding whether to generate the whole song or only the 副歌 / 高潮部分:

```text
references/MusiaVideo/mv-style-research-full-vs-chorus-2026-06-29.md
```

Current decision for **Aya Chan Hikari Ame**: create the full `68.04s` MV first, because the hope/rain/battle concept needs a complete story arc. A chorus/highlight cut can be derived later as a social teaser.

## Prepare A Pack

From this repo:

```bash
node bin/musia.js mv-pack \
  --audio data/soulx_verses/rain-day-english-short-verse-20260628/mix.wav \
  --title "Four Buddies Rain Day" \
  --slug four-buddies-rain-day-15s \
  --duration 15 \
  --ratio 4:3 \
  --copy-references
```

The direct script entrypoint is `python3 scripts/prepare_lalachan_mv_pack.py` and accepts the same arguments.

The generated pack is ignored by git under `data/mv_packs/`. It contains:

- `audio/<slug>-15s.mp3`
- `PROMPT_XYQ.md`
- `MUSIA_LALACHAN_MV_HANDOFF.json`
- `replace_video_audio.sh`
- copied LALACHAN reference images when `--copy-references` is used

## Run LALACHAN Browser

From `../LALACHAN`:

```bash
PORT=9222 PROFILE_DIR="$HOME/.cache/xyq-chrome" \
  scripts/xyq_chrome/launch_chrome.sh

scripts/xyq_cdp_browser.py list-pages
scripts/xyq_cdp_browser.py visible PAGE_ID
```

Use the prompt from the pack. Upload the copied reference images and the pack audio if the Xiaoyunque UI accepts audio attachments in that mode.

## Final Audio Replacement

If the generated video does not preserve the exact Musia soundtrack:

```bash
cd data/mv_packs/four-buddies-rain-day-15s
./replace_video_audio.sh GENERATED_VIDEO.mp4 four-buddies-rain-day-final.mp4
```

This keeps the video stream and replaces only the audio track with the reviewed Musia song.

## Known Limits

- Xiaoyunque may treat uploaded audio as a mood/reference file rather than an exact soundtrack.
- Browser automation can set file inputs, but the visible UI still needs verification before submit.
- Audio-driven lip sync is not guaranteed; use this as an MV/rhythm/mood pipeline, not frame-accurate mouth animation.
- Do not spend Xiaoyunque credits until the prompt, attachments, ratio, duration, and mode are verified.

## Recommended First Proof

Use an existing short Musia vocal clip for a low-risk proof:

```text
data/soulx_verses/rain-day-english-short-verse-20260628/mix.wav
data/soulx_verses/rain-day-bilingual-verse/mix.wav
```

For a higher-quality proof, trim a selected full song section from `data/creative_projects/`, run the packer, and then use the replacement-audio step after video generation.

## Current Full MV Handoff

Aya Chan Hikari Ame now has a full-length hope/battle MV package:

```text
/home/lachlan/ProjectsLFS/Musia/data/creative_projects/aya-chan-hikari-ame-20260628/mv/hikari-ame-full-hope-battle-20260629
```

Reference summary:

```text
/home/lachlan/ProjectsLFS/Musia/references/MusiaVideo/aya-chan-hikari-ame-full-mv-handoff-2026-06-29.md
```

Use this package when LALACHAN should create the 68-second MV with 阿芽酱, 啦啦侠, 飒飒君, 庄子机器人, light rain, a fantasy storm dinosaur/monster attack, and the rally line `冲啊冲啊`.
