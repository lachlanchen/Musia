#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from musai.creative import CreativeMaterials, MODEL_REGISTRY, PROJECTS_ROOT, create_project, list_projects


PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Musai Studio</title>
  <style>
    body { margin: 0; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #18212f; background: #f5f7fa; }
    header { background: #111827; color: white; padding: 18px 28px; }
    main { max-width: 1180px; margin: 0 auto; padding: 24px; }
    h1 { margin: 0; font-size: 28px; }
    h2 { margin-top: 28px; font-size: 20px; }
    form, .panel { background: white; border: 1px solid #dbe2ea; border-radius: 8px; padding: 16px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }
    label { display: block; font-weight: 650; margin-bottom: 4px; }
    input, textarea, select { width: 100%; box-sizing: border-box; border: 1px solid #cbd5e1; border-radius: 6px; padding: 9px; font: inherit; background: white; }
    textarea { min-height: 90px; resize: vertical; }
    button { border: 0; border-radius: 6px; background: #0f766e; color: white; padding: 10px 14px; font-weight: 700; cursor: pointer; }
    button:disabled { opacity: 0.55; cursor: wait; }
    code { background: #eef2f6; border-radius: 4px; padding: 2px 5px; }
    .muted { color: #667085; }
    .project { padding: 10px 0; border-bottom: 1px solid #edf0f4; }
    .project:last-child { border-bottom: 0; }
    a { color: #075985; }
    pre { white-space: pre-wrap; background: #0f172a; color: #e5e7eb; padding: 12px; border-radius: 8px; overflow: auto; }
  </style>
</head>
<body>
  <header>
    <h1>Musai Studio</h1>
    <div class="muted">Idea, lyrics, chords, notation, or reference recordings to song projects.</div>
  </header>
  <main>
    <form id="project-form">
      <h2>Create Project</h2>
      <div class="grid">
        <div><label>Title</label><input name="title" required placeholder="My new song"></div>
        <div><label>Provider</label><select name="provider"><option>deepseek</option><option>openai</option><option>offline</option></select></div>
        <div><label>Model</label><input name="model" placeholder="deepseek-reasoner or gpt-5.5"></div>
        <div><label>Language</label><input name="language" value="en"></div>
        <div><label>Vocal Language</label><input name="vocal_language" value="en"></div>
        <div><label>Target Language</label><input name="target_language" placeholder="zh-CN for localization"></div>
        <div><label>Genre</label><input name="genre" placeholder="pop ballad, anime rock, folk"></div>
        <div><label>Style</label><input name="style" placeholder="warm piano, acoustic guitar, synth pop"></div>
        <div><label>Mood</label><input name="mood" placeholder="tender, hopeful, cinematic"></div>
        <div><label>Duration Seconds</label><input name="duration" type="number" value="120"></div>
        <div><label>BPM</label><input name="bpm" type="number" placeholder="optional"></div>
        <div><label>Key</label><input name="keyscale" placeholder="C major, B minor"></div>
      </div>
      <p><label>Idea</label><textarea name="idea" placeholder="Describe the story, feeling, scene, or purpose."></textarea></p>
      <p><label>Lyrics</label><textarea name="lyrics" placeholder="Paste rough or finished lyrics."></textarea></p>
      <p><label>Chords</label><textarea name="chords" placeholder="C G Am F, Nashville numbers, chord chart, or harmonic notes."></textarea></p>
      <p><label>Notation / Melody Sketch</label><textarea name="notation" placeholder="Staff notes, numbered notation/jianpu, solfege, MIDI note names, or rhythm notes."></textarea></p>
      <div class="grid">
        <div><label>Reference Audio Path</label><input name="reference_audio" placeholder="/path/to/demo.wav"></div>
        <div><label><input name="analyze_reference" type="checkbox" style="width:auto"> Analyze reference audio now</label></div>
      </div>
      <p><label>Private Notes</label><textarea name="notes" placeholder="Voice, arrangement, quality notes, labmate demo details."></textarea></p>
      <button id="create-button" type="submit">Create Musai Project</button>
      <span id="status" class="muted"></span>
    </form>

    <h2>Projects</h2>
    <div id="projects" class="panel">Loading...</div>

    <h2>Model Roles</h2>
    <div class="panel"><pre id="models"></pre></div>
  </main>
<script>
async function jsonFetch(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}
async function refresh() {
  const projects = await jsonFetch('/api/projects');
  document.getElementById('projects').innerHTML = projects.length ? projects.map(p => {
    const m = p.materials || {};
    return `<div class="project"><strong>${m.title || p.project_id}</strong><br>
      <span class="muted">${p.workflow} · ${p.provider}/${p.model}</span><br>
      <a href="/project/${p.project_id}/BRIEF.md" target="_blank">BRIEF.md</a> ·
      <a href="/project/${p.project_id}/commands.sh" target="_blank">commands.sh</a> ·
      <code>${p.root}</code></div>`;
  }).join('') : 'No projects yet.';
  document.getElementById('models').textContent = JSON.stringify(await jsonFetch('/api/models'), null, 2);
}
document.getElementById('project-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = document.getElementById('create-button');
  const status = document.getElementById('status');
  button.disabled = true;
  status.textContent = ' creating...';
  const data = Object.fromEntries(new FormData(event.target).entries());
  data.analyze_reference = event.target.analyze_reference.checked;
  data.duration = Number(data.duration || 120);
  data.bpm = data.bpm ? Number(data.bpm) : null;
  try {
    const project = await jsonFetch('/api/projects', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    status.innerHTML = ` created <code>${project.project_id}</code>`;
    await refresh();
  } catch (err) {
    status.textContent = ' failed: ' + err.message;
  } finally {
    button.disabled = false;
  }
});
refresh().catch(err => document.getElementById('projects').textContent = err.message);
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    server_version = "MusaiStudio/0.1"

    def send_json(self, data: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, text: str, content_type: str = "text/plain; charset=utf-8", status: HTTPStatus = HTTPStatus.OK) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/":
            self.send_text(PAGE, "text/html; charset=utf-8")
            return
        if path == "/api/models":
            self.send_json(MODEL_REGISTRY)
            return
        if path == "/api/projects":
            self.send_json(list_projects())
            return
        if path.startswith("/project/"):
            self.serve_project_file(path)
            return
        self.send_text("not found", status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/projects":
            self.send_text("not found", status=HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        try:
            materials = CreativeMaterials(
                title=payload.get("title") or "Untitled song",
                idea=payload.get("idea") or "",
                lyrics=payload.get("lyrics") or "",
                chords=payload.get("chords") or "",
                notation=payload.get("notation") or "",
                style=payload.get("style") or "",
                genre=payload.get("genre") or "",
                mood=payload.get("mood") or "",
                language=payload.get("language") or "en",
                vocal_language=payload.get("vocal_language") or payload.get("language") or "en",
                reference_audio=payload.get("reference_audio") or "",
                target_language=payload.get("target_language") or "",
                duration=int(payload.get("duration") or 120),
                bpm=payload.get("bpm"),
                keyscale=payload.get("keyscale") or "",
                notes=payload.get("notes") or "",
            )
            project = create_project(
                materials,
                provider=payload.get("provider") or "deepseek",
                model=payload.get("model") or None,
                analyze_reference=bool(payload.get("analyze_reference")),
            )
            self.send_json(json.loads(Path(project.root, "project.json").read_text(encoding="utf-8")), HTTPStatus.CREATED)
        except Exception as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def serve_project_file(self, path: str) -> None:
        parts = [unquote(part) for part in path.split("/") if part]
        if len(parts) < 3:
            self.send_text("missing project file", status=HTTPStatus.BAD_REQUEST)
            return
        project_id = parts[1]
        rel = Path(*parts[2:])
        base = (PROJECTS_ROOT / project_id).resolve()
        target = (base / rel).resolve()
        if base not in target.parents and target != base:
            self.send_text("invalid path", status=HTTPStatus.BAD_REQUEST)
            return
        if not target.exists() or not target.is_file():
            self.send_text("not found", status=HTTPStatus.NOT_FOUND)
            return
        content_type = "text/markdown; charset=utf-8" if target.suffix == ".md" else "text/plain; charset=utf-8"
        self.send_text(target.read_text(encoding="utf-8"), content_type)

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Musai Studio web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Musai Studio: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
