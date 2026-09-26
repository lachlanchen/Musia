# Chord Diagrams And Navigation Fix

## Causes And Changes

The iOS mini-player was inserted outside `TabView`, placing it in the same
bottom region as navigation. It now reserves space inside each tab's content.
Its opaque background prevents list text showing through. Compact transport
text stays on two single lines and caps at XXXL; the full player retains the
user's unrestricted accessibility text size. A rotation/large-text regression
caught and removed a remaining overlap.

Android already stacks mini-player and navigation inside `Scaffold.bottomBar`
and applies its padding to content. Keep that structure; no device-specific
pixel offsets were added. Web content now reserves the actual measured footer
height, including wrapping and safe-area padding. Small-screen enlarged labels
wrap instead of expanding the document horizontally.

Native clients previously had only Em and Am diagrams; the learning web client
had nine shapes. All three now use generated tables from
[`apps/shared/guitar-shapes.json`](../apps/shared/guitar-shapes.json): all 24
major/minor shapes, enharmonic names, finger assignments, muted/open strings,
explicit barres, and four-fret windows that shift for higher-position chords.
The generator checks exact chord tones, root bass, finger/barre consistency and
viewport bounds. Unsupported extensions/slash chords are not silently changed
into a major/minor shape. This fixes rendering, not the accuracy of automatic
song analysis; estimated chords/timing remain labelled as estimates.

## Verified

- Shared table/three-client parity check passes.
- Swift: 23 passed, one opt-in live-network test skipped, zero failures.
- iPhone 17e simulator, iOS 26.5: navigation, non-overlap, rotation and enlarged
  text checks pass. iPad mini simulator: top-tab navigation, rotation and
  enlarged text checks pass. Both can reopen the full player from mini-player.
- Android signed 0.1.1(2): 36 unit tests and release lint pass. API34 emulator
  navigation passes at phone/tablet sizes with normal and 150% text, including
  tablet landscape. Foreground, Home and screen-off media-session state checks
  pass. Existing app data was preserved by using the same release signing key.
- Public web: nine logic tests, 29 API tests, six deployment tests, actual
  First Pulse and Aya playback workflow, and 12 viewport/text-scale combinations
  pass. Every shape renders; the live audit covers 32 items including First
  Pulse, 45 audio versions and 24 chord symbols, with none unsupported.
- Public JS/CSS hashes match the reviewed local files. JavaScript error count
  in the full playback smoke test is zero.

The remote iOS VM has missing system-tab visuals even before song selection
and corrupt rotation screenshots. UI hierarchy/tap/geometry tests are valid
evidence; those screenshots are not visual signoff. Its previously diagnosed
AVPlayer/audio-clock failure remains. Physical-device visual/playback checks
are still required; no simulator test is presented as a physical-device test.

## Reproduce

```sh
conda run -n musia python tools/generate_guitar_shapes.py --check
node --test apps/web/tests/core.test.mjs apps/web/guitar-shapes.test.mjs
conda run -n musia python scripts/test_musia_chord_layout.py --base-url https://musia.lazying.art
conda run -n musia python scripts/test_musia_learning_web.py --base-url https://musia.lazying.art
conda run -n musia python scripts/test_musia_android.py --serial emulator-PORT --layout-only
```

Use a project-owned Android emulator only. Layout testing restores display and
font settings. Native build/UI commands are in the platform READMEs. Run
`PracticeSmokeTests/testMiniPlayerNavigationWithLargeText` on both iPhone and
iPad: iPad's top floating tabs are buttons rather than a `TabBar` accessibility
container. Wait for rotation geometry before making assertions.

Private evidence: `.runtime/learning/{android-chord-fix,android-chord-layout,
chord-fix-public,chord-layout-public}/`, platform `build/` test results, and
`store/.runtime/`. Test fixtures never become a production musical score.

## Delivery

The learning website is deployed at https://musia.lazying.art, transaction
`20260926T131441-2d58d928cc95`. Release SHA-256:
`2d58d928cc954a0c6eb42f67886aa84cd49d2ed6af17dafa0741ac6c6e7a0bbb`.
The preceding release remains available for rollback. Only the Musia service
and its exact static allowlist changed; other services and firewall rules were
preserved. Current native candidate is **0.1.1 (2)**. Store availability is
recorded separately in `store/provider-readiness.json`; a signed archive or
upload is not a completed TestFlight/internal release.
