# Musai Agent Notes

Musai is a local-first AI song-localization prototype.

Primary local workflow:

1. Use the `musai` conda environment.
2. Download a free/open test song with `scripts/download_open_songs.py`.
3. Run `scripts/run_pipeline.py` on the downloaded song.
4. Inspect generated files under `data/runs/<run-id>/`.

Do not commit generated audio, downloaded songs, model weights, API keys, or cloned third-party repositories.

Core commands:

```bash
bash scripts/bootstrap_musai.sh
PYTHONNOUSERSITE=1 conda run -n musai python scripts/download_open_songs.py --id danny-boy-1917
PYTHONNOUSERSITE=1 conda run -n musai python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny --max-duration 45 --asr-model tiny
```
