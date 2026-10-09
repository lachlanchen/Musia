"""Transactional pilot ledger. No identity, tier or worker result is HTTP-trusted."""

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import time
import uuid

from .contracts import CreatorError, Generate, PLANS, TERMS_VERSION


def identifier():
    return uuid.uuid4().hex


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
 id TEXT PRIMARY KEY, issuer TEXT NOT NULL, subject TEXT NOT NULL, name TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'active', terms TEXT NOT NULL DEFAULT '', invited INTEGER NOT NULL DEFAULT 0,
 UNIQUE(issuer,subject));
CREATE TABLE IF NOT EXISTS sessions(
 token TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES users(id), link_id TEXT NOT NULL, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS grants(
 owner TEXT PRIMARY KEY REFERENCES users(id), tier TEXT NOT NULL, expires INTEGER NOT NULL, reason TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS invitations(
 code TEXT PRIMARY KEY, expires INTEGER NOT NULL, remaining INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS redemptions(
 owner TEXT PRIMARY KEY REFERENCES users(id), code TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS jobs(
 id TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES users(id), request_key TEXT NOT NULL, request_hash TEXT NOT NULL,
 brief TEXT NOT NULL, visibility TEXT NOT NULL, state TEXT NOT NULL, credit TEXT NOT NULL,
 period TEXT NOT NULL, created INTEGER NOT NULL, updated INTEGER NOT NULL, lease TEXT,
 audio TEXT, audio_hash TEXT, review TEXT, error TEXT, input_approved INTEGER NOT NULL DEFAULT 0, UNIQUE(owner,request_key));
CREATE INDEX IF NOT EXISTS jobs_usage ON jobs(owner,period,credit);
CREATE INDEX IF NOT EXISTS jobs_queue ON jobs(state,created);
CREATE TABLE IF NOT EXISTS songs(
 id TEXT PRIMARY KEY REFERENCES jobs(id), owner TEXT NOT NULL REFERENCES users(id), title TEXT NOT NULL,
 language TEXT NOT NULL, duration INTEGER NOT NULL, visibility TEXT NOT NULL, moderation TEXT NOT NULL,
 lyrics TEXT NOT NULL, lyric_lines TEXT NOT NULL, created INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS reactions(
 owner TEXT NOT NULL REFERENCES users(id), song TEXT NOT NULL REFERENCES songs(id),
 kind TEXT NOT NULL, PRIMARY KEY(owner,song,kind));
CREATE TABLE IF NOT EXISTS comments(
 id TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES users(id), song TEXT NOT NULL REFERENCES songs(id),
 text TEXT NOT NULL, state TEXT NOT NULL, created INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS blocks(
 owner TEXT NOT NULL REFERENCES users(id), target TEXT NOT NULL REFERENCES users(id), PRIMARY KEY(owner,target));
CREATE TABLE IF NOT EXISTS reports(
 id TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES users(id), song TEXT NOT NULL,
 reason TEXT NOT NULL, created INTEGER NOT NULL, state TEXT NOT NULL DEFAULT 'open');
CREATE TABLE IF NOT EXISTS counters(
 owner TEXT NOT NULL, action TEXT NOT NULL, period TEXT NOT NULL, n INTEGER NOT NULL,
 PRIMARY KEY(owner,action,period));
CREATE TABLE IF NOT EXISTS agent_turns(
 id TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES users(id), created INTEGER NOT NULL,
 request TEXT NOT NULL, response TEXT, state TEXT NOT NULL);
"""


class Store:
    def __init__(self, directory: Path, *, clock=time.time):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if directory.is_symlink() or directory.resolve() != directory.absolute() or directory.stat().st_mode & 0o077:
            raise ValueError("Creator storage must be a real private directory (0700)")
        self.directory, self.clock = directory, clock
        self.path = directory / "creator.sqlite"
        if not self.path.exists():
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            os.close(fd)
        if self.path.is_symlink() or self.path.stat().st_mode & 0o077:
            raise ValueError("Creator database must be private (0600)")
        with self.db() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("BEGIN IMMEDIATE")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def now(self):
        return int(self.clock())

    def period(self, daily=False):
        return datetime.fromtimestamp(self.clock(), timezone.utc).strftime("%Y-%m-%d" if daily else "%Y-%m")

    def active(self, db, owner):
        row = db.execute("SELECT * FROM users WHERE id=? AND state='active'", (owner,)).fetchone()
        if not row:
            raise CreatorError("sign_in_required", 401)
        return dict(row)

    def signed_in(self, issuer, subject, name, link_id):
        """Called only with verified identity from the central adapter."""
        token = secrets.token_urlsafe(32)
        with self.db() as db:
            row = db.execute("SELECT * FROM users WHERE issuer=? AND subject=?", (issuer, subject)).fetchone()
            if row and row["state"] != "active":
                raise CreatorError("account_unavailable", 403)
            owner = row["id"] if row else identifier()
            db.execute("INSERT INTO users(id,issuer,subject,name) VALUES(?,?,?,?) ON CONFLICT(issuer,subject) DO UPDATE SET name=excluded.name",
                       (owner, issuer, subject, name[:100]))
            db.execute("DELETE FROM sessions WHERE expires<=?", (self.now(),))
            db.execute("INSERT INTO sessions VALUES(?,?,?,?)", (digest(token), owner, link_id, self.now()+86400*7))
        return token

    def session(self, token):
        with self.db() as db:
            row = db.execute("SELECT * FROM sessions WHERE token=? AND expires>?", (digest(token), self.now())).fetchone()
            if not row:
                raise CreatorError("sign_in_required", 401)
            return {**dict(row), "user": self.active(db, row["owner"])}

    def logout(self, token):
        with self.db() as db:
            db.execute("DELETE FROM sessions WHERE token=?", (digest(token),))

    def accept_terms(self, owner):
        with self.db() as db:
            self.active(db, owner)
            db.execute("UPDATE users SET terms=? WHERE id=?", (TERMS_VERSION, owner))

    def consent(self, db, owner):
        user = self.active(db, owner)
        if user["terms"] != TERMS_VERSION:
            raise CreatorError("accept_creator_terms", 403)
        return user

    def allowance(self, db, owner):
        self.active(db, owner)
        grant = db.execute("SELECT * FROM grants WHERE owner=? AND expires>?", (owner, self.now())).fetchone()
        tier = grant["tier"] if grant else "free"
        used = db.execute("SELECT count(*) FROM jobs WHERE owner=? AND period=? AND credit IN ('reserved','settled')",
                          (owner, self.period())).fetchone()[0]
        return {"tier": tier, "period": self.period(), "limit": PLANS[tier]["renders"], "used": used,
                "remaining": max(0, PLANS[tier]["renders"]-used), "source": "pilot_grant" if grant else "free",
                "expires": grant["expires"] if grant else None}

    def profile(self, owner):
        with self.db() as db:
            u = self.active(db, owner)
            return {"id": owner, "name": u["name"], "termsAccepted": u["terms"] == TERMS_VERSION,
                    "invited": bool(u["invited"]), "usage": self.allowance(db, owner)}

    def pilot_grant(self, owner, tier, expires, reason):
        if tier not in PLANS or expires <= self.now() or not reason.strip():
            raise ValueError("Invalid pilot grant")
        with self.db() as db:
            self.active(db, owner)
            db.execute("INSERT INTO grants VALUES(?,?,?,?) ON CONFLICT(owner) DO UPDATE SET tier=excluded.tier,expires=excluded.expires,reason=excluded.reason",
                       (owner, tier, expires, reason[:300]))

    def issue_invite(self, expires, uses=1):
        if expires <= self.now() or not 1 <= uses <= 100:
            raise ValueError("Invalid invitation")
        code = secrets.token_urlsafe(24)
        with self.db() as db:
            db.execute("INSERT INTO invitations VALUES(?,?,?)", (digest(code), expires, uses))
        return code

    def rate(self, db, owner, action, limit):
        day = self.period(daily=True)
        db.execute("DELETE FROM counters WHERE period<?", (day,))
        row = db.execute("SELECT n FROM counters WHERE owner=? AND action=? AND period=?", (owner, action, day)).fetchone()
        if row and row[0] >= limit:
            raise CreatorError("daily_limit_reached", 429)
        db.execute("INSERT INTO counters VALUES(?,?,?,1) ON CONFLICT(owner,action,period) DO UPDATE SET n=n+1", (owner, action, day))

    def redeem(self, owner, code):
        # Commit attempt counting even when the guessed code is invalid.
        with self.db() as db:
            self.active(db, owner)
            self.rate(db, owner, "invite", 10)
        with self.db() as db:
            if db.execute("SELECT 1 FROM redemptions WHERE owner=?", (owner,)).fetchone():
                return
            row = db.execute("SELECT * FROM invitations WHERE code=? AND expires>? AND remaining>0", (digest(code), self.now())).fetchone()
            if not row:
                raise CreatorError("invitation_invalid", 400)
            db.execute("UPDATE invitations SET remaining=remaining-1 WHERE code=?", (digest(code),))
            db.execute("INSERT INTO redemptions VALUES(?,?)", (owner, digest(code)))
            db.execute("UPDATE users SET invited=1 WHERE id=?", (owner,))

    def submit(self, owner, key, request: Generate, *, invitation_required=True):
        if not key or len(key) > 100 or not all(c.isalnum() or c in "-_" for c in key):
            raise CreatorError("idempotency_key_required")
        body = request.model_dump_json()
        with self.db() as db:
            user = self.consent(db, owner)
            prior = db.execute("SELECT * FROM jobs WHERE owner=? AND request_key=?", (owner, key)).fetchone()
            if prior:
                if prior["request_hash"] != digest(body):
                    raise CreatorError("idempotency_conflict", 409)
                return self.job_projection(prior)
            if invitation_required and not user["invited"]:
                raise CreatorError("creator_invitation_required", 403)
            usage = self.allowance(db, owner)
            plan = PLANS[usage["tier"]]
            if not usage["remaining"]:
                raise CreatorError("monthly_generation_limit", 429)
            active = db.execute("SELECT count(*) FROM jobs WHERE owner=? AND state IN ('queued','running','review','interrupted')", (owner,)).fetchone()[0]
            if active >= plan["active_jobs"]:
                raise CreatorError("finish_current_job", 409)
            if db.execute("SELECT count(*) FROM jobs WHERE state IN ('queued','running','review','interrupted')").fetchone()[0] >= 100:
                raise CreatorError("queue_full", 503)
            self.rate(db, owner, "generate", max(4, plan["renders"]*2))
            job = identifier()
            db.execute("INSERT INTO jobs(id,owner,request_key,request_hash,brief,visibility,state,credit,period,created,updated) VALUES(?,?,?,?,?,?,'queued','reserved',?,?,?)",
                       (job, owner, key, digest(body), request.brief.model_dump_json(), request.visibility, self.period(), self.now(), self.now()))
            return self.job_projection(db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone())

    def job_projection(self, row):
        return {"id": row["id"], "brief": json.loads(row["brief"]), "visibility": row["visibility"],
                "state": row["state"], "credit": row["credit"], "created": row["created"], "error": row["error"]}

    def jobs(self, owner):
        with self.db() as db:
            self.active(db, owner)
            return [self.job_projection(r) for r in db.execute("SELECT * FROM jobs WHERE owner=? ORDER BY created DESC,id DESC LIMIT 100", (owner,))]

    def cancel(self, owner, job):
        with self.db() as db:
            self.active(db, owner)
            row = db.execute("SELECT * FROM jobs WHERE id=? AND owner=?", (job, owner)).fetchone()
            if not row:
                raise CreatorError("job_not_found", 404)
            if row["state"] == "cancelled":
                return
            if row["state"] != "queued":
                raise CreatorError("job_already_started", 409)
            db.execute("UPDATE jobs SET state='cancelled',credit='released',updated=? WHERE id=?", (self.now(), job))

    def claim(self):
        with self.db() as db:
            # Never duplicate an unknown provider outcome after a worker crash.
            if db.execute("SELECT 1 FROM jobs WHERE state IN ('running','interrupted')").fetchone():
                return None
            row = db.execute("SELECT j.* FROM jobs j JOIN users u ON u.id=j.owner WHERE j.state='queued' AND j.input_approved=1 AND u.state='active' ORDER BY j.created,j.id LIMIT 1").fetchone()
            if not row:
                return None
            lease = secrets.token_hex(24)
            db.execute("UPDATE jobs SET state='running',lease=?,updated=? WHERE id=?", (lease, self.now(), row["id"]))
            return {**dict(row), "lease": lease}

    def result(self, job, lease, *, audio=None, audio_hash=None, review=None, error=None):
        with self.db() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=? AND lease=? AND state='running'", (job, lease)).fetchone()
            if not row:
                raise CreatorError("worker_lease_lost", 409)
            self.active(db, row["owner"])
            if error:
                db.execute("UPDATE jobs SET state='failed',credit='released',error='generation_failed',updated=? WHERE id=?", (self.now(), job))
            else:
                if not audio or not audio_hash or not review:
                    raise ValueError("Audio and review evidence required")
                db.execute("UPDATE jobs SET state='review',audio=?,audio_hash=?,review=?,updated=? WHERE id=?",
                           (audio, audio_hash, review, self.now(), job))

    def approve_input(self, job):
        with self.db() as db:
            if not db.execute("UPDATE jobs SET input_approved=1 WHERE id=? AND state='queued'", (job,)).rowcount:
                raise CreatorError("job_not_queued", 409)

    def approve(self, job, audit):
        """Operator-only: listening + ASR and input-reference correction gate."""
        from .review import audio_digest, validate_audit
        with self.db() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=? AND state='review'", (job,)).fetchone()
            if not row:
                raise CreatorError("review_not_ready", 409)
            self.active(db, row["owner"])
            brief = json.loads(row["brief"])
            audio = self.directory / "artifacts" / job / "song.wav"
            if str(audio) != row["audio"] or audio.is_symlink() or audio.resolve() != audio.absolute() or audio_digest(audio) != row["audio_hash"]:
                raise ValueError("Selected audio changed; repeat review")
            validate_audit(audit, row["audio_hash"])
            db.execute("INSERT INTO songs VALUES(?,?,?,?,?,?,?,?,?,?)",
                       (job, row["owner"], brief["title"], brief["language"], audit["duration"], row["visibility"],
                        "pending" if row["visibility"] == "public" else "private", "\n".join(line["text"] for line in audit["lines"]),
                        json.dumps(audit["lines"], ensure_ascii=False), self.now()))
            db.execute("UPDATE jobs SET state='ready',credit='settled',review=?,updated=? WHERE id=?",
                       (json.dumps({"workerEvidence": row["review"], "audit": audit}, ensure_ascii=False), self.now(), job))

    def reject(self, job):
        with self.db() as db:
            changed = db.execute("UPDATE jobs SET state='failed',credit='released',error='quality_review_failed',updated=? WHERE id=? AND state='review'", (self.now(), job)).rowcount
            if not changed:
                raise CreatorError("review_not_ready", 409)

    def blocked(self, db, viewer, author):
        return viewer and db.execute("SELECT 1 FROM blocks WHERE (owner=? AND target=?) OR (owner=? AND target=?)", (viewer, author, author, viewer)).fetchone()

    def accessible(self, db, song, owner=None):
        row = db.execute("SELECT s.*,u.name FROM songs s JOIN users u ON u.id=s.owner WHERE s.id=? AND u.state='active'", (song,)).fetchone()
        if not row or (row["owner"] != owner and (row["visibility"] != "public" or row["moderation"] != "approved" or self.blocked(db, owner, row["owner"]))):
            raise CreatorError("song_not_found", 404)
        return row

    def card(self, db, row, owner):
        reactions = {r["kind"] for r in db.execute("SELECT kind FROM reactions WHERE song=? AND owner=?", (row["id"], owner or ""))}
        likes = db.execute("SELECT count(*) FROM reactions r JOIN users u ON u.id=r.owner WHERE r.song=? AND r.kind='like' AND u.state='active'", (row["id"],)).fetchone()[0]
        return {**{k: row[k] for k in ("id", "title", "language", "duration", "visibility", "moderation", "lyrics")},
                "author": {"id": row["owner"], "name": row["name"]}, "mine": row["owner"] == owner,
                "liked": "like" in reactions, "saved": "save" in reactions, "likes": likes,
                "lyricLines": json.loads(row["lyric_lines"]),
                "audioUrl": f"/creator/api/songs/{row['id']}/audio",
                "sharePath": f"/creator/?song={row['id']}" if row["visibility"] == "public" and row["moderation"] == "approved" else None}

    def songs(self, owner=None, mode="public", before=2**63-1):
        with self.db() as db:
            if owner:
                self.active(db, owner)
            if mode != "public" and not owner:
                raise CreatorError("sign_in_required", 401)
            condition = {"public": "s.visibility='public' AND s.moderation='approved'", "mine": "s.owner=:owner",
                         "saved": "EXISTS(SELECT 1 FROM reactions r WHERE r.owner=:owner AND r.song=s.id AND r.kind='save')"}[mode]
            rows = db.execute(f"SELECT s.*,u.name FROM songs s JOIN users u ON u.id=s.owner WHERE {condition} AND u.state='active' AND s.rowid<:before ORDER BY s.rowid DESC LIMIT 100",
                              {"owner": owner, "before": before}).fetchall()
            result = []
            for row in rows:
                try:
                    self.accessible(db, row["id"], owner)
                    result.append(self.card(db, row, owner))
                except CreatorError:
                    pass
            return result

    def song(self, song, owner=None):
        with self.db() as db:
            return self.card(db, self.accessible(db, song, owner), owner)

    def audio(self, song, owner=None):
        with self.db() as db:
            self.accessible(db, song, owner)
            return db.execute("SELECT audio,audio_hash FROM jobs WHERE id=? AND state='ready'", (song,)).fetchone()

    def visibility(self, owner, song, visibility):
        with self.db() as db:
            self.consent(db, owner)
            row = self.accessible(db, song, owner)
            if row["owner"] != owner:
                raise CreatorError("song_not_found", 404)
            if row["visibility"] == visibility:
                return
            db.execute("UPDATE songs SET visibility=?,moderation=? WHERE id=?", (visibility, "pending" if visibility == "public" else "private", song))

    def react(self, owner, song, kind, active):
        if kind not in ("like", "save"):
            raise CreatorError("invalid_reaction")
        with self.db() as db:
            self.consent(db, owner)
            self.accessible(db, song, owner)
            self.rate(db, owner, "reaction", 500)
            if active:
                db.execute("INSERT OR IGNORE INTO reactions VALUES(?,?,?)", (owner, song, kind))
            else:
                db.execute("DELETE FROM reactions WHERE owner=? AND song=? AND kind=?", (owner, song, kind))

    def comment(self, owner, song, text):
        if not text.strip():
            raise CreatorError("empty_comment")
        with self.db() as db:
            self.consent(db, owner)
            row = self.accessible(db, song, owner)
            if row["visibility"] != "public" or row["moderation"] != "approved":
                raise CreatorError("comments_require_public_song", 409)
            self.rate(db, owner, "comment", 30)
            comment = identifier()
            db.execute("INSERT INTO comments VALUES(?,?,?,?,'pending',?)", (comment, owner, song, text.strip(), self.now()))
            return comment

    def comments(self, song, owner=None):
        with self.db() as db:
            self.accessible(db, song, owner)
            rows = db.execute("SELECT c.*,u.name FROM comments c JOIN users u ON u.id=c.owner WHERE c.song=? AND u.state='active' AND (c.state='approved' OR (c.owner=? AND c.state='pending')) ORDER BY c.created LIMIT 100", (song, owner or "")).fetchall()
            return [{"id": r["id"], "text": r["text"], "author": r["name"], "state": r["state"], "mine": r["owner"] == owner}
                    for r in rows if not self.blocked(db, owner, r["owner"])]

    def remove_comment(self, owner, comment):
        with self.db() as db:
            self.active(db, owner)
            if not db.execute("DELETE FROM comments WHERE id=? AND owner=?", (comment, owner)).rowcount:
                raise CreatorError("comment_not_found", 404)

    def report(self, owner, song, reason):
        with self.db() as db:
            self.active(db, owner)
            self.accessible(db, song, owner)
            self.rate(db, owner, "report", 20)
            db.execute("INSERT INTO reports(id,owner,song,reason,created) VALUES(?,?,?,?,?)", (identifier(), owner, song, reason, self.now()))

    def block(self, owner, target, active):
        with self.db() as db:
            self.active(db, owner)
            if owner == target or not db.execute("SELECT 1 FROM users WHERE id=?", (target,)).fetchone():
                raise CreatorError("invalid_account")
            self.rate(db, owner, "block", 100)
            if active:
                db.execute("INSERT OR IGNORE INTO blocks VALUES(?,?)", (owner, target))
            else:
                db.execute("DELETE FROM blocks WHERE owner=? AND target=?", (owner, target))

    def blocks(self, owner):
        with self.db() as db:
            self.active(db, owner)
            return [dict(r) for r in db.execute("SELECT u.id,u.name FROM blocks b JOIN users u ON u.id=b.target WHERE b.owner=?", (owner,))]

    def suspend(self, owner):
        with self.db() as db:
            self.active(db, owner)
            db.execute("UPDATE users SET state='suspended' WHERE id=?", (owner,))
            db.execute("DELETE FROM sessions WHERE owner=?", (owner,))
            db.execute("UPDATE jobs SET state='cancelled',credit='released' WHERE owner=? AND state='queued'", (owner,))

    def resolve_report(self, report):
        with self.db() as db:
            if not db.execute("UPDATE reports SET state='resolved' WHERE id=?", (report,)).rowcount:
                raise CreatorError("report_not_found", 404)

    def moderate(self, kind, target, approve):
        with self.db() as db:
            if kind == "song":
                changed = db.execute("UPDATE songs SET moderation=? WHERE id=? AND visibility='public'", ("approved" if approve else "rejected", target)).rowcount
            elif kind == "comment":
                changed = db.execute("UPDATE comments SET state=? WHERE id=?", ("approved" if approve else "rejected", target)).rowcount
            else:
                raise ValueError("Unknown moderation target")
            if not changed:
                raise CreatorError("moderation_target_not_found", 404)

    def start_turn(self, owner, request, *, invitation_required=True):
        with self.db() as db:
            u = self.consent(db, owner)
            if invitation_required and not u["invited"]:
                raise CreatorError("creator_invitation_required", 403)
            plan = PLANS[self.allowance(db, owner)["tier"]]
            self.rate(db, owner, "agent", plan["agent_turns_per_day"])
            if db.execute("SELECT 1 FROM agent_turns WHERE owner=? AND state='running' AND created>?", (owner, self.now()-120)).fetchone():
                raise CreatorError("agent_busy", 409)
            turn = identifier()
            db.execute("INSERT INTO agent_turns VALUES(?,?,?,?,NULL,'running')", (turn, owner, self.now(), request))
            return turn

    def finish_turn(self, owner, turn, response):
        with self.db() as db:
            self.active(db, owner)
            db.execute("UPDATE agent_turns SET response=?,state=? WHERE id=? AND owner=?", (response, "done" if response else "failed", turn, owner))

    def delete_account(self, owner):
        with self.db() as db:
            self.active(db, owner)
            db.execute("UPDATE users SET state='deleted',name='',terms='' WHERE id=?", (owner,))
            db.execute("DELETE FROM sessions WHERE owner=?", (owner,))
            for table in ("grants", "reactions", "comments", "agent_turns"):
                db.execute(f"DELETE FROM {table} WHERE owner=?", (owner,))
            db.execute("DELETE FROM blocks WHERE owner=? OR target=?", (owner, owner))
            db.execute("UPDATE songs SET visibility='private',moderation='removed',lyrics='',lyric_lines='[]',title='' WHERE owner=?", (owner,))
            db.execute("UPDATE jobs SET state='cancelled',credit='released',brief='{}',audio=NULL,review=NULL WHERE owner=?", (owner,))
