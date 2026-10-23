# A Beginner, Even Now

Japanese: **せんせいも一年生**. Chinese: **老师也是一年级**.
Artist: Musia. Japanese female vocal with English and Mandarin translations.

## Song

Aya receives an offer for a specially appointed assistant-professor role in
Chiba. She rehearses introducing herself, finds her stomach answering first,
and discovers that teaching brings more questions rather than fewer. The
heart of the song is an extra chair beside an unsolved problem and a pudding
on the way home. It celebrates curiosity, companionship and self-kindness.
It is a fictional musical portrait, not an institutional announcement.

The approved 48-line lyric remains in
`ideas-and-inspirations/sensei-mo-ichinensei/lyrics.ja.txt`.
Public text uses native Japanese. The model-facing second sweep changes only
特任助教 to とくにんじょきょう and 付箋 to ふせん. No romaji, complete kana
rewrite, real-singer imitation or voice conversion is used.

## Generation

Reuse the successful Brave in Paris ACE full-song route rather than replacing
it with a new backend. The current toolchain check retains this as the proven
production baseline; optional newer tools are not presumed better.

- ACE source: `ca1e85fe9430179831e6bc6be790c332190a3866`.
- Checkpoint: `acestep-v15-xl-turbo`, revision
  `d4a0b288b83ebb7e25a8c0b32c573c22e134e8ee`.
- Official decoder; weight SHA-256
  `da17edb604c40deaf09e9b24974e590d1ca83a374070e5d0884cfa4bed9a99b0`.
- Eight steps, guidance 1, native Japanese; no planning-LM lyric rewrite.
- 112 BPM, G major, 4/4 are production directions, not a verified score.
- First sweep: 228 seconds, seeds 102301-102306.
- Second sweep: 240 seconds, seeds 102311-102314, same caption and the two
  targeted kana substitutions above.

All ten candidates received audio-health checks, comparative APEX screening,
large-v3 ASR and no-VAD windowed transcription. APEX scores are not a human
audition or a promise of quality. Speech VAD misses substantial singing in
these files; its sparse output is not an adequate lyric inventory. Generic
closing credits and social-media text in some recognizer windows are retained
as raw evidence, not treated as sung lyrics.

Selected candidate **102314**, 240 seconds, 48 kHz stereo. Its WAV SHA-256:
`bc465e163692027af4162649bee867e42620cfe6cdcc233abe5ce7d635dab4c5`.
It retains the everyday second verse and the shared-curiosity bridge more
fully than several alternatives. Selection balances narrative coverage and
comparative screening; a tiny APEX difference is not decisive.

Signal checks: approximately -12.7 LUFS, -0.9 dBTP, no clipped/non-finite
samples, a quiet final 100 ms and 2.5 seconds of trailing near-silence.
Human listening approval is not claimed.

## Analysis and Review

Project: `data/creative_projects/sensei-mo-ichinensei-20261023/`.
Selected-audio analysis: `data/runs/sensei-ja-102314/`.
Demucs provides vocals, bass, drums, other and accompaniment stems.
Instrumental analysis estimates 112.347 BPM, 445 beat events and 289 chord
spans. Harmony and meter remain analysis-grade; the key is unverified.
The pYIN vocal guide contains 20,672 frames (67.1% voiced). Atlas keeps Western
pitch estimates but does not invent a verified tonic for numbered scale degrees.

Review evidence is kept in the project's `review/102314/` directory. Full-mix
and isolated-vocal large-v3 windows are unprompted and use no speech VAD.
Independent focused MOSS transcription supplies another hypothesis, not a new source
of authoritative lyrics. The selected audio, original intent and agreement
between passes govern close-word restoration; real omissions or repetitions
must not be hidden by copying the planned lyric.

`build_review.py` records exact ASR word selections and reasoned replacements.
The exported JSON is hash-bound to the selected audio and source evidence.
Japanese within-word timing and translated-word highlighting are approximate;
the line clocks remain anchored to the selected performance. Pure instrumental
sections are gaps, never musical-note rows in lyric data.

### Editorial Decisions

The final export has 51 rows. `lyric-coverage.json` accounts for all 48 input
lines, including changed and absent lines rather than asserting verbatim singing.

- Restore source-close 内定, 四度目, 特任助教, 四文字, 付箋, あや and 背筋
  instead of nearby recognizer homophones. Diction is not certified native.
- Keep the second verse and the entire two-chair/pudding bridge. Do not lose
  their faster phrases at overlapping ASR window boundaries.
- The repeated hook and short 明日もまだ未完成 return in the ending. Do not
  replace that repeat with the unsung planned 世界はまだ未完成.
- The planned 笑える今日に会えたから is not established by any pass. Full mix,
  stem and focused large-v3 give 私の今日なんか; focused MOSS gives 私のような.
  Publish the majority-reading fragment わたしの今日なんか with a fragment
  translation, not a fabricated full planned sentence. This is an unresolved
  diction uncertainty at roughly 148-151s, retained for listener review.
- At 171.84-176.30s, full/stem recognition supports 今日の涙も忘れたら.
  MOSS instead suggests 昨日の涙も忘れるから. Retain the full/stem consensus
  and translate it independently; do not silently collapse it into an earlier
  chorus line. This remains another local uncertainty.
- The tail keeps all four Aya-sensei / posture / breeze / first-hello lines.
  Isolated opening credits, social-network labels and a full-mix-only late
  "oh yeah" guess are not supported as lexical song lines by the vocal checks.
- Furigana is checked after tokenization, including the standalone 四=よん,
  rather than assuming a compound override covers the tokenizer's split.

The MOSS excerpt check completed successfully after the incomplete whole-song
attempt. Its output is evidence for the final chorus only, not the entire song.
The 140-195s crop, absolute offset and SHA-256 are bound into the review packet.

## Artwork

Fresh generated artwork, 1672 by 941 pixels: a small red-panda teacher in a
coral cardigan, notebook and colorful sticky notes, beneath monumental
sunlit timber-and-glass library terraces. The expansive architecture and
blue sky express curiosity and a new beginning. No text, logo, graduation
claim or reused travel-song cover.

## Rebuild and Publish

```bash
conda run -n musia python ideas-and-inspirations/sensei-mo-ichinensei/build_review.py
conda run -n musia python scripts/prepare_reviewed_japanese_fun_item.py \
  ideas-and-inspirations/sensei-mo-ichinensei/release.json
node bin/musia.js atlas-build --media-id sensei-mo-ichinensei
conda run -n musia python scripts/curate_fun_catalog.py --apply
node bin/musia.js fun-audit --media-id sensei-mo-ichinensei --strict
npm run website:validate
```

Audio belongs in MusiaSongs; models, generated WAVs, stems and raw analysis
stay outside Musia Git. Publish audio first, then verify browser playback,
translated lyrics, ruby and moving word/chord highlights before deploying Fun.
The native catalog uses the additive procedure in
`docs/learning-catalog-addition.md`, preserving all existing song DTOs. Its
new exact read-only detail route is admitted separately; authentication,
creator handlers and sibling sites are unchanged. The initial song deployment
did not include recording, social posting, Shipinhao Music or store submission.
The subsequent requested recording and publication are documented in the
[LazyEdit publication record](../handoff/lazyedit/sensei-mo-ichinensei/README.md).

Public song: https://fun.lazying.art/#sensei-mo-ichinensei

## Release Verification

Published on October 23, 2026. MusiaSongs audio commit:
`36fd885ff4f66cf7a58b5563d1d99eab489e2de6`; Fun item commit:
`6068cd18ec9ded5e7e65f010de45450aa4d4bc8a`. The Fun Pages deployment
completed successfully (run `39930624963`). The public MP3 checksum matches
the selected export:
`ec86bbc57f06ad6b3031dcb5d9fb6f6ec283bfb8d9485e529c0a12d8937de789`.

Live desktop and mobile browser checks loaded the public audio, advanced
playback, checked four lyric positions through the ending, and verified moving
word/chord highlights, Japanese ruby and no horizontal overflow or script
errors. Screenshots and checks remain under the project's `review/website/`.

The native catalog's public detail response equals the reviewed packet and its
33-item library contains the new song exactly once. All 32 prior native DTOs
remain structurally identical. No store binary is required for the catalog
addition. Native-device playback was not separately rerun for this release.

An initial loopback-only deployment acceptance missed the public ingress's
literal route allowlist. A scoped addition of this song's exact GET/HEAD detail
path resolved the public 404. The reusable controller now refuses an unadmitted
route before activation and requires verified public HTTPS detail and library
responses before marking publication successful. Tests cover missing routes,
ambiguous matchers, altered methods, failed public acceptance and rollback.
No wildcard route, sibling configuration, login or billing setting was changed.

## Shared Workstation

GPU work runs serially on GPU 1. Existing peer services are preserved. The
known userspace/kernel NVIDIA version mismatch is handled only with existing
verified matching libraries in child-process environments; no global driver
installation, reboot or peer service stop. MOSS uses a 13 GiB GPU weight budget
with CPU offload. This is a placement budget, not a hard process-memory cap.
No new GUI/noVNC stack is required for headless browser checks.

The full-length MOSS attempt returned no text within a 30-minute budget under
CPU offload. Its exact owned process was terminated with SIGTERM (exit 143),
and GPU 1 returned to its pre-job 7209 MiB peer usage. This is a bounded,
incomplete attempt, not an independent full-song pass. A separate 55-second
final-chorus crop (140-195s) uses a 500-token cap and a ten-minute timeout.
Focused large-v3 checks can now use `transcribe_song_windows.py --device cpu
--cpu-threads 4` with int8, preserving the CUDA/float16 default. They run without
contending for the remaining GPU memory. The complete full-mix and vocal-stem
no-VAD large-v3 checks remain the full-song evidence.
