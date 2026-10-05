"""Read-only, public projection of the Fun catalog, with one synthetic exercise."""

from __future__ import annotations

import io
import json
import math
import os
import re
import sys
import threading
import wave
from array import array
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUBLIC_BASE_URL = "https://musia.lazying.art"
MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_STATIC_BYTES = 8 * 1024 * 1024
MAX_ITEMS = 256
MAX_ASSETS = 16
MAX_EVENTS = 8192
MAX_DURATION = 6 * 60 * 60
SAMPLE_RATE = 24000
EXERCISE_SECONDS = 22
EXERCISE_BARS = ((4, 8, "Em"), (8, 12, "Am"), (12, 16, "Em"), (16, 20, "Am"))
ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")
FILE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,199}\Z")
NONPUBLIC = re.compile(r"(?:^|[^a-z])(preview|unlisted|private|draft|experimental|hidden|demo|legacy)(?:$|[^a-z])", re.I)
PRIVATE_PATH = re.compile(r"file:|/(?:home|Users|tmp|mnt|var|etc)/|data/(?:runs|creative_projects)/|[A-Za-z]:[\\/]", re.I)

# Each URL names one public file; neither a directory mount nor an SPA fallback.
STATIC_FILES = {
    "/": ("apps/web/index.html", "text/html"),
    "/index.html": ("apps/web/index.html", "text/html"),
    "/app.js": ("apps/web/app.js", "text/javascript"),
    "/core.js": ("apps/web/core.js", "text/javascript"),
    "/guitar-shapes.js": ("apps/web/guitar-shapes.js", "text/javascript"),
    "/styles.css": ("apps/web/styles.css", "text/css"),
    "/privacy": ("apps/web/privacy.html", "text/html"),
    "/privacy.html": ("apps/web/privacy.html", "text/html"),
    "/support": ("apps/web/support.html", "text/html"),
    "/support.html": ("apps/web/support.html", "text/html"),
    "/vendor/lucide.js": ("apps/web/vendor/lucide.js", "text/javascript"),
    "/assets/musia.js": ("website/musia.js", "text/javascript"),
    "/assets/brand.png": ("website/assets/brand/fun-lazying-art-logo.png", "image/png"),
}


def _object(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _rows(value: Any, limit: int = MAX_EVENTS) -> list[dict]:
    return [row for row in value[:limit] if isinstance(row, dict)] if isinstance(value, list) else []


def _text(value: Any, limit: int = 512) -> str:
    if not isinstance(value, str) or len(value) > limit or PRIVATE_PATH.search(value):
        return ""
    if any(ord(c) < 32 and c not in "\n\t" for c in value):
        return ""
    return value.strip()


def _id(value: Any) -> str:
    return value if isinstance(value, str) and ID_PATTERN.fullmatch(value) else ""


def pinyin_tones(value: str) -> str:
    """Format supplied pronunciation only; never infer a character's reading."""
    def syllable(match):
        letters = match[1].replace("u:", "ü").replace("U:", "Ü").replace("v", "ü").replace("V", "Ü")
        tone = int(match[2])
        if tone in (0, 5):
            return letters
        lower = letters.lower()
        index = next((lower.index(v) for v in ("a", "e") if v in lower), -1)
        if index < 0 and "ou" in lower:
            index = lower.index("o")
        if index < 0:
            index = next((i for i in range(len(lower) - 1, -1, -1) if lower[i] in "iouü"), -1)
        if index < 0:
            return match[0]
        mark = {"a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "ü": "ǖǘǚǜ"}[lower[index]][tone - 1]
        if letters[index].isupper():
            mark = mark.upper()
        return letters[:index] + mark + letters[index + 1:]
    return re.sub(r"([A-Za-züÜ:]+)([0-5])", syllable, value)


def _number(value: Any, low: float = 0, high: float = MAX_DURATION) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) and low <= value <= high else None


def _span(row: dict, duration: float) -> dict | None:
    start, end = _number(row.get("start")), _number(row.get("end"))
    if start is None or end is None or not start < end or start >= duration:
        return None
    return {"start": start, "end": min(end, duration)}


def _listed(data: dict) -> bool:
    for source in (data, _object(data.get("publication"))):
        if any(source.get(key, False) is not False for key in ("hidden", "private", "unlisted", "preview", "experimental")):
            return False
        if source.get("listed", True) is not True:
            return False
        if source.get("visibility", "public") != "public":
            return False
        if any(source.get(key, "published") != "published" for key in ("stage", "releaseStage", "status")):
            return False
        for key in ("id", "title", "label", "category", "previewLabel", "hiddenLabel"):
            if NONPUBLIC.search(str(source.get(key, ""))):
                return False
        tags = source.get("tags")
        if isinstance(tags, list) and any(NONPUBLIC.search(str(tag)) for tag in tags):
            return False
    return "publication" not in data or isinstance(data["publication"], dict)


def _file(root: Path, relative: str) -> Path:
    parts = relative.split("/")
    if any(not FILE_PATTERN.fullmatch(part) or part in (".", "..") for part in parts):
        raise ValueError("Invalid public file")
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("Invalid public file")
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise ValueError("Missing public file")
    return path


def _read(root: Path, relative: str, limit: int) -> bytes:
    path = _file(root, relative)
    with path.open("rb") as handle:
        content = handle.read(limit + 1)
    if len(content) > limit:
        raise ValueError("Public file too large")
    return content


def _reject_constant(value: str) -> None:
    raise ValueError("Non-finite JSON number")


def _json(root: Path, relative: str) -> dict:
    try:
        data = json.loads(_read(root, relative, MAX_JSON_BYTES), parse_constant=_reject_constant)
        return _object(data)
    except (OSError, ValueError, RecursionError):
        return {}


def _public_url(value: Any, kind: str) -> str:
    if not isinstance(value, str) or len(value) > 1024 or re.search(r"[\s\\%]", value):
        return ""
    if kind == "cover" and value.startswith("assets/"):
        value = "https://fun.lazying.art/" + value
    try:
        url = urlsplit(value)
        if url.scheme != "https" or url.username or url.password or url.query or url.fragment or url.port:
            return ""
    except ValueError:
        return ""
    prefixes = {
        "cover": (("fun.lazying.art", "/assets/covers/"), ("fun.lazying.art", "/assets/brand/")),
        "audio": (("lazyingart.github.io", "/MusiaSongs/audio/"), ("fun.lazying.art", "/audio/")),
    }
    extensions = (".png", ".jpg", ".jpeg", ".webp") if kind == "cover" else (".mp3", ".wav", ".ogg", ".m4a", ".flac")
    for host, prefix in prefixes[kind]:
        if url.netloc == host and url.path.startswith(prefix):
            filename = url.path[len(prefix):]
            if FILE_PATTERN.fullmatch(filename) and filename.lower().endswith(extensions):
                return value
    return ""


def _base_url(value: str) -> str:
    try:
        if not isinstance(value, str) or len(value) > 1024 or re.search(r"[\s\\%]", value):
            raise ValueError
        url = urlsplit(value)
        if not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in ("", "/"):
            raise ValueError
        if url.scheme != "https" and not (url.scheme == "http" and url.hostname in ("localhost", "127.0.0.1", "::1")):
            raise ValueError
        if url.port is not None and not 1 <= url.port <= 65535:
            raise ValueError
        if not re.fullmatch(r"[A-Za-z0-9.:-]+", url.hostname):
            raise ValueError
        return value.rstrip("/")
    except (ValueError, TypeError):
        raise ValueError("MUSIA_PUBLIC_BASE_URL must be an HTTPS origin or a loopback HTTP origin, without credentials") from None


def _confidence(value: Any, events: list) -> str:
    if not events:
        return "unavailable"
    # A public analysis label is not proof of a human-verified transcription.
    return "estimated" if value == "estimated" else "analysis"


class PublicLibrary:
    def __init__(self, root: Path):
        self.root = root

    def entries(self) -> list[dict]:
        catalog = _json(self.root, "website/data/catalog.json")
        return [item for item in _rows(catalog.get("items"), MAX_ITEMS)
                if _id(item.get("id")) and item.get("id") != "first-pulse"
                and item.get("kind") in ("song", "localized-song") and _listed(item)]

    def manifest(self, item: dict) -> dict:
        relative = f"data/songs/{item['id']}/manifest.json"
        if item.get("manifest") != relative:
            return {}
        manifest = _json(self.root, "website/" + relative)
        if manifest.get("id") != item["id"] or not _listed(manifest):
            return {}
        return manifest

    def audio_assets(self, manifest: dict) -> list[dict]:
        container = _object(manifest.get("assets"))
        candidates = [_object(container.get("primaryAudio"))] + _rows(container.get("alternateAudio"), MAX_ASSETS - 1)
        result, seen = [], set()
        for asset in candidates:
            asset_id = _id(asset.get("id"))
            if asset_id and asset_id not in seen and _listed(asset) and _public_url(asset.get("src"), "audio"):
                result.append(asset)
                seen.add(asset_id)
        return result

    def metadata(self, item: dict, manifest: dict) -> dict | None:
        cover = _public_url(item.get("cover"), "cover") or _public_url(
            _object(_object(manifest.get("assets")).get("cover")).get("src"), "cover")
        title = _text(manifest.get("title")) or _text(item.get("title"))
        artist = _text(manifest.get("artist")) or _text(item.get("artist"))
        if not cover or not title or not artist:
            return None
        return {"id": item["id"], "title": title, "artist": artist, "coverUrl": cover}

    def lyric_tracks(self, song_id: str, manifest: dict, asset: dict, duration: float) -> list[dict]:
        sets = _rows(manifest.get("lyricSets"), MAX_ASSETS)
        language = asset.get("languageCode")
        if asset.get("lyricSetId"):
            selected = [s for s in sets if s.get("id") == asset["lyricSetId"]]
        else:
            selected = [s for s in sets if s.get("languageCode") == language]
        if sets or asset.get("lyricSetId"):
            if len(selected) != 1 or not _listed(selected[0]):
                return []
            if selected[0].get("languageCode", language) != language:
                return []
            tracks = selected[0].get("textTracks", selected[0].get("tracks"))
        else:
            tracks = manifest.get("textTracks")
        candidates = [t for t in _rows(tracks, 32) if _id(t.get("code")) and _listed(t)]
        result = []
        for candidate in candidates:
            code = candidate["code"]
            # Ambiguous tracks must not silently borrow another vocal's translation.
            if sum(t["code"] == code for t in candidates) != 1:
                continue
            lines = self.lyric_lines(song_id, candidate, duration)
            if lines:
                result.append({"language": code, "lines": lines})
        return result

    def lyrics(self, song_id: str, manifest: dict, asset: dict, duration: float) -> list[dict]:
        return next((t["lines"] for t in self.lyric_tracks(song_id, manifest, asset, duration)
                     if t["language"] == asset.get("languageCode")), [])

    def lyric_lines(self, song_id: str, descriptor: dict, duration: float) -> list[dict]:
        path, language = descriptor.get("path"), descriptor["code"]
        if not isinstance(path, str) or not path.startswith("lyrics/") or not path.endswith(".json"):
            return []
        track = _json(self.root, f"website/data/songs/{song_id}/{path}")
        if _object(track.get("language")).get("code") != language or not _listed(track):
            return []
        result, seen = [], set()
        for row in _rows(track.get("lines"), 512):
            span, text = _span(row, duration), _text(row.get("text"), 2048)
            if not span or not text or row.get("role") == "instrumental" or text in ("\u266a", "\u266a\u266a\u266a"):
                continue
            line_id = _id(row.get("id")) or f"line-{len(result) + 1}"
            if line_id in seen:
                continue
            tokens = []
            for token in _rows(row.get("tokens"), 256):
                timing, word = _span(token, span["end"]), _text(token.get("text"), 256)
                if timing and word and timing["start"] >= span["start"]:
                    clean = {"text": word, **timing}
                    reading = _text(token.get("reading"), 256) or _text(token.get("pinyin"), 256)
                    if reading:
                        clean["reading"] = pinyin_tones(reading) if language.startswith("zh") else reading
                    tokens.append(clean)
            result.append({"id": line_id, **span, "text": text, "tokens": sorted(tokens, key=lambda t: t["start"])})
            seen.add(line_id)
        return sorted(result, key=lambda row: row["start"])

    def asset(self, song_id: str, manifest: dict, source: dict, study: dict) -> dict | None:
        audio_url = _public_url(source.get("src"), "audio")
        # Never attach an old vocal's analysis to a replaced or different recording.
        if study.get("src") != source.get("src") or study.get("languageCode") != source.get("languageCode"):
            study = {}
        duration = (_number(source.get("duration"), 0.001) or _number(study.get("duration"), 0.001)
                    or _number(manifest.get("duration"), 0.001))
        if duration is None:
            return None
        musical = _object(source.get("musical"))
        beats = []
        for beat in _rows(study.get("beats", musical.get("beats"))):
            time = _number(beat.get("time"), 0, duration)
            if time is not None and time < duration:
                beats.append(time)
        beats = [{"time": time} for time in sorted(set(beats))]
        chords = []
        for chord in _rows(study.get("chords", musical.get("chords"))):
            span, name = _span(chord, duration), _text(chord.get("name"), 32)
            if span and name:
                clean = {**span, "name": name}
                confidence = _number(chord.get("confidence"), 0, 1)
                if confidence is not None:
                    clean["confidence"] = confidence
                chords.append(clean)
        melody = []
        for line in _rows(_object(study.get("melody")).get("lines"), 512):
            for token in _rows(line.get("tokens"), 256):
                span, note = _span(token, duration), _text(token.get("note"), 16)
                if span and note and len(melody) < MAX_EVENTS:
                    melody.append({**span, "note": note, "numberNote": _text(token.get("numberNote"), 32),
                                   "text": _text(token.get("text"), 256)})
        tracks = self.lyric_tracks(song_id, manifest, source, duration)
        lyrics = next((t["lines"] for t in tracks if t["language"] == source.get("languageCode")), [])
        signature = study.get("timeSignature", musical.get("timeSignature"))
        if not isinstance(signature, str) or not re.fullmatch(r"[1-9][0-9]?/(?:1|2|4|8|16|32)", signature):
            signature = None
        return {
            "id": source["id"], "label": _text(source.get("label")) or source["id"],
            "language": _id(source.get("languageCode")) or "und", "audioUrl": audio_url,
            "duration": duration, "bpm": _number(study.get("bpm", musical.get("bpm")), 1, 400),
            "timeSignature": signature,
            "confidence": {"beats": _confidence(study.get("beatConfidence"), beats),
                           "chords": _confidence(study.get("chordConfidence"), chords),
                           "melody": "analysis" if melody else "unavailable"},
            "beats": beats, "chords": sorted(chords, key=lambda c: c["start"]), "lyrics": lyrics,
            "lyricTracks": tracks,
            "phrases": [{key: line[key] for key in ("id", "start", "end", "text")} for line in lyrics],
            "melody": sorted(melody, key=lambda m: m["start"]),
        }

    def song(self, item: dict) -> dict | None:
        manifest = self.manifest(item)
        metadata = self.metadata(item, manifest) if manifest else None
        if not metadata:
            return None
        study = _json(self.root, f"website/data/songs/{item['id']}/study.json")
        if study.get("mediaId") != item["id"]:
            study = {}
        assets = []
        for source in self.audio_assets(manifest):
            asset = self.asset(item["id"], manifest, source, _object(_object(study.get("assets")).get(source["id"])))
            if asset:
                assets.append(asset)
        if not assets:
            return None
        default = study.get("defaultAssetId")
        if default not in {asset["id"] for asset in assets}:
            default = assets[0]["id"]
        return {"version": 1, **metadata, "assets": assets, "defaultAssetId": default}


def first_pulse(base_url: str) -> dict:
    asset = {
        "id": "first-pulse", "label": "First Pulse - Em / Am", "language": "und",
        "audioUrl": base_url + "/api/v1/exercises/first-pulse/audio.wav",
        "duration": EXERCISE_SECONDS, "bpm": 60, "timeSignature": "4/4",
        "confidence": {"beats": "verified", "chords": "verified", "melody": "unavailable"},
        "beats": [{"time": beat, "index": beat} for beat in range(20)],
        "chords": [{"start": start, "end": end, "name": name, "confidence": 1.0}
                   for start, end, name in EXERCISE_BARS],
        "lyrics": [], "lyricTracks": [], "melody": [],
        "phrases": [{"id": f"bar-{i + 1}", "start": start, "end": end, "text": name}
                    for i, (start, end, name) in enumerate(EXERCISE_BARS)],
    }
    return {"version": 1, "id": "first-pulse", "title": "First Pulse", "artist": "Musia",
            "coverUrl": base_url + "/assets/brand.png", "assets": [asset], "defaultAssetId": asset["id"]}


_audio_lock = threading.Lock()


@lru_cache(maxsize=1)
def _synthesize_first_pulse() -> bytes:
    samples = array("d", [0.0]) * (SAMPLE_RATE * EXERCISE_SECONDS)
    click_length = SAMPLE_RATE // 20
    for beat in range(20):
        offset = beat * SAMPLE_RATE
        frequency = 1400 if beat % 4 == 0 else 1000
        for n in range(click_length):
            envelope = (1 - n / click_length) ** 4
            samples[offset + n] += 0.5 * envelope * math.cos(2 * math.pi * frequency * n / SAMPLE_RATE)
    for start, end, name in EXERCISE_BARS:
        notes = (52, 55, 59) if name == "Em" else (45, 48, 52)
        frequencies = [440 * 2 ** ((note - 69) / 12) for note in notes]
        length = ((EXERCISE_SECONDS if end == 20 else end) - start) * SAMPLE_RATE
        for n in range(length):
            time = n / SAMPLE_RATE
            envelope = min(1, n / (0.008 * SAMPLE_RATE)) * math.exp(-0.22 * time)
            if end == 20 and time >= 4:
                envelope *= max(0, (length - 1 - n) / (2 * SAMPLE_RATE)) ** 2
            elif end != 20:
                envelope *= min(1, (length - 1 - n) / (0.02 * SAMPLE_RATE))
            tone = sum(math.sin(2 * math.pi * f * time) for f in frequencies) / 3
            samples[start * SAMPLE_RATE + n] += 0.24 * envelope * tone
    pcm = array("h", (round(max(-1, min(1, sample)) * 32767) for sample in samples))
    if sys.byteorder != "little":
        pcm.byteswap()
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(SAMPLE_RATE)
        audio.writeframes(pcm.tobytes())
    return output.getvalue()


def first_pulse_wav() -> bytes:
    with _audio_lock:
        return _synthesize_first_pulse()


LESSONS = [
    {"id": "listen-first", "title": "Hear the Change", "focus": "listening",
     "body": "First Pulse starts with four count-in clicks. Four bars follow: Em, Am, Em, Am. Each bar lasts four seconds.",
     "exerciseId": "first-pulse", "steps": [
         "Listen once without playing. Count the opening clicks: one, two, three, four.",
         "Hear Em enter at 4 seconds and Am at 8 seconds. Notice the different chord colors.",
         "Listen for Em at 12 seconds and Am at 16 seconds. Let the final sound fade after 20 seconds."]},
    {"id": "tap-the-pulse", "title": "Keep a Steady Pulse", "focus": "pulse",
     "body": "At 60 BPM, one beat lasts one second. Tap lightly and keep the space between taps even.",
     "exerciseId": "first-pulse", "steps": [
         "Listen to the four count-in clicks at 0, 1, 2, and 3 seconds.",
         "Start tapping with Em at 4 seconds. Count one, two, three, four for each bar.",
         "Continue through all four bars; make your last tap at 19 seconds and stop at 20 seconds.",
         "Tap timing stays on your device. It is not a guitar or singing accuracy score; device latency can affect it."]},
    {"id": "em-am-switch", "title": "Move Between Em and Am", "focus": "chord-changes",
     "body": "Use a comfortable Em and Am fingering. Start with one gentle down-strum per bar, leaving time to prepare the next shape.",
     "exerciseId": "first-pulse", "steps": [
         "Form Em before playback and listen through the four count-in beats.",
         "Strum Em at 4 seconds, Am at 8 seconds, Em at 12 seconds, and Am at 16 seconds.",
         "Between changes, release excess pressure and prepare the next shape without rushing.",
         "When changes feel comfortable, try one gentle down-strum per click from 4 through 19 seconds, then let the chord ring."]},
]


def _json_response(payload: dict, cache: str = "public, max-age=30, must-revalidate") -> Response:
    content = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    if len(content) > MAX_JSON_BYTES:
        return JSONResponse({"detail": "Public data exceeds response limit"}, status_code=503)
    return Response(content, media_type="application/json", headers={"Cache-Control": cache})


class PublicBoundary:
    """Enforce a read-only surface and headers, including on errors and HEAD."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1008})
                return
            return await self.app(scope, receive, send)
        started = False

        async def secured_send(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                headers = dict(message.get("headers", []))
                headers.setdefault(b"cache-control", b"no-store")
                headers.update({
                    b"x-content-type-options": b"nosniff", b"x-frame-options": b"DENY",
                    b"referrer-policy": b"no-referrer",
                    b"permissions-policy": b"camera=(), microphone=(), geolocation=(), payment=()",
                    b"content-security-policy": (
                        b"default-src 'none'; script-src 'self'; style-src 'self'; "
                        b"img-src 'self' https://fun.lazying.art; "
                        b"media-src 'self' https://musia.lazying.art https://fun.lazying.art https://lazyingart.github.io; "
                        b"connect-src 'self'; font-src 'self'; object-src 'none'; "
                        b"base-uri 'none'; frame-ancestors 'none'; form-action 'none'"),
                })
                message["headers"] = list(headers.items())
            if message["type"] == "http.response.body" and scope["method"] == "HEAD":
                message["body"] = b""
            await send(message)

        raw = scope.get("raw_path", scope["path"].encode())
        headers = dict(scope.get("headers", []))
        if scope["method"] not in ("GET", "HEAD"):
            response = JSONResponse({"detail": "Read-only API"}, status_code=405, headers={"Allow": "GET, HEAD"})
        elif (len(raw) > 2048 or len(scope.get("query_string", b"")) > 1024 or b"%" in raw
              or b"\\" in raw or any(part in (b".", b"..") for part in raw.split(b"/"))):
            response = JSONResponse({"detail": "Invalid request path"}, status_code=400)
        elif headers.get(b"content-length", b"0") != b"0" or b"transfer-encoding" in headers:
            response = JSONResponse({"detail": "Request bodies are not accepted"}, status_code=400)
        else:
            try:
                await self.app(scope, receive, secured_send)
            except Exception:
                if started:
                    raise
                response = JSONResponse({"detail": "Public data unavailable"}, status_code=503)
                await response(scope, receive, secured_send)
            return
        await response(scope, receive, secured_send)


def create_app(root: Path | None = None, public_base_url: str | None = None) -> FastAPI:
    root = Path(root or ROOT).resolve()
    base_url = _base_url(public_base_url if public_base_url is not None else os.environ.get("MUSIA_PUBLIC_BASE_URL", DEFAULT_PUBLIC_BASE_URL))
    library = PublicLibrary(root)
    app = FastAPI(title="Musia Learning", docs_url=None, redoc_url=None, openapi_url=None, redirect_slashes=False)
    app.add_middleware(PublicBoundary)

    @app.api_route("/healthz", methods=["GET", "HEAD"])
    def health():
        return _json_response({"status": "ok"}, "no-store")

    @app.api_route("/api/v1/library", methods=["GET", "HEAD"])
    def get_library():
        exercise = first_pulse(base_url)
        items = [{**{key: exercise[key] for key in ("id", "title", "artist", "coverUrl")},
                  "duration": EXERCISE_SECONDS, "kind": "exercise"}]
        seen = {"first-pulse"}
        for item in library.entries():
            if item["id"] in seen:
                continue
            song = library.song(item)
            if song:
                default = next(a for a in song["assets"] if a["id"] == song["defaultAssetId"])
                items.append({**{key: song[key] for key in ("id", "title", "artist", "coverUrl")},
                              "duration": default["duration"], "kind": "song"})
                seen.add(item["id"])
        return _json_response({"version": 1, "items": items})

    @app.api_route("/api/v1/songs/{song_id}", methods=["GET", "HEAD"])
    def get_song(song_id: str):
        if song_id == "first-pulse":
            return _json_response(first_pulse(base_url))
        if _id(song_id):
            item = next((item for item in library.entries() if item["id"] == song_id), None)
            song = library.song(item) if item else None
            if song:
                return _json_response(song)
        raise HTTPException(404, "Song not found")

    @app.api_route("/api/v1/lessons", methods=["GET", "HEAD"])
    def lessons():
        return _json_response({"lessons": LESSONS}, "public, max-age=300, must-revalidate")

    @app.api_route("/api/v1/capabilities", methods=["GET", "HEAD"])
    def capabilities():
        disabled = {"available": False, "reason": "Disabled pending authentication, consent, and privacy safeguards."}
        return _json_response({"version": 1, "readOnly": True, "library": True, "lessons": True,
                               "exerciseAudio": True, "cloudGeneration": disabled, "upload": disabled,
                               "aiCoaching": disabled, "accounts": {"available": False, "reason": "No accounts or authentication in this release."}})

    @app.api_route("/api/v1/exercises/first-pulse/audio.wav", methods=["GET", "HEAD"])
    def exercise_audio(request: Request):
        content = first_pulse_wav()
        headers = {"Cache-Control": "public, max-age=3600, must-revalidate", "Accept-Ranges": "bytes"}
        byte_range = request.headers.get("range")
        status = 200
        if byte_range:
            match = re.fullmatch(r"bytes=(\d{0,12})-(\d{0,12})", byte_range)
            start, end = 0, len(content) - 1
            if match and any(match.groups()):
                left, right = match.groups()
                start = int(left) if left else max(0, len(content) - int(right))
                end = min(int(right), end) if left and right else end
            if not match or not any(match.groups()) or not 0 <= start <= end < len(content):
                return Response(status_code=416, headers={**headers, "Content-Range": f"bytes */{len(content)}"})
            headers["Content-Range"] = f"bytes {start}-{end}/{len(content)}"
            content, status = content[start:end + 1], 206
        return Response(content, status_code=status, media_type="audio/wav", headers=headers)

    def serve_static(request: Request):
        relative, media_type = STATIC_FILES[request.scope["path"]]
        try:
            content = _read(root, relative, MAX_STATIC_BYTES)
        except (OSError, ValueError):
            raise HTTPException(404, "Public file not found") from None
        return Response(content, media_type=media_type, headers={"Cache-Control": "public, max-age=300, must-revalidate"})

    for route in STATIC_FILES:
        app.add_api_route(route, serve_static, methods=["GET", "HEAD"], include_in_schema=False)
    return app
