#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${MUSIA_MINIMAX_PYTHON:-$ROOT/.conda/minimax-music3/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo 'Install first: bash scripts/install_minimax_music3.sh --verify-sha256' >&2
  exit 1
fi
export PYTHONNOUSERSITE=1
export HF_HOME="${HF_HOME:-$ROOT/.cache/huggingface}"
export TOKENIZERS_PARALLELISM=false
exec "$PYTHON_BIN" -u "$ROOT/scripts/run_minimax_music3.py" "$@"
