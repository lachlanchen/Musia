#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/third_party/SongGeneration-v2"
ENV_DIR="$ROOT_DIR/.conda/songgeneration-v2"
PYTHON_BIN="${MUSIA_SONGGEN_V2_PYTHON:-$ENV_DIR/bin/python}"
MODEL_DIR="${MUSIA_SONGGEN_V2_MODEL:-$BACKEND_DIR/checkpoints/SongGeneration-v2-large}"

usage() {
  cat <<'USAGE'
Usage:
  MUSIA_ACCEPT_SONGGENERATION_RESEARCH_LICENSE=1 \
    scripts/run_songgeneration_v2.sh INPUT.jsonl OUTPUT_DIR [options]

Options:
  --mode mixed|separate|vocal|bgm  Output mode (default: mixed)
  --auto-memory                    Disable low-memory inference
  --flash-attn                     Enable Flash Attention if installed
  --model-dir PATH                 Override the v2-large checkpoint path
  -h, --help                       Show this help

SongGeneration / LeVo 2 is research-only under its current upstream license.
Do not use its output in Musia production or commercial publishing.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${MUSIA_ACCEPT_SONGGENERATION_RESEARCH_LICENSE:-0}" != "1" ]]; then
  echo "Set MUSIA_ACCEPT_SONGGENERATION_RESEARCH_LICENSE=1 after reviewing the upstream research-only license." >&2
  exit 3
fi

if [[ "$#" -lt 2 ]]; then
  usage >&2
  exit 2
fi

INPUT_JSONL="$(realpath "$1")"
OUTPUT_DIR="$(realpath -m "$2")"
shift 2

MODE="mixed"
LOW_MEMORY=1
USE_FLASH_ATTN=0

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:?--mode requires a value}"
      shift 2
      ;;
    --auto-memory)
      LOW_MEMORY=0
      shift
      ;;
    --flash-attn)
      USE_FLASH_ATTN=1
      shift
      ;;
    --model-dir)
      MODEL_DIR="$(realpath "${2:?--model-dir requires a path}")"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$MODE" in
  mixed|separate|vocal|bgm) ;;
  *)
    echo "Unsupported mode: $MODE" >&2
    exit 2
    ;;
esac

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing environment: $ENV_DIR" >&2
  echo "Run: bash scripts/install_quality_envs.sh songgeneration-v2" >&2
  exit 1
fi
if [[ ! -f "$BACKEND_DIR/generate.py" ]]; then
  echo "Missing SongGeneration v2 code: $BACKEND_DIR" >&2
  exit 1
fi
if [[ ! -f "$MODEL_DIR/model.pt" ]]; then
  echo "Missing SongGeneration v2 checkpoint: $MODEL_DIR/model.pt" >&2
  exit 1
fi
if [[ ! -f "$INPUT_JSONL" ]]; then
  echo "Missing input JSONL: $INPUT_JSONL" >&2
  exit 1
fi

REQUIRED_ARTIFACTS=(
  "$MODEL_DIR/config.yaml"
  "$MODEL_DIR/model.pt"
  "$BACKEND_DIR/tools/new_auto_prompt.pt"
  "$BACKEND_DIR/ckpt/model_septoken/model_2.safetensors"
  "$BACKEND_DIR/ckpt/model_1rvq/model_2_fixed.safetensors"
  "$BACKEND_DIR/ckpt/encode-s12k.pt"
  "$BACKEND_DIR/ckpt/vae/autoencoder_music_1320k.ckpt"
  "$BACKEND_DIR/ckpt/models--lengyue233--content-vec-best/snapshots/c0b9ba13db21beaa4053faae94c102ebe326fd68/pytorch_model.bin"
  "$BACKEND_DIR/third_party/demucs/ckpt/htdemucs.pth"
)
for artifact in "${REQUIRED_ARTIFACTS[@]}"; do
  if [[ ! -f "$artifact" ]]; then
    echo "Missing required SongGeneration v2 artifact: $artifact" >&2
    exit 1
  fi
  if [[ -f "$artifact.aria2" ]]; then
    echo "SongGeneration v2 artifact is still downloading: $artifact" >&2
    exit 1
  fi
done

AUTO_PROMPT="$BACKEND_DIR/tools/new_auto_prompt.pt"
AUTO_PROMPT_SHA256="616dbe27c99ac8ce7447423b6baa102f8c19d35e35d9020f32ad27e9a52134e7"
if [[ "$(stat -c '%s' "$AUTO_PROMPT")" != "14959842" ]] \
  || [[ "$(sha256sum "$AUTO_PROMPT" | cut -d' ' -f1)" != "$AUTO_PROMPT_SHA256" ]]; then
  echo "SongGeneration v2 auto-prompt asset is missing or failed verification." >&2
  echo "Rerun the research-only backend downloader before inference." >&2
  exit 1
fi
if ! "$PYTHON_BIN" -c "import pkg_resources" >/dev/null 2>&1; then
  echo "SongGeneration v2 needs setuptools<81 for the legacy CLIP decoder." >&2
  echo "Run: bash scripts/install_quality_envs.sh songgeneration-v2" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
export TRANSFORMERS_CACHE="$BACKEND_DIR/third_party/hub"
export PYTHONPATH="$BACKEND_DIR/codeclm/tokenizer:$BACKEND_DIR:$BACKEND_DIR/codeclm/tokenizer/Flow1dVAE:${PYTHONPATH:-}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export CUDA_LAUNCH_BLOCKING="${CUDA_LAUNCH_BLOCKING:-0}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

VALIDATOR_ARGS=(
  "$ROOT_DIR/scripts/validate_songgeneration_v2_input.py"
  "$INPUT_JSONL"
  --backend-dir "$BACKEND_DIR"
)
if [[ "${MUSIA_SONGGEN_ALLOW_OPEN_TAGS:-0}" != "1" ]]; then
  VALIDATOR_ARGS+=(--strict-tags)
fi
"$PYTHON_BIN" "${VALIDATOR_ARGS[@]}"

ARGS=(
  "$BACKEND_DIR/generate.py"
  --ckpt_path "$MODEL_DIR"
  --input_jsonl "$INPUT_JSONL"
  --save_dir "$OUTPUT_DIR"
  --generate_type "$MODE"
)
if [[ "$LOW_MEMORY" == "1" ]]; then
  ARGS+=(--low_mem)
fi
if [[ "$USE_FLASH_ATTN" == "1" ]]; then
  ARGS+=(--use_flash_attn)
fi

cd "$BACKEND_DIR"
"$PYTHON_BIN" "${ARGS[@]}"
