# Catalog Presentation

The October 5, 2026 owner request supersedes model-based public suffixes.
Use **Chinese title · English title** in the main library, player, native apps,
share title and Atlas. Japanese originals may use **Japanese title · English title**;
set `titleLanguage: "ja"` on their work group (default: `zh-Hans`). This is a
per-work title choice, not a switch on each vocal language. Aya Chan, Rain of
Light and Dawnlight and Blossoms use their Japanese titles.
Do not display ACE, MiniMax, DR, SoulX, V2, generation
seeds, or workflow labels as part of a song's public title.

## Selection and Archives

`catalog-curation.json` is the reviewed title and work-family map. Each work has
at most one selected song. Other recordings use **Chinese title · English title
· Archive 01**, with stable archive numbers within that work. They remain hidden,
not deleted. The Archive number is an identifier, not a quality score.

- Keep the ACE Changfeng recording of 半曲长安; archive MiniMax.
- Keep the selected original-poem 侠客行, 将进酒 and 梦游天姥吟留别 recordings.
- Keep the standard 云海之恋, selected 照顾好自己 and old selected 共白头.
- Preserve distinct compositions such as 晴天路, even when inspired by the same poem.
- Different vocal languages remain available within one selected song.
- Within a song, a competing take in the same language is archived. 洛神赋 keeps
  its already selected pronunciation-refined master. Its original take remains
  accessible with `?showall`.
- MVs are companion media, not duplicate song recordings. They retain a clean
  `MV` label. Preview candidates remain unlisted; renaming does not promote them.

The normal library/search/playback queue hides archives. Existing `?hidden`,
`?hided` and `?showall` links and the library's Legacy control remain supported.

## Apply and Verify

```sh
PYTHONNOUSERSITE=1 conda run -n musia python scripts/curate_fun_catalog.py --apply
PYTHONNOUSERSITE=1 conda run -n musia python scripts/curate_fun_catalog.py
PYTHONNOUSERSITE=1 conda run -n musia python -m unittest discover -s tests -p test_catalog_curation.py
node bin/musia.js fun-validate
PYTHONNOUSERSITE=1 conda run -n musia python scripts/test_catalog_presentation.py
```

The no-argument command is a non-mutating drift check. Update the map when adding
a song; never guess a new winner by stripping text from titles. Historical model
and generation details remain in provenance/IDs and source notes, not names.

The script changes presentation metadata only. Audio URLs, IDs, lyric files,
translations/ruby, timeline events, chord/beat/melody arrays and durations must
remain unchanged. `displayTitle` fixes the bilingual player title across vocal
language switches; `localizedTitles` still stores the clean native titles.
Study data is not regenerated for a naming-only change: only its title and asset
labels are updated, preserving analyzed music and alignment exactly.

## Deployment and Installed Apps

Publish Fun's catalog/manifests/player via the existing GitHub Pages workflow.
Separately rebuild and deploy the sanitized learning catalog using
`scripts/deploy_musia_learning.py`. Native Android and Apple clients read the
existing `/api/v1/library` and `/api/v1/songs/<id>` contract on
`https://musia.lazying.art`; no app binary or store review is needed.

Reopen or refresh the library to see new titles. Already-open players and
device-local historical practice records can retain their old title snapshots.
Do not rewrite private history or break saved song IDs to remove those snapshots.
The media host's audio filenames remain unchanged; this is not an audio reupload.
Deploy from a clean committed snapshot when the main workspace contains unrelated
lyric edits. Do not include those edits in a metadata-only release. After Pages
deploys, repeat the browser check with `--origin https://fun.lazying.art`.

Only eligible records pass the existing public learning API filter. The
legacy `preview` IDs still follow that filter; do not weaken its privacy rules
as a side effect of a naming pass. Fun's explicit published/preview catalog
controls are separate from that more restrictive native feed.
