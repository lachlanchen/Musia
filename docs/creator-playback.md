# Creator Audio Playback

The audited original and the delivery file have different jobs. Keep
`artifacts/<job>/song.wav` unchanged: the corrected lyrics, content review and
approval remain bound to its SHA-256. Generate a smaller full-length
`song.mp3` for browser and native playback. Do not synthesize, trim or rewrite
lyrics to create that derivative.

## Delivery Contract

- `musia/creator/media.py` produces 320 kbps, stereo, 48 kHz MP3 with one CPU
  thread. It verifies both streams and allows at most 0.12 seconds of container
  duration difference, including MP3 encoder padding.
- `playback.json` records fixed local filenames, both digests, durations and
  the encoding profile. It is the atomic completion marker, not an input path.
- Conversion runs under the worker lock, never inside an HTTP request. Both
  source and derivative must match the private completion manifest before the
  API serves the MP3. Missing or invalid derivatives fall back to the WAV.
- Derivative failure must not reject an intact original merely because the
  optional diagnostic cannot be written. Source mutation still fails closed.
- The same audio endpoint checks ownership, visibility and moderation on every
  request, including HEAD and byte ranges. Private and newly unshared songs do
  not become accessible through a static file or alternate URL. Responses remain
  non-cacheable.
- Native private playback downloads through the authenticated API, stores audio
  in an owner-protected app cache and removes it on sign-out. The extension is
  not an authorization decision; clients must support both WAV and MP3.

Backfill an already reviewed song without regenerating or approving it again:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python tools/creator.py \
  --data "$HOME/.local/share/musia/creator-live" prepare-playback JOB_ID
```

The command accepts an existing ready/review job only and uses its ledger path
and original digest. It does not change visibility, quota or review state.

## Verification

The October 9 live check reduced a 90-second file from 17,280,078 WAV bytes to
3,601,965 MP3 bytes. Sequential authenticated full downloads on the same route
took 102.5 and 17.81 seconds respectively. These are individual observations,
not a throughput guarantee. The WAV digest was unchanged.

Run `test_creator_media.py` for fixed-profile conversion, full duration,
idempotence, corruption/path/permission checks and real FFmpeg coverage.
`test_creator.py` also checks derivative MIME, HEAD/ranges, private/public access,
unsharing and malformed-manifest fallback.

On Apple, check the actual song-detail destination, not just the library root.
The mini-player must belong to the whole navigation stack, remain above the
tab bar, and be tappable after the private download. An enabled Open button
only proves that the busy operation ended. Acceptance requires the real player
position to advance and private playback to disappear after sign-out.

Record genuine device/simulator results separately from unit-test fixtures.
Successful download alone is not audible-output, background-audio, or purchase
qualification.
