# Shared Guitar Shapes

`guitar-shapes.json` is the canonical 24-shape major/minor table for the native
learning apps and `apps/web`. It preserves the voicings already used by the Fun
player, adding explicit barre information and validating their pitch content.
The older Fun site remains a separate renderer.

- Standard tuning, low E on the left: MIDI 40, 45, 50, 55, 59, 64.
- Frets: -1 muted, 0 open, positive numbers are absolute frets.
- Fingers: 0 absent, 1 index, 2 middle, 3 ring, 4 little.
- Barres: `[absoluteFret, firstString, lastString, finger]`, zero-based strings.
- Four visible frets. Use fret 1 for low-position shapes; otherwise start at
  the lowest fretted note. Never draw fret 8 inside a fret-1-only diagram.
- Sharp/flat enharmonics and `:maj`/`:min` are accepted. Unsupported seventh,
  suspended, slash, and no-chord symbols stay unavailable rather than silently
  teaching a different chord. Only the web's explicit simplify control may
  request a simplified chord before lookup.

These are playable reference fingerings, not the only possible voicings or a
claim that the automatically detected chord/timestamp in a song is correct.

## Update And Check

Edit the JSON, then run from the repository root:

```sh
conda run -n musia python tools/generate_guitar_shapes.py
conda run -n musia python tools/generate_guitar_shapes.py --check
node --test apps/web/tests/core.test.mjs apps/web/guitar-shapes.test.mjs
```

The generator changes only marked source-table regions. Validation checks exact
major/minor chord tones, root bass, finger assignments, repeated fingers/barres,
and the fret viewport. Native tests check the same invariants independently.
The learning deployment builder rejects stale generated tables.

For browser rendering and responsive footer checks, start the existing learning
server and run `scripts/test_musia_chord_layout.py --base-url <URL>`. Its intercepted
24-chord timeline is a rendering fixture, never a score or production song data.
It checks portrait/landscape phone, tablet and desktop layouts at normal and
enlarged text sizes. Use `scripts/test_musia_learning_web.py` separately for real
audio playback and API integration. Native QA also needs tab navigation with a
selected song, rotation, large text and actual device playback.
