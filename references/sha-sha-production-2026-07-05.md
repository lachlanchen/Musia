# 沙沙 Production Note

Date: 2026-07-05

## Request

Generate a beautiful soft song named `沙沙`: two people walk on the beach and
watch the sun. Keep the user's seed images:

```text
沙沙
大海的沙
沙漠的沙
好多的沙
数不尽

沙沙
风吹到千叶海边
轻指楼兰姑娘面庞
```

The user also asked to show `陌上桑` from Han Yuefu. The reference text was saved
at:

```text
data/creative_projects/sha-sha-20260705/source/moshang-sang-reference.md
```

## Finished Lyric Plan

The generation-facing lyric was refined into a soft Mandarin beach ballad with
short lines and repeated `沙沙` hooks:

```text
沙沙，沙沙
大海的沙
沙漠的沙
好多的沙
数不尽它

你牵着我
沿着浪花
太阳把影子
拉得很长

风吹到千叶海边
轻指楼兰姑娘面庞
你笑着说
世界很大
可此刻只装得下
我们俩

沙沙，沙沙
海浪说悄悄话
沙沙，沙沙
夕阳落在肩上
大海的沙
沙漠的沙
数不清的远方
都在你眼里发光

我们慢慢走
不问明天啊
贝壳睡在月光下
楼兰的风
吹过海角
把孤单吹成花

沙沙，沙沙
海浪说悄悄话
沙沙，沙沙
太阳慢慢落下
我们看着太阳
一起回家
```

## Generation Attempts

All attempts used local ACE-Step 1.5 checkpoints.

1. `xl_turbo_soft_sweep`, 96s, seeds `750501-750504`.
   - Rejected as final because only one seed recovered a partial lyric; one seed
     produced unrelated platform-style chatter.
2. `xl_turbo_compact_clean`, 76s, seeds `750521-750524`.
   - Rejected because ASR recovered even less lyric despite shorter text.
3. `xl_sft_soft_single`, 96s, seed `750511`.
   - Rejected because large-v3 ASR recovered no useful lyric.
4. `xl_turbo_front_vocal_balanced`, 88s, seeds `731231`, `750531`,
   `750532`, `750533`.
   - Selected seed `750531` because it recovered the core song structure and
     had complete stems/chords/beats from the pipeline.

## Selected Audio

```text
data/creative_projects/sha-sha-20260705/selected/sha-sha-zh-ace-xl-turbo-seed750531.wav
data/creative_projects/sha-sha-20260705/selected/sha-sha-zh-ace-xl-turbo-seed750531.mp3
```

Public copy:

```text
../MusiaSongs/audio/sha-sha-zh-Hans-ace-xl-turbo-seed750531-20260705.mp3
```

## Analysis Artifacts

```text
data/runs/sha-sha-f641-balanced-analysis/
data/runs/sha-sha-f641-balanced-analysis/stems/vocals.wav
data/runs/sha-sha-f641-balanced-analysis/stems/drums.wav
data/runs/sha-sha-f641-balanced-analysis/stems/bass.wav
data/runs/sha-sha-f641-balanced-analysis/stems/other.wav
data/runs/sha-sha-f641-balanced-analysis/stems/instrumental.wav
data/runs/sha-sha-f641-balanced-analysis/analysis/lyrics.json
data/runs/sha-sha-f641-balanced-analysis/analysis/chords.csv
data/runs/sha-sha-f641-balanced-analysis/analysis/beats.csv
```

## Website Item

```text
website/data/songs/sha-sha/manifest.json
website/data/songs/sha-sha/lyrics/zh-vocal/zh-Hans.json
website/data/songs/sha-sha/lyrics/zh-vocal/en.json
website/data/songs/sha-sha/lyrics/zh-vocal/ja.json
website/assets/covers/sha-sha-16x9.png
```

Validation:

```bash
node bin/musia.js fun-validate
```

Result: `ok: website follows fun.lazying.media.v1`.

## ASR Correction

The public Chinese lyric uses the Demucs-separated vocal large-v3 ASR as the
main evidence, but it does not blindly accept every ASR word.

Active public lyric:

```text
沙沙，沙沙，大海的沙
沙漠的沙，好多的沙，数不尽它
你牵着我，沿着浪花
风吹到千叶海边，轻指楼兰姑娘面庞
你笑着说，世界很大
可此刻只装得下，我们俩
夕阳落在肩上
沙沙，沙沙，海浪说悄悄话
沙沙，沙沙，太阳慢慢落下
```

Correction decisions:

- Restored `沙沙` from ASR `傻傻` because the title/hook is sound-close and more
  beautiful.
- Restored `大海的沙` from ASR `到海的沙`.
- Kept `好多的沙` for the second phrase after user listening review. The ASR
  repetition `沙漠的沙，沙漠的沙` is close enough that the intended lyric should
  win.
- Kept `轻指楼兰姑娘面庞` instead of the nearby ASR guesses `亲着/倾着楼栏姑娘面旁`.
  `楼兰` and `轻指` are sound-close to the generated vocal and preserve the
  intended image: a gentle pointing/touching gesture, not a kiss.
- Omitted planned lines not recovered in the selected render.

## 2026-07-05 User Listening Correction

The user rechecked the selected song and confirmed two close-ASR corrections:

- line `l02`: publish `沙漠的沙，好多的沙，数不尽它`, not the repeated
  `沙漠的沙，沙漠的沙，数不尽它`;
- line `l04`: restore `轻指楼兰姑娘面庞`; `轻指` is the intended gentle pointing
  image and should not be corrected to `亲着`.

This follows the Musia correction policy: when ASR and listening are close, and
the source lyric is more beautiful and semantically intended, preserve the
source lyric.

The English and Japanese translation tracks were regenerated from
`scripts/prepare_sha_sha_fun_item.py`, and `node bin/musia.js fun-validate`
passed.
