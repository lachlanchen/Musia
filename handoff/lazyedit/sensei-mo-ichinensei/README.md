# Sensei Mo Ichinensei Publication

- Release: **せんせいも一年生 · A Beginner, Even Now**
- Artist: Musia
- Vocal: Japanese
- Listening page: <https://fun.lazying.art/#sensei-mo-ichinensei>
- Production and lyric review: [production record](../../../references/sensei-mo-ichinensei-production-2026-10-23.md)
- Public-facing story context: [listener-context.md](listener-context.md)
- Origin evidence: [creation-proof.md](creation-proof.md)

## Recording

The recording uses the selected `sensei-ja-102314` vocal, with Japanese,
English and Chinese current-phrase lyrics, ruby, moving highlights and guitar
fingering. It is a direct 2160 x 3840 portrait capture at 24 fps, rendered at
1080 x 1920 CSS pixels with device scale factor 2.

The first vocal begins at 20.72 seconds. Capture starts at 19.18 seconds,
leaving 1.54 seconds of musical lead-in, and runs through the song's end.
The 220.82-second recording uses the same source-audio interval; it does not
use microphone or browser-loopback audio.

```bash
conda run -n musia python scripts/record_fun_player_realtime.py \
  --media-id sensei-mo-ichinensei --asset-id sensei-ja-102314 \
  --output recorded_videos/sensei-mo-ichinensei/sensei-mo-ichinensei-ja-lyrics-guitar-portrait-4k.mp4 \
  --width 2160 --height 3840 --css-width 1080 --css-height 1920 \
  --device-scale-factor 2 --fps 24 --start 19.18 --duration 220.82 \
  --multilingual-lyrics --advanced --no-guitar-focus --lyrics-guitar \
  --publication-layout --capture-clock --crf 12 --preset ultrafast
```

Opening, chorus and ending frame checks found no lyric/guitar overlap or
cut-off diagram. The recorder's dedicated browser and display stopped on exit;
its two listening ports were independently verified closed.

The original recording and default Nutstore copy have the same SHA-256:
`e7fd74760f6ed35b1d5b6632ae38aa23e62cbf8e857c5a8854ba5a2b39eb80c4`.

## Video Publication

LazyEdit video **630**, local publication job **475**, remote job
**job-1792750511868-17**.

Verified video results on 2026-10-23:

| Platform | Evidence |
| --- | --- |
| Douyin | Matching management row, 03:41, submitted 18:16 CST; native state was `审核中` at the 18:18 check. |
| Shipinhao | Publisher matched the new song description in management at 18:20 CST. |
| Instagram | [Published reel](https://www.instagram.com/lazyingart/reel/De1VPBpu8Vc/), saved caption verified. |
| YouTube | [Published video](https://youtu.be/bLonSpgYd0k), exact-title native `Video published` dialog and screenshot verified. |

YouTube reconciliation: the remote job retains a historical failure because
its receipt parser recognizes `youtube.com` links but not the native
`youtu.be` share link. The live success dialog was independently inspected;
no reupload or second publish click was made. Do not retry the video merely
to change that queue status. The parser defect is reported to LazyEdit in
`bug-reports/2026-10-23-youtube-youtu-be-published-receipt.md`.

The Chinese video-platform sanitizer removes kana from short titles. Its
observed Douyin title is `一年生 A Beginner, Even Now`; the Shipinhao short
title is further length-limited. Their descriptions retain the localized song
name and story. The package and Japanese/English release name remain unchanged.
The optional `Musia` Shipinhao collection was unavailable; publication succeeded
without assigning an unrelated collection.

- Targets: Shipinhao, normal Instagram account `@lazyingart`, YouTube, Douyin.
- Native portrait throughout; no background fill.
- No additional subtitle burn. The player already displays reviewed lyrics.
- Existing LazyEdit logo, top-right, one-run height ratio `0.028`.
- Imported SRT: all 51 reviewed Japanese rows, shifted by `-19.18` seconds.
- No replacement transcription or automatic lyric rewriting during publication.
- Prepared keyframes and reviewed metadata before queue submission.
- Preserved shared LazyEdit settings; all overrides are specific to this run.

The packaged MP4 matches the inspected logo master byte-for-byte:
`b26629315aa3692bce7f1ac4b7b19d1d0ec9caa7446a54180ec849b352376ece`.
It remains 2160 x 3840 at 24 fps with stereo audio. A one-second chorus
comparison of the lyric/guitar region measured SSIM **0.998709** relative to
the capture. Lower bitrate here reflects compression of a mostly static player;
visual inspection, not file size alone, determined acceptance.

Metadata recovery: the normal context-driven generator twice replaced the
Chinese release title with an editorial headline. After that observed failure,
only the exact title and a mistaken self-introduction phrase were repaired.
The generated story remained intact. The English artist suffix was removed
from the title; the artist stays in the description. This is a narrow recovery,
not a replacement for context-driven metadata generation.

## Music Submission

LazyEdit music item **47**, package slug
`sensei-mo-ichinensei-ja-music-20261023`.
Remote submission job: **job-1792751744186-18**.

Submitted successfully at **18:36 CST on 2026-10-23**. The management table
contains the exact Japanese/English song and album title, release date
2026-10-23 and native state **审核中**. LazyEdit item 47 is recorded as
`submitted`, not approved or publicly available.

The live form confirmed Japanese language, artist and writer/composer/producer
credits, all corrected lyric text, the full audio, square album cover,
external listening URL and completed proof upload. All native validation
sections passed before submission. The chosen site genre was `流行 / 城市流行`.

- Full 240-second Japanese audio, not the shortened recording interval.
- Artist `Musia`, credit `Musia 慕莎`, language `日语`, genre `流行`.
- Lyrics come from `website/data/songs/sensei-mo-ichinensei/lyrics/ja-vocal/ja.json`.
- All 51 plain-text lines match the reviewed website export exactly, including
  repetitions and the documented uncertain render phrases. No draft lyrics or
  translation was substituted.
- One inspected square crop of this release's new sunlit-library artwork.
- The public listening URL and creation proof accompany the package.
- Only Shipinhao Music is requested; the package's auxiliary art-track video
  does not authorize another YouTube post.

Full audio SHA-256:
`ec86bbc57f06ad6b3031dcb5d9fb6f6ec283bfb8d9485e529c0a12d8937de789`.
Reviewed lyric JSON SHA-256:
`e28017a91d6075550bf0238131ac298f6bca51ab95929d6993d648035e3cfe7f`.
Music ZIP SHA-256:
`80005548e0b196d217677501f293e79a33ae6e0f591a75ad967782595a79299e`.

Do not resubmit either package merely because a browser is slow or a status
receipt is delayed. Check the exact job and platform management first.
Submission to music review is not approval or public availability.

## Local Evidence

Private receipts and frame samples are retained under
`recorded_videos/sensei-mo-ichinensei/`; media and private publisher state are
not committed. The original 4K file is also synced to the standard Musia
Nutstore folder. `publication-status.json` preserves the original queue
results alongside separate native YouTube and Shipinhao Music evidence.

Verified published music staging was automatically archived and cleaned by
AutoPublish. The video staging was retained because the historical queue
failure has not been rewritten. Original media, both local ZIPs, corrected
lyrics, cover, screenshots and Nutstore master remain available.
