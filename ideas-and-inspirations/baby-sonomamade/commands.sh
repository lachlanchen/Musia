#!/usr/bin/env bash
set -euo pipefail

SOURCE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${MUSIA_ROOT:-$(cd "$SOURCE/../.." && pwd)}"
MODE="${1:-prepare}"
case "$MODE" in
  prepare) EXTRA=(--dry-run) ;;
  generate) EXTRA=() ;;
  *) printf 'Usage: bash commands.sh [prepare|generate]\n' >&2; exit 2 ;;
esac

cd "$ROOT"
export PYTHONNOUSERSITE=1
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
conda run --no-capture-output -n musia python scripts/run_ace_candidate_sweep.py \
  --lyrics "$SOURCE/lyrics.ja.txt" \
  --caption "$SOURCE/ace-caption.txt" \
  --output-dir "$ROOT/data/creative_projects/baby-sonomamade-20261126/candidates" \
  --seeds 112601 112602 112603 112604 112605 112606 \
  --duration 184 --bpm 108 --key 'D major' --language ja \
  --model acestep-v15-xl-turbo --vae official --batch-size 1 \
  "${EXTRA[@]}"
