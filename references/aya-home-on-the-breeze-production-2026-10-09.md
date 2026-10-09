# Home on the Breeze

Japanese title: **ただいま、風のなか**. English: **Home on the Breeze**.
Chinese display title: **风中归来**. Artist: Musia.

## Intent and Route

A happy homecoming song for Aya returning from Canada to Japan: a maple leaf
in a notebook, a suitcase, taking off a down jacket, Chiba's cool breeze, and
the person waiting at the station. The cool weather is a creative premise,
not a weather report. This is a new song, not a replacement for Beyond the
Maples. The Japanese vocal has English and Chinese meaning tracks, not three
independently generated vocals.

Source: `ideas-and-inspirations/aya-home-on-the-breeze/lyrics.ja.txt` and
`ace-caption.txt`. Native Japanese input, 38 short lines, 320 nonspace lyric
characters. The hook uses everyday `ただいま / おかえり`. Preserve breathing
room and the sparse bridge instead of adding denser lyrical instructions.

The established ACE full-song route is unchanged:

- ACE code `ca1e85fe9430179831e6bc6be790c332190a3866`.
- Model `acestep-v15-xl-turbo`, checkpoint
  `d4a0b288b83ebb7e25a8c0b32c573c22e134e8ee`.
- Eight steps, guidance 1, native `ja`, no LLM lyric/caption rewrite.
- 116 BPM and G major are production targets, not verified analysis.
- First sweep: 164 seconds, seeds 100901-100906.
- Roomier sweep: 184 seconds, seeds 100911-100914, identical lyric/caption.
- Project: `data/creative_projects/aya-home-on-the-breeze-20261009/`.

Both sweeps retain request, config, generation logs, hash-bound candidate
manifests, signal-health reports and APEX results. APEX is comparative screening,
not a human audition or proof of musical quality. Do not claim a human listening
approval before the owner provides one.

## Audit Lessons

Full-mix speech VAD recovered almost no lyrics even where vocal separation plus
large-v3 recovered full sections. Do not treat that first pass as evidence of
an instrumental song. The 164-second finalists 100903 and 100906 compressed or
omitted several planned lines; the second sweep gives the same lyric more room.

Independent MOSS transcription needs the proven Japanese prompt on the vocal
stem. The generic timestamp-oriented prompt on the full mix looped on a
nonlexical opening syllable for 100903. That output is rejected as a failed
recognizer run, not accepted as the song's lyrics. Use:

```text
この音声で実際に歌われている日本語の歌詞を、順番と繰り返しを保って書き起こしてください。聞こえない語句を補わず、器楽部分は歌詞にしないでください。
```

Do not place intended lyrics in the independent recognition prompt. Compare
full-mix and stem no-VAD passes, reference lyrics and focused windows. Preserve
sound-close Japanese rather than nonsense ASR spellings. Explicitly account
for omissions, repeats, the opening, transitions and the ending. Instrumental
sections are timing gaps, never musical-note rows in lyric JSON.

## Reusable Packaging

`scripts/prepare_reviewed_japanese_fun_item.py` accepts a release JSON and uses
the existing source/hash-bound Japanese lyric exporter. It packages selected
WAV/MP3, copies versioned MP3 to MusiaSongs, rebuilds its audio index, exports
JA/EN/ZH tracks, adds the cover, selected-audio chords/beats and catalog entry.
It refuses replacement of differing versioned assets and does not push.

Reading checks include `君=きみ`, `千葉=ちば`, `涼しい=すずしい`, and contextual
`ひと眠り / 一言`. Never apply Chinese pinyin to Japanese kanji. Companion
translations follow the selected vocal's actual line structure; their token
highlighting is approximate and line-relative.

Cover: a newly generated 16:9 illustration of a joyful reunion in a vast,
sunlit coastal station. Coral dress, down coat over a suitcase, blue bay and
white glass-roof architecture. No text or older-song artwork reused.

## Selection and Lyric Coverage

Selected **100912**, 184 seconds, 48 kHz stereo, WAV SHA-256
`419df5ffd45640f0567f7212d3edb18f7e4f328c02e3b319ae21710dec016b40`.
The roomier pair has stronger comparative musicality/coherence than the first
batch; 100912 avoids 100911's malformed late-chorus repeat and retains the warm
final line. 100911 and the shorter candidates remain private alternatives.

Final MP3: approximately -12.3 LUFS, -0.8 dBTP, no clipped/nonfinite samples,
quiet final 100ms. Forty sung lyric rows in each track. Human listening
approval remains pending; model screening is not a human audition.

Evidence under `review/100912/` includes full-mix/stem large-v3 no-VAD,
`data/runs/aya-home-ja-100912/analysis/lyrics.json` (stem VAD),
`moss-vocal-ja.txt`, and focused windows covering 0-16, 14-35, 52-64, 78-87,
128-141, 144-154 and 160-184 seconds. `focused-flat.json` is a lossless
flattening of those window segments for the exporter; raw evidence is retained.
No intended lyric was supplied to either independent ASR prompt.

| Input | Planned line | Public ID | Decision |
| --- | --- | --- | --- |
| 1 | カナダの赤い葉を | l01 | Keep Canada and source 葉, not the homophone 羽 or stem-only あなた. |
| 2 | 手帳にはさんで | l02 | Keep hasande; サンデー is a phonetic recognizer guess. |
| 3 | ふくらむスーツケース | l03 | Keep; merge the zero-length long-vowel ASR subtoken without inventing time. |
| 4 | やっと閉めた朝 | l04 | Keep source 閉めた, a homophone of ASR 締めた. |
| 5 | あとひと眠りで | none | Omitted. Full/stem, MOSS and focused 14-35s do not recover it. |
| 6 | 君に会えるんだ | l05 | Kept; agreement across reference and selected-audio recognition. |
| 7 | 時計の針は違っても | l06 | Kept; agreement across reference and selected-audio recognition. |
| 8 | 帰りたい場所はひとつ | l07 | Kept; agreement across reference and selected-audio recognition. |
| 9 | 窓の向こうが明るんで | l08 | Kept; agreement across reference and selected-audio recognition. |
| 10 | 胸の奥まで晴れてゆく | l09 | Kept; agreement across reference and selected-audio recognition. |
| 11 | ただいま　ただいま | l10 | Kept; agreement across reference and selected-audio recognition. |
| 12 | ダウンを脱いで　風のなか | l11-l12 | Actually repeats ダウンを脱いで; publish both entrances. |
| 13 | 千葉の涼しい風が | l13 | Retain intended 千葉 for a near-sounding nasalized シンバ. Pronunciation is imperfect, not certified native. |
| 14 | ふわり　ほほをなでた | l14 | Kept; agreement across reference and selected-audio recognition. |
| 15 | おかえり　おかえり | l15 | Kept; agreement across reference and selected-audio recognition. |
| 16 | 聞きたかった　その声に | l16 | Kept; agreement across reference and selected-audio recognition. |
| 17 | 遠い空を越えて | l17 | Kept; agreement across reference and selected-audio recognition. |
| 18 | やっと笑って会えたね | l18 | Use focused 80.78s onset rather than stretching やっと across the preceding gap. |
| 19 | 改札抜けたら | l19 | Kept; agreement across reference and selected-audio recognition. |
| 20 | 大きく振る手 | l20 | Kept; agreement across reference and selected-audio recognition. |
| 21 | 名前を呼ぶ前に | l21 | Kept; agreement across reference and selected-audio recognition. |
| 22 | 笑顔がこぼれた | l22 | Kept; agreement across reference and selected-audio recognition. |
| 23 | ふたつ並んだ影が | l23 | Keep; missing in the shorter 100903 render but present in this one. |
| 24 | いつもの道をゆく | l24 | Kept; agreement across reference and selected-audio recognition. |
| 25 | おみやげ話は | l25 | Kept; agreement across reference and selected-audio recognition. |
| 26 | あとでいいかな | l26 | Keep かな, supported by the selected full/stem/MOSS passes. |
| 27 | もう少しこのまま | l27 | Keep complete もう少し, not the truncated wording in rejected 100911. |
| 28 | 君と歩きたい | l28 | Kept; agreement across reference and selected-audio recognition. |
| 29 | ただいま　ただいま | l29 | Kept; agreement across reference and selected-audio recognition. |
| 30 | ダウンを脱いで　風のなか | l30 | Restore sound-close ダウン; MOSS confirms the coat hook. |
| 31 | 千葉の涼しい風に | l31 | Same conservative Chiba decision as the first chorus; discard unconfirmed full-mix ああ split. |
| 32 | ふたり　深呼吸した | l32 | Kept; agreement across reference and selected-audio recognition. |
| 33 | おかえり　おかえり | l33 | Three actual おかえり, not the planned two. Full/stem and MOSS agree. |
| 34 | そのひとことで　うれしくて | l34 | Kept; agreement across reference and selected-audio recognition. |
| 35 | 遠くへ行ったぶんだけ | l35 | Keep 分=ぶん; do not show the dictionary reading ふん. |
| 36 | この街が好きになる | l36 | Kept; agreement across reference and selected-audio recognition. |
| 37 | ただいま　ああ　ただいま | l37-l39 | Three real ただいま entrances. Focused 160-184s resolves merged/missing full-song ASR. |
| 38 | 君のとなりが　あたたかい | l40 | Keep final warm line at 174.36-180.34s, not the stretched full-mix 163.46s onset. |

The opening contains ambiguous nonlexical vocalized sounds, not supported
lexical words. These are not fabricated into text. A possible held continuation
of 朝 was split as さあ by whole-song ASR; focused recognition and MOSS do not
support a separate lexical line. The outro's three real lexical hooks are
preserved, not confused with instrumental sound.

Reading audit fixes Japanese 君=きみ, 一言=ひとこと, 分=ぶん and 行く=ゆく.
Chinese contextual overrides correct 装得=de5, 挥着=zhe5 and 多待=dai1.
The exporter now accepts zero-length ASR subtokens only inside an explicit
reviewed merge with a positive enclosing span; it still rejects unreviewed
zero-duration words. Thirteen focused exporter/release-guard tests pass,
including mixed Latin/punctuation preservation in Chinese translations.

## Musical Data and Limits

Stems: `data/runs/aya-home-ja-100912/stems/` (vocals, drums, bass, other,
instrumental). Beat/chord data comes only from this selected audio. Tempo
estimate 117.454 BPM; 352 beat events and 225 chord spans. Public key remains
Unverified; meter, chords and beats are estimates, not certified notation.
pYIN on the isolated vocal adds F0 and Atlas note guides, explicitly marked
analysis-grade. Do not treat median token pitches as a transcribed lead sheet.
Atlas now withholds numbered scale degrees when the key is unknown, rather
than silently assuming C major. F0-derived note names remain available as
estimates. Two focused tests cover known keys and the unknown-key guard.

MOSS's free-form music critique is subjective. Its claimed 1:37-3:04 outro
conflicts with actual sung lines through 180.34s, so its section times are
rejected. Its speculative noise/clipping claims are not signal measurements.
Do not use that paragraph as verified metadata or a substitute for listening.

## Rebuild and Publish

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/prepare_reviewed_japanese_fun_item.py ideas-and-inspirations/aya-home-on-the-breeze/release.json
PYTHONNOUSERSITE=1 conda run -n musia python scripts/curate_fun_catalog.py --apply
node bin/musia.js atlas-build --media-id aya-home-on-the-breeze
npm run website:validate
node bin/musia.js fun-audit --media-id aya-home-on-the-breeze --strict
```

Selected audio and corrected TXT/LRC/JSON:
`data/creative_projects/aya-home-on-the-breeze-20261009/selected/`.
The canonical publishing lyric is
`website/data/songs/aya-home-on-the-breeze/lyrics/ja-vocal/ja.json`,
never the draft. The builder does not upload or push.

Audio publication uses the existing `lazyingart` repository-owner login
scoped to that Git command; do not switch the
shared workstation's default GitHub account. No credentials are written into
this project.

## Release Verification

Audio publication is complete in MusiaSongs commit
`ad0770ce65d4997efbb8f7f0f99489a6d4f36d40`; Pages run `37936716948` succeeded.
The public audio returns HTTP 206 for range playback, CORS `*`, and its full
download matches SHA-256
`437b1a41dd5b9a836743a3f82719c44ecd044bf788f59646662ba2ea0f7cc70a`.

Local desktop (1440x1000) and mobile (390x844) browser checks passed with the
real public audio: playback, seeking, four timed lyric checkpoints, ruby,
word highlighting, moving chords, loaded cover, no horizontal overflow, and
no JavaScript errors. Screenshots were visually checked. Evidence is under
`review/website/` in the creative project. Full website schema validation,
strict item audit and JavaScript syntax checks pass. Timing remains ASR-based,
not a human-certified word alignment.

Website publication commit `54eed0ef730127c28823472cead4801cc9802b1c` deployed
successfully in Pages run `37938083335`. Live desktop and mobile playback tests
passed at 18.18, 70.38, 120.86 and 176.11 seconds, including the final sung line.
Live catalog, manifest, study data, all three lyric JSON files and cover match
the local reviewed files byte-for-byte. Evidence: `review/website/live-checks.json`
and `live-{desktop,mobile}.png` in the creative project.

Listen: https://fun.lazying.art/#aya-home-on-the-breeze

Atlas: https://fun.lazying.art/atlas/aya-home-on-the-breeze/

This request publishes the song and website only. No player video recording,
social-platform upload, music-platform submission or native-app release was
performed. Temporary browser checks closed their own browser instances; no
new GUI or development-server runtime is left running.

