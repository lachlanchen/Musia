# 半曲长安: website publication

The user explicitly requested website upload after the private MiniMax audition.
Publish the selected seed 91302 as a normal listed song, not an unlisted preview.
Do not regenerate the audio or publish to social/music platforms in this task.

- Player: https://fun.lazying.art/#ban-qu-chang-an
- Atlas: https://fun.lazying.art/atlas/ban-qu-chang-an/
- Audio: https://lazyingart.github.io/MusiaSongs/audio/ban-qu-chang-an-zh-minimax-music3-seed91302-20260914.mp3
- Manifest: `website/data/songs/ban-qu-chang-an/manifest.json`
- Lyrics: `website/data/songs/ban-qu-chang-an/lyrics/zh-minimax-91302/`
- Cover: `website/assets/covers/ban-qu-chang-an-16x9.png`

The audio is unchanged: 158.476 s Mandarin female singing, MiniMax-Music3 seed
91302, native-Chinese model input. Only the MP3 goes into the dedicated MusiaSongs
repo. No weights, WAV, credentials, private source images or unrelated changes
are included. Preserve the site's existing default selection and other songs.

## Lyrics and evidence

All 28 Chinese lines use the source-informed large-v3/no-VAD/MOSS review from
the generation task. English and Japanese are translations of this Chinese
vocal, not separate singing versions. Their line IDs and time windows match.
Word timing remains ASR-derived, with approximate translation highlighting.
The retained 城南/城门 uncertainty and lack of a musician-verified score remain
in provenance; a website upload does not silently certify recording accuracy.

The publication pass corrected Japanese dictionary mistakes with explicit
contextual overrides: 琴=こと, 月明かり=つきあかり, 空=そら, 日=ひ, 人=ひと.
The overrides are stored in the reviewed mapping and supported by the reusable
exporter, so rebuilding will not restore the incorrect readings.

The new optional `manifest.generationCredit` is displayed under the artist.
For this song it reads `AI-generated music · MiniMax-Music3`. It uses textContent,
not HTML. It is hidden for other songs without that field. Listener-facing
title, caption and description remain about the song, not debugging history.

## Rebuild

Use `PYTHONNOUSERSITE=1` with direct conda commands to avoid shadowing the
environment's pykakasi with an obsolete user-site package. The normal Musia CLI
already applies its runtime policy.

```bash
# Export the reviewed mapping to a new, non-overwriting lyrics-publication folder
# using export_reviewed_lyrics.py and the inputs in the production note first.
PYTHONNOUSERSITE=1 conda run -n musia python scripts/prepare_ban_qu_chang_an_fun_item.py
node bin/musia.js atlas-build --media-id ban-qu-chang-an
node bin/musia.js fun-audit --media-id ban-qu-chang-an --strict
node bin/musia.js fun-validate
node --check website/app.js

# Uses hosted audio to exercise real range requests and seeking.
PYTHONNOUSERSITE=1 conda run -n musia python scripts/test_ban_qu_chang_an_website.py
PYTHONNOUSERSITE=1 conda run -n musia python scripts/test_ban_qu_chang_an_website.py --live
```

Browser evidence is stored in the ignored creative project's `review/website/`.
Checks cover desktop/mobile load, real audio playback, seeking to both choruses
and the ending, active lyric/word/chord rendering, ruby, credit visibility and
horizontal overflow. These are clock/rendering checks, not independent proof of
ASR or harmonic accuracy. The temporary server and browser close on exit.

## Deployment order

Push MusiaSongs first and verify the public MP3, then push Musia's scoped website
changes and wait for GitHub Pages. The initial media push used the wrong stored
account and returned 403. A command-scoped saved `lazyingart` credential succeeded;
no secret was printed, committed or written to a URL, and the workstation's
globally active GitHub account was not switched.

Do not change `hidden`/`Legacy` rules or rerun the global naming script for this
new standalone song. The same selected audio is the only public vocal.

## Verified result

- MusiaSongs commit `4cc4fcb`: Pages built; the exact public MP3 returns HTTP 200
  with byte-range support and CORS enabled.
- Musia commit `91a4299`: website deployment run `34787450113` succeeded.
- Strict item audit, full catalog validation and JavaScript syntax passed.
- Live desktop (1440 x 1000) and mobile (390 x 844) browser checks passed:
  playback advances, the opening/choruses/outro seek correctly, current line and
  word highlights update, chord indices change, and ruby/credit render.
- No page JavaScript errors or page-level horizontal overflow were detected.
- Screenshots and JSON evidence: creative project `review/website/live-*`.
- Selected/Nutstore lyric JSONs now match the website publication; the handoff
  and local package link to the public song. Audio bytes were not changed.

The final HTML also versions the changed CSS/JS URLs so a returning browser does
not retain the older bundle that cannot display the optional generation credit.
