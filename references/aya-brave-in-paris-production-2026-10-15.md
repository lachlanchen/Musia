# Brave in Paris

Japanese title: **パリへ、ひとつの勇気**. English: **Brave in Paris**.
Chinese display title: **小小勇气，走向巴黎**. Artist: Musia.

## Intent

A happy Japanese song for Aya-chan's Paris journey: the Louvre, Versailles,
the Arc de Triomphe and the opera. The person at home misses her, but encourages
her to explore instead of rushing back. A photograph, unfamiliar words, a
windblown skirt and dinner for one make the feeling concrete. The refrain's
small courage becomes wings. This is an original song with a generated female
voice, not a real singer's cloned voice.

Source packet: `ideas-and-inspirations/aya-brave-in-paris/`. The Japanese vocal
will have English and Chinese translations of its actual sung lines, not
separate translated vocal performances.

## Generation

The existing successful ACE full-song route is retained, as used for Beyond
the Maples and Home on the Breeze. No new synthesis backend, model upgrade,
voice conversion, or strict melody-transfer route is introduced.

- ACE source: `ca1e85fe9430179831e6bc6be790c332190a3866`.
- Model: `acestep-v15-xl-turbo`.
- Checkpoint: `d4a0b288b83ebb7e25a8c0b32c573c22e134e8ee`.
- Eight steps, guidance 1, native Japanese, no planning-LM lyric/caption rewrite.
- 118 BPM, G major, 4/4: directions to the model, not a certified score.
- First sweep: 174 seconds, seeds 101501-101506.
- Roomier sweep: 188 seconds, seeds 101511-101514, same lyrics and caption.
- Project: `data/creative_projects/aya-brave-in-paris-20261015/`.

The first batch's 101506 leads its comparative APEX aesthetic scores but skips
the intimate bridge and alters the late chorus. Candidates 101502 and 101503
retain more narrative; both received vocal separation and additional large-v3
checks. 101503 also received independent MOSS Japanese transcription. The
first verse has compression/omission evidence, so four roomier candidates were
generated before selecting a public preview.

APEX is a comparative screening signal, not a human audition, popularity
forecast, or proof of beauty. Speech VAD frequently misses singing; full-mix
VAD-only reports from this run are not reliable lyric inventories. Do not
publish recognizer hallucinations such as generic closing credits in the
instrumental tail. Keep the raw evidence and compare independent passes.

## Shared Workstation

Generation and GPU analysis run serially on GPU 1. GPU 0's active LocalVideoGen
job and existing GPU 1 services are preserved. The loaded kernel driver is
595.84 while default userspace libraries are 595.99.02. Existing verified
595.84 libraries are reused read-only through child-process environment
variables; there is no global driver replacement, reboot, service stop or
library-link edit.

MOSS gained an optional `--max-gpu-memory-gib` weight-placement budget for a
shared GPU. The default remains unchanged. This run uses 15 GiB plus CPU
offload to preserve space for other services and inference tensors. This is
not a hard process-memory guarantee. An initial argument-placement mistake
failed before inference; it was corrected and the actual rerun succeeded.

## Cover

A fresh built-in image generation: a small red-panda traveller in a coral dress
and sky-blue scarf, camera and satchel, confidently crossing the Louvre
courtyard toward luminous monumental glass architecture. Warm sunlight and
expansive blue sky express joy and courage. No text, logos, old cover reuse or
unrelated Canadian/station imagery. Saved as `cover-16x9.png` in this project.

## Reusable Publication

`prepare_reviewed_japanese_fun_item.py` now accepts `releaseStage: preview`.
It keeps the item unlisted with a Preview category and makes text-track
provenance consistent. Published remains the backward-compatible default;
unknown stages are rejected before filesystem writes. This is a listening
preview, not a Legacy item or a private access-controlled page.

Raw audio, models and private work files stay out of Musia Git. The selected
versioned MP3 belongs in MusiaSongs. The website, reviewed lyric decisions,
translations, pronunciation metadata and production notes belong in Musia.
Record the exact selection, audit decisions and verified deployment below
before reporting completion. No recording or social/music-platform submission
is part of this request.

## Selection and Audit

Selected **101513**, 188 seconds, 48 kHz stereo. WAV SHA-256:
`d4c630b04c325fad57e151ed8b50dc1d86ff943b181093c90aad8be10ed7179c`.
The roomier batch improves the comparative musicality/coherence screen and
101513 restores the full opening verse. 101511 scores slightly higher on some
APEX dimensions but compresses the first verse and repeats the opera/outro;
101512 blurs the Versailles transition. Selection balances the narrative and
screening rather than treating a small score difference as decisive.

The selected WAV and 320 kbps MP3 pass signal-health checks: approximately
-12.1 LUFS, -0.9 dBTP, no clipped or non-finite samples, and a quiet final
100 ms. Human listening approval remains pending: this is an Unlisted Preview,
not a claim of a perfect master or a completed human audition.

Evidence in `review/101513/`: full-mix no-VAD large-v3 windows, isolated-vocal
large-v3 no-VAD windows including a focused 129-141s check, and independent
MOSS-Music-8B-Instruct transcription. The separate pipeline VAD result is
retained at `data/runs/aya-paris-ja-101513/analysis/lyrics.json`. Neither
independent transcription prompt contained the intended lyrics.

`build_review.py` records every chosen word range and every replacement. Its
flattened evidence preserves raw windows and hashes. The committed
`reviewed-lyrics.json` binds all 37 output rows to the selected WAV hash and
the evidence-file hashes. All 36 source lines are represented in order, with
the final repeated phrase added as row 37.

| Source lines | Decision |
| --- | --- |
| 1, 9 | Restore ルーヴル / ヴェルサイユ spelling from sound-close ルーブル / ベルサイユ. |
| 2-8 | All present in this render, including the words/learning and cobblestone lines that compressed in earlier candidates. Keep native orthography. |
| 10 | Keep the source's short connecting が using the full-mix phrase; stem recognition swallows the particle. |
| 11, 27 | Keep あや and パリ, not isolated recognizer guesses Ah Yeah, 終わり, 針 or マリ. The name/location are source-close; not a promise of perfect diction. |
| 12 | Keep 勇気 and 羽 over 雪 / 羽根 spelling guesses. |
| 13-18 | Present; restore 急がないで over the nonsensical 言うがないで. |
| 19 | Keep contextual 凱旋門の下 over 海鮮物知った / 海岸物した. The sung landmark is slurred, so pronunciation is not certified native. |
| 20-26 | Present; preserve the complete opera, dinner and unsent-message bridge. Companion translations follow these actual lines, not an unrelated poem or old song. |
| 28 | Full/stem and the focused window show a courage repetition. Publish 小さな勇気が勇気が羽になる, normalizing the weak connecting particle rather than deleting the repetition. MOSS collapses this repetition and is not used as sole authority. |
| 29-34 | Present. The stretched/echoed final yo in 手を振るよ remains within its positive ASR span, not a fabricated new sentence. |
| 35-36 | Complete souvenir/story ending; use full-mix start for おみやげ to avoid a stem window stretching it over the previous line. |
| Extra | 聞かせてね repeats at 175.18-178.28s. Full/stem and MOSS support it; add translations and timing. |

No instrumental placeholder rows, generic ASR closing credits, or unsupported
opening words are added. First lexical vocal is around 15.2s. Japanese word
anchors are ASR-based; subdivision within recognizer spans and translation
highlighting are approximate. An ambiguous nonlexical transition sound is
not presented as a new English lyric.

Reading audit: 君=きみ, 石畳=いしだたみ, 勇気=ゆうき, 羽=はね,
凱旋門=がいせんもん, 座=ざ, 灯り=あかり, 内緒=ないしょ. Chinese
contextual overrides include 照片片=pian4, 得/地=de5, 璃=li5 and 识=shi5.

## Musical Data

The selected audio has its own bass, drums, vocals, other and accompaniment
stems. Instrumental analysis estimates **117.454 BPM**, 350 beat events and
187 chord spans. These are analysis-grade, not a verified score. pYIN on the
isolated vocal provides an Atlas melody guide. The key stays `Unverified`;
numbered scale degrees are withheld instead of pretending the target G major
was musically verified.

## Rebuild

```bash
conda run -n musia python ideas-and-inspirations/aya-brave-in-paris/build_review.py
conda run -n musia python scripts/prepare_reviewed_japanese_fun_item.py \
  ideas-and-inspirations/aya-brave-in-paris/release.json
node bin/musia.js atlas-build --media-id aya-brave-in-paris
conda run -n musia python scripts/curate_fun_catalog.py --apply
node bin/musia.js fun-audit --media-id aya-brave-in-paris --strict
npm run website:validate
```

Selected WAV/MP3 and corrected TXT/LRC/JSON:
`data/creative_projects/aya-brave-in-paris-20261015/selected/`.
Canonical active lyrics:
`website/data/songs/aya-brave-in-paris/lyrics/ja-vocal/ja.json`.
The model-input lyric remains a reference, never a publishing substitute.

Public MP3 SHA-256:
`9849c10f7e1e98b40fa2ac30072e384fa823a20a0d6a59fa4cd16e99a913fd57`.
Audio commit: `681c40da6bc17edfeac7e0c80ea862f7817cb83e` in MusiaSongs.

Preview: https://fun.lazying.art/?preview=1#aya-brave-in-paris

Atlas: https://fun.lazying.art/atlas/aya-brave-in-paris/

## Deployment Verification

MusiaSongs Pages run `38745785929` succeeded. The public audio returns HTTP 206
for byte-range requests with cross-origin access enabled. Its full downloaded
SHA-256 matches the selected MP3 above.

The local website test passed on desktop (1440 x 1000) and mobile (390 x 844):
playback, loaded cover, ruby, active words, moving chords, no horizontal
overflow, and no JavaScript errors. Checkpoints at 17.35, 75.26, 122.49 and
177.64 seconds select lines 1, 13, 25 and 37 respectively. Screenshots and
machine-readable results are in the project's `review/website/` directory.
These checks verify rendering and alignment-data selection, not human musical
approval or phoneme-perfect forced alignment.

Release uses a clean worktree based on current remote main so unrelated local
creator/backend work, old lyric edits and README changes are not published.
The catalog map explicitly records this Japanese-titled work as a Preview.
Website commit: `8ceda98fc814dacb4fb90507c632e90d3586b0f3`. Pages run
`38747085479` succeeded. Live desktop/mobile browser checks also passed at all
four checkpoints. The deployed catalog, manifest, all three lyric tracks,
study data, cover and Atlas entry returned HTTP 200 and matched the committed
files byte-for-byte. Live screenshots were visually reviewed; the bilingual
title fits, and the desktop lyric panel shows the correct three languages.

Verification includes 21 reviewed-lyric/release tests, eight catalog-curation
tests, a no-drift curation check, strict item audit, website protocol validation
and a clean patch check. The public MP3 supports seeking and has the verified
content hash above. Automated playback is not a substitute for the owner's
listening decision, so Preview status remains unchanged.

All generation/analysis jobs and temporary test browser/server processes for
this release have finished. No dedicated GUI was left running. No native app
build, video recording, or social/music-platform submission is included.
