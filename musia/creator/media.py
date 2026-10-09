"""Private, full-length playback derivatives; no models or HTTP work.

The caller must hold the parent worker lock across prepare_playback and all
artifact deletion/writes. Path checks are not a substitute for that lock. The
caller also owns authorization and selecting song.wav from its artifact root;
this two-argument helper cannot establish job ownership. A returned Path is not
an open file: serving/deletion races still belong to the parent API.

prepare_playback raises on failure; workers should retain the WAV fallback and
record only the error type privately. playback_path never runs subprocesses.
playback.json is the last, atomic completion marker, not a client-supplied path.
"""

from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
from typing import Optional


MAX_FILE_BYTES = 128 * 1024 * 1024
MAX_MANIFEST_BYTES = 16 * 1024
MAX_DURATION = 240.0
DURATION_TOLERANCE = 0.12
SCHEMA = "musia-creator-playback-v1"
_PROFILE = {
    "schema": SCHEMA,
    "source_path": "song.wav",
    "playback_path": "song.mp3",
    "codec": "mp3",
    "bit_rate": 320000,
    "channels": 2,
    "sample_rate": 48000,
}
_FIELDS = set(_PROFILE) | {
    "source_sha256", "playback_sha256", "source_duration", "playback_duration",
}


def _is_digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _source_path(source, expected):
    if not _is_digest(expected):
        raise ValueError("Expected a lowercase SHA-256 digest")
    source = Path(source).absolute()
    if source.name != "song.wav" or source.resolve(strict=True) != source:
        raise ValueError("Source must be a real song.wav path")
    root = source.parent.stat()
    if not stat.S_ISDIR(root.st_mode) or root.st_uid != os.getuid() or root.st_mode & 0o077:
        raise ValueError("Playback root must be an owned private directory")
    return source, (root.st_dev, root.st_ino)


def _stamp(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _check_file(info, limit, private):
    # The worker's original WAV may be 0644 inside its 0700 job directory.
    unsafe_mode = 0o077 if private else 0o022
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
            or info.st_nlink != 1 or info.st_mode & unsafe_mode
            or info.st_size > limit):
        raise ValueError("Expected a bounded owned regular playback file")


def _state(path, limit=MAX_FILE_BYTES, private=True):
    info = path.lstat()
    _check_file(info, limit, private)
    return _stamp(info)


def _optional_state(path, limit):
    try:
        return _state(path, limit)
    except FileNotFoundError:
        return None


def _read(path, *, limit=MAX_FILE_BYTES, private=True, digest=True):
    before = _state(path, limit, private)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(fd, "rb") as stream:
        if _stamp(os.fstat(stream.fileno())) != before:
            raise ValueError("Playback file changed while opening")
        checksum, chunks, size = hashlib.sha256(), [], 0
        while True:
            block = stream.read(min(1024 * 1024, limit + 1 - size))
            if not block:
                break
            size += len(block)
            if size > limit:
                raise ValueError("Playback file exceeds size bound")
            if digest:
                checksum.update(block)
            else:
                chunks.append(block)
        if (not size or _stamp(os.fstat(stream.fileno())) != before
                or _state(path, limit, private) != before):
            raise ValueError("Playback file is empty or changed while reading")
    return (checksum.hexdigest() if digest else b"".join(chunks)), before


def _verify_source(source, expected, root):
    if _source_path(source, expected)[1] != root:
        raise ValueError("Playback root changed")
    observed, state = _read(source, private=False)
    if observed != expected:
        raise ValueError("Original WAV digest mismatch")
    return state


def _duration(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= MAX_DURATION:
        raise ValueError("Invalid playback duration")
    return float(value)


def _durations(source, playback):
    if abs(_duration(source) - _duration(playback)) > DURATION_TOLERANCE:
        raise ValueError("Playback duration differs from the full source")


def _valid_pair(source, expected, source_state):
    try:
        raw, manifest_state = _read(source.with_name("playback.json"),
                                    limit=MAX_MANIFEST_BYTES, digest=False)
        manifest = json.loads(raw)
        if (not isinstance(manifest, dict) or set(manifest) != _FIELDS
                or any(type(manifest[key]) is not type(value) or manifest[key] != value
                       for key, value in _PROFILE.items())
                or manifest["source_sha256"] != expected
                or not _is_digest(manifest["playback_sha256"])):
            return None
        _durations(manifest["source_duration"], manifest["playback_duration"])
        playback = source.with_name("song.mp3")
        observed, _ = _read(playback)
        if (observed != manifest["playback_sha256"]
                or _state(source, private=False) != source_state
                or _state(source.with_name("playback.json"), MAX_MANIFEST_BYTES) != manifest_state):
            return None
        return playback
    except (OSError, ValueError, OverflowError, RecursionError):
        return None


def playback_path(source: Path, expected_source_sha256: str) -> Optional[Path]:
    """Return the fixed MP3 only for a complete, exact-digest pair; else None.

    Bounded local hashing only, with no probing, transcoding, writes or repair.
    The parent API must use its original WAV fallback when this returns None.
    """
    try:
        source, root = _source_path(source, expected_source_sha256)
        state = _verify_source(source, expected_source_sha256, root)
        return _valid_pair(source, expected_source_sha256, state)
    except (OSError, ValueError, TypeError, RuntimeError):
        return None


def _probe(path, format_name):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-protocol_whitelist", "file", "-threads", "1",
         "-f", format_name, "-show_entries",
         "format=duration:stream=codec_name,codec_type,sample_rate,channels,bit_rate",
         "-of", "json", str(path)],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, check=True, timeout=15,
    )
    try:
        data = json.loads(result.stdout)
        duration = _duration(float(data["format"]["duration"]))
        streams = data["streams"]
        if len(streams) != 1 or streams[0]["codec_type"] != "audio":
            raise ValueError("Expected one audio stream")
        if format_name == "mp3":
            stream = streams[0]
            if (stream["codec_name"] != "mp3" or int(stream["sample_rate"]) != 48000
                    or stream["channels"] != 2 or int(stream["bit_rate"]) != 320000):
                raise ValueError("Unexpected playback encoding")
        return duration
    except (KeyError, TypeError, IndexError, OverflowError, RecursionError) as error:
        raise ValueError("Invalid audio probe metadata") from error


@contextmanager
def _temporary(root, suffix):
    fd, name = tempfile.mkstemp(prefix=".playback-", suffix=suffix, dir=root)
    path = Path(name)
    os.close(fd)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def _sync(path, *, directory=False):
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    if directory:
        flags |= os.O_DIRECTORY
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def prepare_playback(source: Path, expected_source_sha256: str) -> Path:
    """Worker-only full WAV -> 320 kbps stereo/48 kHz MP3, with one CPU thread.

    Hold the parent worker/deletion lock for the entire call. Reuse a valid pair
    without touching it. Invalid/partial owned private finals are replaced only
    after a complete conversion is validated and their original states rechecked.
    Unsafe finals are refused, not removed. Interrupted publication can leave an
    invalid pair; lookup falls back and a later locked call can repair it.

    playback.json v1 records source_path/source_sha256/source_duration and
    playback_path/playback_sha256/playback_duration plus the fixed codec profile.
    Durations are seconds, both at most 240, differing by at most 0.12 seconds.
    No trimming, model inference, re-synthesis, or modification of the WAV.
    """
    source, root = _source_path(source, expected_source_sha256)
    source_state = _verify_source(source, expected_source_sha256, root)
    accepted = _valid_pair(source, expected_source_sha256, source_state)
    if accepted is not None:
        return accepted
    playback, manifest = source.with_name("song.mp3"), source.with_name("playback.json")
    before = (_optional_state(playback, MAX_FILE_BYTES),
              _optional_state(manifest, MAX_MANIFEST_BYTES))
    with _temporary(source.parent, ".mp3") as staged_audio, \
            _temporary(source.parent, ".json") as staged_manifest:
        try:
            source_duration = _probe(source, "wav")
            subprocess.run(
                ["ffmpeg", "-v", "error", "-nostdin", "-y", "-protocol_whitelist", "file",
                 "-threads", "1", "-f", "wav", "-i", str(source), "-map", "0:a:0",
                 "-vn", "-sn", "-dn", "-map_metadata", "-1", "-map_chapters", "-1",
                 "-c:a", "libmp3lame", "-b:a", "320k", "-ac", "2", "-ar", "48000",
                 "-threads", "1", "-filter_threads", "1", "-f", "mp3", str(staged_audio)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                check=True, timeout=120,
            )
            _state(staged_audio)
            playback_duration = _probe(staged_audio, "mp3")
            _durations(source_duration, playback_duration)
            _sync(staged_audio)
            playback_sha256, _ = _read(staged_audio)
        finally:
            # Verify even after a failed encoder/probe, without ever fixing a WAV.
            _verify_source(source, expected_source_sha256, root)
        payload = {**_PROFILE, "source_sha256": expected_source_sha256,
                   "playback_sha256": playback_sha256, "source_duration": source_duration,
                   "playback_duration": playback_duration}
        with staged_manifest.open("w", encoding="utf-8") as output:
            json.dump(payload, output, sort_keys=True, allow_nan=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        source_state = _verify_source(source, expected_source_sha256, root)
        accepted = _valid_pair(source, expected_source_sha256, source_state)
        if accepted is not None:
            return accepted
        current = (_optional_state(playback, MAX_FILE_BYTES),
                   _optional_state(manifest, MAX_MANIFEST_BYTES))
        if current != before:
            raise ValueError("Playback destinations changed; caller lock required")
        os.replace(staged_audio, playback)
        _sync(source.parent, directory=True)
        os.replace(staged_manifest, manifest)
        _sync(source.parent, directory=True)
    return playback
