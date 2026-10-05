# Musia: App Review Answers

October 6, 2026. App 6816265930; bundle art.lazying.musia.
Response to guidelines 4.3 and 4.2.6 for the iOS and macOS submissions.

## 1. What Musia does and the problem it solves

Musia is a standalone song-based music practice instrument. Its starting problem
is personal: our founder had practiced guitar chords for approximately three
years but still struggled to connect chord changes, the beat and sung phrases.
He could form several chords, but could not reliably sing along or decide when
to enter. Repeating an isolated chord or the same assigned song did not explain
how those parts fit together.

The app puts a recording, its lyric phrases, analyzed chord changes and guitar
finger positions on one playback timeline. A learner can slow playback from
25% to 200% without deliberately transposing the audio, loop a phrase or choose
A/B markers, then return to the same passage. First Pulse supplies a known,
locally synthesized Em/Am exercise rather than requiring the learner to start
with uncertain analysis of a full song. Practice history is stored locally.

The latest build, 0.1.2 (4), adds local Do Re Mi reference tones and listening
quizzes, plus an adjustable 40-160 BPM metronome with optional Em/Am changes.
English, Chinese and Japanese lyric tracks can be shown together, with pinyin
and furigana where supplied. Each track belongs to the selected vocal recording;
changing translations does not silently switch the recording. No account,
microphone or second app is required.

## 2. Intended users

The primary audience is adult beginners and returning hobbyist guitar players
who can form some chords but struggle with timing, listening and playing along.
In particular, it is for someone who cannot confidently sing or read a score
and wants to start by hearing and repeating a short, manageable passage.
Multilingual listeners can follow unfamiliar sung words without choosing between
their translation and the original lyric. It is not a clinical hearing tool,
professional transcription service, children's assessment product or a claim
that a quiz can grade a person's singing or guitar performance.

## 3. The need addressed

Musia joins three steps: a reliable elementary reference, practice on a real
recording, and understandable words/chord shapes at the same media time. A user
can learn a pulse with Em/Am, isolate one lyric phrase, slow it down, and see the
corresponding fingering without moving between unrelated applications.

We do not claim to be the only app with loops, chord diagrams or a metronome.
The specific product is this beginner workflow applied to our own multilingual
music catalog, with independently timed translations for each vocal version.
The distinction between the known reference exercise and automatically analyzed
song data is explicit. Estimated chords, beats and melody are not represented
as a guaranteed score or as a performance grade.

## 4. Beta testing and feedback applied

This has been a small founder-led beta, not a large external study. The founder
installed TestFlight on iPhone, reported that the mini-player covered bottom
navigation and that some chords had no diagram, and later confirmed audible and
locked-screen playback. The 0.1.1 binary submitted on September 30 already
contained the fixes: navigation-safe mini-player placement and all 24 major/minor
guitar shapes, including open/muted strings, barres and alternate fret windows.
Phone/tablet rotation and enlarged-text regression checks were added.

Subsequent feedback requested simultaneous English/Chinese/Japanese lyrics,
pronunciation readings, less prominent history, and very elementary listening,
tempo and chord exercises. These are implemented in 0.1.2 (4), which is now
available to the existing internal tester on both Apple platforms. We distinguish
those new changes from the features present in the rejected 0.1.1 submission.
We do not claim that the owner has completed a new physical-iPhone acceptance
test of every 0.1.2 feature.

Engineering checks include 29 Swift core tests, iPhone/iPad beginner UI tests,
and reference-audio/metronome runtime tests on an audio-capable physical Mac.
These are separate from human beta feedback. A virtual Mac without an audio
device failed its audio test; a separate live-catalog iPhone simulator test had
a test-host network timeout. Those results were retained, not reported as passes.
The new release-tool checks passed 42 tests. No production-readiness claim rests
solely on a simulator screenshot or successful upload.

## 5. Standalone product and other company apps

Musia is a standalone product under LazyingArt LLC, not a required module of
another app or a separate app for each song/language. iPhone, iPad and Mac use
the same Musia app record. All supported music languages remain in this app.
It has no dependency on an EchoMind login, company credit balance or companion
purchase. Other app records under the company have different primary jobs:

- Bunko: multilingual book reading, offline books, dictionaries and annotations.
- OnlyIdeas: research-paper reading, document conversion and research discussion.
- EchoMind: AI conversations, social communication and language assistance.
- AiMemo: notes, tasks, voice capture and an organizational assistant.
- L & N: speech articulation and recorded pronunciation practice.
- ClearPair Japanese, Korean, Mandarin, Cantonese, English, Arabic Letters,
  L & R, and H & F: letter/speech contrasts, not song harmony or guitar practice.
- LazyEdit Studio: video processing, editing, subtitles and media publication.
- LazyOracle and Auspice: traditional symbolic-system study and reflection.
- LazyArtCoin: platform credits/community records and public blockchain balances.
- LazyGame: turn-based shared game rooms, initially Weiqi.
- SHI: a historical strategy narrative.
- GlassAgent: a glasses/camera-assistant integration project.
- weStory: a separate story project; we are not claiming that this record is
  currently publicly available or that its prospective features are shipped.

This comparison describes scope, not an assertion that every listed app is
approved or on sale. None of these is required to use Musia. Shared language
readings alone do not make a book reader or speech-contrast exercise a
song-timed guitar practice instrument.

## 6. Why this is not a content add-on to another app

Songs can be displayed as media in a general reader or editor, but the complete
Musia workflow requires a different interaction model: the actual audio playhead
drives phrase loops, beat/chord transitions, fingering and timed sung words.
Local synthesis supplies known reference pitches and an accented metronome;
practice state is distinct from books, conversations or edited-video projects.
Adding all this to the reader, notes, speech or editing apps would introduce an
entire music-learning product, not unlock a content pack. Users do not need to
purchase unrelated reading, chat or video functionality to practice a song.
We keep music languages and recordings consolidated inside Musia.

## 7. Shared code, frameworks and assets within the company

The iOS and macOS editions of Musia intentionally share MusiaCore (music data,
timelines, lyric tokens/readings, guitar shapes, reference synthesis and practice
state), playback/catalog services and SwiftUI practice views. Mac supplies its
own window, sidebar, menu and lifecycle integration. This is the same product
on two platforms, not a second rebranded product.

The shipped native targets use Apple's SwiftUI, AVFoundation, MediaPlayer,
Combine, Foundation and platform UI frameworks. The inspected project has no
third-party runtime package dependency and no embedded web-app shell. Native
core and view code is maintained in the Musia repository. An exact-file audit
of 22 Musia Swift files against tracked Swift sources in ten nearby company
workspaces found no whole-file matches; this is a limited audit, not a claim
that no generic technique or small code fragment has ever been reused.

Shared development practices include signing/build automation, store tooling,
hosting/tunnel infrastructure and learning from other projects' native project
setup. They are not another app's feature runtime embedded in Musia. The
GlassAgent integration workspace references Musia as a repository submodule;
this internal integration/reference reuse should not be confused with Musia
embedding a glasses assistant. The separate music/video production workflow
also passes recordings to our video tools. That content handoff is not shared
native UI or a relabeled application. Musia does not ship the proposed shared
company login integration in this release.

## 8. Third-party code or content libraries

The reviewed native app targets do not include a third-party app codebase,
commercial app template, content-catalog SDK or app-generation runtime.
The musical definitions such as chord tones and equal-tempered pitch frequencies
are standard music knowledge, implemented and tested in Musia's own core.
Xcode project-generation utilities are build tools, not a bundled app service.

Separate desktop production uses tools such as ACE-Step and audio-analysis
software to create recordings and prepare timing/chord data. Those tools and
model weights are not inside the submitted iPhone or Mac binary, and the native
app does not promise in-app AI song generation. The library contains recordings
created by the owner, including settings of public-domain poems, supplied lyric
translations and artwork. The owner confirmed commercial distribution rights.
We do not claim authorship of the historical poems. The added native functionality
is the synchronized, controllable music-practice experience and local exercises,
not merely access to a third-party generator or its content feed.

## 9. Provider of concept, branding and content

Musia was developed for our own music-learning need and catalog. It is not a
client's or an unrelated partner's branded app being submitted on their behalf.
The account holder is the creator/curator of the recordings and has confirmed
the rights to distribute the catalog, lyrics, translations, vocals and covers.
LazyingArt LLC is submitting its own product and content directly. AI-assisted
development and music production do not change who provides this product;
Musia is not a commercial template being resold to multiple clients.

## Review walkthrough for 0.1.2 (4)

1. Open Library > First Pulse. Play the known Em/Am exercise; try the listening,
   tapping and play-along modes, a slower speed and a phrase loop.
2. Open Aya Chan / Rain of Light. Play one vocal recording, choose multiple lyric
   languages and inspect the timed words/readings and guitar diagrams. Streaming
   requires an internet connection; analyzed musical data remains labeled.
3. Open Lessons > Do Re Mi. Play Do/Re/Mi reference tones; switch to Quiz and
   answer by listening. Only the first answer scores. There is no microphone test.
4. Open Lessons > Metronome & chords. Select 60 BPM, start, and enable Em/Am.
   The chord changes every four beats, using the audio playhead. Stop or leave
   the exercise; practice clicks stop. Normal song background playback is separate.
5. Open Settings > Practice history. Inspect local sessions and export/reset
   controls. No account, subscription or special hardware is needed.

We are answering the requested questions rather than assuming that changing a
build number resolves guideline 4.3. The latest available build adds the specific
practice functions above. Please assess the attached evidence and advise if any
remaining concern relates to a particular duplicated feature or app; we will
address that concrete issue before another submission.
