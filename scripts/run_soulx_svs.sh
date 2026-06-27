#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOULX_REPO="$ROOT_DIR/third_party/SoulX-Singer"
SOULX_ENV="$ROOT_DIR/.conda/soulxsinger"

CONTROL="${CONTROL:-melody}"
DEVICE="${DEVICE:-cuda}"
PITCH_SHIFT="${PITCH_SHIFT:-0}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/run_soulx_svs.sh PROMPT_WAV PROMPT_METADATA TARGET_METADATA OUTPUT_DIR

Environment:
  CONTROL=melody|score  default: melody
  DEVICE=cuda|cpu       default: cuda
  PITCH_SHIFT=INT       default: 0
USAGE
}

if [[ $# -ne 4 ]]; then
  usage >&2
  exit 2
fi

if [[ ! -x "$SOULX_ENV/bin/python" ]]; then
  echo "Missing SoulX env: $SOULX_ENV" >&2
  echo "Run: bash scripts/install_quality_envs.sh soulx" >&2
  exit 1
fi

PROMPT_WAV="$(readlink -f "$1")"
PROMPT_METADATA="$(readlink -f "$2")"
TARGET_METADATA="$(readlink -f "$3")"
OUTPUT_DIR="$(mkdir -p "$4" && cd "$4" && pwd)"

export PYTHONNOUSERSITE=1
export PYTHONPATH="$SOULX_REPO:${PYTHONPATH:-}"

cd "$SOULX_REPO"

exec "$SOULX_ENV/bin/python" -m cli.inference \
  --device "$DEVICE" \
  --model_path pretrained_models/SoulX-Singer/model.pt \
  --config soulxsinger/config/soulxsinger.yaml \
  --prompt_wav_path "$PROMPT_WAV" \
  --prompt_metadata_path "$PROMPT_METADATA" \
  --target_metadata_path "$TARGET_METADATA" \
  --phoneset_path soulxsinger/utils/phoneme/phone_set.json \
  --save_dir "$OUTPUT_DIR" \
  --auto_shift \
  --pitch_shift "$PITCH_SHIFT" \
  --control "$CONTROL" \
  --fp16
