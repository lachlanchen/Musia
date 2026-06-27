#!/usr/bin/env bash
set -euo pipefail

export PYTHONNOUSERSITE=1

ENV_NAME="${MUSAI_ENV_NAME:-musai}"
CLONE_FROM=""
WITH_BASIC_PITCH=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)
      ENV_NAME="$2"
      shift 2
      ;;
    --clone-from)
      CLONE_FROM="$2"
      shift 2
      ;;
    --with-basic-pitch)
      WITH_BASIC_PITCH=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if ! command -v conda >/dev/null 2>&1; then
  echo "conda not found on PATH" >&2
  exit 1
fi

if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "Conda env '$ENV_NAME' already exists."
else
  if [[ -n "$CLONE_FROM" ]]; then
    echo "Cloning conda env '$CLONE_FROM' to '$ENV_NAME'."
    conda create -y -n "$ENV_NAME" --clone "$CLONE_FROM"
  else
    echo "Creating conda env '$ENV_NAME'."
    conda create -y -n "$ENV_NAME" -c conda-forge python=3.10 ffmpeg pip
  fi
fi

echo "Installing Musai core packages into '$ENV_NAME'."
conda run -n "$ENV_NAME" python -m pip install --upgrade pip setuptools wheel
conda run -n "$ENV_NAME" python -m pip install \
  torch==2.3.0 \
  torchaudio==2.3.0 \
  demucs \
  faster-whisper \
  librosa \
  soundfile \
  numpy \
  scipy \
  tqdm \
  requests \
  openai \
  pypinyin \
  jieba \
  phonemizer \
  pedalboard \
  pyloudnorm

if [[ "$WITH_BASIC_PITCH" == "1" ]]; then
  echo "Installing optional Basic Pitch. This may pull TensorFlow and can be heavy."
  conda run -n "$ENV_NAME" python -m pip install basic-pitch
fi

echo "Checking install."
conda run -n "$ENV_NAME" python -c "import importlib.util, torch; mods=['torch','torchaudio','librosa','soundfile','demucs','faster_whisper','openai','pypinyin','jieba']; [print(f'{m}: {\"ok\" if importlib.util.find_spec(m) else \"missing\"}') for m in mods]; print('torch_cuda_available:', torch.cuda.is_available())"

cat <<EOF

Musai environment is ready.

Run:
  PYTHONNOUSERSITE=1 conda run -n $ENV_NAME python scripts/download_open_songs.py --id danny-boy-1917
  PYTHONNOUSERSITE=1 conda run -n $ENV_NAME python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny --max-duration 45 --asr-model tiny
EOF
