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

## Correction Notes

The selected render compresses the planned prompt. Public lyrics use the actual audible mixed vocal as the active layer and translate that layer into English, Japanese, and Mandarin. Extra prompt lines such as `Every day I miss you`, `Across the river wide`, `Ding bu fu xiang si yi`, and `Kimi o omou` were not audibly recovered and are omitted from the public timing.

Close intended forms are preserved where ASR drifted phonetically: `Wo zhu Chang Jiang tou`, `Onaji kawa no mizu`, `Kokoro wa kimi e`, `Zhi yuan jun xin si wo xin`, and `Ci hen he shi yi`. The final line is corrected to `Wo xiang xin` because both English and Mandarin ASR support that audible ending better than the planned final hook.

## Website

- URL: `https://fun.lazying.art/#gong-yin-chang-jiang-shui-mixed`.
- Active lyric: `website/data/songs/gong-yin-chang-jiang-shui-mixed/lyrics/mixed-vocal/mul.json`.
- Translations: English, Japanese, and Mandarin tracks in the same lyric set.
