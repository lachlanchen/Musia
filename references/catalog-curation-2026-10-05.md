# Catalog Curation: October 5, 2026

## Published Website

Source commit `da41b32` is live at <https://fun.lazying.art>.
GitHub Pages run `37272281087` succeeded, following the initial `272776c` rollout.
The public catalog contains:

- 30 selected songs, one companion MV, 14 archived recordings, one unlisted preview.
- Titles formatted as `Chinese title · English title`, or `Japanese title · English
  title` for Japanese originals. Aya Chan and Dawnlight use their Japanese names.
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

## App Catalog: Published

Accepted at **2026-10-05 06:26:50 UTC** on <https://musia.lazying.art>.
No new iOS, macOS or Android build is needed. On iOS pull down to refresh the
Library; Android has a Refresh action. Reopening the app also fetches the catalog.

- Release: `4faa66d368a185bb71670355d44debb3c819fc6449eee63798b48b1cfff0c4a5`.
- Transaction: `20261005T142512-4faa66d368a1`.
- Previous release retained: `99b459c47682b3c97b1c171c71b82332673ad0206fd36619b01f7a7f52894ff5`.
- 29 songs plus First Pulse; no archived Chang'an recording in the app library.
- Every live song response was compared exactly against the clean, sanitized
  release: names, assets, lyrics, timing, chords, beats and melody all matched.
- 71 public HTTP acceptance checks passed, plus loopback/restart/high-port
  acceptance. Deployment checks preserved unrelated service identities and
  firewall/import fingerprints.
- Live app web checks passed at 390x844 and 1440x1000: responsive titles,
  one Chang'an entry, Japanese titles, actual song playback, no JavaScript errors.
  Evidence: `.runtime/catalog-app-verification/`.
- Eight curation tests, 29 API tests, nine web tests and eight deployment tests
  passed; the Fun live browser tests passed again after the Japanese-title change.

The blocker was the idle firmware daemon, not Musia's catalog memory usage.
With explicit owner approval, it was stopped only after two idle checks and
checks for active firmware clients, refresh or scheduled offline updates.
Its refresh timer subsequently started it again. The owner then authorized
disabling it: `fwupd.service` is masked/inactive and `fwupd-refresh.timer` is
disabled/inactive. Available RAM rose to 233 MiB afterward. Other app services
and normal OS package updates were not disabled. The 180 MiB deployment guard
was not weakened. The verified status value was `1`,
[fwupd's documented idle state](https://fwupd.github.io/libfwupd/enum.Status.html).

Firmware updates through fwupd now require explicitly restoring these units;
authorized administrator restoration is:

```sh
sudo systemctl unmask fwupd.service
sudo systemctl enable --now fwupd-refresh.timer
sudo systemctl start fwupd.service
```

Do not make disabling firmware services a general deployment routine. This was
a scoped, owner-approved action on this shared low-memory server.
The current release archive and complete private transaction evidence are under
`deploy/learning/.work/build-20261005T142446/` and
`deploy/learning/.work/20261005T142512-4faa66d368a1/` respectively.

### Earlier Blocked Attempt

The first server deployment was refused by the existing memory safety check:
the preflight observed 101 MiB available; a subsequent read showed 125 MiB,
below the required 180 MiB. There was no obsolete Musia process to remove.
No service, firewall, ingress or other project's process was changed.

At that point the API still returned old titles and both Chang'an recordings.
That condition is resolved by the accepted release above.

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

Future deployments should follow `deploy/learning/README.md`, use a clean
committed snapshot, and verify both `/api/v1/library` and individual song
responses afterward. Do not lower the memory threshold or stop unrelated
services to force a release.
The naming rules and reviewed work-family map are in
`catalog-presentation-policy.md` and `catalog-curation.json`.
