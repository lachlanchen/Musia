# Half a Melody in Chang'an: Recording and Publication

Date: 2026-09-14 (Asia/Hong_Kong).

## Scope

The user approved the Changfeng ACE song and requested the established fast
recorder and video publication without added subtitles. Destinations: Shipinhao,
Instagram, YouTube and Douyin. This task does not publish a pure-music package.

- Website: https://fun.lazying.art/#ban-qu-chang-an-ace-changfeng
- Media ID: `ban-qu-chang-an-ace-changfeng`
- Audio asset ID: `ban-qu-chang-an-ace-changfeng-zh`
- Audio: `https://lazyingart.github.io/MusiaSongs/audio/ban-qu-chang-an-ace-changfeng-zh-seed914203-20260914.mp3`
- Reviewed website lyrics: `website/data/songs/ban-qu-chang-an-ace-changfeng/lyrics/zh-ace-914203/`
- `lyrics.reviewed.srt` in this directory is derived from those 28 reviewed
  Mandarin line intervals, not the generation prompt. Line 25 is the shortened
  actual performance, `等我回来`.

## Fast Recorder

Run from Musia with `PYTHONNOUSERSITE=1` and the `musia` conda environment:

```bash
python scripts/record_fun_player_realtime.py \
  --media-id ban-qu-chang-an-ace-changfeng \
  --asset-id ban-qu-chang-an-ace-changfeng-zh \
  --output recorded_videos/ban-qu-chang-an-ace-changfeng/ban-qu-chang-an-ace-changfeng-zh-lyrics-guitar-portrait-4k-20260914.mp4 \
  --width 2160 --height 3840 --css-width 1080 --css-height 1920 \
  --device-scale-factor 2 --fps 24 --start 0 --duration 138 \
  --multilingual-lyrics --advanced --no-guitar-focus --lyrics-guitar \
  --publication-layout --capture-clock --crf 12 --preset ultrafast
```

Vocal starts immediately, so retain the full song from zero. This is native
portrait browser capture, not an upscaled landscape screen or background-filled
video. The song audio is muxed directly after capture. The existing player
renders lyric translations and ruby; no additional LazyEdit subtitles are used.

Output:

`/home/lachlan/ProjectsLFS/Musia/recorded_videos/ban-qu-chang-an-ace-changfeng/ban-qu-chang-an-ace-changfeng-zh-lyrics-guitar-portrait-4k-20260914.mp4`

Identical Nutstore copy:

`/home/lachlan/Nutstore Files/Projects/Musia/ban-qu-chang-an-ace-changfeng-zh-lyrics-guitar-portrait-4k-20260914.mp4`

SHA-256 (both):
`410c2a4e91cc276024b6dce85744f844fd3c764e221526774853afd737779f2f`

## Verification

- H.264, 2160x3840, 24 fps; 138.000 seconds; 215,275,124 bytes.
- AAC, 48 kHz stereo. Original mux uses 320 kb/s audio.
- Audio comparison at 45-55 seconds: zero measured sample lag at 8 kHz;
  normalized waveform correlation 0.999593; RMS -12.925 dBFS.
- Inspected full-resolution frames at 48 and 126 seconds. Current lyrics,
  highlighting, centered chord and guitar fingering change between the frames.
  Cover, lyrics and guitar remain within the frame without overlap.
- Recorder-owned Chrome/Xvfb/HTTP server terminated after completion. Other
  projects' runtimes were left alone.

## LazyEdit Preparation

LazyEdit video ID: `567`. Global/current output (no separate publication session).

Use `scripts/lazyedit_publish.py`, the `lazyedit` environment, and the deployed
API on localhost port 18787. First run uses `--no-publish`, `--prompt-file
story-context.md`, `--subtitle-file lyrics.reviewed.srt --subtitle-language zh`,
`--no-correct-subtitles --no-burn-subtitles --no-portrait-blur-fill`,
`--logo --logo-position top-right --publish-category musia`.

The authoritative import skipped Whisper and supplied all 28 corrected lines.
The existing Studio logo was applied without changing shared settings. The
logo-only output retains 2160x3840, 24 fps and audio; duration 138.005 seconds.
Its 40,013,458-byte size reflects medium/CRF18 encoding rather than the recorder's
ultrafast/CRF12. A full-resolution sample was inspected; SSIM of the area below
the logo against the captured frame was 0.995819. No additional subtitle track
was burned and no portrait fill was applied.

The first metadata pass put Chinese text in the English metadata file. The
shared story context was clarified and only the three metadata steps were
rerun. This did not re-record or regenerate the song, and did not re-render the
video. Public text must describe the song and listener-facing story, not model
details or internal conversation context.

## Publication Submission

Submitted once through the normal CLI with `--video-id 567 --no-process`,
`--platforms shipinhao,instagram,youtube,douyin`, the same no-subtitle/no-fill
logo settings, `--publish-category musia --publish --guided-monitor --wait`.
The publish call omits the context prompt because metadata is already reviewed;
this avoids triggering a fresh process pass.

- LazyEdit job: `411`.
- Remote AutoPublish job: `job-1789344096316-2`.
- Submitted at 08:01:34 HKT; remote job started at 08:01:36 HKT.
- ZIP: `DATA/ban-qu-chang-an-ace-changfeng-zh-lyrics-guitar-portrait-4k-20260914/publish/ban-qu-chang-an-ace-changfeng-zh-lyrics-guitar-portrait-4k-20260914.zip` under LazyEdit.
- ZIP video: `ban-qu-chang-an-ace-changfeng-zh-lyrics-guitar-portrait-4k-20260914_highlighted.mp4`.
- Packaged video SHA-256: `83333bcf72bb21d34c276d5d783d6e3d8efbe1a269e2e9763458aa7a15f9528b`, identical to the reviewed logo-only MP4. The historical `_highlighted` filename is a package convention, not an extra subtitle burn.
- All four platform login checks succeeded. The queue reports processing, not
  publication completion yet.

The logo-only publish master was also copied to Nutstore as
`ban-qu-chang-an-ace-changfeng-zh-lyrics-guitar-portrait-4k-20260914_logo.mp4`.

## Publication Status

| Platform | Status | Evidence |
| --- | --- | --- |
| Douyin | Published, management verified | Submission receipt/navigation accepted; management list matched `半曲长安长风Musia原创AI歌曲`; AutoPublish reported success. |
| Shipinhao | Published, management verified | Management list matched this song's listener-facing description; AutoPublish reported success. |
| Instagram | Published, caption verified | https://www.instagram.com/lazyingart/reel/DdPz5i2uI3D/; saved caption matched and latest profile post confirmed. |
| YouTube | Published, success dialog verified | https://www.youtube.com/shorts/tyPIcdYQhdU; checks completed with no issues; remote recovery job finished `done`. |

Shipinhao's account did not offer a selectable `Musia` collection. The optional
collection was skipped, not treated as a failed post.

The combined remote job finished `failed` at 08:09:29 because its final YouTube
step mistook an earlier completed upload's success overlay for an unrelated
draft. Read-only CDP inspection confirmed `Video published` and the earlier
video's share link. Closing only that success confirmation removed both the
overlay and old wizard; no draft, video or metadata was deleted or changed.
Only YouTube was resubmitted through LazyEdit using video 567 and `--no-process`.
The other three successful platforms were not retried.

YouTube-only recovery: LazyEdit job `412`, remote job
`job-1789345615816-3`, started at 08:26:55 HKT. The original ZIP was reused;
the upload completed and its title, description, thumbnail and Musia playlist
were entered. Platform checks completed with no issues. YouTube's success dialog
confirmed the new video URL and remote job `job-1789345615816-3` finished `done`
at 08:29:41 HKT. All four requested destinations are now confirmed published.

The final YouTube success confirmation was closed after collecting its link,
so a later publication will not inherit this completed-upload overlay. The
original combined job remains a historical partial-failure record; it was not
rewritten or retried for the three successful platforms.

Verified bug report for the publisher maintainer:
`/home/lachlan/DiskMech/Projects/lazyedit/bug-reports/2026-09-14-youtube-success-dialog-misidentified-as-draft.md`.

The logo publish master's 45-55-second audio comparison against the song also
had zero measured lag, with normalized waveform correlation 0.999542.
