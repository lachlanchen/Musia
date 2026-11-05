#!/usr/bin/env python3
"""Reconcile and commit one existing Musia internal edit, never upload again."""
import argparse
import json
from pathlib import Path
import play_internal_api as p
import storelib as s


def recover(operation, build, qa, key, handoff, omit_hold=False):
    with s.lock("play-upload"):
        path = s.private_file(operation)
        record = s.read_json(path)
        s.require(path == p.operation_path(record["version_code"]), "Wrong operation")
        s.require(record["bundle_id"] == p.PACKAGE and record["track"] == p.TRACK, "Wrong scope")
        p.recheck(build, qa, record)
        p.coordination(handoff, record)
        key = s.private_file(key)
        s.require(s.digest(key) == record["service_account_sha256"], "Different credential")
        s.require(record["steps"]["upload_bundle"]["state"] == "accepted"
                  and record["steps"]["update_internal"]["state"] == "accepted"
                  and record["steps"]["commit_edit"]["state"] == "unknown", "Not an unresolved commit")
        attempts = record.setdefault("commit_recovery", [])
        if omit_hold:
            s.require(len(attempts) == 1 and attempts[0].get("http_status") == 400
                      and "changesNotSentForReview" in attempts[0].get("response", {}).get("error", {}).get("message", "")
                      and "must not" in attempts[0]["response"]["error"]["message"],
                      "No provider evidence authorizes removing the hold flag")
        else:
            s.require(not attempts, "Recovery already attempted; inspect its response")
        with p.GoogleVerifier({"service_account_file": str(key)}).session() as session:
            p.no_retries(session)
            api = p.PlayInternalAPI(session, path, record, handoff, readback=True)
            edit = p.edit_id(record["edit_id"])
            s.require(api.request("get", edit=edit) is not None, "Edit already closed; read back instead")
            tracks = api.request("tracks", edit=edit)
            p.preserve_noninternal(record["baseline_tracks"], tracks)
            p.exact_internal(p.tracks_by_name(tracks)[p.TRACK], record)
            s.require(p.find_bundle(api.request("bundles", edit=edit), record), "Exact bundle missing")
            original_url = record["steps"]["commit_edit"]["url"]
            prefix = p.BASE + "/edits/" + edit + ":commit"
            permitted = {p.COMMIT_QUERY, "?changesNotSentForReview=true&changesInReviewBehavior=ERROR_IF_IN_REVIEW"}
            s.require(original_url.startswith(prefix) and original_url[len(prefix):] in permitted,
                      "Original commit query outside approved scope")
            query = p.COMMIT_QUERY if omit_hold else original_url[len(prefix):]
            item = {"state": "intent", "at": s.now(), "edit_id": edit, "query": query,
                    "coordination": p.coordination(handoff, record), "precommit_tracks": tracks}
            attempts.append(item)
            api.persist()
            try:
                response = session.post(p.BASE + "/edits/" + edit + ":commit" + query,
                                        timeout=(10, 45), allow_redirects=False)
                s.require(len(response.content) < 65536, "Provider response too large")
                item.update(http_status=response.status_code, response=response.json(), finished=s.now())
                if response.status_code == 200:
                    s.require(item["response"].get("id") == edit, "Commit ID mismatch")
                    item["state"] = "accepted"
                    record["state"] = "committed_unverified"
                else:
                    item["state"] = "rejected" if 400 <= response.status_code < 500 else "unknown"
                api.persist()
                return {k: item[k] for k in ("state", "http_status", "response")}
            except Exception:
                item["state"] = "unknown"
                api.persist()
                raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("operation", "build", "qa", "key", "handoff"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--omit-hold", action="store_true")
    args = parser.parse_args()
    print(json.dumps(recover(**vars(args)), indent=2))
