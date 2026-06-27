#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONDA_ENV="${CONDA_ENV:-musai}"
MAX_DURATION="${MAX_DURATION:-60}"
ASR_MODEL="${ASR_MODEL:-small}"
DEMUCS_DEVICE="${DEMUCS_DEVICE:-cuda}"

cd "$ROOT_DIR"

export PYTHONNOUSERSITE=1

run_case() {
  local song_id="$1"
  local run_name="$2"
  local language="$3"
  local extra_flag="${4:-}"
  local input

  input="$(PYTHONNOUSERSITE=1 conda run -n "$CONDA_ENV" python scripts/download_open_songs.py --id "$song_id" | awk 'NF { line = $0 } END { print line }')"

  if [[ "$extra_flag" == "skip-asr" ]]; then
    conda run -n "$CONDA_ENV" python scripts/run_pipeline.py "$input" \
      --run-name "$run_name" \
      --max-duration "$MAX_DURATION" \
      --skip-asr \
      --asr-model "$ASR_MODEL" \
      --demucs-device "$DEMUCS_DEVICE"
  else
    conda run -n "$CONDA_ENV" python scripts/run_pipeline.py "$input" \
      --run-name "$run_name" \
      --max-duration "$MAX_DURATION" \
      --asr-model "$ASR_MODEL" \
      --language "$language" \
      --demucs-device "$DEMUCS_DEVICE"
  fi
}

run_case danny-boy-1917 test-danny-en-60 en
run_case chinese-vocal-ensemble test-chinese-vocal-zh-60 zh
run_case hotaru-no-hikari test-hotaru-ja-60 ja
run_case moli-hua-ks-synth test-moli-hua-instrumental-30 zh skip-asr
