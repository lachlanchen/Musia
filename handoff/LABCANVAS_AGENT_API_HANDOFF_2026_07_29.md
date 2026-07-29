# LabCanvas Agent API Handoff

Date: 2026-07-29

This note defines how AgInTi LabCanvas and WeChat/WeCom agents should reuse
Musia without duplicating its music models or production logic. It also records
the stable API surface that Musia should expose as its agent integration
evolves.

## Current Integration

Musia Studio already provides the first usable agent surface:

- one persistent Studio process, normally in tmux;
- Studio sessions with a working directory and message history;
- chat and worker profiles;
- durable worker job JSON;
- a registered artifact catalog and safe artifact download endpoint;
- creative workflow endpoints, including song and MV handoff creation;
- the `musia mv-pack` command for a reviewed song-first LALACHAN/Xiaoyunque
  handoff.

LabCanvas uses these existing endpoints:

```text
GET  /api/setup
GET  /api/chat/sessions
POST /api/chat/sessions
GET  /api/chat/messages?session_id=...
POST /api/chat/send
POST /api/chat/resume
GET  /api/job?id=...
GET  /api/jobs?session_id=...
GET  /api/artifacts?session_id=...
GET  /api/artifact?session_id=...&artifact_id=...
GET  /api/artifact/file?session_id=...&artifact_id=...
POST /api/workflows/create
```

The LabCanvas adapter is:

```text
/home/lachlan/ProjectsLFS/AgenticApp/src/agenticapp/musia_ops.py
```

Operator commands:

```bash
PYTHONPATH=src python -m agenticapp music status --json
PYTHONPATH=src python -m agenticapp music start --json

PYTHONPATH=src python -m agenticapp music submit \
  "Create and review this song" \
  --source-scope "TRANSPORT:EXACT_CHAT_SESSION" \
  --task-id TASK_ID \
  --mode worker \
  --json

PYTHONPATH=src python -m agenticapp music wait JOB_ID \
  --timeout 10800 \
  --json

PYTHONPATH=src python -m agenticapp music artifacts \
  --source-scope "TRANSPORT:EXACT_CHAT_SESSION" \
  --json

PYTHONPATH=src python -m agenticapp music artifact ARTIFACT_ID \
  --source-scope "TRANSPORT:EXACT_CHAT_SESSION" \
  --output-dir output/wechat_worker/TASK_ID/musia \
  --json

PYTHONPATH=src python -m agenticapp music mv-pack \
  --audio /absolute/path/to/reviewed-master.wav \
  --title "Song title" \
  --duration 15 \
  --copy-references \
  --json
```

LabCanvas hashes the source scope before persisting its session registry. Raw
chat identifiers, credentials, and private history must not be written to a
public artifact or committed.

The adapter also hashes task idempotency keys. Repeating the same task/prompt
reuses the existing Musia job. A changed prompt under the same task reports
`revision_required=true`; `--new-revision` is reserved for an explicitly
authorized new generation. Exact registered artifacts are downloaded by
session ID plus artifact ID, never by an arbitrary server-side path.

## Ownership

LabCanvas owns:

- source-chat isolation and current-message permissions;
- the persistent per-chat orchestration agent;
- interruption collection and task state;
- deciding whether the request asks for music only, music plus an MV, or public
  publication;
- verified artifact delivery to the exact source chat.

Musia owns:

- song project structure;
- lyrics, melody, vocal, localization, stem, mix, and review workflows;
- ACE-Step, SoulX, and other model selection;
- music-domain Studio history;
- durable music jobs and artifact registration;
- the reviewed master audio;
- song-first MV handoff packaging.

LALACHAN/Xiaoyunque owns visual MV generation. LazyEdit owns subtitle,
metadata, processing, and explicitly authorized public publication. These are
separate stages.

## Song-First MV Contract

The pipeline is:

1. Create or select a real Musia project.
2. Produce and review the final master audio.
3. Deliver the reviewed song when the request asks for the song.
4. Only when the request also asks for an MV, create a Musia MV handoff pack.
5. Generate visuals through the existing LALACHAN/Xiaoyunque browser workflow.
6. Treat the reviewed Musia master as the timing and soundtrack authority.
7. If generated video audio changed or degraded, use the handoff's ffmpeg
   command to replace it with the reviewed master.
8. Verify duration and audio/video streams.
9. Deliver the reviewed song and final MP4 to the exact source chat.
10. Enter LazyEdit/public platforms only when the current message explicitly
    requests publication.

Do not infer an MV from a song-only request. Do not infer public publication
from an MV request.

## Requested Stable Agent API

The current API is usable. A future stable agent-facing API should add:

```text
POST /api/agent/tasks
GET  /api/agent/tasks/{task_id}
POST /api/agent/tasks/{task_id}/interruptions
POST /api/agent/tasks/{task_id}/cancel
GET  /api/agent/tasks/{task_id}/artifacts
GET  /api/agent/artifacts/{artifact_id}/file
```

Suggested create payload:

```json
{
  "idempotency_key": "opaque-task-key",
  "source_scope_hash": "opaque-hash",
  "session_id": "optional-existing-session",
  "request": "full current request",
  "working_dir": "/path/inside/Musia",
  "mode": "worker",
  "stages": ["music"],
  "permissions": {
    "heavy_generation": true,
    "mv_generation": false,
    "public_publish": false
  }
}
```

Suggested task states:

```text
queued
running
waiting_review
completed
blocked
failed
canceled
```

The task response should include:

```json
{
  "id": "task-id",
  "session_id": "session-id",
  "status": "running",
  "current_stage": "mix_review",
  "message": "safe concise state",
  "next_poll_at": "ISO-8601 or null",
  "blocker": {},
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

Each artifact should include:

```json
{
  "id": "artifact-id",
  "title": "Reviewed master",
  "role": "reviewed_master_audio",
  "media_type": "audio/wav",
  "size_bytes": 123,
  "sha256": "hex",
  "download_url": "/api/agent/artifacts/artifact-id/file",
  "source_path": "safe project-relative path",
  "created_at": "ISO-8601"
}
```

The API should never return arbitrary filesystem paths outside approved Musia
roots. Artifact download must resolve the registered artifact identity rather
than accept a caller-supplied path.

## Interruptions And Resume

The future task API should accept ordered interruptions while a task runs:

```json
{
  "idempotency_key": "opaque-interruption-key",
  "message": "Make the chorus warmer and keep the same melody",
  "created_at": "ISO-8601"
}
```

Musia should persist the interruption and apply it before the next model/tool
stage. It must not silently replace earlier constraints with only the newest
message. If generation already consumed resources, the task should state
whether the interruption can revise the current artifact or requires a new
authorized generation.

Restarting Musia Studio must not erase sessions, task states, registered
artifacts, or pending review gates. Repeated `idempotency_key` values must
return the original task rather than create duplicate heavy generations.

## Permission Gates

Musia may execute local analysis and explicitly requested local music
generation. It must stop and report a blocker for:

- missing model/license/rights prerequisites;
- a requested voice clone without consent;
- a heavy rerun when the current idempotent task already consumed resources;
- MV generation when only music was requested;
- public publication without explicit current-message authorization;
- payment, credential changes, or another irreversible external action.

Publication is not part of the Musia agent API. It should return a reviewed
master and handoff artifacts; LabCanvas/LazyEdit owns later publication
authorization and verification.

## Compatibility

LabCanvas should continue working through the current Studio API while the
stable `/api/agent/*` contract is developed. The adapter should feature-detect
the new endpoints and preserve current commands as a fallback. No migration
may invalidate existing Studio sessions or artifact records.
