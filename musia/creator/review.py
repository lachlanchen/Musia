"""The selected audio, not the planned lyric, owns the publishable transcript."""

import hashlib
import math


def audio_digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024*1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def validate_audit(audit, audio_hash):
    if not isinstance(audit, dict) or audit.get("audioSha256") != audio_hash:
        raise ValueError("Audit must bind the selected audio digest")
    for check in ("listeningPassed", "inputCompared", "asrCompared", "gapsAndTailChecked", "contentApproved"):
        if audit.get(check) is not True:
            raise ValueError("Listening, ASR, source, gaps/tail and content review are mandatory")
    duration = audit.get("duration")
    if type(duration) not in (int, float) or not math.isfinite(duration) or not 1 <= duration <= 240:
        raise ValueError("Actual audio duration required")
    lines = audit.get("lines")
    if not isinstance(lines, list) or not 1 <= len(lines) <= 200:
        raise ValueError("Corrected timed sung lines required")
    previous = 0
    for line in lines:
        if not isinstance(line, dict) or set(line) != {"start", "end", "text", "language"}:
            raise ValueError("Each line needs start/end/text/language")
        start, end, text = line["start"], line["end"], line["text"]
        if type(start) not in (int, float) or type(end) not in (int, float) or not previous <= start < end <= duration:
            raise ValueError("Lyric times must be ordered, finite and inside the selected audio")
        if not isinstance(text, str) or not text.strip() or len(text) > 500 or text.strip() in ("♪", "♪♪♪", "[Instrumental]", "[Intro]", "[Outro]"):
            raise ValueError("Instrumental gaps are not lyric lines")
        if line["language"] not in ("en", "zh", "ja", "mixed"):
            raise ValueError("Each line needs its actual sung language")
        previous = end
