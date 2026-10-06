# Beyond the Maples Publication

Requested 2026-10-06 after the user approved the selected Japanese performance.

## Approved Sources

- Title: 楓の向こうで · Beyond the Maples
- Artist: Musia
- Vocal language: Japanese only.
- Full music master: `data/creative_projects/aya-canada-beyond-the-maples-20261006/selected/aya-canada-beyond-the-maples-ja.mp3`.
- Corrected sung lyrics: `website/data/songs/aya-canada-beyond-the-maples/lyrics/ja-vocal/ja.json` (36 lines).
- Square music cover: `data/creative_projects/aya-canada-beyond-the-maples-20261006/cover-square.png`.
- Public metadata context: [listener-context.md](listener-context.md).
- Private publication proof: [creation-proof.md](creation-proof.md).

Use the exact corrected Japanese lyric lines as plain text for Shipinhao Music.
Do not substitute the original draft, a translation, or LRC timestamps.

## Video

- File: `recorded_videos/aya-canada-beyond-the-maples/aya-canada-beyond-the-maples-ja-lyrics-guitar-portrait-4k.mp4`.
- Nutstore: `/home/lachlan/Nutstore Files/Projects/Musia/aya-canada-beyond-the-maples-ja-lyrics-guitar-portrait-4k.mp4`.
- SHA-256, both copies: `64684d3e6245c6b364ed7a9e7464af3f382b823f6f902d9a7b285fc3495dff9b`.
- Native capture: 2160x3840, 24 fps, H.264; AAC 48 kHz stereo.
- Starts at source time 9.5666 seconds, about 1.5 seconds before the first vocal.
- Duration: 146.433 seconds; original audio muxed at the same source offset.
- Layout: player, current Japanese/English/Chinese lyric translations, guitar fingering.
- Reviewed frames: video times 50 and 138 seconds. No lyric/guitar overlap.
- LazyEdit: existing top-right logo, no additional subtitles, no background fill.
- Targets: Shipinhao video, Instagram, YouTube, Douyin; then Shipinhao Music.

Recording used `scripts/record_fun_player_realtime.py`, native 4K screen capture,
`--publication-layout --capture-clock --multilingual-lyrics --advanced
--no-guitar-focus --lyrics-guitar`, with CRF 12 and the ultrafast encoder preset.
The video is not an upscaled low-resolution capture.

## Publication Status

Recording and Nutstore synchronization verified. LazyEdit video: 607.

- Initial video job 448 / `job-1791281504171-7` failed at Douyin upload before
  any platform post. The uploader displayed `上传失败，重新上传`; it had shown
  2%, 12.8 KB/s and approximately 55 minutes remaining. A draft-recovery selector
  also timed out. The cause of the slow/failed network upload is not established.
- Job 449 / `job-1791281836107-9` **completed**: Shipinhao video was confirmed
  in management; Instagram verified the saved caption at
  https://www.instagram.com/lazyingart/reel/DeJjmI8ORwP/; YouTube completed checks
  and returned https://youtube.com/shorts/_kFST2FpDU0. Do not repeat these posts.
- Douyin-only retry `job-1791281868420-10` restarted only its browser, but a
  malformed retry request sent form fields instead of ZIP bytes. The old API
  overwrote the ZIP and failed before uploading. This was not a platform outage.
- AutoPublish fix `69de891` was pushed and deployed with the shared queue idle.
  It guards ZIP uploads, fixes the stale draft selector wait, logs transfer
  progress and preserves per-platform results. A durable queue journal was
  enabled after preserving all prior terminal receipts. HTTP 400 rejection of
  a malformed request was checked against the live service without publishing.
- Corrected raw-ZIP, Douyin-only retry: `job-1791282667698-1`. Same reviewed
  video hash; no recording regeneration and no other platform retries.
  **Submission confirmed 18:39:52 Asia/Hong_Kong, 2026-10-06.** The upload
  retried once after a 96% transfer failure, then completed successfully.
  The publication receipt and management listing were checked. The 02:26 row
  displayed **审核中**, so submission is complete but public visibility awaits
  Douyin moderation. Do not resubmit while that review is pending.
- **Shipinhao Music verified listed, `已上架`** on 2026-10-06. LazyEdit music item
  44 / `job-1791281606306-8`. Management row has the exact title
  `楓の向こうで · Beyond the Maples`. Its audio hash and all 36 plain Japanese
  lyric lines match the reviewed website source exactly. Square cover and the
  provenance ZIP uploaded successfully. No LRC timestamps or translated lyric
  rows were submitted.
- Music form limitation: AutoPublish could not select `日语` (the aliases
  `日语`, `日文`, `日本語`, `Japanese` were not found); the submitted form retained
  `普通话`. This is a metadata discrepancy, not the actual vocal language. It
  must not be represented as a successful Japanese-language dropdown selection.

All four video submissions are confirmed. A queue receipt alone was not used
as evidence: platform submission/management checks are recorded above.

Publisher changes are pushed through AutoPublish `d32f926` (ZIP/CRC guards,
draft recovery, per-target results and a read-only upload probe), and referenced
by LazyEdit `f198552`. The publisher was updated only while idle; the completed
Douyin receipt survived its reload from the private queue journal. Full test
result: 81 passed, two existing unchanged Instagram caption-test failures.
All tests outside that Instagram module pass (69).

## Published Video Asset

The logo-only derivative is also synced to:

`/home/lachlan/Nutstore Files/Projects/Musia/aya-canada-beyond-the-maples-ja-portrait-4k-logo.mp4`

SHA-256: `d82aac3d417ce947e5f51c348d3bc101c2b787fd00f237548e6570e23d28e93e`.
This exact MP4 is inside the AutoPublish ZIP. It remains native 2160x3840,
24 fps, AAC stereo; 146.453 seconds. Sampled lyric/guitar-region SSIM at video
50 seconds versus the recording master is 0.997456, in addition to visual
readability review. Smaller file size alone is not evidence of lost resolution.

## Prepublication Corrections

The first no-publish preview used the shared 15%-height logo and obscured part
of the release title. It was rejected before upload. A song-only logo burn
uses the same asset at 2.8% of frame height, top-right, without modifying shared
Studio defaults. Review the new frame before posting.

The first metadata pass substituted the translated Chinese title in English
metadata. The context was clarified and all three metadata languages regenerated.
The second English pass still appended a genre label despite the exact-title
instruction; only that title field was normalized to the approved release name
as an explicit recovery. The descriptive prose remains LazyEdit-generated and
was checked for story relevance. No production-conversation notes are public copy.

The one-shot request in `video-publish-request.json` reuses video 607's reviewed
processed output. It must not be blindly replayed after a confirmed publication:
check the stored platform receipts first and retry only missing targets.

After dispatch, the China-platform sanitizer was observed turning the Japanese
name into the nonsensical `枫的向`. The first job never posted. For subsequent
video attempts, the Chinese metadata title uses the proper existing translation
`枫叶彼端 · Beyond the Maples`; English metadata, the recording itself, the
website and the pure-music release retain `楓の向こうで · Beyond the Maples`.
The normal generated descriptions remain unchanged. This defect is reported in
LazyEdit's `bug-reports/2026-10-06-musia-japanese-title-and-portrait-logo.md`.
