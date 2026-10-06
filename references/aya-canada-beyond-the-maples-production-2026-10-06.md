# Beyond the Maples: Japanese Song Production

## Release

- Title: **楓の向こうで · Beyond the Maples**. Chinese display title: 枫叶彼端.
- Artist: Musia. One Japanese vocal, with English and Chinese meaning tracks.
- Story: Aya travels in autumnal Canada. The person missing her at home puts out two coffee cups by habit, but wants her to enjoy the journey without rushing back.
- Public player: https://fun.lazying.art/#aya-canada-beyond-the-maples
- Atlas: https://fun.lazying.art/atlas/aya-canada-beyond-the-maples/
- Public audio: https://lazyingart.github.io/MusiaSongs/audio/aya-canada-beyond-the-maples-ja-seed100604-20261006.mp3
- Local selected master: `data/creative_projects/aya-canada-beyond-the-maples-20261006/selected/aya-canada-beyond-the-maples-ja.wav` and `.mp3`.
- Corrected publishing lyrics: `website/data/songs/aya-canada-beyond-the-maples/lyrics/ja-vocal/ja.json`.
- Corrected text/LRC: `data/creative_projects/aya-canada-beyond-the-maples-20261006/selected/lyrics/`.
- No recording or external social/music-platform publication was requested for this release.

## Production Choice

The proven ACE full-song route remains unchanged. Upstream/model update research is in `ace-and-music-tool-update-2026-10-06.md`. No unverified upgrade or strict melody-transfer pipeline was introduced.

Parameters: native Japanese, 156 seconds, 92 BPM production target, G-major production target, XL Turbo, eight steps, no language-model rewrite, six seeds `100601` through `100606`. The compact positive caption describes a warm, bittersweet J-pop ballad rather than a long list of prohibitions. Native text retains Japanese context; romaji/pinyin is not used for this song.

Selection: **100604**, after signal-health checks, APEX screening, and deeper vocal-stem checks of 100604 and 100606. All six were complete audio files. 100604 led this batch's APEX clarity, naturalness, musicality, coherence and memorability scores; these are comparative model estimates, not proof of a masterpiece or human approval.

- ACE code: `ca1e85fe9430179831e6bc6be790c332190a3866`.
- XL Turbo checkpoint: `d4a0b288b83ebb7e25a8c0b32c573c22e134e8ee`.
- Selected WAV SHA-256: `c2fc9a35a255d3dbe9ac1e069879f5d17aa30d9e4abb491210c87e9b3fdecd44`.
- Duration/sample format: 156 seconds, 48 kHz stereo.
- WAV and 320-kbps MP3 measured approximately -12.7 LUFS and -0.8 dBTP, with no clipping/nonfinite samples and a quiet ending.
- Human listening approval: **not yet provided**. Do not represent automated screening as a human audition.

## Why the First ASR Was Insufficient

Full-mix VAD screening sometimes returned only the opening or generic closing speech. Separating vocals recovered nearly the entire song. Do not equate low full-mix ASR recovery with failed singing.

Evidence for the selected audio:

1. `data/runs/aya-canada-ja-100604/analysis/lyrics.json`: large-v3 on Demucs vocals with VAD.
2. `.../review/100604/correction/selected-large-v3-no-vad.json`: full-mix large-v3 without VAD.
3. `.../review/100604/correction/vocal-stem-large-v3-no-vad.json`: stem large-v3 without VAD.
4. `.../review/100604/moss-lyrics.txt`: independent MOSS-Music-8B-Instruct Japanese transcription, without the intended lyric in its prompt.
5. `.../review/100604/focused-asr.json`: no-VAD stem windows 25-38, 49-57, 78-95, and 128-152 seconds.

Here `...` is `data/creative_projects/aya-canada-beyond-the-maples-20261006`.
The independent MOSS music critique is retained as subjective evidence only. Its section times conflict with ASR and its speculative clipping/phase explanations are not measured facts. Signal-health measurements are the authority for peak/clipping checks.

## Complete Reference-Line Audit

Rows refer to the non-heading, nonempty lines in `ideas-and-inspirations/aya-canada-beyond-the-maples/lyrics.ja.txt`. Public IDs are shared across JA/EN/ZH. The committed `reviewed-lyrics.json` binds every published line to exact ASR word ranges and the selected audio hash.

| Reference row | Public line | Decision |
| --- | --- | --- |
| 1 カナダから届く写真 | l01 | Keep; MOSS's 彼方 loses context, while large-v3 supports カナダ. |
| 2 赤い葉越しに笑う君 | l02 | Keep sound-close source 葉; reject 歯/歯茎 recognizer guesses. |
| 3 こちらはもう深い夜 | l03 | Keep. |
| 4 そちらはまだ青い朝 | l04 | Keep 朝; stem VAD, focused ASR and MOSS support it. |
| 5 「寒くない？」と打ちかけて | none | Omitted by render: all passes skip it and focused 25-38s provides no support. Do not invent it. |
| 6 「楽しんでね」に変えてみる | l05 | Keep 変えて over 帰って; full/focused ASR and context agree. |
| 7 遠い街が君の目に | l06 | Keep. |
| 8 どんな色で映るだろう | l07 | Keep. |
| 9 うれしそうなその顔に | l08 | Orthographic 嬉しそう only. |
| 10 さみしいなんて言えなくて | l09 | Orthographic 寂しい; ruby remains さみしい. |
| 11 会いたいな 会いたいな | l10 | Keep both hooks; VAD merged them, no-VAD/focused/MOSS recover both. |
| 12 楓が風に揺れるころ | l11 | Use 街: multiple independent passes hear machi, not kaede. |
| 13 同じ空のどこかで | l12 | Keep. |
| 14 君も笑っていてほしい | l13 | Orthographic 欲しい only. |
| 15 帰り道 急がないで | l14 | Keep. |
| 16 まだ知らない景色を見て | l15 | Keep. |
| 17 さみしさはここに置いて | l16 | Orthographic 寂しさ; ruby さみしさ. |
| 18 おみやげは君の話 | l17 | Keep one line. Reject isolated VAD-only 0.62s duplicate at 72.32s. |
| 19 ひとりぶんのコーヒーに | l18 | Orthographic 一人分. |
| 20 ふたつのカップ出してしまう | l19 | 二つのカップ出してまう; independent ASR/MOSS support a sung contraction without the second shi. |
| 21 君のいない食卓で | l20 | Keep. |
| 22 また写真をひらいてる | l21 | 写真を開いてる; missing また is not restored without sound support. |
| 23 帰ってきたその夜は | l22 | Keep. |
| 24 時差ぼけのままでいい | l23 | Keep standard spelling; ぼっけ is an ASR spelling artifact. |
| 25 話し疲れて眠るまで | l24 | Keep; full-mix no-VAD recovers 話し. |
| 26 君の旅を聞かせてよ | l25 | Keep. |
| 27 会いたいな 会いたいな | l26 | Keep both hooks; do not add the VAD-only ああ mis-segmentation. |
| 28 楓が風に揺れるころ | l27 | Same real 街 change as l11. |
| 29 同じ空のどこかで | l28 | Keep. |
| 30 君も笑っていてほしい | l29 | Orthographic 欲しい only. |
| 31 帰り道 急がないで | l30 | Keep. |
| 32 まだ知らない景色を見て | l31 | Keep. |
| 33 さみしさも愛しさも | l32 | Orthographic 寂しさ; preserve intended readings. |
| 34 「おかえり」の声に変えて | l33 | Orthographic お帰り only. |
| 35 あや 次に会えたら | l34-l35 | Actual 次に会えたら repeats; no-VAD recovers the second entrance around 142s. Do not force a clear あや where evidence supports an open-vowel ad-lib. |
| 36 何も言わず抱きしめたい | l36 | Keep through 149.32s. |

An initial nonlexical open-vowel ad-lib before the first outro phrase is ambiguous (MOSS only); no unsupported lexical word is added. No-VAD and focused windows confirm the two lexical repetitions. The second ああ has full/stem no-VAD support. Instrumental intro/break/tail spans are gaps, not lyric rows.

## Timing, Readings and Translation

36 lines in each of three tracks, identical IDs and phrase bounds. Japanese word anchors come from the selected render; morpheme subdivision within ASR spans is explicitly approximate. EN/ZH translations follow the actual Japanese, not discarded draft lines; their highlighting is only line-relative, not exact cross-language word alignment.

Manual reading audit overrides 君 to きみ, 葉越し to は・ごし, 朝 to あさ, 頃 to ころ, 寂しい/寂しさ to さみしい/さみしさ, 食卓 to しょくたく, and 時差 to じさ. Never trust a dictionary's context-free 君=くん for song lyrics. Japanese has furigana, Chinese has contextual pinyin; there is no Chinese pinyin on Japanese kanji.

Chords and beats come from the selected 100604 analysis, not 100606. Measured tempo estimate: 92.285 BPM. The manifest retains `key: Unverified`, estimated 4/4, and analysis-grade chords. Atlas uses the exact asset ID `aya-canada-ja-100604` to select the correct analysis run. There is no claimed human-verified lead sheet or invented number-note melody.

## Cover

A fresh 16:9 generated illustration: a traveller in a russet coat beneath red/gold Canadian maples, teal water, snow mountains, and a vast glass-and-timber canopy. Warm morning light and a small human focal point express distance and affectionate waiting. No text, logos or reused older-song image.

- Retained generation: `data/creative_projects/aya-canada-beyond-the-maples-20261006/cover-16x9.png`.
- Public copy: `website/assets/covers/aya-canada-beyond-the-maples-16x9.png`.

## Reproduction

Use `musia` conda for post-production. The sweep dispatches inference through the existing ACE environment; do not clone model installations.

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_ace_candidate_sweep.py \
  --lyrics ideas-and-inspirations/aya-canada-beyond-the-maples/lyrics.ja.txt \
  --caption ideas-and-inspirations/aya-canada-beyond-the-maples/ace-caption.txt \
  --output-dir data/creative_projects/aya-canada-beyond-the-maples-20261006/sweep-v2 \
  --language ja --duration 156 --bpm 92 --key 'G major' \
  --seeds 100601 100602 100603 100604 100605 100606

PYTHONNOUSERSITE=1 conda run -n musia python scripts/prepare_aya_canada_fun_item.py
PYTHONNOUSERSITE=1 conda run -n musia python scripts/curate_fun_catalog.py --apply
node bin/musia.js atlas-build --media-id aya-canada-beyond-the-maples
npm run website:validate
node bin/musia.js fun-audit --media-id aya-canada-beyond-the-maples --strict
```

Reusable helpers added: `review_ace_candidate_audio.py` (screening only), `transcribe_song_windows.py` (unconditioned focused ASR), and `export_reviewed_japanese_lyrics.py` (source/hash-bound reviewed lyrics). `test_export_reviewed_japanese_lyrics.py` checks anchors, source replacements, rejected unreviewed changes and ruby overrides. The browser regression helper now selects the actual vocal language rather than hardcoding Mandarin.

The preparation script does not push. Publish the scoped MusiaSongs audio/index commit first, verify audio range playback, then the scoped Musia website/script/reference commit and Pages deployment. Do not include unrelated worktree lyrics. Retain the catalog's existing default song and all other catalog decisions.

## Verified Publication

- MusiaSongs commit `2fa6a2b`; Pages run `37446111996` succeeded. MP3 range GET returned 206 with CORS enabled and the expected 6,242,033-byte file length.
- Musia website/song commit `a99ec25`; Pages run `37446340660` succeeded.
- Public MP3 SHA-256: `623ececbae9ee3f19b4dd9ce9c93e4413459e1890f6ca618df5c9510d7326692`.
- Live manifest, Atlas study and all three lyric JSONs were fetched and compared equal to the reviewed local payloads.
- Local and live Playwright checks passed at 1440x1000 and 390x844: ready audio, duration, actual playback clock, seeking, four lyric checkpoints, active words, moving/visible current chord, loaded cover, ruby and no horizontal overflow or page errors. Evidence is under the project's `review/website/`; browsers and local test server closed afterward.
- Six sweep tests, seven Japanese review-export tests, 32 learning API tests and nine web/core/guitar tests passed. Strict song audit, full website schema validation and whitespace checks passed.
- Learning catalog deployed from a clean `a99ec25` source snapshot, not the dirty workspace. The existing verified lucide vendor file and shared runtime cache were reused. This was a data/backend deployment, not an app-store build or submission.
- Native/web learning origin: `https://musia.lazying.art`. Transaction `20261006T175731-8c57a319c180`, release hash `8c57a319c1809c54ebc633a09564d0546879774824d0ae2d0d4d965434ea7353`. Public acceptance passed; song detail returns the Japanese asset and JA/EN/ZH tracks with 36 lines each. Private deployment receipts remain under `deploy/learning/.work/`.
- No generation jobs or new GUI/noVNC stacks remain. The pre-existing Musia learning service and other projects' runtimes were not stopped.
