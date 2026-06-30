#!/usr/bin/env python3
"""Prepare and optionally run a reproducible DiffRhythm clean generation route."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
PROJECTS_ROOT = ROOT / "data" / "creative_projects"
DIFFRHYTHM_ROOT = ROOT / "third_party" / "DiffRhythm"
DIFFRHYTHM_PYTHON = ROOT / ".conda" / "diffrhythm" / "bin" / "python"

CLEAN_PROMPT_SUFFIX = (
    "Only sing the supplied LRC lyrics. No spoken words, no credits, no songwriter names, "
    "no artist names, no extra intro words, no extra outro words, no watermark, no distortion, "
    "clear lead vocal, smooth full-song phrasing, natural breath, no clipped final syllables."
)


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower()).strip("-")
    return cleaned or "diffrhythm-song"


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def sh_join(args: Iterable[str | Path]) -> str:
    return " ".join(shlex.quote(str(arg)) for arg in args)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    return path.expanduser().read_text(encoding="utf-8")


def clean_lyric_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            continue
        if line.startswith("#"):
            continue
        if line.startswith("《") and line.endswith("》"):
            continue
        lines.append(line)
    return lines


def seconds_to_lrc_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    minutes = int(seconds // 60)
    rest = seconds - minutes * 60
    whole = int(rest)
    centiseconds = int(round((rest - whole) * 100))
    if centiseconds >= 100:
        whole += 1
        centiseconds -= 100
    return f"{minutes:02d}:{whole:02d}.{centiseconds:02d}"


def build_even_lrc(lines: list[str], audio_length: int, vocal_start: float, tail_margin: float) -> str:
    if not lines:
        raise ValueError("No lyric lines found after removing blank lines and section labels.")
    usable = max(1.0, float(audio_length) - vocal_start - tail_margin)
    if len(lines) == 1:
        starts = [vocal_start]
    else:
        step = usable / len(lines)
        starts = [vocal_start + step * index for index in range(len(lines))]
    return "\n".join(f"[{seconds_to_lrc_time(start)}]{line}" for start, line in zip(starts, lines)) + "\n"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_infer_command(
    *,
    lrc_path: Path,
    output_dir: Path,
    audio_length: int,
    batch_infer_num: int,
    ref_prompt: str | None,
    ref_audio_path: Path | None,
    chunked: bool,
    diffrhythm_python: Path,
) -> list[str]:
    cmd = [
        str(diffrhythm_python),
        "infer/infer.py",
        "--lrc-path",
        str(lrc_path),
        "--audio-length",
        str(audio_length),
        "--output-dir",
        str(output_dir),
        "--batch-infer-num",
        str(batch_infer_num),
    ]
    if ref_audio_path:
        cmd += ["--ref-audio-path", str(ref_audio_path)]
    elif ref_prompt:
        cmd += ["--ref-prompt", ref_prompt]
    else:
        raise ValueError("Either ref_prompt or ref_audio_path is required.")
    if chunked:
        cmd.append("--chunked")
    return cmd


def run_command(cmd: list[str], cwd: Path, env: dict[str, str]) -> None:
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def render_commands_sh(infer_cmd: list[str], qa_cmd: list[str], analysis_cmd: list[str] | None) -> str:
    blocks = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        f"cd {shlex.quote(str(DIFFRHYTHM_ROOT))}",
        f"PYTHONNOUSERSITE=1 PYTHONPATH={shlex.quote(str(DIFFRHYTHM_ROOT))} {sh_join(infer_cmd)}",
        "",
        f"cd {shlex.quote(str(ROOT))}",
        sh_join(qa_cmd),
    ]
    if analysis_cmd:
        blocks += ["", sh_join(analysis_cmd)]
    blocks.append("")
    return "\n".join(blocks)


def render_route_md(
    *,
    title: str,
    language: str,
    project_dir: Path,
    source_lyrics: Path,
    lrc_path: Path,
    output_dir: Path,
    clean_prompt: str,
    infer_cmd: list[str],
    qa_cmd: list[str],
    analysis_cmd: list[str] | None,
    ran: bool,
) -> str:
    lines = [
        f"# DiffRhythm Clean Route - {title}",
        "",
        f"Created: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Purpose",
        "",
        "Use DiffRhythm for a full lyric-following route while reducing common failure modes:",
        "",
        "- credit hallucinations such as songwriter or artist names;",
        "- spoken intro/outro words not present in the lyric;",
        "- clipped final syllables;",
        "- prompt-only website lyrics that do not match generated sound.",
        "",
        "## Project",
        "",
        "```text",
        display_path(project_dir),
        "```",
        "",
        "## Inputs",
        "",
        f"- Language: `{language}`",
        f"- Source lyrics: `{display_path(source_lyrics)}`",
        f"- LRC: `{display_path(lrc_path)}`",
        f"- Output directory: `{display_path(output_dir)}`",
        "",
        "## Clean Prompt",
        "",
        "```text",
        clean_prompt,
        "```",
        "",
        "## Commands",
        "",
        "Generate:",
        "",
        "```bash",
        f"cd {shlex.quote(str(DIFFRHYTHM_ROOT))}",
        f"PYTHONNOUSERSITE=1 PYTHONPATH={shlex.quote(str(DIFFRHYTHM_ROOT))} {sh_join(infer_cmd)}",
        "```",
        "",
        "Quality check:",
        "",
        "```bash",
        f"cd {shlex.quote(str(ROOT))}",
        sh_join(qa_cmd),
        "```",
    ]
    if analysis_cmd:
        lines += [
            "",
            "Pipeline analysis:",
            "",
            "```bash",
            f"cd {shlex.quote(str(ROOT))}",
            sh_join(analysis_cmd),
            "```",
        ]
    lines += [
        "",
        "## Acceptance Checklist",
        "",
        "- Listen before publishing.",
        "- Run ASR on the selected mix and, when stems exist, on the separated vocal stem.",
        "- Run a no-VAD ASR pass when the beginning, outro, or soft repeated CJK lines may be swallowed.",
        "- Compare planned lyric lines against ASR timing gaps and long merged ASR segments.",
        "- Keep planned lyrics only when they are sound-close, grammatically stronger, and supported by listening.",
        "- Reject or mark experimental if the render adds credits, artist names, or unrelated outro text.",
        "- Website/LazyEdit lyrics must come from the corrected active-vocal lyric JSON, not the raw prompt.",
        "",
        f"Ran generation in this invocation: `{str(ran).lower()}`",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    lyric_group = parser.add_mutually_exclusive_group(required=True)
    lyric_group.add_argument("--lyrics-file", type=Path, help="Plain lyric file. Section labels are stripped and an even LRC is created.")
    lyric_group.add_argument("--lrc-file", type=Path, help="Existing hand-timed LRC file.")
    ref_group = parser.add_mutually_exclusive_group(required=True)
    ref_group.add_argument("--style-prompt", help="DiffRhythm text style prompt.")
    ref_group.add_argument("--ref-audio-path", type=Path, help="Reference audio for DiffRhythm style conditioning.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--project-dir", type=Path)
    parser.add_argument("--language", default="zh")
    parser.add_argument("--audio-length", type=int, default=285, help="DiffRhythm length: exactly 95, or 96-285.")
    parser.add_argument("--vocal-start", type=float, default=8.0, help="Used only when creating LRC from plain lyrics.")
    parser.add_argument("--tail-margin", type=float, default=8.0, help="Used only when creating LRC from plain lyrics.")
    parser.add_argument("--output-name", default="clean")
    parser.add_argument("--batch-infer-num", type=int, default=1)
    parser.add_argument("--no-chunked", action="store_true")
    parser.add_argument("--asr-model", default="small")
    parser.add_argument("--run", action="store_true", help="Actually run DiffRhythm after writing files.")
    parser.add_argument("--review", action="store_true", help="Run Musia QA after generation. Implied by --analyze.")
    parser.add_argument("--analyze", action="store_true", help="Run full Musia pipeline after generation.")
    parser.add_argument("--demucs-device", default="cuda")
    parser.add_argument("--diffrhythm-root", type=Path, default=DIFFRHYTHM_ROOT)
    parser.add_argument("--diffrhythm-python", type=Path, default=DIFFRHYTHM_PYTHON)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.audio_length != 95 and not (96 <= args.audio_length <= 285):
        raise SystemExit("--audio-length must be exactly 95 or between 96 and 285.")
    project_dir = args.project_dir or PROJECTS_ROOT / f"{slugify(args.title)}-diffrhythm-clean-{now_stamp()}"
    project_dir = project_dir.resolve()
    lyrics_dir = project_dir / "lyrics"
    output_dir = project_dir / "diffrhythm_outputs" / args.output_name
    reviews_dir = project_dir / "reviews" / args.output_name
    lrc_path = lyrics_dir / "clean.lrc"
    source_lyrics = lyrics_dir / "source_lyrics.txt"

    if args.lyrics_file:
        source_text = read_text(args.lyrics_file)
        write_text(source_lyrics, source_text)
        lrc_text = build_even_lrc(clean_lyric_lines(source_text), args.audio_length, args.vocal_start, args.tail_margin)
        write_text(lrc_path, lrc_text)
    else:
        lrc_text = read_text(args.lrc_file)
        source_text = "\n".join(line.split("]", 1)[-1] for line in lrc_text.splitlines() if "]" in line)
        write_text(source_lyrics, source_text.strip() + "\n")
        write_text(lrc_path, lrc_text if lrc_text.endswith("\n") else lrc_text + "\n")

    clean_prompt = ""
    ref_audio_path: Path | None = None
    if args.ref_audio_path:
        ref_audio_path = args.ref_audio_path.resolve()
        clean_prompt = f"Reference audio style route. Clean constraints documented: {CLEAN_PROMPT_SUFFIX}"
    else:
        clean_prompt = f"{args.style_prompt.strip()} {CLEAN_PROMPT_SUFFIX}"

    infer_cmd = build_infer_command(
        lrc_path=lrc_path,
        output_dir=output_dir,
        audio_length=args.audio_length,
        batch_infer_num=args.batch_infer_num,
        ref_prompt=None if ref_audio_path else clean_prompt,
        ref_audio_path=ref_audio_path,
        chunked=not args.no_chunked,
        diffrhythm_python=args.diffrhythm_python.resolve(),
    )
    qa_cmd = [
        "env",
        "PYTHONNOUSERSITE=1",
        "conda",
        "run",
        "--no-capture-output",
        "-n",
        "musia",
        "python",
        "scripts/musia_quality_check.py",
        str(output_dir / "output.wav"),
        "--language",
        args.language,
        "--asr-model",
        args.asr_model,
        "--expected-lyrics-file",
        str(source_lyrics),
        "--output-dir",
        str(reviews_dir),
    ]
    analysis_cmd = None
    if args.analyze:
        analysis_cmd = [
            "env",
            "PYTHONNOUSERSITE=1",
            "conda",
            "run",
            "--no-capture-output",
            "-n",
            "musia",
            "python",
            "scripts/run_pipeline.py",
            str(output_dir / "output.wav"),
            "--run-name",
            f"{slugify(args.title)}-{args.output_name}-analysis",
            "--max-duration",
            str(args.audio_length),
            "--asr-model",
            args.asr_model,
            "--language",
            args.language,
            "--demucs-device",
            args.demucs_device,
        ]

    write_text(project_dir / "commands.sh", render_commands_sh(infer_cmd, qa_cmd, analysis_cmd))
    (project_dir / "commands.sh").chmod(0o755)
    write_json(
        project_dir / "route.json",
        {
            "title": args.title,
            "language": args.language,
            "audioLength": args.audio_length,
            "projectDir": str(project_dir),
            "sourceLyrics": str(source_lyrics),
            "lrc": str(lrc_path),
            "outputDir": str(output_dir),
            "cleanPrompt": clean_prompt,
            "run": args.run,
            "review": args.review,
            "analyze": args.analyze,
            "inferCommand": infer_cmd,
            "qaCommand": qa_cmd,
            "analysisCommand": analysis_cmd,
        },
    )
    write_text(
        project_dir / "ROUTE.md",
        render_route_md(
            title=args.title,
            language=args.language,
            project_dir=project_dir,
            source_lyrics=source_lyrics,
            lrc_path=lrc_path,
            output_dir=output_dir,
            clean_prompt=clean_prompt,
            infer_cmd=infer_cmd,
            qa_cmd=qa_cmd,
            analysis_cmd=analysis_cmd,
            ran=args.run,
        ),
    )

    env = dict(**__import__("os").environ)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONPATH"] = str(args.diffrhythm_root.resolve())

    if args.run:
        run_command(infer_cmd, cwd=args.diffrhythm_root.resolve(), env=env)
    if args.run and (args.review or args.analyze):
        run_command(qa_cmd, cwd=ROOT, env=env)
    if args.run and args.analyze and analysis_cmd:
        run_command(analysis_cmd, cwd=ROOT, env=env)

    print(project_dir)


if __name__ == "__main__":
    main()
