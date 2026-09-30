# 半曲长安 · 长风: Shipinhao Music

Date: September 30, 2026. Scope: pure music on Shipinhao Music only. Do not
republish the already published recording video or enable other destinations.

## Selected Performance

- Public music title: `半曲长安 · 长风`.
- Artist: Musia; author/lyricist/composer/producer credit: Musia 慕莎.
- Audio: the approved ACE Changfeng rendition, seed 914203, 138 seconds.
- Website: https://fun.lazying.art/#ban-qu-chang-an-ace-changfeng
- Selected local MP3:
  `data/creative_projects/ban-qu-chang-an-ace-changfeng-20260914/selected/ban-qu-chang-an-ace-changfeng.mp3`
- Corrected lyrics:
  `website/data/songs/ban-qu-chang-an-ace-changfeng/lyrics/zh-ace-914203/zh-Hans.json`
- Language: Mandarin Chinese. Genre: Pop, described as guofeng pop-rock.

The less-preferred MiniMax version was not selected. The historical video
publication note confirms this ACE performance was approved and published as
video, not pure music. LazyEdit had no matching music record among its 42
existing records. Live music-management preflight showed no matching title in
the visible rows; that observation is not an exhaustive inventory of all pages.

## Lyric and Audio Checks

The strict Musia media audit passes. The live website's Mandarin JSON exactly
matches the local corrected file. Packaging preserved all 28 lines, including
the second chorus's shorter `等我回来`; no draft lyrics, pinyin, translation
rows, instrumental placeholders or LRC timestamps were used.

The package's audio bytes match the approved/public MP3 SHA-256:
`e7ba2ef0db9d4674b9e5c0acbe3fa2fd08f5d9384d3d3778d9e27f8aac1174c5`.
FFprobe: MP3, 320 kb/s, 48 kHz stereo, 138.024 seconds including MP3 padding.
The already reviewed performance was not regenerated and no new ASR accuracy
claim is made: this submission reuses its documented multi-source correction.

## Artwork and Public Copy

Square artwork:
`data/publish_assets/ban-qu-chang-an-ace-changfeng-music-20260930/cover-square.png`.

Generated with the built-in image tool, referencing the song's approved 16:9
artwork. Prompt: recompose as a high-resolution square cover, preserving the
adult crimson-hanfu traveler carrying a guqin, immense Chang'an walls, luminous
Yellow River, red Danxia mountains and golden sunrise. Heroic yet tender,
journey and homecoming; cyan sky, warm light, no text, logos, frames or collage.
Both the generated cover and LazyEdit's 1440 x 1440 package JPG were inspected.
One curated square cover was supplied, not nine duplicate images or screenshots
of the player. The website cover is unchanged.

Public story:

> 半首琴声留在长安，一半随她越过千山。沿着黄河、丹霞与城墙的风，把远行唱得明亮，也把牵挂藏进归途。愿每个走向远方的人，都有一盏灯等你回家。

The description identifies AI-assisted music/vocals without exposing model
names, internal instructions or conversation history. `source-fields.json`
adds only source/provenance fields: the package CLI's source URL is otherwise
stored in the database but not passed to the platform metadata. Marking this
song as previously published is necessary because it is already on Fun and in
social videos. It must not claim to be a first-ever publication.

## Package and Submission

Built using LazyEdit's existing `scripts/lazyedit_music_package.py`, without
`--post`, then inspected before submission. Originality-source note: `SOURCE.md`.
The package uses plain corrected lyrics and its own proof ZIP. Only the music
target is enabled; the automatically created YouTube art-track file is not
being published to YouTube.

- LazyEdit music record: **43**.
- Package folder:
  `/home/lachlan/DiskMech/Projects/lazyedit/DATA/music_publish/ban-qu-chang-an-changfeng-zh-music-20260930/`
- ZIP: `ban-qu-chang-an-changfeng-zh-music-20260930.zip` in that folder.
- AutoPublish job: **job-1790769411340-17**.
- Queued: September 30, 2026, 19:56:51 HKT.
- Target: `shipinhao_music` only.

The verified existing ZIP was posted with LazyEdit's
`post_music_package_to_autopublish`, without rebuilding, through `/publish`.
The durable database row was updated with the remote job ID. An earlier job
was already processing; this one was queued without restarting the service or
touching the other job.

## Confirmed Result

The job started at **20:06:22 HKT** and finished **done at 20:07:31 HKT**.
The platform's music-management snapshot at that same time contains the exact
title in both tabs:

- Album: `半曲长安 · 长风`, one track, September 30, 2026, **已上架**.
- Song: `半曲长安 · 长风`, matching album, September 30, 2026, **审核中**.

This is a confirmed music submission, not a claim that song review has passed.
LazyEdit record 43 is `submitted`, remote status `done`, with no `published_at`
timestamp or invented public share URL. Management URL:
https://channels.weixin.qq.com/platform/post/music

Publisher form readback confirms the title, all 28 corrected plain lyric lines,
Mandarin, full-length original version, Musia singer credit, author credits,
album title/description, square cover, agreement checkbox, and previously
published selection. The site's selected genre was 流行 / 城市流行. The proof
ZIP finished uploading; it was not left at 0% or removed. The independent
音乐人说 / 歌曲故事 field was absent, so the public description was provided in
the album introduction instead. Do not claim a nonexistent field was filled.

Local `submission.json`, `queue.json`, `management-after-submit.json` and
`publisher.log` evidence lives beside the square cover. The queue monitor
exited after the terminal result. No new browser stack, rerendered recording,
cross-platform video post, or duplicate music submission was created.
Reconcile this exact record and platform row before any retry.
