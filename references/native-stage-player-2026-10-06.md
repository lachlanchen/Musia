# Native Stage Player

## Intent

Bring the recording composition into the real iPhone, iPad, Mac and Android
players: cover and playback, English/Chinese/Japanese lyrics, then guitar.
Use the cover area for useful information rather than a large empty artwork
frame. This is a playback view, not an on-device video recorder.

## Design

- Songs open in **Stage**. **Practice** retains Listen/Tap/Play, phrase loops,
  detailed reference notes and exercises. First Pulse opens in Practice.
- Cover, title, artist, effective BPM and speed share a compact heading. BPM
  follows the playback rate and is labeled with its analysis confidence.
  Meter appears only when supplied. No key or downbeat is guessed.
- The current phrase is shown in the selected languages, default EN/ZH/JA,
  using that vocal's existing tracks. Chinese pinyin and Japanese furigana
  remain attached to the supplied tokens. Practice also shows upcoming lines.
- Word highlighting, beat pulse and guitar all follow the native media clock.
  An instrumental gap is a UI status, not a new lyric. Missing current chords
  never borrow the upcoming chord and mislabel it as current.
- Current fingering sits below the lyrics, with the next chord and its time
  beside it. Unknown shapes remain explicitly unavailable, not approximated.
- Transport is reserved at the bottom inside safe areas, not laid over the
  lyrics or navigation. Settings collapse speed and audio-version controls.
- Long lyrics and enlarged accessibility text can scroll; they are not clipped
  or shrunk to force an attractive screenshot. Wider Apple layouts put the
  cover/info and lyrics beside each other above the guitar.

## Scope And Tests

No audio, lyric text, timings, analysis data, API contract, permissions or
background playback engine changes. Existing timeline/ruby/chord tests remain
the regression baseline. `testStageLayoutAndPracticeSwitch` checks the native
iOS mode switch and transport after scrolling and rotation.

This update is **test distribution only**: 0.1.3, Apple build 5 and Android
code 4. Preserve the existing Apple/Google production reviews and pricing.
Build, upload, processing and tester availability must be recorded separately
in the store delivery record. Do not claim physical-device or audio quality
verification from a simulator screenshot.
