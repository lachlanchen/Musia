# Fun Lazying Art Media Protocol

`fun.lazying.art` is the public website for high-quality media we create: songs, localized songs, MVs, musical short films, and future mixed-media works.

The website uses a static, versioned protocol named:

```text
fun.lazying.media.v1
```

It is designed so Musai, LALACHAN, AgInTiFlow, image-generation tools, and future video tools can all publish media into the same layout without rewriting the player.

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
- `items[].kind`: `song`, `mv`, `short-film`, or `video`
- `items[].manifest`: path to the media manifest
- `items[].cover`: library thumbnail

## Manifest

Each media item has one `manifest.json`.

Important fields:

- `schema`: `fun.lazying.media.manifest.v1`
- `kind`: `song`, `mv`, `short-film`, or `video`
- `assets.cover`: square artwork for audio/song cards and social previews
- `assets.poster`: poster/loading image for video, MV, and short film
- `assets.primaryAudio`: final audio mix
- `assets.primaryVideo`: final video file
- `assets.alternateAudio`: vocal-only, instrumental, commentary, language versions
- `assets.stems`: `bass`, `drums`, `vocals`, `other`, `instrumental`
- `musical.chords`: optional timed chord timeline
- `textTracks[]`: one JSON file per language
- `timeline.lines[]`: canonical timed line ids shared by every language
- `share`: public title, description, URL, and image
- `provenance`: model/tool prompts and generation source

## Text Tracks

Each language gets its own JSON file:

```text
lyrics/en.json
lyrics/zh-Hans.json
lyrics/ja.json
```

Important fields:

- `schema`: `fun.lazying.media.text-track.v1`
- `mediaId`: manifest id
- `language.code`: `en`, `zh-Hans`, `ja`, etc.
- `lines[].id`: must match `manifest.timeline.lines[].id`
- `lines[].text`: lyric, subtitle, or translation
- `lines[].tokens[].pinyin`: Chinese pronunciation
- `lines[].tokens[].reading`: Japanese furigana
- `lines[].tokens[].start/end`: optional word or token timing

## Cover / Poster Rule

Pure audio must have `assets.cover`. MV and short film items should have both `assets.poster` and, when useful, `assets.cover`.

Recommended cover pipeline:

1. Generate a clean cover image with AgInTi/imagegen from the media brief.
2. Save it under `website/assets/covers/<media-id>.png`.
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
- sorted, valid timing ranges
