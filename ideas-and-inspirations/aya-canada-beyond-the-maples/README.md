# 楓の向こうで · Beyond the Maples

Written 2026-10-06 for the request: Aya-chan travels in Canada, and the narrator
misses her. Japanese-only song, not the usual mixed-language default because
the user specifically requested Japanese. Status: **six complete renders,
seed 100604 selected, lyric audit complete, website and learning catalog published**.

Listen: https://fun.lazying.art/#aya-canada-beyond-the-maples

See [production and full phrase audit](../../references/aya-canada-beyond-the-maples-production-2026-10-06.md)
and [source-bound reviewed lyrics](reviewed-lyrics.json). The input below is the
generation reference, not the authoritative publishing transcript. The owner
approved the song on 2026-10-06 and then requested the standard portrait video
and video/music publication. Automated checks and human approval are recorded
separately.

## Story and lyric choices

The narrator receives a happy photograph at night while Aya has daylight. A
half-written "Are you cold?" becomes "Enjoy yourself." Missing her appears in
an ordinary action: taking out two coffee cups while making coffee for one.
The chorus allows two feelings to coexist: "I miss you" and "Don't hurry home."
The welcome at the end is a promise, not a demand that she abandon her trip.

Maple leaves and the time-zone contrast are creative scene choices, not a
claim about Aya's actual itinerary, city or travel dates. No invented personal
biography, exact destination, or previous song's story is imported.

The title reads **かえでのむこうで**. Public artist remains Musia. The Japanese
native text is both the intended lyric and the initial model-facing lyric.
Do not convert it wholesale to romaji or kana: the previous Hikari Ame
kana-heavy trial was not better. Keep **あや** in kana to protect the name's
reading. Other readings to check after synthesis: 楓 かえで, 葉 は,
深い ふかい, 朝 あさ, 食卓 しょくたく, 時差ぼけ じさぼけ,
愛しさ いとしさ. This guide belongs outside the sung lyric.

The repeated **会いたいな** is the melodic anchor. Japanese vowel echoes and
natural phrase endings matter more than forced English-style end rhyme.
The second chorus changes only the final two lines to develop longing into
welcome. Lines should remain connected across their line breaks, not rendered
as independent clips. Leave space after the hook, before the bridge, and for
the final held vowel. Do not squeeze this complete lyric into 60-90 seconds.

## Proposed musical treatment

- Initial target: about 156 seconds, 92 BPM, 4/4, G major.
- Warm natural female Japanese vocal; no real performer imitation.
- Intimate guitar/piano verses, a rising chorus with live drums and strings,
  a quieter bridge, and an unhurried resolved outro.
- Key/BPM/duration are model directions, not measured facts about an audio file.
- Start with the proven ACE XL Turbo 8-step non-thinking path and six seeds.
  Melody, vocal tenderness, whole-song coherence and replay value drive selection.
- Preserve the full lyric first. If delivery rushes, extend duration or shorten
  the weaker verse before adding restrictive prompt instructions.

Inputs: [lyrics](lyrics.ja.txt), [compact ACE caption](ace-caption.txt).
The broader model check is in
[the October research note](../../references/ace-and-music-tool-update-2026-10-06.md).

## Reproducible preparation

Run from the Musia root. The dry run writes configuration only and uses no GPU:

```bash
PYTHONNOUSERSITE=1 conda run --no-capture-output -n musia \
  python scripts/run_ace_candidate_sweep.py \
  --lyrics ideas-and-inspirations/aya-canada-beyond-the-maples/lyrics.ja.txt \
  --caption ideas-and-inspirations/aya-canada-beyond-the-maples/ace-caption.txt \
  --output-dir data/creative_projects/aya-canada-beyond-the-maples-20261006/sweep-v2 \
  --language ja --duration 156 --bpm 92 --key "G major" \
  --seeds 100601 100602 100603 100604 100605 100606 --dry-run
```

For an actual generation, first check host RAM, GPU use, project processes,
tmux sessions and GUI ports. Run only one Musia generation at a time. Repeat
the command without `--dry-run`, selecting an available GPU using
`CUDA_VISIBLE_DEVICES`. The runner uses ACE's existing verified `.venv`; do not
install ACE dependencies over the general `musia` environment.

Changing the vocal language, caption, lyric, seed set or other recorded inputs
requires a new sweep directory. The language flag is `ja`, not `jp`.
The earlier `sweep/` was a dry run before the final pre-chorus wording polish;
`sweep-v2/` is the completed six-candidate generation. `sweep/` remains a dry run.

## Gates before any publication

1. Screen every candidate for silence, clipping, broken transitions and cut tails.
2. Listen through finalists, not only the hook; retain the strongest full song.
3. Separate vocals and transcribe in Japanese with large-v3. Cross-check with
   independent transcription, the input and listening. Examine no-VAD gaps,
   repeats and the complete outro. Do not mistake ASR guesses for sung facts.
4. Account for every planned phrase. Retain source wording for sound-close
   errors; record real omissions, additions and changed phrase structure.
5. Build the actual Japanese vocal's JA/EN/ZH lyric set, Japanese furigana,
   Chinese pinyin, real word/phrase anchors and actual-audio chords/beats.
   No invented timings or instrumental rows in lyric tracks.
6. Generate this song's own 16:9 cover: Canadian autumn, distance, warmth and
   a small human-scale focal point within a vast landscape/megastructure.
7. Only after selecting and auditing audio: publish audio in MusiaSongs, then
   the Fun manifest/catalog/lyric data. Run strict audits and playback checks.
   The user subsequently requested generation and website publication. No
   social post or recording was made as part of that request.
