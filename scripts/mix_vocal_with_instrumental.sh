#!/usr/bin/env bash
set -euo pipefail

VOCAL_GAIN="${VOCAL_GAIN:-1.15}"
INSTRUMENTAL_GAIN="${INSTRUMENTAL_GAIN:-0.82}"
LOUDNESS_I="${LOUDNESS_I:--16}"
LOUDNESS_LRA="${LOUDNESS_LRA:-11}"
LOUDNESS_TP="${LOUDNESS_TP:--1.5}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/mix_vocal_with_instrumental.sh INSTRUMENTAL_WAV VOCAL_WAV OUTPUT_WAV [OUTPUT_MP3]

Environment:
  VOCAL_GAIN=1.15
  INSTRUMENTAL_GAIN=0.82
  LOUDNESS_I=-16
  LOUDNESS_LRA=11
  LOUDNESS_TP=-1.5
USAGE
}

if [[ $# -lt 3 || $# -gt 4 ]]; then
  usage >&2
  exit 2
fi

INSTRUMENTAL="$1"
VOCAL="$2"
OUTPUT_WAV="$3"
OUTPUT_MP3="${4:-}"

mkdir -p "$(dirname "$OUTPUT_WAV")"

ffmpeg -hide_banner -y \
  -i "$INSTRUMENTAL" \
  -i "$VOCAL" \
  -filter_complex "[0:a]volume=${INSTRUMENTAL_GAIN}[i];[1:a]aresample=44100,pan=stereo|c0=c0|c1=c0,volume=${VOCAL_GAIN}[v];[i][v]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.95,loudnorm=I=${LOUDNESS_I}:LRA=${LOUDNESS_LRA}:TP=${LOUDNESS_TP},aresample=44100,aformat=sample_fmts=s16:channel_layouts=stereo[out]" \
  -map "[out]" \
  "$OUTPUT_WAV"

if [[ -n "$OUTPUT_MP3" ]]; then
  mkdir -p "$(dirname "$OUTPUT_MP3")"
  ffmpeg -hide_banner -y -i "$OUTPUT_WAV" -codec:a libmp3lame -q:a 2 "$OUTPUT_MP3"
fi
