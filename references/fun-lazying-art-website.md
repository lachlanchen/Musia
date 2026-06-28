# Fun Lazying Art Website

`fun.lazying.art` is the public static media site for work created by Musai, LALACHAN, AgInTiFlow, and related media-generation tools.

Live URL:

```text
https://fun.lazying.art/
```

Repository path:

```text
website/
```

GitHub Pages is configured for workflow deployments from `main`. The custom domain is `fun.lazying.art`, HTTPS enforcement is enabled, and GitHub reports the Pages certificate as approved.

## Purpose

The website is meant to become a clean public platform for:

- original songs
- localized songs
- music videos
- musical short films
- pure audio with generated cover art
- synced subtitles and lyrics
- Chinese pinyin and Japanese furigana learning views
- chords, stems, vocal-only files, final mixes, and source artifacts

The current implementation is intentionally static. This keeps it easy to host on GitHub Pages, easy to clone, and easy for future CLI/agent tools to publish by writing JSON and assets.

## Current Demo

Current catalog item:

```text
rain-day-bilingual-verse
```

Files:

```text
website/data/catalog.json
website/data/songs/rain-day-bilingual-verse/manifest.json
website/data/songs/rain-day-bilingual-verse/lyrics/en.json
website/data/songs/rain-day-bilingual-verse/lyrics/zh-Hans.json
website/data/songs/rain-day-bilingual-verse/lyrics/ja.json
website/assets/audio/rain-day-bilingual-verse.mp3
website/assets/audio/rain-day-bilingual-verse-vocal.mp3
website/assets/covers/rain-day-bilingual-verse.png
website/assets/covers/rain-day-bilingual-verse.svg
```

Media facts:

- Kind: `song`
- Duration: `16.3` seconds
- Key: `D minor`
- BPM: `78`
- Text tracks: `zh-Hans`, `ja`, `en`
- Playable assets: final mix and vocal-only audio
- Cover/poster: `website/assets/covers/rain-day-bilingual-verse.png`
- Source workflow: `musai soulx-verse`
- Model noted in provenance: `SoulX-Singer`
- Lyric refinement noted in provenance: `DeepSeek`

## Player UI

Main files:

```text
website/index.html
website/styles.css
website/app.js
website/favicon.svg
```

The UI has four main areas:

- top navigation for media categories: all, music, MV, short film
- library panel for catalog items
- player panel with cover art, waveform, transport, asset switcher, and current chord
- synced text panel with chords, active lyric/subtitle lines, pinyin, furigana, and translations
- inspector panel with current line, protocol links, artifact links, and creation command

For pure audio, the player uses `assets.cover` or `assets.poster` as the stage image behind the waveform. For video/MV/short-film media, `assets.primaryVideo` can replace the waveform stage while the same poster remains available for loading states and share previews.

## Data Protocol

The site uses:

```text
fun.lazying.media.v1
```

Protocol overview:

- `catalog.json` lists all media items.
- each media item has one `manifest.json`.
- every language has its own text-track JSON file.
- `timeline.lines[].id` is the canonical sync key shared by every language.
- audio/video/cover/stem files are referenced from the manifest.
- chords, chapters, shots, provenance, artifacts, and share metadata are optional structured extensions.

Schema files:

```text
website/data/schema/fun-media-catalog-v1.schema.json
website/data/schema/fun-media-manifest-v1.schema.json
website/data/schema/fun-media-text-track-v1.schema.json
```

Detailed format reference:

```text
references/musai-website-json-format.md
```

## Required Files For A New Media Item

For a song:

```text
website/assets/audio/<media-id>.mp3
website/assets/covers/<media-id>.png
website/data/songs/<media-id>/manifest.json
website/data/songs/<media-id>/lyrics/en.json
website/data/songs/<media-id>/lyrics/zh-Hans.json
website/data/songs/<media-id>/lyrics/ja.json
```

For an MV:

```text
website/assets/video/<media-id>.mp4
website/assets/covers/<media-id>.png
website/data/mvs/<media-id>/manifest.json
website/data/mvs/<media-id>/subtitles/en.json
website/data/mvs/<media-id>/subtitles/zh-Hans.json
website/data/mvs/<media-id>/subtitles/ja.json
```

For a short film:

```text
website/assets/video/<media-id>.mp4
website/assets/covers/<media-id>.png
website/data/films/<media-id>/manifest.json
website/data/films/<media-id>/subtitles/en.json
website/data/films/<media-id>/subtitles/zh-Hans.json
website/data/films/<media-id>/subtitles/ja.json
```

Then add the item to:

```text
website/data/catalog.json
```

## Cover And Poster Workflow

Every shareable media item should have artwork.

For pure audio:

- generate a square cover
- save as `website/assets/covers/<media-id>.png`
- optionally keep editable art as `website/assets/covers/<media-id>.svg`
- set `assets.cover.src`
- set `assets.poster.src`
- set `share.image`
- record the image prompt in `provenance.coverPrompt`

For MV or short film:

- use `assets.poster` for the video poster/loading image
- use `assets.cover` for square cards and social previews
- keep generated or designed source files as artifacts when useful

Recommended prompt shape:

```text
Square album/poster cover for "<title>" on Fun Lazying Art.
Describe the song/film mood and visual concept.
Premium clean media artwork, cinematic composition, no readable text,
no logo, high-quality cover/poster, suitable for a public media player.
```

## Publishing Workflow

Local validation:

```bash
npm run website:validate
node --check website/app.js
```

Local preview:

```bash
python3 -m http.server 8778 --directory website
```

Open:

```text
http://127.0.0.1:8778/
```

Commit and push:

```bash
git add website references scripts package.json README.md .github/workflows/website-pages.yml
git commit -m "Add media item"
git push origin main
```

GitHub Actions workflow:

```text
.github/workflows/website-pages.yml
```

The workflow:

1. checks out the repo
2. runs `npm run website:validate`
3. uploads `website/` as the Pages artifact
4. deploys to GitHub Pages

Current deploy workflow run verified:

```text
Deploy website: success
URL: https://fun.lazying.art/
```

## Validation Rules

Validator:

```text
scripts/validate_fun_media_site.py
```

Command:

```bash
npm run website:validate
```

It checks:

- `website/data/catalog.json` exists
- catalog schema is `fun.lazying.media.catalog.v1`
- `defaultMedia` exists in catalog items
- every catalog item has `kind` and `manifest`
- local cover paths exist
- every manifest path exists
- manifest schema is `fun.lazying.media.manifest.v1`
- manifest id matches catalog item id
- duration is positive
- local asset and artifact paths exist
- timeline lines exist
- timeline line ids are unique
- timeline timing is sorted and valid
- every text track exists
- text-track schema is `fun.lazying.media.text-track.v1`
- text-track media id matches manifest id
- language codes match the manifest text-track entries
- every text track contains every canonical line id

## Current GitHub Pages Setup

Verified Pages state:

```json
{
  "url": "https://fun.lazying.art/",
  "cname": "fun.lazying.art",
  "https_enforced": true,
  "https_certificate": "approved"
}
```

DNS observed:

```text
fun.lazying.art CNAME lachlanchen.github.io
```

If the domain needs to be reconfigured:

```bash
gh api -X POST repos/lachlanchen/Musai/pages -f build_type=workflow
printf '%s' '{"cname":"fun.lazying.art","https_enforced":true,"build_type":"workflow"}' \
  | gh api -X PUT repos/lachlanchen/Musai/pages --input - --silent
```

Then verify:

```bash
gh api repos/lachlanchen/Musai/pages \
  --jq '{url:.html_url,cname:.cname,https_enforced:.https_enforced,https_certificate:.https_certificate.state}'

curl -I -L https://fun.lazying.art/
curl -fsS https://fun.lazying.art/data/catalog.json | python3 -m json.tool >/dev/null
```

## Design Rules

Keep the site elegant and durable:

- no marketing landing page before the media experience
- media item is the first visible signal
- cover/poster must be visible for pure audio
- keep cards shallow and avoid nested card-heavy layout
- use stable dimensions for player, transport, chords, and lyric lines
- ensure text never overlaps controls
- support mobile and desktop without changing data shape
- do not rely on one large JSON file; each language track stays separate
- keep the protocol static-host friendly
- do not commit large generated media by default

Small demo media may be committed only when it is intentionally part of the public website. Larger generated media should stay ignored or move to external storage/CDN, with manifest URLs pointing to the external asset.

## Future Extensions

Planned fields that fit the current protocol:

- `chapters[]` for short films and long videos
- `shots[]` for generated video scene boundaries
- `assets.stems.bass/drums/vocals/other/instrumental`
- `assets.alternateAudio[]` for language versions or commentary
- `assets.subtitles` for WebVTT/SRT export
- `provenance.models[]` for model/tool traceability
- `rights` for ownership, license, and public/private status
- `quality` for loudness, duration, ASR overlap, and human review status
- `collections` or playlists for albums, MV sets, and short-film series

