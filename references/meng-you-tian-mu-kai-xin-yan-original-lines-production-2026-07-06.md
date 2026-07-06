# 梦游天姥吟留别 · 开心颜原文段 Production Note

Date: 2026-07-06

## Goal

Generate a song from the ending excerpt of 李白《梦游天姥吟留别》 with no modern
adaptation. Repetition and small reordering were allowed, but the lyric source
had to remain original poem wording or original poem fragments.

Source excerpt:

```text
忽魂悸以魄動，怳驚起而長嗟。
惟覺時之枕席，失向來之煙霞。
世間行樂亦如此，古來萬事東流水。
別君去兮何時還？且放白鹿青崖間，須行即騎訪名山。
安能摧眉折腰事權貴，使我不得開心顏。
```

## Generation

Project:

```text
data/creative_projects/meng-you-tian-mu-kai-xin-yan-original-lines-20260706
```

Selected audio:

```text
data/creative_projects/meng-you-tian-mu-kai-xin-yan-original-lines-20260706/selected/meng-you-tian-mu-kai-xin-yan-original-lines-zh-Hans-ace-turbo-seed746204.wav
data/creative_projects/meng-you-tian-mu-kai-xin-yan-original-lines-20260706/selected/meng-you-tian-mu-kai-xin-yan-original-lines-zh-Hans-ace-turbo-seed746204.mp3
```

Route:

- ACE-Step 1.5 XL Turbo.
- Mandarin source-text-only short-line lyric.
- D minor, 82 BPM requested, cinematic xianxia ballad direction.
- Selected seed: `746204`.

Candidate summary:

| Candidate | Route | Result |
| --- | --- | --- |
| 746201 | first full repeat lyric | rejected; very weak ASR recovery |
| 746202-746204 | short-line source sweep | selected 746204; strongest source anchors |
| 746205 | XL SFT | rejected; introduced unrelated modern ASR |
| 746211-746213 | compact shorter lyric | rejected; worse source recovery |

## Audit

Full analysis run:

```text
data/runs/meng-you-tian-mu-kai-xin-yan-original-lines-20260706-selected-analysis
```

Artifacts:

```text
stems/vocals.wav
stems/drums.wav
stems/bass.wav
stems/other.wav
stems/human_sound.wav
stems/instrumental.wav
analysis/chords.csv
analysis/beats.csv
analysis/lyrics.json
analysis/lyrics.txt
```

Large-v3 ASR showed partial source recovery. Clearer anchors included:

```text
东流水
别君...兮
何时...
白...青...
访名山-like ending
权贵
不得开心颜-like ending
```

The opening and dense classical phrases are blurred. Public website data uses
source wording where sound-close, but the item is labeled as `原文段`, not the
pure poem title and not a perfect full original-poem master.

## Website

Website id:

```text
meng-you-tian-mu-kai-xin-yan-original-lines
```

Public title:

```text
梦游天姥吟留别 · 开心颜原文段
```

Files:

```text
scripts/prepare_meng_you_tian_mu_kai_xin_yan_original_lines_fun_item.py
website/data/songs/meng-you-tian-mu-kai-xin-yan-original-lines/manifest.json
website/data/songs/meng-you-tian-mu-kai-xin-yan-original-lines/lyrics/zh-vocal/zh-Hans.json
website/data/songs/meng-you-tian-mu-kai-xin-yan-original-lines/lyrics/zh-vocal/en.json
website/data/songs/meng-you-tian-mu-kai-xin-yan-original-lines/lyrics/zh-vocal/ja.json
website/data/catalog.json
```

Public audio:

```text
../MusiaSongs/audio/meng-you-tian-mu-kai-xin-yan-original-lines-zh-Hans-ace-turbo-seed746204-20260706.mp3
https://lazyingart.github.io/MusiaSongs/audio/meng-you-tian-mu-kai-xin-yan-original-lines-zh-Hans-ace-turbo-seed746204-20260706.mp3
```

Validation:

```bash
node bin/musia.js fun-validate
node bin/musia.js fun-audit --media-id meng-you-tian-mu-kai-xin-yan-original-lines
node --check website/app.js
python -m py_compile scripts/prepare_meng_you_tian_mu_kai_xin_yan_original_lines_fun_item.py
```

All passed on 2026-07-06.

