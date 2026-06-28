#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const PKG = JSON.parse(fs.readFileSync(path.join(ROOT, "package.json"), "utf8"));
const DEFAULT_ENV = "musai";

const PY_COMMANDS = new Set([
  "models",
  "list",
  "show",
  "plan",
  "setup",
  "sessions",
  "new-session",
  "resume-session",
  "messages",
  "chat",
  "jobs",
  "job",
  "artifacts",
  "soulx-verse"
]);

function usage() {
  return `Musai ${PKG.version}

Usage:
  musai <command> [args]

Web app:
  musai studio [--host 127.0.0.1] [--port 8766]
  musai studio --tmux
  musai web [...same as studio]

Creative CLI:
  musai setup
  musai models
  musai plan --title "My Song" --idea "..." --provider deepseek
  musai song init --title "Aya Chan" --vocal-language ja --lyrics-file lyrics.txt
  musai song review --project-dir data/creative_projects/... --audio song.wav --run-analysis
  musai song correct --project-dir data/creative_projects/... --issues "vocal too quiet"
  musai song handoff --project-dir data/creative_projects/... --audio song.wav
  musai plan --title "Vocal" --generation-mode free_vocal --lyrics "..."
  musai plan --title "Controlled" --generation-mode controlled_song --control-level melody_sheet --melody "..."
  musai plan --title "Licensed CN Version" --generation-mode localization --control-level strict_localization --rights-confirmed --target-language zh-CN --reference-audio song.wav
  musai soulx-verse --title "Rain Day" --idea "A rainy bilingual musical short film verse"
  musai new-session --title "My album" --cwd ./my-song-folder
  musai chat --cwd ./my-song-folder --mode chat "What should I do next?"
  musai chat --cwd ./my-song-folder --mode worker "Analyze this song and register artifacts."
  musai sessions --cwd ./my-song-folder
  musai resume-session <session-id> --cwd ./another-folder
  musai jobs --session-id <id>
  musai artifacts <session-id>

Analysis pipeline:
  musai pipeline INPUT_AUDIO --run-name my-run --max-duration 60
  musai download-open-song --id danny-boy-1917

Environment/setup:
  musai bootstrap
  musai doctor [--json]

Runtime selection:
  MUSAI_CONDA_ENV=musai          conda env name, default "musai"
  MUSAI_PYTHON=/path/python      use a direct Python interpreter
  MUSAI_NO_CONDA=1               use python3/python instead of conda
`;
}

function fail(message, code = 1) {
  console.error(message);
  process.exit(code);
}

function hasArg(args, name) {
  return args.includes(name);
}

function stripArgs(args, names) {
  return args.filter((arg) => !names.includes(arg));
}

function findExecutable(names) {
  const pathEnv = process.env.PATH || "";
  const exts = process.platform === "win32" ? ["", ".cmd", ".exe", ".bat"] : [""];
  for (const dir of pathEnv.split(path.delimiter)) {
    if (!dir) continue;
    for (const name of names) {
      for (const ext of exts) {
        const candidate = path.join(dir, name + ext);
        if (fs.existsSync(candidate)) return candidate;
      }
    }
  }
  return "";
}

function spawn(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || ROOT,
    env: { ...process.env, PYTHONNOUSERSITE: process.env.PYTHONNOUSERSITE || "1" },
    stdio: options.stdio || "inherit",
    encoding: options.encoding || "utf8"
  });
  if (result.error) {
    fail(`${command}: ${result.error.message}`);
  }
  if (typeof result.status === "number" && result.status !== 0 && options.exitOnError !== false) {
    process.exit(result.status);
  }
  return result;
}

function pythonCommand(scriptRelative, args) {
  const script = path.join(ROOT, scriptRelative);
  if (!fs.existsSync(script)) {
    fail(`Missing script: ${script}`);
  }
  if (process.env.MUSAI_PYTHON) {
    return { command: process.env.MUSAI_PYTHON, args: [script, ...args] };
  }
  if (!process.env.MUSAI_NO_CONDA) {
    const conda = findExecutable(["conda"]);
    if (conda) {
      return {
        command: conda,
        args: ["run", "-n", process.env.MUSAI_CONDA_ENV || DEFAULT_ENV, "python", script, ...args]
      };
    }
  }
  const python = findExecutable(["python3", "python"]);
  if (!python) {
    fail("Python was not found. Install Python/conda or set MUSAI_PYTHON.");
  }
  return { command: python, args: [script, ...args] };
}

function runPython(scriptRelative, args) {
  const cmd = pythonCommand(scriptRelative, args);
  return spawn(cmd.command, cmd.args);
}

function runShell(scriptRelative, args) {
  const script = path.join(ROOT, scriptRelative);
  if (!fs.existsSync(script)) fail(`Missing script: ${script}`);
  return spawn("bash", [script, ...args]);
}

function doctor(jsonOutput = false) {
  const conda = findExecutable(["conda"]);
  const python = process.env.MUSAI_PYTHON || findExecutable(["python3", "python"]);
  const ffmpeg = findExecutable(["ffmpeg"]);
  const tmux = findExecutable(["tmux"]);
  const codex = findExecutable(["codex"]);
  const npm = findExecutable(["npm"]);
  const setupScript = fs.existsSync(path.join(ROOT, "scripts", "musai_create.py"));
  const data = {
    package: PKG.name,
    version: PKG.version,
    root: ROOT,
    node: process.version,
    npm: npm || "",
    conda: conda || "",
    conda_env: process.env.MUSAI_CONDA_ENV || DEFAULT_ENV,
    python: python || "",
    ffmpeg: ffmpeg || "",
    tmux: tmux || "",
    codex: codex || "",
    openai_api_key: Boolean(process.env.OPENAI_API_KEY),
    deepseek_api_key: Boolean(process.env.DEEPSEEK_API_KEY),
    hf_token: Boolean(process.env.HF_TOKEN),
    scripts_present: setupScript
  };
  if (jsonOutput) {
    console.log(JSON.stringify(data, null, 2));
    return;
  }
  for (const [key, value] of Object.entries(data)) {
    console.log(`${key}: ${value}`);
  }
}

function npmSmoke() {
  const checks = [
    ["package.json", path.join(ROOT, "package.json")],
    ["bin/musai.js", path.join(ROOT, "bin", "musai.js")],
    ["musai/studio.py", path.join(ROOT, "musai", "studio.py")],
    ["scripts/musai_studio_web.py", path.join(ROOT, "scripts", "musai_studio_web.py")],
    ["scripts/musai_create.py", path.join(ROOT, "scripts", "musai_create.py")]
  ];
  const missing = checks.filter(([, file]) => !fs.existsSync(file));
  if (missing.length) {
    fail(`Missing package files: ${missing.map(([label]) => label).join(", ")}`);
  }
  console.log("Musai npm smoke ok.");
}

function runStudio(args) {
  if (hasArg(args, "--tmux")) {
    return runShell("scripts/start_musai_studio_tmux.sh", stripArgs(args, ["--tmux"]));
  }
  return runPython("scripts/musai_studio_web.py", args.length ? args : ["--host", "127.0.0.1", "--port", "8766"]);
}

function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  const rest = args.slice(1);

  if (!command || command === "-h" || command === "--help" || command === "help") {
    console.log(usage());
    return;
  }
  if (command === "-v" || command === "--version" || command === "version") {
    console.log(PKG.version);
    return;
  }
  if (command === "doctor") {
    doctor(hasArg(rest, "--json"));
    return;
  }
  if (command === "npm-smoke") {
    npmSmoke();
    return;
  }
  if (command === "studio" || command === "web") {
    runStudio(rest);
    return;
  }
  if (command === "bootstrap") {
    runShell("scripts/bootstrap_musai.sh", rest);
    return;
  }
  if (command === "pipeline" || command === "run-pipeline") {
    runPython("scripts/run_pipeline.py", rest);
    return;
  }
  if (command === "download-open-song" || command === "download-open-songs") {
    runPython("scripts/download_open_songs.py", rest);
    return;
  }
  if (command === "song" || command === "song-workbench") {
    runPython("scripts/musai_song_workbench.py", rest);
    return;
  }
  if (PY_COMMANDS.has(command)) {
    runPython("scripts/musai_create.py", [command, ...rest]);
    return;
  }
  fail(`Unknown command: ${command}\n\n${usage()}`);
}

main();
