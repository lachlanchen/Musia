# LALACHAN Song-First Video Workflow

Preferred flow for musical short films:

```text
Musai song package
-> generate song audio
-> review song audio
-> write LALACHAN handoff
-> generate Xiaoyunque/Seedance video from the song
-> merge or replace final audio only after video approval
```

This is better than generating video first because the song controls:

- rhythm;
- phrase timing;
- emotional arc;
- chorus/high point;
- shot pacing;
- character movement.

## Musai Side

Create and render the song:

```bash
musai song init --title "My Character Song" --vocal-language ja --lyrics-file lyrics.txt
data/creative_projects/<song-id>/commands.sh generate
data/creative_projects/<song-id>/commands.sh review
```

After choosing the best candidate, create a final folder:

```text
data/creative_projects/<song-id>/final/
  selected.wav
  selected.mp3
```

Refresh the handoff:

```bash
musai song handoff \
  --project-dir data/creative_projects/<song-id> \
  --audio data/creative_projects/<song-id>/final/selected.mp3 \
  --cover data/creative_projects/<song-id>/assets/cover-16x9.png
```

## LALACHAN Side

Use:

```text
LALACHAN_SONG_TO_VIDEO_HANDOFF.md
```

The Xiaoyunque prompt should:

- upload the character reference images first;
- upload or attach the selected song audio as timing/emotion reference;
- ask for a musical short film that follows the song structure;
- avoid subtitles, local file names, and path text in the video;
- keep the character consistent with the uploaded references;
- time camera movement and scene changes to phrase changes.

## When To Merge Audio

If the video tool preserves the uploaded song exactly, no merge is needed.

If the video tool changes or compresses the soundtrack, use the generated video as the picture track and merge the reviewed Musai audio back in:

```bash
ffmpeg -y -i video.mp4 -i selected.wav \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 192k \
  final-mv.mp4
```

## Safety And Rights

- Use original lyrics and original generated audio unless rights are confirmed.
- Do not clone or imply a real singer voice without consent.
- Character references are visual continuity references, not voice-clone consent.
- For public releases, keep `SELECTED_VERSION.md`, QA, and handoff files with the project.
