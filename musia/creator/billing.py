"""App-owned verified subscriptions; prices, pilot grants and receipts stay distinct."""

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import stat
import uuid

from cryptography.fernet import Fernet
from pydantic import Field
from typing import Literal

from .contracts import CreatorError, RequestModel
from .store import digest

BUNDLE = "art.lazying.musia"
APP_ID = 6816265930
PRODUCTS = [
    {"tier": tier, "appleProductId": f"{BUNDLE}.{tier}.monthly",
     "googleProductId": f"musia_{tier}", "googleBasePlanId": "monthly"}
    for tier in ("creator", "studio")
]
ACTIVE = ("active", "grace", "canceled")


class Verification(RequestModel):
    provider: Literal["apple", "google"]
    reference: str = Field(min_length=1, max_length=4096)


def private_read(path):
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_size > 1048576:
            raise ValueError("Private billing file required")
        return stream.read()


@dataclass(frozen=True)
class Snapshot:
    provider: str
    reference: str
    product: str
    tier: str
    state: str
    expires: int
    environment: str
    account_token: str
    replaces: str = ""


def account_token(owner):
    return str(uuid.UUID(hex=owner))


class Billing:
    def __init__(self, store, config=None, *, verifier_factory=None):
        self.store = store
        if config is None:
            path = os.environ.get("MUSIA_CREATOR_BILLING_CONFIG")
            config = json.loads(private_read(path)) if path else {"schema":1,"providers":{}}
        if config.get("schema") != 1 or not isinstance(config.get("providers"), dict):
            raise ValueError("Invalid Musia billing configuration")
        self.config = config
        for provider, item in config["providers"].items():
            if provider not in ("apple", "google") or item.get("environment") not in ("test", "live"):
                raise ValueError("Invalid billing provider")
            if item.get("bundle_id", BUNDLE) != BUNDLE or item.get("app_id", APP_ID) != APP_ID:
                raise ValueError("Musia billing requires its own app identity")
            if item.get("sales_enabled", False) and (not item.get("qualified", False) or not item.get("reconciliation_enabled", False)):
                raise ValueError("Sales require provider qualification and reconciliation")
            if item.get("environment") == "test" and item.get("sales_enabled") and not item.get("test_owners"):
                raise ValueError("Test sales require explicit no-charge testers")
            if item.get("test_sales_enabled") and (item.get("environment") != "test" or
                    not item.get("no_charge_test_setup") or not item.get("test_owners") or
                    not item.get("reconciliation_enabled")):
                raise ValueError("Sandbox checkout requires app-specific no-charge setup and named testers")
        self.verifier_factory = verifier_factory
        key = store.directory / "billing.key"
        try:
            with os.fdopen(os.open(key, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600), "wb") as out:
                out.write(Fernet.generate_key())
        except FileExistsError:
            pass
        self.cipher = Fernet(private_read(key))
        with store.db() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS subscriptions(
                provider TEXT NOT NULL, reference_hash TEXT NOT NULL, reference TEXT NOT NULL,
                owner TEXT NOT NULL, product TEXT NOT NULL, tier TEXT NOT NULL, state TEXT NOT NULL,
                expires INTEGER NOT NULL, environment TEXT NOT NULL, verified INTEGER NOT NULL,
                revision INTEGER NOT NULL, PRIMARY KEY(provider,reference_hash));
            CREATE TABLE IF NOT EXISTS billing_operations(
                id INTEGER PRIMARY KEY AUTOINCREMENT, provider TEXT NOT NULL, reference_hash TEXT NOT NULL,
                owner TEXT NOT NULL, started INTEGER NOT NULL, state TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS billing_events(
                provider TEXT NOT NULL, id TEXT NOT NULL, reference TEXT NOT NULL,
                received INTEGER NOT NULL, state TEXT NOT NULL, PRIMARY KEY(provider,id));
            CREATE TABLE IF NOT EXISTS subscription_replacements(
                provider TEXT NOT NULL, reference_hash TEXT NOT NULL, owner TEXT NOT NULL,
                replacement_hash TEXT NOT NULL, PRIMARY KEY(provider,reference_hash));
            """)

    def verifier(self, provider):
        if provider not in self.config["providers"]:
            raise CreatorError("billing_provider_not_configured", 503)
        if self.verifier_factory:
            return self.verifier_factory(provider)
        from .billing_providers import AppleVerifier, GoogleVerifier
        return {"apple":AppleVerifier,"google":GoogleVerifier}[provider](self.config["providers"][provider])

    @property
    def sales_available(self):
        return any((c.get("sales_enabled") and c.get("qualified")) or c.get("test_sales_enabled")
                   for c in self.config["providers"].values())

    def status(self, owner):
        with self.store.db() as db:
            self.store.active(db, owner)
            records = db.execute("SELECT * FROM subscriptions WHERE owner=? ORDER BY expires DESC", (owner,)).fetchall()
        usable = [r for r in records if r["state"] in ACTIVE and r["expires"] > self.store.now() and r["verified"] > self.store.now()-900]
        chosen = max(usable, key=lambda r: (r["tier"] == "studio",r["expires"])) if usable else None
        entitlement = {"tier": chosen["tier"] if chosen else "free", "state": chosen["state"] if chosen else "none",
                       "expiresAt": chosen["expires"] if chosen else None, "provider": chosen["provider"] if chosen else None,
                       "environment": chosen["environment"] if chosen else None}
        unresolved = any(r["state"] in ("active","grace","canceled","hold","pending") and
                         (r["expires"] > self.store.now() or r["state"] in ("hold","pending")) for r in records)
        capabilities = {}
        for provider in ("apple","google"):
            cfg = self.config["providers"].get(provider, {})
            allowed = bool(((cfg.get("sales_enabled") and cfg.get("qualified")) or cfg.get("test_sales_enabled")) and not unresolved)
            if "sales_owners" in cfg:
                allowed = allowed and owner in cfg["sales_owners"]
            if cfg.get("environment") == "test":
                allowed = allowed and owner in cfg.get("test_owners", [])
            capabilities[provider] = {"purchase": allowed, "restore": bool(cfg),
                                      "reason": "manage_existing_subscription" if unresolved else "ready" if allowed else "sales_not_qualified"}
        return {"accountToken": account_token(owner), "products": PRODUCTS, "entitlement": entitlement,
                "capabilities": capabilities}

    def verify(self, owner, request, *, reconciliation=False):
        if request.provider == "apple" and not re.fullmatch(r"[0-9]{1,64}", request.reference):
            raise CreatorError("billing_reference_invalid")
        if any(c.isspace() for c in request.reference):
            raise CreatorError("billing_reference_invalid")
        verifier = self.verifier(request.provider)
        reference_hash = digest(request.reference)
        with self.store.db() as db:
            self.store.active(db, owner)
            if not reconciliation:
                self.store.rate(db, owner, "billing_verify", 100)
            if db.execute("SELECT 1 FROM billing_operations WHERE provider=? AND reference_hash=? AND state='running' AND started>?",
                          (request.provider, reference_hash, self.store.now()-180)).fetchone():
                raise CreatorError("billing_verification_pending", 409)
            operation = db.execute("INSERT INTO billing_operations(provider,reference_hash,owner,started,state) VALUES(?,?,?,?,'running')",
                                   (request.provider,reference_hash,owner,self.store.now())).lastrowid
        try:
            snapshot = verifier.fetch(request.reference)
            if not isinstance(snapshot, Snapshot) or snapshot.provider != request.provider or snapshot.tier not in ("creator","studio") or snapshot.state not in (*ACTIVE,"expired","pending","hold","revoked"):
                raise CreatorError("billing_provider_response_invalid", 503)
            product = next((p for p in PRODUCTS if p[request.provider+"ProductId"] == snapshot.product), None)
            if not product or product["tier"] != snapshot.tier or snapshot.account_token != account_token(owner):
                raise CreatorError("billing_account_mismatch", 403)
            cfg = self.config["providers"][request.provider]
            if snapshot.environment == "test" and owner not in cfg.get("test_owners", []):
                raise CreatorError("billing_test_account_required", 403)
            if snapshot.environment not in ("test","live"):
                raise CreatorError("billing_environment_mismatch", 503)
            if cfg["environment"] == "test" and snapshot.environment != "test":
                raise CreatorError("billing_environment_mismatch", 403)
            with self.store.db() as db:
                self.store.active(db, owner)
                tombstone = db.execute("SELECT owner FROM subscription_replacements WHERE provider=? AND reference_hash=?",
                                       (snapshot.provider,digest(snapshot.reference))).fetchone()
                if tombstone:
                    if tombstone["owner"] != owner:
                        raise CreatorError("billing_account_mismatch", 403)
                    raise CreatorError("billing_verification_superseded", 409)
                old = db.execute("SELECT * FROM subscriptions WHERE provider=? AND reference_hash=?", (snapshot.provider,digest(snapshot.reference))).fetchone()
                if old and old["owner"] != owner:
                    raise CreatorError("billing_account_mismatch", 403)
                if old and old["revision"] > operation:
                    raise CreatorError("billing_verification_superseded", 409)
                if snapshot.replaces:
                    if snapshot.replaces == snapshot.reference:
                        raise CreatorError("billing_provider_response_invalid", 503)
                    replaced = db.execute("SELECT owner FROM subscriptions WHERE provider=? AND reference_hash=?", (snapshot.provider,digest(snapshot.replaces))).fetchone()
                    if replaced and replaced["owner"] != owner:
                        raise CreatorError("billing_account_mismatch", 403)
                    lineage = db.execute("SELECT * FROM subscription_replacements WHERE provider=? AND reference_hash=?",
                                         (snapshot.provider,digest(snapshot.replaces))).fetchone()
                    if lineage and lineage["owner"] != owner:
                        raise CreatorError("billing_account_mismatch", 403)
                    if lineage and lineage["replacement_hash"] != digest(snapshot.reference):
                        raise CreatorError("billing_verification_superseded", 409)
                    db.execute("INSERT OR IGNORE INTO subscription_replacements VALUES(?,?,?,?)",
                               (snapshot.provider,digest(snapshot.replaces),owner,digest(snapshot.reference)))
                    db.execute("UPDATE subscriptions SET state='expired',revision=MAX(revision,?) WHERE provider=? AND reference_hash=? AND owner=?",
                               (operation,snapshot.provider,digest(snapshot.replaces),owner))
                encrypted = self.cipher.encrypt(snapshot.reference.encode()).decode()
                db.execute("""INSERT INTO subscriptions VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(provider,reference_hash) DO UPDATE SET
                    reference=excluded.reference,product=excluded.product,tier=excluded.tier,
                    state=excluded.state,expires=excluded.expires,environment=excluded.environment,
                    verified=excluded.verified,revision=excluded.revision""",
                    (snapshot.provider,digest(snapshot.reference),encrypted,owner,snapshot.product,snapshot.tier,
                     snapshot.state,snapshot.expires,snapshot.environment,self.store.now(),operation))
                db.execute("UPDATE billing_operations SET state='verified' WHERE id=?", (operation,))
            # Delivery is durable before acknowledging any store purchase.
            verifier.acknowledge(snapshot)
            return {"verified":True, **self.status(owner)}
        except CreatorError:
            with self.store.db() as db:
                db.execute("UPDATE billing_operations SET state='retry' WHERE id=? AND state='running'", (operation,))
            raise
        except Exception:
            with self.store.db() as db:
                db.execute("UPDATE billing_operations SET state='retry' WHERE id=? AND state='running'", (operation,))
            raise CreatorError("billing_provider_unavailable", 503) from None

    def restore(self, owner, *, reconciliation=False):
        with self.store.db() as db:
            self.store.active(db, owner)
            upper = db.execute("SELECT COALESCE(MAX(rowid),0) FROM subscriptions WHERE owner=?", (owner,)).fetchone()[0]
        failures = []
        cursor = 0
        while True:
            with self.store.db() as db:
                self.store.active(db, owner)
                query = """SELECT s.rowid AS cursor,provider,reference FROM subscriptions s
                    WHERE owner=? AND s.rowid>? AND s.rowid<=?
                    AND NOT EXISTS(SELECT 1 FROM subscription_replacements r
                        WHERE r.provider=s.provider AND r.reference_hash=s.reference_hash)"""
                query += (" AND state NOT IN ('expired','revoked') ORDER BY s.rowid LIMIT 10" if reconciliation else
                          " ORDER BY CASE WHEN state IN ('expired','revoked') THEN 1 ELSE 0 END, verified,expires DESC LIMIT 10")
                rows = db.execute(query, (owner,cursor,upper)).fetchall()
            for row in rows:
                try:
                    self.verify(owner, Verification(provider=row["provider"],reference=self.cipher.decrypt(row["reference"].encode()).decode()), reconciliation=reconciliation)
                except CreatorError as exc:
                    failures.append(exc)
            if not reconciliation or len(rows) < 10:
                break
            # Keyset pages cover the initial active set even as verification
            # changes states/revisions; concurrent inserts wait for the next run.
            cursor = rows[-1]["cursor"]
        if failures:
            raise failures[0]
        return self.status(owner)

    def reconcile(self):
        with self.store.db() as db:
            owners = [r[0] for r in db.execute("SELECT DISTINCT s.owner FROM subscriptions s JOIN users u ON u.id=s.owner WHERE u.state='active' AND s.state NOT IN ('expired','revoked')")]
        result = {"checked":0,"retry":0}
        for owner in owners:
            try:
                self.restore(owner, reconciliation=True)
                result["checked"] += 1
            except CreatorError:
                result["retry"] += 1
        return result
