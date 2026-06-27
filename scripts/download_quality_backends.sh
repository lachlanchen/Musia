#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THIRD_PARTY="$ROOT_DIR/third_party"
HF_HOME_DIR="$ROOT_DIR/.cache/huggingface"
UV_CACHE_DIR="${UV_CACHE_DIR:-$ROOT_DIR/.cache/uv}"
TMPDIR="${TMPDIR:-$ROOT_DIR/.cache/tmp}"
DOWNLOADS_DIR="$ROOT_DIR/downloads/pro-vocal-tools"
UV_BIN="${UV_BIN:-$(command -v uv || true)}"
if [[ -z "$UV_BIN" && -x "$HOME/miniconda3/bin/uv" ]]; then
  UV_BIN="$HOME/miniconda3/bin/uv"
fi

mkdir -p "$THIRD_PARTY" "$HF_HOME_DIR" "$UV_CACHE_DIR" "$TMPDIR" "$DOWNLOADS_DIR"

export HF_HOME="$HF_HOME_DIR"
export HF_HUB_CACHE="$HF_HOME_DIR/hub"
export HUGGINGFACE_HUB_CACHE="$HF_HOME_DIR/hub"
export UV_CACHE_DIR
export TMPDIR
export PYTHONNOUSERSITE=1

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

clone_or_update_recursive() {
  local name="$1"
  local url="$2"
  clone_or_update "$name" "$url"
  git -C "$THIRD_PARTY/$name" submodule update --init --recursive --depth 1 || true
}

hf_download() {
  local repo="$1"
  local dest="$2"
  echo "Downloading $repo -> $dest"
  mkdir -p "$dest"
  hf download "$repo" --local-dir "$dest"
}

case "${1:-core}" in
  repos)
    clone_or_update SoulX-Singer https://github.com/Soul-AILab/SoulX-Singer.git
    clone_or_update YingMusic-Singer-Plus https://github.com/ASLP-lab/YingMusic-Singer-Plus.git
    clone_or_update ACE-Step https://github.com/ace-step/ACE-Step.git
    clone_or_update ACE-Step-1.5 https://github.com/ace-step/ACE-Step-1.5.git
    clone_or_update DiffRhythm https://github.com/ASLP-lab/DiffRhythm.git
    clone_or_update SongGen https://github.com/LiuZH-19/SongGen.git
    clone_or_update YuE https://github.com/multimodal-art-projection/YuE.git
    clone_or_update HeartMuLa https://github.com/HeartMuLa/heartlib.git
    clone_or_update MOSS-Music https://github.com/OpenMOSS/MOSS-Music.git
    ;;

  expanded-repos)
    "$0" repos
    clone_or_update Muzic https://github.com/microsoft/muzic.git
    clone_or_update MERT https://github.com/yizhilll/MERT.git
    clone_or_update MuQ https://github.com/tencent-ailab/MuQ.git
    clone_or_update MuCodec https://github.com/tencent-ailab/MuCodec.git
    clone_or_update_recursive FunMusic https://github.com/FunAudioLLM/FunMusic.git
    clone_or_update Amphion https://github.com/open-mmlab/Amphion.git
    clone_or_update OpenVPI-DiffSinger https://github.com/openvpi/DiffSinger.git
    clone_or_update NNSVS https://github.com/nnsvs/nnsvs.git
    clone_or_update OpenUtau https://github.com/openutau/OpenUtau.git
    clone_or_update AudioCraft https://github.com/facebookresearch/audiocraft.git
    clone_or_update stable-audio-tools https://github.com/Stability-AI/stable-audio-tools.git
    clone_or_update Magenta https://github.com/magenta/magenta.git
    ;;

  soulx)
    hf_download Soul-AILab/SoulX-Singer "$THIRD_PARTY/SoulX-Singer/pretrained_models/SoulX-Singer"
    hf_download Soul-AILab/SoulX-Singer-Preprocess "$THIRD_PARTY/SoulX-Singer/pretrained_models/SoulX-Singer-Preprocess"
    ;;

  ace-step)
    if [[ -z "$UV_BIN" ]]; then
      echo "uv is required for ACE-Step. Install uv or set UV_BIN=/path/to/uv." >&2
      exit 1
    fi
    (
      cd "$THIRD_PARTY/ACE-Step-1.5"
      export HF_HOME="$HF_HOME_DIR"
      export HF_HUB_CACHE="$HF_HOME_DIR/hub"
      "$UV_BIN" sync
      "$UV_BIN" run acestep-download
      "$UV_BIN" run acestep-download --model acestep-v15-xl-turbo
    )
    ;;

  songgen)
    hf_download LiuZH-19/SongGen_mixed_pro "$THIRD_PARTY/SongGen/checkpoints/SongGen_mixed_pro"
    hf_download LiuZH-19/SongGen_interleaving_A_V "$THIRD_PARTY/SongGen/checkpoints/SongGen_interleaving_A_V"
    hf_download ZhenYe234/xcodec "$THIRD_PARTY/SongGen/songgen/xcodec_wrapper/xcodec_infer/ckpts/general_more"
    ;;

  yue-minimal)
    hf_download m-a-p/xcodec_mini_infer "$THIRD_PARTY/YuE/inference/xcodec_mini_infer"
    hf_download m-a-p/YuE-s1-7B-anneal-zh-cot "$THIRD_PARTY/YuE/checkpoints/YuE-s1-7B-anneal-zh-cot"
    hf_download m-a-p/YuE-s2-1B-general "$THIRD_PARTY/YuE/checkpoints/YuE-s2-1B-general"
    ;;

  heartmula)
    hf_download HeartMuLa/HeartMuLaGen "$THIRD_PARTY/HeartMuLa/ckpt"
    hf_download HeartMuLa/HeartMuLa-oss-3B-happy-new-year "$THIRD_PARTY/HeartMuLa/ckpt/HeartMuLa-oss-3B"
    hf_download HeartMuLa/HeartCodec-oss-20260123 "$THIRD_PARTY/HeartMuLa/ckpt/HeartCodec-oss"
    ;;

  moss-music)
    hf_download OpenMOSS-Team/MOSS-Music-8B-Instruct "$THIRD_PARTY/MOSS-Music/weights/MOSS-Music-8B-Instruct"
    hf_download OpenMOSS-Team/MOSS-Music-8B-Thinking "$THIRD_PARTY/MOSS-Music/weights/MOSS-Music-8B-Thinking"
    ;;

  diffrhythm)
    hf_download ASLP-lab/DiffRhythm-1_2-full "$THIRD_PARTY/DiffRhythm/checkpoints/DiffRhythm-1_2-full"
    hf_download ASLP-lab/DiffRhythm-vae "$THIRD_PARTY/DiffRhythm/checkpoints/DiffRhythm-vae"
    ;;

  pro-links)
    cat > "$DOWNLOADS_DIR/OFFICIAL_TRIAL_AND_PAID_LINKS.md" <<'LINKS'
# Official Trial / Paid Vocal Tools

These are official links only. Do not use cracked builds or bypass licensing.

- Synthesizer V Studio 2 Pro trial: https://dreamtonics.com/download-free-trials/
- Synthesizer V product page: https://dreamtonics.com/synthesizerv/
- ACE Studio download: https://acestudio.ai/download/
- ACE Studio pricing/trial: https://acestudio.ai/pricing/
- ACE Studio MuseHub listing: https://www.musehub.com/app/ace-studio
- Kits AI: https://www.kits.ai/
- Musicfy: https://musicfy.lol/
- LALAL.AI voice tools: https://www.lalal.ai/voice-changer/

Linux note:
- Current ACE Studio desktop downloads are Windows/macOS.
- Current Synthesizer V Studio 2 Pro trial downloads are Windows/macOS.
- Synthesizer V Studio Pro 1 historically supports Linux, but Pro downloads are tied to purchase channels.
LINKS
    echo "$DOWNLOADS_DIR/OFFICIAL_TRIAL_AND_PAID_LINKS.md"
    ;;

  core)
    "$0" repos
    "$0" pro-links
    "$0" soulx
    "$0" ace-step
    ;;

  all)
    "$0" core
    "$0" songgen
    "$0" yue-minimal
    "$0" diffrhythm
    "$0" heartmula
    "$0" moss-music
    ;;

  *)
    echo "Usage: $0 {repos|expanded-repos|soulx|ace-step|songgen|yue-minimal|diffrhythm|heartmula|moss-music|pro-links|core|all}" >&2
    exit 2
    ;;
esac
