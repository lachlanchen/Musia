from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import shutil
import subprocess
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI

from .creative import MODEL_REGISTRY, make_client, provider_defaults
from .io import ensure_dir, write_json


ROOT = Path(__file__).resolve().parents[1]
STUDIO_ROOT = ROOT / "data" / "studio"
SESSION_ROOT = STUDIO_ROOT / "sessions"
ARTIFACT_ROOT = STUDIO_ROOT / "artifacts"
JOB_ROOT = STUDIO_ROOT / "jobs"
SETTINGS_PATH = STUDIO_ROOT / "settings.json"
PROJECT_SESSION_DIR = Path(".musia") / "sessions"

TEXT_SUFFIXES = {
    ".txt",
    ".md",
    ".json",
    ".jsonl",
    ".csv",
    ".tsv",
    ".toml",
    ".yaml",
    ".yml",
    ".py",
    ".sh",
    ".log",
    ".html",
    ".css",
    ".js",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".mkv"}
SECRET_MARKERS = {
    ".env",
    ".git",
    ".ssh",
    "id_rsa",
    "id_ed25519",
    "private_key",
    "password",
    "passwd",
    "secret",
    "token",
    "apikey",
    "api_key",
}


DEFAULT_SETTINGS: dict[str, Any] = {
    "profiles": {
        "chat": {
            "provider": "codex",
            "model": "gpt-5.5",
            "reasoning": "medium",
            "sandbox": "danger-full-access",
            "timeout_seconds": 240,
            "cwd": str(ROOT),
        },
        "worker": {
            "provider": "codex",
            "model": "gpt-5.5",
            "reasoning": "xhigh",
            "sandbox": "danger-full-access",
            "timeout_seconds": 1800,
            "cwd": str(ROOT),
        },
        "writer": {
            "provider": "deepseek",
            "model": "deepseek-reasoner",
            "reasoning": "high",
            "timeout_seconds": 240,
            "cwd": str(ROOT),
        },
    },
    "router": {
        "worker_keywords": [
            "analyze",
            "analyse",
            "setup",
            "install",
            "run",
            "generate",
            "create",
            "localize",
            "separate",
            "transcribe",
            "commit",
            "agent",
            "worker",
            "download",
            "test",
            "fix",
            "build",
        ]
    },
    "artifact_pipe": {
        "max_inline_bytes": 2_500_000,
        "allowed_roots": [
            str((ROOT / "data").resolve()),
            str((ROOT / "references").resolve()),
            str((ROOT / "VoidAbyssSong").resolve()),
            str((ROOT / "downloads").resolve()),
        ],
    },
}


def load_env_file(path: Path = ROOT / ".env") -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()


@dataclass
class ChatMessage:
    id: str
    role: str
    content: str
    created_at: str
    profile: str = ""
    status: str = "ok"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Artifact:
    id: str
    session_id: str
    title: str
    kind: str
    path: str
    source: str = "musia"
    tab: str = "explorer"
    selected: bool = False
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def short_id() -> str:
    return uuid.uuid4().hex[:10]


def merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def load_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        save_settings(DEFAULT_SETTINGS)
        return json.loads(json.dumps(DEFAULT_SETTINGS))
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    return merge_dict(DEFAULT_SETTINGS, data)


def save_settings(settings: dict[str, Any]) -> dict[str, Any]:
    merged = merge_dict(DEFAULT_SETTINGS, settings)
    write_json(SETTINGS_PATH, merged)
    return merged


def profile_settings(profile: str) -> dict[str, Any]:
    settings = load_settings()
    profiles = settings.get("profiles", {})
    selected = dict(profiles.get(profile) or profiles.get("chat") or DEFAULT_SETTINGS["profiles"]["chat"])
    if selected.get("provider") == "codex":
        timeout_key = "MUSIA_CODEX_WORKER_TIMEOUT" if profile == "worker" else "MUSIA_CODEX_TIMEOUT"
        timeout_value = os.getenv(timeout_key)
        if timeout_value:
            try:
                selected["timeout_seconds"] = int(timeout_value)
            except ValueError:
                pass
    return selected


def session_dir(session_id: str) -> Path:
    return SESSION_ROOT / session_id


def messages_path(session_id: str) -> Path:
    return session_dir(session_id) / "messages.jsonl"


def resolve_working_dir(working_dir: str | Path | None = None) -> Path:
    if working_dir:
        path = Path(working_dir).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
    else:
        path = ROOT
    return ensure_dir(path.resolve())


def session_pointer_path(working_dir: Path, session_id: str) -> Path:
    return working_dir / PROJECT_SESSION_DIR / session_id / "session.json"


def write_session_pointer(session: dict[str, Any]) -> None:
    working_dir_text = session.get("working_dir") or str(ROOT)
    try:
        working_dir = resolve_working_dir(working_dir_text)
        pointer = session_pointer_path(working_dir, str(session["id"]))
        payload = {
            "id": session["id"],
            "title": session.get("title", ""),
            "working_dir": str(working_dir),
            "session_dir": str(session_dir(str(session["id"])).resolve()),
            "messages": str(messages_path(str(session["id"])).resolve()),
            "created_at": session.get("created_at", ""),
            "updated_at": session.get("updated_at", ""),
        }
        write_json(pointer, payload)
    except Exception:
        return


def update_session_working_dir(session_id: str, working_dir: str | Path | None = None) -> dict[str, Any] | None:
    session = load_session(session_id)
    if not session:
        return None
    if working_dir:
        resolved_working_dir = resolve_working_dir(working_dir)
        session["working_dir"] = str(resolved_working_dir)
        session["project_session_pointer"] = str(session_pointer_path(resolved_working_dir, session_id))
        session["updated_at"] = utc_now()
        write_json(session_dir(session_id) / "session.json", session)
    else:
        resolved_working_dir = resolve_working_dir(session.get("working_dir") or ROOT)
        session["working_dir"] = str(resolved_working_dir)
        session["project_session_pointer"] = str(session_pointer_path(resolved_working_dir, session_id))
        write_json(session_dir(session_id) / "session.json", session)
    write_session_pointer(session)
    return session


def create_session(title: str = "Musia chat", working_dir: str | Path | None = None) -> dict[str, Any]:
    session_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + short_id()
    root = ensure_dir(session_dir(session_id))
    resolved_working_dir = resolve_working_dir(working_dir)
    data = {
        "id": session_id,
        "title": title or "Musia chat",
        "working_dir": str(resolved_working_dir),
        "project_session_pointer": str(session_pointer_path(resolved_working_dir, session_id)),
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    write_json(root / "session.json", data)
    messages_path(session_id).touch()
    write_session_pointer(data)
    return data


def ensure_session(session_id: str | None = None, title: str = "Musia chat", working_dir: str | Path | None = None) -> dict[str, Any]:
    if session_id:
        existing = update_session_working_dir(session_id, working_dir)
        if existing:
            return existing
    sessions = list_sessions(working_dir=working_dir)
    if sessions:
        return sessions[0]
    return create_session(title, working_dir=working_dir)


def load_session(session_id: str) -> dict[str, Any] | None:
    path = session_dir(session_id) / "session.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_sessions(working_dir: str | Path | None = None) -> list[dict[str, Any]]:
    if not SESSION_ROOT.exists():
        return []
    resolved_working_dir = str(resolve_working_dir(working_dir)) if working_dir else ""
    sessions: list[dict[str, Any]] = []
    for path in sorted(SESSION_ROOT.glob("*/session.json"), reverse=True):
        try:
            session = json.loads(path.read_text(encoding="utf-8"))
            session.setdefault("working_dir", str(ROOT))
            if resolved_working_dir and str(Path(session["working_dir"]).expanduser().resolve()) != resolved_working_dir:
                continue
            session["message_count"] = len(load_messages(session["id"]))
            session["artifact_count"] = len(list_artifacts(session["id"])["items"])
            session["project_session_pointer"] = str(session_pointer_path(Path(session["working_dir"]).expanduser().resolve(), session["id"]))
            sessions.append(session)
        except Exception:
            continue
    return sessions


def append_message(session_id: str, role: str, content: str, profile: str = "", status: str = "ok", metadata: dict[str, Any] | None = None) -> ChatMessage:
    ensure_dir(session_dir(session_id))
    message = ChatMessage(
        id=short_id(),
        role=role,
        content=content,
        created_at=utc_now(),
        profile=profile,
        status=status,
        metadata=metadata or {},
    )
    with messages_path(session_id).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(message), ensure_ascii=False) + "\n")
    session = load_session(session_id) or {"id": session_id, "title": "Musia chat", "created_at": utc_now()}
    session["updated_at"] = utc_now()
    if role == "user" and content and session.get("title") == "Musia chat":
        session["title"] = content[:60]
    write_json(session_dir(session_id) / "session.json", session)
    write_session_pointer(session)
    return message


def load_messages(session_id: str) -> list[dict[str, Any]]:
    path = messages_path(session_id)
    if not path.exists():
        return []
    messages: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            messages.append(json.loads(line))
        except Exception:
            continue
    return messages


def classify_artifact(path: Path, explicit_kind: str | None = None) -> tuple[str, str]:
    if explicit_kind:
        kind = explicit_kind
    else:
        suffix = path.suffix.lower()
        if suffix in IMAGE_SUFFIXES:
            kind = "image"
        elif suffix in AUDIO_SUFFIXES:
            kind = "audio"
        elif suffix in VIDEO_SUFFIXES:
            kind = "video"
        elif suffix == ".pdf":
            kind = "pdf"
        elif suffix in TEXT_SUFFIXES:
            kind = "markdown" if suffix == ".md" else "text"
        else:
            kind = "file"
    if kind in {"image", "video"}:
        tab = "canvas"
    elif kind == "pdf":
        tab = "pdf"
    elif kind in {"markdown", "text", "json", "diff"}:
        tab = "editor"
    elif kind == "audio":
        tab = "canvas"
    else:
        tab = "explorer"
    return kind, tab


def blocked_path(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    text = str(path).lower()
    return any(marker in parts or marker in text for marker in SECRET_MARKERS)


def allowed_artifact_path(path: Path) -> bool:
    if blocked_path(path):
        return False
    settings = load_settings()
    roots = [Path(item).expanduser().resolve() for item in settings["artifact_pipe"]["allowed_roots"]]
    if SESSION_ROOT.exists():
        for session_json in SESSION_ROOT.glob("*/session.json"):
            try:
                session = json.loads(session_json.read_text(encoding="utf-8"))
                working_dir = Path(session.get("working_dir") or "").expanduser().resolve()
                if working_dir.exists():
                    roots.append(working_dir)
            except Exception:
                continue
    resolved = path.expanduser().resolve()
    return any(resolved == root or root in resolved.parents for root in roots)


def resolve_artifact_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    if not allowed_artifact_path(resolved):
        raise ValueError(f"artifact path is outside allowed roots or blocked: {path_text}")
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(path_text)
    return resolved


def artifact_registry_path(session_id: str) -> Path:
    return ARTIFACT_ROOT / session_id / "artifacts.json"


def load_artifact_registry(session_id: str) -> dict[str, Any]:
    path = artifact_registry_path(session_id)
    if not path.exists():
        return {"items": [], "selected_artifact_id": ""}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("items", [])
        data.setdefault("selected_artifact_id", "")
        return data
    except Exception:
        return {"items": [], "selected_artifact_id": ""}


def save_artifact_registry(session_id: str, data: dict[str, Any]) -> None:
    write_json(artifact_registry_path(session_id), data)


def register_artifact(
    session_id: str,
    title: str,
    path: str | None = None,
    text: str | None = None,
    kind: str | None = None,
    source: str = "musia",
    tab: str | None = None,
    selected: bool = False,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_dir(ARTIFACT_ROOT / session_id / "files")
    if text is not None and not path:
        suffix = ".md" if (kind or "markdown") == "markdown" else ".txt"
        filename = re.sub(r"[^A-Za-z0-9._-]+", "-", title.strip()).strip("-").lower() or "artifact"
        target = ARTIFACT_ROOT / session_id / "files" / f"{filename}-{short_id()}{suffix}"
        target.write_text(text, encoding="utf-8")
        artifact_path = target.resolve()
    elif path:
        artifact_path = resolve_artifact_path(path)
    else:
        raise ValueError("artifact requires path or text")

    detected_kind, detected_tab = classify_artifact(artifact_path, kind)
    artifact = Artifact(
        id=short_id(),
        session_id=session_id,
        title=title or artifact_path.name,
        kind=detected_kind,
        path=str(artifact_path),
        source=source,
        tab=tab or detected_tab,
        selected=selected,
        created_at=utc_now(),
        metadata=metadata or {},
    )
    registry = load_artifact_registry(session_id)
    if selected:
        for item in registry["items"]:
            item["selected"] = False
        registry["selected_artifact_id"] = artifact.id
    elif not registry.get("selected_artifact_id"):
        artifact.selected = True
        registry["selected_artifact_id"] = artifact.id
    registry["items"].append(asdict(artifact))
    save_artifact_registry(session_id, registry)
    return asdict(artifact)


def list_artifacts(session_id: str) -> dict[str, Any]:
    registry = load_artifact_registry(session_id)
    safe_items: list[dict[str, Any]] = []
    for item in registry.get("items", []):
        copied = dict(item)
        copied["exists"] = Path(copied.get("path", "")).exists()
        copied["filename"] = Path(copied.get("path", "")).name
        copied.pop("path", None)
        safe_items.append(copied)
    return {"items": safe_items, "selected_artifact_id": registry.get("selected_artifact_id") or ""}


def select_artifact(session_id: str, artifact_id: str) -> dict[str, Any]:
    registry = load_artifact_registry(session_id)
    found = False
    for item in registry["items"]:
        item["selected"] = item["id"] == artifact_id
        found = found or item["selected"]
    if not found:
        raise KeyError(artifact_id)
    registry["selected_artifact_id"] = artifact_id
    save_artifact_registry(session_id, registry)
    return list_artifacts(session_id)


def get_artifact(session_id: str, artifact_id: str) -> dict[str, Any]:
    registry = load_artifact_registry(session_id)
    for item in registry.get("items", []):
        if item.get("id") == artifact_id:
            path = resolve_artifact_path(item["path"])
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            return {"item": item, "path": path, "mime": mime}
    raise KeyError(artifact_id)


def artifact_payload(session_id: str, artifact_id: str) -> dict[str, Any]:
    data = get_artifact(session_id, artifact_id)
    item = dict(data["item"])
    path: Path = data["path"]
    mime = data["mime"]
    item.pop("path", None)
    payload: dict[str, Any] = {"artifact": item, "filename": path.name, "mime": mime}
    if path.suffix.lower() in TEXT_SUFFIXES:
        payload["text"] = path.read_text(encoding="utf-8", errors="replace")
        return payload
    max_inline = int(load_settings()["artifact_pipe"].get("max_inline_bytes") or 0)
    if path.stat().st_size <= max_inline:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        payload["data_url"] = f"data:{mime};base64,{encoded}"
    else:
        payload["too_large_for_inline"] = True
    return payload


def router_mode(message: str, requested: str = "auto") -> str:
    requested = requested or "auto"
    if requested in {"chat", "worker"}:
        return requested
    lowered = message.lower()
    keywords = load_settings().get("router", {}).get("worker_keywords", [])
    return "worker" if any(word in lowered for word in keywords) else "chat"


def format_history(messages: list[dict[str, Any]], limit: int = 12) -> str:
    recent = messages[-limit:]
    return "\n\n".join(f"{m.get('role', 'unknown').upper()}:\n{m.get('content', '')}" for m in recent)


def session_working_dir(session_id: str) -> Path:
    session = load_session(session_id) or {}
    return resolve_working_dir(session.get("working_dir") or ROOT)


def build_chat_prompt(session_id: str, message: str) -> str:
    history = format_history(load_messages(session_id))
    working_dir = session_working_dir(session_id)
    return f"""You are Musia Studio Chat, a concise producer-engineer assistant for AI song creation and localization.

Repository: {ROOT}
Working directory for this session: {working_dir}
Default chat wrapper: Codex GPT-5.5 medium.
Default worker wrapper: Codex GPT-5.5 xhigh.

Answer the user directly. For heavy work, recommend or trigger the worker path instead of pretending it ran.
Use the working directory as the user's music project folder. Read supplied material from that folder when paths are relative.
Prefer concrete Musia commands, project paths, and quality gates. Do not claim audio was generated unless a file exists.
Use Musia control language: free_vocal, melody_generation, full_production, controlled_song, localization; and control levels free, lyrics, lyrics_chords, melody_sheet, reference_audio, strict_localization.

Recent session history:
{history}

Current user message:
{message}
"""


def build_worker_prompt(session_id: str, message: str) -> str:
    history = format_history(load_messages(session_id), limit=20)
    working_dir = session_working_dir(session_id)
    return f"""You are Musia Studio Worker, running through the high-reasoning Codex wrapper.

Goal:
Handle the user's requested Musia setup, analysis, project creation, artifact generation, or code/workflow task in this repository.

Repository:
{ROOT}

Session working directory:
{working_dir}

Rules:
- Inspect before changing.
- Prefer existing Musia scripts and repo patterns.
- Treat the session working directory as the user's music project folder; relative material paths are relative to that folder.
- Keep raw/private media out of Git unless explicitly requested.
- For song localization, produce explicit paths for stems, lyrics, beats, chords, vocals, mixes, and QA notes.
- Route clean vocal-only / human_sound work to SoulX first; route complete instrumental/vocal production to ACE-Step or full-song backends.
- For melody / 旋律 requests, translate the user need into melody contour, phrase rhythm, hook shape, note durations, MIDI/sheet/metadata needs, and vocal phrasing.
- For controlled generation, preserve user lyrics, chords, sheets, melody sketches, friend recordings, or reference audio before inventing new material.
- For licensed localization, require rights confirmation for release/publication, preserve source structure, and adapt lyrics singably in the target language.
- If a model or API key is missing, write a clear setup artifact instead of claiming completion.
- Registerable artifacts should be normal files under this repo, especially data/, references/, or VoidAbyssSong/.
- Finish with a concise summary and list any artifact paths created or updated.

Recent session history:
{history}

User task:
{message}
"""


def run_codex_profile(prompt: str, profile: dict[str, Any], output_dir: Path, cwd_override: Path | None = None) -> dict[str, Any]:
    ensure_dir(output_dir)
    codex = shutil.which("codex")
    if not codex:
        return {"status": "fallback", "answer": "Codex CLI was not found on PATH.", "stdout": "", "stderr": ""}
    prompt_path = output_dir / "prompt.md"
    stdout_path = output_dir / "stdout.txt"
    stderr_path = output_dir / "stderr.txt"
    answer_path = output_dir / "answer.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    model = profile.get("model") or "gpt-5.5"
    reasoning = profile.get("reasoning") or "medium"
    sandbox = profile.get("sandbox") or "danger-full-access"
    cwd = cwd_override or Path(profile.get("cwd") or ROOT).expanduser()
    cwd = resolve_working_dir(cwd)
    cmd = [
        codex,
        "exec",
        "-m",
        model,
        "-c",
        f'model_reasoning_effort="{reasoning}"',
        "-s",
        sandbox,
        "--cd",
        str(cwd),
        "-o",
        str(answer_path),
        "-",
    ]
    timeout = int(profile.get("timeout_seconds") or 240)
    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            cwd=str(cwd),
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        stdout_path.write_text(result.stdout or "", encoding="utf-8")
        stderr_path.write_text(result.stderr or "", encoding="utf-8")
        answer = answer_path.read_text(encoding="utf-8", errors="replace") if answer_path.exists() else (result.stdout or result.stderr or "")
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "answer": answer.strip(),
            "returncode": result.returncode,
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "prompt": str(prompt_path),
            "model": model,
            "reasoning": reasoning,
        }
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(exc.stdout or "", encoding="utf-8")
        stderr_path.write_text(exc.stderr or "", encoding="utf-8")
        return {
            "status": "timeout",
            "answer": f"Codex wrapper timed out after {timeout} seconds.",
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "prompt": str(prompt_path),
            "model": model,
            "reasoning": reasoning,
        }


def run_api_profile(prompt: str, profile: dict[str, Any]) -> dict[str, Any]:
    provider = profile.get("provider") or "deepseek"
    model = profile.get("model")
    provider_name, model_name, api_key = provider_defaults(provider, model)
    client: OpenAI | None = make_client(provider_name, api_key)
    if client is None:
        return {"status": "fallback", "answer": f"Missing API key for {provider_name}.", "model": model_name}
    messages = [
        {"role": "system", "content": "You are Musia Studio Chat. Be concise, concrete, and production-minded."},
        {"role": "user", "content": prompt},
    ]
    try:
        response = client.chat.completions.create(model=model_name, messages=messages)
        return {"status": "ok", "answer": (response.choices[0].message.content or "").strip(), "model": model_name}
    except Exception as exc:
        return {"status": "error", "answer": str(exc), "model": model_name}


def run_profile(prompt: str, profile_name: str, output_dir: Path, cwd_override: Path | None = None) -> dict[str, Any]:
    profile = profile_settings(profile_name)
    provider = profile.get("provider") or "codex"
    if provider == "codex":
        return run_codex_profile(prompt, profile, output_dir, cwd_override=cwd_override)
    if provider in {"openai", "deepseek"}:
        return run_api_profile(prompt, profile)
    return {"status": "fallback", "answer": f"Unsupported provider: {provider}"}


def discover_artifact_paths(text: str) -> list[Path]:
    candidates: list[str] = []
    patterns = [
        r"(/home/lachlan/ProjectsLFS/Musia/[^\s`'\"<>]+)",
        r"\b((?:data|references|VoidAbyssSong|downloads)/[^\s`'\"<>]+)",
    ]
    for pattern in patterns:
        candidates.extend(re.findall(pattern, text))
    paths: list[Path] = []
    for candidate in candidates:
        cleaned = candidate.rstrip(".,);]")
        try:
            path = resolve_artifact_path(cleaned)
        except Exception:
            continue
        if path not in paths:
            paths.append(path)
    return paths[:20]


def register_wrapper_artifacts(session_id: str, result: dict[str, Any], source: str) -> list[dict[str, Any]]:
    registered: list[dict[str, Any]] = []
    answer = result.get("answer") or ""
    if answer:
        registered.append(
            register_artifact(
                session_id,
                title=f"{source} response",
                text=answer,
                kind="markdown",
                source=source,
                selected=True,
            )
        )
    for key in ["stdout", "stderr", "prompt"]:
        path = result.get(key)
        if path and Path(path).exists():
            registered.append(
                register_artifact(
                    session_id,
                    title=f"{source} {key}",
                    path=path,
                    kind="text" if key != "prompt" else "markdown",
                    source=source,
                )
            )
    for path in discover_artifact_paths(answer):
        try:
            registered.append(register_artifact(session_id, title=path.name, path=str(path), source=source))
        except Exception:
            continue
    return registered


def send_chat_message(session_id: str | None, message: str, mode: str = "auto", working_dir: str | Path | None = None) -> dict[str, Any]:
    session = ensure_session(session_id, working_dir=working_dir)
    sid = session["id"]
    append_message(sid, "user", message)
    resolved_mode = router_mode(message, mode)
    if resolved_mode == "worker":
        job = create_worker_job(sid, message)
        append_message(
            sid,
            "assistant",
            f"Worker job queued: `{job['id']}`. The artifact pipe will update when it completes.",
            profile="worker",
            metadata={"job_id": job["id"]},
        )
        return {"mode": "worker", "session_id": sid, "job": job, "messages": load_messages(sid)}
    prompt = build_chat_prompt(sid, message)
    output_dir = session_dir(sid) / "wrapper" / short_id()
    result = run_profile(prompt, "chat", output_dir, cwd_override=session_working_dir(sid))
    artifacts = register_wrapper_artifacts(sid, result, "chat")
    append_message(sid, "assistant", result.get("answer") or "", profile="chat", status=result.get("status") or "ok", metadata={"artifacts": artifacts})
    return {"mode": "chat", "session_id": sid, "result": result, "artifacts": artifacts, "messages": load_messages(sid)}


def job_path(job_id: str) -> Path:
    return JOB_ROOT / job_id / "job.json"


def save_job(job: dict[str, Any]) -> None:
    write_json(job_path(job["id"]), job)


def load_job(job_id: str) -> dict[str, Any] | None:
    path = job_path(job_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_jobs(session_id: str | None = None) -> list[dict[str, Any]]:
    if not JOB_ROOT.exists():
        return []
    jobs: list[dict[str, Any]] = []
    for path in sorted(JOB_ROOT.glob("*/job.json"), reverse=True):
        try:
            job = json.loads(path.read_text(encoding="utf-8"))
            if session_id and job.get("session_id") != session_id:
                continue
            jobs.append(job)
        except Exception:
            continue
    return jobs


def create_worker_job(session_id: str, message: str) -> dict[str, Any]:
    job_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + short_id()
    job = {
        "id": job_id,
        "session_id": session_id,
        "status": "queued",
        "profile": "worker",
        "message": message,
        "working_dir": str(session_working_dir(session_id)),
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "root": str((JOB_ROOT / job_id).resolve()),
    }
    ensure_dir(JOB_ROOT / job_id)
    save_job(job)
    thread = threading.Thread(target=run_worker_job, args=(job_id,), daemon=True)
    thread.start()
    return job


def run_worker_job(job_id: str) -> None:
    job = load_job(job_id)
    if not job:
        return
    job["status"] = "running"
    job["started_at"] = utc_now()
    job["updated_at"] = utc_now()
    save_job(job)
    session_id = job["session_id"]
    prompt = build_worker_prompt(session_id, job["message"])
    output_dir = JOB_ROOT / job_id
    result = run_profile(prompt, "worker", output_dir, cwd_override=session_working_dir(session_id))
    artifacts = register_wrapper_artifacts(session_id, result, "worker")
    job["status"] = "completed" if result.get("status") == "ok" else result.get("status", "error")
    job["result"] = result
    job["artifacts"] = artifacts
    job["finished_at"] = utc_now()
    job["updated_at"] = utc_now()
    save_job(job)
    append_message(
        session_id,
        "assistant",
        (result.get("answer") or f"Worker job {job_id} finished with status {job['status']}").strip(),
        profile="worker",
        status=job["status"],
        metadata={"job_id": job_id, "artifacts": artifacts},
    )


def setup_status() -> dict[str, Any]:
    settings = load_settings()
    songgeneration_root = ROOT / "third_party" / "SongGeneration-v2"
    songgeneration_assets = (
        (
            songgeneration_root
            / "checkpoints"
            / "SongGeneration-v2-large"
            / "model.pt",
            12_000_000_000,
        ),
        (songgeneration_root / "tools" / "new_auto_prompt.pt", 10_000_000),
        (
            songgeneration_root
            / "ckpt"
            / "model_septoken"
            / "model_2.safetensors",
            4_000_000_000,
        ),
        (
            songgeneration_root
            / "ckpt"
            / "model_1rvq"
            / "model_2_fixed.safetensors",
            4_000_000_000,
        ),
    )
    apex_root = ROOT / "third_party" / "APEX"

    def completed_artifact(path: Path, minimum_size: int) -> bool:
        return (
            path.is_file()
            and path.stat().st_size >= minimum_size
            and not Path(f"{path}.aria2").exists()
        )

    return {
        "root": str(ROOT),
        "studio_root": str(STUDIO_ROOT),
        "codex_cli": shutil.which("codex") or "",
        "conda": shutil.which("conda") or "",
        "ffmpeg": shutil.which("ffmpeg") or "",
        "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
        "deepseek_api_key": bool(os.getenv("DEEPSEEK_API_KEY")),
        "hf_token": bool(os.getenv("HF_TOKEN")),
        "profiles": settings.get("profiles", {}),
        "model_registry": MODEL_REGISTRY,
        "third_party": {
            "ace_step": (ROOT / "third_party" / "ACE-Step-1.5").exists(),
            "soulx_singer": (ROOT / "third_party" / "SoulX-Singer").exists(),
            "yingmusic": (ROOT / "third_party" / "YingMusic-Singer-Plus").exists(),
            "heartmula": (ROOT / "third_party" / "HeartMuLa").exists(),
            "songgeneration_v2": all(
                completed_artifact(path, minimum_size)
                for path, minimum_size in songgeneration_assets
            ),
            "moss_music": (ROOT / "third_party" / "MOSS-Music").exists(),
            "apex_music_quality": (
                completed_artifact(apex_root / "pytorch_model.bin", 3_000_000)
                and completed_artifact(
                    apex_root / "mert-v1-95m" / "pytorch_model.bin",
                    300_000_000,
                )
            ),
        },
    }
