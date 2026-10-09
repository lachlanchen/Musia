# Home on the Breeze Publication

Requested 2026-10-09. Release: **ただいま、風のなか · Home on the Breeze**,
artist Musia. Chinese platform title: **风中归来 · Home on the Breeze**.

## Authoritative Sources

- Song: https://fun.lazying.art/#aya-home-on-the-breeze
- Full audio: `data/creative_projects/aya-home-on-the-breeze-20261009/selected/aya-home-on-the-breeze-ja.mp3`.
- Corrected lyrics: `website/data/songs/aya-home-on-the-breeze/lyrics/ja-vocal/ja.json`.
- Square artwork: `data/creative_projects/aya-home-on-the-breeze-20261009/cover-square.png`.
- Metadata context: [listener-context.md](listener-context.md).
- Creation record: [creation-proof.md](creation-proof.md).

Only Japanese is sung. EN/ZH are companion translations. Music publishing uses
all 40 corrected Japanese lines as plain text, not the draft or LRC timestamps.
Package audio SHA-256 and all 40 lines were compared exactly with these sources.

## Recording

Realtime native portrait capture: 2160x3840, 24 fps, H.264, 48 kHz stereo AAC.
Player, current multilingual lyrics, chord carousel and guitar fingering;
coral/sky-blue theme. No full lyric sheet, no background fill, no added subtitles.

Source start: **14.6s**, 1.5 seconds before the first lyric. Duration: **169.4s**.
Synthetic capture clock and muxed original audio use the same offset.
Frames at video 55s and 162s were checked for lyric timing and non-overlap.

Local original:
`recorded_videos/aya-home-on-the-breeze/aya-home-on-the-breeze-ja-lyrics-guitar-portrait-4k.mp4`

Nutstore original:
`/home/lachlan/Nutstore Files/Projects/Musia/aya-home-on-the-breeze-ja-lyrics-guitar-portrait-4k.mp4`

Both SHA-256: `158d969a66d7c32eb792f4735909423e379929454e265418f2a52ee20585322e`.

Exact logo-only publication master, also synced:
`/home/lachlan/Nutstore Files/Projects/Musia/aya-home-on-the-breeze-ja-portrait-4k-logo.mp4`

SHA-256: `3f9d57b720e4684a86708ef895194fb98cda525fa52fd80e084c1cd4a6ac4b8a`.
Duration 169.408s, unchanged 2160x3840/24fps. The existing LazyEdit logo is
top-right, height ratio 0.028, as a one-shot override; shared defaults unchanged.
The processed lyric/guitar region at 55s has sampled SSIM 0.999175 against the
recording, with a separate visual sharpness check. The MP4 inside the submitted
ZIP was hash-matched to this reviewed logo master.

## Jobs and Deduplication

No prior matching jobs existed before this request. Do not replay after a
confirmed post. Retry only a failed platform with the same reviewed ZIP.

- LazyEdit video ID: **609**. Local publication job: **451**.
- Remote video job: **job-1791556875057-2**.
- Targets: Shipinhao video, Instagram, YouTube, Douyin.
- Video ZIP: `aya-home-on-the-breeze-ja-lyrics-guitar-portrait-4k.zip`.
- LazyEdit music item: **45**.
- Remote music job: **job-1791557167225-3**, queued after the video.
- Music ZIP: `aya-home-on-the-breeze-ja-music.zip`.
- Music target: Shipinhao Music only; full 184-second song, not the intro-cut video.

Verified completion (local time, UTC+8):

| Target | Evidence | Completed |
| --- | --- | --- |
| Douyin | `job-1791556875057-2`, platform result done | Oct 9, 22:57 |
| Instagram | [Public reel](https://www.instagram.com/lazyingart/reel/DeRz1AvuSKV/) | Oct 9, 23:23 |
| YouTube | `job-1791556875057-2`, platform result done | Oct 9, 23:34 |
| Shipinhao video | Scoped repair `job-1791560823457-1`, done | Oct 10, 00:01 |
| Shipinhao Music | Retained form recovery after `job-1791562024442-1`; management row **已上架** | Oct 10, 00:15 |

The music management count rose from 25 to 26, with this exact title first.
Screenshot and management JSON are retained privately under the recording
directory. Music uses the full 184-second master, square cover, all 40 corrected
Japanese lines, Japanese language, and the public website playback URL.
No successful video platform was duplicated during recovery.

The first metadata pass altered both release titles. A stronger exact-title
instruction and normal metadata-only retry fixed them. Later, the Chinese
platform sanitizer damaged Japanese quotations in the generated description;
a diagnosed Shipinhao-only recovery replaced that prose with natural Chinese.
It did not change the video or repost the other targets. Descriptions focus on reunion and the song.
The bilingual title survives the final platform packaging.

## Reliability and Retention

AutoPublish now caches only verified original public Tencent WASM dependencies
when the CDN is unreachable, fixes the asynchronous Japanese dropdown, waits
for native music form validation, requires explicit submission confirmation,
and avoids automatic duplicate retries after a submit click. Production
autoreload defaults off. LazyEdit includes the source URL in music packages.

Published staging cleanup is **on by default**. It requires archive checksums
and successful receipts for every requested target. It deletes only matching
remote staging media and uploaded ZIPs, preserving corrected lyrics, covers,
proofs, metadata, receipts and all original/Nutstore masters. Active, failed,
ambiguous and unverified old data remain. See AutoPublish's
`references/shipinhao-dependencies-and-published-retention.md` and LazyEdit's
`bug-reports/2026-10-09-shipinhao-wasm-and-music-language.md`.

Four verified staging packages were cleaned, freeing **244,832,791 bytes**.
The canonical song and Nutstore logo master hashes were rechecked afterward.
Music item 45 and video job 451 are reconciled as published/done; the remote
queue is idle. Earlier failed attempts remain in the audit history.

## Native App Catalog

The song is listed in the live Musia catalog at `https://musia.lazying.art`.
Library and song-detail API checks confirm this ID and JA/EN/ZH tracks of
40 lines each. No native store build or review was changed.

Clean source snapshot: `ba98af4`. Immutable release SHA-256:
`f6501fc892071a3368879ff96fa6f7d4fe4e3d3d1dd4ba8993b350c7f0b2d867`.
Deployment transaction: `20261009T222233-f6501fc89207`.
Public acceptance: 73 checks passed, 31 songs plus First Pulse.
The existing guarded deployment reused the runtime cache and preserved other
services. Private receipts remain under `deploy/learning/.work/`.
The temporary clean worktree and recorder GUI were closed after use.
