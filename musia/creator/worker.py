"""One-shot private ACE worker. Never invoked directly by an HTTP request."""

import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys

from musia.learning import ROOT
from .contracts import Brief
from .review import audio_digest


def run(command, log, *, timeout=7200):
    with log.open("ab") as output:
        process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True,
                                   env={**os.environ, "PYTHONNOUSERSITE": "1"})
        try:
            if process.wait(timeout=timeout):
                raise RuntimeError("Worker stage failed; inspect private log")
        except BaseException:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            raise


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
    processes = subprocess.check_output(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"], text=True, timeout=15)
    if processes.strip():
        raise RuntimeError("GPU is occupied; leave jobs queued and preserve other projects")


def work_once(store):
    resource_check()
    with (store.directory / "worker.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
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
                 "--model", "large-v3"], folder / "worker.log")
            store.result(job["id"], job["lease"], audio=str(audio), audio_hash=checksum,
                         review=str(folder / "review"))
        except BaseException:
            # No automatic retry: the next user render needs a new confirmed reservation.
            store.result(job["id"], job["lease"], error="generation_failed")
            raise
        return True
