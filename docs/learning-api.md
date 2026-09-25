# Public Musia Learning API

This service reads the published Fun website catalog. It does not import the
private studio, run models, fetch URLs, accept uploads, create accounts, record
audio, or write source data. There are no mutation endpoints. Generation and AI
coaching are unavailable, not simulated.

## Run and Test

Use the existing `musia` conda environment. The isolated dependency list matches
the versions verified in that environment; do not install the generation stack.

```bash
PYTHONNOUSERSITE=1 conda run -n musia python -m pip install -r requirements-learning.txt
MUSIA_PUBLIC_BASE_URL=http://127.0.0.1:18440 PYTHONNOUSERSITE=1 conda run -n musia python scripts/serve_musia_learning.py
PYTHONNOUSERSITE=1 conda run -n musia python -m unittest discover -s tests -p test_learning_api.py -v
```

The default listener is `127.0.0.1:18440`; `--host` and `--port` override it.
Production should put this loopback listener behind a TLS reverse proxy.
`MUSIA_PUBLIC_BASE_URL` defaults to `https://musia.lazying.art`. Set it explicitly
for development so native and web clients fetch the local exercise. It must be
an HTTPS origin or loopback HTTP origin, without credentials, path, query, or
fragment. It controls generated exercise audio and cover URLs only. Existing
song URLs remain on their approved public hosts.

The runner disables proxy-header trust, the server banner, and access logging.
Host, Forwarded, and X-Forwarded-* headers never determine public URLs. The
service does not implement redirects, including trailing-slash redirects.
There is no wildcard CORS policy: serve the web client from the same origin;
native clients can call the API directly. Configure proxy logs, TLS, request
size/rate limits, and retention separately before public deployment. Do not
proxy the private studio or expose the repository as a static directory.

## Contract

All times are seconds on the selected asset's audio clock. End times are
exclusive. IDs are ASCII letters, digits, `_`, and `-`, with an alphanumeric
first character and at most 128 characters. Invalid, absent, hidden, and
unpublished song IDs return 404. The schema is identical for web and native.

`GET /healthz` returns `{"status":"ok"}`. This is a process liveness check,
not a claim that remote audio hosts or the catalog are healthy.

`GET /api/v1/library` returns:

```json
{"version":1,"items":[{"id":"first-pulse","title":"First Pulse","artist":"Musia","coverUrl":"https://musia.lazying.art/assets/brand.png","duration":22,"kind":"exercise"}]}
```

Published music entries follow the same shape with `kind: "song"`. The exercise
is first. Song duration is the default asset's duration.

`GET /api/v1/songs/{id}` returns exactly these fields:

```text
{version: 1, id, title, artist, coverUrl, assets: [
  {id, label, language, audioUrl, duration, bpm, timeSignature,
   confidence: {beats, chords, melody},
   beats: [{time, index?}],
   chords: [{start, end, name, confidence?}],
   lyrics: [{id, start, end, text, tokens: [{text, start, end, reading?}]}],
   phrases: [{id, start, end, text}],
   melody: [{start, end, note, numberNote, text}]}
], defaultAssetId}
```

- `bpm` is a number or `null`; `timeSignature` is a string such as `"4/4"` or
  `null`. Missing data is never filled with an invented tempo or beat grid.
- `confidence` values are `verified`, `analysis`, `estimated`, or `unavailable`.
  Only the synthesized exercise receives `verified`. Individual chord scores,
  when present, are numeric in `[0, 1]`, not proof of correctness.
- Published song beats have **only `time`**, even if the source has an index.
  There is no inferred downbeat, bar number, or `index % 4` song counting.
  Published meter is source metadata, not independently verified meter.
- Melody is always `analysis` when present: token-median vocal F0 is noisy and
  is not a verified transcription or a single exact note for a whole syllable.
  `numberNote` is existing source notation, not newly inferred music theory.
- Each audio asset gets its own study entry and active-language lyric track.
  Study source URL and language must match the audio asset. An explicit missing
  lyric-set reference never falls back to another vocal or a translation.
  Mandarin `pinyin` and existing pronunciation `reading` normalize to `reading`.
- Song phrases are the selected vocal's corrected lyric lines without tokens.
  Instrumental lyric rows are omitted. Empty arrays mean unavailable data.
- Duration uses asset metadata, then matching study metadata, then the legacy
  manifest duration. Some legacy per-vocal files lack their own duration, so
  that fallback is nominal, not newly measured. No remote audio is downloaded.
  Invalid events are omitted and event ends are bounded by this duration.
- All clients must render text as text, not HTML. Capo/simplified chord names
  are display aids; this API does not transpose or alter published audio.

## First Pulse

`GET /api/v1/songs/first-pulse` uses the same song-detail schema.
`defaultAssetId` and its single asset ID are both `first-pulse`.
`GET /api/v1/exercises/first-pulse/audio.wav` returns deterministic PCM WAV:
24,000 Hz, mono, signed 16-bit little-endian, exactly 528,000 samples / 22 s.
It supports HEAD and one byte range (206); invalid/multiple ranges return 416.

| Source interval | Content |
| --- | --- |
| 0-4 s | Four count-in clicks at 0, 1, 2, 3 s |
| 4-8 s | Em, phrase `bar-1` |
| 8-12 s | Am, phrase `bar-2` |
| 12-16 s | Em, phrase `bar-3` |
| 16-20 s | Am, phrase `bar-4` |
| 20-22 s | Final Am decay; no additional beats or bar |

The tempo is 60 BPM and meter is 4/4. Twenty beats have `time` and zero-based
ordinal `index` values 0 through 19. Each beat starts at sample
`index * 24000`; chord changes share the same integer sample clock. Indices
0-3 are the count-in, not the first practice bar. Bar starts are 4, 8, 12,
and 16 s. Chord confidence is verified by construction. Lyrics and melody are
empty: this is instrumental practice, not synthesized singing. The four
phrases have text `Em`, `Am`, `Em`, `Am`; instructions live in lessons.
The final tail ends at zero. WAV bytes are synthesized once in memory and
cached (one entry), never persisted. The cache is guarded against concurrent
duplicate synthesis. This is fixed oscillator synthesis, not a model job.

## Lessons and Capabilities

`GET /api/v1/lessons` returns `{lessons: [...]}` with three lessons:
`listen-first`, `tap-the-pulse`, and `em-am-switch`. Each contains exactly
`id`, `title`, `focus`, `body`, `exerciseId`, and `steps` (an array of strings).
All point to `first-pulse`. Clients may measure local tap timing; it stays on the
device and is not a guitar or singing accuracy score. Device latency can affect
it. This backend does not receive taps or record microphone audio.

`GET /api/v1/capabilities` returns:

```json
{
  "version": 1,
  "readOnly": true,
  "library": true,
  "lessons": true,
  "exerciseAudio": true,
  "cloudGeneration": {"available": false, "reason": "Disabled pending authentication, consent, and privacy safeguards."},
  "upload": {"available": false, "reason": "Disabled pending authentication, consent, and privacy safeguards."},
  "aiCoaching": {"available": false, "reason": "Disabled pending authentication, consent, and privacy safeguards."},
  "accounts": {"available": false, "reason": "No accounts or authentication in this release."}
}
```

## Publication Boundary

Only catalog entries with `kind` song/localized-song and the exact canonical
`data/songs/<id>/manifest.json` path are considered. Catalog, manifest, and audio
asset publication checks exclude hidden, unlisted, private, preview, draft,
experimental, demo, and legacy markers, including IDs/titles/tags where older
records lack publication flags. Explicit publication settings must say public,
published, and listed. Legacy records without flags retain the existing normal
catalog's public convention. Preview URLs do not become accessible by knowing
an ID or passing `showall`. Non-catalog files and music videos are not exposed.

Response objects are newly constructed from allowlisted fields; manifests and
study files are never returned whole. Provenance, source paths, local run data,
prompts, and private evidence are not part of this API. Only existing HTTPS
audio URLs under `lazyingart.github.io/MusiaSongs/audio/` or
`fun.lazying.art/audio/`, and covers under `fun.lazying.art/assets/covers/` or
`assets/brand/`, are accepted. Userinfo, query strings, fragments, arbitrary
ports, encoded paths, and directory traversal in asset URLs are rejected.
URLs are not fetched or proxied. The service depends on the curated local
publication metadata; it does not independently certify licensing or remote
availability.

Reads are restricted to canonical website JSON paths and same-song lyric paths.
Symlinks in any child path component are rejected. JSON files and JSON responses
are limited to 4 MiB, catalog items to 256, assets to 16, and event arrays to
8,192. Lyric and melody input lines are limited to 512 with 256 tokens per line.
Malformed/missing catalog data leaves only the exercise; invalid songs are
omitted. Oversized response projection returns generic 503, not a partial song.
Unexpected errors never include exception details or local paths.

Publication files are reread per request, including lyric and study changes;
there is no stale catalog cache. HTTP caches have bounded `max-age` and
`must-revalidate`: 30 s for catalog/detail/capabilities, 300 s for lessons/static
files, 3,600 s for fixed WAV. Liveness and errors are `no-store`. A previously
cached public response can remain visible until that short lifetime expires.
No unbounded request body is consumed; request bodies and non-GET/HEAD methods
are rejected (400 and 405 respectively). Encoded/traversal paths are rejected.
There is no OpenAPI/docs endpoint, arbitrary file/model/code endpoint, directory
listing, catch-all SPA route, or websocket API.

## Exact Web Files

| URL | Repository file |
| --- | --- |
| `/`, `/index.html` | `apps/web/index.html` |
| `/app.js` | `apps/web/app.js` |
| `/core.js` | `apps/web/core.js` |
| `/styles.css` | `apps/web/styles.css` |
| `/privacy`, `/privacy.html` | `apps/web/privacy.html` |
| `/support`, `/support.html` | `apps/web/support.html` |
| `/vendor/lucide.js` | `apps/web/vendor/lucide.js` |
| `/assets/musia.js` | `website/musia.js` |
| `/assets/brand.png` | `website/assets/brand/fun-lazying-art-logo.png` |

No other `/vendor` or `/assets` files are served. Missing files return 404, so
the web owner can deliver these files independently without a backend restart.
Static file reads are limited to 8 MiB. The existing brand PNG is reused without
editing or copying it. The helper script is suitable for
`window.Musia.displayChord` display-only changes.

All responses include nosniff, frame denial, no-referrer, a restrictive CSP,
and a Permissions-Policy disabling microphone, camera, location, and payments.
The web owner must use same-origin external JS/CSS, no inline script, no inline
style blocks, no remote icon CDN, and no iframe/form submission. Media/images
are allowed from the listed public origins. No analytics, cookies, or account
identifiers are added by this service. These headers are not authentication.

Tests use synthetic temporary fixtures plus a read-only repository smoke test.
They verify the contract, per-vocal isolation, hidden/preview exclusion, path
and URL filtering, symlink rejection, mutation rejection, limits, security
headers, range playback, deterministic WAV samples, audible triad frequencies,
and the exact count-in/bar/decay timeline. They do not run a long-lived server.
