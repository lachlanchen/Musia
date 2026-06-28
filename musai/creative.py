from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI

from .io import ensure_dir, write_json


ROOT = Path(__file__).resolve().parents[1]
PROJECTS_ROOT = ROOT / "data" / "creative_projects"


MODEL_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "ace-step-1.5",
        "local_path": "third_party/ACE-Step-1.5",
        "status": "installed",
        "best_for": [
            "idea_to_complete_song",
            "lyrics_to_complete_song",
            "genre_prompt_to_song",
            "reference_audio_cover_or_repaint_experiments",
        ],
        "quality_role": "Best local full-song generator for polished demos. Not strict same-stems localization.",
        "outputs": ["full mixed song wav/mp3", "model generation folder"],
    },
    {
        "id": "soulx-singer",
        "local_path": "third_party/SoulX-Singer",
        "status": "installed",
        "best_for": [
            "melody_conditioned_singing",
            "cross_language_singing",
            "reference_voice_singing",
            "strict_localization_experiments",
        ],
        "quality_role": "Best local strict vocal/melody backend, but needs corrected metadata for high intelligibility.",
        "outputs": ["generated vocal wav", "mix with Demucs stems"],
    },
    {
        "id": "demucs-whisper-chords",
        "local_path": "musai/",
        "status": "installed",
        "best_for": ["reference_audio_analysis", "stems", "lyrics", "beats", "chords"],
        "quality_role": "Turns a recording into materials for composition, localization, and QA.",
        "outputs": ["bass", "drums", "vocals", "other", "instrumental", "lyrics", "beats", "chords"],
    },
    {
        "id": "yingmusic-singer-plus",
        "local_path": "third_party/YingMusic-Singer-Plus",
        "status": "code_staged",
        "best_for": ["lyric_editing", "cn_en_translation", "melody_guided_singing_research"],
        "quality_role": "Closest research fit for lyric replacement, but not yet wrapped as a reliable CLI backend.",
        "outputs": ["edited singing vocal when manually configured"],
    },
    {
        "id": "yue-songgen-diffrhythm-heartmula",
        "local_path": "third_party/",
        "status": "installed_or_staged",
        "best_for": ["alternate_full_song_generation", "research_comparison"],
        "quality_role": "Use as comparison models after ACE-Step. Label outputs as new/inspired songs unless structure is preserved.",
        "outputs": ["full-song candidates"],
    },
    {
        "id": "deepseek-openai-lyricfit",
        "local_path": "api",
        "status": "api_key_optional",
        "best_for": ["idea_expansion", "lyrics_refinement", "song_brief", "quality_review", "localization_adaptation"],
        "quality_role": "Creative planning and QA layer. Does not produce audio by itself.",
        "outputs": ["brief.json", "lyrics_draft.txt", "quality checklist"],
    },
]


@dataclass
class CreativeMaterials:
    title: str
    idea: str = ""
    lyrics: str = ""
    chords: str = ""
    notation: str = ""
    style: str = ""
    genre: str = ""
    mood: str = ""
    language: str = "en"
    vocal_language: str = "en"
    reference_audio: str = ""
    reference_lyrics: str = ""
    target_language: str = ""
    duration: int = 120
    bpm: int | None = None
    keyscale: str = ""
    time_signature: str = "4"
    notes: str = ""


@dataclass
class CreativeProject:
    project_id: str
    root: str
    created_at: str
    materials: CreativeMaterials
    workflow: str
    provider: str
    model: str
    artifacts: dict[str, str] = field(default_factory=dict)
    commands: dict[str, str] = field(default_factory=dict)


def slugify(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower())
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "untitled"


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def read_text_source(value: str | None) -> str:
    if not value:
        return ""
    path = Path(value).expanduser()
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return value.strip()


def copy_material(path_text: str, materials_dir: Path) -> str:
    if not path_text:
        return ""
    path = Path(path_text).expanduser()
    if not path.exists() or not path.is_file():
        return path_text
    ensure_dir(materials_dir)
    destination = materials_dir / path.name
    if path.resolve() != destination.resolve():
        shutil.copy2(path, destination)
    return str(destination)


def classify_workflow(materials: CreativeMaterials) -> str:
    has_reference = bool(materials.reference_audio)
    has_lyrics = bool(materials.lyrics.strip())
    has_chords = bool(materials.chords.strip())
    has_notation = bool(materials.notation.strip())
    has_target = bool(materials.target_language.strip())
    if has_reference and has_target:
        return "localize_reference_song"
    if has_reference and (has_chords or has_notation or has_lyrics):
        return "compose_from_reference_plus_materials"
    if has_reference:
        return "analyze_reference_then_compose"
    if has_lyrics and (has_chords or has_notation):
        return "lyrics_plus_music_skeleton"
    if has_lyrics:
        return "lyrics_to_complete_song"
    if has_chords or has_notation:
        return "music_skeleton_to_song"
    return "idea_to_complete_song"


def provider_defaults(provider: str, model: str | None) -> tuple[str, str, str | None]:
    if provider == "deepseek":
        return "deepseek", model or os.getenv("DEEPSEEK_MODEL", "deepseek-reasoner"), os.getenv("DEEPSEEK_API_KEY")
    if provider == "openai":
        return "openai", model or os.getenv("OPENAI_MODEL", "gpt-5.5"), os.getenv("OPENAI_API_KEY")
    return "offline", model or "offline", None


def make_client(provider: str, api_key: str | None) -> OpenAI | None:
    if provider == "deepseek" and api_key:
        return OpenAI(api_key=api_key, base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    if provider == "openai" and api_key:
        return OpenAI(api_key=api_key)
    return None


def strip_json_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def parse_json_output(text: str) -> Any:
    cleaned = strip_json_fence(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def call_brief_model(provider: str, model: str, materials: CreativeMaterials, workflow: str, analysis_manifest: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    _, _, api_key = provider_defaults(provider, model)
    client = make_client(provider, api_key)
    fallback = offline_brief(materials, workflow, analysis_manifest)
    if client is None:
        return fallback, {"status": "fallback", "reason": f"missing {provider} api key or offline provider"}

    payload = {
        "task": "Create a high-quality Musai song production brief. Return strict JSON.",
        "workflow": workflow,
        "materials": asdict(materials),
        "reference_analysis_manifest": analysis_manifest or {},
        "model_stack": MODEL_REGISTRY,
        "return_schema": {
            "concept": "one paragraph",
            "production_strategy": "how to use the provided materials",
            "song_structure": ["intro", "verse", "chorus"],
            "lyrics": "complete or revised lyrics with section labels",
            "caption_for_music_model": "rich production prompt for ACE-Step or similar",
            "vocal_direction": "singer, language, delivery, emotion",
            "harmony_rhythm_notes": "chords, beat, groove, notation guidance",
            "recommended_backend": "ace-step-1.5 or soulx-singer or analysis-only",
            "quality_checklist": ["item"],
            "risks": ["item"],
        },
    }
    messages = [
        {
            "role": "system",
            "content": (
                "You are Musai Producer: a senior songwriter, arranger, lyricist, and AI music QA engineer. "
                "Return strict JSON only. Prefer concrete, singable lyrics and actionable model settings."
            ),
        },
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    try:
        try:
            response = client.chat.completions.create(model=model, messages=messages, temperature=0.55)
        except Exception as exc:
            if "temperature" not in str(exc).lower():
                raise
            response = client.chat.completions.create(model=model, messages=messages)
        text = response.choices[0].message.content or ""
        parsed = parse_json_output(text)
        if not isinstance(parsed, dict):
            raise ValueError("model returned non-object JSON")
        return parsed, {"status": "ok", "provider": provider, "model": model}
    except Exception as exc:
        return fallback, {"status": "fallback", "provider": provider, "model": model, "error": str(exc)}


def offline_brief(materials: CreativeMaterials, workflow: str, analysis_manifest: dict[str, Any] | None) -> dict[str, Any]:
    title = materials.title or "Untitled song"
    language = materials.vocal_language or materials.language or "en"
    style = ", ".join(part for part in [materials.genre, materials.style, materials.mood] if part) or "clear modern pop production"
    source = materials.idea or materials.lyrics or materials.chords or materials.notation or "an original song idea"
    lyrics = materials.lyrics.strip()
    if not lyrics:
        lyrics = (
            "[Verse 1]\n"
            f"I started with {title}\n"
            "A quiet thought becoming sound\n\n"
            "[Chorus]\n"
            "Carry the light through the night\n"
            "Let the melody find its ground"
        )
    caption_parts = [
        f"High quality {language} vocal song titled {title}.",
        f"Style: {style}.",
        "Professional arrangement, clear lead vocal, polished mix, memorable chorus.",
    ]
    if materials.chords:
        caption_parts.append(f"Respect this chord/harmony idea: {materials.chords[:700]}")
    if materials.notation:
        caption_parts.append(f"Respect this notation or melody sketch: {materials.notation[:700]}")
    if analysis_manifest:
        caption_parts.append(
            f"Reference analysis: tempo {analysis_manifest.get('tempo_bpm')} BPM, "
            f"{analysis_manifest.get('beat_count')} beats, {analysis_manifest.get('chord_segment_count')} chord segments."
        )
    return {
        "concept": f"{title}: {source[:500]}",
        "production_strategy": strategy_for_workflow(workflow),
        "song_structure": ["Intro", "Verse 1", "Pre-Chorus", "Chorus", "Verse 2", "Bridge", "Final Chorus", "Outro"],
        "lyrics": lyrics,
        "caption_for_music_model": " ".join(caption_parts),
        "vocal_direction": f"Lead vocal in {language}; natural phrasing, emotionally direct, no spoken TTS.",
        "harmony_rhythm_notes": materials.chords or materials.notation or "Let the model create harmony; keep rhythm singable and chorus-forward.",
        "recommended_backend": "soulx-singer" if workflow == "localize_reference_song" else "ace-step-1.5",
        "quality_checklist": [
            "Lead vocal is sung and intelligible.",
            "Lyrics scan naturally in the target language.",
            "The chorus has a memorable melodic hook.",
            "Reference chords/rhythm are reflected when provided.",
            "Final loudness and vocal balance are checked before accepting.",
        ],
        "risks": [
            "Full-song generators may change arrangement or melody.",
            "Strict localization needs corrected phrase/note metadata.",
        ],
    }


def strategy_for_workflow(workflow: str) -> str:
    strategies = {
        "idea_to_complete_song": "Expand idea into lyrics, arrangement, prompt, then generate with ACE-Step.",
        "lyrics_to_complete_song": "Refine lyrics for singability, generate a rich music caption, then use ACE-Step.",
        "lyrics_plus_music_skeleton": "Preserve lyric intent plus chords/notation; use ACE-Step for a full demo and optionally export MIDI for professional vocal tools.",
        "music_skeleton_to_song": "Use chords/notation as the musical anchor, ask the AI layer for lyrics and production prompt, then generate.",
        "analyze_reference_then_compose": "Analyze reference audio for stems, beats, chords, and feel; use those artifacts to guide a new song.",
        "compose_from_reference_plus_materials": "Analyze reference audio and combine extracted rhythm/chords with supplied lyrics or notation.",
        "localize_reference_song": "Use Demucs/analysis plus SoulX/YingMusic-style singing synthesis; keep output marked experimental until ASR and listening checks pass.",
    }
    return strategies.get(workflow, "Create a song brief and route to the best available backend.")


def ace_language_code(materials: CreativeMaterials) -> str:
    language = (materials.vocal_language or materials.language or "en").lower()
    if language in {"zh-cn", "zh", "chinese", "mandarin", "cn"}:
        return "zh"
    if language in {"ja", "japanese"}:
        return "ja"
    if language in {"ko", "korean"}:
        return "ko"
    return "en"


def toml_string(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return '""'
    return json.dumps(str(value), ensure_ascii=False)


def extract_bpm(text: str) -> int:
    match = re.search(r"\b([4-9][0-9]|1[0-9]{2}|2[0-2][0-9])\s*(?:bpm|BPM)\b", text)
    return int(match.group(1)) if match else 0


def extract_keyscale(text: str) -> str:
    match = re.search(r"\bkey\s+of\s+([A-G](?:#|b)?\s+(?:major|minor))\b", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def write_ace_config(project_dir: Path, materials: CreativeMaterials, brief: dict[str, Any]) -> Path:
    config_path = project_dir / "ace_step_config.toml"
    output_dir = project_dir / "ace_step_output"
    lyrics = brief.get("lyrics") or materials.lyrics or ""
    caption = brief.get("caption_for_music_model") or brief.get("concept") or materials.idea or materials.title
    bpm = int(materials.bpm) if materials.bpm else extract_bpm(caption)
    keyscale = materials.keyscale or extract_keyscale(caption)
    config = {
        "project_root": str((ROOT / "third_party" / "ACE-Step-1.5").resolve()),
        "checkpoint_dir": str((ROOT / "third_party" / "ACE-Step-1.5" / "checkpoints").resolve()),
        "save_dir": str(output_dir.resolve()),
        "task_type": "text2music",
        "caption": caption,
        "lyrics": lyrics,
        "duration": int(materials.duration or 120),
        "bpm": bpm,
        "keyscale": keyscale,
        "timesignature": materials.time_signature or "4",
        "vocal_language": ace_language_code(materials),
        "thinking": False,
        "use_cot_lyrics": False,
        "use_cot_caption": False,
        "inference_steps": 60,
        "guidance_scale": 15.0,
        "seed": -1,
        "batch_size": 1,
        "audio_format": "wav",
    }
    lines = ["# Generated by Musai Creative Studio"]
    for key, value in config.items():
        lines.append(f"{key} = {toml_string(value)}")
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config_path


def render_brief_markdown(project: CreativeProject, brief: dict[str, Any], model_meta: dict[str, Any], analysis_manifest: dict[str, Any] | None) -> str:
    materials = project.materials
    lines = [
        f"# Musai Creative Project: {materials.title}",
        "",
        f"- Project id: `{project.project_id}`",
        f"- Workflow: `{project.workflow}`",
        f"- AI provider: `{project.provider}`",
        f"- AI model: `{project.model}`",
        f"- Model status: `{json.dumps(model_meta, ensure_ascii=False)}`",
        "",
        "## Inputs",
        "",
        f"- Idea: {materials.idea or '(none)'}",
        f"- Language: `{materials.language}`",
        f"- Vocal language: `{materials.vocal_language}`",
        f"- Genre/style/mood: `{materials.genre}` / `{materials.style}` / `{materials.mood}`",
        f"- Reference audio: `{materials.reference_audio or '(none)'}`",
        f"- Target language: `{materials.target_language or '(none)'}`",
        "",
        "## Recommended Workflow",
        "",
        brief.get("production_strategy", ""),
        "",
        "## Concept",
        "",
        brief.get("concept", ""),
        "",
        "## Music Model Caption",
        "",
        brief.get("caption_for_music_model", ""),
        "",
        "## Lyrics Draft",
        "",
        "```text",
        brief.get("lyrics", "").strip(),
        "```",
        "",
        "## Harmony / Rhythm / Notation",
        "",
        brief.get("harmony_rhythm_notes", ""),
        "",
        "## Backend Routing",
        "",
        f"- Recommended backend: `{brief.get('recommended_backend', '')}`",
        f"- ACE-Step config: `{project.artifacts.get('ace_step_config', '')}`",
        f"- Command script: `{project.artifacts.get('commands', '')}`",
        "",
        "## Quality Checklist",
        "",
    ]
    for item in brief.get("quality_checklist", []):
        lines.append(f"- [ ] {item}")
    if analysis_manifest:
        lines += [
            "",
            "## Reference Analysis",
            "",
            f"- Run: `{analysis_manifest.get('run_name')}`",
            f"- Tempo: `{analysis_manifest.get('tempo_bpm')}`",
            f"- Beats: `{analysis_manifest.get('beat_count')}`",
            f"- Chord segments: `{analysis_manifest.get('chord_segment_count')}`",
        ]
    lines.append("")
    return "\n".join(lines)


def render_commands(project_dir: Path, ace_config: Path, workflow: str, language: str) -> str:
    ace_cmd = (
        "cd third_party/ACE-Step-1.5 && "
        f".venv/bin/python cli.py -c {ace_config.resolve()} --backend vllm"
    )
    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "",
            f"# Project: {project_dir}",
            f"# Workflow: {workflow}",
            "",
            "case \"${1:-help}\" in",
            "  ace)",
            f"    {ace_cmd}",
            "    ;;",
            "  ace-tmux)",
            f"    tmux new-session -d -s musai-ace-$(basename {project_dir}) 'cd {ROOT} && {ace_cmd}; read -p \"done\"'",
            "    ;;",
            "  show)",
            f"    sed -n '1,260p' {project_dir / 'BRIEF.md'}",
            "    ;;",
            "  qa-ace)",
            f"    audio=$(find {project_dir / 'ace_step_output'} -type f -name '*.wav' 2>/dev/null | sort | head -n 1 || true)",
            "    if [[ -z \"${audio:-}\" ]]; then echo 'No ACE-Step wav output found.' >&2; exit 1; fi",
            f"    PYTHONNOUSERSITE=1 conda run -n musai python scripts/musai_quality_check.py \"$audio\" --language {language} --expected-lyrics-file {project_dir / 'lyrics_draft.txt'} --output-dir {project_dir}",
            "    ;;",
            "  *)",
            "    echo 'Usage: commands.sh ace|ace-tmux|qa-ace|show'",
            "    ;;",
            "esac",
            "",
        ]
    )


def render_aginti_handoff(project: CreativeProject) -> str:
    return f"""# AgInTiFlow Handoff - Musai Creative Project

Project: `{project.project_id}`
Musai repo: `{ROOT}`
Project dir: `{project.root}`

Goal:
Create the highest-quality song output possible from the provided materials. Do not claim final quality until listening and ASR/lyrics checks pass.

Suggested AgInTiFlow/Codex command:

```bash
codex -m gpt-5.5 -c model_reasoning_effort=\"high\" -s danger-full-access -a never --cd {ROOT} \"Inspect {project.root}, run the Musai commands, improve lyrics/prompt quality, generate or review audio outputs, and update the project report with evidence.\"
```

Key files:

```text
{project.root}/project.json
{project.root}/BRIEF.md
{project.root}/lyrics_draft.txt
{project.root}/ace_step_config.toml
{project.root}/commands.sh
```

Quality gate:

- Vocal must be sung and audible.
- Lyrics must be intelligible in the chosen language.
- Arrangement should follow supplied idea, chords, notation, or reference rhythm.
- For localization, keep stems and final mix paths explicit.
- Write a short QA note before accepting an output.
"""


def create_project(
    materials: CreativeMaterials,
    provider: str = "deepseek",
    model: str | None = None,
    analyze_reference: bool = False,
    output_root: Path = PROJECTS_ROOT,
) -> CreativeProject:
    provider_name, model_name, _ = provider_defaults(provider, model)
    project_id = f"{now_stamp()}-{slugify(materials.title)}"
    project_dir = ensure_dir(output_root / project_id)
    materials_dir = ensure_dir(project_dir / "materials")

    materials.lyrics = read_text_source(materials.lyrics)
    materials.chords = read_text_source(materials.chords)
    materials.notation = read_text_source(materials.notation)
    materials.reference_lyrics = read_text_source(materials.reference_lyrics)
    materials.reference_audio = copy_material(materials.reference_audio, materials_dir)

    workflow = classify_workflow(materials)
    analysis_manifest: dict[str, Any] | None = None
    artifacts: dict[str, str] = {}
    if analyze_reference and materials.reference_audio and Path(materials.reference_audio).exists():
        from .pipeline import run_pipeline

        analysis_name = f"{project_id}-reference-analysis"
        analysis_manifest = run_pipeline(
            Path(materials.reference_audio),
            ROOT / "data" / "runs",
            run_name=analysis_name,
            lyrics_ref=None,
            max_duration=min(float(materials.duration or 120), 180.0),
            asr_model="small",
            language=None,
            demucs_device=os.getenv("MUSAI_DEMUCS_DEVICE", "cuda"),
        )
        artifacts["reference_analysis"] = str((ROOT / "data" / "runs" / analysis_name).resolve())

    brief, model_meta = call_brief_model(provider_name, model_name, materials, workflow, analysis_manifest)
    ace_config = write_ace_config(project_dir, materials, brief)
    commands_path = project_dir / "commands.sh"

    project = CreativeProject(
        project_id=project_id,
        root=str(project_dir),
        created_at=datetime.now(timezone.utc).isoformat(),
        materials=materials,
        workflow=workflow,
        provider=provider_name,
        model=model_name,
        artifacts=artifacts,
    )
    project.artifacts.update(
        {
            "brief_json": str(project_dir / "brief.json"),
            "brief_md": str(project_dir / "BRIEF.md"),
            "lyrics_draft": str(project_dir / "lyrics_draft.txt"),
            "ace_step_config": str(ace_config),
            "commands": str(commands_path),
            "aginti_handoff": str(project_dir / "AGINTI_HANDOFF.md"),
        }
    )
    project.commands = {
        "show": f"{commands_path} show",
        "ace": f"{commands_path} ace",
        "ace_tmux": f"{commands_path} ace-tmux",
        "web": "scripts/start_musai_studio_tmux.sh",
    }

    write_json(project_dir / "brief.json", {"meta": model_meta, "brief": brief})
    (project_dir / "lyrics_draft.txt").write_text((brief.get("lyrics") or "").strip() + "\n", encoding="utf-8")
    (project_dir / "BRIEF.md").write_text(render_brief_markdown(project, brief, model_meta, analysis_manifest), encoding="utf-8")
    commands_path.write_text(render_commands(project_dir, ace_config, workflow, ace_language_code(materials)), encoding="utf-8")
    commands_path.chmod(0o755)
    (project_dir / "AGINTI_HANDOFF.md").write_text(render_aginti_handoff(project), encoding="utf-8")
    write_json(project_dir / "project.json", asdict(project))
    return project


def list_projects(root: Path = PROJECTS_ROOT) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    projects: list[dict[str, Any]] = []
    for project_json in sorted(root.glob("*/project.json"), reverse=True):
        try:
            projects.append(json.loads(project_json.read_text(encoding="utf-8")))
        except Exception:
            continue
    return projects


def load_project(project_id: str, root: Path = PROJECTS_ROOT) -> dict[str, Any]:
    path = root / project_id / "project.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))
