(function initMusiaToolkit() {
  const NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  const FLATS = {
    Cb: "B",
    Db: "C#",
    Eb: "D#",
    Fb: "E",
    Gb: "F#",
    Ab: "G#",
    Bb: "A#"
  };
  const SIMPLE_SUFFIXES = [
    [/^m(?!aj)/i, "m"],
    [/^(dim|o)/i, "dim"],
    [/^aug/i, "aug"],
    [/^sus2/i, "sus2"],
    [/^sus4|^sus/i, "sus4"]
  ];

  function normalizeRoot(root) {
    const clean = String(root || "").trim().replace(/♯/g, "#").replace(/♭/g, "b");
    return FLATS[clean] || clean;
  }

  function noteIndex(note) {
    return NOTES.indexOf(normalizeRoot(note));
  }

  function transposeRoot(root, semitones = 0) {
    const index = noteIndex(root);
    if (index < 0) return root || "";
    const next = (index + Number(semitones || 0) + 1200) % 12;
    return NOTES[next];
  }

  function parseChord(symbol) {
    const source = String(symbol || "").trim().replace(/♯/g, "#").replace(/♭/g, "b");
    const match = source.match(/^([A-G](?:#|b)?)([^/]*)((?:\/)([A-G](?:#|b)?))?$/);
    if (!match) {
      return { source, root: "", suffix: "", bass: "", valid: false };
    }
    return {
      source,
      root: normalizeRoot(match[1]),
      suffix: match[2] || "",
      bass: normalizeRoot(match[4] || ""),
      valid: true
    };
  }

  function transposeChord(symbol, semitones = 0) {
    const parsed = parseChord(symbol);
    if (!parsed.valid) return String(symbol || "");
    const root = transposeRoot(parsed.root, semitones);
    const bass = parsed.bass ? `/${transposeRoot(parsed.bass, semitones)}` : "";
    return `${root}${parsed.suffix}${bass}`;
  }

  function simplifyChord(symbol) {
    const parsed = parseChord(symbol);
    if (!parsed.valid) return String(symbol || "");
    let suffix = "";
    for (const [pattern, replacement] of SIMPLE_SUFFIXES) {
      if (pattern.test(parsed.suffix)) {
        suffix = replacement;
        break;
      }
    }
    const bass = parsed.bass && parsed.bass !== parsed.root ? `/${parsed.bass}` : "";
    return `${parsed.root}${suffix}${bass}`;
  }

  function displayChord(symbol, options = {}) {
    const transpose = Number(options.transpose || 0);
    const capo = Math.max(0, Number(options.capo || 0));
    const concertRaw = transposeChord(symbol, transpose);
    const guitarRaw = transposeChord(symbol, transpose - capo);
    return {
      original: String(symbol || ""),
      concert: options.simplify ? simplifyChord(concertRaw) : concertRaw,
      guitar: options.simplify ? simplifyChord(guitarRaw) : guitarRaw,
      capo,
      transpose
    };
  }

  function beatLengthFromBpm(bpm) {
    const value = Number(bpm);
    return Number.isFinite(value) && value > 0 ? 60 / value : 0;
  }

  function makeBeatGrid({ beats = [], bpm = 0, duration = 0, timeSignature = "4/4" } = {}) {
    const numericBeats = beats
      .map((beat, index) => ({
        index: Number.isFinite(Number(beat?.index)) ? Number(beat.index) : index,
        time: Number(beat?.time),
        source: beat?.source || "analysis"
      }))
      .filter((beat) => Number.isFinite(beat.time))
      .sort((a, b) => a.time - b.time);
    const beatsPerBar = Number(String(timeSignature || "4/4").split("/")[0]) || 4;
    if (!numericBeats.length) {
      const step = beatLengthFromBpm(bpm);
      if (!step || !duration) return [];
      const count = Math.ceil(Number(duration) / step);
      return Array.from({ length: count }, (_, index) => ({
        index,
        time: Number((index * step).toFixed(3)),
        bar: Math.floor(index / beatsPerBar) + 1,
        beatInBar: (index % beatsPerBar) + 1,
        source: "estimated"
      }));
    }
    return numericBeats.map((beat, index) => ({
      ...beat,
      bar: Math.floor(index / beatsPerBar) + 1,
      beatInBar: (index % beatsPerBar) + 1
    }));
  }

  function activeBeatAt(grid = [], time = 0) {
    if (!grid.length) return null;
    let active = null;
    for (const beat of grid) {
      if (Number(beat.time) <= Number(time)) active = beat;
      else break;
    }
    return active || grid[0];
  }

  function lineMetrics(line, beatGrid = []) {
    const start = Number(line?.start);
    const end = Number(line?.end);
    const tokens = Array.isArray(line?.tokens)
      ? line.tokens.filter((token) => String(token?.text || "").trim() && !/^[,，、。.!?？；;：:\s]+$/.test(token.text))
      : [];
    const duration = Number.isFinite(start) && Number.isFinite(end) ? Math.max(0, end - start) : 0;
    const beats = beatGrid.filter((beat) => Number(beat.time) >= start && Number(beat.time) < end);
    return {
      duration,
      tokenCount: tokens.length,
      wordsPerSecond: duration > 0 ? tokens.length / duration : 0,
      beatCount: beats.length,
      startBeat: beats[0] || activeBeatAt(beatGrid, start),
      endBeat: beats[beats.length - 1] || activeBeatAt(beatGrid, end)
    };
  }

  window.Musia = {
    NOTES,
    normalizeRoot,
    parseChord,
    transposeRoot,
    transposeChord,
    simplifyChord,
    displayChord,
    makeBeatGrid,
    activeBeatAt,
    lineMetrics
  };
})();
