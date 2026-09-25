# Musia: Music Within Reach

## The User's Starting Point

The founder bought a guitar and practiced for three years, including lessons and
roughly six months on one song. Many chord shapes are familiar, but transitions
are uneven. Singing, catching a tune, understanding rhythm and knowing when a
lyric or chord enters remain difficult. Isolated drills feel disconnected from
making music. After stopping for half a year, another generic chord chart is not
enough.

The request is to convert that experience into a useful native iOS/Android app
and a web workspace: understand a favorite song, hear the pulse, play along at a
comfortable speed, and eventually create music. Singing ability and knowledge of
theory must not be prerequisites. This is not a claim that the user lacks musical
potential, and the product must not punish or shame imperfect practice.

## First Complete Learning Loop

1. **Listen:** hear four count-in beats and an Em/Am reference accompaniment.
2. **Tap:** follow the pulse; observe steadiness separately from systematic device
   latency. Do not label this as guitar or vocal accuracy.
3. **Play:** one down-strum per bar first, then one per beat when comfortable.
4. Slow playback to 25–200%, preserving pitch; loop one bounded phrase.
5. Save time practiced locally, return later, and choose a familiar song.

The reference exercise is 60 BPM, 4/4, four count-in seconds followed by Em at 4s,
Am at 8s, Em at 12s and Am at 16s. The final chord decays through 22s. Its audio is
synthesized from known pitches, not advertised as a recorded guitar performance.

Real songs are a separate exploration surface: the player's corrected lyrics
and timing are reusable, but automatically inferred beats, chords and melody
are explicitly estimates. A generated F0 contour is not a verified lead sheet.
Instrumental gaps have no invented lyric rows. Vocal versions keep their own
timelines. The existing Fun site and its production/recording workflow remain
unchanged.

## Architecture

- `apps/web`: accessible browser practice workspace; no bundled third-party
  analytics, external font service, microphone or login.
- `apps/android`: Kotlin/Compose with native Media3 playback, not a WebView.
- `apps/ios`: SwiftUI with AVFoundation playback, not a web shell.
- `musia/learning.py`: small read-only FastAPI projection of public catalog data.
- `musia.lazying.art`: learning app, hosted behind existing Huanayun ingress.
- `fun.lazying.art`: existing music/video publication experience.

The public API does not mount a filesystem or expose Studio sessions, commands,
generation workers, credentials or uploads. LazyEdge's authenticated private
worker architecture is reserved for a later isolated generation service. Public
curated playback does not need a GPU tunnel or model credentials.

Learning progress and drafts are device-local in the first release. Export is
available; cloud sync is not implied. Creative briefs are saved inputs, not fake
generation results. The full existing local Musia production pipeline remains
available independently.

## Quality Gates

Three checks mean different evidence, not three repetitions of the same model:

1. Validate event schemas, time bounds, ordering, vocal identity and gaps.
2. Cross-check automatic analysis against the source audio and a second method
   or known reference. Keep disagreements visible and confidence conservative.
3. Before assessed lessons, have musical content reviewed against a known score
   or by a qualified reviewer. Do not label unreviewed song analysis verified.

Automated tests cover boundary timing, rate-aware taps, loop safety, catalog
visibility, response privacy and request denial. Browser checks cover playback,
responsive layout, history persistence and accessibility basics. Native builds
need on-device interruption/background tests before a production quality claim.

## Store Delivery

Reuse the existing LazyingArt LLC developer accounts and privately established
self-test recipient from Bunko's successful receipts. Musia owns its own bundle
identifier (`art.lazying.musia`), signing configuration, store records, metadata,
screenshots and privacy declarations. Do not copy another app's prices,
provisioning profiles or review answers.

Track these as distinct evidence-backed stages: build, signed archive, upload,
provider processing, TestFlight/internal-test availability, invitation delivered,
formal review submission, approval and public availability. Existing account
access is not proof that any stage is complete. Public documents must not contain
private recipients, account credentials, browser profiles or raw agent sessions.

## Next Product Layers

- More verified exercises: chord changes, down/up strumming, fingerpicking and
  melody-to-chord relationships, with accessible visual/audio alternatives.
- User-selected goals and progressive routines based on practice, not inflated
  streak rewards or unsupported musical ability scores.
- Optional microphone practice only after explicit consent, latency calibration,
  validated pitch/onset feedback, retention rules and safe permission recovery.
- AI explanations grounded in reviewed musical facts; distinguish suggestions
  from measured data. Never claim an AI guarantees theory or transcription.
- Authenticated creation jobs that reuse Musia's quality-first production and
  lyric audit workflow, with budgets, rights checks and durable artifacts.

## References

- [Apple AVAudioSession](https://developer.apple.com/documentation/AVFAudio/AVAudioSession)
- [Apple time/pitch algorithms](https://developer.apple.com/documentation/avfoundation/time-pitch-algorithm-settings)
- [Android Media3 background playback](https://developer.android.com/media/media3/session/background-playback)
- [Apple review guidelines](https://developer.apple.com/app-store/review/guidelines/)
- Local implementation patterns: LazyOracle and AiMemo for native apps;
  Bunko, L-And-N and EchoMind for store operations; LazyEdit and LazyEdge for
  protected Huanayun ingress and deployment discipline.
