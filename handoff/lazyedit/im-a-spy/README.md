# I'm a Spy Publication

Release: **我是间谍 · I'm a Spy**, by Musia.
The listener approved the song and requested the usual recorded-video and
Shipinhao Music publication on November 11, 2026.

## Sources

- Player: https://fun.lazying.art/#im-a-spy
- Full audio: `data/creative_projects/im-a-spy-20261111/selected/im-a-spy-en.mp3`.
- Corrected English performance: `website/data/songs/im-a-spy/lyrics/en-vocal/en.json`.
- Context: `listener-context.md`; origin record: `creation-proof.md`.
- Square music artwork: `data/creative_projects/im-a-spy-20261111/cover-square.png`.

The music package has all **49** reviewed English lines, including actual
repetitions. Its plain lyric text is identical to the website track. The full
184-second, 320 kbps MP3 is unchanged; its SHA-256 is
`77ff438fbc13308ce10408cdf44401a1da230caa020daf71e132346a28a9461a`.
The generated square artwork preserves the song's couple, glass observatory,
stars, flowers and small apple, with no text or logo. It was made with the
built-in image-generation tool, not a reused song cover.

## Recording

Fast realtime capture, native 2160 x 3840, 24 fps. Full-width player, current
trilingual lyric display with readings, active chords and guitar fingering.
No full lyric sheet, added subtitles or portrait background fill.

The recording starts at source time **17.136 seconds**, a beat boundary about
1.5 seconds before the first lexical vocal. It runs **166.864 seconds**, through
the original ending. The same offset is applied to muxed audio and reviewed SRT.
The music submission retains the full intro and full song.

- Recording: `recorded_videos/im-a-spy/im-a-spy-en-lyrics-guitar-portrait-4k.mp4`.
- Synced recording: `/home/lachlan/Nutstore Files/Projects/Musia/im-a-spy-en-lyrics-guitar-portrait-4k.mp4`.
- Synced logo master: `/home/lachlan/Nutstore Files/Projects/Musia/im-a-spy-en-portrait-4k-logo.mp4`.
- Recording SHA-256: `a3571d00f7607ab2b01d4a8a80bda67cfc967c2d6ceffa17f868e7c10e548f16`.
- Logo master SHA-256: `c68321511904c8def086e2659debc78375ec853fcb74a0c8c81743718ce84784`.

The first capture briefly froze during cold startup and was rejected, never
published. The realtime recorder now warms font/image decoding and the initial
lyric/chord layouts for five seconds before resetting the capture clock. The
new recording passes 167 one-second visible-clock samples within the audit's
one-second integer-clock tolerance. One OCR misread was visually checked and
recovered by the raw-line OCR fallback. This checks screen-clock progression,
not phoneme-perfect lyric timing or musician-verified chords.

The existing LazyEdit logo is top-right at a one-run height ratio of 0.028;
shared settings are unchanged. Sampled lyric/guitar SSIM after logo rendering
is 0.997815, and the frame was visually inspected for legibility and overlap.
The packaged MP4 hash matches this inspected logo master exactly.

## Jobs

- LazyEdit video: **681**; local publication job: **538**.
- Remote video: `job-1794402926468-6`.
- Video destinations: normal Shipinhao, Instagram, YouTube and Douyin accounts.
- Music item: **48**; remote music: `job-1794402959875-7`.
- Music destination: Shipinhao Music only, queued after the video job.
- Pure-music package: `im-a-spy-en-music-20261111.zip`.

Submission requests are accepted. Platform results must be verified before
calling publication complete. Do not repost confirmed targets; inspect existing
jobs and management receipts before retrying an uncertain outcome.

## Reproduction and Evidence

`ideas-and-inspirations/im-a-spy/prepare_publication.py` derives the reviewed
recording SRT and hash-bound inputs. With `--video-id`, it also prepares one-run
LazyEdit process/publish requests; it does not submit them or change defaults.

`scripts/audit_recording_clock.py` scans a captured player clock against the
source-audio offset. Its clock crop is layout-specific and must be checked
when the recording geometry changes.

Runtime evidence, generated packages, queue receipts, screenshots and final
publication results belong in `recorded_videos/im-a-spy/`, outside Git.
