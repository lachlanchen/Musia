#!/usr/bin/env bash
set -euo pipefail

SESSION="${MUSAI_STUDIO_SESSION:-musai-studio}"
PORT="${MUSAI_STUDIO_PORT:-8765}"
HOST="${MUSAI_STUDIO_HOST:-127.0.0.1}"
ENV_NAME="${MUSAI_ENV_NAME:-musai}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/data/runs"
LOG_FILE="$LOG_DIR/musai-studio-server.log"
PORT_FILE="$LOG_DIR/musai-studio-server.port"

mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  if [[ -f "$PORT_FILE" ]]; then
    PORT="$(cat "$PORT_FILE")"
  fi
  echo "Musai Studio already running in tmux session: $SESSION"
  echo "URL: http://$HOST:$PORT"
  exit 0
fi

if [[ -z "${MUSAI_STUDIO_PORT:-}" ]]; then
  for candidate in $(seq "$PORT" 8785); do
    if ! ss -ltn | awk '{print $4}' | grep -Eq "(:|\\])${candidate}$"; then
      PORT="$candidate"
      break
    fi
  done
fi

printf '%s\n' "$PORT" > "$PORT_FILE"

tmux new-session -d -s "$SESSION" \
  "cd '$ROOT_DIR' && PYTHONNOUSERSITE=1 conda run -n '$ENV_NAME' python scripts/musai_studio_web.py --host '$HOST' --port '$PORT' 2>&1 | tee '$LOG_FILE'"

echo "Started Musai Studio in tmux session: $SESSION"
echo "URL: http://$HOST:$PORT"
echo "Log: $LOG_FILE"
echo "Attach: tmux attach -t $SESSION"
