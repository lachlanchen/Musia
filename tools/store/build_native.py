"""Explicit native builds and signature/identity inspection. Never runs on import."""
import base64
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from storelib import BUNDLE, ROOT, RUNTIME, TEAM, config, digest, lock, now, private_dir, private_file, release, require, run, source_sha, write_private

WATCH_BUNDLE = BUNDLE + ".watchkitapp"


def includes_watch(r):
    # Build 8 remains inspectable while the first companion release is prepared.
    require(str(r["ios_build"]).isdigit(), "Invalid iOS build selector")
    return int(r["ios_build"]) >= 9


def android_config(cfg):
    home = Path(cfg["java_home"])
    require(all((home / "bin" / tool).is_file() and os.access(home / "bin" / tool, os.X_OK)
                for tool in ("java", "javac", "keytool", "jarsigner")),
            "java_home must reference a complete shared JDK, not a JRE")
    sdk = Path(cfg["android_sdk"])
    bundletool = Path(cfg.get("bundletool_jar") or "/missing-bundletool")
    require(bundletool.is_file(), "Configure an existing verified bundletool_jar before a signed build")
    require(digest(bundletool) == cfg.get("bundletool_sha256"), "bundletool checksum not pinned/mismatched")
    env = dict(os.environ, JAVA_HOME=str(home), ANDROID_HOME=str(sdk), ANDROID_SDK_ROOT=str(sdk))
    return home, sdk, bundletool, env


def android_manifest(xml):
    manifest = ET.fromstring(xml)
    ns = "{http://schemas.android.com/apk/res/android}"
    r = release()
    require(manifest.get("package") == BUNDLE and manifest.get(ns + "versionName") == r["version"]
            and manifest.get(ns + "versionCode") == str(r["android_version_code"]), "AAB identity/version mismatch")
    permissions = {node.get(ns + "name") for node in manifest.findall("uses-permission")}
    forbidden = {"android.permission.RECORD_AUDIO", "android.permission.CAMERA", "android.permission.READ_CONTACTS",
                 "android.permission.GET_ACCOUNTS", "com.google.android.gms.permission.AD_ID"}
    require(not permissions & forbidden, "Unexpected permission for initial Musia scope")
    application = manifest.find("application")
    require(application is not None and application.get(ns + "debuggable", "false") == "false", "Release is debuggable")
    return permissions


def inspect_android(artifact, cfg):
    home, sdk, bundletool, env = android_config(cfg)
    xml = run([home / "bin/java", "-jar", bundletool, "dump", "manifest", "--bundle=" + str(artifact)], env=env)
    permissions = android_manifest(xml)
    verified = run([home / "bin/jarsigner", "-verify", artifact], env=dict(env, LC_ALL="C"))
    require(b"jar verified." in verified, "Bundle signature not verified")
    certs = run([home / "bin/keytool", "-printcert", "-jarfile", artifact, "-rfc"], env=env)
    certificates = re.findall(rb"-----BEGIN CERTIFICATE-----(.*?)-----END CERTIFICATE-----", certs, re.S)
    expected = json.loads(private_file(RUNTIME / "android/key.json").read_text())["certificate_sha256"]
    require(len(certificates) == 1 and hashlib.sha256(base64.b64decode(certificates[0])).hexdigest() == expected,
            "Bundle is not signed by the Musia-specific upload key")
    return {"permissions": sorted(permissions), "certificate_sha256": expected}


def decode_profile(path):
    if sys.platform == "darwin":
        data = run(["/usr/bin/security", "cms", "-D", "-i", path])
    else:
        data = run(["openssl", "cms", "-verify", "-inform", "DER", "-in", path, "-noverify"])
    return plistlib.loads(data)


def check_profile(profile, cfg, bundle_id=BUNDLE):
    import datetime as dt
    require(bundle_id in {BUNDLE, WATCH_BUNDLE}, "Unexpected provisioning bundle")
    require(profile.get("TeamIdentifier") == [TEAM], "Provisioning team mismatch")
    ent = profile["Entitlements"]
    require(ent.get("application-identifier") == TEAM + "." + bundle_id, "Provisioning is not Musia-specific")
    require(ent.get("get-task-allow") is False and not profile.get("ProvisionedDevices")
            and not profile.get("ProvisionsAllDevices"), "Not App Store distribution provisioning")
    expiry = profile["ExpirationDate"].replace(tzinfo=dt.timezone.utc)
    require(expiry > dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=7), "Provisioning is expired/near expiry")
    hashes = [hashlib.sha1(c).hexdigest().upper() for c in profile["DeveloperCertificates"]]
    require(hashes == [cfg["apple_certificate_sha1"]], "Provisioning certificate mismatch")
    return profile


def ios_profiles(cfg, r):
    keys = {BUNDLE: "apple_profile_path"}
    if includes_watch(r):
        keys[WATCH_BUNDLE] = "apple_watch_profile_path"
    profiles = {}
    for bundle, key in keys.items():
        require(bool(cfg.get(key)), "Configure the approved " + key + "; no automatic provisioning")
        path = private_file(cfg[key])
        profiles[bundle] = (path, check_profile(decode_profile(path), cfg, bundle))
    return profiles


def check_watch_info(info, r):
    require(info.get("CFBundleIdentifier") == WATCH_BUNDLE
            and info.get("CFBundleShortVersionString") == r["version"]
            and info.get("CFBundleVersion") == str(r["ios_build"]), "Watch identity/version mismatch")
    require(info.get("WKApplication") is True and info.get("WKCompanionAppBundleIdentifier") == BUNDLE
            and info.get("WKRunsIndependentlyOfCompanionApp") is False
            and not info.get("WKWatchOnly") and "NSExtension" not in info, "Expected a single-target iPhone companion")
    require(info.get("UIDeviceFamily") == [4] and info.get("CFBundleSupportedPlatforms") == ["WatchOS"]
            and info.get("MinimumOSVersion") in {"10.0", "10.0.0"}, "Unexpected watchOS platform/deployment target")
    require(not any(key.endswith("UsageDescription") for key in info)
            and not info.get("UIBackgroundModes") and not info.get("WKBackgroundModes")
            and "NSAppTransportSecurity" not in info, "Unexpected Watch permission/background capability")


def embedded_watch(app, r):
    expected = app / "Watch/MusiaWatch.app"
    nested = set(app.rglob("*.app"))
    require(nested == ({expected} if includes_watch(r) else set())
            and not list(app.rglob("*.appex")), "Unexpected embedded app/extension")
    if not includes_watch(r):
        return None
    require(expected.is_dir() and not list(expected.rglob("MusiaCore.framework")),
            "Watch must not embed the iOS MusiaCore framework")
    info = plistlib.loads((expected / "Info.plist").read_bytes())
    check_watch_info(info, r)
    executable = info.get("CFBundleExecutable")
    require(isinstance(executable, str) and bool(executable) and Path(executable).name == executable
            and (expected / executable).is_file(), "Watch executable missing/invalid")
    return expected


def inspect_ios_signature(app, cfg, bundle_id, certificate_prefix):
    run(["/usr/bin/codesign", "--verify", "--deep", "--strict", app])
    entitlements = plistlib.loads(run(["/usr/bin/codesign", "-d", "--entitlements", ":-", app]))
    require(entitlements.get("application-identifier") == TEAM + "." + bundle_id
            and entitlements.get("com.apple.developer.team-identifier") == TEAM
            and not entitlements.get("get-task-allow", False), "Actual signed entitlements mismatch")
    if bundle_id == WATCH_BUNDLE:
        require(set(entitlements) <= {"application-identifier", "com.apple.developer.team-identifier",
                                      "get-task-allow", "beta-reports-active", "keychain-access-groups"}
                and set(entitlements.get("keychain-access-groups", [])) <= {TEAM + "." + WATCH_BUNDLE},
                "Unexpected Watch signing capability")
    profile = check_profile(decode_profile(app / "embedded.mobileprovision"), cfg, bundle_id)
    # Check each actual signing leaf, not just certificates permitted by its profile.
    run(["/usr/bin/codesign", "-d", "--extract-certificates=" + str(certificate_prefix), app])
    require(hashlib.sha1(Path(str(certificate_prefix) + "0").read_bytes()).hexdigest().upper()
            == cfg["apple_certificate_sha1"], "IPA signer differs from the pinned account distribution certificate")
    return {"profile_uuid": profile["UUID"], "certificate_sha1": cfg["apple_certificate_sha1"]}


def inspect_ios(artifact, cfg):
    require(sys.platform == "darwin", "IPA signature inspection requires the Mac")
    with tempfile.TemporaryDirectory(prefix="musia-inspect-") as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(artifact) as archive:
            entries = archive.infolist()
            require(sum(x.file_size for x in entries) < 2_000_000_000, "IPA unexpectedly large")
            for entry in entries:
                p = Path(entry.filename)
                require(not p.is_absolute() and ".." not in p.parts
                        and (entry.external_attr >> 16) & 0o170000 != 0o120000, "Unsafe IPA member")
            archive.extractall(root)
        apps = list((root / "Payload").glob("*.app"))
        require(len(apps) == 1, "Expected one iOS app")
        app = apps[0]
        info = plistlib.loads((app / "Info.plist").read_bytes())
        r = release()
        require(info.get("CFBundleIdentifier") == BUNDLE and info.get("CFBundleShortVersionString") == r["version"]
                and info.get("CFBundleVersion") == r["ios_build"], "IPA identity/version mismatch")
        require(not any(k in info for k in ("NSMicrophoneUsageDescription", "NSCameraUsageDescription",
                                           "NSSpeechRecognitionUsageDescription", "NSPhotoLibraryUsageDescription")),
                "Unexpected capture permission")
        require(set(info.get("UIBackgroundModes", [])) <= {"audio"}, "Unexpected background capability")
        watch = embedded_watch(app, r)
        identity = inspect_ios_signature(app, cfg, BUNDLE, root / "signer")
        if watch is not None:
            identity["watch"] = dict(inspect_ios_signature(watch, cfg, WATCH_BUNDLE, root / "watch-signer"),
                                     bundle_id=WATCH_BUNDLE, version=r["version"], build_number=str(r["ios_build"]))
        return identity


def build(platform, execute=False):
    cfg, r = config(), release()
    require(platform in {"ios", "android"}, "Unknown platform")
    before = source_sha(platform)
    number = r["ios_build"] if platform == "ios" else str(r["android_version_code"])
    output = RUNTIME / "artifacts" / f"{platform}-{r['version']}-{number}-{before[:12]}"
    if not execute:
        return {"state": "plan_only", "platform": platform, "source_sha256": before,
                "output": str(output), "requires": "exclusive worker coordination, protected signing, then --execute-build"}
    if platform == "android":
        android_config(cfg)
    require(not output.exists(), "Build output exists; preserve it and explicitly reconcile before another build")
    with lock("build-" + platform):
        private_dir(output)
        if platform == "android":
            home, sdk, _, env = android_config(cfg)
            properties = private_file(RUNTIME / "android/signing.properties")
            env["MUSIA_SIGNING_PROPERTIES"] = str(properties)
            run([ROOT / "apps/android/gradlew", "--no-daemon", "--max-workers=2", ":app:testReleaseUnitTest",
                 ":app:lintRelease", ":app:assembleRelease", ":app:bundleRelease"],
                cwd=ROOT / "apps/android", env=env, log=output / "build.log")
            artifact = output / "Musia.aab"
            shutil.copyfile(ROOT / "apps/android/app/build/outputs/bundle/release/app-release.aab", artifact)
            os.chmod(artifact, 0o600)
            identity = inspect_android(artifact, cfg)
            apk = output / "Musia-qa.apk"
            shutil.copyfile(ROOT / "apps/android/app/build/outputs/apk/release/app-release.apk", apk)
            os.chmod(apk, 0o600)
            apk_result = run([sdk / "build-tools" / cfg["android_build_tools"] / "apksigner",
                              "verify", "--print-certs", apk], env=env).decode()
            match = re.findall(r"Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]+)", apk_result)
            require(match == [identity["certificate_sha256"]], "QA APK signer mismatch")
            android_manifest(run([sdk / "cmdline-tools/latest/bin/apkanalyzer", "manifest", "print", apk], env=env))
            identity.update(qa_apk=str(apk), qa_apk_sha256=digest(apk))
        else:
            require(sys.platform == "darwin", "Build iOS on echomind-kvm-macos only")
            profiles = ios_profiles(cfg, r)
            keychain = private_file(cfg["apple_keychain"])
            identities = run(["/usr/bin/security", "find-identity", "-v", "-p", "codesigning", keychain]).decode()
            require(cfg["apple_certificate_sha1"] in identities, "Configured signing identity unavailable; no shared keychain changes made")
            for directory in (Path.home() / "Library/MobileDevice/Provisioning Profiles",
                              Path.home() / "Library/Developer/Xcode/UserData/Provisioning Profiles"):
                directory.mkdir(parents=True, exist_ok=True)
                for profile_path, profile in profiles.values():
                    target = directory / (profile["UUID"] + ".mobileprovision")
                    require(not target.exists() or digest(target) == digest(profile_path), "Existing profile differs; no overwrite")
                    if not target.exists():
                        shutil.copyfile(profile_path, target)
                        os.chmod(target, 0o600)
            env = dict(os.environ, DEVELOPER_DIR=cfg["xcode_developer_dir"])
            archive = output / "Musia.xcarchive"
            signing = ["MUSIA_APP_PROFILE=" + profiles[BUNDLE][1]["Name"]]
            if WATCH_BUNDLE in profiles:
                signing.append("MUSIA_WATCH_PROFILE=" + profiles[WATCH_BUNDLE][1]["Name"])
            run(["/usr/bin/xcodebuild", "-project", ROOT / "apps/ios/Musia.xcodeproj", "-scheme", "Musia",
                 "-configuration", "Release", "-destination", "generic/platform=iOS", "-jobs", "2",
                 "-derivedDataPath", output / "DerivedData", "-archivePath", archive,
                 "DEVELOPMENT_TEAM=" + TEAM, "CODE_SIGN_STYLE=Manual", "CODE_SIGN_IDENTITY=" + cfg["apple_certificate_sha1"],
                 *signing, "MARKETING_VERSION=" + r["version"],
                 "CURRENT_PROJECT_VERSION=" + number, "OTHER_CODE_SIGN_FLAGS=--keychain " + str(keychain), "archive"],
                cwd=ROOT, env=env, log=output / "archive.log")
            options = {"method": "app-store-connect", "teamID": TEAM, "signingStyle": "manual",
                       "signingCertificate": cfg["apple_certificate_sha1"],
                       "provisioningProfiles": {bundle: profile["Name"] for bundle, (_, profile) in profiles.items()},
                       "manageAppVersionAndBuildNumber": False}
            write_private(output / "ExportOptions.plist", plistlib.dumps(options))
            run(["/usr/bin/xcodebuild", "-exportArchive", "-archivePath", archive, "-exportOptionsPlist",
                 output / "ExportOptions.plist", "-exportPath", output / "export"], env=env, log=output / "export.log")
            ipas = list((output / "export").glob("*.ipa"))
            require(len(ipas) == 1, "Expected one exported IPA")
            artifact = ipas[0]
            os.chmod(artifact, 0o600)
            identity = inspect_ios(artifact, cfg)
        require(source_sha(platform) == before, "Native source changed during build; do not upload")
        receipt = {"schema": 1, "state": "signed", "platform": platform, "bundle_id": BUNDLE, "at": now(),
                   "version": r["version"], "build_number": number, "source_sha256": before,
                   "artifact": str(artifact.relative_to(output)), "artifact_sha256": digest(artifact), "identity": identity}
        write_private(output / "build.json", receipt)
        return {"state": "signed_not_qualified", "receipt": str(output / "build.json")}
