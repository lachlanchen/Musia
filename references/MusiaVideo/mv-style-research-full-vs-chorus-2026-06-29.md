# Full Song MV And Chorus Cut Research

Date: 2026-06-29  
Scope: Musia-to-LALACHAN handoff style selection.

## Decision Model

Create two possible MV products from one Musia song:

- **Full-song MV**: uses the whole reviewed song and builds a complete visual story.
- **Chorus / climax MV**: uses only the strongest 副歌 or 高潮部分 as a compact social cut.

For `Aya Chan Hikari Ame`, make the full-song MV first because the selected track is about `68.04s` and the requested hope/rain/battle concept needs setup, attack, charge, and resolution. Make a chorus cut later as a trailer or social preview.

## Full-Song MV

Use when:

- the user says full length, total music, complete MV, or whole song;
- the song is 45s or longer;
- the story needs emotional change over time;
- character action, dialogue, and final payoff matter.

Recommended handoff files:

- `README.md`
- `STORY.md`
- `SEGMENTS.json`
- `XYQ_PROMPT_FULL_MV.md`
- `ASSET_LIST.md`
- `SOUND_MIX_NOTES.md`
- `MUSIA_LALACHAN_MV_HANDOFF.json`

The prompt should follow song sections: intro, verse, tension, chorus, bridge, final release, outro. Dialogue should be short and placed in musical gaps.

## Chorus / Climax MV

Use when:

- the user asks for 副歌, 高潮部分, hook, teaser, or short social cut;
- credits are limited;
- the full MV is not needed yet;
- the concept is one memorable action, dance, joke, or transformation.

The chorus cut should not summarize every beat of the full song. It should start strong, move on beat, and finish with one clean payoff.

## Audio Rule

The reviewed Musia audio is the master. If Xiaoyunque changes the song, use the generated video track but mux the Musia audio back in.

The LALACHAN repo has a reusable helper:

```bash
scripts/musia_mv_finalize.sh \
  --video GENERATED_VISUAL.mp4 \
  --audio data/creative_projects/SONG/final/selected.mp3 \
  --output FINAL_SONG_LOCKED.mp4
```

The portable LazySkills version is:

```bash
$LAZYSKILLS_ROOT/skills/musia-lalachan-mv-workflow/scripts/mux_musia_audio.sh \
  --video GENERATED_VISUAL.mp4 \
  --audio SELECTED_MUSIA_MASTER.mp3 \
  --output FINAL_SONG_LOCKED.mp4
```

## Publishing

For public release, use normal LazyEdit publish logic. The story/prompt can guide subtitle correction and metadata tone, but metadata must be concise and viewer-facing. Do not use the whole storyboard as the platform description.

