"""Bounded private maintenance. Never deletes active-owner media or peer files."""

from contextlib import ExitStack, contextmanager
import fcntl
import os
import re
import shutil
import sqlite3
import stat

from .supervisor import supervisor_lock


@contextmanager
def _worker_lock(directory):
    fd = os.open(directory / "worker.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(fd)
        # Older workers created this lock with the process umask inside 0700 storage.
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid():
            raise ValueError("Invalid worker lock file")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def _check_private_file(info):
    if (not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077
            or info.st_nlink != 1 or info.st_uid != os.getuid()):
        raise ValueError("Supervisor journal must be a private owned regular file")


def _purge_supervisor_evidence(directory, jobs):
    """Called with supervisor then worker locks held; never initialize a journal."""
    path = (directory / "supervisor.sqlite").absolute()
    try:
        original = path.lstat()
    except FileNotFoundError:
        return 0, 0
    _check_private_file(original)
    if original.st_size < 100:
        raise ValueError("Invalid existing supervisor journal")
    total_size = original.st_size
    for suffix in ("-wal", "-shm", "-journal"):
        try:
            info = path.with_name(path.name + suffix).lstat()
            _check_private_file(info)
            total_size += info.st_size
        except FileNotFoundError:
            pass
    if total_size > 64 * 1024 * 1024:
        raise ValueError("Supervisor journal exceeds bounded cleanup size; operator maintenance required")
    # Let SQLite validate/open its own file: closing an unrelated raw fd for the
    # same inode can release another connection's process-wide POSIX locks.
    db = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, timeout=0)
    try:
        current = path.lstat()
        _check_private_file(current)
        if (original.st_dev, original.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError("Supervisor journal changed while opening")
        db.execute("PRAGMA trusted_schema=OFF")
        tables = {
            "runs": {"id", "config", "passes", "actions", "dispatches", "reviews", "reserved_microusd"},
            "attempts": {"id", "run_id", "stage", "job", "status", "evidence"},
            "output_evidence": {"job", "expected_sha256", "observed_sha256", "status", "checked_at"},
        }
        db.execute("PRAGMA secure_delete=ON")
        removed, redacted = 0, 0
        with db:
            db.execute("BEGIN IMMEDIATE")
            for table, columns in tables.items():
                if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
                    raise ValueError("Unexpected supervisor journal schema")
                if {row[1] for row in db.execute(f"PRAGMA table_info({table})")} != columns:
                    raise ValueError("Unexpected supervisor journal columns")
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='trigger'").fetchone():
                raise ValueError("Unexpected supervisor journal trigger")
            for job in jobs:
                removed += db.execute("DELETE FROM attempts WHERE stage='input' AND job=?", (job,)).rowcount
                removed += db.execute("DELETE FROM output_evidence WHERE job=?", (job,)).rowcount
                redacted += db.execute("UPDATE attempts SET evidence='{}' WHERE stage='dispatch' "
                                       "AND job=? AND evidence!='{}'", (job,)).rowcount
        # Historical updates without secure_delete can leave old values in free space.
        # Repeat on retry even when a previous cleanup committed its row deletions.
        db.execute("VACUUM")
        if db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0]:
            raise sqlite3.OperationalError("Supervisor journal checkpoint busy; retry maintenance")
        return removed, redacted
    finally:
        db.close()


def purge_deleted(store):
    result = {"removed": 0, "waitingForWorker": False, "waitingForSupervisor": False,
              "supervisorEvidenceRemoved": 0, "supervisorEvidenceRedacted": 0}
    with ExitStack() as locks:
        try:
            locks.enter_context(supervisor_lock(store.directory))
        except BlockingIOError:
            return {**result, "waitingForSupervisor": True}
        try:
            locks.enter_context(_worker_lock(store.directory))
        except BlockingIOError:
            return {**result, "waitingForWorker": True}
        with store.db() as db:
            jobs = [row[0] for row in db.execute("SELECT j.id FROM jobs j JOIN users u ON u.id=j.owner WHERE u.state='deleted'")]
        if any(not re.fullmatch(r"[a-f0-9]{32}", job) for job in jobs):
            raise ValueError("Invalid owned artifact identity")
        root = store.directory / "artifacts"
        if root.is_symlink():
            raise ValueError("Refuse symlink artifact root")
        if jobs:
            result["supervisorEvidenceRemoved"], result["supervisorEvidenceRedacted"] = _purge_supervisor_evidence(
                store.directory, jobs)
        for job in jobs:
            folder = root / job
            if folder.is_symlink():
                folder.unlink()
                result["removed"] += 1
            elif folder.exists():
                if not folder.is_dir() or folder.resolve() != folder.absolute():
                    raise ValueError("Unexpected artifact location")
                shutil.rmtree(folder)
                result["removed"] += 1
    return result
