# Take Care of Yourself same-score localization

Date: 2026-06-28

## Goal

Create same-melody localized vocals for `Take Care of Yourself` from the Japanese guide render, then publish the usable website package with per-vocal trilingual lyric JSON.

## Result

Public website media id:

```text
take-care-of-yourself-same-score
```

Website assets:

```text
website/assets/audio/take-care-of-yourself-en.mp3
website/assets/audio/take-care-of-yourself-zh-Hans.mp3
website/assets/audio/take-care-of-yourself-yue-Hant.mp3
website/assets/covers/take-care-of-yourself-16x9.png
website/data/songs/take-care-of-yourself-same-score/manifest.json
website/data/songs/take-care-of-yourself-same-score/lyrics/
```

Local working outputs:

```text
data/creative_projects/take-care-of-yourself-20260628/localized_soulx/
```

## Method

The cleanest available local path was:

```text
Japanese guide render
→ extract melody/F0 and phrase timing
→ build one shared score plan
→ synthesize English, Mandarin, and Cantonese with SoulX-Singer
→ mix each dry vocal against the same instrumental stem
→ publish each vocal with its own lyricSetId and trilingual translation tracks
```

SoulX-Singer's installed local phone set supports English, Mandarin, and Cantonese phones. It does not include Japanese phones, so Japanese target synthesis is deferred until a Japanese-capable singing backend or phone set is installed.

## Reusable Script

The score/metadata builder is:

```text
scripts/create_soulx_same_score_localizations.py
```

Example:

```bash
PYTHONNOUSERSITE=1 conda run -n musai python scripts/create_soulx_same_score_localizations.py \
  --f0-csv data/runs/take-care-of-yourself-20260628-20260628-185010-analysis/analysis/melody_f0.csv \
  --output-dir data/creative_projects/take-care-of-yourself-20260628/localized_soulx
```

It writes SoulX target metadata for:

```text
soulx_target_en.json
soulx_target_zh-Hans.json
soulx_target_yue-Hant.json
```

## Render Commands

English:

```bash
CONTROL=score DEVICE=cuda PITCH_SHIFT=0 bash scripts/run_soulx_svs.sh \
  third_party/SoulX-Singer/example/audio/en_prompt.mp3 \
  third_party/SoulX-Singer/example/audio/en_prompt.json \
  data/creative_projects/take-care-of-yourself-20260628/localized_soulx/soulx_target_en.json \
  data/creative_projects/take-care-of-yourself-20260628/localized_soulx/render_en
```

Mandarin:

```bash
CONTROL=score DEVICE=cuda PITCH_SHIFT=0 bash scripts/run_soulx_svs.sh \
  third_party/SoulX-Singer/example/audio/zh_prompt.mp3 \
  third_party/SoulX-Singer/example/audio/zh_prompt.json \
  data/creative_projects/take-care-of-yourself-20260628/localized_soulx/soulx_target_zh-Hans.json \
  data/creative_projects/take-care-of-yourself-20260628/localized_soulx/render_zh-Hans
```

Cantonese:

```bash
CONTROL=score DEVICE=cuda PITCH_SHIFT=0 bash scripts/run_soulx_svs.sh \
  third_party/SoulX-Singer/example/audio/yue_target.mp3 \
  third_party/SoulX-Singer/example/audio/yue_target.json \
  data/creative_projects/take-care-of-yourself-20260628/localized_soulx/soulx_target_yue-Hant.json \
  data/creative_projects/take-care-of-yourself-20260628/localized_soulx/render_yue-Hant
```

Mix:

```bash
VOCAL_GAIN=1.25 INSTRUMENTAL_GAIN=0.78 scripts/mix_vocal_with_instrumental.sh \
  <dry-vocal.wav> \
  data/runs/take-care-of-yourself-20260628-20260628-185010-analysis/stems/instrumental.wav \
  <final-mix.wav>
```

## QA

All final mixes are 58 seconds and use the same instrumental stem.

Level check:

```text
English:  RMS 0.11327, peak 0.67758
Mandarin: RMS 0.12686, peak 0.79666
Cantonese: RMS 0.11398, peak 0.73987
```

ASR/listening gate:

```text
English dry/mix: pass
Mandarin dry: pass; Mandarin mix: review because backing lowers ASR recovery
Cantonese dry/mix: pass
```

Website verification:

```bash
npm run website:validate
python3 -m py_compile scripts/create_soulx_same_score_localizations.py
```

Browser smoke test:

```text
http://127.0.0.1:8781/#take-care-of-yourself-same-score
```

Verified:

```text
Title: Take Care of Yourself
Artist: by Musia
Vocal options: English, 中文, 廣東話
Audio swaps:
  assets/audio/take-care-of-yourself-en.mp3
  assets/audio/take-care-of-yourself-zh-Hans.mp3
  assets/audio/take-care-of-yourself-yue-Hant.mp3
```

## Notes

This is the first successful same-score SoulX localization package for this song. It is better aligned than independent full-song generations because all three vocals follow one phrase/F0 plan. It is still not a final commercial master: Mandarin pronunciation and mix intelligibility should be improved with a stronger singing backend or a second SoulX correction pass.
