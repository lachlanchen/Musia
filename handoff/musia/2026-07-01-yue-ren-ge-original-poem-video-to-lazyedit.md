# LazyEdit Video Handoff: 越人歌 · 原诗版

Created: 2026-07-01
Source repo: `/home/lachlan/ProjectsLFS/Musia`
Artist / musician: `Musia`
Website brand: `Fun Lazying Art`
Publishing category: `musia`
No publish has been done from Musia.

## Goal

Publish the corrected **4K portrait Fun Lazying Art player recording** for:

```text
越人歌 · 原诗版
```

This is a video/short/music-video style post, not a pure music upload. The video already contains the Fun Lazying Art player, cover, synced lyrics, pinyin/ruby-style lyric display, and the final corrected `不知` lyric tail.

## Selected Video

Use the Nutstore copy first for LazyEdit / AutoPublish import:

```text
/home/lachlan/Nutstore Files/Projects/Musia/yue-ren-ge-original-poem-zh-Hans-portrait-4k.mp4
```

Local source:

```text
/home/lachlan/ProjectsLFS/Musia/recorded_videos/yue-ren-ge-original-poem/yue-ren-ge-original-poem-zh-Hans-portrait-4k.mp4
```

Verified properties:

```text
Resolution: 2160x3840
Frame rate: 24 fps
Duration: 100.000s
Video: H.264, yuv420p
Audio: AAC stereo, 48 kHz, about 313 kbps
Volume: mean -15.1 dB, max -1.0 dB
File size: about 79 MB
```

## Public Website

```text
Fun URL: https://fun.lazying.art/#yue-ren-ge-original-poem
Media id: yue-ren-ge-original-poem
```

The public website JSON was corrected and verified after user review.

## LazyEdit Publish Settings

Recommended settings:

```text
publish_category: musia
platforms: youtube,instagram,shipinhao
subtitles: no LazyEdit subtitles by default
logo: enabled if this is the normal LazyEdit setting
logo_position: top-right
processing: logo-only if LazyEdit needs to process
```

Command-style intent:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lazyedit

python scripts/lazyedit_publish.py \
  --video "/home/lachlan/Nutstore Files/Projects/Musia/yue-ren-ge-original-poem-zh-Hans-portrait-4k.mp4" \
  --use-current-settings \
  --platforms youtube,instagram,shipinhao \
  --publish-category musia \
  --no-burn-subtitles \
  --logo \
  --logo-position top-right \
  --guided-monitor \
  --wait
```

Use `--no-publish` first if checking packaging:

```bash
python scripts/lazyedit_publish.py \
  --video "/home/lachlan/Nutstore Files/Projects/Musia/yue-ren-ge-original-poem-zh-Hans-portrait-4k.mp4" \
  --use-current-settings \
  --platforms youtube,instagram,shipinhao \
  --publish-category musia \
  --no-burn-subtitles \
  --logo \
  --logo-position top-right \
  --no-publish
```

Important:

- Do **not** burn extra LazyEdit subtitles by default. The video already shows corrected synced lyrics in the player.
- Keep the original audio track.
- If LazyEdit burns a logo, verify one sample frame before real publish.
- Do not re-transcribe and replace lyrics unless explicitly requested.
- Do not claim a real singer performed it.

## Suggested Metadata

Title:

```text
越人歌 · 原诗版 | Musia
```

Alternative English title:

```text
Song of the Yue Boatman - Original Poem | Musia
```

Chinese description:

```text
《越人歌 · 原诗版》由 Musia 生成并整理为一首中文古风歌曲。以先秦《越人歌》的意象为核心：月下同舟、隐秘心意、山木有枝、心悦君兮。视频录制自 Fun Lazying Art 播放器，使用修正后的同步歌词。
```

English description:

```text
Song of the Yue Boatman - Original Poem is a Musia ancient-style Mandarin song built from the pre-Qin poem 越人歌. The video was recorded from the Fun Lazying Art player with corrected synced lyrics.
```

Short hook:

```text
山有木兮木有枝，心悦君兮君不知。
```

Tags:

```text
Musia, Fun Lazying Art, 越人歌, 原诗版, 中文古风, AI音乐, 古诗成歌, lyric video, Chinese poetry, Song of the Yue Boatman
```

## Corrected Lyric Source

Corrected active Mandarin lyric JSON:

```text
/home/lachlan/ProjectsLFS/Musia/website/data/songs/yue-ren-ge-original-poem/lyrics/zh-vocal/zh-Hans.json
```

Optional translations:

```text
/home/lachlan/ProjectsLFS/Musia/website/data/songs/yue-ren-ge-original-poem/lyrics/zh-vocal/en.json
/home/lachlan/ProjectsLFS/Musia/website/data/songs/yue-ren-ge-original-poem/lyrics/zh-vocal/ja.json
```

Corrected visible lyric sequence:

```text
今夕何夕兮
搴舟中流
今日何日兮
得遇望之王子
山有木兮
木有枝
心悦君兮
君不知
心悦君兮
今夕何夕兮
搴舟中流
今日何日兮
得与王子同舟
蒙羞被好兮
不訾诟耻
心急烦而不绝兮
得知王子
山有木兮
木有枝
心悦君兮
君不知
山有木兮
木有枝
心悦君兮
不知
```

Lyric correction policy used:

```text
same phrase length + close sound + better source text => preserve source
different phrase length or clearly different structure => sound-close compromise
soft final tail heard by listening but swallowed by ASR => add it with conservative timing
```

User-reviewed corrections already applied:

```text
牵愁中流 -> 搴舟中流
心爱君兮 -> 心悦君兮
追不着 -> 君不知
final soft tail -> 不知
second 同舟 line -> 得与王子同舟
```

## Cover / Thumbnail

Use the website cover or let LazyEdit choose a strong frame from the player video:

```text
/home/lachlan/ProjectsLFS/Musia/website/assets/covers/yue-ren-ge-original-poem-16x9.png
```

If the platform needs a vertical thumbnail, choose a frame showing:

```text
Fun Lazying Art header
Musia
越人歌 · 原诗版
large current lyric panel
```

## Final Checklist

```text
[ ] Import the Nutstore 4K MP4.
[ ] Confirm the MP4 is 2160x3840 and has audio.
[ ] Do not burn extra subtitles.
[ ] If logo burn is enabled, use top-right and inspect a sample frame.
[ ] Set category to musia.
[ ] Use artist/musician name Musia.
[ ] Use corrected lyric context above, not raw ASR or prompt drafts.
[ ] Publish once after checking the package.
```
