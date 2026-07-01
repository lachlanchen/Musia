# かぎろひと花 Production Note

Date: 2026-07-01

## Goal

Create a Japanese source-text song from selected `万葉集` and `古今和歌集`
waka lines. The user explicitly allowed reordering/repetition when it improves
rhythm, and asked Codex to choose between kana and normal Japanese.

## Decision

Use kana as the model-facing control layer when pronunciation and rhythm are the
main risk, but keep the normal source text as the public truth layer.

Reason:

- kana reduces rare-kanji pronunciation failures and strongly influences vocal
  rhythm;
- normal Japanese/kanji keeps semantic context, but ACE often garbles rare or
  classical readings;
- the final website lyric must match the actual audio, so public text is
  restored to original waka wording only where ASR/listening evidence is
  sound-close.

## Tested Routes

Project folder:

```text
data/creative_projects/kagirohi-to-hana-20260701
```

Tested ACE-Step 1.5 routes:

| Route | Result |
| --- | --- |
| XL SFT full kana | Mostly failed, ASR recovered credit/empty text. |
| XL SFT full normal Japanese | Mostly failed, ASR recovered credit/empty text. |
| XL Turbo short normal | Partial opening only. |
| XL Turbo short kana | Best recovery; selected seed `741214`. |
| XL Turbo compact normal hook | Failed or only weak opening recovery. |
| XL Turbo compact kana hook | Clearer opening, but less complete than selected short-kana render. |
| XL Turbo two-hook kana | Did not improve; mostly lost the Kokin hook. |

Selected audio:

```text
data/creative_projects/kagirohi-to-hana-20260701/selected/kagirohi-to-hana-ja-ace-20260701.wav
```

Public audio:

```text
../MusiaSongs/audio/kagirohi-to-hana-ja-ace-20260701.mp3
```

## Lyric Correction

Large-v3 ASR was run on both the selected full mix and the separated vocal
analysis. The public lyric includes only lines represented in the selected
audio:

```text
東の野に
かぎろひの立つ見えて
かへり見すれば
あかねさす
紫野行き
標野行き
君が袖振る
君待つと
吾が恋ひをれば
簾動かし
秋の風吹く
久方の
光のどけき
久方の
光のどけき
春の日に
しづ心なく
花の散るらむ
```

Planned lines that the render skipped are not published. This follows the
Musia rule:

```text
actual audible structure > close intended/source lyric > ASR guess > translation draft
```

## Website Artifacts

Fun item:

```text
website/data/songs/kagirohi-to-hana/manifest.json
website/data/songs/kagirohi-to-hana/lyrics/ja-vocal/ja.json
website/data/songs/kagirohi-to-hana/lyrics/ja-vocal/zh-Hans.json
website/data/songs/kagirohi-to-hana/lyrics/ja-vocal/en.json
website/assets/covers/kagirohi-to-hana-16x9.png
```

Analysis artifacts:

```text
data/runs/kagirohi-to-hana-20260701-selected-analysis/REPORT.md
data/runs/kagirohi-to-hana-20260701-selected-analysis/stems/
data/runs/kagirohi-to-hana-20260701-selected-analysis/analysis/chords.csv
data/runs/kagirohi-to-hana-20260701-selected-analysis/analysis/beats.csv
data/runs/kagirohi-to-hana-20260701-selected-analysis/analysis/lyrics.json
```

Reusable prep script:

```text
scripts/prepare_kagirohi_to_hana_fun_item.py
```

Validation:

```bash
npm run website:validate
PYTHONNOUSERSITE=1 conda run -n musia python scripts/audit_fun_media_item.py --media-id kagirohi-to-hana
node --check website/app.js
```

All passed on 2026-07-01.
