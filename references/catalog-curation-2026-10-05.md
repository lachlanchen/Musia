# Catalog Curation: October 5, 2026

## Published Website

Source commit `272776c` is live at <https://fun.lazying.art>.
GitHub Pages run `37270593910` succeeded. The public catalog contains:

- 30 selected songs, one companion MV, 14 archived recordings, one unlisted preview.
- Titles formatted as `Chinese title · English title`.
- Archived titles formatted as `Chinese title · English title · Archive 01`.
- Half a Melody in Chang'an: the existing ACE Changfeng recording stays selected;
  the MiniMax recording is hidden, not deleted. Its public display title is
  `半曲长安 · The Melody I Left in Chang'an`.
- Language vocals retained. The prior same-language Luoshenfu take is archive-only.
- Stable IDs, audio URLs, musical analysis, timing and lyric files are unchanged.

Use `?hidden` to browse archives, or `?showall` for the complete library.
The default song remains the previously selected Snow We Share recording.
The media repository does not require an audio reupload for this change.

## Verification

- Six catalog tests, 29 learning API tests, nine web/core guitar tests and eight
  deployment tests passed. Guitar-shape generation checks passed.
- Fun manifest validation passed; the curation script is idempotent.
- Independent metadata-only checks verified preservation of manifest musical
  content and study analysis. Unrelated uncommitted lyric edits were not staged.
- Live Playwright checks passed at 1440x1000 and 390x844: bilingual title fit,
  archive filtering, hidden alternative takes, and stable names when changing
  vocal language. No JavaScript page errors occurred.
- The browser test waits for the active asset and rendered title, not merely
  the earlier manifest fetch, before checking language switching.
- Local screenshots: `.runtime/catalog-presentation/player-{1440,390}.png`.
- Naming instructions updated in the repository, installed Codex skill and
  LazySkills (`9ed2aba`).

## App Catalog: Not Yet Deployed

No new iOS, macOS or Android build is needed. Those apps fetch the learning API.
However, its server deployment was refused by the existing memory safety check:
the preflight observed 101 MiB available; a subsequent read showed 125 MiB,
below the required 180 MiB. There was no obsolete Musia process to remove.
No service, firewall, ingress or other project's process was changed.

The live learning API still returns the previous titles and both Chang'an
recordings. Do not describe the native catalog update as published yet.

The validated release is retained locally:

- SHA-256: `eeeec9d74a88819d33b3c71227ae981d617e6c89311c671bf36bee6e7298430b`.
- Archive: `deploy/learning/.work/build-20261005T140517/release.tar.gz`.
- Receipt: `deploy/learning/.work/20261005T140532-eeeec9d74a88/release-receipt.json`.
- Private preflight: the same transaction directory's `preflight.json`.
- Projected API: 29 songs plus First Pulse, retaining the existing preview-ID
  privacy filter. The build passed its staged HTTP acceptance.

The build used a clean detached worktree at `272776c`, plus the existing
generated `apps/web/vendor/lucide.js`, not the dirty primary workspace. It reused
the existing dependency cache and wrote artifacts to the main deployment work
directory. The temporary worktree can be recreated from the commit.

Resume only after sufficient memory is available. Follow
`deploy/learning/README.md`, rebuild from a clean committed snapshot, and verify
both `/api/v1/library` and `/api/v1/songs/ban-qu-chang-an-ace-changfeng` afterward.
Do not lower the memory threshold or stop unrelated services to force a release.
The naming rules and reviewed work-family map are in
`catalog-presentation-policy.md` and `catalog-curation.json`.
