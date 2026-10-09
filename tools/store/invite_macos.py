#!/usr/bin/env python3
"""Attach one already-uploaded, VALID Musia Mac build to the existing owner group.

Default: GET-only plan, no journal writes. --confirm permits one build attachment;
--readback is GET-only and saves reconciliation evidence. Neither mode uploads,
creates groups/testers, resends invitations, or changes formal reviews.

Supply the original PKG, its SHA-256, marketing version, build number, and the
canonical macos-uploads/<sha256>/upload-accepted.json from upload_macos.py.
After an uncertain POST, reuse these inputs with --readback. A journaled POST
is never automatically retried, even with --confirm.
"""
import argparse
import contextlib
import hashlib
import json
from pathlib import Path
import re
import sys

import storelib as s
from musia_store import apple_owner_tester


def operation_path(sha256):
    s.require(isinstance(sha256, str) and re.fullmatch(r"[0-9a-f]{64}", sha256), "Invalid PKG SHA-256")
    return s.RUNTIME / "operations" / ("macos-internal-" + sha256 + ".json")


def check_inputs(package, upload_receipt, sha256, version, build, cfg):
    operation_path(sha256)
    s.require(isinstance(version, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+){0,2}", version), "Invalid marketing version")
    s.require(isinstance(build, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+){0,2}", build), "Invalid build number")
    package = Path(package).expanduser().absolute()
    s.require(package.suffix == ".pkg" and package.is_file() and not package.is_symlink(), "Expected original regular PKG")
    s.require(s.digest(package) == sha256, "Installer checksum mismatch")
    receipt = Path(upload_receipt).expanduser().absolute()
    expected = s.RUNTIME / "macos-uploads" / sha256 / "upload-accepted.json"
    s.require(receipt == expected, "Supply the canonical accepted-upload receipt, not inspection/validation or upload-started")
    upload = s.read_json(s.private_file(receipt))
    fields = {"platform": "MAC_OS", "bundle_id": s.BUNDLE, "version": version,
              "build": build, "package_sha256": sha256}
    s.require(all(upload.get(k) == v for k, v in fields.items()), "Upload receipt identity/version/hash mismatch")
    s.require(bool(upload.get("at")) and upload.get("signer_sha1") == cfg.get("apple_certificate_sha1")
              and bool(cfg.get("apple_certificate_sha1")), "Upload receipt signer or timestamp missing/mismatched")
    s.require(sorted(upload.get("architectures", [])) == ["arm64", "x86_64"], "Upload receipt is not universal")
    return dict(fields, upload_receipt_sha256=s.digest(receipt))


def resource_id(row):
    value = row.get("id")
    s.require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9-]+", value), "Invalid provider resource ID")
    return value


def formal_attachments(api, app_id):
    result = []
    for row in api.rows(f"/v1/apps/{app_id}/appStoreVersions?limit=50"):
        rid = resource_id(row)
        attrs = row["attributes"]
        build = api.request("GET", f"/v1/appStoreVersions/{rid}/build")["data"]
        result.append({"id": rid, "platform": attrs["platform"], "version": attrs["versionString"],
                       "build_id": resource_id(build) if build else None})
    # Review status can progress independently; only compare version/build bindings.
    s.require(len({r["id"] for r in result}) == len(result), "Duplicate formal version resources")
    return sorted(result, key=lambda row: row["id"])


def observe(api, cfg, candidate):
    app = api.app()
    app_id = resource_id(app)
    s.require(app["attributes"].get("bundleId") == s.BUNDLE, "Wrong Musia app")
    builds = s.apple_platform_builds(api, app_id, candidate["build"], "MAC_OS")
    s.require(len(builds) == 1, "Exact Mac build missing or ambiguous; reconcile upload, never reupload here")
    selected = builds[0]
    build_id = resource_id(selected)
    attrs = selected["attributes"]
    s.require(attrs.get("version") == candidate["build"] and attrs.get("processingState") == "VALID"
              and attrs.get("expired") is not True, "Exact Mac build is not VALID/nonexpired")
    owner = api.request("GET", f"/v1/builds/{build_id}/app")["data"]
    s.require(resource_id(owner) == app_id and owner["attributes"].get("bundleId") == s.BUNDLE,
              "Processed build belongs to another app")
    pre = api.request("GET", f"/v1/builds/{build_id}/preReleaseVersion")["data"]["attributes"]
    s.require(pre.get("platform") == "MAC_OS" and pre.get("version") == candidate["version"],
              "Processed Mac platform/marketing version mismatch")
    groups = [g for g in api.rows(f"/v1/apps/{app_id}/betaGroups?limit=200")
              if g["attributes"].get("name") == "Musia Internal"]
    s.require(len(groups) == 1, "Existing Musia Internal group missing or ambiguous; no group creation")
    group = groups[0]
    group_id = resource_id(group)
    s.require(group["attributes"].get("isInternalGroup") is True
              and group["attributes"].get("hasAccessToAllBuilds") is False,
              "Group must be internal without all-build access")
    recipient = cfg.get("self_tester_email", "")
    s.require(isinstance(recipient, str) and "@" in recipient and not any(c in recipient for c in "\r\n"),
              "Protected owner recipient missing/invalid")
    tester = apple_owner_tester(api, app_id, recipient)
    tester_id = resource_id(tester)
    members = api.rows(f"/v1/betaGroups/{group_id}/relationships/betaTesters?limit=200")
    s.require(tester_id in {resource_id(r) for r in members}, "Verified existing owner is not in Musia Internal; no tester changes")
    path = f"/v1/betaGroups/{group_id}/relationships/builds"
    attached = build_id in {resource_id(r) for r in api.rows(path + "?limit=200")}
    detail = api.request("GET", f"/v1/builds/{build_id}/buildBetaDetail")["data"]["attributes"]
    state = detail.get("internalBuildState")
    s.require(isinstance(state, str) and bool(state), "Internal beta state missing")
    return {"identity": dict(candidate, app_id=app_id, build_id=build_id, group_id=group_id, tester_id=tester_id),
            "attached": attached, "internal_state": state, "formal": formal_attachments(api, app_id)}


def result(view, *, attempted=False, prior=False, preserved=True):
    identity = view["identity"]
    available = view["attached"] and view["internal_state"] == "IN_BETA_TESTING" and preserved
    if not preserved:
        state = "formal_attachment_changed_readback_required"
    elif available:
        state = "available_to_internal_owner"
    elif view["attached"]:
        state = "attached_availability_pending"
    elif prior:
        state = "attachment_unconfirmed_readback_required"
    else:
        state = "attachment_plan_only"
    return {"at": s.now(), "state": state, "platform": "MAC_OS", "bundle_id": s.BUNDLE,
            "version": identity["version"], "build": identity["build"], "package_sha256": identity["package_sha256"],
            "build_id": identity["build_id"], "processing": "VALID", "internal_state": view["internal_state"],
            "in_internal_group": view["attached"], "owner_membership_verified": True,
            "available": available, "would_attach": not view["attached"] and not prior and preserved,
            "post_attempted_this_run": attempted, "prior_attempt": prior,
            "formal_attachments_preserved": preserved, "email_delivery": "not verified; no invitation or resend requested"}


def invite(package, upload_receipt, sha256, version, build, *, confirm=False, readback=False):
    s.require(not (confirm and readback), "Choose confirm or readback, not both")
    # Share the existing iOS invitation lock; dry runs do not write lock/journal files.
    with s.lock("apple-invite") if confirm or readback else contextlib.nullcontext():
        cfg = s.config()
        candidate = check_inputs(package, upload_receipt, sha256, version, build, cfg)
        api = s.Apple(cfg)
        view = observe(api, cfg, candidate)
        path = operation_path(sha256)
        previous = s.read_json(s.private_file(path)) if path.exists() else None
        if previous is not None:
            s.require(previous.get("identity") == view["identity"] and isinstance(previous.get("formal_before"), list),
                      "Existing attachment journal identity changed; manual reconciliation required")
        operation = "musia-internal-builds-" + view["identity"]["build_id"]
        provider_path = s.RUNTIME / "operations" / (hashlib.sha256(operation.encode()).hexdigest() + ".json")
        legacy = s.read_json(s.private_file(provider_path)) if provider_path.exists() else None
        relation = f"/v1/betaGroups/{view['identity']['group_id']}/relationships/builds"
        if legacy is not None:
            s.require(legacy.get("operation") == operation and legacy.get("state") in {"started", "accepted", "rejected"}
                      and legacy.get("path", relation) == relation, "Existing provider journal mismatch; do not retry")
        prior = previous is not None or legacy is not None
        baseline = previous["formal_before"] if previous else view["formal"]
        preserved = view["formal"] == baseline
        record = previous or {"schema": 1, "identity": view["identity"], "formal_before": baseline,
                              "operation": operation, "created_at": s.now()}
        attempted = False
        if confirm and not prior and not view["attached"]:
            # Persist the exact binding before Apple.request writes its own one-shot journal.
            record.update(state="intent", before=view, at=s.now())
            s.write_private(path, record)
            attempted = prior = True
            try:
                api.request("POST", relation, {"data": [{"type": "builds", "id": view["identity"]["build_id"]}]},
                            operation=operation)
                record["post_outcome"] = "accepted_readback_required"
            except Exception:
                # No raw provider exceptions: they can contain private response/credential data.
                record["post_outcome"] = "unknown_or_rejected_readback_required"
            record.update(state="readback_required", at=s.now())
            s.write_private(path, record)
            try:
                fresh = observe(api, cfg, candidate)
                s.require(fresh["identity"] == view["identity"], "Attachment identity changed during readback")
            except Exception:
                record["readback_error"] = "Provider readback failed; reuse exact inputs with --readback; no POST retry"
                s.write_private(path, record)
                raise s.GuardError(record["readback_error"]) from None
            view = fresh
            preserved = view["formal"] == baseline
        outcome = result(view, attempted=attempted, prior=prior, preserved=preserved)
        if readback and outcome["state"] == "attachment_plan_only":
            outcome.update(state="not_attached", would_attach=False)
        if confirm or readback:
            if prior:
                record.update(state=outcome["state"], at=s.now(), readback=view, result=outcome)
                s.write_private(path, record)
            s.write_private(s.RUNTIME / "macos-internal" / sha256 / "readback.json", outcome)
        return outcome


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("package", type=Path)
    parser.add_argument("--upload-receipt", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--build", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--confirm", action="store_true", help="Attach once after fresh guards; never retry a journaled POST")
    mode.add_argument("--readback", action="store_true", help="GET-only reconciliation; save private evidence")
    args = parser.parse_args(argv)
    try:
        outcome = invite(args.package, args.upload_receipt, args.sha256, args.version, args.build,
                         confirm=args.confirm, readback=args.readback)
        print(json.dumps(outcome, indent=2))
        pending = not outcome["available"] and (args.confirm or args.readback or outcome["prior_attempt"])
        return 2 if pending else 0
    except (s.GuardError, OSError, ValueError, KeyError, TypeError, ImportError) as error:
        print(str(error) if isinstance(error, s.GuardError) else "Local input/provider runtime invalid; no retry authorized",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
