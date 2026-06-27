# Musai Product Architecture Reference

## Name

**Musai**

Meaning: **Music + AI**

Pronunciation: **mu-sai**

Tagline:

> Musai - sing every song in any language.

Musai is short, global, and AI-native. It keeps the feeling of a music product while avoiding more generic language-learning names such as LinguaTune or SongLingo.

Earlier working name:

**SingBabel** - useful as a concept phrase, but Musai is stronger as a one-word product name.

This is not a trademark check. A real naming process should still include trademark, domain, app-store, and social-handle checks.

## One-Line Product Idea

Musai is a music player and generation studio that re-sings a song in another language with adapted lyrics and professional vocal rendering.

The core product is **AI song localization**, not simple song translation.

## Key Insight

This is not:

```text
English lyrics -> Chinese translation -> AI TTS
```

It should be:

```text
song audio
-> vocals/instrumental separation
-> lyric and timing extraction
-> melody/F0 extraction
-> singable lyric adaptation
-> AI singing voice generation
-> mixing/mastering
-> playable translated song
```

The hardest part is **singable lyric adaptation**. The system must preserve meaning while fitting rhythm, rhyme, syllables or mora, phrase duration, emotion, and melody. For Chinese, tone-melody compatibility also matters because lexical tones can clash with melodic contour.

## Recommended Open-Source Stack

| Module | Recommended Tool | Role |
| --- | --- | --- |
| Vocal/accompaniment separation | Demucs v4 | Separate vocals, drums, bass, and accompaniment stems. |
| Lyrics/timing extraction | WhisperX | Transcribe vocals and obtain word-level timestamps with forced alignment. |
| Pitch/melody extraction | RMVPE, CREPE, Basic Pitch | Extract vocal F0, melody, or MIDI-like phrase information. |
| Singable lyric adaptation | LLM + custom constraint checker | Generate target-language lyrics that fit duration, syllable count, rhyme, emotion, and melody. |
| Melody-preserving lyric replacement | YingMusic-Singer-Plus | Supports lyric manipulation, CN<->EN translation, code-switching, alignment-free operation, and melody preservation. |
| Zero-shot/cross-language singing | SoulX-Singer | Supports F0/MIDI-conditioned singing, timbre cloning, cross-lingual synthesis, and singing voice editing. |
| Full-song generation alternative | ACE-Step 1.5 or YuE | Useful for full adapted-song generation modes rather than strict source-song localization. |
| Voice cloning/timbre transfer | GPT-SoVITS, RVC-style SVC | Useful for voice timbre transfer, but not enough alone for professional lyric-changing singing. |

## MVP Architecture

Build the first version as a **web music player plus generation studio**, not a pure mobile app.

Recommended components:

| Layer | Choice |
| --- | --- |
| Frontend | Next.js or React Native |
| Backend API | FastAPI |
| Worker queue | Celery or RQ + Redis |
| Audio stack | FFmpeg, PyTorch, torchaudio, librosa |
| Storage | S3-compatible object storage |
| Database | PostgreSQL |

## MVP Pipeline

1. User uploads a song they own or have permission to transform.
2. Demucs separates `vocal.wav` and `accompaniment.wav`.
3. WhisperX transcribes vocals and generates word-level timings.
4. RMVPE, CREPE, or Basic Pitch extracts melody, F0, and phrase timing.
5. The lyric adaptation engine creates several target-language candidates.
6. The constraint checker scores candidates for fit and flags weak lines.
7. YingMusic-Singer-Plus or SoulX-Singer generates the new singing vocal.
8. FFmpeg and audio post-processing mix the new vocal with the original accompaniment.
9. The player shows the original lyrics, adapted lyrics, translated meaning, and generated localized song.

## Lyric Adaptation Constraints

The lyric engine should generate multiple candidates per phrase and score them against explicit constraints:

| Constraint | Goal |
| --- | --- |
| Phrase duration | Target lyric must fit the same time window as the source phrase. |
| Syllable/mora count | Target lyric should match singable note density. |
| Natural language | Lyrics must sound native, not mechanically translated. |
| Meaning | Preserve the emotional and narrative intent, not just literal words. |
| Rhyme | Preserve rhyme where possible, especially line endings and hooks. |
| Prosody | Stress, pauses, and emphasis should land on musically important notes. |
| Tone-melody fit | Especially important for Mandarin, Cantonese, Vietnamese, Thai, and other tonal languages. |

Recommended implementation pattern:

1. Segment the source song into phrase-level units.
2. For each phrase, collect source lyric, timestamps, melody contour, syllable count, rhyme group, and emotional label.
3. Ask the LLM for several target-language candidates.
4. Score each candidate with deterministic checks and model-based quality checks.
5. Regenerate weak candidates with focused feedback.
6. Keep a human-editable lyric review screen in the MVP.

## Practical Product Scope

Start with:

```text
English <-> Chinese
```

Reason:

YingMusic-Singer-Plus is especially relevant for CN<->EN lyric translation/editing and bilingual processing. This makes English/Chinese the strongest first language pair while the lyric constraint engine is still immature.

Add later:

- Japanese
- Korean
- Cantonese
- Spanish
- French
- Other high-demand localization languages

## Player Experience

The product should feel like a music player with a generation workflow behind it.

Core screens:

- Upload/import song
- Separation and analysis progress
- Lyric adaptation review
- Voice/style selection
- Generated localized song player
- Side-by-side lyric view

The player should show:

- Original lyric
- Adapted singable lyric
- Literal translated meaning
- Phrase timing
- Confidence or fit score
- Regenerate/edit controls per line

## Legal Design

The first version should support:

- User-owned songs
- Licensed songs
- Public-domain songs
- Creator-uploaded songs
- Internal demos with cleared rights

Avoid positioning the first version as:

```text
Upload any Spotify or YouTube song and publish the Chinese version.
```

Safer positioning:

```text
Translate and re-sing your own song into another language.
```

Translated songs, lyric adaptations, new arrangements, vocal performances, and mixed recordings can create derivative/adapted works. Rights handling should be designed into the product from the start.

## Product Positioning

Preferred positioning:

> Musai - AI song localization.

Avoid positioning it as only:

> AI song translation.

Reason:

"Translation" sounds like a text utility. "Localization" signals that the song is adapted musically, lyrically, and culturally for another language.

## Development Milestones

### Milestone 1 - Offline Research Prototype

- Upload one local song.
- Run Demucs separation.
- Run WhisperX transcription and alignment.
- Extract melody/F0.
- Produce phrase-level JSON.
- Manually generate adapted lyrics.
- Test one singing model for replacement vocals.

### Milestone 2 - Lyric Constraint Engine

- Add phrase segmentation.
- Add syllable counting for English and Chinese.
- Add phrase-duration checks.
- Add rhyme/ending checks.
- Add tone-melody heuristic for Mandarin.
- Add candidate scoring and regeneration.

### Milestone 3 - Web Studio MVP

- Add FastAPI backend.
- Add worker queue.
- Add object storage.
- Add Next.js studio UI.
- Add job progress and artifact browsing.
- Add side-by-side lyric editor.
- Add final mix export.

### Milestone 4 - Product Alpha

- Add accounts and project history.
- Add licensing/ownership acknowledgement.
- Add voice/style presets.
- Add quality scoring and manual correction tools.
- Add creator export workflow.

## Open Questions

- Which singing model is most stable for full-length commercial-style songs today?
- How much manual lyric editing is acceptable in the first creator workflow?
- Should voice cloning be included in the MVP or delayed for legal and safety reasons?
- Should Musai preserve the original singer timbre, or default to licensed synthetic voices?
- Should the first market be creators, localization studios, karaoke users, or language learners?

