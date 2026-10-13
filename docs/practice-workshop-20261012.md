# Beginner Practice Workshop

October 13: this workshop is included in the **0.2.1 test update**, with a
simpler chat-first Create interface and new native UI checks. See the
[delivery record](../store/testflight-0.2.1.md) for exact platform availability.
The October 12 local-only verification below is historical, not latest delivery.

## Intent

Build from the owner's experience: several years of guitar chords without a
clear feel for pitch, rhythm or how singing fits a phrase. Practice should give
small audible references, repeatable actions and honest feedback. It must not
pretend that a tap, quiz or model estimate proves good guitar playing.

The three static lesson cards are removed from the native Lessons/Practice hub.
The existing First Pulse song and backwards-compatible lesson API remain.

## Implemented

- Listen: hear Do/Re/Mi, then a full octave, with numbered and letter-note names.
- Recognize: compare a random reference with Do; score the first answer only.
- Sing / Match a note: explicitly request three seconds of a comfortable hum or
  sung note; compare measured monophonic pitch with the selected reference.
- First Pulse rhythm workshop: 30-240 BPM, tap tempo, 2/4, 3/4, 4/4 or 6/4,
  beat/eighth/triplet subdivisions, accented downbeats and audio-clock animation.
- Chord changes: click only, Em/Am, or C/Am/F/G; hold, down-strum or arpeggio
  reference. Existing verified guitar shapes are reused. References are synthesized,
  not recordings of guitar strings or a detected guitar performance.
- Beat feedback requires at least four taps. The timing window is 8% of a beat
  with a 40 ms floor. Report signed bias and average absolute offset; Bluetooth
  and input latency can affect the result. Separate monotonic debouncing from the
  looping audio timeline, so taps across a loop boundary are not discarded.

Do is C in these exercises: this is a declared fixed reference, not a claim
that movable-Do solfege always means C. Six quarter-note beats are 6/4, not 6/8.
Listening, recognize and microphone-match scores are separate measures.

## Pitch Boundary

The bounded monophonic estimator implements the YIN difference/normalization
method described by [de Cheveigne and Kawahara (2002)](https://pubmed.ncbi.nlm.nih.gov/12002874/).
Input is 16 kHz mono; frames have 2048 samples, stride 1024, range 70-1000 Hz.
Reject DC/silence, non-finite input, clipping and insufficient voiced evidence.
Require ten measurable frames and at least 25% voiced coverage. Feedback is the
percentage of measurable frames within 50 cents of the reference plus median
pitch offset; it is **not a singing-quality grade**. Octave ambiguity, breathy
voice, accompaniment and noisy hardware remain practical limitations.

Android keeps the take in memory. Apple uses a temporary WAV removed after
measurement, cancellation or handled failure. Neither uploads audio or keeps it
in practice history. Permission is requested only on the capture button; denial
keeps listening usable. Leaving/backgrounding/interruption cancels practice.
Normal song background playback remains supported. A killed process can leave
an OS temporary file until cleanup; do not claim crash-proof immediate erasure.

## Code

Shared-equivalent algorithms: `apps/ios/Musia/Core/{BeginnerPractice,PracticeWorkshop,PitchPractice}.swift`
and Android files of the same names under `art/lazying/musia`.
Swift `PitchCapture` owns permission, local take and cleanup; `PitchMatchView`
owns the focused exercise. Android `PitchMatchPanel` owns the equivalent lifecycle.
`apps/scripts/register-practice-sources.rb` adds source references without
regenerating signing settings or all Xcode project IDs.

## Verification

12 October 2026 local builds, not new store uploads:

- Android debug/release: 53 unit tests each, no failures; both lint and builds pass.
- iOS simulator and native macOS Debug compile pass with shared sources.
- Swift core/catalog/Watch protocol: 69 tests, one opt-in live test skipped,
  no failures. This does not exercise a physical Watch or microphone.
- Mac source/privacy/entitlement/project registration validation passes.
- API: 35 tests pass, including validators/compression and unchanged audio Range.
- Android owned-emulator UI smoke passes: default languages, Settings history,
  reference note, first-answer score, Match a note, silence abstention, beat tap,
  audio-clock Em/Am transition, background stop, live Aya catalog loading.
- Android microphone denial was separately exercised before granting the QA
  emulator permission. Silent input produced no score. This is not a physical
  voice/speaker test. Apple microphone permission/capture still needs device QA.

Evidence: `store/.runtime/practice-20261012/android-smoke/`. The headless emulator
was stopped after evidence capture, retaining its data. Apple build/test logs are
in the isolated `~/Projects/Musia-practice-20261012/store/.runtime/` on the Mini.
Do not replace the installed TestFlight app with the unsigned development build.

```sh
python -m unittest discover -s tests -p test_learning_api.py -q
python apps/macos/scripts/validate.py
cd apps/android
bash gradlew --no-daemon --max-workers=2 :app:testDebugUnitTest :app:lintDebug
```

`tools/store/android_practice_smoke.py --output <absolute-private-directory>`
replays native UI checks. `--silent-microphone` is only for an explicitly
authorized, silent Musia QA emulator with permission already granted. Do not run
it against someone's live recording session or label silence as successful singing.

Before release: test natural voices on real iOS/Android/Mac microphones, quiet
and noisy rooms, headphones/Bluetooth, permission denial, interruption and
account-independent offline practice. Report octave errors and abstention rates;
do not turn a synthetic-tone pass into a promise of calibrated vocal scoring.
