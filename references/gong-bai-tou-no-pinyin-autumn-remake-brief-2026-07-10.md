# 共白头 No-Pinyin Autumn Remake Brief

## Purpose

Create the next clean-language remake of `共白头 · Snow We Share`.

The current public render is titled `共白头 · Snow We Share · 雪中回声` because it
used Mandarin pinyin and Japanese romaji as the sung model-facing lyric. Keep
that version public only as a snow-memory/phonetic render.

For the next generation, use real Mandarin Chinese characters and real Japanese
script in the sung lyric. Do not use pinyin as the sung lyric. Pinyin should be
website ruby or a separate pronunciation note only.

## Key Lyric Change

Use:

```text
回首山河已入秋
```

not:

```text
回首山河已入冬
```

`秋` gives the line a softer ache and avoids the blunt winter pronunciation in
the current pinyin render. Only publish `秋` after a new generated vocal actually
sings it.

## Version Naming

- Current public pinyin render: `共白头 · Snow We Share · 雪中回声`
- Future selected no-pinyin standard render: `共白头 · Snow We Share`
- Rejected or alternate no-pinyin candidates can use poetic suffixes such as
  `秋声未远`, `雪约`, or `同雪之约`, but do not use mechanical suffixes like
  `Qiu Version` or `Dong Version`.

## Model-Facing Lyric Draft

```text
[Intro]
忽有故人心上过
Lights fall soft in the snow

[Verse]
回首山河已入秋
Your name still glows
遠い日の声が
胸に降る

[Pre-Chorus]
振り返れば世界は
秋の色になる
他朝若是同淋雪
此生也算共白头

[Chorus]
忽有故人心上过
回首山河已入秋
If we share the snow someday
Will our hearts be less alone

[Post-Chorus]
同じ雪の下で
白くなれるかな
他朝若是同淋雪
此生也算共白头

[Bridge]
旧时月照不回
I keep a little light
回不去的街
Waiting through the night

[Final Chorus]
忽有故人心上过
回首山河已入秋
他朝若是同淋雪
此生也算共白头

[Outro]
Snow on your hair
Snow on my soul
若能同淋雪
也算共白头
```

## Generation Notes

- Use ACE/ACE-Step as the quality-first route.
- Try XL/SFT and XL/Turbo candidates; keep the best actual song, not the route
  that looks cleaner on paper.
- Female vocal, intimate cinematic art-pop ballad, 74-78 BPM, piano, warm
  strings, soft bells, airy autumn-to-snow atmosphere.
- Leave space; do not cram the lyric.
- After generation, run ASR/listening correction before website publication.
- If ACE mispronounces a character, adjust the lyric with a beautiful
  sound-close character only when necessary. Do not fall back to pinyin as the
  public sung lyric unless all native-script candidates fail.
