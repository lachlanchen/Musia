#!/usr/bin/env python3
"""Musia creator operations; run with the musia environment. No public admin API."""

import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from musia.creator.api import Settings
from musia.creator.store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Settings.environment().directory)
    sub = parser.add_subparsers(dest="action", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8796)
    sub.add_parser("queue")
    invite = sub.add_parser("invite")
    invite.add_argument("--days", type=int, default=7, choices=range(1, 31))
    invite.add_argument("--uses", type=int, default=1)
    grant = sub.add_parser("pilot-grant")
    grant.add_argument("owner")
    grant.add_argument("tier", choices=["free", "creator", "studio"])
    grant.add_argument("--days", type=int, default=30, choices=range(1, 91))
    grant.add_argument("--reason", required=True)
    approve_input = sub.add_parser("approve-input")
    approve_input.add_argument("job")
    approve = sub.add_parser("approve-audio")
    approve.add_argument("job")
    approve.add_argument("--audit", type=Path, required=True)
    reject = sub.add_parser("reject-audio")
    reject.add_argument("job")
    moderate = sub.add_parser("moderate")
    moderate.add_argument("kind", choices=["song", "comment"])
    moderate.add_argument("target")
    moderate.add_argument("decision", choices=["approve", "reject"])
    sub.add_parser("work-once")
    suspend = sub.add_parser("suspend")
    suspend.add_argument("owner")
    resolve = sub.add_parser("resolve-report")
    resolve.add_argument("report")
    args = parser.parse_args()
    os.umask(0o077)
    if args.action == "serve":
        if not 1024 <= args.port <= 65535:
            parser.error("Port must be 1024..65535")
        import uvicorn
        from dataclasses import replace
        from musia.creator.api import create_app
        cfg = replace(Settings.environment(), directory=args.data)
        if "MUSIA_CREATOR_ORIGIN" not in os.environ:
            cfg = replace(cfg, origin=f"http://127.0.0.1:{args.port}")
        uvicorn.run(create_app(cfg), host="127.0.0.1", port=args.port, access_log=False)
        return
    store = Store(args.data)
    if args.action == "queue":
        with store.db() as db:
            print(json.dumps({"jobs": [dict(r) for r in db.execute("SELECT id,owner,state,input_approved,brief,review FROM jobs WHERE state IN ('queued','running','review','interrupted')")],
                              "songs": [dict(r) for r in db.execute("SELECT id,title FROM songs WHERE moderation='pending'")],
                              "comments": [dict(r) for r in db.execute("SELECT id,text FROM comments WHERE state='pending'")],
                              "reports": [dict(r) for r in db.execute("SELECT * FROM reports WHERE state='open'")]}, indent=2, ensure_ascii=False))
    elif args.action == "invite":
        # A bearer invitation: print only when explicitly requested by the operator.
        print(store.issue_invite(store.now()+args.days*86400, args.uses))
    elif args.action == "pilot-grant":
        store.pilot_grant(args.owner, args.tier, store.now()+args.days*86400, args.reason)
    elif args.action == "approve-input":
        store.approve_input(args.job)
    elif args.action == "approve-audio":
        store.approve(args.job, json.loads(args.audit.read_text()))
    elif args.action == "reject-audio":
        store.reject(args.job)
    elif args.action == "moderate":
        store.moderate(args.kind, args.target, args.decision == "approve")
    elif args.action == "suspend":
        store.suspend(args.owner)
    elif args.action == "resolve-report":
        store.resolve_report(args.report)
    elif args.action == "work-once":
        from musia.creator.worker import work_once
        print("Processed one job" if work_once(store) else "No approved queued job")


if __name__ == "__main__":
    main()
