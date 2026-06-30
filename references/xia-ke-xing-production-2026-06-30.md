# 侠客行 Production Note - 2026-06-30

## Source

- Poem: 《侠客行》 by Li Bai, Tang dynasty.
- Use: public-domain source text adapted into a modern Musia wuxia theme song.

## Generation Route

- Model route: ACE-Step 1.5 XL Turbo.
- Selected render: `data/creative_projects/xia-ke-xing-20260630/ace_outputs/zh_corrected_20260630-231230/5f973ed3-5012-047c-e4e4-736d1b72c4c2.wav`
- Selected MP3: `data/creative_projects/xia-ke-xing-20260630/selected/xia-ke-xing-zh-Hans-ace-20260630.mp3`
- Public audio mirror: `../MusiaSongs/audio/xia-ke-xing-zh-Hans-ace-20260630.mp3`
- Website item: `website/data/songs/xia-ke-xing/manifest.json`

## Quality Decision

Several ACE candidates were generated and reviewed. The final tight lyric pass was selected because it preserved the most important musical identity:

- 长风 / 白马
- 月下剑光明
- 霜雪 / 吴钩
- 三杯酒 / 一诺定
- 不留姓名
- repeated 侠客行 hook

ASR overlap is still low, so the website lyrics are not the full planned prompt lyric. The published lyric JSON follows the actual vocal structure, with sound-close corrections only where the input lyric and context are clearly stronger, especially `侠客行` for ASR variants such as `夏可熏`.

## Analysis Artifacts

- Analysis run: `data/runs/xia-ke-xing-20260630-20260630-231322-analysis/`
- Stems: `data/runs/xia-ke-xing-20260630-20260630-231322-analysis/stems/`
- Lyrics ASR: `data/runs/xia-ke-xing-20260630-20260630-231322-analysis/analysis/lyrics.json`
- Chords: `data/runs/xia-ke-xing-20260630-20260630-231322-analysis/analysis/chords.csv`
- Beats: `data/runs/xia-ke-xing-20260630-20260630-231322-analysis/analysis/beats.csv`

## Website Data

- Manifest: `website/data/songs/xia-ke-xing/manifest.json`
- Active Mandarin lyric track: `website/data/songs/xia-ke-xing/lyrics/zh-vocal/zh-Hans.json`
- English translation: `website/data/songs/xia-ke-xing/lyrics/zh-vocal/en.json`
- Japanese translation with furigana metadata: `website/data/songs/xia-ke-xing/lyrics/zh-vocal/ja.json`
- Cover: `website/assets/covers/xia-ke-xing-16x9.png`
- Prep script: `scripts/prepare_xia_ke_xing_fun_item.py`

## Recording

Target output:

`recorded_videos/xia-ke-xing/xia-ke-xing-zh-Hans-portrait-4k.mp4`

The recorder uses local cached audio for browser playback when the manifest points to a freshly pushed GitHub Pages URL that has not propagated yet.
