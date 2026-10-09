#!/usr/bin/env bash
# Authorized native test build, using existing shared signing material only.
set -euo pipefail
root="${MUSIA_ROOT:-$HOME/Projects/Musia}"
cd "$root"
python="${MUSIA_STORE_PYTHON:-$HOME/.local/share/musia/store-python/bin/python}"
export DEVELOPER_DIR="${DEVELOPER_DIR:-/usr/local/echomind-formal-xcode/Xcode_26.6.app/Contents/Developer}"
export PATH="$DEVELOPER_DIR/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin"
case "${1:-}" in ios|macos) ;; *) exit 64 ;; esac
if pgrep -x xcodebuild >/dev/null || pgrep -x swift-frontend >/dev/null; then
    printf '%s\n' 'Peer Apple build active; no Musia build launched.'
    exit 75
fi
df -h /Users
memory_pressure -Q
test "$(df -k /Users | awk 'NR==2 {print $4}')" -gt 4194304
if [[ "$1" == ios ]]; then
    keychain=$($python -c 'import sys; sys.path.insert(0,"tools/store"); from storelib import config; print(config()["apple_keychain"])')
    password=$(tr -d '\r\n' < "${MUSIA_KEYCHAIN_PASSWORD_FILE:-$HOME/.config/echomind/apple/release-keychain.pass}")
    security unlock-keychain -p "$password" "$keychain"
    unset password
    exec "$python" tools/store/musia_store.py build-ios --execute-build
fi
export MUSIA_MAC_RELEASE
MUSIA_MAC_RELEASE=$($python -c 'import json; r=json.load(open("store/release.json")); print(r["version"]+"-"+r["ios_build"])')
export MUSIA_MAC_PROFILE_PATH="${MUSIA_MAC_PROFILE_PATH:-$root/store/.runtime/macos-20261004/Musia_Mac_App_Store.provisionprofile}"
export MUSIA_BUILD_JOBS=2
exec bash tools/store/build_macos.sh
