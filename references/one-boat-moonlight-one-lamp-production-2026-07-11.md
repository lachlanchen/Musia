# 一船明月一灯影 · One Boat of Moonlight

Date: 2026-07-11

## Source

This song merges two farewell poems about a monk returning to Japan:

- 钱起《送僧归日本》
- 韦庄《送日本国僧敬龙归》

The public Chinese companion track uses only original poem anchors where the
selected vocal is sound-close. It does not use modern Chinese paraphrase.

## Selected Render

- Project: `data/creative_projects/one-boat-moonlight-one-lamp-20260711/`
- Selected WAV: `data/creative_projects/one-boat-moonlight-one-lamp-20260711/selected/one-boat-moonlight-one-lamp-ace-xl-turbo-seed780826.wav`
- Selected MP3: `data/creative_projects/one-boat-moonlight-one-lamp-20260711/selected/one-boat-moonlight-one-lamp-ace-xl-turbo-seed780826.mp3`
- Public audio: `../MusiaSongs/audio/one-boat-moonlight-one-lamp-ace-xl-turbo-seed780826-20260711.mp3`
- Analysis run: `data/runs/one-boat-moonlight-one-lamp-20260711-analysis/`
- Website item: `website/data/songs/one-boat-moonlight-one-lamp/manifest.json`
- URL: `https://fun.lazying.art/#one-boat-moonlight-one-lamp`

## Generation Route

The final selected route used ACE-Step 1.5 XL Turbo with a compact
mixed-language phonetic hook, following the successful `哭晁卿衡` style:

- English hook to establish the song's emotional entry.
- Mandarin pinyin for classical Chinese poem lines to reduce rare-character
  pronunciation failures.
- Short Japanese romaji phrases for the eastward-return image.
- Chinese source poems preserved in the prompt notes for semantic grounding.

Attempted routes before selection:

- Dense mixed pinyin route, seeds `791301` to `791304`: poor recovery and
  generic drift.
- Sparse hook route, seeds `791305` to `791308`: not enough poem material
  recovered.
- Native Chinese poem route, seeds `791309` to `791312`: recovered fragments
  such as `家在扶桑东更东` and `一船明月一帆`, but the overall vocal was less
  stable.
- Ku-style phonetic route, seeds `780824` to `780827`: selected seed `780826`
  for the best balance of melody, vocal smoothness, and lyric recovery.

## ASR And Lyric Correction

Evidence sources:

- `run_pipeline.py` small ASR on the selected full mix.
- Whisper large-v3 ASR on the full mix.
- Whisper large-v3 ASR on the separated vocal stem.
- Planned phonetic hook lyric and the original poem text.
- Manual listening policy: actual audible structure > close intended lyric >
  ASR guess > translation draft.

The render does not sing every planned line. Public lyrics include only
sound-supported sung lines. Instrumental and uncertain gaps are omitted from
song-level lyric JSON; the player can show non-lyric state from timing gaps.

Corrected active vocal lines:

| ID | Time | Active vocal |
| --- | --- | --- |
| l01 | 6.10-11.90 | When love shines across the sea |
| l02 | 13.88-16.95 | Shang guo sui yuan zhu |
| l03 | 17.00-20.08 | Lai tu ruo meng xing |
| l04 | 20.08-23.80 | Fu tian cang hai yuan |
| l05 | 23.80-26.56 | Fa zhou qing |
| l06 | 26.56-30.62 | Shui yue tong chan ji |
| l07 | 30.62-32.98 | Moon in the water |
| l08 | 33.66-36.86 | Yu long ting fan sheng |
| l09 | 36.86-40.46 | Haruka Haruka |
| l10 | 40.46-44.38 | Wei lian yi deng ying |
| l11 | 44.38-47.76 | Wan li yan zhong ming |
| l12 | 48.44-51.10 | Fu sang miao mang zhong |
| l13 | 51.10-54.96 | Higashi no higashi e |
| l14 | 68.46-71.02 | Haruka umi e |

Important correction decisions:

- ASR hallucinated `作词/作曲/编曲` in the early instrumental area. These were
  excluded.
- The long gap after `Higashi no higashi e` is not represented as a lyric row.
- The final soft phrase `Haruka umi e` is included because multiple ASR passes
  and listening support a tail at the end.
- The Chinese companion line for pinyin phrases restores original poem anchors
  only where sound-close and phrase length is compatible. After user review,
  `Fa zhou qing` is published as `法舟轻`, not `去世法舟轻`, because the
  selected vocal does not sing `去世`. Likewise `Fu sang miao mang zhong` is
  published as `扶桑渺茫中`, not `扶桑已在渺茫中`, because the selected vocal
  omits `已在`. Other sound-close anchors include `上国随缘住`, `来途若梦行`,
  `浮天沧海远`, `水月通禅寂`, `鱼龙听梵声`, `惟怜一灯影`, `万里眼中明`,
  `家在扶桑东更东`, and `一船明月一帆风`.

## Website Protocol Output

Generated with:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/prepare_one_boat_moonlight_one_lamp_fun_item.py
node bin/musia.js fun-validate
```

The script writes:

- `website/data/songs/one-boat-moonlight-one-lamp/manifest.json`
- `website/data/songs/one-boat-moonlight-one-lamp/lyrics/mixed-vocal/mul.json`
- `website/data/songs/one-boat-moonlight-one-lamp/lyrics/mixed-vocal/en.json`
- `website/data/songs/one-boat-moonlight-one-lamp/lyrics/mixed-vocal/ja.json`
- `website/data/songs/one-boat-moonlight-one-lamp/lyrics/mixed-vocal/zh-Hans.json`
- `website/assets/covers/one-boat-moonlight-one-lamp-16x9.png`
- `website/data/catalog.json`

The validator requires `manifest.timeline.lines`, not `manifest.timeline.lyrics`.

## Cover

The first procedural moonlit boat cover was replaced with a selected
image-generation cover candidate:

- Candidate: `website/assets/cover-candidates/one-boat-megastructure-cover-candidate-20260711.png`
- Live 16:9 cover: `website/assets/covers/one-boat-moonlight-one-lamp-16x9.png`

Prompt direction: moonlit ocean, tiny boat with a warm lamp, and an immense
graceful ring-gate/lighthouse-city megastructure rising from the water. This
matches the song's scale: one human lamp against the far sea and the return
toward Fusang.

## Reuse Note

For mixed classical-poem songs, use pinyin or romaji as private sound-control
when native characters fail, but publish the real active vocal after ASR and
listening correction. Restore original source lines only when phrase length,
sound, and meaning are close. Do not publish prompt-only lines that the selected
audio did not sing.
