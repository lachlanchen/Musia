#!/usr/bin/env bash
# Internal QA only. One owned simulator, no store/device/profile mutations.
set -euo pipefail
cd "${MUSIA_ROOT:?Set the isolated Musia source checkout}"
phase="${1:?headless, core, mac, mobile, iphone or ipad}"
out="${2:?Fresh private evidence directory}"
# Invoke through apple_build_guard.py after explicit queue admission.
/usr/bin/python3 -c '
import json,os
from pathlib import Path
owner=json.loads(Path("/tmp/lazyingart-apple-build.lock/owner.json").read_text())
assert owner["app"]=="Musia" and owner["token"]==os.environ.get("MUSIA_APPLE_GUARD_TOKEN")
assert Path(owner["checkout"]).resolve()==Path.cwd().resolve()
'
device=""
cleanup() {
    if [[ -n "$device" ]]; then
        xcrun simctl shutdown "$device" >/dev/null 2>&1 || true
        xcrun simctl list devices --json | /usr/bin/python3 -c '
import json,sys
rows=[d for ds in json.load(sys.stdin)["devices"].values() for d in ds if d["udid"]==sys.argv[1]]
assert len(rows)==1 and rows[0]["state"]=="Shutdown"
' "$device" || exit 76
    fi
    if [[ "$phase" == mac ]]; then
        /usr/bin/python3 tools/store/apple_qa_command.py --check-app-exited || exit 76
    fi
}
trap cleanup EXIT
bounded() { /usr/bin/python3 tools/store/apple_qa_command.py "$@"; }
if pgrep -x xcodebuild >/dev/null || pgrep -x swift-frontend >/dev/null; then
    printf '%s\n' 'Peer Apple build active; no Musia QA launched.'
    exit 75
fi
test ! -e "$out"
mkdir -m 700 -p "$out"
df -h /Users
memory_pressure -Q
test "$(df -k /Users | awk 'NR==2 {print $4}')" -gt 4194304
case "$phase" in
mobile)
    : "${MUSIA_IPHONE_UDID:?Existing stopped Musia iPhone}"
    : "${MUSIA_IPAD_UDID:?Existing stopped Musia iPad}"
    MUSIA_QA_DERIVED_DATA="${MUSIA_QA_DERIVED_DATA:-$out/build}" MUSIA_SIMULATOR_UDID="$MUSIA_IPHONE_UDID" \
      bash "$0" iphone "$out/iphone"
    MUSIA_QA_DERIVED_DATA="${MUSIA_QA_DERIVED_DATA:-$out/build}" MUSIA_SIMULATOR_UDID="$MUSIA_IPAD_UDID" \
      bash "$0" ipad "$out/ipad"
    exit
    ;;
headless)
    swift test --package-path apps/ios --jobs 2 > "$out/core.log" 2>&1
    xcodebuild -project apps/macos/Musia.xcodeproj -scheme Musia \
      -configuration Debug -destination 'platform=macOS' \
      -derivedDataPath "$PWD/DerivedData" -jobs 1 OTHER_SWIFT_FLAGS=-j1 \
      CODE_SIGNING_ALLOWED=NO build > "$out/mac-build.log" 2>&1
    exit
    ;;
core)
    swift test --package-path apps/ios --jobs 2 > "$out/core.log" 2>&1
    exit
    ;;
mac)
    mac_args=( -project apps/macos/Musia.xcodeproj -scheme Musia \
      -configuration Debug -destination 'platform=macOS' -derivedDataPath "$out/build" \
      -jobs 2 -parallel-testing-enabled NO \
      OTHER_SWIFT_FLAGS=-j2 CODE_SIGN_IDENTITY=- \
      MUSIA_MAC_BUNDLE_PREFIX=art.lazying.musia.compatibilityqa \
      MUSIA_DEBUG_PROFILE= MUSIA_MAC_PROFILE= PROVISIONING_PROFILE_SPECIFIER= \
      ENABLE_HARDENED_RUNTIME=NO )
    bounded 900 xcodebuild build-for-testing "${mac_args[@]}" > "$out/mac-build.log" 2>&1
    /usr/bin/python3 tools/store/verify_mac_qa_bundles.py \
      "$out/build/Build/Products/Debug/Musia.app" > "$out/mac-identity.json"
    bounded 600 xcodebuild test-without-building "${mac_args[@]}" \
      -resultBundlePath "$out/mac.xcresult" \
      -only-testing:MusiaMacTests/MacPlaybackTests \
      -test-timeouts-enabled YES -maximum-test-execution-time-allowance 120 \
      > "$out/mac.log" 2>&1
    exit
    ;;
iphone|ipad) ;;
*) exit 64 ;;
esac
candidate="${MUSIA_SIMULATOR_UDID:?Use the existing stopped Musia simulator}"
xcrun simctl list devices available --json | /usr/bin/python3 -c '
import json,sys
rows=[d for ds in json.load(sys.stdin)["devices"].values() for d in ds if d["udid"]==sys.argv[1]]
assert len(rows)==1 and rows[0]["name"].startswith("Musia-") and rows[0]["state"]=="Shutdown"
' "$candidate"
device="$candidate"
xcrun simctl boot "$device"
bounded 120 xcrun simctl bootstatus "$device" -b > "$out/boot.log" 2>&1
tests=(
  -only-testing:MusiaUITests/PracticeSmokeTests/testComposerSurvivesRotationAndBackground
  -only-testing:MusiaUITests/PracticeSmokeTests/testStagePlaybackSurvivesRotationWithLargeText
  -only-testing:MusiaUITests/PracticeSmokeTests/testMiniPlayerNavigationWithLargeText
)
if [[ "${MUSIA_QA_CAPTURE_ONLY:-0}" != 1 ]]; then
    tests+=(
      -only-testing:MusiaTests
      -only-testing:MusiaUITests/PracticeSmokeTests/testBeginnerPracticeAndSettings
      -only-testing:MusiaUITests/PracticeSmokeTests/testSimpleCreatorComposer
      -only-testing:MusiaUITests/PracticeSmokeTests/testStageLayoutAndPracticeSwitch
    )
fi
status=0
bounded 900 xcodebuild test -project apps/ios/Musia.xcodeproj -scheme Musia \
  -configuration Debug -destination "platform=iOS Simulator,id=$device" \
  -derivedDataPath "${MUSIA_QA_DERIVED_DATA:-$out/build}" -resultBundlePath "$out/ui.xcresult" \
  -jobs 2 -parallel-testing-enabled NO -collect-test-diagnostics never \
  -test-timeouts-enabled YES -maximum-test-execution-time-allowance 180 \
  "${tests[@]}" \
  CODE_SIGNING_ALLOWED=YES CODE_SIGN_IDENTITY=- ONLY_ACTIVE_ARCH=YES \
  OTHER_SWIFT_FLAGS=-j2 COMPILER_INDEX_STORE_ENABLE=NO > "$out/ui.log" 2>&1 || status=$?
if [[ -d "$out/ui.xcresult" ]]; then
    bounded 120 xcrun xcresulttool export attachments --path "$out/ui.xcresult" \
      --output-path "$out/attachments" > "$out/export.log" 2>&1
fi
exit "$status"
