# 梦游天姥吟留别 Hook ACE Generation - 2026-07-06

## Goal

Generate a beautiful, complete Mandarin song for Li Bai's `梦游天姥吟留别`, with
correct `天姥` pronunciation. The public lyric keeps `天姥山`; the model-facing
lyric uses `天母山` only as a pronunciation-control spelling for `tian1 mu3
shan1`, preventing the common `lao3 mu3` misread.

## Selected Candidate

- Project: `data/creative_projects/meng-you-tian-mu-yin-liu-bie-selected-20260706`
- Selected WAV: `data/creative_projects/meng-you-tian-mu-yin-liu-bie-selected-20260706/selected/meng-you-tian-mu-yin-liu-bie-zh-Hans-ace-xl-turbo-hook-seed741402.wav`
- Selected MP3: `data/creative_projects/meng-you-tian-mu-yin-liu-bie-selected-20260706/selected/meng-you-tian-mu-yin-liu-bie-zh-Hans-ace-xl-turbo-hook-seed741402.mp3`
- Model: `acestep-v15-xl-turbo`
- Seed: `741402`
- Duration: `82s`
- BPM/key: `82 BPM`, `D minor`, `4/4`
- Route: hook-focused ACE route with fewer words and more musical space.

## Public Lyric

The public lyric is:

```text
海上烟涛
远到难求
有人说天姥山
云霞在尽头

我乘一夜月
飞过镜湖秋
月光照着我
送我向山流

青云梯
青云梯
海日升
天鸡鸣

梦游天姥山
梦到云天外
万山为我开
我心不尘埃

雷声起
石门开
日月照金台
仙人踏风来

世间万事
东流入海
安能低眉折腰
让我不得开心颜

梦游天姥山
梦到云天外
万山为我开
我心不尘埃

梦醒之后
我仍向名山
梦醒之后
我心更高远
```

## Candidate Checks

Exact/source-heavy and medium-density versions were tried first, but the ASR
recovered fewer reliable lyric anchors. The best new candidate came from the
hook-focused route:

| Route | Seed | ASR model | Overlap | Note |
| --- | ---: | --- | ---: | --- |
| Standard long lyric | 741237 | small | 0.216 | More source content, weaker lyric recovery |
| Compact standard | 741264 | small | 0.246 | Cleaner density, still not strong enough |
| Compact repro | 741224 | small | 0.261 | Fresh render, did not beat earlier legacy pass |
| Hook-focused | 741402 | tiny | 0.301 | Best new candidate; selected for full analysis |

Full analysis run:

```text
data/runs/meng-you-tian-mu-yin-liu-bie-selected-hook-741402-analysis
```

Artifacts include:

```text
stems/vocals.wav
stems/drums.wav
stems/bass.wav
stems/other.wav
stems/instrumental.wav
stems/human_sound.wav
analysis/chords.csv
analysis/beats.csv
analysis/lyrics.txt
analysis/lyrics.json
```

## Quality Caveat

This candidate is the best new render from the run, and the `天姥` pronunciation
control worked in the important sense that ASR heard `tian-mu`-like variants
(`天幕` / `天母` / `天无`) rather than `lao-mu`. It is not yet a final
publication-grade lyric-aligned website item: the active lyric JSON still needs
manual post-correction against listening/ASR before publishing or recording.

For public website or Shipinhao Music use, do not use the prompt lyric directly.
Prepare the Fun item from the selected audio, then correct line timing and text
against the selected render.

## Website Item

The Fun website item was prepared after user request with the corrected audible
structure rather than the full prompt lyric:

Visible website title:

```text
梦游天姥吟留别 · 青云梯改编版
```

This selected render is a hook-focused adaptation, not the original-poem
version, so it must not use the pure poem title on the public website.

```text
website/data/songs/meng-you-tian-mu-yin-liu-bie/manifest.json
website/data/songs/meng-you-tian-mu-yin-liu-bie/lyrics/zh-vocal/zh-Hans.json
website/data/songs/meng-you-tian-mu-yin-liu-bie/lyrics/zh-vocal/en.json
website/data/songs/meng-you-tian-mu-yin-liu-bie/lyrics/zh-vocal/ja.json
```

Public audio in the media repo:

```text
../MusiaSongs/audio/meng-you-tian-mu-yin-liu-bie-zh-Hans-ace-xl-turbo-hook-seed741402-20260706.mp3
https://lazyingart.github.io/MusiaSongs/audio/meng-you-tian-mu-yin-liu-bie-zh-Hans-ace-xl-turbo-hook-seed741402-20260706.mp3
```

The corrected active lyric is intentionally short because the selected render
only clearly recovers the opening and hook sections:

```text
海上烟涛，远到难求
有人说天姥山，云霞在尽头
我乘一夜月，飞过镜湖秋
月光照着我，送我向山流
梦游天姥山
梦到云天外
万山为我开
我心不尘埃
梦游天姥山
万山为我开
```

Validation:

```bash
node bin/musia.js fun-validate
node bin/musia.js fun-audit --media-id meng-you-tian-mu-yin-liu-bie
```

Both passed on 2026-07-06.
