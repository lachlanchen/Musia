# Best Am I Production Note

`Best Am I · 我是天下第一等` is a mixed EN/ZH/JP motivational anthem. The intended
meaning is confidence without arrogance: a small, unseen person choosing to
believe they are worthy and still becoming.

## Final Route

- Model: ACE-Step 1.5 `acestep-v15-xl-turbo`
- Route: compact mixed-language anthem
- Selected seed: `812401`
- Selected MP3: `data/creative_projects/best-am-i-20260712/selected/best-am-i-mixed-ace-xl-turbo-seed812401.mp3`
- Selected WAV: `data/creative_projects/best-am-i-20260712/selected/best-am-i-mixed-ace-xl-turbo-seed812401.wav`

## Key Lesson

This song followed the same lesson as `The Babiest`, `共饮长江水`, `哭晁卿衡`,
and `巫峡月`: mixed-language ACE songs work best when the prompt is sparse,
hook-led, and phonetic-control friendly. Dense multilingual lyrics caused ACE to
sing only the beginning and drop later sections. The selected route reduced the
lyric to a compact hook form:

```text
Best am I
I am still becoming
Wo shi tian xia di yi deng
Mada ikeru
```

Use this as a reusable pattern for future mixed EN/ZH/JP songs:

1. Write the public native lyric for meaning.
2. Write an ACE-facing compact phonetic lyric with fewer unique lines.
3. Keep one language phrase per line.
4. Repeat the strongest hook instead of cramming every idea.
5. Audit with ASR and listening before website, recording, or music publishing.

## Rejected Route Notes

SFT was tested because it is the higher-step checkpoint, but it hallucinated
generic video outro text. For this song, XL Turbo was better. This confirms the
current Musia rule: model size/step count does not automatically win; choose by
actual vocal beauty and lyric recovery.
## Website Publication

- Media ID: `best-am-i`
- URL: `https://fun.lazying.art/#best-am-i`
- Manifest: `website/data/songs/best-am-i/manifest.json`
- Active lyric: `website/data/songs/best-am-i/lyrics/mixed-vocal/mul.json`
- Public audio: `https://lazyingart.github.io/MusiaSongs/audio/best-am-i-mixed-ace-xl-turbo-seed812401-20260712.mp3`
- Public audio file: `../MusiaSongs/audio/best-am-i-mixed-ace-xl-turbo-seed812401-20260712.mp3`
- Cover: `website/assets/covers/best-am-i-16x9.png`
- Cover source: `/home/lachlan/.codex/generated_images/019f0842-25ba-7bd2-9d4b-0b1c60d8a951/ig_02a348b19ca3f962016a531567298481909c58ed5626f8a703.png`
- Correction packet: `data/creative_projects/best-am-i-20260712/correction_packets/selected-seed812401-20260712-121122/CORRECTION_PACKET.md`

The public lyric set contains 18 sung lines only. The selected render ends its
vocal around `60.16s`; draft lines after that are not published as lyrics. The
active mixed line keeps intended sound-close forms such as `Best am I`,
`Wo shi tian xia di yi deng`, `Mada ikeru`, and `Dare ni mo mienai namida`
instead of awkward ASR guesses.
