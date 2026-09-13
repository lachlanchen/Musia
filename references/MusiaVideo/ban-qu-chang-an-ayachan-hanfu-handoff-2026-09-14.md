# 半曲长安: Aya Chan hanfu song handoff

Website update, September 14: the user requested upload after the audition.
The selected song is now public at https://fun.lazying.art/#ban-qu-chang-an .
Canonical website lyrics are in
`website/data/songs/ban-qu-chang-an/lyrics/zh-minimax-91302/` in Musia, including
the corrected contextual Japanese readings. The review caveats below remain;
website publication does not approve social posting or new video generation.

## Scope and status

New original Mandarin song for Aya's Chang'an, Yellow River, Lanzhou and danxia
journey. **Musia / 半曲长安 / The Melody I Left in Chang'an**.
MiniMax-Music3 seed 91302, 158.476 seconds, generic adult female AI singing.
Selected for private audition after two MiniMax candidates and two updated ACE
controls. No new MV generation, social publication or player recording is
authorized by this handoff alone.

## Exact inputs

Source story and reference images, unchanged:

`/home/lachlan/Nutstore Files/Share/ayachan/2026-09-13-luoshen-hanfu-mv/`

- `01-final/contact-sheet.jpg`: source-story overview.
- `03-reference-images/01-xian-wall-fan.png`
- `03-reference-images/02-huaqing-guqin.png`
- `03-reference-images/03-yellow-river-sword.png`
- `03-reference-images/04-danxia-bow.png`
- `03-reference-images/05-palace-umbrella.png`
- `03-reference-images/06-xian-horse.png`

This source project depicts an **adult woman in red hanfu and gold headpiece**.
Preserve the references; do not substitute the red-panda figurine from older Aya
projects or import their story/metadata. The landscapes are a cinematic journey,
not a documentary geography claim.

## Exact song outputs

Musia selected folder:

`/home/lachlan/ProjectsLFS/Musia/data/creative_projects/aya-chan-ban-qu-chang-an-minimax-20260913/selected/`

Nutstore handoff folder:

`/home/lachlan/Nutstore Files/Share/ayachan/2026-09-14-ban-qu-chang-an-song/`

Both contain:

- `ban-qu-chang-an-minimax.wav`: editing master, PCM-24 stereo, 44.1 kHz.
- `ban-qu-chang-an-minimax.mp3`: 320 kbps listening copy with cover and title.
- `cover-16x9.png`: new project-specific cover, no title text, 1672 x 941.
- `lyrics/lyrics.reviewed.txt`: reviewed Mandarin text, **not the raw ASR**.
- `lyrics/lyrics.reviewed.lrc`: approximate Chinese line timing.
- `lyrics/zh-Hans.json`, `lyrics/en.json`, `lyrics/ja.json`: Chinese vocal text
  with pinyin, English/Japanese translations, Japanese furigana.
- `manifest.json`: identity and explicit review/publication state.
- `README.md`: listening and reuse notes.

WAV SHA-256:
`ab11dafb5c11624588d9c60c6243f3611c2e8cc3460c7db9d8772b029603b4fe`.

Local stems and estimated harmony:

`/home/lachlan/ProjectsLFS/Musia/data/runs/ban-qu-chang-an-minimax-91302/`

Use `stems/` for bass, drums, vocals, other and instrumental. `analysis/beats.csv`
and `analysis/chords.csv` are **estimates, not a verified score**. Do not use the
initial `analysis/lyrics.txt` as final lyrics: its VAD pass missed material.

## Story and edit direction

A guqin melody is interrupted by departure. Aya leaves half of it with the
person waiting in Chang'an. On the road she protects others while hiding her own
fear. The Yellow River and red ridges give the longing physical distance. She
returns, sits beside the waiting person and finishes the melody. Her courage
serves that intimate promise, rather than replacing it with constant battle.

Approximate musical chapter anchors from the selected audio's ASR, not
frame-accurate edit decisions:

| Audio time | Musical material | Story opportunity |
| --- | --- | --- |
| 0:00–0:15 | Instrumental opening | Guqin detail, dusk on Chang'an walls; the unfinished promise. |
| 0:15–0:38 | First verse | Red sleeve, parting gesture, evening light, departure. |
| 0:38–0:51 | Pre-chorus | Hoofbeats recede; a quiet glance back to the city. |
| 0:52–1:12 | First chorus | Yellow River, crossing, home held in memory. |
| 1:12–1:27 | Instrumental transition | Breathing room; travel and changing light. |
| 1:27–1:40 | Second verse | Lanzhou night, danxia; protect fellow travelers. |
| 1:41–1:55 | Bridge | Private fear and tears; the waiting window restores resolve. |
| 1:57–2:16 | Final chorus | Return through the gates; anticipation without rushed closure. |
| 2:23–2:29 | Sung ending | Reunited at the guqin; finish the interrupted melody. |
| 2:29–2:38.476 | Instrumental release | Hold the reunion and let the last sound decay. |

The existing source MV is about **48.7 s**, not 2:38. Do not speed the song up
or stretch the old video mechanically to fit. After listening approval, either
build a full song-first MV or explicitly select a self-contained musical excerpt
with natural entry and exit. No cut has already been rendered.

If new footage is later requested, use song-locked timing and replace the video
generator's music with this WAV. Keep story foley/dialogue on separate tracks;
do not bury the singing. No paid Xiaoyunque submission without its normal visible
preflight and user-approved cost.

## Review gate before recording/publication

1. Listen to the complete WAV. Automatic MOSS/APEX review is not human approval.
2. Resolve **城南 versus 城门**, around 44.3–50.6 s. Input and MOSS favor 城南;
   Whisper favors 城门. Current text conservatively keeps 城南.
3. Verify line/word cues against audible attacks and held endings. They are
   ASR-derived, not forced-aligned; English/Japanese token timing is approximate
   translation highlighting. Do not treat it as exact lip-sync data.
4. All 28 intended lines, including the final two, are represented in the reviewed
   package. Unsupported intro composer-credit hallucinations were excluded.
5. Instrumental gaps are player state, not lyric rows.
6. Check the applicable MiniMax Community License and distribution requirements
   before commercial release or exposing a public generator. No blanket licensing
   clearance is implied here.

The WAV passes signal-health checks (-14.9 LUFS, -2.1 dBFS true peak, no clipped
or non-finite samples). APEX musicality/naturalness are about 2.74/2.55 out of 5,
similar to the ACE controls. Selection favors fuller pacing and a clean export,
not a claimed measured victory over ACE.

## Story-only metadata draft

**半曲长安 | The Melody I Left in Chang'an | Musia**

半首琴声留在长安，一半随她越过千山。黄河的夜、丹霞的风，都通向同一个约定：
平安归来，坐在你身旁，把那年未尽的半曲，轻轻弹完。

Keep debugging conversations out of public descriptions. Supply required
AI-generation/attribution disclosures separately and truthfully.

## Reproduction

Installation, version pins, generation commands and audit methodology:
`/home/lachlan/ProjectsLFS/Musia/references/minimax-music3-setup-and-ayachan-2026-09-13.md`.

Reviewed source-to-ASR mapping:
`/home/lachlan/ProjectsLFS/Musia/ideas-and-inspirations/ban-qu-chang-an/review-minimax-91302.json`.

This handoff is mirrored in LALACHAN at
`references/MusiaVideo/ban-qu-chang-an-ayachan-hanfu-handoff-2026-09-14.md`.
