#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THIRD_PARTY="$ROOT_DIR/third_party"
mkdir -p "$THIRD_PARTY"

clone_or_update() {
  local name="$1"
  local url="$2"
  local dest="$THIRD_PARTY/$name"
  if [[ -d "$dest/.git" ]]; then
    echo "Updating $name"
    git -C "$dest" fetch --depth 1 origin || true
  else
    echo "Cloning $name"
    git clone --depth 1 "$url" "$dest"
  fi
}

clone_or_update demucs https://github.com/facebookresearch/demucs.git
clone_or_update whisperx https://github.com/m-bain/whisperX.git
clone_or_update RMVPE https://github.com/Dream-High/RMVPE.git
clone_or_update basic-pitch https://github.com/spotify/basic-pitch.git
clone_or_update YingMusic-Singer https://github.com/ASLP-lab/YingMusic-Singer.git
clone_or_update SoulX-Singer https://github.com/Soul-AILab/SoulX-Singer.git
clone_or_update Amphion https://github.com/open-mmlab/Amphion.git
clone_or_update DiffSinger https://github.com/MoonInTheRiver/DiffSinger.git
clone_or_update RVC-WebUI https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git
clone_or_update GPT-SoVITS https://github.com/RVC-Boss/GPT-SoVITS.git
clone_or_update ACE-Step-1.5 https://github.com/ace-step/ACE-Step-1.5.git
clone_or_update YuE https://github.com/multimodal-art-projection/YuE.git

echo "Research repositories are under $THIRD_PARTY."
echo "Model weights are not downloaded automatically; check each license and setup guide first."

