# 哭晁卿衡 Mixed Song Production Note

## Intent

Create a beautiful mixed English/Japanese/Chinese song from Li Bai's
`哭晁卿衡`.

Hard lyric constraint: Chinese sung text should only use original poem lines.
English and Japanese may be companion lines, but should not replace or dilute
the poem's core emotional images: leaving Chang'an, one sail around Penghu, the
moon sinking into the blue sea, and white clouds full of sorrow.

## Source Poem

```text
日本晁卿辞帝都，
征帆一片绕蓬壶。
明月不归沉碧海，
白云愁色满苍梧。
```

## Working Mixed Lyric

```text
[Intro]
Haruka umi e
One sail fades into blue

[Verse 1]
日本晁卿辞帝都
Sail away, my friend, from the city of stars
征帆一片绕蓬壶
Haruka, haruka, over the sea

[Pre-Chorus]
明月不归沉碧海
Moonlight will not return to me
Tsuki wa kaeranu
白云愁色满苍梧

[Chorus]
明月不归沉碧海
Moon over the blue sea
白云愁色满苍梧
Shiroi kumo, kanashimi no iro

[Bridge]
征帆一片绕蓬壶
Far beyond the waves, I still call your name
日本晁卿辞帝都
Haruka umi e

[Final Chorus]
明月不归沉碧海
Moonlight will not return to me
白云愁色满苍梧
Tsuki wa kaeranu
明月不归沉碧海
白云愁色满苍梧
```

## Generation Rule

Start with ACE-Step 1.5 XL Turbo because recent Musia successes show it often
gives smoother vocals than SFT for short mixed-language songs. Use SFT only if
Turbo candidates are weak, noisy, or incoherent.

After generation, do not trust the prompt lyric. Run ASR and analysis on the
selected render. Public lyrics must match the actual audio while preserving the
original Chinese poem when the sound is close.

## Website Rule

The Fun item should use a `mixed-vocal` lyric set:

- `mul.json`: active performance layer with the actual mixed sung text;
- `en.json`: English companion meaning;
- `ja.json`: Japanese companion meaning with furigana where kanji is used;
- `zh-Hans.json`: original poem source anchors only, no modern Chinese
  paraphrase.

If ACE skips or repeats lines, update the timing JSON to the rendered audio and
document the compromise here.
## Selected Render

- Route: ACE-Step 1.5 XL Turbo hook-led phonetic mixed route.
- Seed: `780824`.
- Selected audio: `data/creative_projects/ku-chao-qing-heng-mixed-20260708/selected/ku-chao-qing-heng-mixed-ace-xl-turbo-seed780824.mp3`.
- Public audio: `https://lazyingart.github.io/MusiaSongs/audio/ku-chao-qing-heng-mixed-ace-xl-turbo-seed780824-20260708.mp3`.
- Analysis: `data/runs/ku-chao-qing-heng-mixed-20260708-seed780824-analysis/`.
- Website manifest: `website/data/songs/ku-chao-qing-heng-mixed/manifest.json`.

Original-character route notes: the native CJK mixed sweep produced very weak lyric recovery. SFT hook comparison produced generic outro chatter. The selected Turbo hook route recovered the main pinyin/romaji/English shape best.

Correction compromise: active `mul` lyrics are phonetic because that is what the selected audio sings. The `zh-Hans` track translates each active line, preserving original Li Bai lines where the active vocal sings poem pinyin.
