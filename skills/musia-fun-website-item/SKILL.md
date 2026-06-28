---
name: musia-fun-website-item
description: Use when preparing, auditing, fixing, documenting, or publishing a Fun Lazying Art website media item for Musia, including ASR/STT-corrected lyrics, multilingual lyric JSON, per-vocal lyric sets, timing and word highlighting, pinyin/furigana/Jyutping ruby, 16:9 covers, manifests, website validation, and player recording.
---

# Musia Fun Website Item

Use this skill after a song, localization, MV, short film, or vocal render has been selected for `fun.lazying.art`. This skill is about truthful website publication, not about accepting raw generation quality.

## Default Repo

```text
/home/lachlan/ProjectsLFS/Musia
```

## Core Rule

The website must match the real audio. Planned lyrics, prompts, and translations are references; ASR/STT, listening, and phrase timing are evidence. If a vocal repeats, skips, garbles, or changes a line, the published lyric set must reflect that vocal or the vocal should stay experimental.

## Workflow

1. Run or collect analysis for every public vocal:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py AUDIO \
  --run-name <media-id>-<vocal>-analysis \
  --max-duration 180 \
  --asr-model small \
  --language LANG
```

2. Correct lyrics using at least two sources:

- ASR/STT from the selected vocal or stem;
- input/reference lyric, second ASR, or manual listening;
- phrase timing, separated vocal, and repeated listening when they disagree.

Use this priority:

```text
audio truth > ASR text > input/reference lyric > translation draft
```

3. Choose the JSON shape:

- shared `textTracks[]` only when all playable vocals truly share line IDs and timing;
- per-vocal `lyricSets[]` when vocals are independent, imperfect, translated, mixed-language, or have different timing.

4. Build lyric tracks:

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
lyrics/mixed-vocal/mul.json
lyrics/yue-vocal/yue-Hant.json
```

Inside one lyric set, every track shares the same `line.id` sequence. The active vocal-language track owns line timing and exact word highlighting. Other tracks translate that active vocal's actual sung lines and may rough-highlight tokens inside the same current line.

5. Add pronunciation metadata:

- Mandarin CJK tokens: `pinyin`, such as `{"text": "光", "pinyin": "guang1"}`;
- Japanese kanji tokens: `reading`, such as `{"text": "光", "reading": "ひかり"}`;
- Cantonese CJK tokens: Jyutping in `reading`, such as `{"text": "光", "reading": "gwong1"}`.

Do not duplicate ruby by also putting pronunciation into the visible native text unless the active sung source is intentionally phonetic.

6. Prepare cover/poster:

- use 16:9 by default;
- save to `website/assets/covers/<media-id>-16x9.png`;
- set `assets.cover`, `assets.poster`, and `share.image`;
- record the cover prompt/source in `manifest.provenance` or the song production note.

7. Validate and audit:

```bash
npm run website:validate
musia fun-audit --media-id <media-id>
node --check website/app.js
git diff --check
```

Use strict audit mode before public release when reasonable:

```bash
musia fun-audit --media-id <media-id> --strict
```

8. Preview and record:

```bash
python3 -m http.server 9174 --directory website
musia fun-record --media-id <media-id> --skip-intro
```

## Quality Gate

Before calling an item public-demo quality:

- listen to every selected vocal;
- confirm each vocal has its own lyric set unless ASR proves shared timing is correct;
- confirm the first highlighted line begins at the real vocal entrance;
- confirm active-vocal word highlighting does not jump into another language's future line;
- confirm translation highlighting stays within the current line ID;
- confirm pinyin/furigana/Jyutping display once and cleanly;
- confirm the chord row has a current highlighted chord when chord data exists;
- confirm title, artist `Musia`, cover, social image, and localized titles are present;
- document ASR correction decisions and caveats under `references/`.

## Detailed Reference

Read only when preparing or reviewing a real website item:

```text
references/fun-website-item-preparation.md
references/musia-website-json-format.md
references/musia-song-generation-and-website-runbook.md
```
