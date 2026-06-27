#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THIRD_PARTY="$ROOT_DIR/third_party"
ENV_ROOT="$ROOT_DIR/.conda"
CACHE_ROOT="$ROOT_DIR/.cache"
CONDA_EXE="${CONDA_EXE:-$(command -v conda)}"

mkdir -p "$ENV_ROOT" "$CACHE_ROOT/pip" "$CACHE_ROOT/huggingface" "$CACHE_ROOT/tmp"

export PIP_CACHE_DIR="$CACHE_ROOT/pip"
export HF_HOME="$CACHE_ROOT/huggingface"
export HF_HUB_CACHE="$HF_HOME/hub"
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
export TMPDIR="$CACHE_ROOT/tmp"
export PYTHONNOUSERSITE=1

create_env() {
  local path="$1"
  local python_version="$2"
  if [[ -x "$path/bin/python" ]]; then
    echo "Using existing env: $path"
  else
    "$CONDA_EXE" create -y -p "$path" "python=$python_version" pip
  fi
}

pip_in_env() {
  local path="$1"
  shift
  "$path/bin/python" -m pip "$@"
}

add_python_path_entry() {
  local path="$1"
  local entry="$2"
  local name="$3"
  local site_packages
  site_packages="$("$path/bin/python" -c 'import site; print(site.getsitepackages()[0])')"
  printf '%s\n' "$entry" > "$site_packages/$name.pth"
}

case "${1:-all}" in
  system-deps)
    if command -v espeak-ng >/dev/null 2>&1; then
      echo "espeak-ng already installed"
    elif command -v sudo >/dev/null 2>&1; then
      sudo -n apt-get update
      sudo -n apt-get install -y espeak-ng libsndfile1 ffmpeg
    else
      echo "sudo unavailable; install espeak-ng manually for DiffRhythm phonemizer support" >&2
      exit 1
    fi
    ;;

  soulx)
    create_env "$ENV_ROOT/soulxsinger" "3.10"
    pip_in_env "$ENV_ROOT/soulxsinger" install -U pip setuptools wheel
    pip_in_env "$ENV_ROOT/soulxsinger" install -r "$THIRD_PARTY/SoulX-Singer/requirements.txt"
    pip_in_env "$ENV_ROOT/soulxsinger" install "lightning>=2.2,<3" fiddle cloudpickle
    add_python_path_entry "$ENV_ROOT/soulxsinger" "$THIRD_PARTY/SoulX-Singer" "musai-soulx-singer"
    ;;

  ace-step)
    (
      cd "$THIRD_PARTY/ACE-Step-1.5"
      uv sync
    )
    ;;

  songgen)
    create_env "$ENV_ROOT/songgen" "3.9.18"
    pip_in_env "$ENV_ROOT/songgen" install -U pip setuptools wheel
    pip_in_env "$ENV_ROOT/songgen" install \
      torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 \
      --index-url https://download.pytorch.org/whl/cu118
    pip_in_env "$ENV_ROOT/songgen" install psutil ninja
    pip_in_env "$ENV_ROOT/songgen" install flash-attn==2.6.1 --no-build-isolation
    pip_in_env "$ENV_ROOT/songgen" install "spacy==3.7.5"
    pip_in_env "$ENV_ROOT/songgen" install -e "$THIRD_PARTY/SongGen"
    ;;

  diffrhythm)
    create_env "$ENV_ROOT/diffrhythm" "3.10"
    pip_in_env "$ENV_ROOT/diffrhythm" install -U pip setuptools wheel
    pip_in_env "$ENV_ROOT/diffrhythm" install \
      torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 \
      --index-url https://download.pytorch.org/whl/cu124
    pip_in_env "$ENV_ROOT/diffrhythm" install -r "$THIRD_PARTY/DiffRhythm/requirements.txt"
    ;;

  heartmula)
    create_env "$ENV_ROOT/heartmula" "3.10"
    pip_in_env "$ENV_ROOT/heartmula" install -U pip setuptools wheel
    pip_in_env "$ENV_ROOT/heartmula" install -e "$THIRD_PARTY/HeartMuLa"
    ;;

  moss-music)
    create_env "$ENV_ROOT/moss-music" "3.12"
    "$CONDA_EXE" install -y -p "$ENV_ROOT/moss-music" -c conda-forge "ffmpeg=7"
    pip_in_env "$ENV_ROOT/moss-music" install -U pip setuptools wheel
    pip_in_env "$ENV_ROOT/moss-music" install --extra-index-url https://download.pytorch.org/whl/cu128 -e "$THIRD_PARTY/MOSS-Music[torch-runtime]"
    pip_in_env "$ENV_ROOT/moss-music" install "nvidia-npp-cu12==12.4.1.87"
    ;;

  all)
    "$0" system-deps || true
    "$0" soulx
    "$0" ace-step
    "$0" songgen
    "$0" diffrhythm
    "$0" heartmula
    "$0" moss-music
    ;;

  *)
    echo "Usage: $0 {system-deps|soulx|ace-step|songgen|diffrhythm|heartmula|moss-music|all}" >&2
    exit 2
    ;;
esac
