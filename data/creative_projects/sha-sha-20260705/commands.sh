#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/lachlan/ProjectsLFS/Musia"
PROJECT_DIR="$ROOT_DIR/data/creative_projects/sha-sha-20260705"
CONDA_ENV="${MUSIA_CONDA_ENV:-musia}"
LANGUAGE="zh"
LYRICS="$PROJECT_DIR/lyrics/zh-ace.txt"
cd "$ROOT_DIR"

latest_audio() { find "$PROJECT_DIR/ace_outputs" -type f -name "*.wav" 2>/dev/null | sort | tail -n 1; }

case "${1:-help}" in
  generate-turbo)
    cd third_party/ACE-Step-1.5
    .venv/bin/python cli.py -c "$PROJECT_DIR/configs/ace_xl_turbo_soft_sweep.toml" --backend "${ACE_BACKEND:-vllm}"
    ;;
  generate-compact)
    cd third_party/ACE-Step-1.5
    .venv/bin/python cli.py -c "$PROJECT_DIR/configs/ace_xl_turbo_compact_clean.toml" --backend "${ACE_BACKEND:-vllm}"
    ;;
  generate-sft)
    cd third_party/ACE-Step-1.5
    .venv/bin/python cli.py -c "$PROJECT_DIR/configs/ace_xl_sft_soft_single.toml" --backend "${ACE_BACKEND:-vllm}"
    ;;
  generate-balanced)
    cd third_party/ACE-Step-1.5
    .venv/bin/python cli.py -c "$PROJECT_DIR/configs/ace_xl_turbo_front_vocal_balanced.toml" --backend "${ACE_BACKEND:-vllm}"
    ;;
  quality)
    audio="$(latest_audio)"
    if [[ -z "${audio:-}" ]]; then echo "No generated WAV found." >&2; exit 1; fi
    PYTHONNOUSERSITE=1 conda run -n "$CONDA_ENV" python scripts/musia_quality_check.py "$audio" --language "$LANGUAGE" --expected-lyrics-file "$LYRICS" --asr-model large-v3 --output-dir "$PROJECT_DIR/reviews/$(basename "${audio%.wav}")-large"
    ;;
  review)
    audio="$(latest_audio)"
    if [[ -z "${audio:-}" ]]; then echo "No generated WAV found." >&2; exit 1; fi
    PYTHONNOUSERSITE=1 conda run -n "$CONDA_ENV" python scripts/musia_song_workbench.py review --project-dir "$PROJECT_DIR" --audio "$audio" --lyrics-file "$LYRICS" --language "$LANGUAGE" --run-analysis
    ;;
  analyze)
    audio="$(latest_audio)"
    if [[ -z "${audio:-}" ]]; then echo "No generated WAV found." >&2; exit 1; fi
    PYTHONNOUSERSITE=1 conda run -n "$CONDA_ENV" python scripts/run_pipeline.py "$audio" --run-name "$(basename "$PROJECT_DIR")-analysis" --max-duration 140 --asr-model large-v3 --language "$LANGUAGE" --demucs-device "${MUSIA_DEMUCS_DEVICE:-cuda}"
    ;;
  show)
    sed -n "1,220p" "$PROJECT_DIR/source/producer-brief.md"
    ;;
  help|*)
    echo "Usage: commands.sh generate-turbo|generate-compact|generate-sft|generate-balanced|quality|review|analyze|show"
    ;;
esac
