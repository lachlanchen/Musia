#!/usr/bin/env python3
"""Musia store preparation. No pricing, legal attestations or formal submission."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import urllib.parse

from build_native import build, check_profile, decode_profile, inspect_android, inspect_ios
from storelib import Apple, BUNDLE, GuardError, RUNTIME, TEAM, check_qa, config, digest, lock, now, private_dir, private_file, read_json, release, require, run, snapshot_artifact, write_private


def apple_inventory():
    result = Apple().inventory()
    write_private(RUNTIME / "apple-inventory.json", result)
    return {"at": result["at"], "bundle_id": BUNDLE, "app_ids": [x["id"] for x in result["apps"]],
            "bundle_id_resources": [x["id"] for x in result["bundle_ids"]]}


def apple_setup(confirm):
    cfg, api = config(), Apple()
    inventory = api.inventory()
    certificate = api.request("GET", "/v1/certificates/" + cfg["apple_certificate_id"])["data"]
    attributes = certificate["attributes"]
    cert = base64.b64decode(attributes["certificateContent"])
    require(attributes["certificateType"] in {"DISTRIBUTION", "IOS_DISTRIBUTION"}
            and hashlib.sha1(cert).hexdigest().upper() == cfg["apple_certificate_sha1"], "Account certificate pin mismatch")
    if not confirm:
        return {"state": "setup_plan_only", "register_bundle": not inventory["bundle_ids"],
                "profile_name": "Musia App Store", "creates_app_record": False}
    with lock("apple-setup"):
        if inventory["bundle_ids"]:
            bundle = inventory["bundle_ids"][0]
        else:
            bundle = api.request("POST", "/v1/bundleIds", {"data": {"type": "bundleIds", "attributes": {
                "identifier": BUNDLE, "name": "Musia", "platform": "IOS"}}}, operation="register-musia-bundle")["data"]
        require(bundle["attributes"]["identifier"] == BUNDLE, "Created bundle identity mismatch")
        profiles = api.rows(f"/v1/bundleIds/{bundle['id']}/profiles?limit=200")
        matches = [p for p in profiles if p["attributes"]["name"] == "Musia App Store"
                   and p["attributes"]["profileType"] == "IOS_APP_STORE" and p["attributes"]["profileState"] == "ACTIVE"]
        require(len(matches) <= 1, "Multiple Musia profiles; review rather than replace")
        if matches:
            profile = api.request("GET", "/v1/profiles/" + matches[0]["id"])["data"]
        else:
            profile = api.request("POST", "/v1/profiles", {"data": {"type": "profiles", "attributes": {
                "name": "Musia App Store", "profileType": "IOS_APP_STORE"}, "relationships": {
                    "bundleId": {"data": {"type": "bundleIds", "id": bundle["id"]}},
                    "certificates": {"data": [{"type": "certificates", "id": certificate["id"]}]}}}},
                                  operation="create-musia-app-store-profile")["data"]
        target = RUNTIME / "apple/Musia_App_Store.mobileprovision"
        raw = base64.b64decode(profile["attributes"]["profileContent"])
        require(not target.exists() or target.read_bytes() == raw, "Existing profile differs; no overwrite")
        write_private(target, raw)
        decoded = check_profile(decode_profile(target), cfg)
        result = {"at": now(), "bundle_id": BUNDLE, "bundle_resource_id": bundle["id"], "profile_id": profile["id"],
                  "profile_uuid": decoded["UUID"], "profile_sha256": digest(target), "team": TEAM,
                  "certificate_sha1": cfg["apple_certificate_sha1"], "app_record_created": False}
        write_private(RUNTIME / "apple/setup.json", result)
        return result


def android_key(confirm):
    cfg = config()
    directory = RUNTIME / "android"
    receipt = directory / "key.json"
    if receipt.exists():
        value = read_json(private_file(receipt))
        require(value["bundle_id"] == BUNDLE and digest(private_file(directory / "upload-keystore.p12")) == value["keystore_sha256"],
                "Existing Musia key receipt mismatch")
        return {"state": "existing_key_preserved", "certificate_sha256": value["certificate_sha256"]}
    if not confirm:
        return {"state": "key_plan_only", "alias": "musia-upload", "reuse_other_app_key": False}
    with lock("android-key"):
        private_dir(directory)
        key = directory / "upload-keystore.p12"
        password_path = directory / "keystore.password"
        require(not key.exists() and not password_path.exists(), "Partial key setup exists; no overwrite")
        password = secrets.token_urlsafe(40)
        write_private(password_path, (password + "\n").encode())
        keytool = Path(cfg["java_home"]) / "bin/keytool"
        run([keytool, "-genkeypair", "-keystore", key, "-storetype", "PKCS12", "-storepass:file", password_path,
             "-alias", "musia-upload", "-keyalg", "RSA", "-keysize", "3072", "-validity", "10000",
             "-dname", "CN=Musia Upload, O=LazyingArt LLC", "-noprompt"], log=directory / "keygen.log")
        os.chmod(key, 0o600)
        cert = run([keytool, "-exportcert", "-keystore", key, "-storepass:file", password_path, "-alias", "musia-upload"])
        write_private(directory / "upload-certificate.der", cert)
        props = f"storeFile={key}\nstorePassword={password}\nkeyAlias=musia-upload\nkeyPassword={password}\n"
        write_private(directory / "signing.properties", props.encode())
        value = {"at": now(), "bundle_id": BUNDLE, "alias": "musia-upload", "keystore_sha256": digest(key),
                 "certificate_sha256": hashlib.sha256(cert).hexdigest()}
        write_private(receipt, value)
        return {"state": "musia_upload_key_created", "certificate_sha256": value["certificate_sha256"]}


def qualified(args):
    require(args.build_receipt and args.qa, "Supply --build-receipt and --qa; never upload untested source")
    candidate = check_qa(Path(args.build_receipt), Path(args.qa))
    cfg = config()
    inspection = inspect_ios if candidate["platform"] == "ios" else inspect_android
    inspection(Path(candidate["artifact"]), cfg)
    return candidate


def upload_apple(args):
    candidate = qualified(args)
    require(candidate["platform"] == "ios", "Wrong candidate platform")
    cfg, api = config(), Apple()
    app = api.app()
    existing = api.rows("/v1/builds?" + urllib.parse.urlencode({"filter[app]": app["id"],
                          "filter[version]": candidate["build_number"], "limit": 200}))
    require(not existing, "Build number already exists; reconcile processing instead of uploading again")
    if not args.confirm_upload:
        return {"state": "qualified_upload_plan", "app_id": app["id"], "sha256": candidate["artifact_sha256"]}
    journal = RUNTIME / "operations" / ("apple-upload-" + candidate["artifact_sha256"] + ".json")
    with lock("apple-upload"):
        require(not journal.exists(), "Upload attempted before; inspect Apple processing before any retry")
        candidate = snapshot_artifact(candidate)
        key = private_file(cfg["asc_key_path"])
        require(key.name == "AuthKey_" + cfg["asc_key_id"] + ".p8", "altool API key filename mismatch")
        env = dict(os.environ, DEVELOPER_DIR=cfg["xcode_developer_dir"], API_PRIVATE_KEYS_DIR=str(key.parent))
        common = ["--type", "ios", "--file", candidate["artifact"], "--apiKey", cfg["asc_key_id"], "--apiIssuer", cfg["asc_issuer"]]
        run(["/usr/bin/xcrun", "altool", "--validate-app", *common], env=env, log=RUNTIME / "apple/validate.log")
        write_private(journal, {"state": "started", "at": now(), "sha256": candidate["artifact_sha256"], "app_id": app["id"]})
        run(["/usr/bin/xcrun", "altool", "--upload-app", *common], env=env, log=RUNTIME / "apple/upload.log")
        write_private(journal, {"state": "upload_accepted_processing_unverified", "at": now(),
                                "sha256": candidate["artifact_sha256"], "app_id": app["id"]})
        return {"state": "upload_accepted_processing_unverified", "submitted_for_review": False}


def invite_apple(args):
    candidate = qualified(args)
    require(candidate["platform"] == "ios", "TestFlight needs an iOS candidate")
    api, cfg = Apple(), config()
    app = api.app()
    journal = RUNTIME / "operations" / ("apple-upload-" + candidate["artifact_sha256"] + ".json")
    upload = read_json(private_file(journal))
    require(upload["state"] == "upload_accepted_processing_unverified" and upload["app_id"] == app["id"],
            "No upload receipt binding this IPA to Musia")
    builds = api.rows("/v1/builds?" + urllib.parse.urlencode({"filter[app]": app["id"], "filter[version]": candidate["build_number"], "limit": 200}))
    require(len(builds) == 1 and builds[0]["attributes"]["processingState"] == "VALID", "Exact build not VALID")
    selected = builds[0]
    owner = api.request("GET", f"/v1/builds/{selected['id']}/app")["data"]
    require(owner["id"] == app["id"] and owner["attributes"]["bundleId"] == BUNDLE, "Processed build belongs to another app")
    prerelease = api.request("GET", f"/v1/builds/{selected['id']}/preReleaseVersion")["data"]
    require(prerelease["attributes"]["version"] == candidate["version"], "Processed marketing version mismatch")
    recipient = cfg.get("self_tester_email", "")
    require("@" in recipient and not any(c in recipient for c in "\r\n"), "Private self-test recipient missing")
    testers = api.rows("/v1/betaTesters?" + urllib.parse.urlencode({"filter[email]": recipient, "limit": 200}))
    require(len(testers) == 1 and testers[0]["attributes"]["email"].casefold() == recipient.casefold(),
            "Expected existing owner tester; do not create account users or guess recipients")
    groups = [g for g in api.rows(f"/v1/apps/{app['id']}/betaGroups?limit=200")
              if g["attributes"]["name"] == "Musia Internal"]
    require(len(groups) <= 1 and all(g["attributes"].get("isInternalGroup")
            and g["attributes"].get("hasAccessToAllBuilds") is False for g in groups), "Unexpected tester group")
    if not args.confirm_invite:
        return {"state": "invite_plan_only", "app_id": app["id"], "build_id": selected["id"], "recipient_count": 1}
    with lock("apple-invite"):
        group = groups[0] if groups else api.request("POST", "/v1/betaGroups", {"data": {"type": "betaGroups", "attributes": {
            "name": "Musia Internal", "isInternalGroup": True, "hasAccessToAllBuilds": False},
            "relationships": {"app": {"data": {"type": "apps", "id": app["id"]}}}}}, operation="create-musia-internal-group")["data"]
        for relation, item in (("builds", selected), ("betaTesters", testers[0])):
            path = f"/v1/betaGroups/{group['id']}/relationships/{relation}"
            attached = {r["id"] for r in api.rows(path + "?limit=200")}
            if item["id"] not in attached:
                api.request("POST", path, {"data": [{"type": relation, "id": item["id"]}]},
                            operation=f"musia-internal-{relation}-{item['id']}")
            require(item["id"] in {r["id"] for r in api.rows(path + "?limit=200")}, "Tester/build attachment not confirmed")
        result = {"at": now(), "state": "owner_added_to_testflight_group", "app_id": app["id"],
                  "build_id": selected["id"], "tester_id": testers[0]["id"], "email": recipient,
                  "email_delivery": "not independently verified; no resend requested"}
        write_private(RUNTIME / "apple/self-test.json", result)
        return {k: v for k, v in result.items() if k not in {"email", "tester_id"}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["inventory-apple", "inventory-play", "setup-apple", "setup-android-key",
                                            "build-ios", "build-android", "qualify", "upload-apple", "upload-play", "invite-self", "invite-play-self"])
    parser.add_argument("--confirm-setup", action="store_true")
    parser.add_argument("--execute-build", action="store_true")
    parser.add_argument("--build-receipt")
    parser.add_argument("--qa")
    parser.add_argument("--confirm-upload", action="store_true")
    parser.add_argument("--confirm-invite", action="store_true")
    args = parser.parse_args()
    release()
    if args.command == "inventory-apple":
        result = apple_inventory()
    elif args.command == "inventory-play":
        from play_console import inventory
        result = inventory()
    elif args.command == "setup-apple":
        result = apple_setup(args.confirm_setup)
    elif args.command == "setup-android-key":
        result = android_key(args.confirm_setup)
    elif args.command.startswith("build-"):
        result = build(args.command.removeprefix("build-"), args.execute_build)
    elif args.command == "qualify":
        value = qualified(args)
        result = {"state": "qualified", "platform": value["platform"], "artifact_sha256": value["artifact_sha256"]}
    elif args.command == "upload-apple":
        result = upload_apple(args)
    elif args.command == "upload-play":
        from play_console import upload
        value = qualified(args)
        require(value["platform"] == "android", "Play needs an Android candidate")
        with lock("play-upload"):
            result = upload(value, args.confirm_upload)
    elif args.command == "invite-play-self":
        from invite_play import invite
        result = invite(qualified(args), args.confirm_invite)
    else:
        result = invite_apple(args)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Arbitrary provider/subprocess errors can contain private response data.
        message = str(error) if isinstance(error, GuardError) else type(error).__name__ + ": check private configuration/evidence"
        print("Musia store: " + message, file=sys.stderr)
        sys.exit(1)
