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

## Future Upgrades

- Add a human-audited lead-sheet layer with confidence `verified`.
- Add strumming-pattern panels once rhythm extraction is checked against a musician.
- Add optional note/melody display from extracted F0 or MIDI when it is accurate enough.
- Add alphaTab or a similar renderer only when Musia has reliable symbolic tab/notation data.
- Add Tonal.js-style theory helpers if the local `musia.js` utility becomes too limited.

## Quality Rule

Atlas is allowed to help a learner practice. It is not allowed to silently invent certainty. If a chord, beat, lyric timing, or melody cue is approximate, the interface and data must say so.
