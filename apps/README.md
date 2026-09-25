# Musia Learning Apps

An accessible first music-practice loop, with native mobile clients. No singing
test or theory exam is required to start. The existing production Studio and Fun
player are independent of this learning app.

| Surface | Implementation |
| --- | --- |
| Web | `web/`, vanilla ES modules and local Lucide icons |
| Android | `android/`, Kotlin/Compose and Media3 |
| iOS | `ios/`, SwiftUI and AVFoundation |
| Shared catalog | `../musia/learning.py`, read-only FastAPI |

## Run Locally

Use the existing `musia` conda environment; do not duplicate model environments.

```bash
npm ci --prefix apps/web
npm run vendor --prefix apps/web
PYTHONNOUSERSITE=1 conda run -n musia python -m pip install -r requirements-learning.txt
PYTHONNOUSERSITE=1 MUSIA_PUBLIC_BASE_URL=http://127.0.0.1:18440 \
  conda run --no-capture-output -n musia python scripts/serve_musia_learning.py
```

Open <http://127.0.0.1:18440>. For a local persistent review use one project-owned
tmux session, `musia-learning`; do not create additional GUI stacks. Native
clients default to `https://musia.lazying.art`; see their own build instructions.

```bash
npm test --prefix apps/web
PYTHONNOUSERSITE=1 conda run -n musia python -m unittest discover -s tests -p test_learning_api.py
PYTHONNOUSERSITE=1 conda run -n musia python scripts/test_musia_learning_web.py
```

Browser tests use an installed Google Chrome when available, otherwise
Playwright's managed Chromium. Screenshots and receipts go under ignored
`.runtime/learning/review/`. They play actual reference audio and an existing Aya
song, check loop/rate/tap controls, persistence and mobile overflow.

## Trust And Scope

First Pulse is a constructed reference exercise with known timing and harmony.
Browser phrase replay is scheduled against the media clock, but HTML media
seeking and background timer throttling are not sample-accurate audio editing.
Use a rendered practice clip when exact seamless loop boundaries are required.
Song analyses are estimates, not verified transcriptions. No microphone, account,
user upload, analytics SDK, cloud synchronization or public generation control is
enabled. Creative briefs are local drafts. Do not market disabled capabilities
as completed features or submit inaccurate store privacy answers.

The public API exposes neither the Studio HTTP server nor arbitrary files or
shell commands. Deploy only through the isolated learning deployment workflow,
not by placing the development Studio behind a public reverse proxy.

See [product brief](../references/musia-learning-app-2026-09-25.md) and
[API contract](../docs/learning-api.md). Build success, internal testing,
invitations, formal review and public release are separate milestones.
