#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_DIR="${MUSIA_MINIMAX_ENV:-$ROOT/.conda/minimax-music3}"
SOURCE="$ROOT/third_party/diffusers-music3"
DIFFUSERS_REV="${MUSIA_MINIMAX_DIFFUSERS_REV:-c419dac0152186060246c93a095bc1bfaea342b3}"
export PYTHONNOUSERSITE=1
export HF_HOME="${HF_HOME:-$ROOT/.cache/huggingface}"

if [[ ! -x "$ENV_DIR/bin/python" ]]; then
  BASE_PYTHON="${MUSIA_MINIMAX_BASE_PYTHON:-$ROOT/.conda/moss-music/bin/python}"
  if [[ -x "$BASE_PYTHON" ]] && "$BASE_PYTHON" -c 'import torch; assert torch.cuda.is_available() and tuple(map(int, torch.__version__.split(".")[:2])) >= (2, 6)'; then
    # The overlay owns new packages; the verified base CUDA runtime is read-only.
    "$BASE_PYTHON" -m venv --system-site-packages "$ENV_DIR"
  else
    conda create -y -p "$ENV_DIR" python=3.11 pip
  fi
fi
if [[ ! -d "$SOURCE/.git" ]]; then
  git clone --depth 1 https://github.com/huggingface/diffusers.git "$SOURCE"
fi
if [[ -n "$(git -C "$SOURCE" status --porcelain)" ]]; then
  echo "Refusing to modify a dirty Diffusers checkout: $SOURCE" >&2
  exit 1
fi
git -C "$SOURCE" fetch origin "$DIFFUSERS_REV"
git -C "$SOURCE" checkout --detach "$DIFFUSERS_REV"
# PyPI's Linux torch 2.8 wheel includes CUDA 12.8 dependencies. Use PyPI for
# the whole resolution: NVIDIA's wheel host repeatedly timed out here.
if ! "$ENV_DIR/bin/python" -c 'import torch; assert tuple(map(int, torch.__version__.split(".")[:2])) >= (2, 6)'; then
  "$ENV_DIR/bin/python" -m pip install torch==2.8.0 \
    --index-url https://pypi.org/simple
fi
# pip honors the overlay's system site packages; uv otherwise resolves a new
# torch/CUDA stack even though the shared base already satisfies the requirement.
"$ENV_DIR/bin/python" -m pip install -e "$SOURCE" \
  transformers==5.17.0 accelerate==1.12.0 soundfile psutil
if [[ ! -f "$ENV_DIR/pyvenv.cfg" ]]; then
  "$ENV_DIR/bin/python" -m pip check
fi
if [[ "${MUSIA_MINIMAX_SKIP_DOWNLOAD:-0}" != "1" ]]; then
  "$ENV_DIR/bin/python" "$ROOT/scripts/download_minimax_music3.py" --verify-sha256 "$@"
fi
"$ENV_DIR/bin/python" -c 'from diffusers import ModularPipeline, MiniMaxMusic3ModularPipeline; import torch; print("MiniMax Music 3 runtime ready", torch.__version__, torch.cuda.is_available())'
