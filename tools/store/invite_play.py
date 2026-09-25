"""Private self-invite, with observed Play access and an explicit existing MTA."""
from email.message import EmailMessage
from email.policy import SMTP
import os
from pathlib import Path

from play_console import test_access
from storelib import BUNDLE, RUNTIME, config, lock, now, private_file, read_json, require, run, write_private


def invite(build, confirm=False):
    require(build["platform"] == "android", "Play invitation requires Android QA")
    upload = read_json(private_file(RUNTIME / "operations" / ("play-upload-" + build["artifact_sha256"] + ".json")))
    require(upload.get("sha256") == build["artifact_sha256"] and upload.get("state") == "upload_dispatched_readback_required",
            "Missing exact Musia AAB upload journal")
    cfg = config()
    url = test_access(build)
    recipient = cfg["self_tester_email"]
    require("@" in recipient and not any(c in recipient for c in "\r\n"), "Invalid protected recipient")
    message = EmailMessage(policy=SMTP)
    message["To"] = recipient
    message["From"] = recipient
    message["Subject"] = "Musia native Android internal test"
    message["Message-ID"] = "<musia." + build["artifact_sha256"] + "@lazying.art>"
    message.set_content(f"Musia {build['version']} ({build['build_number']}) is available for internal testing.\n\n"
                        f"Package: {BUNDLE}\nOpt in using this same Google account:\n{url}\n\n"
                        "This is the native Kotlin/Compose build, not a web wrapper.\n")
    payload = message.as_bytes()
    draft = RUNTIME / "mail" / (build["artifact_sha256"] + ".eml")
    write_private(draft, payload)
    if not confirm:
        return {"state": "private_invitation_prepared_not_sent", "path": str(draft), "recipient_count": 1}
    transport = Path(cfg.get("sendmail_path") or "/missing-mail-transport")
    require(transport.is_absolute() and transport.is_file(), "No existing mail transport configured; private draft retained, not sent")
    info = transport.stat()
    require(not transport.is_symlink() and info.st_uid in {0, os.getuid()} and not info.st_mode & 0o022
            and os.access(transport, os.X_OK), "Mail transport must be an explicitly trusted existing executable")
    journal = RUNTIME / "mail" / (build["artifact_sha256"] + ".json")
    with lock("play-invite"):
        require(not journal.exists(), "Invitation attempted before; reconcile delivery before retry")
        write_private(journal, {"state": "started", "at": now(), "message_id": message["Message-ID"]})
        run([transport, "-i", "-t"], input_data=payload, log=RUNTIME / "mail/transport.log")
        write_private(journal, {"state": "accepted_by_transport_delivery_unverified", "at": now(),
                                "message_id": message["Message-ID"], "recipient": recipient})
        return {"state": "accepted_by_transport_delivery_unverified", "recipient_count": 1}
