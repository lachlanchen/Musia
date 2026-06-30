# 侠客行 · 原诗版 Production Note - 2026-07-01

## Goal

Generate an ACE-Step version of Li Bai's 《侠客行》 using the original poem as the lyric source, then audit the result with ASR before publishing to Fun Lazying Art.

This is intentionally separate from the existing smoother adapted item:

- Existing adapted item: `xia-ke-xing`
- Original-poem experiment: `xia-ke-xing-original-poem`

## Source And Pronunciation Prep

The user-supplied text matches the common public-domain text checked against Wikisource and classical-poetry reference pages:

- Wikisource: https://zh.wikisource.org/zh-hans/%E4%BF%A0%E5%AE%A2%E8%A1%8C_%28%E6%9D%8E%E7%99%BD%29
- 古诗词网 reference with pinyin/notes: https://m.gushici.net/shici/20/1581.html

Pronunciation guide:

- `data/creative_projects/xia-ke-xing-original-poem-20260701/source/pronunciation-guide.md`

Important manual pronunciation checks:

- `飒沓`: `sa4 ta4`
- `事了`: `shi4 liao3`
- `不留行`: `bu4 liu2 xing2`
- `将炙`: `jiang1 zhi4`
- `五岳倒为轻`: `wu3 yue4 dao4 wei2 qing1`
- `烜赫`: `xuan3 he4`

## Generation Attempts

Four exact-poem ACE candidates were generated.

1. XL turbo, full couplet lyric, 128s, seed `731901`
   - WAV: `data/creative_projects/xia-ke-xing-original-poem-20260701/ace_outputs/zh/dcb255b2-d6ab-9c88-04ec-c6a9558ddc16.wav`
   - Result: rejected. ASR recovered no intelligible lyric.

2. XL turbo, clearer solo-vocal correction, 142s, seed `731902`
   - WAV: `data/creative_projects/xia-ke-xing-original-poem-20260701/ace_outputs/zh_corrected_20260701-022232/d0943d83-3781-5832-9316-9fa1ae5b7bec.wav`
   - Result: rejected. ASR recovered only a stray phrase.

3. Non-XL turbo, simpler sparse wuxia arrangement, 108s, seed `731903`
   - WAV: `data/creative_projects/xia-ke-xing-original-poem-20260701/ace_outputs/zh_corrected_20260701-022423/94467276-ec50-3742-609c-4654c61e4cda.wav`
   - Result: selected. It recovered the most poem structure, especially in vocal-stem medium/large ASR, though classical diction remains imperfect.

4. Non-XL turbo, phrase-sheet lyric layout, 112s, seed `731904`
   - WAV: `data/creative_projects/xia-ke-xing-original-poem-20260701/ace_outputs/zh_corrected_20260701-022756/66815eca-a4e9-542c-dc7a-369fe540da12.wav`
   - Result: rejected. Phrase layout did not improve the ASR recovery enough.

## Selected Audio Audit

Selected candidate:

```text
data/creative_projects/xia-ke-xing-original-poem-20260701/ace_outputs/zh_corrected_20260701-022423/94467276-ec50-3742-609c-4654c61e4cda.wav
```

Analysis run:

```text
data/runs/xia-ke-xing-original-poem-20260701-20260701-022506-analysis
```

Deep correction packet:

```text
data/creative_projects/xia-ke-xing-original-poem-20260701/correction_packets/candidate3/CORRECTION_PACKET.md
```

ASR overlaps:

- Selected audio large-v3: `0.2583`
- Vocal stem medium: `0.3333`
- Vocal stem large-v3: `0.3167`

Important policy decision:

The public lyric JSON preserves Li Bai's original poem text where the rendered syllables are sound-close and the poem context is clear. This is not a perfect commercial master. Some classical words are garbled, and the website item is labeled/provenanced as an original-poem ACE experiment.

## Lyric Realignment - 2026-07-01

After user review, the public lyric JSON was tightened again against the actual
selected audio. Evidence used:

- existing selected-audio and vocal-stem `small` / `medium` / `large-v3` ASR;
- existing no-VAD ASR packet under
  `data/creative_projects/xia-ke-xing-original-poem-20260701/correction_packets/candidate3/`;
- an additional `large-v3` prompted ASR pass on the separated vocal stem using
  the source poem as initial prompt.

Prompted vocal-stem `large-v3` anchors:

```text
20.00-27.24 客门呼应 客门呼应 吴钩霜雪明
28.56-32.18 银鞍照白马洒脱入流星
33.14-34.96 誓不杀一人
34.96-37.14 誓了负一曲
37.14-40.00 生苍生与命
43.64-45.82 拖剑系前行
46.62-48.92 将枝挡住怀
48.92-51.34 持上拳后一举
51.34-53.64 持上拳后一
56.26-61.82 三辈徒然诺五月到为期
64.28-68.86 愿法而得后一气俗离神
68.86-75.20 就照辉青春 / 寒淡鲜鲜真净
76.20-80.50 千秋而壮世 / 鲜河大凉城
80.50-86.20 从死下孤狭 / 不残血上瘾
88.80-93.96 谁能说孤狭 / 白首抬陷阱
```

Website correction decisions:

- the opening now starts at `20.00s` and shows `赵客缦胡缨` twice before
  `吴钩霜雪明`, matching the repeated vocal shape;
- `千里不留行` is not published as a sung line because the audio goes directly
  from the `十步杀一人`-like phrase into the `事了拂衣去`-like phrase;
- `闲过信陵饮` is not published because the slot is much closer to
  `脱剑膝前横`;
- `持觞劝侯嬴` is shown twice because the render repeats that phrase;
- the final two lines now follow the AI-mutated sound as `谁能说孤侠` and
  `白首太仙境` instead of forcing the clean poem text.

Updated files:

- `scripts/prepare_xia_ke_xing_original_poem_fun_item.py`
- `website/data/songs/xia-ke-xing-original-poem/manifest.json`
- `website/data/songs/xia-ke-xing-original-poem/lyrics/zh-vocal/zh-Hans.json`
- `website/data/songs/xia-ke-xing-original-poem/lyrics/zh-vocal/en.json`
- `website/data/songs/xia-ke-xing-original-poem/lyrics/zh-vocal/ja.json`

## Website Item

Website URL:

```text
https://fun.lazying.art/#xia-ke-xing-original-poem
```

Files:

- Manifest: `website/data/songs/xia-ke-xing-original-poem/manifest.json`
- Active lyrics: `website/data/songs/xia-ke-xing-original-poem/lyrics/zh-vocal/zh-Hans.json`
- English translation: `website/data/songs/xia-ke-xing-original-poem/lyrics/zh-vocal/en.json`
- Japanese translation: `website/data/songs/xia-ke-xing-original-poem/lyrics/zh-vocal/ja.json`
- Cover: `website/assets/covers/xia-ke-xing-original-poem-16x9.png`
- Public MP3: `../MusiaSongs/audio/xia-ke-xing-original-poem-zh-Hans-ace-20260701.mp3`

Validation:

```bash
npm run website:validate
node bin/musia.js fun-audit --media-id xia-ke-xing-original-poem
node --check website/app.js
git diff --check
```

All passed before commit.
