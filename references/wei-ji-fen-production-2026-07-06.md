# 微积分 Production Note

Date: 2026-07-06

## Song

- Title: `微积分`
- Artist: `Musia`
- Route: ACE-Step 1.5 XL Turbo, hook-first Mandarin C-pop breakup ballad
- Selected seed: `760622`
- Selected project: `data/creative_projects/wei-ji-fen-20260706`
- Selected audio:
  - `data/creative_projects/wei-ji-fen-20260706/selected/wei-ji-fen-zh-ace-xl-turbo-seed760622.wav`
  - `data/creative_projects/wei-ji-fen-20260706/selected/wei-ji-fen-zh-ace-xl-turbo-seed760622.mp3`
- Analysis run: `data/runs/wei-ji-fen-zh-ace-seed760622-analysis`
- Public audio: `https://lazyingart.github.io/MusiaSongs/audio/wei-ji-fen-zh-Hans-ace-xl-turbo-seed760622-20260706.mp3`
- Website media id: `wei-ji-fen`

## Public Lyric Policy

The balanced and compact ACE sweeps had healthy audio levels but poor lyric
recovery beyond the opening. The selected hook-first render recovered a usable
song structure. Website lyrics are corrected against the selected render's
large-v3 ASR plus a medium/large-v3 no-VAD correction packet on the full mix
and separated vocal stem. Planned words are preserved only when they are
sound-close and more musical.

Important corrections:

- `微微琐事` is kept over ASR `微微松弛`.
- `我绕着你转` is kept over ASR `我绕着你穿`.
- `角度还不肯散` is kept over ASR `脚都还不肯散`.
- `傅立叶变换 / 拆开了思念` is kept over a garbled ASR bridge because the
  syllable shape is close and the math image is central.
- The opening `微微，微微` and later `不要分开` are restored because no-VAD
  ASR showed normal VAD had swallowed these soft/repeated hook phrases.
- Unsupported planned lines such as `微积分那么难` and `二重积分好奇怪` are
  omitted from the public active lyric track for this selected audio.

## Mixed EN/JP/ZH Attempt

The user also asked for a mixed English/Japanese/Chinese version. Three routes
were tested:

- native mixed EN/JP/ZH, ACE XL Turbo;
- English + pinyin + romaji full mixed performance, ACE XL Turbo;
- short mixed hook, ACE XL Turbo and ACE XL SFT.

All mixed routes failed lyric recovery. The best fragments were unrelated or
too weak, such as `we play, we play` or spoken-style English. The mixed lyrics
are kept locally under `data/creative_projects/wei-ji-fen-20260706/lyrics/`,
but no mixed audio is published to the public website yet because quality comes
first.

## Website Files

- `scripts/prepare_wei_ji_fen_fun_item.py`
- `website/data/songs/wei-ji-fen/manifest.json`
- `website/data/songs/wei-ji-fen/lyrics/zh-vocal/zh-Hans.json`
- `website/data/songs/wei-ji-fen/lyrics/zh-vocal/en.json`
- `website/data/songs/wei-ji-fen/lyrics/zh-vocal/ja.json`
- `website/assets/covers/wei-ji-fen-16x9.png`
- `website/data/catalog.json`

Validation:

```bash
node bin/musia.js fun-audit --media-id wei-ji-fen
node bin/musia.js fun-validate
```
