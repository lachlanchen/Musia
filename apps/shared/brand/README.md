# Musia Ribbon Icon

The coral/cyan ribbon forms an M and suggests a vibrating string. A dark neutral
ground gives the colors contrast without a busy background or a generic music
note. Generated October 6, 2026; the user explicitly requested rounded corners.

- `musia-ribbon-square.png`: generated full-bleed RGB master, retained unchanged.
- `musia-ribbon-rounded.png`: image-generation corner edit, with transparent
  outside corners. The letter and colors retain the same design.

The image-generation originals are preserved locally. These selected masters are
the reproducible source, not an instruction to regenerate artwork on each build.
Only mechanical resizing, format conversion and platform padding are exported:

```sh
node apps/shared/scripts/export-icons.mjs
node apps/shared/scripts/export-icons.mjs ios
node apps/shared/scripts/export-icons.mjs macos
node apps/shared/scripts/export-icons.mjs android
node apps/shared/scripts/validate-icons.mjs
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

This artwork is for the next accumulated native update. It does not modify the
already-delivered 0.1.3 beta packages or current formal review attachments.
First Pulse artwork and the separate Fun Lazying Art website logo stay unchanged.

## Verification

October 6 checks passed: all 18 exports have correct sizes/color types, small
icons contain visible colored detail, Mac/fallback corners are transparent,
and Android's colored mark fits within a 30.1dp radius (below its 33dp safe
radius). Android debug resource compilation and lint passed; the icon was
visually checked in the native API34 launcher. Apple asset validators passed;
no new Apple binary was uploaded for this artwork-only change.

`store/.runtime/icon-20261006/launcher.png` holds the private native screenshot.
Regenerating the iOS assets was also checked to leave First Pulse unchanged.
