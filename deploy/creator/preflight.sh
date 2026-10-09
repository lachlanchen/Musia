#!/usr/bin/env bash
# Read-only local inventory. Run separately on each role; never opens SSH itself.
set -euo pipefail
role=${1:?usage: preflight.sh edge-or-worker}
case "$role" in edge|worker) ;; *) exit 2 ;; esac
printf 'creator-preflight-role=%s\n' "$role"
free -h
df -h .
ss -ltn '( sport = :8797 or sport = :18440 or sport = :18896 or sport = :18897 or sport = :18898 )'
systemctl --no-pager --plain list-units 'musia-creator-*' 'musia-learning*' 'lazystudio-caddy*' 2>/dev/null || true
tmux list-sessions -F '#{session_name}' 2>/dev/null || true
node --version
if [[ -n "${MUSIA_LAZYEDGE_ROOT:-}" ]]; then
  node "$(dirname "$0")/inventory.mjs"
fi
if [[ "$role" == edge ]]; then
  if [[ -r /etc/lazystudio/Caddyfile ]]; then
    stat -c 'caddy-mode=%a owner=%U:%G' /etc/lazystudio/Caddyfile
    sha256sum /etc/lazystudio/Caddyfile
  fi
  if command -v nft >/dev/null 2>&1; then
    if rules=$(nft --stateless --numeric list ruleset 2>/dev/null); then
      printf '%s\n' "$rules" | sha256sum
    else
      printf 'firewall-inventory=unavailable-without-privilege\n'
    fi
  fi
fi
