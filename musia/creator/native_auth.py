"""App-owned PKCE completion; central credentials never enter native clients."""

import base64
import hashlib
import re
import secrets

from .contracts import CreatorError, RequestModel
from .store import digest, identifier
from pydantic import Field
from typing import Literal


class NativeStart(RequestModel):
    challenge: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")
    platform: Literal["apple", "android"]


class NativeExchange(RequestModel):
    attempt: str = Field(pattern=r"^[a-f0-9]{32}$")
    code: str = Field(min_length=32, max_length=128)
    verifier: str = Field(pattern=r"^[A-Za-z0-9._~-]{43,128}$")
    platform: Literal["apple", "android"]


def challenge(verifier):
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).decode().rstrip("=")


class NativeFlow:
    def __init__(self, store):
        self.store = store
        with store.db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS native_flows(
                id TEXT PRIMARY KEY, challenge TEXT NOT NULL, platform TEXT NOT NULL,
                expires INTEGER NOT NULL, state TEXT NOT NULL, binding TEXT UNIQUE,
                code TEXT, session_hash TEXT)""")

    def start(self, body, peer):
        attempt = identifier()
        with self.store.db() as db:
            self.store.rate(db, digest(peer), "native_login", 100)
            db.execute("DELETE FROM sessions WHERE token IN (SELECT session_hash FROM native_flows WHERE expires<=?)", (self.store.now(),))
            db.execute("DELETE FROM native_flows WHERE expires<=?", (self.store.now(),))
            db.execute("INSERT INTO native_flows(id,challenge,platform,expires,state) VALUES(?,?,?,?,'new')",
                       (attempt, body.challenge, body.platform, self.store.now()+600))
        return attempt

    def browser(self, attempt, binding):
        if not re.fullmatch(r"[a-f0-9]{32}", attempt):
            raise CreatorError("sign_in_expired", 401)
        with self.store.db() as db:
            if not db.execute("UPDATE native_flows SET state='browser',binding=? WHERE id=? AND state='new' AND expires>?",
                              (digest(binding), attempt, self.store.now())).rowcount:
                raise CreatorError("sign_in_expired", 401)

    def finish(self, binding, token):
        expired = False
        with self.store.db() as db:
            row = db.execute("SELECT * FROM native_flows WHERE binding=?", (digest(binding),)).fetchone()
            if row is None:
                return None
            if row["state"] != "browser" or row["expires"] <= self.store.now():
                db.execute("DELETE FROM sessions WHERE token=?", (digest(token),))
                expired = True
            else:
                code = secrets.token_urlsafe(32)
                db.execute("UPDATE native_flows SET state='complete',code=?,session_hash=? WHERE id=?",
                           (digest(code), digest(token), row["id"]))
                return {"attempt": row["id"], "code": code}
        if expired:
            raise CreatorError("sign_in_expired", 401)

    def exchange(self, body):
        with self.store.db() as db:
            row = db.execute("SELECT * FROM native_flows WHERE id=? AND state='complete' AND expires>?",
                             (body.attempt, self.store.now())).fetchone()
            if not row or row["platform"] != body.platform or not secrets.compare_digest(row["code"], digest(body.code)) or not secrets.compare_digest(row["challenge"], challenge(body.verifier)):
                raise CreatorError("sign_in_failed", 401)
            session = db.execute("SELECT * FROM sessions WHERE token=? AND expires>?", (row["session_hash"], self.store.now())).fetchone()
            if not session:
                raise CreatorError("sign_in_expired", 401)
            self.store.active(db, session["owner"])
            token = secrets.token_urlsafe(32)
            db.execute("INSERT INTO sessions VALUES(?,?,?,?)", (digest(token), session["owner"], session["link_id"], session["expires"]))
            db.execute("DELETE FROM sessions WHERE token=?", (row["session_hash"],))
            db.execute("DELETE FROM native_flows WHERE id=?", (body.attempt,))
            return {"token": token, "expiresIn": session["expires"]-self.store.now()}
