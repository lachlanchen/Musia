# 将进酒 · 原诗版 Production Note

Date: 2026-07-01

Goal: create a new ACE-Step render that treats Li Bai's original `将进酒` poem as the lyric source. This is not the older `将进酒 · ACE Poetry Demo` item and not the adapted normal-song version.

## Source Lyric

The user requested the common simplified text:

```text
君不见黄河之水天上来，奔流到海不复回。
君不见高堂明镜悲白发，朝如青丝暮成雪。

人生得意须尽欢，莫使金樽空对月。
天生我材必有用，千金散尽还复来。

烹羊宰牛且为乐，会须一饮三百杯。
岑夫子，丹丘生，将进酒，杯莫停。

与君歌一曲，请君为我倾耳听。
钟鼓馔玉不足贵，但愿长醉不愿醒。

古来圣贤皆寂寞，惟有饮者留其名。
陈王昔时宴平乐，斗酒十千恣欢谑。

主人何为言少钱，径须沽取对君酌。
五花马，千金裘，
呼儿将出换美酒，与尔同销万古愁。
```

Pronunciation guide:

```text
data/creative_projects/qiang-jin-jiu-original-poem-20260701/source/pronunciation-guide.md
```

Important readings:

- `将进酒`: `qiāng jìn jiǔ`
- `呼儿将出`: `hū ér jiāng chū`
- `朝如`: `zhāo rú`
- `斗酒`: `dǒu jiǔ`
- `馔玉`: `zhuàn yù`
- `恣欢谑`: `zì huān xuè`

## Generation Route

Project:

```text
data/creative_projects/qiang-jin-jiu-original-poem-20260701
```

The selected render came from the ACE-Step 1.5 XL sectioned exact-poem route:

```text
data/creative_projects/qiang-jin-jiu-original-poem-20260701/ace_zh_sectioned_xl_more.toml
```

Selected audio:

```text
data/creative_projects/qiang-jin-jiu-original-poem-20260701/ace_outputs/zh_sectioned_xl_more/20ea2127-e90d-f93c-77ed-26e210a5316d.wav
```

Why this candidate was selected:

- It was the strongest of six exact-poem candidates.
- Quick small ASR overlap: `0.363636`.
- Large-v3 no-VAD selected-audio overlap: approximately `0.409091`.
- Large-v3 no-VAD vocal-stem overlap: approximately `0.386364`.
- The vocal is audible and song-like, with better lyric anchors than the earlier dense or base-checkpoint candidates.

Rejected candidates:

- `1e7222c5-61d2-4fc4-62b9-9100285c0354.wav`: dense exact-poem route, low lyric recovery.
- `775f7805-93e4-6ddb-3ebb-bd8063ee5bbc.wav`: non-XL phrase-sheet route, low lyric recovery.
- `5af97218-dd90-81e3-833f-b40ad573e616.wav`: XL sectioned route, better but still lower recovery.
- `ed54e1f4-9411-2b33-737b-eccc01a63a0f.wav`: base checkpoint route, rejected.
- `4ede96eb-1d0a-c59e-b050-02ad9ee0c2b6.wav`: XL sectioned route, rejected.

## ASR Correction

Deep correction packet:

```text
data/creative_projects/qiang-jin-jiu-original-poem-20260701/corrections/deep-large-selected-732206/CORRECTION_PACKET.md
```

Evidence used:

- selected audio large-v3 no-VAD ASR;
- separated vocal-stem large-v3 no-VAD ASR;
- quick small-ASR review reports;
- the requested original poem and pronunciation guide.

Correction policy:

```text
actual audible structure > close intended lyric > ASR guess > translation draft
```

The website preserves the original poem where the rendered sound is close. It also reflects real rendered structure:

- `莫使金樽空对月` / `天生我材必有用` are repeated in the audio.
- `陈王昔时宴平乐` is repeated in the audio.
- Some final-section phrases are garbled, so unsupported phrase spans are not forced into the displayed lyric.
- The no-VAD ASR reported a likely hallucinated intro credit; this is not shown as poem lyric.

This render is a usable original-poem song candidate, not a perfect commercial recitation of every classical word.

## Website Item

Media id:

```text
qiang-jin-jiu-original-poem
```

Public URL:

```text
https://fun.lazying.art/#qiang-jin-jiu-original-poem
```

Website files:

```text
website/data/songs/qiang-jin-jiu-original-poem/manifest.json
website/data/songs/qiang-jin-jiu-original-poem/lyrics/zh-vocal/zh-Hans.json
website/data/songs/qiang-jin-jiu-original-poem/lyrics/zh-vocal/en.json
website/data/songs/qiang-jin-jiu-original-poem/lyrics/zh-vocal/ja.json
website/data/catalog.json
```

Public audio:

```text
https://lazyingart.github.io/MusiaSongs/audio/qiang-jin-jiu-original-poem-zh-Hans-ace-20260701.mp3
```

Preparation script:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/prepare_qiang_jin_jiu_original_poem_fun_item.py
```

Validation:

```bash
npm run website:validate
node --check website/app.js
node bin/musia.js fun-audit --media-id qiang-jin-jiu-original-poem
```

All three passed on 2026-07-01.

## Reuse Rule

For future exact classical-poem songs:

1. Prepare a pinyin/pronunciation guide before generation.
2. Use section labels and short breath-friendly line breaks, but keep lyric words exact when the user asks for original-poem mode.
3. Generate multiple ACE candidates; do not accept the first WAV.
4. Select by vocal quality and ASR recovery.
5. Run large-v3 no-VAD ASR on both selected audio and vocal stem.
6. Publish website lyrics only after correcting against the audio.
7. Keep original poem wording only when sound-close; document repeats, skips, and garbled spans.
