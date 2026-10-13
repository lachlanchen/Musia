#!/usr/bin/env bash
# Source-based native QA. This never uploads or replaces a TestFlight install.
set -euo pipefail
cd "${MUSIA_ROOT:?Set the isolated Musia source checkout}"
device="${1:?Pass the existing stopped Musia simulator UDID}"
out="${2:?Pass a fresh private output directory}"
if pgrep -x xcodebuild >/dev/null || pgrep -x swift-frontend >/dev/null; then
    printf '%s\n' 'Peer Apple build active; retry after it completes.'
    exit 75
fi
test ! -e "$out"
mkdir -m 700 -p "$out"
df -h /Users
memory_pressure -Q
test "$(df -k /Users | awk 'NR==2 {print $4}')" -gt 4194304
xcrun simctl list devices available --json | /usr/bin/python3 -c '
import json,sys
rows=[d for ds in json.load(sys.stdin)["devices"].values() for d in ds if d["udid"]==sys.argv[1]]
assert len(rows)==1 and rows[0]["name"].startswith("Musia-") and rows[0]["state"]=="Shutdown"
' "$device"
swift test --package-path apps/ios --jobs 2 > "$out/core-tests.log" 2>&1
xcodebuild -project apps/macos/Musia.xcodeproj -scheme Musia \
  -configuration Debug -destination 'platform=macOS' \
  -derivedDataPath "$out/mac" -jobs 2 CODE_SIGN_IDENTITY=- \
  CODE_SIGNING_ALLOWED=NO build > "$out/mac-build.log" 2>&1
trap 'xcrun simctl shutdown "$device" >/dev/null 2>&1 || true' EXIT
xcrun simctl boot "$device"
xcrun simctl bootstatus "$device" -b > "$out/boot.log" 2>&1
status=0
xcodebuild test -project apps/ios/Musia.xcodeproj -scheme Musia \
  -configuration Debug -destination "platform=iOS Simulator,id=$device" \
  -derivedDataPath "$out/ios" -resultBundlePath "$out/practice.xcresult" \
  -jobs 2 -parallel-testing-enabled NO -collect-test-diagnostics never \
  -test-timeouts-enabled YES -maximum-test-execution-time-allowance 180 \
  -only-testing:MusiaUITests/PracticeSmokeTests/testBeginnerPracticeAndSettings \
  -only-testing:MusiaUITests/PracticeSmokeTests/testSimpleCreatorComposer \
  CODE_SIGNING_ALLOWED=YES CODE_SIGN_IDENTITY=- ONLY_ACTIVE_ARCH=YES \
  COMPILER_INDEX_STORE_ENABLE=NO > "$out/ios-test.log" 2>&1 || status=$?
if [[ -d "$out/practice.xcresult" ]]; then
    xcrun xcresulttool export attachments --path "$out/practice.xcresult" \
      --output-path "$out/attachments" > "$out/export.log" 2>&1
fi
exit "$status"
