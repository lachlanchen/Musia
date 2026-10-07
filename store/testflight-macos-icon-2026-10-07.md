# Rounded Mac Icon Test Update

Scope: fix the square Mac icon, audit all native platforms, and distribute to
testing only. Do not submit or replace formal reviews.

## Root Cause

The shipped Mac 0.1.3 (5) still contained the old opaque teal/equalizer icon.
Its actual archived `AppIcon.icns` was extracted and inspected. The October 6
ribbon update reached iOS 0.1.3 (6) and Android 0.1.3 (5), but Mac was explicitly
not rebuilt in that delivery. Rounded Mac source PNGs alone did not update the
installed TestFlight binary. This was a packaging/delivery gap, not evidence of
a user-side icon-cache problem.

## Candidate And Checks

Mac **0.1.3 (6)** now packages the existing approved coral/cyan ribbon artwork,
with transparent rounded corners and balanced Dock padding. It is a universal
Intel/Apple-silicon signed installer. No song data, playback, permissions,
pricing or public listing changed.

Installer SHA-256:
`65161e669f5091574525f29a1e8338a2cbbd9637cafd48e1c7f7cdbeb48ef6bc`.

- New silhouette tests check the visible tile's corners, not just the corners
  of its canvas. A padded square and an almost-square tile fail. Small-size
  anti-aliasing is handled without accepting opaque square corners.
- All 18 source exports pass dimensions, color type, corner, detail and padding
  checks. Android's colored detail remains inside its adaptive safe circle.
- `tools/store/inspect_macos_icon.swift` checks the actual compiled ICNS and
  macOS `NSWorkspace.icon(forFile:)` at 64px and 512px, saving native renders.
  The old package fails; the new archived app passes. The Mac-rendered icon was
  visually inspected. These are native icon renders, not a fabricated Dock shot.
- Both the Mac build and upload tools now run this check. The upload tool
  expands and checks the exact signed installer, not just a source PNG.
- New package signatures, sandbox, universal architectures and identity pass.
  Apple's package validation passes. Upload/processing is tracked separately.
- Five geometry regression tests and all 42 store-tool tests pass.
- Swift core: 29 tests executed, one opt-in network test skipped, zero failures.
  No new physical-device audio or locked-screen test is claimed for an icon-only
  update; prior Stage UI evidence remains applicable to unchanged app code.

## Mobile Audit

- Android 0.1.3 (5): the icon extracted from the signed AAB matches the latest
  ribbon source exactly at the decoded-pixel level. Existing launcher evidence
  and the package's adaptive/round-icon bindings are retained. No source icon or
  app behavior change requires a duplicate Android upload.
- iOS/iPadOS 0.1.3 (6): the signed IPA contains the ribbon icon; extracted iPhone
  and iPad assets were checked. The opaque source is intentional, not a Mac-style
  transparent tile. iOS applies its platform mask.
- A fresh iPhone simulator home-screen capture on the KVM again showed blank
  artwork even for Apple's system icons. This is retained as a graphics-test
  limitation, not called a passing Musia launcher inspection. That owned
  simulator was shut down afterward.
- Android launcher outlines depend on the device mask; do not bake a second
  mask into adaptive foreground layers. See
  [Android adaptive icon guidance](https://developer.android.com/develop/ui/compose/system/icon_design_adaptive).

## Delivery

Confirmed **October 7, 2026, 19:55 Hong Kong time**: Mac 0.1.3 (6) is VALID,
IN_BETA_TESTING, and attached to the existing Musia Internal group. Exact build:
`e4fabee4-19b1-4c42-85d7-5a962683e35c`. Open TestFlight on Mac and update Musia.

Existing iOS 0.1.3 (6) and Android 0.1.3 (5) remain the latest correct mobile
test builds, with fresh provider readback. They were not rebuilt or uploaded
again. No new invitation or formal review requested; email delivery is not
independently verified.

Both formal Apple 0.1.2 (4) submissions remain WAITING_FOR_REVIEW, with the
same iOS build `7b0ae745-7e3b-44ab-9100-1de68e99cfc7` and Mac build
`1d5a2c57-de54-4120-a219-5a4b158265f5`. No production, price or territory changes.

Private archive, installer and icon evidence are on the established KVM Mac at
`store/.runtime/macos-0.1.3-6/`. Cross-platform evidence and provider readback are
in `store/.runtime/corners-20261007/`. Coordination handoff belongs under
`/home/lachlan/Nutstore Files/OneTimeSync/Musia/`.
The owned iPhone simulator and read-only Google tab are closed; no build,
upload or polling task remains running. The shared store browser is preserved.

## Repeatable Validation

```sh
node --test apps/shared/scripts/icon-geometry.test.mjs
node apps/shared/scripts/validate-icons.mjs
python3 apps/macos/scripts/validate.py
python3 -m unittest discover -s tools/store/tests
# On the authorized Mac, after a native build:
xcrun swift tools/store/inspect_macos_icon.swift /path/to/Musia.app /private/icon-evidence
```

Keep the platform's current and previous reproducible package plus evidence.
Do not flush system-wide Dock/LaunchServices caches or replace another app's
artwork to fix a Musia icon. After updating in TestFlight, quit/reopen Musia
before investigating any stale running-app icon.
