# Fun Website Item Preparation

Use this runbook before adding or fixing a `fun.lazying.art` media item. The goal is truthful, beautiful playback: the website must reflect what the audio actually sings, while using the prompt/input lyrics as correction evidence.

## 0. Lyric Correction Evidence

Do not publish planned lyrics blindly. Build each vocal lyric set from at least two evidence sources:

- source A: ASR/STT output from the selected vocal or full mix, preferably after stem separation;
- source B: input/reference lyrics, second ASR model, manual listening, or model prompt;
- optional source C: phrase timing from `analysis/lyrics.json`, separated `vocals.wav`, or a previous accepted lyric map.

Correction rule:

```text
audio truth > ASR text > input/reference lyric > translation draft
```

If ASR is phonetically close but misspelled, correct it using the input lyric. If the audio repeats, drops, or changes a line, publish the repeated/dropped/changed line for that vocal. If the vocal is too unclear, mark the item experimental or regenerate; do not invent precise lyrics.

Recommended evidence package per vocal:

```text
data/runs/<song>-<vocal>-analysis/analysis/lyrics.json
data/runs/<song>-<vocal>-analysis/analysis/lyrics.txt
data/runs/<song>-<vocal>-analysis/stems/vocals.wav
references/<song>-production-YYYY-MM-DD.md
```

## 1. Multilingual Lyric JSON

Use shared `textTracks[]` only when every playable vocal truly follows the same line IDs, wording, and timing. Otherwise use `lyricSets[]`.

For independent English, Mandarin, and Japanese vocals:

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

For a mixed-language vocal:

```text
lyrics/mixed-vocal/mul.json
lyrics/mixed-vocal/en.json
lyrics/mixed-vocal/zh-Hans.json
lyrics/mixed-vocal/ja.json
```

For Cantonese, use `yue-Hant` when the text is Traditional Chinese:

```text
lyrics/yue-vocal/yue-Hant.json
lyrics/yue-vocal/en.json
lyrics/yue-vocal/zh-Hans.json
```

Each playable asset must point to the correct set:

```json
{
  "languageCode": "zh-Hans",
  "lyricSetId": "zh-vocal"
}
```

Inside one `lyricSets[]` group, every language track should share the same `line.id` sequence. The active vocal-language track owns the timing. The other tracks are translations of that active vocal's real sung lines.

## 2. Timing And Highlight

Line timing should come from the selected vocal, not from another render. Use ASR phrase boundaries first, then refine by listening.

Minimum timing quality:

- `lines[].start` and `lines[].end` are sorted and match audible phrase boundaries;
- the first line starts when the vocal starts, not during the instrumental intro;
- repeated audible lines get separate line IDs or repeated line entries;
- the active vocal track has token timing when available;
- when token timing is unavailable, tokens still exist so the player can distribute rough highlights inside the line;
- translation tracks use the same `line.id` as the active track so rough translation highlighting stays on the current line.

The player logic is line-first:

```text
active playable asset -> lyricSetId -> active timing track -> current line.id
```

Only the active vocal language needs exact word highlighting. Translation tracks may rough-highlight corresponding tokens in the same line. Do not let English/Japanese/Chinese highlight unrelated future lines while another vocal is playing.

## 3. Ruby, Furigana, Pinyin

Every public CJK lyric track needs pronunciation metadata.

Mandarin:

```json
{"text": "光", "pinyin": "guang1"}
```

Japanese:

```json
{"text": "光", "reading": "ひかり"}
```

Cantonese:

```json
{"text": "光", "reading": "gwong1"}
```

Rules:

- Chinese `zh-Hans` or `zh-Hant` CJK tokens should have `pinyin`.
- Japanese kanji tokens should have `reading`; kana particles do not need readings.
- Cantonese `yue-Hant` CJK tokens should have Jyutping in `reading`.
- Do not duplicate ruby/furigana by putting pronunciation both in visible text and in `rt`, unless the sung source is intentionally phonetic such as pinyin/romaji.
- For mixed local-model renders, it is acceptable to store phonetic sung text in `mul.json` and native-script translations in `zh-Hans.json` / `ja.json`; document that choice.

## 4. Cover

Every audio-only item needs a clean visual identity.

Cover requirements:

- default aspect ratio: 16:9;
- save under `website/assets/covers/<media-id>-16x9.png`;
- set `assets.cover`, `assets.poster`, and `share.image`;
- include `width` and `height` metadata in the manifest;
- store the image-generation prompt/source under `manifest.provenance.coverPrompt` or the production note;
- avoid text baked into the image unless the design specifically needs it.

The cover should match the emotional world of the song, not just be decorative.

## 5. Different Vocals

Treat each vocal render as independent unless the audio proves otherwise.

Examples:

- English vocal selected: `en-vocal/en.json` owns timing and exact highlights; `en-vocal/zh-Hans.json` and `en-vocal/ja.json` are translations of the English vocal.
- Mandarin vocal selected: `zh-vocal/zh-Hans.json` owns timing; English/Japanese tracks translate the Mandarin vocal, even if the English render sang different lines.
- Mixed vocal selected: `mixed-vocal/mul.json` owns timing; native-script language tracks translate the mixed phonetic line.

Do not copy one vocal's line map into another vocal just because both were generated from the same prompt. Cross-check by ASR/listening first.

## Required Commands

Run schema validation:

```bash
npm run website:validate
```

Run the publication audit:

```bash
musia fun-audit --media-id <media-id>
```

Use strict mode before a public push when possible:

```bash
musia fun-audit --media-id <media-id> --strict
```

Preview locally:

```bash
python3 -m http.server 9174 --directory website
```

Record a clean player video:

```bash
musia fun-record --media-id <media-id> --skip-intro
```

## Final Quality Gate

Before commit:

- listen to each selected vocal;
- verify the active track starts at the real vocal entrance;
- switch every vocal language in the website;
- confirm the visible title, artist, cover, chord row, and two-line lyric carousel are tidy;
- confirm pinyin/furigana display once, not duplicated;
- run `npm run website:validate`;
- run `musia fun-audit --media-id <media-id>`;
- document ASR correction decisions and caveats in `references/`.

If any vocal has low quality, buried singing, broken pronunciation, or unreliable lyric recovery, keep it out of the default public item or label it experimental.
