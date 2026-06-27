# Deep research: tools for **Musai**

For **Musai**, the best architecture is **not one model**. It should be a modular AI music-localization pipeline:

```text
song upload
→ rights / ownership check
→ vocal + instrumental separation
→ lyrics transcription
→ word / phoneme timing
→ melody / pitch extraction
→ singable lyric adaptation
→ AI singing synthesis
→ voice/timbre conversion, optional
→ mixing + mastering
→ music-player interface
```

The closest research pattern is **singing-voice-to-singing-voice translation**: lyrics transcription, phoneme alignment, melody extraction, lyric translation, then singing voice synthesis. PolySinger describes this exact type of pipeline. ([arXiv][1])

My recommended MVP stack is:

> **Demucs + WhisperX + RMVPE + Basic Pitch + LLM lyric adapter + YingMusic-Singer-Plus + SoulX-Singer + FastAPI + Celery/RQ + Redis + Docker + wavesurfer.js**

---

## 1. Vocal / instrumental separation

This is the first technical step. You need to split the original song into:

```text
vocals.wav
instrumental.wav
drums.wav, bass.wav, other.wav optional
```

### Best tool: **Demucs**

**Use it first.** Demucs v4 is a Hybrid Transformer source-separation model and can separate vocals, drums, bass, and other accompaniment. The repository reports strong MUSDB HQ performance for v4. ([GitHub][2])

Use Demucs for:

```text
original song → vocal stem + accompaniment stem
```

### Alternatives

| Tool                            | Use case                        | Comment                                      |
| ------------------------------- | ------------------------------- | -------------------------------------------- |
| **Demucs**                      | Main default                    | Best open-source default for Musai           |
| **Spleeter**                    | Fast baseline                   | Older, simple, useful for quick tests        |
| **UVR / MDX / Roformer models** | Better stem quality experiments | Good for comparing separation quality        |
| **AudioSep**                    | Text-guided separation          | Interesting research direction, not MVP core |

### Recommendation

For v1:

```text
Demucs 4-stem separation
```

For v2:

```text
Demucs + MDX/Roformer ensemble, then choose the cleaner vocal stem automatically
```

---

## 2. Lyrics transcription and timing

After separation, run speech recognition only on the **isolated vocal**.

### Best tool: **WhisperX**

WhisperX is very useful because it gives fast ASR, word-level timestamps, VAD-based segmentation, and diarization support. Its repo describes batched inference, faster-whisper backend support, and wav2vec2-based alignment for more accurate word timestamps. ([GitHub][3])

Use it for:

```text
vocals.wav → lyric text + word-level timestamps
```

### Supporting tool: **faster-whisper**

faster-whisper is a CTranslate2 implementation of Whisper and is designed to run faster with lower memory use, including int8 quantization. ([GitHub][4])

Use it when:

```text
you need cheaper / faster ASR inference
```

### Other useful tools

| Tool                        | Role                                                     |
| --------------------------- | -------------------------------------------------------- |
| **WhisperX**                | Best default for transcription + word timestamps         |
| **faster-whisper**          | Fast inference backend                                   |
| **stable-ts**               | Better timestamp stabilization for Whisper-style outputs |
| **Montreal Forced Aligner** | More serious phoneme / word forced alignment             |
| **Aeneas**                  | Lightweight text-audio alignment, useful for experiments |

### Recommendation

For Musai v1:

```text
WhisperX → word-level timing
```

For Musai v2:

```text
WhisperX → lyric text
Montreal Forced Aligner → phoneme-level timing
```

---

## 3. Melody, pitch, rhythm, and MIDI extraction

This is essential. The translated lyric must fit the original melody.

You need:

```text
note timing
pitch contour
phrase boundaries
syllable count target
vocal rhythm
```

### Best vocal pitch tool: **RMVPE**

RMVPE is a robust vocal pitch estimation model designed for polyphonic music. It is directly relevant because your input is a full song or separated vocal, not clean studio monophonic speech. ([GitHub][5])

Use it for:

```text
vocals.wav → F0 pitch curve
```

### Best audio-to-MIDI helper: **Basic Pitch**

Basic Pitch is Spotify’s automatic music transcription tool. It generates MIDI with pitch bends and is designed to work on many instruments, though it works best when one instrument is present at a time. ([GitHub][6])

Use it for:

```text
vocals.wav → approximate MIDI melody
```

### Other tools

| Tool                   | Role                                                   |
| ---------------------- | ------------------------------------------------------ |
| **RMVPE**              | Best default F0 extractor for vocals                   |
| **Basic Pitch**        | Audio-to-MIDI melody extraction                        |
| **CREPE / torchcrepe** | Monophonic pitch tracking                              |
| **librosa.pyin**       | Classical F0 estimation baseline                       |
| **librosa**            | Beat tracking, onset detection, chroma, audio analysis |

### Recommendation

Use both:

```text
RMVPE → accurate F0 curve
Basic Pitch → MIDI-like note structure
```

RMVPE tells you **how the singer actually moved**. Basic Pitch gives you a cleaner **musical skeleton**.

---

## 4. Singable lyric adaptation

This is the heart of Musai.

Do **not** do simple translation:

```text
English lyric → Chinese translation
```

That will sound bad.

You need:

```text
English lyric
→ meaning extraction
→ emotional intent
→ phrase length target
→ syllable / character count target
→ rhyme target
→ Chinese tone-melody compatibility
→ singable Chinese lyric
```

Research on English-to-Mandarin song translation stresses that the system must preserve meaning, singability, and intelligibility, and that tonal-language translation has the extra problem of aligning word tones with melody. ([ACL Anthology][7]) Another English-Chinese lyric-translation paper frames lyric translation as constrained translation and evaluates length, rhyme, and word-boundary constraints. ([ACL Anthology][8])

### Tools you need here

| Tool                                       | Role                                                    |
| ------------------------------------------ | ------------------------------------------------------- |
| **Commercial or local LLM**                | Generate lyric candidates                               |
| **Custom constraint checker**              | Reject lyrics that do not fit the melody                |
| **pypinyin**                               | Convert Chinese characters to pinyin / tone information |
| **jieba**                                  | Chinese word segmentation                               |
| **phonemizer**                             | Multilingual text-to-phoneme conversion                 |
| **Rhyme dictionary / custom rhyme scorer** | Chinese rhyme checking                                  |
| **Prosody scorer**                         | Check stress, rhythm, tone, phrase fit                  |

pypinyin converts Chinese characters to pinyin, including formats useful for pronunciation processing. ([GitHub][9]) jieba supports Chinese word segmentation modes and custom dictionaries. ([GitHub][10]) phonemizer provides command-line and Python phonemization across many languages using backends such as espeak, festival, and segments. ([GitHub][11])

### Minimum lyric-adaptation constraints

For every lyric phrase, store:

```json
{
  "source_text": "I found a love for me",
  "target_language": "zh-CN",
  "phrase_start": 12.31,
  "phrase_end": 15.82,
  "duration_seconds": 3.51,
  "target_syllables": 7,
  "melody_notes": ["E4", "F#4", "G#4", "G#4", "F#4", "E4", "C#4"],
  "rhyme_group": "i",
  "emotion": "tender, intimate",
  "meaning": "The singer has found someone they love"
}
```

Then ask the lyric engine to generate several candidates:

```text
literal version
singable version
poetic version
pop-song version
shorter version
more emotional version
```

Then score each candidate.

### Recommendation

Build your own **Lyric Adaptation Engine**. This should be one of Musai’s core inventions.

Name it internally:

```text
Musai LyricFit
```

---

## 5. Singing voice synthesis

This is where the new Chinese lyric becomes sung audio.

There are two main strategies:

```text
A. Preserve original melody and generate new singing
B. Generate a full new song from lyrics
```

For Musai, strategy **A** is better.

---

### Best tool for CN↔EN lyric editing: **YingMusic-Singer-Plus**

This is probably the most relevant open-source project for your idea.

YingMusic-Singer-Plus is a diffusion-based singing-voice synthesis model focused on melody-controllable singing voice editing. Its repo says it supports flexible lyric manipulation, does not require manual alignment or phoneme annotation, supports partial and full lyric changes, insertion/deletion, CN↔EN translation, code-switching, bilingual IPA tokenization, and 44.1 kHz stereo output. ([GitHub][12])

Use it for:

```text
original vocal melody + new Chinese lyric → new sung Chinese vocal
```

### Best zero-shot / cross-language option: **SoulX-Singer**

SoulX-Singer is also highly relevant. Its repo describes zero-shot singing voice synthesis, F0/MIDI conditioning, singing voice conversion, timbre cloning, lyric editing, and cross-lingual synthesis. ([GitHub][13])

Use it for:

```text
new lyrics + melody/F0 + reference voice → new vocal
```

### Research toolkit: **Amphion**

Amphion is a broader open-source toolkit for audio, music, and speech generation. It includes support for TTS, singing voice synthesis, voice conversion, singing voice conversion, evaluation metrics, and vocoders. ([GitHub][14])

Use it for:

```text
research experiments
model comparison
future custom training
```

### Classical SVS baseline: **DiffSinger**

DiffSinger is an official PyTorch implementation of a diffusion-based singing voice synthesis system. It is useful as a research baseline, but less directly product-ready than YingMusic-Singer-Plus for your specific lyric-editing goal. ([GitHub][15])

### Other SVS tools

| Tool                      | Use case                                           |
| ------------------------- | -------------------------------------------------- |
| **YingMusic-Singer-Plus** | Best first choice for CN↔EN lyric-changing singing |
| **SoulX-Singer**          | Best cross-language / zero-shot direction          |
| **Amphion**               | Research framework                                 |
| **DiffSinger**            | Academic SVS baseline                              |
| **OpenUtau**              | Manual singing-synthesis editor                    |
| **NNSVS**                 | Research singing voice synthesis                   |
| **Muskits**               | Research toolkit for SVS                           |

### Recommendation

For Musai v1:

```text
YingMusic-Singer-Plus first
SoulX-Singer second
```

For Musai v2:

```text
Train / fine-tune your own Musai singer model
```

---

## 6. Voice conversion and voice cloning

Important distinction:

```text
Singing synthesis = create the new sung performance
Voice conversion = change the timbre of an existing sung performance
```

Voice conversion alone cannot solve Musai. It can make a Chinese sung vocal sound like a target voice, but it does not automatically create good Chinese singing.

### Useful tools

| Tool            | Role                                         | Caution                                  |
| --------------- | -------------------------------------------- | ---------------------------------------- |
| **RVC**         | Singing voice conversion / timbre transfer   | Popular, useful, but not enough alone    |
| **Seed-VC**     | Zero-shot voice and singing voice conversion | GPL-3.0 license needs care               |
| **GPT-SoVITS**  | TTS / voice cloning / cross-lingual speech   | More speech-focused than singing-focused |
| **so-vits-svc** | Singing voice conversion                     | Useful, but older ecosystem              |

RVC’s repo says it can train a good voice conversion model with relatively small voice data and is MIT licensed. ([GitHub][16]) GPT-SoVITS supports zero-shot TTS from a short sample, few-shot fine-tuning, and cross-lingual inference across several languages, including English, Japanese, Korean, Cantonese, and Chinese. ([GitHub][17]) Seed-VC supports zero-shot voice conversion, real-time VC, and zero-shot singing voice conversion, but its repo lists GPL-3.0 licensing, which matters for commercial product design. ([GitHub][18])

### Recommendation

For v1, avoid cloning famous singers. Use:

```text
default Musai voices
user-consented creator voice
licensed voice library
```

Later add:

```text
“clone my own voice” mode
```

with explicit consent.

---

## 7. Full-song generation tools

These are powerful, but they are not the best MVP path if your goal is:

```text
same song, new language, professional adaptation
```

They are better for:

```text
generate a new song from adapted lyrics
create demo arrangements
make alternate genre versions
```

### ACE-Step 1.5

ACE-Step 1.5 supports local generation, cover generation, repainting, vocal-to-BGM conversion, multi-track features, lyric/timestamp generation, LoRA training, and more than 50 languages according to its repo. ([GitHub][19])

### YuE

YuE is an open-source foundation model for transforming lyrics into full songs, including vocal and accompaniment, across diverse genres, languages, and vocal techniques. Its repo lists Apache 2.0 licensing. ([GitHub][20])

### Recommendation

Do not make full-song generation the center of v1.

Use it as:

```text
“inspiration mode”
“demo arrangement mode”
“rewrite as new song mode”
```

Your main Musai promise should remain:

```text
same song feeling → new language performance
```

---

## 8. Phoneme, pronunciation, and language tools

This part becomes very important when adding Chinese, Japanese, Korean, Cantonese, and other languages.

### Chinese

| Tool                    | Role                                        |
| ----------------------- | ------------------------------------------- |
| **pypinyin**            | Chinese characters → pinyin and tones       |
| **jieba**               | Chinese word segmentation                   |
| **OpenCC**              | Simplified / Traditional Chinese conversion |
| **custom tone checker** | Check Mandarin tone movement against melody |

For Mandarin, your lyric engine should avoid placing awkward falling/rising tones on melody shapes that make pronunciation sound unnatural. It will not be perfect, but even a simple tone-melody penalty will improve results.

### Japanese

| Tool                  | Role                                    |
| --------------------- | --------------------------------------- |
| **MeCab / SudachiPy** | Tokenization                            |
| **pyopenjtalk**       | Japanese phoneme conversion             |
| **kana/romaji tools** | Lyric display and pronunciation support |

### Korean

| Tool                     | Role                         |
| ------------------------ | ---------------------------- |
| **KoNLPy / MeCab-ko**    | Korean tokenization          |
| **g2pK**                 | Korean grapheme-to-phoneme   |
| **Hangul decomposition** | Syllable-level rhythm checks |

### Multilingual

| Tool           | Role                                 |
| -------------- | ------------------------------------ |
| **phonemizer** | General multilingual phonemization   |
| **espeak-ng**  | Backend for many languages           |
| **Epitran**    | Transliteration / phonology research |
| **uroman**     | Universal romanization               |

### Recommendation

For first release:

```text
English ↔ Mandarin Chinese
```

Do not start with “any language” technically. Product copy can say “many languages coming,” but engineering should start with one strong pair.

---

## 9. Mixing, mastering, and audio repair

After AI singing, you need to make the new vocal sit inside the original instrumental.

Basic chain:

```text
noise cleanup
EQ
compression
de-essing
reverb
delay
loudness normalization
limiting
```

### Tools

| Tool                                 | Role                                                      |
| ------------------------------------ | --------------------------------------------------------- |
| **FFmpeg**                           | Format conversion, muxing, loudness normalization         |
| **pedalboard**                       | Python audio effects and VST3 / Audio Unit plugin support |
| **pyloudnorm**                       | Loudness measurement                                      |
| **Matchering**                       | Reference-based mastering                                 |
| **librosa / soundfile / torchaudio** | Audio analysis and file processing                        |

FFmpeg’s `loudnorm` filter supports EBU R128 loudness normalization and can target integrated loudness, loudness range, and true peak. ([FFmpeg][21]) Spotify’s Pedalboard is a Python audio library for reading, writing, rendering, and applying audio effects, with support for common audio effects and VST3 / Audio Unit plugins. ([GitHub][22]) pyloudnorm implements ITU-R BS.1770-style loudness measurement in Python. ([GitHub][23]) Matchering is an open-source audio matching and mastering library. ([GitHub][24])

### Recommendation

For v1:

```text
FFmpeg + pedalboard + pyloudnorm
```

For v2:

```text
automatic vocal-mix model
reference mastering
genre-specific vocal presets
```

---

## 10. Music player interface

The player should not just play audio. It should show the localization process.

### Features to build

```text
original song playback
translated song playback
A/B switch
original lyrics
adapted lyrics
word-level highlighting
phrase timeline
vocal/instrumental solo buttons
generation status
version history
```

### Web tools

| Tool                     | Role                                              |
| ------------------------ | ------------------------------------------------- |
| **wavesurfer.js**        | Waveform, regions, timeline, lyric phrase editing |
| **howler.js**            | Cross-browser audio playback                      |
| **Web Audio API**        | Low-level audio processing                        |
| **Media Session API**    | Lock-screen / OS media controls                   |
| **React / Next.js**      | Main web app                                      |
| **Tailwind / shadcn/ui** | Fast UI development                               |

wavesurfer.js has useful plugins such as regions, timeline, minimap, envelope, and record. ([GitHub][25]) howler.js uses Web Audio by default and falls back to HTML5 Audio, which makes it practical for browser playback. ([GitHub][26]) The Media Session API lets a web app integrate with operating-system-level media controls. ([MDN Web Docs][27])

### Mobile tools

| Tool                          | Role                         |
| ----------------------------- | ---------------------------- |
| **React Native**              | Mobile app                   |
| **Expo**                      | Faster development           |
| **React Native Track Player** | Background music playback    |
| **Flutter**                   | Alternative mobile framework |

For v1, I would build web first. Audio generation is heavy, and web makes iteration much easier.

---

## 11. Backend and job system

Musai is a long-running GPU workflow, so you need a job queue.

### Recommended backend

```text
FastAPI
PostgreSQL
Redis
Celery or RQ
Docker Compose
GPU worker containers
S3-compatible object storage
```

FastAPI is a Python API framework built around type hints and high-performance API development. ([FastAPI][28]) Celery is a distributed task queue for real-time processing and scheduling. ([Celery Documentation][29]) RQ is a simpler Redis-backed Python job queue. ([python-rq.org][30]) Docker Compose defines and runs multi-container applications from a YAML file. ([Docker Documentation][31])

### Recommended service split

```text
musai-api
  FastAPI app
  handles auth, projects, uploads, lyrics, job status

musai-worker-separation
  Demucs / separation models

musai-worker-asr
  WhisperX / faster-whisper

musai-worker-melody
  RMVPE / Basic Pitch

musai-worker-lyrics
  LLM lyric adaptation + constraint scoring

musai-worker-singing
  YingMusic-Singer-Plus / SoulX-Singer

musai-worker-mixing
  FFmpeg / pedalboard / loudness normalization

musai-web
  Next.js player + editor
```

### Recommendation

For your first prototype:

```text
FastAPI + RQ + Redis
```

For production:

```text
FastAPI + Celery + Redis/RabbitMQ + PostgreSQL + S3 + GPU worker autoscaling
```

---

## 12. GPU deployment

You need GPUs for separation, ASR, singing synthesis, and maybe LLM inference.

### Options

| Platform              | Best for                          |
| --------------------- | --------------------------------- |
| **Local workstation** | Research and early prototype      |
| **RunPod**            | Cheap GPU experiments             |
| **Modal**             | Serverless GPU jobs               |
| **Replicate**         | Fast public demos                 |
| **AWS/GCP/Azure GPU** | Serious production                |
| **NVIDIA Triton**     | Serving optimized model endpoints |

RunPod supports serverless GPU endpoints for containerized inference workloads. ([runpod.io][32]) Modal positions itself as infrastructure for AI inference, training, and sandboxed execution. ([Modal][33]) NVIDIA Triton is an inference server supporting multiple frameworks including PyTorch, ONNX, and TensorRT. ([NVIDIA Docs][34])

### Recommendation

Start with:

```text
one local GPU or one rented RunPod machine
Docker Compose
manual job queue
```

Then move to:

```text
serverless GPU workers
separate queues by model type
```

---

## 13. Dataset and evaluation tools

You need evaluation from the beginning, otherwise the model will produce songs that sound impressive once but fail often.

### Metrics to track

```text
stem separation quality
ASR word error rate
word timestamp accuracy
pitch extraction accuracy
lyric syllable fit
rhyme fit
tone-melody penalty
generated vocal naturalness
speaker similarity, if voice cloning is used
mix loudness
human preference score
```

### Tools

| Tool                     | Role                            |
| ------------------------ | ------------------------------- |
| **museval**              | Source-separation evaluation    |
| **FAD / fadtk**          | Audio-generation quality metric |
| **stable-audio-metrics** | Music/audio generation metrics  |
| **pyloudnorm**           | Loudness measurement            |
| **custom lyric scorer**  | Musai-specific quality          |
| **human A/B testing**    | Essential for final judgment    |

museval is commonly used for evaluating music source separation with datasets such as MUSDB18. ([GitHub][35]) Frechet Audio Distance tools such as fadtk are used to evaluate generated audio distributions. ([GitHub][36])

### Musai-specific score

Create your own score:

```text
MusaiScore =
  0.25 * meaning_preservation
+ 0.20 * singability
+ 0.15 * syllable_fit
+ 0.15 * tone_melody_fit
+ 0.10 * rhyme_quality
+ 0.10 * vocal_quality
+ 0.05 * mix_quality
```

This score will become your internal quality compass.

---

## 14. Legal, rights, and safety tools

This is not optional. Musai touches copyright, derivative works, sound recordings, and voice rights.

A translated lyric or musical arrangement can be treated as a derivative work under U.S. copyright concepts; the U.S. Copyright Office lists translations and musical arrangements as examples of derivative works. ([U.S. Copyright Office][37]) Hong Kong also protects musical works, sound recordings, and performers’ performances. ([HKRRLS][38]) Spotify’s current AI policies also target unauthorized AI voice clones and artist impersonation; its support page says music that impersonates an artist’s voice without permission may be removed. ([Spotify][39])

### Product rules I recommend

```text
Allow:
- user-owned songs
- public-domain songs
- licensed songs
- creator-uploaded songs
- user’s own voice
- licensed AI voices

Do not allow:
- cloning famous singers without permission
- publishing transformed copyrighted songs without rights
- pretending the generated song is by the original artist
- scraping lyrics without licensing
```

### Required product features

```text
rights confirmation checkbox
voice consent checkbox
watermark / provenance metadata
private generation by default
DMCA / takedown process
artist impersonation detector
content reporting flow
```

---

# Best complete tool stack

## MVP stack

Use this first:

| Layer                | Tool                                   |
| -------------------- | -------------------------------------- |
| Frontend             | **Next.js + wavesurfer.js**            |
| Backend              | **FastAPI**                            |
| Queue                | **RQ + Redis**                         |
| Database             | **PostgreSQL**                         |
| Storage              | **S3-compatible object storage**       |
| Separation           | **Demucs**                             |
| ASR                  | **WhisperX + faster-whisper**          |
| Melody               | **RMVPE + Basic Pitch**                |
| Lyric adaptation     | **LLM + Musai LyricFit custom scorer** |
| Chinese processing   | **pypinyin + jieba**                   |
| Singing              | **YingMusic-Singer-Plus**              |
| Backup singing model | **SoulX-Singer**                       |
| Mixing               | **FFmpeg + pedalboard + pyloudnorm**   |
| Deployment           | **Docker Compose + rented GPU**        |

This is the stack I would actually build first.

---

## Research stack

Use this to explore higher quality:

| Layer             | Tools                               |
| ----------------- | ----------------------------------- |
| Better separation | Demucs + MDX/Roformer comparison    |
| Better alignment  | Montreal Forced Aligner             |
| Better singing    | SoulX-Singer, Amphion, DiffSinger   |
| Full-song mode    | ACE-Step, YuE                       |
| Voice conversion  | RVC, Seed-VC                        |
| Evaluation        | museval, fadtk, human A/B tests     |
| Mastering         | Matchering + genre-specific presets |

---

# What not to do first

Avoid these traps:

```text
1. Do not build “translation + TTS”.
   It will not sound like a real adapted song.

2. Do not build “RVC-only”.
   RVC changes voice timbre; it does not solve lyric adaptation.

3. Do not start with “any language”.
   Start with English ↔ Chinese and make it excellent.

4. Do not rely only on full-song generation.
   It may lose the original melody, phrasing, and arrangement.

5. Do not ignore copyright and voice consent.
   This can kill the product even if the technology works.
```

---

# Best product direction

The strongest positioning is:

## **Musai — AI song localization**

Not “song translation.”

The technical goal should be:

```text
same melody
same emotion
same arrangement
new language
natural lyrics
professional vocal
```

The first impressive demo should be:

```text
English song → Chinese adapted lyrics → Chinese AI vocal → original instrumental mix
```

And the first serious product should be:

```text
creator uploads their own song
Musai adapts it into Chinese
creator edits lyrics phrase by phrase
Musai regenerates selected lines
creator exports a licensed localized version
```

[1]: https://arxiv.org/html/2407.14399v1 "PolySinger: Singing-Voice to Singing-Voice Translation from English to Japanese"
[2]: https://github.com/facebookresearch/demucs "GitHub - facebookresearch/demucs: Code for the paper Hybrid Spectrogram and Waveform Source Separation · GitHub"
[3]: https://github.com/m-bain/whisperx "GitHub - m-bain/whisperX: WhisperX:  Automatic Speech Recognition with Word-level Timestamps (& Diarization) · GitHub"
[4]: https://github.com/SYSTRAN/faster-whisper "GitHub - SYSTRAN/faster-whisper: Faster Whisper transcription with CTranslate2 · GitHub"
[5]: https://github.com/Dream-High/RMVPE "GitHub - Dream-High/RMVPE · GitHub"
[6]: https://github.com/spotify/basic-pitch "GitHub - spotify/basic-pitch: A lightweight yet powerful audio-to-MIDI converter with pitch bend detection · GitHub"
[7]: https://aclanthology.org/2022.findings-acl.60/ "Automatic Song Translation for Tonal Languages - ACL Anthology"
[8]: https://aclanthology.org/2023.acl-long.27/ "Songs Across Borders: Singable and Controllable Neural Lyric Translation - ACL Anthology"
[9]: https://github.com/mozillazg/python-pinyin/blob/master/README_en.rst?utm_source=chatgpt.com "python-pinyin/README_en.rst at master"
[10]: https://github.com/fxsjy/jieba?utm_source=chatgpt.com "fxsjy/jieba: 结巴中文分词"
[11]: https://github.com/bootphon/phonemizer?utm_source=chatgpt.com "bootphon/phonemizer: Simple text to phones converter for ..."
[12]: https://github.com/ASLP-lab/YingMusic-Singer "GitHub - ASLP-lab/YingMusic-Singer-Plus: YingMusic-Singer-Plus: Controllable Singing Voice Synthesis with Flexible Lyric Manipulation and Annotation-free Melody Guidance · GitHub"
[13]: https://github.com/Soul-AILab/SoulX-Singer "GitHub - Soul-AILab/SoulX-Singer: Official inference code for SoulX-Singer: Towards High-Quality Zero-Shot Singing Voice Synthesis · GitHub"
[14]: https://github.com/open-mmlab/amphion "GitHub - open-mmlab/Amphion: Amphion (/æmˈfaɪən/) is a toolkit for Audio, Music, and Speech Generation. Its purpose is to support reproducible research and help junior researchers and engineers get started in the field of audio, music, and speech generation research and development. · GitHub"
[15]: https://github.com/MoonInTheRiver/DiffSinger "GitHub - MoonInTheRiver/DiffSinger: DiffSinger: Singing Voice Synthesis via Shallow Diffusion Mechanism (SVS & TTS); AAAI 2022; Official code · GitHub"
[16]: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI "GitHub - RVC-Project/Retrieval-based-Voice-Conversion-WebUI: Easily train a good VC model with voice data <= 10 mins! · GitHub"
[17]: https://github.com/RVC-Boss/GPT-SoVITS "GitHub - RVC-Boss/GPT-SoVITS: 1 min voice data can also be used to train a good TTS model! (few shot voice cloning) · GitHub"
[18]: https://github.com/Plachtaa/seed-vc "GitHub - Plachtaa/seed-vc: zero-shot voice conversion & singing voice conversion, with real-time support · GitHub"
[19]: https://github.com/ace-step/ACE-Step-1.5 "GitHub - ace-step/ACE-Step-1.5: The most powerful local music generation model that outperforms almost all commercial alternatives, supporting Mac, AMD, Intel, and CUDA devices. · GitHub"
[20]: https://github.com/multimodal-art-projection/YuE "GitHub - multimodal-art-projection/YuE: YuE: Open Full-song Music Generation Foundation Model, something similar to Suno.ai but open · GitHub"
[21]: https://ffmpeg.org/ffmpeg-filters.html?utm_source=chatgpt.com "FFmpeg Filters Documentation"
[22]: https://github.com/spotify/pedalboard?utm_source=chatgpt.com "spotify/pedalboard: 🎛 🔊 A Python library for audio."
[23]: https://github.com/csteinmetz1/pyloudnorm?utm_source=chatgpt.com "csteinmetz1/pyloudnorm: Flexible audio loudness meter in ..."
[24]: https://github.com/sergree/matchering?utm_source=chatgpt.com "sergree/matchering: 🎚️ Open Source Audio Matching and ..."
[25]: https://github.com/katspaugh/wavesurfer.js/?utm_source=chatgpt.com "katspaugh/wavesurfer.js: Audio waveform player"
[26]: https://github.com/goldfire/howler.js/?utm_source=chatgpt.com "Howler.js - Javascript audio library for the modern web."
[27]: https://developer.mozilla.org/en-US/docs/Web/API/Media_Session_API?utm_source=chatgpt.com "Media Session API - MDN Web Docs - Mozilla"
[28]: https://fastapi.tiangolo.com/?utm_source=chatgpt.com "FastAPI - FastAPI"
[29]: https://docs.celeryq.dev/?utm_source=chatgpt.com "Celery - Distributed Task Queue — Celery 5.6.3 documentation"
[30]: https://python-rq.org/?utm_source=chatgpt.com "RQ: Simple job queues for Python"
[31]: https://docs.docker.com/compose/?utm_source=chatgpt.com "Docker Compose"
[32]: https://www.runpod.io/product/serverless?utm_source=chatgpt.com "Serverless GPU Inference"
[33]: https://modal.com/?utm_source=chatgpt.com "Modal: High-performance AI infrastructure"
[34]: https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/index.html?utm_source=chatgpt.com "NVIDIA Triton Inference Server"
[35]: https://github.com/sigsep/sigsep-mus-eval/?utm_source=chatgpt.com "museval - source separation evaluation tools for python"
[36]: https://github.com/microsoft/fadtk?utm_source=chatgpt.com "microsoft/fadtk - Frechet Audio Distance Toolkit"
[37]: https://www.copyright.gov/title17/92chap1.html "Chapter 1 - Circular 92 | U.S. Copyright Office"
[38]: https://www.hkrrls.org.hk/en/copyright/copyright-protection-in-the-hong-kong-sar/?utm_source=chatgpt.com "Copyright Protection in the Hong Kong SAR"
[39]: https://newsroom.spotify.com/2025-09-25/spotify-strengthens-ai-protections/ "Spotify Strengthens AI Protections for Artists, Songwriters, and Producers — Spotify"
