# Add One Song to Musia

For a catalog-only addition, use the existing learning runtime without changing
authentication, billing, creator services or store builds. The public ingress
uses an exact detail-path allowlist: a new song ID also needs its exact GET/HEAD
route admitted before the catalog is activated.
Publish and verify the audio and Fun item before activating the native catalog.

## Prepare

From a clean release checkout, using the Musia Python environment:

```bash
python scripts/prepare_learning_song_addition.py SONG_ID .runtime/song-addition.json
python -m unittest tests.test_catalog_add_packet
```

The packet contains one eligible public song, its sanitized native DTO, its
catalog entry, and only its manifest, study and lyric JSON. It cannot add server
code or another song. Review the packet and retain its SHA-256 outside Git.

## Activate

Use the existing pinned admin SSH route and private credential helper. Do not
copy credentials or introduce another tunnel. Coordinate a separate, bounded
ingress-owner update for `/api/v1/songs/SONG_ID` before activation. That update
must preserve all other matchers and sites, validate its candidate, use live
configuration concurrency checks, and retain a scoped rollback. Never widen
the matcher to all song paths or replace the whole Musia site from stale config.
The catalog controller itself does not mutate ingress and refuses a missing
route before changing the service.
Read the current release immediately before deployment. Upload the packet to a
private staging path, then run the reviewed controller through the existing
admin helper:

```bash
python3 -B catalog_add.py PACKET_PATH \
  --sha256 PACKET_SHA256 \
  --expected-release /srv/musia-learning/releases/EXACT_CURRENT_RELEASE
```

The controller takes the existing deployment lock and refuses an unresolved
transaction, changed release, insufficient memory/disk or an existing song ID.
It creates a new immutable copy of the current release, adds the one song and
checks every existing song DTO for byte-equivalent JSON structure. Only
`musia-learning.service` is restarted. Caddy configuration hashes and process
identity must remain unchanged during catalog activation. The public HTTPS
detail DTO must equal the approved packet and appear exactly once in the public
library; loopback success alone cannot produce a publication receipt.
Failed acceptance restores the previous unit
and catalog; an unexpected concurrent edit retains the private journal for
owner reconciliation instead of overwriting another deployment.

Accepted receipts are stored in
`/var/lib/musia-learning/deployments/catalog-PACKET_PREFIX/accepted.json`.
The prior release is retained. This command does not prune releases or make
storage-policy decisions for other deployments.

## Verify

Independently fetch the public `/api/v1/library` and `/api/v1/songs/SONG_ID`.
Check the new title, audio URL, cover, all translated lyrics and timings.
Verify audio range playback and cover availability. Retain the deployed
release, packet digest and external probe result in the private deployment
receipt. Mock test success is not a live-deployment receipt.

Existing native apps fetch the catalog; no new store binary is needed for this
addition. App-side caches can require refreshing the library or reopening the
app. Updating an existing song is deliberately outside this add-only command.
