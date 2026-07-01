# 蜀道难 Production Note

Date: 2026-07-01

## Source

User request: generate an adapted Musia song for Li Bai's `蜀道难`, first
downloading/checking the original poem and then adapting it like the earlier
Li Bai normal-song workflows.

Downloaded source pages:

- Wikisource: https://zh.wikisource.org/wiki/蜀道難_(李白)
  - Local: `data/creative_projects/shu-dao-nan-20260701/source/wikisource-shu-dao-nan.html`
- Gushiwen / Guwendao mirror: https://m.gushiwen.cn/shiwenv_d59ec5d6c91c.aspx
  - Local: `data/creative_projects/shu-dao-nan-20260701/source/gushiwen-shu-dao-nan.html`

Source and preparation files:

- Original poem: `data/creative_projects/shu-dao-nan-20260701/source/source-poem.md`
- Pronunciation guide: `data/creative_projects/shu-dao-nan-20260701/source/pronunciation-guide.md`
- Producer brief: `data/creative_projects/shu-dao-nan-20260701/source/producer-brief.md`
- Final prompt lyric basis: `data/creative_projects/shu-dao-nan-20260701/lyrics/zh.txt`

## Generation Route

Route used: ACE-Step 1.5 normal-song adaptation, not original-poem-only.

Attempts:

- `ace_zh.toml`: dense adaptation, seeds `735101`, `735102`; ASR recovery too weak.
- `ace_zh_v2_clear.toml`: clearer adaptation, seeds `735201`, `735202`; selected seed `735202`.
- `ace_zh_turbo_direct.toml`: non-XL direct-start diction pass, seeds `735301`-`735304`; did not beat seed `735202`.
- `ace_zh_compact_xl.toml`: compact hook pass, seeds `735401`, `735402`; did not beat seed `735202`.

Selected audio:

```text
data/creative_projects/shu-dao-nan-20260701/ace_outputs/zh-v2-clear/91355521-1698-0d9d-06c8-c1f7d004c80e.wav
```

Analysis run:

```text
data/runs/shu-dao-nan-20260701-735202-analysis/
```

Artifacts include:

- `stems/vocals.wav`
- `stems/drums.wav`
- `stems/bass.wav`
- `stems/other.wav`
- `stems/instrumental.wav`
- `analysis/chords.json`
- `analysis/beats.json`
- `analysis/lyrics.json`

## Lyric Correction

Correction packet:

```text
data/creative_projects/shu-dao-nan-20260701/correction_packets/seed-735202-large-v3/CORRECTION_PACKET.md
```

Evidence:

- selected audio large-v3 overlap: `0.2925531914893617`
- vocal-stem large-v3 overlap: `0.4308510638297872`

Policy applied:

- Use the selected audio's large-v3 ASR timing as the line-timing source.
- Preserve intended lines when ASR substitutions were sound-close and the
  poem/adaptation context strongly supported the intended phrase.
- Omit or merge prompt lines not supported by ASR timing.
- Publish corrected trilingual tracks, not the raw prompt lyric.

Important limitation:

This selected render is a usable adapted song candidate, but it is not as
lyrically clean as the strongest `侠客行`, `将进酒`, and `梦游天姥` normal-song
renders. The website item is therefore corrected conservatively and its
manifest provenance marks the gate as `review-with-correction`.

## Website

Media id:

```text
shu-dao-nan
```

Website files:

- `scripts/prepare_shu_dao_nan_fun_item.py`
- `website/data/songs/shu-dao-nan/manifest.json`
- `website/data/songs/shu-dao-nan/lyrics/zh-vocal/zh-Hans.json`
- `website/data/songs/shu-dao-nan/lyrics/zh-vocal/en.json`
- `website/data/songs/shu-dao-nan/lyrics/zh-vocal/ja.json`
- `website/assets/covers/shu-dao-nan-16x9.png`

Public audio mirror:

```text
../MusiaSongs/audio/shu-dao-nan-zh-Hans-ace-20260701.mp3
https://lazyingart.github.io/MusiaSongs/audio/shu-dao-nan-zh-Hans-ace-20260701.mp3
```

Fun URL:

```text
https://fun.lazying.art/#shu-dao-nan
```

Validation:

```bash
npm run website:validate
node --check website/app.js
node bin/musia.js fun-audit --media-id shu-dao-nan --strict
git diff --check -- scripts/prepare_shu_dao_nan_fun_item.py references/shu-dao-nan-production-2026-07-01.md website/data/catalog.json website/data/songs/shu-dao-nan website/assets/covers/shu-dao-nan-16x9.png
git -C ../MusiaSongs diff --check -- audio.json audio/shu-dao-nan-zh-Hans-ace-20260701.mp3
```

Result: all passed locally.

