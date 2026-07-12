# Best Am I Mixed-Language Route Lessons

Date: 2026-07-12

This note records why `Best Am I · 我是天下第一等` worked and how to reuse the
route for future high-quality mixed EN/ZH/JP songs.

## Final Result

- Media ID: `best-am-i`
- Website URL: `https://fun.lazying.art/#best-am-i`
- Selected audio: `data/creative_projects/best-am-i-20260712/selected/best-am-i-mixed-ace-xl-turbo-seed812401.mp3`
- Website manifest: `website/data/songs/best-am-i/manifest.json`
- Corrected active lyric: `website/data/songs/best-am-i/lyrics/mixed-vocal/mul.json`
- Correction packet: `data/creative_projects/best-am-i-20260712/correction_packets/selected-seed812401-20260712-121122/CORRECTION_PACKET.md`
- Public audio: `https://lazyingart.github.io/MusiaSongs/audio/best-am-i-mixed-ace-xl-turbo-seed812401-20260712.mp3`

## What Failed

Dense mixed-language lyrics produced technically healthy audio but did not carry
the full song. The model recovered the opening and early verse, then skipped or
blurred later sections. Adding more prompt instructions did not solve that.

The XL SFT comparison also failed for this song. It hallucinated generic video
outro/subscriber phrases instead of singing the supplied lyrics. This confirms
the Musia rule: do not assume the larger or slower checkpoint is better. Select
by actual vocal beauty, lyric recovery, and listening.

## What Worked

The selected route used:

- ACE-Step 1.5 `acestep-v15-xl-turbo`;
- seed `812401`;
- `64s` duration;
- compact mixed-language anthem lyric;
- English as the lead scaffold;
- Mandarin pinyin and Japanese romaji as short active-vocal sound-control lines;
- repeated title hook;
- one language phrase per line;
- few unique semantic ideas.

The compact hook was:

```text
Best am I
I am still becoming
Wo shi tian xia di yi deng
Mada ikeru
```

For mixed EN/ZH/JP songs, this is the reusable rule:

```text
public native lyric for intent
-> compact ACE-facing mixed performance lyric
-> XL Turbo seed sweep
-> medium/large-v3 full-mix + vocal-stem ASR
-> publish only corrected active-vocal JSON
```

## Producer Brief Pattern

```text
High-quality emotional motivational art-pop anthem, English lead vocal with
short Mandarin pinyin and Japanese romaji color lines. Clear upfront expressive
female vocal, beautiful memorable chorus, smooth connected melody, strong hook,
full-song quality throughout. Piano, warm bass, clean drums, bright pads, light
strings in the final chorus. Sparse lyric, sing the supplied lines, leave breath
and held notes, no crammed words, no clipped final words, no buried vocal, no
spoken narration, no real singer imitation.
```

## Correction Pattern

The website lyric must follow the rendered compact vocal, not the longer draft
prompt. Evidence used:

- full-mix ASR;
- Demucs vocal-stem ASR;
- medium and large-v3 checks;
- no-VAD checks for soft mixed-language lines;
- planned compact lyric as reference only.

Correction policy:

```text
actual audible structure
> sound-close intended lyric
> ASR guess
> translation draft
```

Examples:

- Restore `Best am I` over ASR guesses like `Best of my` or `Best of all`.
- Restore `Wo shi tian xia di yi deng` over variants like `Washi tian shadi den`.
- Restore `Dare ni mo mienai namida` when ASR produces approximate romaji.
- Omit unsung bridge/final lines instead of forcing them into subtitles.

The final public track contains 18 sung lines and ends the vocal around `60.16s`.

## Cover Lesson

The generated cover worked because it was song-specific and emotionally aligned:
a small figure standing in a vast luminous golden-and-glass megastructure at
sunrise. It matched the song's self-belief theme without text, logo, or reused
visual baggage.

Reusable cover rule:

```text
fresh song-specific 16:9 cover
cinematic megastructure scale
one small warm human focal point
clean vivid color
no text, logo, watermark, or old-song contamination
```

## Website Checklist

1. Copy selected MP3 to `../MusiaSongs/audio/`.
2. Rebuild `../MusiaSongs/audio.json`.
3. Generate a fresh 16:9 cover aligned to this exact song.
4. Write `website/data/songs/<media-id>/manifest.json`.
5. Write active and companion lyric tracks.
6. Keep identical line IDs and timings across companion tracks.
7. Validate with `node bin/musia.js fun-validate`.
8. Push website and audio repos.
9. Verify live HTTP 200 for audio, manifest, and active lyric JSON.

