# 半曲长安

Original Mandarin song for Aya Chan's hanfu journey. Working English title:
*The Melody I Left in Chang'an*. Created 2026-09-13 for the LALACHAN collaboration.

## Story

Aya leaves a half-finished guqin melody with someone in Chang'an. She rides out
past the old city walls, follows the Yellow River through Lanzhou and red danxia
mountains, and helps her companions return safely. At the end, she completes the
melody beside the person who waited. Affection and quiet courage carry the song;
it is not a list of destinations or a tourism advertisement.

This is a fictional cinematic journey, not a precise historical or geographical
record. It follows the existing LALACHAN hanfu story, not an unrelated earlier
Aya song. The lyric need not name the character to work as her first-person song.

## Production

- Requested backend: MiniMax Music 3, current official open weights, BF16.
- Female adult Mandarin lead; lyrical guofeng pop with cinematic breadth.
- Native Chinese characters, not global pinyin replacement or speech recitation.
- The recurring chorus carries the main melody; leave room for breaths and held
  vowels rather than squeezing all words into a short fixed duration.
- The production caption and sung lyric are separate files. MiniMax section tags
  occupy their own lines, because text after a leading tag can be discarded.
- A 240-second generation ceiling allows the model to finish naturally; it is
  not a claim that the finished song lasts exactly four minutes.

## Lyric Review Before Generation

The main rhyme family is `an/ang`: 长安、千山、想念、眼、身旁、弹完. Several
lines deliberately use a near rhyme or cadence rather than replacing natural
language to force an exact match. The two choruses repeat the full hook. The
four-line bridge creates a brief vulnerable moment before the resolution.

Pronunciation references: 长安 `chang2 an1`, 兰州 `lan2 zhou1`, 丹霞 `dan1 xia2`,
衣裳 `yi1 shang`, 别在 `bie2 zai4`, 半曲 `ban4 qu3`, 弹完 `tan2 wan2`.
These are review notes, not text to sing. Prefer source characters unless an
actual render demonstrates a pronunciation error requiring a minimal patch.

## Release Gate

Input lyrics are intentions, not a transcript. After generation, inspect the
complete output, use large-model transcription, compare source and recognition
phrase by phrase, include repetitions and the complete tail, and preserve source
wording when the sound is close. Do not invent timings or claim subjective
listening review from ASR alone. Keep the initial MiniMax candidates private
until quality and the model's public/commercial-use conditions are reviewed.

Source materials remain in Nutstore; the delivery note will contain the exact
operator paths. Do not copy private character/source images into git.
