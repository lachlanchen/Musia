# Brave in Paris Publication

Owner approved the song and requested recording, video publication and
Shipinhao Music on October 15, 2026. Aya's Chinese name is **阿芽**.

## Sources

- Website: https://fun.lazying.art/#aya-brave-in-paris
- Full 188-second audio: `data/creative_projects/aya-brave-in-paris-20261015/selected/aya-brave-in-paris-ja.mp3`.
- Corrected 37 Japanese lines: `website/data/songs/aya-brave-in-paris/lyrics/ja-vocal/ja.json`.
- Story context: `listener-context.md`; provenance: `creation-proof.md`.
- Music audio SHA-256: `9849c10f7e1e98b40fa2ac30072e384fa823a20a0d6a59fa4cd16e99a913fd57`.

The song is now listed, with 阿芽/pinyin corrected in all four relevant Chinese
translation lines. Japanese words/tokens/timing remain identical to the
approved preview. Player copy is story-only; provenance remains in the
manifest and original-proof package. Required platform declarations remain
separate from the promotional description.

## Recording

Realtime native 2160x3840 portrait, 24 fps, source audio muxed at 13.7 seconds.
The first lexical lyric starts at 15.2 seconds, leaving 1.5 seconds of musical
lead-in. Recording length: 174.3 seconds. No background fill, no extra subtitle
burn, player/current multilingual lyrics/chords/guitar publication layout.

Original and Nutstore copies match:
`d0a6969c3dd5677dce4f1a97a3e468450c8f55bc9d850d910f767dd4d943587b`.

- Local: `recorded_videos/aya-brave-in-paris/aya-brave-in-paris-ja-lyrics-guitar-portrait-4k.mp4`.
- Nutstore: `/home/lachlan/Nutstore Files/Projects/Musia/aya-brave-in-paris-ja-lyrics-guitar-portrait-4k.mp4`.
- Logo master: `/home/lachlan/Nutstore Files/Projects/Musia/aya-brave-in-paris-ja-portrait-4k-logo.mp4`.

Existing LazyEdit logo, top-right, one-time height ratio 0.028; shared defaults
unchanged. Sampled lyric/guitar SSIM after the logo-only encode: 0.999196.
Chorus and final repeated lyric frames reviewed for clarity and non-overlap.

## Jobs

- Website release: `f90da9d`; Pages run `38749739803` succeeded.
- Live desktop/mobile playback and lyric/ruby/chord checks passed.
- LazyEdit video 618, publication job 461.
- Remote video job `job-1792074274794-10`.
- Video targets: Shipinhao, Instagram, YouTube and Douyin.
- Music item 46, remote job `job-1792074415721-11`, queued after video.
- Music target: Shipinhao Music only, full master with square Louvre artwork.
- Music package lyrics and audio hash compared exactly with the website/source.

Do not replay a confirmed target. Generated media, private queue snapshots and
API payloads stay outside Git under the recording directory.

## Confirmed Results

All four video targets completed on October 15, 2026 (Hong Kong time).

| Target | Confirmed time | Result |
| --- | --- | --- |
| Douyin | 22:27:02 | Published; management verification matched the new post |
| Shipinhao video | 22:29:34 | Published; management verification matched the new post |
| Instagram | 22:32:46 | [Published reel](https://www.instagram.com/lazyingart/reel/DehLVMUOQwp/) |
| YouTube | 22:35:52 | [Published Short](https://youtube.com/shorts/f3yLcYt4654) |
| Shipinhao Music | 22:37:06 | Submitted; management row explicitly shows 审核中 |

Remote video job and local publication job 461 are `done`. Music item 46 is
`submitted`, remote status `done`; this means upload/submission succeeded, not
that music review has been approved. The management row has the official name
**小小勇气，走向巴黎 · Brave in Paris**, Japanese language, all 37 corrected
Japanese lines, full 188-second audio and the square Louvre cover. No public
music-item URL is available yet.

The published ZIP contains exactly the reviewed logo master, SHA-256:
`203c1d879de7daefb289fe0341062785914d8e62b7642620bf462907f36ddb45`.
Its Nutstore copy has the same hash. Local evidence:
`recorded_videos/aya-brave-in-paris/autopublish-final-queue.json` and
`recorded_videos/aya-brave-in-paris/shipinhao-music-management.json`.

Video titles were changed by the metadata prerequisite rerun described below:
Chinese platforms use **阿芽酱的巴黎之歌**; YouTube uses
**Aya Aya Paris Sky: A Gentle Song About Longing and Small Courage**.
Descriptions are story-focused, without AI/model/recording commentary. The
website and pure-music submission retain the official release title. No
duplicate posts were made to repair video titles. Shipinhao's missing Musia
collection was handled as an optional collection fallback; publication itself
was verified. YouTube used the Musia playlist.

## Metadata Follow-up

An initial metadata pass changed titles and used Chinese for English prose.
A stronger language/title contract fixed the normal metadata-only retry.
However, publication readiness subsequently required missing keyframes and
automatically reran completed metadata without context. Resulting titles differ
from the release title, though copy remains about the song and uses 阿芽.
Recorded as LazyEdit bug report
`bug-reports/2026-10-15-reviewed-metadata-replaced-by-prerequisite-rerun.md`.
Future preparation must include keyframes before approval and compare final
packaged metadata, not just preparation files. Never duplicate a post to repair
its title; use an edit or a separately authorized republish.
