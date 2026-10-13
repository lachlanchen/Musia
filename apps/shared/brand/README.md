# Musia App Icon

## Current: Original Sound Bars

On October 13, 2026 the owner chose to restore the original teal sound-bar
icon for the next **test builds only**. `musia-sound-bars.png` is the exact
original 1024px artwork from the parent of commit `0516cc6`, not a redraw.
SHA-256: `165fa7aee650c4519891008f0885b300d96bd375201f3513d219532b2e09a7aa`.

The exporter now uses this master for iOS, the companion Watch, macOS and
Android. It preserves the original geometry and colors. iOS/Watch use the
system mask; Mac gets a transparent rounded mask and 10% canvas padding;
Android gets the matching teal adaptive background and rounded fallbacks.
The separate Fun website logo and First Pulse artwork are unchanged.

Run `node apps/shared/scripts/export-icons.mjs` then
`node apps/shared/scripts/validate-icons.mjs` and
`node --test apps/shared/scripts/icon-geometry.test.mjs`.
All 19 exports are checked, including the companion Watch icon. Always inspect
the compiled Mac ICNS and native icon lookup, not just source PNGs.

The ribbon masters below are retained as design history. Do not silently
restore the ribbon when preparing a future build. This artwork change does
not authorize a production release or a store-listing change.

## Previous: Ribbon M

The coral/cyan ribbon forms an M and suggests a vibrating string. A dark neutral
ground gives the colors contrast without a busy background or a generic music
note. Generated October 6, 2026; the user explicitly requested rounded corners.

- `musia-ribbon-square.png`: generated full-bleed RGB master, retained unchanged.
- `musia-ribbon-rounded.png`: image-generation corner edit, with transparent
  outside corners. The letter and colors retain the same design.

The image-generation originals are preserved locally. These selected masters are
the reproducible source, not an instruction to regenerate artwork on each build.
The shared export commands now select the sound-bar master above:

```sh
node apps/shared/scripts/export-icons.mjs
node apps/shared/scripts/export-icons.mjs ios
node apps/shared/scripts/export-icons.mjs macos
node apps/shared/scripts/export-icons.mjs android
node apps/shared/scripts/validate-icons.mjs
node --test apps/shared/scripts/icon-geometry.test.mjs
```

Requires Node and ImageMagick (`magick` or `convert`) for maintainer exports.
Ordinary native builds use committed assets with no image-tool dependency.

## Rounded Corners

- iPhone/iPad: opaque RGB 1024px source; iOS supplies its own rounded mask.
  Do not bake transparent corners into this store asset.
- Mac: rounded RGBA source with 10% transparent canvas padding. All ten icon
  slots retain transparency instead of becoming opaque square tiles.
- Android: adaptive background/foreground and round-icon manifest entry.
  The foreground is inset into the adaptive layer to protect the M in round
  and rounded-square launchers. Rounded density exports are the fallback.
- Play listing: `store/branding/musia-icon-512.png`, opaque RGB; prepared only,
  not uploaded to change an existing listing automatically.

This artwork is included in the subsequent iOS 0.1.3 (6) and Android 0.1.3 (5)
test candidates. See the [delivery record](../../../store/testflight-0.1.3-icon.md)
for provider availability. Older binaries and formal review attachments are
unchanged. Mac 0.1.3 (5) was not rebuilt for it; the subsequent
[Mac build 6 correction](../../../store/testflight-macos-icon-2026-10-07.md)
packages the ribbon and verifies the compiled/native-rendered icon.
First Pulse artwork and the separate Fun Lazying Art website logo stay unchanged.

## Verification

October 6 checks passed: all 18 exports have correct sizes/color types, small
icons contain visible colored detail, Mac/fallback corners are transparent,
and Android's colored mark fits within a 30.1dp radius (below its 33dp safe
radius). Android debug resource compilation and lint passed; the icon was
visually checked in the native API34 launcher. Apple asset validators passed;
the artwork-only commit itself did not upload a new Apple binary. Subsequent
test packaging and provider delivery are recorded separately above.

`store/.runtime/icon-20261006/launcher.png` holds the private native screenshot.
Regenerating the iOS assets was also checked to leave First Pulse unchanged.

October 7 validation additionally rejects padded square silhouettes. Mac
build/upload tools inspect the signed artifact and native icon lookup, so
correct source PNGs cannot silently stand in for an older packaged icon.
