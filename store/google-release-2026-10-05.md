# Google Play Production Release

**Published October 5, 2026. Production is Active: 0.1.1 (2).**

The owner explicitly authorized publication after a fresh Console check showed
the approved release under **Changes ready to publish**. Published the exact ten
approved changes once, confirmed the final **Publish changes** dialog, and
reloaded the Console to verify **Last published on October 5, 2026** with an
empty ready-to-publish queue.

## Verified Release

| Field | Result |
| --- | --- |
| Name / developer | Musia: Learn Music & Guitar / LazyingArt LLC |
| Package | `art.lazying.musia` |
| Play app record | `4973883817798043601` |
| Version / code | 0.1.1 / 2 |
| Production track | Active; latest release 0.1.1 (2) |
| Rollout / availability | Full rollout; 172 countries/regions |
| US price | USD 2.99 |
| Managed publishing | Still enabled for future changes |
| Public listing | HTTP 200 at 2026-10-05T04:07:13Z |

The unauthenticated US listing independently identifies the exact app and
developer. Its structured SoftwareApplication data reports an InStock offer
priced at USD 2.99. This verifies public US availability, not purchase/install
completion on every device or immediate propagation in every region.

[Open Musia on Google Play](https://play.google.com/store/apps/details?id=art.lazying.musia).

## Scope and Evidence

No new binary, price, country selection, legal declaration or tester invitation
was created. The existing qualified production candidate was released. Apple
iOS and macOS submissions remain untouched; both were freshly observed as
WAITING_FOR_REVIEW earlier on October 5.

Private evidence is under `store/.runtime/formal/play-release-20261005/`:
before/after reload text, production track state, public listing HTML and HTTP
receipt. The final Console confirmation is also in the private action journal.
Only this task's retained tab was used; shared browser/profile and peer tabs
were preserved. No build, emulator or extra desktop was started.

Do not click Publish again for this release. Future changes should first be
reconciled against the active track and the current publishing queue. The
existing beta CLI's formal-publication restrictions remain unchanged.
