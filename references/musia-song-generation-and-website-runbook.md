# Musia Song Generation And Website Runbook

This is the practical rulebook for creating beautiful Musia songs and publishing them on `fun.lazying.art`.

## Core Principle

Respect the user's creative instruction, but also respect the rendered audio.

Prompt lyrics are an intention. A generated vocal is evidence. If the vocal does not sing the prompt exactly, publish the lyric/timing data that matches the actual sound, with translations derived from that actual vocal line. Do not force another vocal's timeline or another language's planned lyric onto a render.

## Song Creation Modes

| Input | Best route | Output |
| --- | --- | --- |
| Idea only | Write a producer brief and singable lyric, then use ACE-Step/YuE-style full-song generation | full mixed song candidate |
| Lyrics only | Rewrite for singability first, then generate | full mixed song candidate |
| Lyrics + chords | Preserve chord intent in the prompt and final analysis notes | song candidate with chord reference |
| Lyrics + numbered notation / melody sketch | Keep the melody/rhythm constraints visible in prompt and handoff | more controlled song candidate |
| Reference recording | Run Musia analysis, then write a new-song or localization brief | stems, chords, beats, lyric reference, new song candidate |
| Strict same-song localization | Analyze source, adapt lyrics phrase by phrase, use singing synthesis or pro vocal workflow | same arrangement, new-language vocal |

## Master-Language Alignment

For trilingual original songs, do not start with three unrelated full-song generations if the goal is aligned melody.

Use this route instead:

```text
master language lyric
-> one master full-song render
-> vocal separation and ASR timing
-> beat/chord/melody/F0 extraction
-> phrase map
-> English/Japanese/Chinese lyric adaptation against that phrase map
-> melody-conditioned vocal synthesis for each target language
-> mix each target vocal back into the same arrangement
```

When the user asks for English, Japanese, and Chinese versions with the same melody, choose one master language first. Japanese is a good master when the desired sound is J-pop/anime/fantasy; English can be better for western pop; Mandarin can be better when tonal phrasing is the creative priority.

Important distinction:

- ACE-Step/YuE-style full-song models create the full arrangement and vocal together. They usually do not provide a clean independent melody or MIDI track as the primary output.
- Musia derives the melody guide after generation/source upload by separating the vocal and extracting F0, approximate note timing, beats, and chords.
- If the user already has jianpu, MIDI, sheet music, or a sung guide recording, that supplied melody is stronger than any extracted melody.
- For strict target-language vocals, use the extracted/supplied melody with SoulX-Singer, YingMusic-Singer-Plus, or a professional vocal workflow. Three independent text-to-music renders can be beautiful, but they are reinterpretations, not guaranteed same-melody localizations.
- Japanese target vocals require a backend with real Japanese singing support. Do not force Japanese through a phone set that only supports English, Mandarin, or Cantonese. The next proper path is to install and validate an OpenVPI-DiffSinger, NNSVS, OpenUtau, or equivalent Japanese-capable singing workflow, then feed it the same extracted MIDI/F0/phrase plan and export a dry vocal for the shared instrumental mix.

## Production Standard

A song is not accepted because a model produced a WAV. A usable song needs:

- clear audible singing, not just instrumental or hum;
- healthy loudness and no severe clipping;
- a saved prompt, lyrics, and model config;
- ASR or manual lyric review;
- beat and chord analysis;
- a cover/poster if it will be published;
- a website manifest that matches the real audio;
- a short human listening pass.

If the song is meant to be beautiful and moving, run at least one correction pass when:

- final words are clipped;
- the vocal is buried;
- the language sounds wrong;
- the generated melody ignores the emotional arc;
- ASR recovers almost none of the target lyric;
- the song feels like disconnected lines instead of one continuous performance.

## Writing Better Lyrics For AI Singing

Use short image-heavy lines. Avoid dense clauses and abstract overload.

Do not turn "short lines" into a rigid rule. The goal is not minimum words.
The goal is a natural phrase density for the melody:

```text
some lines can breathe
some lines can hold one strong image
some lines can be fuller when the melody has room
```

Use **留白** deliberately: rests, held vowels, repeated hooks, and silent space can make the song more emotional. But do not delete useful words just to satisfy a constraint checker. Lyric density should be chosen by listening, rhythm, rhyme/押韵, stress or mora flow, and the emotional arc.

Good generation lyrics:

```text
Red sand over my boots
A blue sun falls through dust
I am a breath beside the canyon
But still I rise, still I trust
```

Risky generation lyrics:

```text
In the existential aftermath of planetary isolation I discover a cosmological courage
```

For Chinese and Japanese:

- keep lines short;
- avoid rare words when pronunciation matters;
- reduce hard-to-sing kanji compounds in Japanese if the model mispronounces them;
- for Mandarin, prefer natural phrases with good vowel endings on long notes;
- allow adaptation instead of literal translation.

## Prompt Shape

Every serious generation should have:

```text
title
language
duration
bpm/key/time signature if known
form: intro / verse / pre-chorus / chorus / bridge / final
emotional arc
arrangement
vocal identity without imitating a real singer
negative instructions: no real singer clone, no clipped endings, no buried vocal
lyrics
```

Example vocal prompt:

```text
Clear upfront expressive female vocal, natural Mandarin diction, connected full-song phrasing,
no famous singer imitation, no clipped final syllables, vocal slightly above the mix.
```

## Generation Workflow

1. Create the project.

```bash
musia song init \
  --title "Song Title" \
  --idea "creative direction" \
  --vocal-language zh-Hans \
  --genre "cinematic pop ballad" \
  --style "piano, warm strings, wide drums, subtle synth" \
  --mood "vast, lonely, hopeful" \
  --voice-notes "clear upfront vocal, no real singer imitation" \
  --duration 82 \
  --bpm 82 \
  --keyscale "E minor" \
  --lyrics-file lyrics.txt
```

2. Generate.

```bash
data/creative_projects/<song-id>/commands.sh generate
```

3. Review.

```bash
data/creative_projects/<song-id>/commands.sh review
```

4. Correct if needed.

```bash
musia song correct \
  --project-dir data/creative_projects/<song-id> \
  --issues "vocal unclear; ending syllables clipped; lyric too dense" \
  --caption-extra "clearer vocal, fewer words per line, smoother full-song phrasing" \
  --lyrics-file corrected-lyrics.txt
```

5. Select only the render that passes the quality gate.

## Analysis Workflow

Run every selected render through Musia analysis before website publication:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py AUDIO \
  --run-name <song-id>-<lang>-analysis \
  --max-duration 120 \
  --asr-model small \
  --language LANG \
  --demucs-device cuda
```

Expected outputs:

```text
data/runs/<run-name>/stems/vocals.wav
data/runs/<run-name>/stems/drums.wav
data/runs/<run-name>/stems/bass.wav
data/runs/<run-name>/stems/other.wav
data/runs/<run-name>/stems/instrumental.wav
data/runs/<run-name>/analysis/lyrics.json
data/runs/<run-name>/analysis/beats.csv
data/runs/<run-name>/analysis/chords.csv
```

Use ASR as evidence, not as unquestioned truth. Correct obvious recognition errors with:

- the intended lyric;
- repeated listening;
- line duration and phrase boundary;
- language knowledge.

## Website Data Rule

Use shared `textTracks[]` only when the playable vocals truly share the same line structure.

Use `lyricSets[]` when vocals are independent renders, imperfect localizations, or have different line counts/timings.

Per-vocal layout:

```text
lyrics/en-vocal/en.json
lyrics/en-vocal/zh-Hans.json
lyrics/en-vocal/ja.json
lyrics/zh-vocal/en.json
lyrics/zh-vocal/zh-Hans.json
lyrics/zh-vocal/ja.json
lyrics/ja-vocal/en.json
lyrics/ja-vocal/zh-Hans.json
lyrics/ja-vocal/ja.json
```

Each playable asset must point to its lyric set:

```json
{
  "languageCode": "zh-Hans",
  "lyricSetId": "zh-vocal"
}
```

Rules:

- The active vocal language owns timing.
- The active vocal language owns exact current-word highlighting.
- Other selected translation tracks may rough-highlight corresponding tokens inside the same current `line.id`.
- Other languages in that set are translations of the active vocal's actual sung lines.
- If a vocal does not sing a planned line, do not show that planned line in that vocal set.
- If a vocal repeats a line, show the repeated line if it is audible.
- If ASR is garbled but the audio clearly matches the intended line, correct the text and keep the ASR-derived timing.
- For mixed-language vocals, use one active sung/phonetic track such as `lyrics/mixed-vocal/mul.json`, then add `en`, `zh-Hans`, and `ja` translation tracks in the same lyric set.
- If a local model fails to sing native CJK script reliably in a mixed render, use pinyin/romaji for the sung input and display native Chinese/Japanese in translation tracks with pinyin/furigana. Document the compromise instead of claiming native-script singing.

## Website Publishing Workflow

For the detailed publication checklist, including two-source lyric correction,
multilingual JSON, timing/highlight rules, pinyin/furigana/Jyutping, covers, and
different vocal renders, use:

```text
references/fun-website-item-preparation.md
```

Prepare:

```text
website/assets/audio/<media-id>-en.mp3
website/assets/audio/<media-id>-zh.mp3
website/assets/audio/<media-id>-ja.mp3
website/assets/covers/<media-id>-16x9.png
website/data/songs/<media-id>/manifest.json
website/data/songs/<media-id>/lyrics/...
```

Cover rule:

- default aspect ratio is 16:9;
- no readable text unless intentionally designed;
- image should communicate the song mood;
- save the source prompt in the production note or manifest provenance.

Validate:

```bash
npm run website:validate
musia fun-audit --media-id <media-id>
node --check website/app.js
npm run check
npm run smoke
git diff --check
```

Preview:

```bash
python3 -m http.server 9174 --directory website
```

Browser smoke:

- load the media hash;
- switch every vocal language;
- confirm each vocal shows its own trilingual lines;
- confirm pinyin/furigana do not duplicate;
- confirm the KTV lyric panel shows only the current two-line pair;
- confirm word highlighting alternates between the first and second lyric line;
- confirm translation tracks rough-highlight the same current line without cross-line jumps;
- confirm the chord row follows the active render and the current chord is visibly highlighted in the center;
- confirm the short/hidden demos are not visible unless intentionally in the catalog.

Recording smoke:

```bash
musia fun-record --media-id <media-id> --skip-intro
```

This captures the Fun player in `capture=1` mode and replaces browser audio with the source media file directly. Use `--skip-intro` for a trimmed video that begins at the first timed vocal line.

For sharp mobile/social exports, keep the layout at the target CSS viewport and raise the device pixel scale:

```bash
musia fun-record \
  --media-id one-sky-three-lights-mixed \
  --portrait \
  --width 1080 \
  --height 1920 \
  --device-scale-factor 2 \
  --crf 12 \
  --audio-bitrate 320k
```

This renders the same portrait layout at `2160x3840` device pixels. It is better than enlarging the viewport, because enlarging the viewport changes the layout instead of improving text sharpness.

Publish:

```bash
git add website references README.md
git commit -m "Add or fix media item"
git push origin main
gh run watch <deploy-run-id> --exit-status
```

Live checks:

```bash
curl -fsSL https://fun.lazying.art/data/catalog.json
curl -fsSL https://fun.lazying.art/data/songs/<media-id>/manifest.json
curl -fsSI -L https://fun.lazying.art/assets/audio/<file>.mp3
```

## Documentation Required Per Song

For every serious song, write a note under `references/` with:

- user creative direction;
- research anchors if any;
- lyrics;
- generation model and selected files;
- analysis run folders;
- ASR/lyric correction decisions;
- website asset paths;
- quality caveats;
- validation commands;
- live URL after deployment.

Examples:

```text
references/mars-red-sky-song-production-2026-06-28.md
references/fun-player-full-song-demo-2026-06-28.md
```

## Decision Language

Use honest labels:

- `production candidate`: sounds good, still may need manual release review;
- `public demo`: acceptable for website demo, with documented imperfections;
- `experimental`: useful artifact, not a final song;
- `blocked`: missing model weights, permissions, or quality backend.

Do not call an output perfect unless it has passed listening, ASR/timing, lyric, mix, and website checks.
