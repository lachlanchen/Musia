# Musia Agent Notes

For Musia song videos, publish Instagram via the direct Meta API for
`@lazyingart`, separately from other destinations. Follow
[`references/musia-instagram-meta-api.md`](references/musia-instagram-meta-api.md).
Do not substitute a browser or Postiz when the API is not authorized.

Musia is a local-first AI song-localization prototype.

Primary local workflow:

1. Use the `musia` conda environment.
2. Download a free/open test song with `scripts/download_open_songs.py`.
3. Run `scripts/run_pipeline.py` on the downloaded song.
4. Inspect generated files under `data/runs/<run-id>/`.

Do not commit generated audio, downloaded songs, model weights, API keys, or cloned third-party repositories.

Core commands:

```bash
bash scripts/bootstrap_musia.sh
PYTHONNOUSERSITE=1 conda run -n musia python scripts/download_open_songs.py --id danny-boy-1917
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny --max-duration 45 --asr-model tiny
```

Legacy naming: old local notes may mention `Musai`, `musai`, or `MUSAI_*`.
Treat those as compatibility fallbacks only. New code, docs, and commands should
use `Musia`, `musia`, and `MUSIA_*`.
