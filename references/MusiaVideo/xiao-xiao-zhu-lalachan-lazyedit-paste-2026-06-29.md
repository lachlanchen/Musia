# Xiao Xiao Zhu LALACHAN And LazyEdit Paste Notes

Date: 2026-06-29

Use this as a copy/paste handoff for LALACHAN and LazyEdit.

## Key Links

Fun website:

```text
https://fun.lazying.art/#xiao-xiao-zhu-trilingual
```

MusiaSongs audio:

```text
https://lazyingart.github.io/MusiaSongs/audio/xiao-xiao-zhu-zh-Hans.mp3
https://lazyingart.github.io/MusiaSongs/audio/xiao-xiao-zhu-en.mp3
https://lazyingart.github.io/MusiaSongs/audio/xiao-xiao-zhu-ja.mp3
```

## Three Recorded Fun Player Videos

Nutstore copies for sharing/publishing:

```text
/home/lachlan/Nutstore Files/Projects/Musia/xiao-xiao-zhu-zh-Hans-portrait-4k.mp4
/home/lachlan/Nutstore Files/Projects/Musia/xiao-xiao-zhu-en-portrait-4k.mp4
/home/lachlan/Nutstore Files/Projects/Musia/xiao-xiao-zhu-ja-portrait-4k.mp4
```

Local originals:

```text
/home/lachlan/ProjectsLFS/Musia/recorded_videos/xiao-xiao-zhu/xiao-xiao-zhu-zh-Hans-portrait-4k.mp4
/home/lachlan/ProjectsLFS/Musia/recorded_videos/xiao-xiao-zhu/xiao-xiao-zhu-en-portrait-4k.mp4
/home/lachlan/ProjectsLFS/Musia/recorded_videos/xiao-xiao-zhu/xiao-xiao-zhu-ja-portrait-4k.mp4
```

Video facts:

```text
Chinese:  2160x3840, about 92.02s, AAC stereo, 320k, mean volume about -15.9 dB
English:  2160x3840, about 88.04s, AAC stereo, 319k, mean volume about -14.7 dB
Japanese: 2160x3840, about 82.04s, AAC stereo, 319k, mean volume about -14.0 dB
```

## Paste To LALACHAN

```text
Please generate a LALACHAN/Xiaoyunque MV for Musia song 你是一只猪 / Xiao Xiao Zhu.

Important creative direction:
- Aya Chan / 阿芽酱 is the red panda lead singer and camera center.
- Let Aya Chan sing most main vocal shots: front-facing singer shots, side profile, hand gestures, expressive performance.
- RaraXia, Sasa Kun, and Zhuangzi robot support as dancers, backing singers, comic reactions, and protectors of the small piggy cloud.
- 小小猪 is an affectionate cloud-pig rest mascot, not an insult.
- Keep music primary. Dialogue should be sparse and only in musical gaps.

Use this Musia handoff package:
/home/lachlan/ProjectsLFS/Musia/data/creative_projects/ni-shi-yi-zhi-zhu-20260629/mv/xiao-xiao-zhu-comfort-mv-20260629

Paste-ready Xiaoyunque prompt:
/home/lachlan/ProjectsLFS/LALACHAN/references/prompts/2026-06-29-xiao-xiao-zhu-full-mv-92s.md

LALACHAN-side handoff note:
/home/lachlan/ProjectsLFS/LALACHAN/references/MusiaVideo/xiao-xiao-zhu-mv-handoff-2026-06-29.md

Upload the normal LALACHAN references as 图1-图8:
图1 /home/lachlan/ProjectsLFS/LALACHAN/words-card.jpg
图2 /home/lachlan/ProjectsLFS/LALACHAN/LazyingArtRobot.png
图3 /home/lachlan/ProjectsLFS/LALACHAN/display.png
图4 /home/lachlan/ProjectsLFS/LALACHAN/patchwork-leather-notebook-luxury-clean-v2.png
图5 /home/lachlan/ProjectsLFS/LALACHAN/raraxia.jpeg
图6 /home/lachlan/ProjectsLFS/LALACHAN/ayachan.png
图7 /home/lachlan/ProjectsLFS/LALACHAN/sasakun.jpeg
图8 /home/lachlan/ProjectsLFS/LALACHAN/Trio.png

Upload the Musia Mandarin audio as 音频1:
/home/lachlan/ProjectsLFS/MusiaSongs/audio/xiao-xiao-zhu-zh-Hans.mp3

Preferred generation:
- Mode: 创作 Agent for full 92s MV.
- Ratio: 16:9 first.
- Subtitles: off.
- No lyrics/subtitles/file paths/watermarks in the generated image.

After Xiaoyunque returns a video, verify duration and audio. If Xiaoyunque changes the soundtrack, keep the visuals and mux the Musia MP3 back:
/home/lachlan/ProjectsLFS/LazySkills/skills/musia-lalachan-mv-workflow/scripts/mux_musia_audio.sh --video GENERATED_VIDEO.mp4 --audio /home/lachlan/ProjectsLFS/MusiaSongs/audio/xiao-xiao-zhu-zh-Hans.mp3 --output /home/lachlan/ProjectsLFS/LALACHAN/Videos/xiao_xiao_zhu_mv_song_locked_2026-06-29.mp4
```

## Paste To LazyEdit For Video Recording Publish

Use these when publishing the already-recorded Fun player videos as normal videos.

Chinese recording:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lazyedit
python scripts/lazyedit_publish.py \
  --video "/home/lachlan/Nutstore Files/Projects/Musia/xiao-xiao-zhu-zh-Hans-portrait-4k.mp4" \
  --title "你是一只猪 - Musia 中文版" \
  --use-current-settings \
  --prompt-file /home/lachlan/ProjectsLFS/Musia/references/MusiaVideo/xiao-xiao-zhu-lalachan-lazyedit-paste-2026-06-29.md \
  --publish-category musia \
  --no-burn-subtitles \
  --platforms shipinhao,youtube,instagram \
  --wait \
  --poll-seconds 10
```

English recording:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lazyedit
python scripts/lazyedit_publish.py \
  --video "/home/lachlan/Nutstore Files/Projects/Musia/xiao-xiao-zhu-en-portrait-4k.mp4" \
  --title "You Little Piggy - Musia English Version" \
  --use-current-settings \
  --prompt-file /home/lachlan/ProjectsLFS/Musia/references/MusiaVideo/xiao-xiao-zhu-lalachan-lazyedit-paste-2026-06-29.md \
  --publish-category musia \
  --no-burn-subtitles \
  --platforms shipinhao,youtube,instagram \
  --wait \
  --poll-seconds 10
```

Japanese recording:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lazyedit
python scripts/lazyedit_publish.py \
  --video "/home/lachlan/Nutstore Files/Projects/Musia/xiao-xiao-zhu-ja-portrait-4k.mp4" \
  --title "きみはこぶた - Musia 日本語版" \
  --use-current-settings \
  --prompt-file /home/lachlan/ProjectsLFS/Musia/references/MusiaVideo/xiao-xiao-zhu-lalachan-lazyedit-paste-2026-06-29.md \
  --publish-category musia \
  --no-burn-subtitles \
  --platforms shipinhao,youtube,instagram \
  --wait \
  --poll-seconds 10
```

## Paste To LazyEdit For Shipinhao Music-Only Publish

Use this for publishing the song as music, not as a video post. Start without `--post`, inspect the package, then rerun with `--post --shipinhao-music` when ready.

Package only:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lazyedit
python scripts/lazyedit_music_package.py \
  --audio /home/lachlan/ProjectsLFS/MusiaSongs/audio/xiao-xiao-zhu-zh-Hans.mp3 \
  --title "你是一只猪" \
  --author "Musia 慕莎" \
  --artist "Musia" \
  --language 中文 \
  --genre "Bedroom Pop" \
  --story "一首可爱又有一点撒娇的休息之歌。累了一天的人，也可以像小小猪一样，被允许休息、被照顾、慢慢呼吸。" \
  --description "Musia 原创中文歌曲《你是一只猪》。小小猪是温柔的休息精灵，唱给被作业、工作、论文和消息追着跑的人。" \
  --lyrics-json /home/lachlan/ProjectsLFS/Musia/website/data/songs/xiao-xiao-zhu-trilingual/lyrics/zh-vocal/zh-Hans.json \
  --cover /home/lachlan/ProjectsLFS/Musia/website/assets/covers/xiao-xiao-zhu-16x9.png \
  --cover-video "/home/lachlan/Nutstore Files/Projects/Musia/xiao-xiao-zhu-zh-Hans-portrait-4k.mp4" \
  --cover-count 9 \
  --cover-model codex \
  --proof /home/lachlan/ProjectsLFS/Musia/website/data/songs/xiao-xiao-zhu-trilingual/manifest.json \
  --source-url "https://fun.lazying.art/#xiao-xiao-zhu-trilingual" \
  --output-slug xiao-xiao-zhu-musia-music \
  --platforms shipinhao_music
```

After inspecting the package, publish to Shipinhao music only:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lazyedit
python scripts/lazyedit_music_package.py \
  --audio /home/lachlan/ProjectsLFS/MusiaSongs/audio/xiao-xiao-zhu-zh-Hans.mp3 \
  --title "你是一只猪" \
  --author "Musia 慕莎" \
  --artist "Musia" \
  --language 中文 \
  --genre "Bedroom Pop" \
  --story "一首可爱又有一点撒娇的休息之歌。累了一天的人，也可以像小小猪一样，被允许休息、被照顾、慢慢呼吸。" \
  --description "Musia 原创中文歌曲《你是一只猪》。小小猪是温柔的休息精灵，唱给被作业、工作、论文和消息追着跑的人。" \
  --lyrics-json /home/lachlan/ProjectsLFS/Musia/website/data/songs/xiao-xiao-zhu-trilingual/lyrics/zh-vocal/zh-Hans.json \
  --cover /home/lachlan/ProjectsLFS/Musia/website/assets/covers/xiao-xiao-zhu-16x9.png \
  --cover-video "/home/lachlan/Nutstore Files/Projects/Musia/xiao-xiao-zhu-zh-Hans-portrait-4k.mp4" \
  --cover-count 9 \
  --cover-model codex \
  --proof /home/lachlan/ProjectsLFS/Musia/website/data/songs/xiao-xiao-zhu-trilingual/manifest.json \
  --source-url "https://fun.lazying.art/#xiao-xiao-zhu-trilingual" \
  --output-slug xiao-xiao-zhu-musia-music \
  --platforms shipinhao_music \
  --post \
  --shipinhao-music
```

