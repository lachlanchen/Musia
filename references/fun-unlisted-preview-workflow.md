# Fun Unlisted Preview Workflow

## Naming

- Chinese product term: `试听`
- English UI term: `Preview`
- Full release-stage label: `Unlisted Preview`

`Unlisted Preview` means the item is publicly reachable by direct URL but is
excluded from the normal library, search peek, and autoplay queue. It is not a
privacy control.

## Use Case

Use this stage when Musia has one or more healthy song candidates that need
human listening before a final master is selected. Treat the preview as a
normal-quality publication package:

```text
normalized candidate audio
ASR/listening-corrected active lyrics
candidate-specific word timing
candidate-specific chords and beats
multilingual companion translations
pinyin/furigana/Jyutping
16:9 song-specific cover
manifest and catalog entry
strict audit and browser test
```

Do not use this stage for low-quality, failed, or superseded work. Those remain
`hidden` and carry a truthful method or Legacy suffix.

## Catalog Contract

```json
{
  "id": "<media-id>",
  "visibility": "unlisted",
  "releaseStage": "preview",
  "category": "preview",
  "previewLabel": "Listening Preview",
  "previewReason": "Awaiting human master selection."
}
```

The manifest mirrors the release state:

```json
{
  "publication": {
    "visibility": "unlisted",
    "stage": "preview",
    "label": "Unlisted Preview",
    "listed": false
  }
}
```

## Multiple Candidates

Put candidates for the same decision into one media item when that makes A/B
listening clearer. Each candidate still needs an independent:

- audio asset and selector label;
- lyric set corrected from that exact render;
- word and line timing map;
- chord and beat analysis;
- correction note and provenance record.

Never copy timing or lyrics from one candidate to another merely because they
share a prompt or duration.

## URLs

```text
Preview library:
https://fun.lazying.art/?preview=1

Direct item:
https://fun.lazying.art/?preview=1#<media-id>
```

The direct hash also remains loadable without the query parameter, but
`?preview=1` makes the release stage explicit and exposes the Preview library
button.

## Release Gate

```bash
node bin/musia.js fun-audit --media-id <media-id> --strict
node bin/musia.js fun-validate
node --check website/app.js
git diff --check
```

Publish `MusiaSongs` first, confirm every public audio URL returns HTTP 200,
then publish Musia and verify the live catalog, manifest, cover, and direct
preview page. Confirm the default homepage does not list the preview.

After the listener selects a master, promote only that candidate to the normal
listed catalog or build a final item from it. Run the lyric and timing audit
again before promotion.
