#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_DIR="$ROOT_DIR/.conda/apex-music"
PYTHON_BIN="${MUSIA_APEX_PYTHON:-$ENV_DIR/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing APEX environment: $ENV_DIR" >&2
  echo "Run: bash scripts/install_quality_envs.sh apex-music" >&2
  exit 1
fi
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  export PYTHONNOUSERSITE=1
  exec "$PYTHON_BIN" "$ROOT_DIR/scripts/run_apex_music_quality.py" "$@"
fi
if [[ ! -f "$ROOT_DIR/third_party/APEX/config.json" ]] ||
   [[ ! -f "$ROOT_DIR/third_party/APEX/mert-v1-95m/config.json" ]]; then
  echo "Missing local APEX or MERT weights." >&2
  echo "Run: bash scripts/download_quality_backends.sh apex-music" >&2
  exit 1
fi

export PYTHONNOUSERSITE=1
exec "$PYTHON_BIN" "$ROOT_DIR/scripts/run_apex_music_quality.py" "$@"
