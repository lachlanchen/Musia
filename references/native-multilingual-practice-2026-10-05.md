# Native Lyrics and Beginner Practice

## Owner Requests

Update native iPhone/iPad, Android and Mac together:

- Lyric language multi-selection, English / 中文 / 日本語 on by default.
- Chinese pinyin and Japanese furigana above the correct base text.
- Independent audio-version selection; translations belong to the selected vocal.
- Move History below Settings, out of primary navigation.
- Beginner listening practice for someone who knows some guitar chords but cannot
  confidently follow pitch, singing entrances or rhythm.
- Do Re Mi, a BPM metronome, chord-change practice, and understandable scores.

Apple iOS and Mac 0.1.1 submissions were freshly observed WAITING_FOR_REVIEW.
The owner explicitly chose **keep current reviews; prepare the next update**.
Do not withdraw, replace or resubmit either pending Apple review. Android's
current 0.1.1 production release can receive a separately tested update.
Candidate: 0.1.2, Apple build4, Android code3. This document is not a submission
receipt; record qualification and provider outcomes separately.

## Contract

The read-only v1 API adds `lyricTracks: [{language, lines}]` to each audio asset.
The existing `lyrics` and `phrases` remain the original-vocal track for old clients
and phrase loops. Tracks are selected only from the exact audio asset's lyric set.
The same visibility, path, timing and private-field boundary applies to translations.
The deployment exporter round-trips every sanitized track without raw provenance.

Native clients fall back to the old `lyrics` field for older servers. Language
preferences are independent of audio selection and persist locally. No selected
languages means lyrics are hidden. Missing translations are not synthesized or
borrowed from a different independently generated vocal.

Supplied Chinese numeric pinyin is formatted into tone marks without guessing
pronunciation. Japanese readings remain kana. Native wrapping ruby keeps readings
attached to the original token, while preserving English spacing and punctuation.
Highlights use each track's timed tokens on the audio source clock; future lines
and instrumental gaps are never highlighted as if already sung.

## Beginner Tools

Do Re Mi uses fixed Do in C major, equal temperament with A4=440Hz. It starts
with C4/D4/E4, with an optional full octave. Reference notes can be replayed.
Only the first answer per question affects the correct-answer score; this measures
listening identification, not singing or guitar skill. No microphone is requested.

The metronome is synthesized at exact sample positions, 40-160 BPM, in four-beat
bars. The first beat is accented. Optional Em/Am accompaniment changes every four
beats; start by strumming only on beat1. Visual counts/fingering use the audio
playhead, not an independently accumulated UI timer. Tap feedback reports mean
absolute offset in milliseconds and acknowledges output/Bluetooth latency.

Practice sounds are local/offline and stop when leaving the lesson or backgrounding
it. Existing full-song background playback is unaffected. The exercises do not
infer a song's meter or pretend that analyzed music is a verified score.

## Verification

- Backend tests: per-vocal isolation, missing/hidden/ambiguous tracks, pinyin formatting.
- Native core tests: legacy decoding, ruby text preservation, language preferences,
  pitch frequencies, PCM durations/headroom and first-answer-only scoring.
- Native runtime: phone/tablet/Mac layout, toggles, current/next timing, beginner
  audio, metronome tempo/chord switching, Back navigation and Settings > History.
- Release: preserve exact signing identities and submitted Apple artifacts; record
  provider status separately from build/upload status.

Catalog audit: 29 published songs; three older Cantonese assets currently have
English and Chinese, but no Japanese translation. This update must not fabricate
their missing Japanese track.

## Live API Deployment

Deployed from clean source commit `5a3eca9`, not from unrelated dirty lyric files.
Transaction `20261005T150626-1b2bc4faf344` passed the edge safety checks and public
readback. Origin: <https://musia.lazying.art>. All three Aya Chan vocals expose
their own en/zh/ja tracks, including tone-marked pinyin and kana readings.
The existing read-only boundary, service port, memory guard and other apps remain
unchanged. Private rollback/verification evidence is in
`deploy/learning/.work/20261005T150626-1b2bc4faf344/`.

## Reusable Checks

- `tools/store/android_review_ui.py`: inspect, tap exact observed labels, scroll,
  and capture one explicitly Musia-owned emulator.
- `tools/store/android_practice_smoke.py`: native Settings, language defaults,
  reference notes, quiz scoring, Em/Am audio-clock transitions and lifecycle.
- `PracticeSmokeTests.testBeginnerPracticeAndSettings`: equivalent iOS UI checks.
- `PracticeSmokeTests.testLiveMultilingualLyrics`: live Aya lyric selector check.
- `MacPlaybackTests.testBeginnerReferenceAudioAndMetronomeClock`: reference-tone
  completion, metronome media clock and stop on a Mac with an audio device.

Do not weaken a failing runtime test because the VM lacks audio or a test host
cannot reach the catalog. Record the failure, diagnose it, and rerun on a suitable
host. The KVM has no audio device; its AVPlayer clock alone is not an audible
audio test. The physical Mac mini passed the practice-audio runtime test. Its
direct route to this API timed out during live iPhone lyric tests, whereas the
KVM's live contract and Android's live rendering worked.

The Android note player releases focus at the final PCM marker via the official
[AudioTrack position callback](https://developer.android.com/reference/android/media/AudioTrack#setNotificationMarkerPosition(int));
looping metronome frames are read from the actual playback head. These are not
independent timing animations or inferred grades.

## Verified Candidate

Android 0.1.2 (3) uses source `12c1e70b59c0` and AAB SHA-256
`0bd51cd813effb9082a297a0e310dbdfa5495dcf361f19df1a7b1c7a22b639e3`.
Release unit tests: 40 passed; Android lint and signing checks passed. The exact
signed QA APK passed Settings, language persistence, History, pitch quiz,
metronome, Em/Am transitions and practice-background-stop checks. Normal song
playback remained PLAYING after Home and advanced from 3126 to 6121 ms. Offline
reference notes, saved song sessions and language preferences survived restart.
Emulator tests do not establish physical-speaker audibility.

Swift core: 29 passed, including the opt-in live Aya contract. iPhone and iPad
beginner UI tests passed. The physical Mac mini passed reference-note completion,
metronome clock and stop checks. The KVM Mac suite passed 32 of 33: the remaining
reference-audio failure is attributable to its missing audio device and was not
reported as a pass. Live lyric iPhone UI tests could not reach the API from the
Mac mini; identical API data and ruby rendering were verified on KVM Mac and
Android. Simulator logs also warn about synchronous AVAudioSession activation;
keep this as a responsiveness follow-up, not a fabricated clean-log claim.

Backend tests: 32 passed. Deployment tests: 8 passed. Store-tool tests: 40 passed.
Private screenshots, native results and hash-bound QA receipts are retained under
`store/.runtime/practice-012/`; Apple xcresults also remain on their test Macs.

iOS and universal macOS 0.1.2 (4) packages are signed and prepared. This is not an
Apple review submission or TestFlight delivery. Preserve 0.1.1's existing review
queues. See `store/native-update-2026-10-05.md` for provider state.

## Scope of the First Beginner Tools

These tools teach listening, steady pulse and two comfortable chord changes.
They do not yet implement a microphone pitch meter, singing score or automatic
guitar-performance grading. Any future "Nail the Pitch"-style feedback needs
explicit microphone permission, calibrated latency, octave-error handling and
real acoustic validation. Keep it separate from this honest listening score.
