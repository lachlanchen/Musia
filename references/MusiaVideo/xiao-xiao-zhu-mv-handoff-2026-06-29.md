# Xiao Xiao Zhu MV Handoff

Date: 2026-06-29

This is the Musia-to-LALACHAN handoff for a music video based on the selected Mandarin version of **你是一只猪 / Xiao Xiao Zhu**.

## Decision

Use the Mandarin vocal as the master:

```text
data/creative_projects/ni-shi-yi-zhi-zhu-20260629/selected/ni-shi-yi-zhi-zhu-zh-master.wav
```

Public website item:

```text
https://fun.lazying.art/#xiao-xiao-zhu-trilingual
```

Public MP3:

```text
https://lazyingart.github.io/MusiaSongs/audio/xiao-xiao-zhu-zh-Hans.mp3
```

Recommended local upload audio for Xiaoyunque:

```text
../MusiaSongs/audio/xiao-xiao-zhu-zh-Hans.mp3
```

Recorded Fun player reference video:

```text
recorded_videos/xiao-xiao-zhu/xiao-xiao-zhu-zh-Hans-portrait-4k.mp4
```

## Song Facts

- Duration: about `92.0s`.
- Language: Mandarin Chinese.
- Artist: `Musia`.
- BPM: about `103.36`.
- Detected key guide: `A major / detected guide`.
- Mood: cute, joyful, slightly whiny, warm, bedroom-pop comfort.
- Theme: tired people wanting one soft night without work, homework, papers, messages, or pressure.

## MV Concept

Treat `小小猪` as an affectionate mascot, not an insult.

Story: the four buddies are tired by homework, messages, reports, and deadlines. A soft little piggy cloud appears and opens a warm blanket world. A harmless but annoying `deadline storm` made of alarm clocks, paper sheets, and notification bubbles chases them. The team does not fight violently; they turn the storm quiet by singing, dancing, building a cloud-bed shelter, and choosing rest for one night. The ending is warm: the world is still heavy, but everyone learns to breathe, sleep, and keep going tomorrow.

## LALACHAN Character Roles

- 阿芽酱: red panda lead singer and camera center; most vocal lines should return to her face, gestures, and performance.
- 啦啦侠: warm and brave, slightly hungry, protects the tiny piggy cloud.
- 飒飒君: quick movement and comic reactions; dodges notification bubbles.
- 庄子机器人: precise and dry; uses a tiny `quiet mode` remote and blanket-shield.
- 小小猪: soft cloud-pig mascot, round and sleepy; can float, hum, and glow.

## Section Timing

```text
00.00-08.69  Intro: quiet bedroom, desk, night window, tiny piggy cloud appears.
08.69-17.63  Verse 1: the piggy cloud is happy and sleepy; characters notice its easy joy.
18.41-27.91  Pre-chorus: pressure world gets quieter; characters enter the cloud-bed room.
27.91-43.99  Chorus 1: dance, blanket shelter, no homework/no work fantasy.
44.79-53.37  Verse 2: alarm clocks and messages become a deadline storm.
54.23-62.59  Bridge: characters admit they are tired, then choose to breathe.
62.59-80.07  Final chorus: warm group dance; storm turns into soft pillows and stars.
81.63-89.29  Outro: sleepy piggy hum, lights fade, everyone rests.
89.29-92.00  Tail: soft ending, no extra dialogue.
```

## Handoff Package

Versioned prompt copy:

```text
references/MusiaVideo/xiao-xiao-zhu-full-mv-prompt-2026-06-29.md
```

Local working package on this machine:

```text
data/creative_projects/ni-shi-yi-zhi-zhu-20260629/mv/xiao-xiao-zhu-comfort-mv-20260629
```

Files:

- `README.md` - package overview.
- `STORY.md` - story, roles, and timing.
- `XYQ_PROMPT_FULL_MV.md` - paste-ready Xiaoyunque prompt.
- `SEGMENTS.json` - machine-readable section timing.
- `ASSET_LIST.md` - upload order.
- `SOUND_MIX_NOTES.md` - song-locked audio instructions.
- `PROMPT_SHORT_AGENT_MESSAGE.md` - short handoff message for LALACHAN Codex.
- `MUSIA_LALACHAN_MV_HANDOFF.json` - machine-readable paths and metadata.

## Xiaoyunque Setup

Recommended:

```text
Mode: 创作 Agent for full 92s MV, or 沉浸式短片 for a 15-30s chorus test.
Ratio: 16:9 for full MV first; make portrait social cut later with LazyEdit.
Audio: upload the Musia MP3 as 音频1.
Images: upload the normal LALACHAN references as 图1-图8.
Subtitles: off. Prompt explicitly says no subtitles, no lyric text, no file names.
```

## Expected Finalization

If Xiaoyunque changes the song audio, mux the Musia MP3 back into the generated video:

```bash
export MUSIA_ROOT="${MUSIA_ROOT:-/home/lachlan/ProjectsLFS/Musia}"
export LALACHAN_ROOT="${LALACHAN_ROOT:-/home/lachlan/ProjectsLFS/LALACHAN}"
export LAZYSKILLS_ROOT="${LAZYSKILLS_ROOT:-/home/lachlan/ProjectsLFS/LazySkills}"

"$LAZYSKILLS_ROOT/skills/musia-lalachan-mv-workflow/scripts/mux_musia_audio.sh" \
  --video "$LALACHAN_ROOT/Videos/xiao_xiao_zhu_mv_xyq_2026-06-29.mp4" \
  --audio "$MUSIA_ROOT/../MusiaSongs/audio/xiao-xiao-zhu-zh-Hans.mp3" \
  --output "$LALACHAN_ROOT/Videos/xiao_xiao_zhu_mv_song_locked_2026-06-29.mp4"
```

Verify:

```bash
ffprobe -v error -show_entries format=duration -show_streams \
  "$LALACHAN_ROOT/Videos/xiao_xiao_zhu_mv_song_locked_2026-06-29.mp4"
```
