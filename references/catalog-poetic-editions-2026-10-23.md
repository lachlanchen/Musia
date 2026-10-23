# Luoshen Fu Recording Names And Cover

## Presentation

| Recording | Public name | Artwork |
| --- | --- | --- |
| Selected `luoshenfu-pronunciation-v2` | 洛神赋·回雪 · Snow on the Wind | New dawn river/palace cover |
| Archived `luoshenfu-original-zh` | 洛神赋·惊鸿 · A Glimpse of Grace | Existing blue moonlit cover |

Both names draw from the sung text. They distinguish the recordings without
claiming different source poems. `原文选段` and `V2` are not public titles.
The shared media ID remains `luoshenfu-original-excerpt-preview`; the old asset
IDs and audio filenames remain stable to preserve links and lyric associations.
The original recording remains hidden unless archive/show-all mode is used.

Other reviewed titles already match the intended clean catalog names, including
半曲长安 · The Melody I Left in Chang'an, 共白头 · Snow We Share,
哭晁卿衡 · Moon Over the Blue Sea, 凉州词 · Songs of Liangzhou and
越人歌 · Song of the Yue Boatman. No additional rename is needed for these.

## Cover

Built-in image generation produced the new artwork on October 23, 2026.
File: `website/assets/covers/luoshenfu-hui-xue-16x9.png`, 1672 x 941 pixels,
near-16:9 landscape. The original image remains unchanged. The companion square
Shipinhao artwork is not yet prepared or uploaded.

Prompt brief: an elegant woman in flowing ivory Han-style robes beside the Luo
River at dawn, translucent gauze moving over jade water, a vast tiered
Han-inspired palace terrace disappearing into luminous mist, sparse windborne
flecks and reflective ripples recalling returning snow. Pearl light, jade and
rose dawn highlights. Central subject suitable for a later square composition.
No text, logo, watermark, circular gateways, giant moon or unrelated imagery.
This is imaginative cover art, not a historical reconstruction.

## Data Safety

The curation map is the title/artwork authority. Named-recording overrides also
update selector labels, the current player title/cover, share metadata, Atlas
title and Media Session metadata. Musical identity checks preserve audio URLs,
durations, each lyric set and all timeline/chord/beat data.

Musia's public learning API intentionally excludes legacy preview/hidden IDs.
This task does not relax that filter, create a duplicate public ID or promote
the archived take. The live API was checked and already serves the clean names
for the other listed songs. No native binary or app-store submission is needed
for this metadata change; Luoshen Fu remains excluded from the app feed under
the existing eligibility policy.

Shipinhao entries are not edited by this release. Their one-time title/cover
changes require separate live-record reconciliation and a complete final packet.

## Verification

Local verification passed: 11 catalog curation unit tests, 35 learning API
tests, the no-drift check, website protocol validation and JavaScript syntax
validation. The browser regression passed at 1440 x 1000 and 390 x 844. It
covers both recording titles/covers, the hidden-original filter, retained lyric
set IDs, share/lock-screen metadata and unchanged multilingual vocal titles.
Desktop and mobile screenshots were also visually inspected.

Deployment verification must read back the live manifest and compare the new
artwork hash. The private release receipt records the deployed commit and
whether those checks passed.
