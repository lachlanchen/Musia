"""One-shot private ACE worker. Never invoked directly by an HTTP request."""

import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import csv
import time

from musia.learning import ROOT
from .contracts import Brief
from .review import audio_digest


class WorkerOutcomeUnknown(RuntimeError):
    """Execution could not be confirmed stopped; keep the ledger reservation."""


def owned_group(process):
    # WNOWAIT keeps our child PID allocated even after exit, preventing group-ID
    # reuse until all destructive signals are finished and wait() reaps it.
    os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    if os.getpgid(process.pid) != process.pid or os.getsid(process.pid) != process.pid or process.pid == os.getpgrp():
        raise WorkerOutcomeUnknown("Worker group ownership changed; refusing to signal")


def wait_leader(process, timeout):
    deadline = time.monotonic() + timeout
    while True:
        result = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        if result is not None:
            return result.si_status if result.si_code == os.CLD_EXITED else -result.si_status
        if time.monotonic() >= deadline:
            raise subprocess.TimeoutExpired(process.args, timeout)
        time.sleep(0.05)


def stop_group(process):
    try:
        owned_group(process)
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            wait_leader(process, 15)
        except subprocess.TimeoutExpired:
            pass
        # The leader may have exited while descendants still own the group.
        owned_group(process)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=15)
        deadline = time.monotonic() + 5
        while True:
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                return
            if time.monotonic() >= deadline:
                raise WorkerOutcomeUnknown("Worker process group remains; reconciliation required")
            time.sleep(0.05)
    except BaseException as exc:
        raise WorkerOutcomeUnknown("Worker cleanup uncertain; reconciliation required") from exc


def run(command, log, *, timeout=7200):
    with log.open("ab") as output:
        process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True,
                                   env={**os.environ, "PYTHONNOUSERSITE": "1"})
        try:
            owned_group(process)
            if wait_leader(process, timeout):
                raise RuntimeError("Worker stage failed; inspect private log")
        except BaseException:
            stop_group(process)
            raise
        stop_group(process)


def prepare(job, directory):
    brief = Brief.model_validate_json(job["brief"])
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    lyrics, caption = directory / "lyrics.txt", directory / "caption.txt"
    lyrics.write_text(brief.lyrics, encoding="utf-8")
    caption.write_text(brief.caption, encoding="utf-8")
    return [sys.executable, str(ROOT / "scripts/run_ace_candidate_sweep.py"),
            "--lyrics", str(lyrics), "--caption", str(caption), "--output-dir", str(directory / "render"),
            "--seeds", str(int(job["id"][:8], 16) % 2_000_000_000), "--duration", str(brief.duration),
            "--bpm", str(brief.bpm), "--key", brief.key, "--language", "unknown" if brief.language == "mixed" else brief.language]


def resource_check():
    memory = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        memory[key] = int(value.strip().split()[0])
    if memory["MemAvailable"] < 24*1024*1024 or (memory["SwapTotal"] and memory["SwapFree"] < memory["SwapTotal"]*.25):
        raise RuntimeError("Insufficient shared-workstation memory; leave jobs queued")
    device = os.environ.get("CUDA_VISIBLE_DEVICES", "0")
    if not device.isdigit():
        raise RuntimeError("Worker requires one explicitly selected GPU index")
    output = subprocess.check_output(["nvidia-smi", "--id="+device,
        "--query-gpu=memory.total,memory.free,utilization.gpu", "--format=csv,noheader,nounits"],
        text=True, timeout=15)
    rows = list(csv.reader(output.splitlines()))
    if len(rows) != 1:
        raise RuntimeError("Expected exactly one GPU")
    total, free, utilization = (int(x.strip()) for x in rows[0])
    # Small idle resident services need not block an otherwise available card.
    # Never evict a process; a busy card or insufficient actual VRAM stays queued.
    if free < 22*1024 or free < total*.90 or utilization > 5:
        raise RuntimeError("Selected GPU lacks an idle 22 GiB budget; leave jobs queued")


def work_once(store):
    with (store.directory / "worker.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with store.db() as db:
            pending = db.execute("SELECT 1 FROM jobs WHERE state='queued' AND input_approved=1 LIMIT 1").fetchone()
        if not pending:
            return False
        resource_check()
        job = store.claim()
        if not job:
            return False
        folder = store.directory / "artifacts" / job["id"]
        try:
            command = prepare(job, folder)
            run(command, folder / "worker.log")
            candidates = json.loads((folder / "render/candidates.json").read_text())
            if len(candidates) != 1:
                raise ValueError("Expected one metered render")
            source = Path(candidates[0]["audio"])
            if source.is_symlink() or not source.resolve().is_relative_to((folder / "render").resolve()):
                raise ValueError("Invalid worker output location")
            audio = folder / "song.wav"
            shutil.copyfile(source, audio)
            checksum = audio_digest(audio)
            if checksum != candidates[0]["sha256"]:
                raise ValueError("Worker audio digest changed")
            brief = Brief.model_validate_json(job["brief"])
            # Mixed vocals require per-phrase multilingual follow-up before approval.
            # This blind full-mix pass is evidence, never automatic lyric truth.
            run([sys.executable, str(ROOT / "scripts/review_ace_candidate_audio.py"),
                 str(folder / "render/candidates.json"), str(folder / "review"),
                 "--language", "en" if brief.language == "mixed" else brief.language,
                 "--model", "large-v3", "--window-crosscheck"], folder / "worker.log")
            store.result(job["id"], job["lease"], audio=str(audio), audio_hash=checksum,
                         review=str(folder / "review"))
        except WorkerOutcomeUnknown:
            # Leave running/reserved: neither a refund nor another claim is safe.
            raise
        except BaseException:
            # No automatic retry: the next user render needs a new confirmed reservation.
            store.result(job["id"], job["lease"], error="generation_failed")
            raise
        return True
