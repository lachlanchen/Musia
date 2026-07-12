# Musia Atlas Learning Tool

Date: 2026-07-12

## Why this exists

Musia is also a way to learn music from the songs we generate. The motivating user story is practical: a learner may own a guitar, know many chord shapes, and still struggle because they cannot sing confidently, cannot feel where lyrics enter, and do not yet understand rhythm, tempo, chord timing, or melody well enough to combine them.

The goal is not to pretend the learner already reads theory. The goal is to make a song behave like a readable map:

- play the music;
- show corrected lyrics and current line timing;
- show chord changes and guitar fingering;
- show beat/tempo cues;
- support transpose, capo, and simplified chord display;
- explain whether each data layer is corrected, analyzed, or estimated.

Working name: **Musia Atlas**.

Path style:

```text
https://fun.lazying.art/?mode=atlas&media=<song-id>
https://fun.lazying.art/atlas/<song-id>/
```

The first prepared song is:

```text
aya-chan-hikari-ame
```

## Design Principles

1.  Corrected lyrics come first.

    Atlas must use the same corrected website lyric JSON as the public player. If ASR and the input lyric disagree, use the Musia correction policy: respect the original/input when sound and syllable count are close; respect the audio when words are clearly missing, inserted, repeated, or structurally different.

2.  Do not show instrumental spans as lyric lines.

    Instrumental intro, bridge, and outro are player states. They can be shown as UI hints, but they must not pollute song-level lyric JSON.

3.  Label uncertainty.

    Chord and beat analysis can be useful for guitar practice, but unless a human has audited the harmony, label it as analysis-grade. This prevents Musia from teaching false certainty.

4.  Capo and transpose are display transforms.

    Audio is unchanged. The displayed guitar chord may differ from the concert chord, especially with capo enabled.

5.  Beginner usefulness beats dense theory.

    The page should help someone tap beats, change chords, and speak lyrics in time before expecting them to sing.

## Data Contract

Each song can optionally include:

```text
website/data/songs/<song-id>/study.json
```

Current fields:

```json
{
  "schema": "https://fun.lazying.art/schemas/musia-atlas-study.v1.json",
  "version": 1,
  "toolName": "Musia Atlas",
  "mediaId": "aya-chan-hikari-ame",
  "defaultAssetId": "aya-hikari-ame-ja",
  "dataPolicy": [
    "Lyrics use corrected website timing JSON for the active vocal.",
    "Beats come from local analysis runs and are marked as analysis data.",
    "Chords are imported from the song manifest and should be verified by ear before formal teaching."
  ],
  "assets": {
    "<asset-id>": {
      "bpm": 92.285,
      "timeSignature": "4/4",
      "beatConfidence": "analysis",
      "beatSource": "data/runs/.../analysis/beats.json",
      "beats": [{ "index": 0, "time": 1.904 }]
    }
  }
}
```

The player still reads chords from the normal manifest:

```text
website/data/songs/<song-id>/manifest.json
assets.primaryAudio.musical.chords
assets.alternateAudio[].musical.chords
```

## Implementation Added

- `website/musia.js`
  - chord parsing;
  - chord transposition;
  - capo display conversion;
  - chord simplification;
  - beat-grid generation;
  - active-beat lookup;
  - lyric-line practice metrics.

- `website/index.html`
  - Atlas link in the header;
  - hidden `study-panel` that appears in Atlas mode;
  - script load for `musia.js`.

- `website/app.js`
  - `?mode=atlas` support;
  - optional `study.json` loading;
  - active phrase metrics;
  - beat lane;
  - chord practice list;
  - transpose/capo/simplify controls;
  - guitar fingering uses the transformed study chord in Atlas mode.

- `website/data/songs/aya-chan-hikari-ame/study.json`
  - beat grids from existing analysis runs for Japanese, English, and Mandarin vocals.

- `website/atlas/aya-chan-hikari-ame/index.html`
  - static redirect for a clean shareable Atlas path.

## Rebuild Command

After a song is corrected for Fun Lazying Art or prepared for Shipinhao Music,
rebuild Atlas study data:

```bash
node bin/musia.js atlas-build --all
node bin/musia.js fun-validate
```

For one song:

```bash
node bin/musia.js atlas-build --media-id <media-id>
```

The generator writes:

```text
website/data/songs/<media-id>/study.json
website/atlas/<media-id>/index.html
```

Atlas source priority:

1.  corrected website lyric JSON;
2.  manifest/asset chord maps;
3.  matched local analysis beats/chords under `data/runs`;
4.  BPM-estimated beat grid in the browser when no reliable beat file is found.

The matcher is conservative: if a beat-analysis run cannot be strongly matched
to the media id, asset id, or audio filename, Atlas uses BPM-estimated beats
instead of borrowing another song's run.

## Rhythm Coach

Atlas now includes an optional beginner rhythm coach:

- `Off`
- `Strum`
- `Fingerpick`
- practice speed from `25%` to `200%`
- sticky mini player for play/pause, time, current chord, and speed while
  scrolling the study section

The first practical model is intentionally simple. It is designed for a learner
who does not yet know how to feel rhythm or sing while playing guitar.

Default strum pattern:

```text
1  2  3  4
D  U  D  U
```

This maps to the user's memory from guitar class: keep the hand or foot moving
down-up-down-up, and divide each active chord span into four practice parts.

Other included practice patterns:

```text
D D D D
D D U U D U
Bass 3 2 1
P I M A
```

Important quality rule:

```text
Rhythm coach pattern = practice guide, not verified original strumming.
```

The coach uses:

1.  active chord start/end timing when available;
2.  beat timing as fallback;
3.  browser playback speed control for slow practice.

Atlas top layout in study mode:

```text
col 1: compact player
col 2: chord row + guitar fingering
col 3: current lyric line A
col 4: current lyric line B
```

The lyrics card spans the last two grid columns and renders the current two
lyric rows side by side on desktop. This keeps the top area shorter so the
rhythm/study cards appear higher on the page. The normal homepage player remains
unchanged; Atlas moves the existing chord and fingering DOM into the middle card
only in `study-mode`.

The current phrase card must use the same ruby-aware lyric renderer as the main
player. Chinese lines should show pinyin when the corrected lyric JSON contains
`token.pinyin`; Japanese kanji should show furigana when the corrected lyric JSON
contains `token.reading`. If a line has no token ruby, Atlas must not invent it
client-side; fix or enrich the lyric JSON first.

Atlas can also display **Number notes** when an analysis run has a matching
`melody_f0.csv`. This is the English UI label for 简谱-style numbered musical
notation. The current implementation computes median vocal F0 inside each lyric
token, converts it to a Western note name and a key-relative numbered scale
degree, highlights the current sung note, and auto-scrolls the note lane as the
song plays. This is labeled `analysis`, not a verified lead sheet. It is useful
for seeing the relationship between sung pitch and the active chord, but a
human-audited score should use confidence `verified`.

Playback speed is display/practice behavior only. It does not rewrite audio,
lyrics, chords, or Atlas source data. The page tries to preserve pitch when the
browser supports it.

Catalog curation rule:

```text
hidden: true        -> hidden from normal catalog and playback queue
?showall or showAll -> include hidden songs again for review/debug
```

Use hiding rather than deleting when a song is low quality, a superseded suffix
variant, or a demo that should remain linkable for audit history. Standard
published versions, especially songs already uploaded to Shipinhao Music, should
normally stay visible unless the user explicitly asks to hide them.

Future deep-analysis work can add:

- downbeat detection confidence;
- section-specific strumming suggestions;
- more reliable melody-entry cues from F0/MIDI;
- GPU-assisted rhythm/chord/melody reanalysis;
- optional symbolic notation or tab rendering when Musia has reliable data.

## Future Upgrades

- Add a human-audited lead-sheet layer with confidence `verified`.
- Add strumming-pattern panels once rhythm extraction is checked against a musician.
- Add optional note/melody display from extracted F0 or MIDI when it is accurate enough.
- Add alphaTab or a similar renderer only when Musia has reliable symbolic tab/notation data.
- Add Tonal.js-style theory helpers if the local `musia.js` utility becomes too limited.

## Quality Rule

Atlas is allowed to help a learner practice. It is not allowed to silently invent certainty. If a chord, beat, lyric timing, or melody cue is approximate, the interface and data must say so.
