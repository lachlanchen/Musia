# Fun Lazying Art Media Protocol

`fun.lazying.art` is the public website for high-quality media we create: songs, localized songs, MVs, musical short films, and future mixed-media works.

The website uses a static, versioned protocol named:

```text
fun.lazying.media.v1
```

It is designed so Musai, LALACHAN, AgInTiFlow, image-generation tools, and future video tools can all publish media into the same layout without rewriting the player.

Operational website, deployment, cover/poster, and publishing details are documented in:

```text
references/fun-lazying-art-website.md
```

LALACHAN and YouTube publishing details are documented in:

```text
references/lalachan-fun-media-publishing.md
```

## Layout

```text
website/
  CNAME
  index.html
  app.js
  styles.css
  assets/
    audio/
    covers/
    video/
  data/
    catalog.json
    schema/
      fun-media-catalog-v1.schema.json
      fun-media-manifest-v1.schema.json
      fun-media-text-track-v1.schema.json
    songs/<media-id>/
      manifest.json
      lyrics/en.json
      lyrics/zh-Hans.json
      lyrics/ja.json
```

Use the same shape for short films and MVs:

```text
website/data/films/<media-id>/manifest.json
website/data/mvs/<media-id>/manifest.json
```

## Catalog

`website/data/catalog.json` lists everything the site can show.

Important fields:

- `schema`: `fun.lazying.media.catalog.v1`
- `defaultMedia`: media id loaded first
- `items[].kind`: `song`, `localized-song`, `mv`, `short-film`, `video`, or `youtube-video`
- `items[].manifest`: path to the media manifest
- `items[].cover`: library thumbnail, preferably a 16:9 poster unless a square-only thumbnail is required

## Manifest

Each media item has one `manifest.json`.

Important fields:

- `schema`: `fun.lazying.media.manifest.v1`
- `kind`: `song`, `localized-song`, `mv`, `short-film`, `video`, or `youtube-video`
- `assets.cover`: default artwork for audio/song cards and social previews; prefer a 16:9 image
- `assets.poster`: default 16:9 poster/loading image for the player, video, MV, and short film
- `assets.primaryAudio`: final audio mix
- `assets.primaryVideo`: final video file
- `assets.youtube`: YouTube embed descriptor for already-published videos
- `assets.externalVideos`: external video embeds, including YouTube
- `assets.alternateAudio`: vocal-only, instrumental, commentary, language versions
- `assets.stems`: `bass`, `drums`, `vocals`, `other`, `instrumental`
- `musical.chords`: optional timed chord timeline
- `textTracks[]`: one JSON file per language
- `lyricSets[]`: optional per-vocal text-track groups for independent generated renders
- `timeline.lines[]`: canonical line ids shared by every language; timings are the default/canonical timing
- `share`: public title, description, URL, and image
- `provenance`: model/tool prompts and generation source

## Text Tracks

Each language gets its own JSON file. Use this simple form when all playable audio assets share the same lyric structure and only need language-specific text:

```text
lyrics/en.json
lyrics/zh-Hans.json
lyrics/ja.json
```

Important fields:

- `schema`: `fun.lazying.media.text-track.v1`
- `mediaId`: manifest id
- `language.code`: `en`, `zh-Hans`, `ja`, etc.
- `lines[].id`: must match `manifest.timeline.lines[].id` for shared `textTracks[]`; must match the other tracks inside the same `lyricSets[]` group for per-vocal sets
- `lines[].start/end`: timing for this lyric line
- `lines[].text`: lyric, subtitle, or translation
- `lines[].tokens[].pinyin`: Chinese pronunciation
- `lines[].tokens[].reading`: Japanese furigana
- `lines[].tokens[].start/end`: optional word or token timing

## Per-Vocal Lyric Sets

Use `lyricSets[]` when different playable vocals are independent generated renders or imperfect localizations. In that case, each vocal has its own trilingual group:

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

Each playable asset should point to the matching group:

```json
{
  "languageCode": "zh-Hans",
  "lyricSetId": "zh-vocal"
}
```

Rules:

- If a vocal render does not actually sing a planned line, do not force that planned line into that vocal set.
- Use ASR/STT timing as evidence, then correct obvious recognition errors with the input lyric as reference.
- The active vocal language drives current-word highlighting.
- The other languages in the same set are translations of that active vocal's real sung lines, not translations from another render's timeline.
- If EN/ZH/JA really do sing the same line structure, a shared `textTracks[]` layout is acceptable.

The Fun player uses the currently playing asset language or `lyricSetId` to choose timing. Example:

- if the Chinese audio is selected, `lyrics/zh-Hans.json` drives current-line sync;
- if the Japanese audio is selected, `lyrics/ja.json` drives current-line sync;
- if a track has no language-specific timing, the player falls back to `manifest.timeline.lines[]`.

This allows one media item to present strict same-timeline localized songs or separate full-song generation renders with their own phrase timings.

## Cover / Poster Rule

Pure audio must have visual artwork. The default artwork aspect ratio is **16:9** so songs, MVs, short films, and YouTube embeds can share the same player frame. Square album-art assets may still be kept as secondary thumbnails, but the player hero and `share.image` should prefer a 16:9 poster.

Recommended cover pipeline:

1. Generate a clean 16:9 poster image with AgInTi/imagegen from the media brief.
2. Save it under `website/assets/covers/<media-id>-poster-16x9.png`.
3. Store the exact image prompt in `manifest.provenance.coverPrompt`.
4. Reference the PNG from `assets.cover.src`, `assets.poster.src`, and `share.image`.
5. Keep editable/source art, if any, as an artifact link.

## Validation

Run before commit or publish:

```bash
npm run website:validate
```

The validator checks:

- catalog schema and default item
- every manifest path
- local media/cover/artifact paths
- every text track path
- shared line ids across languages
- shared line ids inside every `lyricSets[]` group
- sorted, valid timing ranges
