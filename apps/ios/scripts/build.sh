#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACTION="${1:-preflight}"
if [[ "$(uname -s)" != Darwin ]]; then
  printf '%s\n' 'iOS builds require macOS. No remote command was started.' >&2
  exit 1
fi
if [[ -n "${MUSIA_DEVELOPER_DIR:-}" ]]; then
  export DEVELOPER_DIR="$MUSIA_DEVELOPER_DIR"
fi
cd "$ROOT"

preflight() {
  xcodebuild -version
  xcrun --find swift
  plutil -lint Musia/Resources/Info.plist Musia/Resources/PrivacyInfo.xcprivacy
  plutil -lint Musia.xcodeproj/project.pbxproj
  printf '\nMemory and swap:\n'
  vm_stat
  sysctl vm.swapusage
  printf '\nActive build / simulator / remote desktop processes:\n'
  ps axo pid,ppid,rss,command | grep -E '[x]codebuild|[G]radleDaemon|[g]radle|[e]mulator|[S]imulator.app/Contents/MacOS|[X]vfb|[x]11vnc|[w]ebsockify|Projects/[M]usia' || true
  if command -v tmux >/dev/null; then tmux list-sessions || true; fi
  lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -E ':(590[0-9]|608[0-9]|609[0-9])\b' || true
  printf '\nNo build has started. Coordinate with the Android job and inspect resource ownership first.\n'
}

if [[ "$ACTION" == preflight ]]; then preflight; exit 0; fi
case "$ACTION" in
  build|test|core-test|archive|export) ;;
  *) printf 'Usage: bash scripts/build.sh [preflight|build|test|core-test|archive|export]\n' >&2; exit 2 ;;
esac
if [[ "${MUSIA_BUILD_COORDINATED:-}" != 1 ]]; then
  printf '%s\n' 'Blocked: set MUSIA_BUILD_COORDINATED=1 only after Android has finished and the shared Mac slot is confirmed.' >&2
  exit 2
fi

mkdir -p "$ROOT/build"
LOCK="$ROOT/build/.native-build-lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  printf '%s\n' 'A Musia native build lock exists. Verify its owner; do not start another build.' >&2
  exit 3
fi
printf '%s\n' "$$" > "$LOCK/pid"
trap 'rm -f "$LOCK/pid"; rmdir "$LOCK"' EXIT

COMMON=(-quiet -project "$ROOT/Musia.xcodeproj" -scheme Musia -derivedDataPath "$ROOT/build/DerivedData"
  -jobs "${MUSIA_BUILD_JOBS:-1}" "OTHER_SWIFT_FLAGS=\$(inherited) -j${MUSIA_BUILD_JOBS:-1}")
case "$ACTION" in
  build)
    xcodebuild "${COMMON[@]}" -configuration Debug -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build
    ;;
  test)
    : "${MUSIA_TEST_DESTINATION:?Set a specific available simulator, e.g. platform=iOS Simulator,id=UUID}"
    TEST_FILTER=()
    if [[ -n "${MUSIA_ONLY_TESTING:-}" ]]; then TEST_FILTER=("-only-testing:$MUSIA_ONLY_TESTING"); fi
    xcodebuild "${COMMON[@]}" "${TEST_FILTER[@]}" -configuration Debug -destination "$MUSIA_TEST_DESTINATION" \
      -parallel-testing-enabled NO -maximum-concurrent-test-simulator-destinations 1 \
      -resultBundlePath "$ROOT/build/Tests-$(date -u +%Y%m%dT%H%M%SZ).xcresult" CODE_SIGNING_ALLOWED=NO test
    ;;
  core-test)
    swift test --package-path "$ROOT" --scratch-path "$ROOT/build/SwiftPackage" --jobs "${MUSIA_BUILD_JOBS:-1}"
    ;;
  archive)
    : "${MUSIA_DEVELOPMENT_TEAM:?Set the approved Apple team in the environment}"
    : "${MUSIA_SIGNING_IDENTITY:?Set the installed signing identity in the environment}"
    : "${MUSIA_PROVISIONING_PROFILE:?Set the Musia-specific provisioning profile in the environment}"
    : "${MUSIA_BUILD_NUMBER:?Set a new build number}"
    # Sign core with the team identity, but apply the provisioning profile only to the app target.
    xcodebuild "${COMMON[@]}" -configuration Release -destination 'generic/platform=iOS' \
      -archivePath "$ROOT/build/Musia.xcarchive" \
      DEVELOPMENT_TEAM="$MUSIA_DEVELOPMENT_TEAM" CODE_SIGN_STYLE=Manual \
      CODE_SIGN_IDENTITY="$MUSIA_SIGNING_IDENTITY" MUSIA_APP_PROFILE="$MUSIA_PROVISIONING_PROFILE" \
      CURRENT_PROJECT_VERSION="$MUSIA_BUILD_NUMBER" archive
    ;;
  export)
    : "${MUSIA_EXPORT_OPTIONS_PLIST:?Set the absolute path of an external export-options plist}"
    if [[ "$MUSIA_EXPORT_OPTIONS_PLIST" != /* || ! -f "$MUSIA_EXPORT_OPTIONS_PLIST" ]]; then
      printf '%s\n' 'Export options must be an existing absolute path outside the source tree.' >&2; exit 2
    fi
    case "$MUSIA_EXPORT_OPTIONS_PLIST" in "$ROOT"/*) printf '%s\n' 'Keep signing/export configuration outside this source tree.' >&2; exit 2 ;; esac
    plutil -lint "$MUSIA_EXPORT_OPTIONS_PLIST"
    DESTINATION="$(/usr/libexec/PlistBuddy -c 'Print :destination' "$MUSIA_EXPORT_OPTIONS_PLIST" 2>/dev/null || true)"
    if [[ "$DESTINATION" == upload ]]; then
      printf '%s\n' 'Upload export options are forbidden. This script only exports local artifacts.' >&2; exit 2
    fi
    xcodebuild -exportArchive -archivePath "$ROOT/build/Musia.xcarchive" \
      -exportPath "$ROOT/build/export" -exportOptionsPlist "$MUSIA_EXPORT_OPTIONS_PLIST"
    ;;
esac
