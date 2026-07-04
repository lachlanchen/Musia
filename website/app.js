const state = {
  catalog: null,
  manifest: null,
  manifestUrl: "",
  defaultTracks: [],
  lyricSets: [],
  activeLyricSetId: "",
  tracks: [],
  trackByCode: new Map(),
  selectedLyricLangs: new Set(),
  kindFilter: "all",
  searchQuery: "",
  libraryOpen: false,
  searchOpen: false,
  activeMediaId: "",
  activeAssetId: "",
  mediaElement: null,
  sourceNodes: new Map(),
  audioContext: null,
  analyser: null,
  source: null,
  sourceElement: null,
  frequencyData: null,
  captureMode: false,
  captureMultilingual: false,
  skipIntroOnLoad: false,
  didApplySkipIntro: false,
  renderedChordKey: "",
  captureTime: null,
  libraryPreviewIndex: 0,
  libraryPreviewTimer: null,
  requestedAssetId: "",
  playbackMode: "off",
  userPlaybackMode: false,
  advancingPlayback: false,
  advancedMode: false,
  advancedChordRenderKey: "",
  playbackSyncFrame: 0,
  mediaSessionHandlersInstalled: false
};

const $ = (id) => document.getElementById(id);
const audio = $("audio");
const video = $("video");
const externalPlayer = $("external-player");
const coverArt = $("cover-art");
const coverThumb = $("cover-thumb");
const canvas = $("visualizer");
const ctx = canvas.getContext("2d");

const PLAYBACK_MODES = [
  { id: "off", label: "Stop", title: "Stop after the current song" },
  { id: "cycle", label: "Cycle", title: "Play the next song when this one ends" },
  { id: "shuffle", label: "Shuffle", title: "Play a random song when this one ends" },
  { id: "single", label: "Loop 1", title: "Loop the current song" }
];

const NOTE_FRETS = {
  E: 0,
  F: 1,
  "F#": 2,
  Gb: 2,
  G: 3,
  "G#": 4,
  Ab: 4,
  A: 5,
  "A#": 6,
  Bb: 6,
  B: 7,
  C: 8,
  "C#": 9,
  Db: 9,
  D: 10,
  "D#": 11,
  Eb: 11
};

const GUITAR_CHORDS = {
  A: { frets: ["x", 0, 2, 2, 2, 0], fingers: ["", "", "1", "2", "3", ""], label: "open A" },
  Am: { frets: ["x", 0, 2, 2, 1, 0], fingers: ["", "", "2", "3", "1", ""], label: "open A minor" },
  B: { frets: ["x", 2, 4, 4, 4, 2], fingers: ["", "1", "3", "3", "3", "1"], label: "A-shape barre" },
  Bb: { frets: ["x", 1, 3, 3, 3, 1], fingers: ["", "1", "3", "3", "3", "1"], label: "A-shape barre" },
  Bbmaj7: { frets: ["x", 1, 3, 2, 3, 1], fingers: ["", "1", "3", "2", "4", "1"], label: "Bb major 7" },
  Bm: { frets: ["x", 2, 4, 4, 3, 2], fingers: ["", "1", "3", "4", "2", "1"], label: "A minor-shape barre" },
  Bbm: { frets: ["x", 1, 3, 3, 2, 1], fingers: ["", "1", "3", "4", "2", "1"], label: "A minor-shape barre" },
  C: { frets: ["x", 3, 2, 0, 1, 0], fingers: ["", "3", "2", "", "1", ""], label: "open C" },
  Cadd9: { frets: ["x", 3, 2, 0, 3, 3], fingers: ["", "3", "2", "", "4", "4"], label: "open C add 9" },
  "C#": { frets: ["x", 4, 6, 6, 6, 4], fingers: ["", "1", "3", "3", "3", "1"], label: "A-shape barre" },
  "C#m": { frets: ["x", 4, 6, 6, 5, 4], fingers: ["", "1", "3", "4", "2", "1"], label: "A minor-shape barre" },
  Cm: { frets: ["x", 3, 5, 5, 4, 3], fingers: ["", "1", "3", "4", "2", "1"], label: "A minor-shape barre" },
  D: { frets: ["x", "x", 0, 2, 3, 2], fingers: ["", "", "", "1", "3", "2"], label: "open D" },
  Dm: { frets: ["x", "x", 0, 2, 3, 1], fingers: ["", "", "", "2", "3", "1"], label: "open D minor" },
  "Dm/A": { frets: ["x", 0, 0, 2, 3, 1], fingers: ["", "", "", "2", "3", "1"], label: "D minor over A" },
  Dm9: { frets: ["x", 5, 3, 5, 5, "x"], fingers: ["", "2", "1", "3", "4", ""], label: "D minor 9" },
  E: { frets: [0, 2, 2, 1, 0, 0], fingers: ["", "2", "3", "1", "", ""], label: "open E" },
  Eb: { frets: ["x", 6, 8, 8, 8, 6], fingers: ["", "1", "3", "3", "3", "1"], label: "A-shape barre" },
  Ebm: { frets: ["x", 6, 8, 8, 7, 6], fingers: ["", "1", "3", "4", "2", "1"], label: "A minor-shape barre" },
  Em: { frets: [0, 2, 2, 0, 0, 0], fingers: ["", "2", "3", "", "", ""], label: "open E minor" },
  F: { frets: [1, 3, 3, 2, 1, 1], fingers: ["1", "3", "4", "2", "1", "1"], label: "E-shape barre" },
  Fadd9: { frets: [1, 3, 3, 0, 1, 1], fingers: ["1", "3", "4", "", "1", "1"], label: "F add 9" },
  "F#": { frets: [2, 4, 4, 3, 2, 2], fingers: ["1", "3", "4", "2", "1", "1"], label: "E-shape barre" },
  "F#m": { frets: [2, 4, 4, 2, 2, 2], fingers: ["1", "3", "4", "1", "1", "1"], label: "E minor-shape barre" },
  Fm: { frets: [1, 3, 3, 1, 1, 1], fingers: ["1", "3", "4", "1", "1", "1"], label: "E minor-shape barre" },
  G: { frets: [3, 2, 0, 0, 0, 3], fingers: ["3", "2", "", "", "", "4"], label: "open G" },
  Gm: { frets: [3, 5, 5, 3, 3, 3], fingers: ["1", "3", "4", "1", "1", "1"], label: "E minor-shape barre" },
  Gm7: { frets: [3, 5, 3, 3, 3, 3], fingers: ["1", "3", "1", "1", "1", "1"], label: "G minor 7" },
  Ab: { frets: [4, 6, 6, 5, 4, 4], fingers: ["1", "3", "4", "2", "1", "1"], label: "E-shape barre" },
  Abm: { frets: [4, 6, 6, 4, 4, 4], fingers: ["1", "3", "4", "1", "1", "1"], label: "E minor-shape barre" }
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[char]);
}

function formatTime(seconds) {
  const safe = Number.isFinite(seconds) ? Math.max(0, seconds) : 0;
  return `${Math.floor(safe / 60)}:${Math.floor(safe % 60).toString().padStart(2, "0")}`;
}

function labelKind(kind) {
  return {
    song: "Music",
    "localized-song": "Localized",
    mv: "MV",
    "short-film": "Short film",
    video: "Video",
    "youtube-video": "YouTube"
  }[kind] || "Media";
}

function resolveSitePath(path) {
  if (!path) return "";
  return new URL(path, window.location.href).href;
}

function resolveManifestPath(path) {
  if (!path) return "";
  return new URL(path, state.manifestUrl).href;
}

function pinyinTone(value) {
  return String(value || "")
    .replace("1", "ˉ")
    .replace("2", "ˊ")
    .replace("3", "ˇ")
    .replace("4", "ˋ")
    .replace("5", "");
}

function tokenLabel(token) {
  return token.display || (token.pinyin ? token.pinyin.replace(/\d/g, "") : token.text);
}

function tokenHasTiming(token) {
  return Number.isFinite(Number(token?.start)) && Number.isFinite(Number(token?.end));
}

function isSungToken(token) {
  const text = String(token?.text || "");
  return text.trim() && !/^[,，、。.!?？；;：:\s]+$/.test(text);
}

function timedTokensForLine(line) {
  const tokens = Array.isArray(line?.tokens) ? line.tokens.map((token) => ({ ...token })) : [];
  const start = Number(line?.start);
  const end = Number(line?.end);
  const sungIndexes = tokens
    .map((token, index) => isSungToken(token) ? index : -1)
    .filter((index) => index >= 0);

  if (!sungIndexes.length || !Number.isFinite(start) || !Number.isFinite(end) || end <= start) {
    return tokens;
  }
  if (sungIndexes.every((index) => tokenHasTiming(tokens[index]))) {
    return tokens;
  }

  const slot = (end - start) / sungIndexes.length;
  sungIndexes.forEach((tokenIndex, sungIndex) => {
    if (!tokenHasTiming(tokens[tokenIndex])) {
      tokens[tokenIndex].start = Number((start + slot * sungIndex).toFixed(3));
      tokens[tokenIndex].end = Number((start + slot * (sungIndex + 1)).toFixed(3));
    }
  });
  return tokens;
}

function timingAttrs(token) {
  if (!tokenHasTiming(token)) return "";
  return ` data-token-start="${Number(token.start)}" data-token-end="${Number(token.end)}"`;
}

function renderRubyToken(token) {
  const attrs = timingAttrs(token);
  if (token.reading) {
    return `<span class="text-token ruby-token"${attrs}><ruby>${escapeHtml(token.text)}<rt>${escapeHtml(token.reading)}</rt></ruby></span>`;
  }
  if (token.pinyin) {
    return `<span class="text-token ruby-token"${attrs}><ruby>${escapeHtml(token.text)}<rt>${escapeHtml(pinyinTone(token.pinyin))}</rt></ruby></span>`;
  }
  return attrs ? `<span class="text-token ruby-token"${attrs}>${escapeHtml(token.text)}</span>` : escapeHtml(token.text);
}

function renderTrackLine(track, line, { compact = false } = {}) {
  if (!line) return "";
  const tokens = timedTokensForLine(line);
  const hasRuby = tokens.some((token) => token.pinyin || token.reading);
  const hasTiming = tokens.some(tokenHasTiming);
  const text = line.singableText || line.text;

  if (hasRuby) {
    return `<div class="${compact ? "ruby-line compact" : "ruby-line"}">${tokens.map(renderRubyToken).join("")}</div>`;
  }

  if (hasTiming && !compact) {
    return `<div class="token-line">${tokens.map((token) => `
      <span class="text-token"${timingAttrs(token)}>
        ${escapeHtml(token.text)}
      </span>
    `).join("")}</div>`;
  }

  return `<div class="plain-line">${escapeHtml(text)}</div>`;
}

function manifestLines() {
  return state.manifest?.timeline?.lines || [];
}

function activeTimingTrack() {
  const activeAsset = activePlayableAsset();
  return state.trackByCode.get(activeAsset?.languageCode) || selectedLyricTracks()[0] || state.tracks[0] || null;
}

function timingLines() {
  const track = activeTimingTrack();
  return Array.isArray(track?.lines) && track.lines.length ? track.lines : manifestLines();
}

function lineStartForDisplay(line) {
  const timing = lineForTrack(activeTimingTrack(), line?.id);
  return Number.isFinite(timing?.start) ? timing.start : line?.start || 0;
}

function chords() {
  return activeMusical()?.chords || [];
}

function activeMusical() {
  const manifestMusical = state.manifest?.musical || {};
  const primaryMusical = state.manifest?.assets?.primaryAudio?.musical || {};
  const assetMusical = activePlayableAsset()?.musical || {};
  const timeline = (...values) => values.find((value) => Array.isArray(value) && value.length) || [];
  return {
    ...manifestMusical,
    ...primaryMusical,
    ...assetMusical,
    chords: timeline(assetMusical.chords, primaryMusical.chords, manifestMusical.chords),
    beats: timeline(assetMusical.beats, primaryMusical.beats, manifestMusical.beats)
  };
}

function selectedLyricTracks() {
  const selected = state.tracks.filter((track) => state.selectedLyricLangs.has(track.language.code));
  return selected.length ? selected : state.tracks;
}

function languageName(trackOrCode) {
  const track = typeof trackOrCode === "string" ? state.trackByCode.get(trackOrCode) : trackOrCode;
  return track?.language?.nativeLabel || track?.language?.label || track?.language?.code || "";
}

function selectedLyricSummary() {
  const tracks = selectedLyricTracks();
  if (!tracks.length) return "Lyrics";
  if (tracks.length === state.tracks.length) return "Lyrics";
  return tracks.map(languageName).join(" · ");
}

function languageKey(code) {
  const value = String(code || "").toLowerCase();
  if (value.startsWith("zh")) return "zh";
  if (value.startsWith("ja")) return "ja";
  if (value.startsWith("en")) return "en";
  return value;
}

function languageShortLabel(code) {
  const key = languageKey(code);
  return { en: "EN", zh: "ZH", ja: "JP" }[key] || String(code || "LANG").slice(0, 3).toUpperCase();
}

function nativeLanguageName(code, fallback = "") {
  const key = languageKey(code);
  return {
    en: "English",
    zh: "中文",
    ja: "日本語",
    mul: "Multilingual"
  }[key] || fallback || String(code || "Language");
}

function vocalLanguageName(asset) {
  return asset?.languageNativeLabel
    || nativeLanguageName(asset?.languageCode, asset?.languageLabel || asset?.label);
}

function publicAssetRole(asset) {
  if (asset?.publicRoleLabel) return asset.publicRoleLabel;
  if (asset?.roleLabel && !/render|generated|same-score|localized|analysis|review|candidate/i.test(asset.roleLabel)) {
    return asset.roleLabel;
  }
  if (asset?.type === "external-video" || asset?.type === "video") return "Video";
  if (asset?.languageCode) return "Vocal";
  if (asset?.type === "audio") return "Audio";
  return "Media";
}

function displayTitleForAsset(asset = activePlayableAsset()) {
  const titles = state.manifest?.localizedTitles || {};
  const code = asset?.languageCode || activeTimingTrack()?.language?.code || "";
  return titles[code] || titles[languageKey(code)] || state.manifest?.title || "Fun Lazying Art";
}

function updateMediaTitle() {
  const title = displayTitleForAsset();
  $("media-title").textContent = title;
  $("media-artist").textContent = state.manifest?.artist ? `by ${state.manifest.artist}` : "";
  document.title = `${title} - Fun Lazying Art`;
}

function firstVocalStart() {
  const lines = timingLines();
  const first = lines.find((line) => Number.isFinite(Number(line?.start)));
  return Number.isFinite(Number(first?.start)) ? Math.max(0, Number(first.start)) : 0;
}

function applySkipIntro({ force = false } = {}) {
  const media = state.mediaElement;
  if (!media) return;
  const start = firstVocalStart();
  if (start <= 0.25) return;
  if (!force && state.didApplySkipIntro) return;
  media.currentTime = Math.max(0, start - 0.02);
  state.didApplySkipIntro = true;
  updateSync();
}

function updateMusicalLabels() {
  const musical = activeMusical();
  $("key-label").textContent = musical.key || "No key";
  $("bpm-label").textContent = musical.bpm ? `${Math.round(Number(musical.bpm))} BPM` : "No BPM";
}

function lineForTrack(track, lineId) {
  return track?.lines?.find((line) => line.id === lineId) || null;
}

function activeLineAt(time) {
  const lines = timingLines();
  const active = lines.find((line) => time >= line.start && time < line.end);
  if (active) return active;

  const previous = [...lines].reverse().find((line) => time >= line.end);
  const next = lines.find((line) => time < line.start);
  const hangoverSeconds = 1.25;
  if (previous && time - previous.end <= hangoverSeconds) return previous;
  if (previous && next && next.start - previous.end <= hangoverSeconds) return previous;
  return null;
}

function lyricGapState(time) {
  const lines = timingLines();
  if (!lines.length) return null;
  const previousIndex = [...lines].reverse().findIndex((line) => time >= line.end);
  const previous = previousIndex >= 0 ? lines[lines.length - 1 - previousIndex] : null;
  const next = lines.find((line) => time < line.start) || null;
  if (!previous && next) {
    return { label: "♪♪♪", detail: `[Instrumental intro] vocal starts at ${formatTime(next.start)}`, next };
  }
  if (previous && next) {
    return { label: "♪♪♪", detail: `[Instrumental break] next vocal at ${formatTime(next.start)}`, previous, next };
  }
  if (previous && !next) {
    return { label: "♪♪♪", detail: "[Instrumental outro] vocal has ended", previous };
  }
  return null;
}

function fullLyricDisplayRows(lines) {
  const rows = [];
  const gapThreshold = 1.6;
  const duration = Number(state.manifest?.duration) || 0;
  lines.forEach((line, index) => {
    rows.push({ type: "lyric", line });
    const next = lines[index + 1];
    if (next && next.start - line.end > gapThreshold) {
      rows.push({
        type: "instrumental",
        id: `gap-${line.id}-${next.id}`,
        start: line.end,
        end: next.start,
        label: "♪♪♪",
        detail: `${index === 0 ? "[Instrumental intro]" : "[Instrumental break]"} no vocal lyric · next vocal ${formatTime(next.start)}`
      });
    }
  });
  const last = lines[lines.length - 1];
  if (last && duration && duration - last.end > gapThreshold) {
    rows.push({
      type: "instrumental",
      id: `gap-${last.id}-outro`,
      start: last.end,
      end: duration,
      label: "♪♪♪",
      detail: "[Instrumental outro] no vocal lyric"
    });
  }
  return rows;
}

function activeChordAt(time) {
  const list = chords();
  return list.find((chord) => time >= chord.start && time < chord.end)
    || [...list].reverse().find((chord) => time >= chord.end)
    || null;
}

function parseChordName(name) {
  const source = String(name || "").trim().replace(/♯/g, "#").replace(/♭/g, "b");
  const base = source.split("/")[0];
  const match = base.match(/^([A-G](?:#|b)?)(.*)$/);
  if (!match) return null;
  const root = match[1];
  const suffix = match[2] || "";
  let quality = "";
  if (/^m(?!aj)/i.test(suffix)) quality = "m";
  if (/maj7/i.test(suffix)) quality = "maj7";
  else if (/m7/i.test(suffix)) quality = "m7";
  else if (/7/i.test(suffix)) quality = "7";
  else if (/add9/i.test(suffix)) quality = "add9";
  return { root, quality, key: `${root}${quality}`, suffix, source };
}

function movableShapeForChord(parsed) {
  if (!parsed || !Object.prototype.hasOwnProperty.call(NOTE_FRETS, parsed.root)) return null;
  const rootFret = NOTE_FRETS[parsed.root];
  const useFret = rootFret === 0 ? 12 : rootFret;
  if (parsed.quality === "m") {
    return {
      frets: [useFret, useFret + 2, useFret + 2, useFret, useFret, useFret],
      fingers: ["1", "3", "4", "1", "1", "1"],
      label: "movable minor barre"
    };
  }
  if (parsed.quality === "7") {
    return {
      frets: [useFret, useFret + 2, useFret, useFret + 1, useFret, useFret],
      fingers: ["1", "3", "1", "2", "1", "1"],
      label: "movable dominant 7"
    };
  }
  if (parsed.quality === "" || parsed.quality === "add9" || parsed.quality === "maj7") {
    return {
      frets: [useFret, useFret + 2, useFret + 2, useFret + 1, useFret, useFret],
      fingers: ["1", "3", "4", "2", "1", "1"],
      label: parsed.quality ? "movable major shape" : "movable major barre"
    };
  }
  return null;
}

function guitarShapeForChord(name) {
  const parsed = parseChordName(name);
  if (!parsed) return null;
  const exact = GUITAR_CHORDS[parsed.source] || GUITAR_CHORDS[parsed.key];
  if (exact) return { ...exact, parsed };
  const movable = movableShapeForChord(parsed);
  return movable ? { ...movable, parsed } : null;
}

function diagramBaseFret(frets) {
  const numeric = frets.filter((fret) => Number.isFinite(Number(fret)) && Number(fret) > 0).map(Number);
  if (!numeric.length) return 1;
  if (numeric.some((fret) => fret === 1) || frets.some((fret) => Number(fret) === 0)) return 1;
  return Math.min(...numeric);
}

function renderGuitarDiagram(chordName, shape) {
  const diagram = $("guitar-diagram");
  const position = $("chord-diagram-position");
  const fingering = $("chord-fingering");
  $("chord-diagram-name").textContent = chordName || "--";
  if (!shape) {
    position.textContent = "";
    diagram.innerHTML = `<div class="guitar-empty">No guitar fingering for this chord yet.</div>`;
    fingering.innerHTML = `<span>${escapeHtml(chordName || "No chord")}</span>`;
    return;
  }

  const frets = shape.frets;
  const fingers = shape.fingers || [];
  const baseFret = diagramBaseFret(frets);
  const fretCount = 5;
  const stringLeft = (index) => 10 + index * 16;
  const fretTop = (index) => 12 + index * 17;
  const markerTop = (absoluteFret) => {
    const relative = Math.max(1, Number(absoluteFret) - baseFret + 1);
    return (fretTop(relative - 1) + fretTop(relative)) / 2;
  };

  const strings = frets.map((_, index) =>
    `<span class="guitar-string" style="left:${stringLeft(index)}%"></span>`
  ).join("");
  const fretLines = Array.from({ length: fretCount + 1 }, (_, index) =>
    `<span class="guitar-fret ${index === 0 && baseFret === 1 ? "nut" : ""}" style="top:${fretTop(index)}%"></span>`
  ).join("");
  const openMuted = frets.map((fret, index) => {
    const muted = String(fret).toLowerCase() === "x";
    if (!muted && Number(fret) !== 0) return "";
    return `<span class="guitar-open ${muted ? "muted" : ""}" style="left:${stringLeft(index)}%">${muted ? "×" : "○"}</span>`;
  }).join("");
  const markers = frets.map((fret, index) => {
    const numeric = Number(fret);
    if (!Number.isFinite(numeric) || numeric <= 0) return "";
    const relative = numeric - baseFret + 1;
    if (relative < 1 || relative > fretCount) return "";
    const finger = fingers[index] || "●";
    return `<span class="guitar-marker" style="left:${stringLeft(index)}%;top:${markerTop(numeric)}%">${escapeHtml(finger)}</span>`;
  }).join("");

  position.textContent = baseFret > 1 ? `${baseFret}fr` : "open";
  diagram.setAttribute("aria-label", `${chordName} guitar fingering`);
  diagram.innerHTML = `${strings}${fretLines}${openMuted}${markers}`;
  fingering.innerHTML = [
    `<span>${escapeHtml(shape.label || "guitar shape")}</span>`,
    `<span>frets ${escapeHtml(frets.join(" "))}</span>`,
    `<span>E A D G B E</span>`
  ].join("");
}

function updateAdvancedChord(activeChord = null) {
  const panel = $("advanced-panel");
  if (!panel) return;
  panel.hidden = !state.advancedMode || !activeChord;
  if (!state.advancedMode) {
    state.advancedChordRenderKey = "";
    return;
  }
  const chordName = activeChord?.name || "";
  const chordKey = `${activeChord?.start ?? ""}-${activeChord?.end ?? ""}-${chordName}`;
  if (state.advancedChordRenderKey === chordKey) return;
  state.advancedChordRenderKey = chordKey;
  renderGuitarDiagram(chordName, guitarShapeForChord(chordName));
}

function setAdvancedMode(enabled, { persist = true } = {}) {
  state.advancedMode = Boolean(enabled);
  document.body.classList.toggle("advanced-mode", state.advancedMode);
  const button = $("advanced-toggle");
  if (button) {
    button.setAttribute("aria-pressed", state.advancedMode ? "true" : "false");
    button.textContent = state.advancedMode ? "Advanced On" : "Advanced";
  }
  if (persist) {
    try {
      localStorage.setItem("funAdvancedMode", state.advancedMode ? "1" : "0");
    } catch {
      // Storage can be unavailable in private or file contexts.
    }
  }
  updateAdvancedChord(activeChordAt(state.mediaElement?.currentTime || 0));
}

function youtubeIdFromUrl(value) {
  if (!value) return "";
  const text = String(value).trim();
  if (/^[a-zA-Z0-9_-]{6,}$/.test(text) && !text.includes("/")) return text;
  try {
    const url = new URL(text);
    if (url.hostname.includes("youtu.be")) return url.pathname.replace("/", "");
    if (url.hostname.includes("youtube.com")) {
      if (url.searchParams.get("v")) return url.searchParams.get("v");
      const embedMatch = url.pathname.match(/\/embed\/([^/?#]+)/);
      if (embedMatch) return embedMatch[1];
      const shortsMatch = url.pathname.match(/\/shorts\/([^/?#]+)/);
      if (shortsMatch) return shortsMatch[1];
    }
  } catch {
    return "";
  }
  return "";
}

function youtubeEmbedUrl(asset) {
  if (asset.embedUrl) return asset.embedUrl;
  const videoId = asset.videoId || youtubeIdFromUrl(asset.url || asset.src);
  if (!videoId) return "";
  const params = new URLSearchParams({ rel: "0", modestbranding: "1", playsinline: "1" });
  return `https://www.youtube-nocookie.com/embed/${encodeURIComponent(videoId)}?${params}`;
}

function youtubeWatchUrl(asset) {
  if (asset.url) return asset.url;
  const videoId = asset.videoId || youtubeIdFromUrl(asset.embedUrl || asset.src);
  return videoId ? `https://www.youtube.com/watch?v=${encodeURIComponent(videoId)}` : asset.embedUrl || asset.src || "";
}

function youtubeThumbnailUrl(asset) {
  const videoId = asset?.videoId || youtubeIdFromUrl(asset?.url || asset?.embedUrl || asset?.src);
  return videoId ? `https://i.ytimg.com/vi/${encodeURIComponent(videoId)}/hqdefault.jpg` : "";
}

function playableAssets(manifest) {
  const assets = manifest.assets || {};
  const result = [];
  if (assets.primaryAudio?.src) result.push({ ...assets.primaryAudio, id: assets.primaryAudio.id || "primary", label: assets.primaryAudio.label || "Mix", type: "audio", src: assets.primaryAudio.src });
  if (assets.primaryVideo?.src) result.push({ ...assets.primaryVideo, id: assets.primaryVideo.id || "video", label: assets.primaryVideo.label || "Video", type: "video", src: assets.primaryVideo.src });
  if (assets.youtube) {
    const embedUrl = youtubeEmbedUrl(assets.youtube);
    if (embedUrl) result.push({ ...assets.youtube, id: assets.youtube.id || "youtube", label: assets.youtube.label || "YouTube", type: "external-video", embedUrl, url: youtubeWatchUrl(assets.youtube) });
  }
  for (const item of assets.externalVideos || []) {
    const provider = item.provider || (youtubeIdFromUrl(item.url || item.embedUrl || item.src) ? "youtube" : "external");
    const embedUrl = provider === "youtube" ? youtubeEmbedUrl(item) : (item.embedUrl || item.src || "");
    if (embedUrl) result.push({ ...item, id: item.id || item.label || embedUrl, label: item.label || "External", type: "external-video", embedUrl, url: provider === "youtube" ? youtubeWatchUrl(item) : (item.url || embedUrl) });
  }
  for (const item of assets.alternateAudio || []) {
    if (item.src) result.push({ ...item, id: item.id || item.label || item.src, label: item.label || item.id || "Audio", type: "audio", src: item.src });
  }
  return result;
}

function activePlayableAsset() {
  return playableAssets(state.manifest || {}).find((asset) => asset.id === state.activeAssetId) || null;
}

function playbackQueueItems() {
  return (state.catalog?.items || []).filter((item) =>
    (item.kind === "song" || item.kind === "localized-song") && item.manifest
  );
}

function defaultPlaybackModeForManifest(manifest) {
  const mode = manifest?.playback?.defaultMode;
  return PLAYBACK_MODES.some((item) => item.id === mode) ? mode : "off";
}

function renderPlaybackMode() {
  const root = $("playback-mode");
  if (!root) return;
  root.innerHTML = PLAYBACK_MODES.map((mode) => {
    const active = mode.id === state.playbackMode;
    return `
      <button class="${active ? "active" : ""}" type="button" data-playback-mode="${escapeHtml(mode.id)}" aria-pressed="${active ? "true" : "false"}" title="${escapeHtml(mode.title)}">
        ${escapeHtml(mode.label)}
      </button>
    `;
  }).join("");
}

function setPlaybackMode(mode, { user = false } = {}) {
  state.playbackMode = PLAYBACK_MODES.some((item) => item.id === mode) ? mode : "off";
  if (user) state.userPlaybackMode = true;
  renderPlaybackMode();
}

function nextPlaybackItem({ shuffle = false } = {}) {
  const items = playbackQueueItems();
  if (!items.length) return null;
  if (shuffle && items.length > 1) {
    const candidates = items.filter((item) => item.id !== state.activeMediaId);
    return candidates[Math.floor(Math.random() * candidates.length)] || items[0];
  }
  const index = Math.max(0, items.findIndex((item) => item.id === state.activeMediaId));
  return items[(index + 1) % items.length];
}

async function playLoadedMediaFromStart() {
  const media = state.mediaElement;
  if (!media) return;
  state.captureTime = null;
  initAudioGraph();
  if (state.audioContext?.state === "suspended") await state.audioContext.resume();
  try {
    media.currentTime = 0;
    await media.play();
  } catch (error) {
    console.warn("Autoplay after track end was blocked.", error);
  }
}

async function handleMediaEnded() {
  if (state.captureMode || state.advancingPlayback) return;
  const mode = state.playbackMode;
  if (mode === "off") return;
  if (mode === "single") {
    await playLoadedMediaFromStart();
    return;
  }
  const nextItem = nextPlaybackItem({ shuffle: mode === "shuffle" });
  if (!nextItem) return;
  state.advancingPlayback = true;
  try {
    await loadMediaItem(nextItem, true);
    await playLoadedMediaFromStart();
  } finally {
    state.advancingPlayback = false;
  }
}

function activeLyricSetForAsset(asset = activePlayableAsset()) {
  if (!state.lyricSets.length) return null;
  return state.lyricSets.find((set) => set.id && set.id === asset?.lyricSetId)
    || state.lyricSets.find((set) => set.languageCode && set.languageCode === asset?.languageCode)
    || null;
}

function applyActiveLyricSet({ resetSelection = false } = {}) {
  const set = activeLyricSetForAsset();
  const tracks = set?.tracks?.length ? set.tracks : state.defaultTracks;
  const lyricSetId = set?.id || "__default__";
  const changedLyricSet = lyricSetId !== state.activeLyricSetId;
  state.activeLyricSetId = lyricSetId;
  state.tracks = tracks;
  state.trackByCode = new Map(state.tracks.map((track) => [track.language.code, track]));

  const available = new Set(state.tracks.map((track) => track.language.code));
  if (resetSelection || changedLyricSet || !state.selectedLyricLangs.size) {
    state.selectedLyricLangs = new Set(available);
    return;
  }
  state.selectedLyricLangs = new Set([...state.selectedLyricLangs].filter((code) => available.has(code)));
  if (!state.selectedLyricLangs.size) state.selectedLyricLangs = new Set(available);
}

function setLibraryOpen(open) {
  state.libraryOpen = Boolean(open);
  $("library-panel").hidden = !state.libraryOpen;
  $("library-backdrop").hidden = !state.libraryOpen;
  $("library-peek").hidden = state.libraryOpen;
  $("library-toggle").setAttribute("aria-expanded", state.libraryOpen ? "true" : "false");
  $("library-peek").setAttribute("aria-expanded", state.libraryOpen ? "true" : "false");
  if (!state.libraryOpen) {
    state.searchOpen = false;
    $("search-toggle").setAttribute("aria-expanded", "false");
  }
}

function setSearchOpen(open) {
  state.searchOpen = Boolean(open);
  $("search-toggle").setAttribute("aria-expanded", state.searchOpen ? "true" : "false");
  if (state.searchOpen) {
    setLibraryOpen(true);
    requestAnimationFrame(() => {
      $("catalog-search").focus();
      $("catalog-search").select();
    });
  }
}

function coverUrl(manifest) {
  return manifest.assets?.cover?.src || manifest.assets?.poster?.src || manifest.share?.image || youtubeThumbnailUrl(manifest.assets?.youtube) || "";
}

function setMeta(selector, value, attr = "content") {
  const node = document.querySelector(selector);
  if (node && value) node.setAttribute(attr, value);
}

function updateShareMetadata(manifest) {
  const title = manifest.share?.title || manifest.title;
  const description = manifest.share?.description || manifest.description || manifest.subtitle || "";
  const image = manifest.share?.image || coverUrl(manifest);
  const url = manifest.share?.url || manifest.canonicalUrl || "https://fun.lazying.art";
  document.title = `${manifest.title} - Fun Lazying Art`;
  setMeta('meta[name="description"]', description);
  setMeta('meta[property="og:title"]', title);
  setMeta('meta[property="og:description"]', description);
  setMeta('meta[property="og:image"]', image ? new URL(image, window.location.href).href : "");
  setMeta('meta[property="og:url"]', url);
  setMeta('meta[property="og:type"]', manifest.kind === "song" ? "music.song" : "video.other");
  setMeta('meta[name="twitter:title"]', title);
  setMeta('meta[name="twitter:description"]', description);
  setMeta('meta[name="twitter:image"]', image ? new URL(image, window.location.href).href : "");
}

function mediaSessionArtwork() {
  const cover = coverUrl(state.manifest || {});
  const resolvedCover = cover ? new URL(cover, window.location.href).href : "";
  const logo192 = new URL("assets/brand/fun-lazying-art-logo-192.png", window.location.href).href;
  const logo1024 = new URL("assets/brand/fun-lazying-art-logo.png", window.location.href).href;
  const artwork = [
    ...(resolvedCover ? [{ src: resolvedCover, sizes: "512x512", type: "image/png" }] : []),
    { src: logo192, sizes: "192x192", type: "image/png" },
    { src: logo1024, sizes: "1024x1024", type: "image/png" }
  ];
  return artwork;
}

function updateMediaSessionPosition() {
  if (!("mediaSession" in navigator) || typeof navigator.mediaSession.setPositionState !== "function") return;
  const media = state.mediaElement;
  if (!media) return;
  const duration = media.duration || state.manifest?.duration || 0;
  if (!Number.isFinite(duration) || duration <= 0) return;
  try {
    navigator.mediaSession.setPositionState({
      duration,
      playbackRate: media.playbackRate || 1,
      position: Math.min(duration, Math.max(0, media.currentTime || 0))
    });
  } catch {
    // Some browsers reject position updates before metadata is fully ready.
  }
}

function updateMediaSessionPlaybackState() {
  if (!("mediaSession" in navigator)) return;
  const media = state.mediaElement;
  navigator.mediaSession.playbackState = media && !media.paused ? "playing" : "paused";
  updateMediaSessionPosition();
}

async function playCurrentMedia() {
  const media = state.mediaElement;
  if (!media) return;
  state.captureTime = null;
  if (state.audioContext?.state === "suspended") await state.audioContext.resume();
  await media.play();
  updateMediaSessionPlaybackState();
}

function pauseCurrentMedia() {
  const media = state.mediaElement;
  if (!media) return;
  media.pause();
  updateMediaSessionPlaybackState();
}

async function loadAdjacentMedia({ previous = false, shuffle = false } = {}) {
  const items = playbackQueueItems();
  if (!items.length) return;
  let item = null;
  if (shuffle) {
    item = nextPlaybackItem({ shuffle: true });
  } else {
    const index = Math.max(0, items.findIndex((entry) => entry.id === state.activeMediaId));
    item = previous ? items[(index - 1 + items.length) % items.length] : items[(index + 1) % items.length];
  }
  if (!item) return;
  await loadMediaItem(item, true);
  await playLoadedMediaFromStart();
}

function installMediaSessionHandlers() {
  if (state.mediaSessionHandlersInstalled || !("mediaSession" in navigator)) return;
  state.mediaSessionHandlersInstalled = true;
  const setHandler = (name, handler) => {
    try {
      navigator.mediaSession.setActionHandler(name, handler);
    } catch {
      // Browsers support different Media Session action subsets.
    }
  };
  setHandler("play", () => playCurrentMedia());
  setHandler("pause", () => pauseCurrentMedia());
  setHandler("seekbackward", (details) => {
    const media = state.mediaElement;
    if (!media) return;
    media.currentTime = Math.max(0, media.currentTime - (details.seekOffset || 10));
    updateSync();
    updateMediaSessionPosition();
  });
  setHandler("seekforward", (details) => {
    const media = state.mediaElement;
    if (!media) return;
    const duration = media.duration || state.manifest?.duration || Number.MAX_SAFE_INTEGER;
    media.currentTime = Math.min(duration, media.currentTime + (details.seekOffset || 10));
    updateSync();
    updateMediaSessionPosition();
  });
  setHandler("seekto", (details) => {
    const media = state.mediaElement;
    if (!media || !Number.isFinite(details.seekTime)) return;
    media.currentTime = Math.max(0, details.seekTime);
    updateSync();
    updateMediaSessionPosition();
  });
  setHandler("previoustrack", () => loadAdjacentMedia({ previous: true }));
  setHandler("nexttrack", () => loadAdjacentMedia({ shuffle: state.playbackMode === "shuffle" }));
}

function updateMediaSession() {
  if (!("mediaSession" in navigator) || !state.manifest || !window.MediaMetadata) return;
  installMediaSessionHandlers();
  const asset = activePlayableAsset();
  navigator.mediaSession.metadata = new MediaMetadata({
    title: displayTitleForAsset(asset),
    artist: state.manifest.artist || "Musia",
    album: "Fun Lazying Art",
    artwork: mediaSessionArtwork()
  });
  updateMediaSessionPlaybackState();
}

function setMediaSource(asset, keepTime = false) {
  const previous = state.mediaElement;
  const previousTime = previous?.currentTime || 0;
  const wasPlaying = previous && !previous.paused;
  if (previous) previous.pause();
  state.activeAssetId = asset.id;
  state.captureTime = null;

  if (asset.type === "external-video") {
    state.mediaElement = null;
    audio.hidden = true;
    video.hidden = true;
    video.removeAttribute("src");
    externalPlayer.hidden = false;
    externalPlayer.src = asset.embedUrl;
    $("play").disabled = true;
    $("play").title = "Use the embedded player controls";
    $("play-symbol").textContent = "▶";
    applyActiveLyricSet();
    renderAssetSwitcher();
    renderLanguageButtons();
    renderVocalLanguageSelect();
    updateMediaTitle();
    updateMusicalLabels();
    updateMediaSession();
    updateSync();
    return;
  }

  externalPlayer.hidden = true;
  externalPlayer.src = "about:blank";
  state.mediaElement = asset.type === "video" ? video : audio;
  audio.hidden = asset.type === "video";
  video.hidden = asset.type !== "video";
  $("play").disabled = false;
  $("play").title = "";
  if (asset.crossOrigin === false) {
    state.mediaElement.removeAttribute("crossorigin");
  } else {
    state.mediaElement.crossOrigin = asset.crossOrigin || "anonymous";
  }
  state.mediaElement.src = resolveSitePath(asset.src);
  if (keepTime) state.mediaElement.currentTime = Math.min(previousTime, (state.manifest.duration || previousTime) - 0.1);
  if (wasPlaying) state.mediaElement.play().catch((error) => console.warn("Playback after asset switch was blocked.", error));
  applyActiveLyricSet();
  state.renderedChordKey = "";
  renderAssetSwitcher();
  renderLanguageButtons();
  renderVocalLanguageSelect();
  updateMediaTitle();
  updateMusicalLabels();
  updateMediaSession();
  updateSync();
}

function renderLibrary() {
  const items = state.catalog.items || [];
  const query = state.searchQuery.trim().toLowerCase();
  const visibleItems = items.filter((item) => {
    const kindMatch = state.kindFilter === "all" || item.kind === state.kindFilter;
    const haystack = [
      item.id,
      item.title,
      item.artist,
      item.summary,
      ...(item.languages || []),
      ...(item.tags || [])
    ].join(" ").toLowerCase();
    return kindMatch && (!query || haystack.includes(query));
  });
  $("media-library").innerHTML = visibleItems.length ? visibleItems.map((item) => `
    <button class="media-chip ${item.id === state.activeMediaId ? "active" : ""}" type="button" data-media-id="${escapeHtml(item.id)}">
      <span>${escapeHtml(labelKind(item.kind))}</span>
      <strong>${escapeHtml(item.title)}</strong>
    </button>
  `).join("") : `<div class="empty-chip">No matching media</div>`;
  document.querySelectorAll("[data-media-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const item = state.catalog.items.find((entry) => entry.id === button.dataset.mediaId);
      if (!item) return;
      if (item.id === state.activeMediaId) {
        setLibraryOpen(false);
        return;
      }
      await loadMediaItem(item, true);
      setLibraryOpen(false);
    });
  });
}

function libraryPreviewItems() {
  return (state.catalog?.items || [])
    .filter((item) => item.kind === "song" || item.kind === "localized-song")
    .slice(0, 3);
}

function updateLibraryPeekPreview() {
  const node = $("peek-song");
  const items = libraryPreviewItems();
  if (!node || !items.length) return;
  const item = items[state.libraryPreviewIndex % items.length];
  state.libraryPreviewIndex = (state.libraryPreviewIndex + 1) % items.length;
  node.textContent = item.title;
  node.classList.remove("is-looping");
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    void node.offsetWidth;
    node.classList.add("is-looping");
  }
}

function startLibraryPeekLoop() {
  if (state.libraryPreviewTimer) clearInterval(state.libraryPreviewTimer);
  updateLibraryPeekPreview();
  if (state.captureMode || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  state.libraryPreviewTimer = setInterval(updateLibraryPeekPreview, 2800);
}

function renderAssetSwitcher() {
  const assets = playableAssets(state.manifest);
  $("asset-switcher").innerHTML = assets.map((asset) => `
    <button class="${asset.id === state.activeAssetId ? "active" : ""}" type="button" data-asset-id="${escapeHtml(asset.id)}">
      <span>${escapeHtml(publicAssetRole(asset))}</span>
      <strong>${escapeHtml(asset.languageLabel || asset.label)}</strong>
    </button>
  `).join("");
  document.querySelectorAll("[data-asset-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const asset = assets.find((item) => item.id === button.dataset.assetId);
      if (asset) setMediaSource(asset, true);
    });
  });
}

function renderVocalLanguageSelect() {
  const wrap = $("vocal-language-select")?.closest(".vocal-select-wrap");
  const select = $("vocal-language-select");
  if (!wrap || !select) return;
  const assets = playableAssets(state.manifest).filter((asset) => asset.languageCode);
  wrap.hidden = assets.length < 2;
  if (assets.length < 2) {
    select.innerHTML = "";
    return;
  }
  select.innerHTML = assets.map((asset) => `
    <option value="${escapeHtml(asset.id)}">${escapeHtml(vocalLanguageName(asset))}</option>
  `).join("");
  select.value = state.activeAssetId || assets[0].id;
}

function renderLanguageButtons() {
  if (!state.tracks.length) {
    $("language-tabs").innerHTML = `<span class="soft-note">No lyrics</span>`;
    return;
  }
  $("language-tabs").innerHTML = `
    ${state.tracks.map((track) => {
      const active = state.selectedLyricLangs.has(track.language.code);
      return `
    <button class="${active ? "active" : ""}" type="button" data-lang="${escapeHtml(track.language.code)}" aria-pressed="${active ? "true" : "false"}">
      ${escapeHtml(track.language.nativeLabel || track.language.label || track.language.code)}
    </button>
      `;
    }).join("")}
  `;
  document.querySelectorAll("[data-lang]").forEach((button) => {
    button.addEventListener("click", () => {
      const code = button.dataset.lang;
      if (state.selectedLyricLangs.has(code)) state.selectedLyricLangs.delete(code);
      else state.selectedLyricLangs.add(code);
      if (state.selectedLyricLangs.size === 0) state.selectedLyricLangs.add(code);
      renderLanguageButtons();
      updateSync();
    });
  });
}

function renderChords(activeChord = null) {
  const list = chords();
  const row = $("chord-row");
  const activeIndex = activeChord ? list.findIndex((chord) =>
    chord === activeChord
    || (chord.name === activeChord.name
      && Number(chord.start) === Number(activeChord.start)
      && Number(chord.end) === Number(activeChord.end))
  ) : -1;
  row.hidden = list.length === 0;
  const key = list.map((chord) => `${chord.start}-${chord.end}-${chord.name}`).join("|");
  if (row.dataset.chordKey !== key) {
    row.dataset.chordKey = key;
    row.dataset.activeChordIndex = "";
    row.innerHTML = list.map((chord, index) => `
      <button class="chord-pill" type="button" data-chord-index="${index}">
        <strong>${escapeHtml(chord.name)}</strong><span>${escapeHtml(chord.degree || "")}</span>
      </button>
    `).join("");
    row.querySelectorAll("[data-chord-index]").forEach((button) => {
      button.addEventListener("click", () => {
        const chord = list[Number(button.dataset.chordIndex)];
        if (!chord || !state.mediaElement) return;
        state.mediaElement.currentTime = chord.start;
        state.mediaElement.play();
      });
    });
  }
  row.querySelectorAll("[data-chord-index]").forEach((button) => {
    const active = Number(button.dataset.chordIndex) === activeIndex;
    button.classList.toggle("active", active);
    button.setAttribute("aria-current", active ? "true" : "false");
  });
  if (activeIndex >= 0 && row.dataset.activeChordIndex !== String(activeIndex)) {
    row.dataset.activeChordIndex = String(activeIndex);
    requestAnimationFrame(() => {
      const activeButton = row.querySelector(".chord-pill.active");
      if (!activeButton) return;
      const rowRect = row.getBoundingClientRect();
      const buttonRect = activeButton.getBoundingClientRect();
      const buttonCenter = (buttonRect.left - rowRect.left) + row.scrollLeft + (buttonRect.width / 2);
      const centeredLeft = buttonCenter - (row.clientWidth / 2);
      row.scrollTo({ left: Math.max(0, centeredLeft), behavior: state.captureMode ? "auto" : "smooth" });
    });
  }
  updateAdvancedChord(activeChord);
}

function renderCarousel(activeLine) {
  const tracks = selectedLyricTracks();
  const lines = timingLines();
  if (!tracks.length || !lines.length) {
    $("lyric-carousel").innerHTML = `<div class="empty-state"><h2>${escapeHtml(state.manifest.title)}</h2><p>${escapeHtml(state.manifest.description || "No timed lyrics are attached yet.")}</p></div>`;
    return;
  }
  const rawActiveIndex = activeLine ? lines.findIndex((line) => line.id === activeLine.id) : -1;
  const time = state.mediaElement?.currentTime || 0;
  const gap = rawActiveIndex >= 0 ? null : lyricGapState(time);
  const nextIndex = gap?.next ? lines.findIndex((line) => line.id === gap.next.id) : -1;
  const previousIndex = gap?.previous ? lines.findIndex((line) => line.id === gap.previous.id) : -1;
  const upcomingIndex = lines.findIndex((line) => time < line.end);
  const centerIndex = rawActiveIndex >= 0
    ? rawActiveIndex
    : Math.max(0, nextIndex >= 0 ? nextIndex : previousIndex >= 0 ? previousIndex : upcomingIndex);
  const pairStart = Math.max(0, centerIndex - (centerIndex % 2));
  const itemIndexes = state.captureMultilingual ? [centerIndex] : [pairStart, pairStart + 1];
  const idle = gap ? `
    <div class="carousel-idle" aria-live="polite">
      <span>${escapeHtml(gap.label)}</span>
      <strong>${escapeHtml(gap.detail || "")}</strong>
    </div>
  ` : "";
  const items = itemIndexes
    .filter((index) => index >= 0 && index < lines.length)
    .map((index) => {
      const active = rawActiveIndex >= 0 && index === rawActiveIndex;
      return `
        <div class="carousel-line ${active ? "active" : ""}" data-line-id="${escapeHtml(lines[index].id)}">
          <span>${formatTime(lines[index].start)}</span>
          <div class="carousel-translations">
            ${tracks.map((track) => {
              const line = lineForTrack(track, lines[index].id);
              return `
                <section class="carousel-track" lang="${escapeHtml(track.language.code)}" data-track-code="${escapeHtml(track.language.code)}">
                  <label>${escapeHtml(languageName(track))}</label>
                  ${renderTrackLine(track, line)}
                </section>
              `;
            }).join("")}
          </div>
        </div>
      `;
    }).join("");
  $("lyric-carousel").innerHTML = idle + items;
}

function renderFullLyrics(activeLine = null) {
  const lines = timingLines();
  if (!lines.length) {
    $("full-lyrics").innerHTML = "";
    return;
  }
  let lyricNumber = 0;
  $("full-lyrics").innerHTML = fullLyricDisplayRows(lines).map((row) => {
    if (row.type === "instrumental") {
      return `
        <article class="full-row instrumental-row" data-line-id="${escapeHtml(row.id)}">
          <div class="line-index">♪<span>${formatTime(row.start)}-${formatTime(row.end)}</span></div>
          <div class="language-lines">
            <section>
              <label>Instrumental</label>
              <div class="plain-line">${escapeHtml(row.label)} <span>${escapeHtml(row.detail || "")}</span></div>
            </section>
          </div>
        </article>
      `;
    }
    const line = row.line;
    lyricNumber += 1;
    return `
      <article class="full-row ${line.id === activeLine?.id ? "active" : ""}" data-line-id="${escapeHtml(line.id)}">
        <div class="line-index">${String(lyricNumber).padStart(2, "0")}<span>${formatTime(lineStartForDisplay(line))}</span></div>
        <div class="language-lines">
          ${state.tracks.map((track) => {
            const trackLine = lineForTrack(track, line.id);
            return `
              <section data-track-code="${escapeHtml(track.language.code)}">
                <label>${escapeHtml(track.language.nativeLabel || track.language.code)}</label>
                ${renderTrackLine(track, trackLine, { compact: true })}
              </section>
            `;
          }).join("")}
        </div>
      </article>
    `;
  }).join("");
}

function updateTokenHighlights(time, activeLine = activeLineAt(time)) {
  const activeLineId = activeLine?.id || "";
  document.querySelectorAll("[data-token-start]").forEach((node) => {
    const start = Number(node.dataset.tokenStart);
    const end = Number(node.dataset.tokenEnd);
    const lineId = node.closest("[data-line-id]")?.dataset.lineId || "";
    node.classList.toggle("active", Boolean(activeLineId && lineId === activeLineId && time >= start && time < end));
  });
}

function updateSync() {
  if (!state.manifest) return;
  const media = state.mediaElement;
  const time = Number.isFinite(state.captureTime) ? state.captureTime : (media?.currentTime || 0);
  const duration = media?.duration || state.manifest.duration || 1;
  const activeLine = activeLineAt(time);
  const activeChord = activeChordAt(time);
  const gap = activeLine ? null : lyricGapState(time);
  const activeAsset = activePlayableAsset();
  const track = activeTimingTrack() || state.trackByCode.get(activeAsset?.languageCode) || selectedLyricTracks()[0] || state.tracks[0] || null;
  const trackLine = lineForTrack(track, activeLine?.id);
  const progress = Math.min(100, Math.max(0, (time / duration) * 100));

  $("current-time").textContent = formatTime(time);
  $("duration").textContent = formatTime(duration);
  $("seek").value = String(Math.round((time / duration) * 1000));
  $("progress-fill").style.width = `${progress}%`;
  $("now-chord").textContent = activeChord?.name || "--";
  $("now-degree").textContent = activeChord?.degree || "";
  $("stage-line").textContent = trackLine?.singableText || trackLine?.text || gap?.label || "";
  $("current-lyric-label").textContent = selectedLyricSummary();
  const introStart = firstVocalStart();
  $("skip-intro").hidden = !state.mediaElement || introStart <= 0.25;
  renderCarousel(activeLine);
  renderFullLyrics(activeLine);
  renderChords(activeChord);
  updateTokenHighlights(time, activeLine);
}

window.funPlayerSetTime = function funPlayerSetTime(time) {
  const media = state.mediaElement || audio || video;
  const nextTime = Math.max(0, Number(time) || 0);
  state.captureTime = nextTime;
  if (media) {
    try {
      media.currentTime = nextTime;
    } catch {
      // Headless Chrome cannot always seek MP3 files through a local server.
      // The capture timestamp still drives the rendered UI; FFmpeg muxes audio.
    }
  }
  updateSync();
  return nextTime;
};

window.funPlayerUpdateSync = updateSync;

function initAudioGraph() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("audioGraph") !== "1") return;
  const media = state.mediaElement;
  if (!media || state.sourceElement === media) return;
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) return;
  try {
    if (!state.audioContext) state.audioContext = new AudioContext();
    if (state.source) state.source.disconnect();
    state.analyser = state.audioContext.createAnalyser();
    state.analyser.fftSize = 128;
    state.frequencyData = new Uint8Array(state.analyser.frequencyBinCount);
    state.source = state.sourceNodes.get(media);
    if (!state.source) {
      state.source = state.audioContext.createMediaElementSource(media);
      state.sourceNodes.set(media, state.source);
    }
    state.source.connect(state.analyser);
    state.analyser.connect(state.audioContext.destination);
    state.sourceElement = media;
  } catch (error) {
    console.warn("Audio visualizer unavailable; continuing normal media playback.", error);
    state.analyser = null;
    state.frequencyData = null;
    state.sourceElement = null;
  }
}

function drawVisualizer() {
  const width = Math.max(1, canvas.clientWidth * window.devicePixelRatio);
  const height = Math.max(1, canvas.clientHeight * window.devicePixelRatio);
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  ctx.clearRect(0, 0, width, height);
  const bars = state.frequencyData?.length || 48;
  if (state.analyser && state.frequencyData) state.analyser.getByteFrequencyData(state.frequencyData);
  for (let i = 0; i < bars; i += 1) {
    const value = state.frequencyData ? state.frequencyData[i] / 255 : (Math.sin(Date.now() / 700 + i * 0.7) + 1) / 2;
    const barWidth = width / bars * 0.56;
    const x = i * (width / bars) + (width / bars - barWidth) / 2;
    const barHeight = Math.max(10, value * height * 0.42);
    ctx.fillStyle = `rgba(55, 132, 122, ${0.16 + value * 0.36})`;
    ctx.fillRect(x, height - barHeight - 18, barWidth, barHeight);
  }
  requestAnimationFrame(drawVisualizer);
}

function stopPlaybackSync({ render = true } = {}) {
  if (state.playbackSyncFrame) {
    cancelAnimationFrame(state.playbackSyncFrame);
    state.playbackSyncFrame = 0;
  }
  if (render) updateSync();
}

function startPlaybackSync() {
  if (state.playbackSyncFrame) return;
  const tick = () => {
    const media = state.mediaElement;
    if (!media || media.paused || media.ended) {
      state.playbackSyncFrame = 0;
      updateSync();
      updateMediaSessionPosition();
      return;
    }
    updateSync();
    state.playbackSyncFrame = requestAnimationFrame(tick);
  };
  state.playbackSyncFrame = requestAnimationFrame(tick);
}

function mediaListeners(element) {
  element.addEventListener("play", () => {
    $("play-symbol").textContent = "❚❚";
    startPlaybackSync();
    updateMediaSessionPlaybackState();
  });
  element.addEventListener("pause", () => {
    $("play-symbol").textContent = "▶";
    stopPlaybackSync();
    updateMediaSessionPlaybackState();
  });
  element.addEventListener("timeupdate", () => {
    updateSync();
    updateMediaSessionPosition();
  });
  element.addEventListener("loadedmetadata", () => {
    updateSync();
    updateMediaSession();
  });
  element.addEventListener("loadedmetadata", () => {
    if (state.skipIntroOnLoad) applySkipIntro();
  });
  element.addEventListener("durationchange", updateMediaSessionPosition);
  element.addEventListener("ratechange", updateMediaSessionPosition);
  element.addEventListener("seeked", updateMediaSessionPosition);
  element.addEventListener("ended", () => {
    stopPlaybackSync({ render: false });
    handleMediaEnded();
  });
}

function bindEvents() {
  $("play").addEventListener("click", async () => {
    state.captureTime = null;
    const media = state.mediaElement;
    if (!media) return;
    if (media.paused) await playCurrentMedia();
    else pauseCurrentMedia();
  });
  $("seek").addEventListener("input", () => {
    const media = state.mediaElement;
    if (!media) return;
    state.captureTime = null;
    const duration = media.duration || state.manifest.duration || 1;
    media.currentTime = Number($("seek").value) / 1000 * duration;
  });
  $("skip-intro").addEventListener("click", () => {
    applySkipIntro({ force: true });
    playCurrentMedia();
  });
  $("playback-mode").addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target : null;
    const button = target?.closest("[data-playback-mode]");
    if (!button) return;
    setPlaybackMode(button.dataset.playbackMode, { user: true });
  });
  mediaListeners(audio);
  mediaListeners(video);
  $("library-toggle").addEventListener("click", () => setLibraryOpen(!state.libraryOpen));
  $("library-peek").addEventListener("click", () => setLibraryOpen(true));
  $("library-close").addEventListener("click", () => setLibraryOpen(false));
  $("library-backdrop").addEventListener("click", () => setLibraryOpen(false));
  $("search-toggle").addEventListener("click", () => setSearchOpen(true));
  $("advanced-toggle").addEventListener("click", () => setAdvancedMode(!state.advancedMode));
  document.querySelectorAll("[data-kind-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      state.kindFilter = button.dataset.kindFilter;
      document.querySelectorAll("[data-kind-filter]").forEach((node) => node.classList.toggle("active", node === button));
      renderLibrary();
    });
  });
  $("catalog-search").addEventListener("input", () => {
    state.searchQuery = $("catalog-search").value;
    setLibraryOpen(true);
    renderLibrary();
  });
  $("vocal-language-select").addEventListener("change", () => {
    const assets = playableAssets(state.manifest);
    const asset = assets.find((item) => item.id === $("vocal-language-select").value);
    if (asset) setMediaSource(asset, true);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      setLibraryOpen(false);
      setSearchOpen(false);
    }
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      setSearchOpen(true);
    }
  });
  document.addEventListener("visibilitychange", updateMediaSessionPlaybackState);
}

async function loadJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to load ${url}: ${response.status}`);
  return response.json();
}

async function loadTextTracks(trackInfos = []) {
  return Promise.all(trackInfos.map(async (trackInfo) => {
    const url = resolveManifestPath(trackInfo.path);
    const track = await loadJson(url);
    track.__url = url;
    track.__trackInfo = trackInfo;
    return track;
  }));
}

async function loadMediaItem(item, updateHash = false) {
  if (!item) throw new Error("No media item in catalog.");
  if (state.mediaElement) state.mediaElement.pause();
  externalPlayer.src = "about:blank";
  state.activeMediaId = item.id;
  state.manifestUrl = resolveSitePath(item.manifest);
  state.manifest = await loadJson(state.manifestUrl);
  state.didApplySkipIntro = false;
  state.renderedChordKey = "";
  if (!state.userPlaybackMode) setPlaybackMode(defaultPlaybackModeForManifest(state.manifest));
  else renderPlaybackMode();
  state.defaultTracks = await loadTextTracks(state.manifest.textTracks || []);
  state.lyricSets = await Promise.all((state.manifest.lyricSets || []).map(async (set) => ({
    ...set,
    tracks: await loadTextTracks(set.textTracks || set.tracks || [])
  })));
  state.tracks = [];
  state.trackByCode = new Map();
  state.activeLyricSetId = "";
  state.selectedLyricLangs = new Set();

  const musical = state.manifest.musical || {};
  $("kind-label").textContent = labelKind(state.manifest.kind);
  $("media-title").textContent = state.manifest.title;
  $("media-artist").textContent = state.manifest.artist ? `by ${state.manifest.artist}` : "";
  $("media-subtitle").textContent = "";
  $("media-caption").textContent = state.manifest.caption || labelKind(state.manifest.kind);
  $("key-label").textContent = musical.key || "No key";
  $("bpm-label").textContent = musical.bpm ? `${Math.round(Number(musical.bpm))} BPM` : "No BPM";
  updateShareMetadata(state.manifest);
  const cover = coverUrl(state.manifest);
  coverArt.src = cover ? resolveSitePath(cover) : "";
  coverArt.alt = state.manifest.assets?.cover?.label || `${state.manifest.title} cover`;
  coverThumb.src = coverArt.src;
  coverThumb.alt = coverArt.alt;

  renderLibrary();
  const assets = playableAssets(state.manifest);
  const selectedAsset = assets.find((asset) => asset.id === state.requestedAssetId) || assets[0];
  if (!selectedAsset) throw new Error("No playable media asset in manifest.");
  setMediaSource(selectedAsset);
  updateMediaSession();
  updateSync();
  if (updateHash) history.replaceState(null, "", `#${encodeURIComponent(item.id)}`);
}

async function boot() {
  const params = new URLSearchParams(window.location.search);
  state.captureMode = params.get("capture") === "1" || params.get("record") === "1";
  state.skipIntroOnLoad = params.get("skipIntro") === "1" || params.get("skip") === "vocal";
  state.requestedAssetId = params.get("asset") || "";
  try {
    state.advancedMode = params.get("advanced") === "1" || (!state.captureMode && localStorage.getItem("funAdvancedMode") === "1");
  } catch {
    state.advancedMode = params.get("advanced") === "1";
  }
  const captureFullLyrics = state.captureMode && params.get("fullLyrics") === "1";
  const capturePortrait = state.captureMode && params.get("portrait") === "1";
  const captureGuitarFocus = state.captureMode && params.get("guitarFocus") === "1";
  state.captureMultilingual = state.captureMode && params.get("multiLyrics") === "1";
  document.body.classList.toggle("capture-mode", state.captureMode);
  document.body.classList.toggle("capture-full-lyrics", captureFullLyrics);
  document.body.classList.toggle("capture-portrait", capturePortrait);
  document.body.classList.toggle("capture-guitar-focus", captureGuitarFocus);
  document.body.classList.toggle("capture-multilingual", state.captureMultilingual);
  document.body.classList.toggle("capture-ktv", capturePortrait && !captureFullLyrics && !captureGuitarFocus);
  bindEvents();
  setAdvancedMode(state.advancedMode, { persist: false });
  state.catalog = await loadJson("data/catalog.json");
  startLibraryPeekLoop();
  const requestedId = params.get("media") || params.get("id") || window.location.hash.replace(/^#/, "");
  const hashId = decodeURIComponent(requestedId);
  const item = state.catalog.items.find((entry) => entry.id === hashId)
    || state.catalog.items.find((entry) => entry.id === state.catalog.defaultMedia)
    || state.catalog.items[0];
  await loadMediaItem(item);
  drawVisualizer();
}

boot().catch((error) => {
  document.body.innerHTML = `<pre style="padding:24px;color:#111827">${escapeHtml(error.stack || error.message)}</pre>`;
});
