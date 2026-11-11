# I'm a Spy

Public title: **我是间谍 · I'm a Spy**. Artist: Musia. English lead vocal,
with Chinese and Japanese translations of the actual performance.

## Composition

A dreamy, playful indie-pop love song about trying to seem mysterious while
being unable to hide affection. The owner's spy / why / eye / cry hook is
retained. The supplied lyric is largely unchanged: the bridge question gains
"me", the outro returns to "the apple of my eye", and the requested cool-guy
idea becomes "I'm a cool guy, don't you cry / Take my hand and we can fly".

The arrangement brief asks for a warm male vocal, shimmering clean guitar,
rounded bass, light drums, airy synthesizers, delicate bells and a lifted final
chorus. No real singer's voice is cloned or imitated.

## Generation and Selection

- ACE XL Turbo, official decoder, eight steps, CFG 1, DCW enabled.
- ACE source `ca1e85fe9430179831e6bc6be790c332190a3866`.
- Checkpoint revision `d4a0b288b83ebb7e25a8c0b32c573c22e134e8ee`.
- Composition targets: 184 seconds, 104 BPM, A major, 4/4.
- Six takes: seeds 111101 through 111106. Selected: **111101**.
- WAV SHA-256: `9179b878e74999ff6468fc784783c0b916363569f8664c605ff66346a173c62a`.
- Runtime project: `data/creative_projects/im-a-spy-20261111/`.

The initial two-sample batch was reduced to one sample by ACE's free-VRAM
guard. The sweep correctly refused to pretend both seeds had rendered. Its
evidence was preserved; the complete sweep ran in a new directory with explicit
`--batch-size 1`. No peer GPU process or service was stopped. The small reusable
batch-size option is covered by a test and is part of request identity.

All six takes received signal checks, APEX screening and large-v3 recognition
with and without speech VAD. Speech VAD was unsuitable for these mixes: it
returned almost no lyrics. No-VAD windows recovered the performances. APEX
slightly favoured 111104, but its isolated vocal confirmed more omitted and
changed phrases. Take 111101 retains the second verse and bridge, and its
additional refrains fit the song's hook. Automated ranking is not proof of
beauty or human listening approval; the listener's assessment remains open.

The selected WAV is 48 kHz stereo, about -13 LUFS and -1 dBTP, with no clipped
or non-finite samples and a quiet ending. The public MP3 is 320 kbps.

## Lyric Review

Review compares the intended lyric with full-mix large-v3 no-VAD windows,
isolated-vocal large-v3 windows, the pipeline's stem recognition and an
independent MOSS transcription. No intended lyrics were supplied as ASR prompts.
`build_review.py` records the exact chosen source words and their timestamps;
the review is hash-bound to the selected audio and saved evidence.

The public track contains **49 lines**, accounting for all 42 input lines:

- The first "Like the stars up in the sky" is not recovered between the eye
  line and "I don't know". It is not forced into the display.
- An extra opening-chorus passage ends with "And I won't just say bye-bye".
  It is retained, followed by the full regular chorus.
- The late "I won't lie / I won't leave you behind / I won't ever say bye-bye"
  passage repeats. Both occurrences receive their own timings and translations.
- MOSS and two focused full-mix windows confirm **three** outro spy phrases.
  Stem-only recognition missed the first one at about 168 seconds. It is added
  as a short line before the usual doubled hook, with its own translations.
- Keep **cool**, supported by focused stem recognition and the input, rather
  than full-mix **cold** or a stem-VAD **fool** guess.
- Keep **spy**, supported by the stem and repeated hook, rather than one
  full-mix **spark** guess.
- Overlapping window fragments are context, not extra repeats. The isolated
  recognizer's zero-duration post-outro duplicate is not a new lyric.
- A zero-duration "you" is merged with its enclosing "don't you" phrase;
  no precise word boundary is invented for it.
- Instrumental passages have no fake lyric or musical-note rows. Nonlexical
  backing sounds are not presented as invented English sentences.

English timing uses selected ASR word anchors, not evenly spaced words across
the entire song. It is still approximate, not phoneme-perfect forced alignment.
The EN/JA/ZH tracks share the same real line structure. Chinese pinyin is based
on the Chinese translation; Japanese kanji have Japanese furigana. Translation
highlighting is line-relative and approximate.

## Musical Data and Cover

Demucs provides vocals, drums, bass, other and an instrumental mix for the
selected audio. Instrumental analysis estimates 103.359 BPM, 308 beat events
and 160 chord spans. These are analysis-grade learning aids, not a verified
score. The key remains unverified rather than treating the A-major prompt as
measured truth. Atlas is built from these assets and the corrected lyrics.

The new 16:9 cover places an affectionate couple in a monumental glass
observatory under the stars, with coral and pale-blue clothing, luminous paths
and a small apple. It is specific to this song, with no text, logo or reused
cover. Generated cover provenance is retained in the manifest.

## Rebuild and Publication

```sh
conda run -n musia python ideas-and-inspirations/im-a-spy/build_review.py
conda run -n musia python scripts/prepare_reviewed_japanese_fun_item.py \
  ideas-and-inspirations/im-a-spy/release.json
node bin/musia.js atlas-build --media-id im-a-spy
conda run -n musia python scripts/curate_fun_catalog.py --apply
node bin/musia.js fun-audit --media-id im-a-spy --strict
npm run website:validate
```

The historically named reviewed-Japanese exporter now also accepts
`vocalLanguage: "en"`, preserving actual English word spans and generating
JA/ZH translation readings. Existing Japanese behavior remains the default.
`--media-repo` allows an isolated release checkout to use the existing audio
repository without duplicating media. Focused regression tests cover both.

Public player: https://fun.lazying.art/#im-a-spy

Selected audio and corrected TXT/LRC/JSON are under the project's `selected/`
directory. The website's canonical lyric is
`website/data/songs/im-a-spy/lyrics/en-vocal/en.json`. Only the selected MP3 is
published to MusiaSongs; alternate takes and analysis stems remain local.
This request does not include video recording or social/music-platform posting.
