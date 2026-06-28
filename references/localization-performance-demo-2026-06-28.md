# Localization Performance Demo - 2026-06-28

This note records the local Musai performance-demo run. The generated audio, model outputs, and downloaded fixtures are kept under ignored `data/` paths and are not committed to GitHub.

## Dedicated Command

```bash
MUSAI_LYRIC_PROVIDER=deepseek \
DEEPSEEK_MODEL=deepseek-reasoner \
scripts/run_localization_performance_pipeline.sh \
  --output-dir data/runs/localization-performance-20260628-deepseek
```

OpenAI GPT-5.5-compatible path was also checked:

```bash
scripts/run_localization_performance_pipeline.sh \
  --provider openai \
  --model gpt-5.5 \
  --output-dir data/runs/localization-performance-20260628-openai55-retry \
  --skip-asr-check
```

`gpt-5.5` rejected non-default temperature on the first attempt, so the script now retries without `temperature`. The retry completed and wrote a valid lyric package.

## DeepSeek Result

- Report: `data/runs/localization-performance-20260628-deepseek/REPORT.md`
- Provider result: `{"status": "ok", "model": "deepseek-reasoner"}`
- English input fixture: `data/open_songs/danny-boy-1917/original.ogg`
- English analysis run: `data/runs/test-danny-en-60/`
- Chinese target lyrics: `data/runs/localization-performance-20260628-deepseek/en-to-zh-danny/target_lyrics_zh.txt`
- Chinese target text: `呼唤回荡千山万谷盛夏已去百花凋落爱人别离我等待在此守候永不弃`
- SoulX target metadata: `data/runs/localization-performance-20260628-deepseek/en-to-zh-danny/soulx_target_metadata_zh.json`
- Existing experimental vocal: `data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_localized_vocal_zh-CN_first_verse.wav`
- Existing experimental mix: `data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_final_mix_zh-CN_first_verse.wav`
- Quality gate: `experimental_not_production_ready`

ASR check for the existing experimental render:

```text
Vocal: 明日在你回省省花園光的闪闪 日月玫瑰掉落我只等你乖
Mix: 暂逸归生生怀怨怨的很善 日月玫瑰掉落我只等你乖
```

This confirms the render has audible Chinese-like singing, but not production-level intelligibility.

## OpenAI GPT-5.5 Result

- Report: `data/runs/localization-performance-20260628-openai55-retry/REPORT.md`
- Provider result: `{"status": "ok", "model": "gpt-5.5", "retry": "without_temperature"}`
- Chinese target text: `长歌呼唤越过山谷群峰夏日已远玫瑰飘落你独自离去我仍默默在等候`
- English Mo Li Hua target lines:

```text
Sweet jasmine, white and fair
Fragrant blossom in the air
Let me pick you, soft and true
Give this flower, dear, to you
```

## Listening Showcase Added

After the first performance script pass, three fresher SoulX renders were produced with the original Danny Boy first-verse instrumental and a cleaner bundled Mandarin prompt voice:

```text
data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_simple30_clean_prompt_score_mix.mp3
data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_deepseek_clean_prompt_score_mix.mp3
data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_simple30_clean_prompt_melody_mix.mp3
```

The local listening page is:

```text
data/runs/musai-listening-showcase-20260628/index.html
```

The best current listening pick is:

```text
data/runs/danny-boy-zh-localization/localization/zh-CN/soulx_simple30_clean_prompt_score_mix.mp3
```

It is 29.31 seconds and uses the extracted first-verse instrumental. The vocal is clearly audible, but it still fails production intelligibility: faster-whisper recovered only partial Mandarin from the target phrase. This is an improvement over the near-inaudible earlier mix, but it is still an experiment.

## Artifacts Checked

The English and Chinese/instrumental fixture runs include:

```text
stems/bass.wav
stems/drums.wav
stems/vocals.wav
stems/other.wav
stems/instrumental.wav
stems/human_sound.wav
analysis/lyrics.*
analysis/beats.*
analysis/chords.*
manifest.json
REPORT.md
```

The SoulX backend itself passes bundled Mandarin and English demo sanity checks:

```text
Mandarin ASR: 像我这样懦弱的人 凡事都要留几分
English ASR: Who says you're not pretty? Who says you're not beautiful? Who says...
```

## Current Quality Boundary

The dedicated script is useful for reproducible package generation, provider comparison, and honest quality reporting. It does not yet produce a perfect full-song translated vocal. The blocker is still the strict same-song singing layer: phrase/note alignment and target-language phoneme timing need to be corrected before accepting a production render.
