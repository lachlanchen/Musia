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
export HF_XET_HIGH_PERFORMANCE="${HF_XET_HIGH_PERFORMANCE:-1}"

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

clone_or_update_no_lfs() {
  local name="$1"
  local url="$2"
  local dest="$THIRD_PARTY/$name"
  if [[ -d "$dest/.git" ]]; then
    echo "Updating $name"
    git -C "$dest" fetch --depth 1 origin || true
  else
    echo "Cloning $name without optional Git LFS assets"
    GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 "$url" "$dest"
  fi
}

hf_download() {
  local repo="$1"
  local dest="$2"
  echo "Downloading $repo -> $dest"
  mkdir -p "$dest"
  hf download "$repo" --local-dir "$dest"
}

hf_aria_download() {
  local repo="$1"
  local remote_path="$2"
  local dest_root="$3"
  local output_dir="$dest_root/$(dirname "$remote_path")"
  local output_name
  local attempt
  local connections="${MUSIA_ARIA_CONNECTIONS:-4}"
  output_name="$(basename "$remote_path")"
  mkdir -p "$output_dir"
  if [[ -f "$output_dir/$output_name" && ! -f "$output_dir/$output_name.aria2" ]]; then
    echo "Using completed download: $output_dir/$output_name"
    return
  fi

  # Hugging Face's large-file redirects use expiring signed URLs. Restarting
  # aria2 against the stable resolve URL refreshes the signature while keeping
  # the existing .aria2 control file and downloaded byte ranges.
  for attempt in 1 2 3 4 5; do
    if aria2c \
      --continue=true \
      --max-connection-per-server="$connections" \
      --split="$connections" \
      --min-split-size=1M \
      --file-allocation=none \
      --auto-file-renaming=false \
      --max-tries=20 \
      --retry-wait=5 \
      --summary-interval=10 \
      --dir="$output_dir" \
      --out="$output_name" \
      "https://huggingface.co/$repo/resolve/main/$remote_path?download=true"; then
      return
    fi
    echo "Retrying $repo/$remote_path with a refreshed signed URL ($attempt/5)" >&2
    sleep 5
  done

  echo "Download failed after five resumable attempts: $repo/$remote_path" >&2
  return 1
}

download_verified_file() {
  local url="$1"
  local dest="$2"
  local expected_sha256="$3"
  local expected_size="$4"
  local tmp="${dest}.download"
  local actual_sha256
  local actual_size

  if [[ -f "$dest" ]]; then
    actual_size="$(stat -c '%s' "$dest")"
    actual_sha256="$(sha256sum "$dest" | cut -d' ' -f1)"
    if [[ "$actual_size" == "$expected_size" && "$actual_sha256" == "$expected_sha256" ]]; then
      echo "Using verified download: $dest"
      return
    fi
  fi

  mkdir -p "$(dirname "$dest")"
  rm -f "$tmp"
  curl \
    --fail \
    --location \
    --retry 5 \
    --retry-all-errors \
    --output "$tmp" \
    "$url"

  actual_size="$(stat -c '%s' "$tmp")"
  actual_sha256="$(sha256sum "$tmp" | cut -d' ' -f1)"
  if [[ "$actual_size" != "$expected_size" || "$actual_sha256" != "$expected_sha256" ]]; then
    rm -f "$tmp"
    echo "Downloaded file failed verification: $url" >&2
    return 1
  fi
  mv "$tmp" "$dest"
}

hydrate_lfs_file() {
  local repo_dir="$1"
  local relative_path="$2"
  local source_url="$3"
  local pointer
  local expected_sha256
  local expected_size

  pointer="$(git -C "$repo_dir" show "HEAD:$relative_path")"
  expected_sha256="$(printf '%s\n' "$pointer" | sed -n 's/^oid sha256://p')"
  expected_size="$(printf '%s\n' "$pointer" | sed -n 's/^size //p')"
  if [[ -z "$expected_sha256" || -z "$expected_size" ]]; then
    echo "Not a Git LFS pointer in $repo_dir: $relative_path" >&2
    return 1
  fi

  download_verified_file \
    "$source_url" \
    "$repo_dir/$relative_path" \
    "$expected_sha256" \
    "$expected_size"
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
    hf download HeartMuLa/HeartTranscriptor-oss \
      --exclude "model.safetensors" \
      --local-dir "$THIRD_PARTY/HeartMuLa/ckpt/HeartTranscriptor-oss"
    hf_aria_download \
      HeartMuLa/HeartTranscriptor-oss \
      model.safetensors \
      "$THIRD_PARTY/HeartMuLa/ckpt/HeartTranscriptor-oss"
    python3 "$ROOT_DIR/scripts/verify_hf_artifacts.py" \
      HeartMuLa/HeartTranscriptor-oss \
      "$THIRD_PARTY/HeartMuLa/ckpt/HeartTranscriptor-oss" \
      model.safetensors \
      --sha256
    ;;

  songgeneration-v2)
    if [[ "${MUSIA_ACCEPT_SONGGENERATION_RESEARCH_LICENSE:-0}" != "1" ]]; then
      cat >&2 <<'NOTICE'
SongGeneration / LeVo 2 is restricted to academic, research, and education use.
It must not be used for Musia commercial or production publishing.

Review:
  https://github.com/tencent-ailab/SongGeneration

Then rerun with:
  MUSIA_ACCEPT_SONGGENERATION_RESEARCH_LICENSE=1 \
    bash scripts/download_quality_backends.sh songgeneration-v2
NOTICE
      exit 3
    fi

    # The upstream GitHub repository currently returns 404 from this machine.
    # This mirror preserves the upstream code; model/runtime assets still come
    # from the original author's Hugging Face repositories.
    clone_or_update_no_lfs SongGeneration-v2 https://github.com/banner88/SongGeneration-v2.git
    # The mirror's LFS object is missing. Tencent's official Hugging Face Space
    # publishes the same asset under new_prompt.pt; the Git pointer's SHA-256
    # and size are still the source of truth before it replaces the pointer.
    hydrate_lfs_file \
      "$THIRD_PARTY/SongGeneration-v2" \
      tools/new_auto_prompt.pt \
      https://huggingface.co/spaces/tencent/SongGeneration/resolve/48275bf2c48a655af63684672fbbb1742ee4e919/tools/new_prompt.pt
    hf download lglg666/SongGeneration-Runtime \
      --include "ckpt/*" "third_party/*" \
      --exclude \
        "ckpt/model_septoken/model_2.safetensors" \
        "ckpt/model_1rvq/model_2_fixed.safetensors" \
        "ckpt/encode-s12k.pt" \
        "ckpt/vae/autoencoder_music_1320k.ckpt" \
        "ckpt/models--lengyue233--content-vec-best/blobs/*" \
        "ckpt/models--lengyue233--content-vec-best/snapshots/*/pytorch_model.bin" \
        "third_party/demucs/ckpt/htdemucs.pth" \
      --local-dir "$THIRD_PARTY/SongGeneration-v2"
    hf_aria_download \
      lglg666/SongGeneration-Runtime \
      ckpt/model_septoken/model_2.safetensors \
      "$THIRD_PARTY/SongGeneration-v2"
    hf_aria_download \
      lglg666/SongGeneration-Runtime \
      ckpt/model_1rvq/model_2_fixed.safetensors \
      "$THIRD_PARTY/SongGeneration-v2"
    hf_aria_download \
      lglg666/SongGeneration-Runtime \
      ckpt/encode-s12k.pt \
      "$THIRD_PARTY/SongGeneration-v2"
    hf_aria_download \
      lglg666/SongGeneration-Runtime \
      ckpt/vae/autoencoder_music_1320k.ckpt \
      "$THIRD_PARTY/SongGeneration-v2"
    hf_aria_download \
      lglg666/SongGeneration-Runtime \
      ckpt/models--lengyue233--content-vec-best/snapshots/c0b9ba13db21beaa4053faae94c102ebe326fd68/pytorch_model.bin \
      "$THIRD_PARTY/SongGeneration-v2"
    hf_aria_download \
      lglg666/SongGeneration-Runtime \
      third_party/demucs/ckpt/htdemucs.pth \
      "$THIRD_PARTY/SongGeneration-v2"
    hf download lglg666/SongGeneration-v2-large \
      --exclude "model.pt" \
      --local-dir "$THIRD_PARTY/SongGeneration-v2/checkpoints/SongGeneration-v2-large"
    hf_aria_download \
      lglg666/SongGeneration-v2-large \
      model.pt \
      "$THIRD_PARTY/SongGeneration-v2/checkpoints/SongGeneration-v2-large"
    python3 "$ROOT_DIR/scripts/verify_hf_artifacts.py" \
      lglg666/SongGeneration-v2-large \
      "$THIRD_PARTY/SongGeneration-v2/checkpoints/SongGeneration-v2-large" \
      model.pt \
      --sha256
    python3 "$ROOT_DIR/scripts/verify_hf_artifacts.py" \
      lglg666/SongGeneration-Runtime \
      "$THIRD_PARTY/SongGeneration-v2" \
      ckpt/model_septoken/model_2.safetensors \
      ckpt/model_1rvq/model_2_fixed.safetensors \
      ckpt/encode-s12k.pt \
      ckpt/vae/autoencoder_music_1320k.ckpt \
      ckpt/models--lengyue233--content-vec-best/snapshots/c0b9ba13db21beaa4053faae94c102ebe326fd68/pytorch_model.bin \
      third_party/demucs/ckpt/htdemucs.pth \
      --sha256
    ;;

  moss-music)
    hf_download OpenMOSS-Team/MOSS-Music-8B-Instruct "$THIRD_PARTY/MOSS-Music/weights/MOSS-Music-8B-Instruct"
    hf_download OpenMOSS-Team/MOSS-Music-8B-Thinking "$THIRD_PARTY/MOSS-Music/weights/MOSS-Music-8B-Thinking"
    ;;

  apex-music)
    hf_download amaai-lab/apex "$THIRD_PARTY/APEX"
    hf_download m-a-p/MERT-v1-95M "$THIRD_PARTY/APEX/mert-v1-95m"
    python3 "$ROOT_DIR/scripts/verify_hf_artifacts.py" \
      amaai-lab/apex \
      "$THIRD_PARTY/APEX" \
      pytorch_model.bin \
      --sha256
    python3 "$ROOT_DIR/scripts/verify_hf_artifacts.py" \
      m-a-p/MERT-v1-95M \
      "$THIRD_PARTY/APEX/mert-v1-95m" \
      pytorch_model.bin \
      --sha256
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
    "$0" apex-music
    if [[ "${MUSIA_ACCEPT_SONGGENERATION_RESEARCH_LICENSE:-0}" == "1" ]]; then
      "$0" songgeneration-v2
    else
      echo "Skipping research-only SongGeneration v2; set MUSIA_ACCEPT_SONGGENERATION_RESEARCH_LICENSE=1 after reviewing its license."
    fi
    ;;

  *)
    echo "Usage: $0 {repos|expanded-repos|soulx|ace-step|songgen|songgeneration-v2|yue-minimal|diffrhythm|heartmula|moss-music|apex-music|pro-links|core|all}" >&2
    exit 2
    ;;
esac
