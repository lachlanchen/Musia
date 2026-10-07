#!/usr/bin/env bash
# Run on the authorized Xcode host; never changes shared signing settings.
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
root="${MUSIA_ROOT:-$HOME/Projects/Musia}"
release="${MUSIA_MAC_RELEASE:-0.1.3-6}"
out="$root/store/.runtime/macos-$release"
keychain="${MUSIA_KEYCHAIN:-$HOME/Library/Keychains/landn-release.keychain-db}"
passfile="${MUSIA_KEYCHAIN_PASSWORD_FILE:-$HOME/.config/echomind/apple/release-keychain.pass}"
profile="${MUSIA_MAC_PROFILE_PATH:?Set MUSIA_MAC_PROFILE_PATH to the private Musia Mac App Store profile}"
test ! -e "$out/Musia.xcarchive"
umask 077
mkdir -p "$out"
# Keep the enclosing runtime private, but installed bundle files must be readable.
umask 022
password=$(tr -d '\r\n' < "$passfile")
security unlock-keychain -p "$password" "$keychain"
unset password
profile_xml=$(security cms -D -i "$profile")
uuid=$(printf '%s' "$profile_xml" | plutil -extract UUID raw -o - -)
name=$(printf '%s' "$profile_xml" | plutil -extract Name raw -o - -)
identifier=$(printf '%s' "$profile_xml" | plutil -extract 'Entitlements.com\.apple\.application-identifier' raw -o - -)
test "$name" = 'Musia Mac App Store'
test "$identifier" = 'Q8M2S2FY77.art.lazying.musia'
unset profile_xml
for directory in "$HOME/Library/MobileDevice/Provisioning Profiles" "$HOME/Library/Developer/Xcode/UserData/Provisioning Profiles"; do
    mkdir -p "$directory"
    cp "$profile" "$directory/$uuid.provisionprofile"
done
cd "$root"
xcodebuild -project apps/macos/Musia.xcodeproj -scheme Musia -configuration Release \
    -destination 'generic/platform=macOS' -archivePath "$out/Musia.xcarchive" \
    -derivedDataPath "$out/DerivedData" -jobs "${MUSIA_BUILD_JOBS:-2}" archive \
    ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO COMPILER_INDEX_STORE_ENABLE=NO \
    MUSIA_MAC_PROFILE="$name" "OTHER_CODE_SIGN_FLAGS=--keychain $keychain" > "$out/archive.log" 2>&1
app="$out/Musia.xcarchive/Products/Applications/Musia.app"
version=$(plutil -extract CFBundleShortVersionString raw -o - "$app/Contents/Info.plist")
build=$(plutil -extract CFBundleVersion raw -o - "$app/Contents/Info.plist")
test "$version-$build" = "$release"
test "$(plutil -extract CFBundleIdentifier raw -o - "$app/Contents/Info.plist")" = art.lazying.musia
chmod -R a+rX "$app"
lipo "$app/Contents/MacOS/Musia" -verify_arch arm64 x86_64
codesign --verify --deep --strict "$app"
swift tools/store/inspect_macos_icon.swift "$app" "$out/icon-evidence" > "$out/icon-inspection.json"
# The shared keychain can auto-lock during the universal archive.
password=$(tr -d '\r\n' < "$passfile")
security unlock-keychain -p "$password" "$keychain"
unset password
mkdir -p "$out/export"
productbuild --component "$app" /Applications \
    --sign '3rd Party Mac Developer Installer: LazyingArt LLC (Q8M2S2FY77)' \
    --keychain "$keychain" "$out/export/Musia.pkg" > "$out/export.log" 2>&1
pkgutil --check-signature "$out/export/Musia.pkg" > "$out/installer-signature.txt"
shasum -a 256 "$out/export/Musia.pkg"
