# 共饮长江水 · Same River Production Note

## Source Poem

The source is Li Zhiyi's Song-dynasty lyric `卜算子·我住长江头`. The canonical opening is `我住长江头，君住长江尾`; the user phrase `君住长江头，我住长江尾` was corrected for source reference.

```text
我住长江头，君住长江尾。
日日思君不见君，共饮长江水。
此水几时休？此恨何时已？
只愿君心似我心，定不负相思意。
```

## Selected Render

- Route: ACE-Step 1.5 XL Turbo mixed-language hook route.
- Seed: `790904`.
- Selected audio: `data/creative_projects/gong-yin-chang-jiang-shui-mixed-20260709/selected/gong-yin-chang-jiang-shui-mixed-ace-xl-turbo-seed790904.mp3`.
- Public audio: `https://lazyingart.github.io/MusiaSongs/audio/gong-yin-chang-jiang-shui-mixed-ace-xl-turbo-seed790904-20260709.mp3`.
- Analysis: `data/runs/gong-yin-chang-jiang-shui-mixed-20260709-analysis/`.
- Website manifest: `website/data/songs/gong-yin-chang-jiang-shui-mixed/manifest.json`.

## Generation Recipe

This song used the hook-led mixed-language ACE route, not a native-character poem-recitation route. The model-facing lyric was written mostly in Latin letters:

```text
Wo zhu Chang Jiang tou
You live where the river ends
Ri ri si jun bu jian jun
Still we drink the same water
Onaji kawa no mizu
Gong yin Chang Jiang shui
Same river, same moonlight
Kokoro wa kimi e
Zhi yuan jun xin si wo xin
Ci shui ji shi xiu
Ci hen he shi yi
When will this river rest
When will this longing sleep
Zhi yuan jun xin si wo xin
Ding bu fu xiang si yi
Same river, same longing
Kimi o omou
```

This was intentional. For this ACE-Step mixed EN/JP/ZH route, Mandarin pinyin and Japanese romaji gave the model a clearer phonetic path than mixing English with native Chinese characters and Japanese kana/kanji in the same lyric block. The pronunciation is still not perfect, but the pinyin/romaji route produced better musical continuity, less garbling, and a more singable result than prior mixed native-script attempts.

Config:

```text
config_path = "acestep-v15-xl-turbo"
task_type = "text2music"
duration = 74
bpm = 72
keyscale = "A minor"
timesignature = "4"
vocal_language = "en"
inference_steps = 8
guidance_scale = 1.0
seeds = [790901, 790902, 790903, 790904]
```

Caption strategy:

- state the emotional story plainly: two people separated along the Yangtze;
- ask for `mixed English lead with Mandarin pinyin and Japanese romaji`;
- keep arrangement vivid but not crowded: piano, guzheng/pipa color, strings, subtle drums, water ambience, spacious reverb;
- include negative constraints: no crammed words, no clipped endings, no buried vocal, no spoken narration, no real singer imitation.

Commands:

```bash
data/creative_projects/gong-yin-chang-jiang-shui-mixed-20260709/commands.sh generate-hook
data/creative_projects/gong-yin-chang-jiang-shui-mixed-20260709/commands.sh quality-hook <candidate.wav>
data/creative_projects/gong-yin-chang-jiang-shui-mixed-20260709/commands.sh analyze <selected.wav>
```

Candidate selection:

- `790901`: weak lyric recovery;
- `790902`: recovered only fragments;
- `790903`: mostly gibberish;
- `790904`: best recovery of `Chang Jiang`, `You live where the river ends`, `Ri ri si jun bu jian jun`, `Gong yin Chang Jiang shui`, and the final chorus shape, so it was selected.

Reusable rule: for mixed EN/JP/ZH ACE songs, use a phonetic active-vocal layer when pronunciation matters. Publish native-language companion tracks as translations, not as the active sung layer, unless the audio clearly sings the native script.

## Correction Notes

The selected render compresses the planned prompt. Public lyrics use the actual audible mixed vocal as the active layer and translate that layer into English, Japanese, and Mandarin. Extra prompt lines such as `Every day I miss you`, `Across the river wide`, and `Kimi o omou` were not audibly recovered clearly enough for public timing.

Close intended forms are preserved where ASR drifted phonetically: `Wo zhu Chang Jiang tou`, `Onaji kawa no mizu`, `Kokoro wa kimi e`, `Zhi yuan jun xin si wo xin`, and `Ci hen he shi yi`.

2026-07-09 tail correction: user listening found that the earlier `Wo xiang xin` correction was wrong. The ending is `Ding bu fu xiang si yi`, followed by `Same, same longing`, then a soft English phrase close to `Give me all`. Focused large-v3 ASR on the soft tail hallucinated unrelated text, so the ending was corrected from manual listening plus VAD instead of ASR alone.

VAD evidence from the separated vocal stem:

```text
57.50-58.00 rms=0.03536 active
58.00-61.50 rms=0.04009-0.12910 active
61.50-65.95 active sustained vocal
65.95-69.80 active final soft phrase
70.00-74.00 near-silence / fade
```

Final public tail:

```text
57.82-61.20 Ding bu fu xiang si yi
61.20-65.95 Same, same longing
65.95-69.80 Give me all
69.80-74.04 ♪
```

Before recording or publishing, use the corrected website active lyric JSON as the source of truth and do not use the original prompt lyric.

## Website

- URL: `https://fun.lazying.art/#gong-yin-chang-jiang-shui-mixed`.
- Active lyric: `website/data/songs/gong-yin-chang-jiang-shui-mixed/lyrics/mixed-vocal/mul.json`.
- Translations: English, Japanese, and Mandarin tracks in the same lyric set.
