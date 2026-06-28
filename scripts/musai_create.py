#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from musai.creative import CreativeMaterials, create_project, list_projects, load_project, MODEL_REGISTRY


def read_file_arg(path: str | None) -> str:
    if not path:
        return ""
    return Path(path).expanduser().read_text(encoding="utf-8").strip()


def cmd_models(_: argparse.Namespace) -> None:
    print(json.dumps(MODEL_REGISTRY, indent=2, ensure_ascii=False))


def cmd_list(_: argparse.Namespace) -> None:
    projects = list_projects()
    if not projects:
        print("No creative projects yet.")
        return
    for project in projects:
        materials = project.get("materials", {})
        print(f"{project.get('project_id')}  {project.get('workflow')}  {materials.get('title')}")


def cmd_show(args: argparse.Namespace) -> None:
    project = load_project(args.project_id)
    brief_path = Path(project["artifacts"]["brief_md"])
    print(brief_path.read_text(encoding="utf-8"))


def cmd_plan(args: argparse.Namespace) -> None:
    lyrics = args.lyrics or read_file_arg(args.lyrics_file)
    chords = args.chords or read_file_arg(args.chords_file)
    notation = args.notation or read_file_arg(args.notation_file)
    reference_lyrics = args.reference_lyrics or read_file_arg(args.reference_lyrics_file)
    materials = CreativeMaterials(
        title=args.title,
        idea=args.idea or "",
        lyrics=lyrics,
        chords=chords,
        notation=notation,
        style=args.style or "",
        genre=args.genre or "",
        mood=args.mood or "",
        language=args.language,
        vocal_language=args.vocal_language or args.language,
        reference_audio=args.reference_audio or "",
        reference_lyrics=reference_lyrics,
        target_language=args.target_language or "",
        duration=args.duration,
        bpm=args.bpm,
        keyscale=args.keyscale or "",
        time_signature=args.time_signature or "4",
        notes=args.notes or "",
    )
    project = create_project(
        materials,
        provider=args.provider,
        model=args.model,
        analyze_reference=args.analyze_reference,
    )
    print(project.root)
    print(f"Brief: {project.artifacts['brief_md']}")
    print(f"ACE-Step config: {project.artifacts['ace_step_config']}")
    print(f"Commands: {project.artifacts['commands']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Musai creative song CLI: idea/lyrics/chords/reference audio to model-ready song projects.")
    sub = parser.add_subparsers(dest="command", required=True)

    models = sub.add_parser("models", help="List local/API model roles.")
    models.set_defaults(func=cmd_models)

    list_cmd = sub.add_parser("list", help="List creative projects.")
    list_cmd.set_defaults(func=cmd_list)

    show = sub.add_parser("show", help="Show a project brief.")
    show.add_argument("project_id")
    show.set_defaults(func=cmd_show)

    plan = sub.add_parser("plan", help="Create a song project brief and backend commands.")
    plan.add_argument("--title", required=True)
    plan.add_argument("--idea")
    plan.add_argument("--lyrics")
    plan.add_argument("--lyrics-file")
    plan.add_argument("--chords")
    plan.add_argument("--chords-file")
    plan.add_argument("--notation", help="Staff notation, numbered notation, MIDI notes, or a melody sketch as text.")
    plan.add_argument("--notation-file")
    plan.add_argument("--style")
    plan.add_argument("--genre")
    plan.add_argument("--mood")
    plan.add_argument("--language", default="en")
    plan.add_argument("--vocal-language")
    plan.add_argument("--target-language")
    plan.add_argument("--reference-audio")
    plan.add_argument("--reference-lyrics")
    plan.add_argument("--reference-lyrics-file")
    plan.add_argument("--duration", type=int, default=120)
    plan.add_argument("--bpm", type=int)
    plan.add_argument("--keyscale")
    plan.add_argument("--time-signature", default="4")
    plan.add_argument("--notes")
    plan.add_argument("--provider", choices=["deepseek", "openai", "offline"], default="deepseek")
    plan.add_argument("--model")
    plan.add_argument("--analyze-reference", action="store_true", help="Run Demucs/ASR/beats/chords on --reference-audio while creating the project.")
    plan.set_defaults(func=cmd_plan)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
