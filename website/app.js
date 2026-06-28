const state = {
  catalog: null,
  manifest: null,
  manifestUrl: "",
  tracks: [],
  trackByCode: new Map(),
  view: "all",
  activeAssetId: "",
  mediaElement: null,
  sourceNodes: new Map(),
  audioReady: false,
  audioContext: null,
  analyser: null,
  source: null,
  sourceElement: null,
  frequencyData: null
};

const $ = (id) => document.getElementById(id);
const audio = $("audio");
const video = $("video");
const coverArt = $("cover-art");
const coverThumb = $("cover-thumb");
const canvas = $("visualizer");
const ctx = canvas.getContext("2d");

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
  const mins = Math.floor(safe / 60);
  const secs = Math.floor(safe % 60).toString().padStart(2, "0");
  return `${mins}:${secs}`;
}

function labelKind(kind) {
  return {
    song: "Music",
    mv: "MV",
    "short-film": "Short Film",
    video: "Video"
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

function renderRubyToken(token) {
  if (token.pinyin) {
    const rt = `${tokenLabel(token)}${pinyinTone(token.pinyin)}`;
    return `<ruby>${escapeHtml(token.text)}<rt>${escapeHtml(rt)}</rt></ruby>`;
  }
  if (token.reading) {
    return `<ruby>${escapeHtml(token.text)}<rt>${escapeHtml(token.reading)}</rt></ruby>`;
  }
  return escapeHtml(token.text);
}

function renderTrackLine(track, line) {
  const tokens = Array.isArray(line.tokens) ? line.tokens : [];
  const timedTokens = tokens.some((token) => Number.isFinite(token.start) && Number.isFinite(token.end));
  const rubyTokens = tokens.some((token) => token.pinyin || token.reading);

  if (rubyTokens) {
    return `<p class="ruby-line">${tokens.map(renderRubyToken).join("")}</p>`;
  }

  if (timedTokens) {
    return `<p class="token-line">${tokens.map((token) => `
      <span class="text-token" data-token-start="${token.start}" data-token-end="${token.end}">
        ${escapeHtml(token.text)}
      </span>
    `).join("")}</p>`;
  }

  return `<p>${escapeHtml(line.text)}</p>`;
}

function manifestLines() {
  return state.manifest?.timeline?.lines || [];
}

function chords() {
  return state.manifest?.musical?.chords || [];
}

function activeLineAt(time) {
  const lines = manifestLines();
  return lines.find((line) => time >= line.start && time < line.end) || lines.at(-1) || null;
}

function activeChordAt(time) {
  const list = chords();
  return list.find((chord) => time >= chord.start && time < chord.end) || list.at(-1) || null;
}

function lineForTrack(track, lineId) {
  return track.lines.find((line) => line.id === lineId);
}

function playableAssets(manifest) {
  const assets = manifest.assets || {};
  const result = [];
  if (assets.primaryAudio?.src) {
    result.push({ id: "primary", label: assets.primaryAudio.label || "Mix", type: "audio", src: assets.primaryAudio.src });
  }
  if (assets.primaryVideo?.src) {
    result.push({ id: "video", label: assets.primaryVideo.label || "Video", type: "video", src: assets.primaryVideo.src });
  }
  for (const item of assets.alternateAudio || []) {
    if (item.src) result.push({ id: item.id || item.label || item.src, label: item.label || item.id || "Audio", type: "audio", src: item.src });
  }
  for (const [id, item] of Object.entries(assets.stems || {})) {
    if (item?.src) result.push({ id, label: item.label || id, type: "audio", src: item.src });
  }
  return result;
}

function setMeta(selector, value, attr = "content") {
  const node = document.querySelector(selector);
  if (node && value) node.setAttribute(attr, value);
}

function shareImageUrl(manifest) {
  return manifest.share?.image || manifest.assets?.cover?.src || manifest.assets?.poster?.src || "";
}

function coverUrl(manifest) {
  return manifest.assets?.cover?.src || manifest.assets?.poster?.src || manifest.share?.image || "";
}

function updateShareMetadata(manifest) {
  const title = manifest.share?.title || manifest.title;
  const description = manifest.share?.description || manifest.description || manifest.subtitle || "";
  const image = shareImageUrl(manifest);
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

function setMediaSource(asset, keepTime = false) {
  const previous = state.mediaElement;
  const previousTime = previous?.currentTime || 0;
  const wasPlaying = previous && !previous.paused;
  if (previous) previous.pause();

  state.mediaElement = asset.type === "video" ? video : audio;
  audio.hidden = asset.type === "video";
  video.hidden = asset.type !== "video";
  canvas.classList.toggle("dimmed", asset.type === "video");
  coverArt.classList.toggle("dimmed", asset.type === "video");

  state.mediaElement.src = resolveSitePath(asset.src);
  state.activeAssetId = asset.id;
  if (keepTime) state.mediaElement.currentTime = Math.min(previousTime, (state.manifest.duration || previousTime) - 0.1);
  if (wasPlaying) state.mediaElement.play();
  renderAssetSwitcher();
  updateSync();
}

function renderLibrary() {
  const items = state.catalog.items || [];
  $("media-library").innerHTML = items.map((item) => `
    <button class="media-tile active" type="button" data-media-id="${escapeHtml(item.id)}">
      <span>${escapeHtml(labelKind(item.kind))}</span>
      <strong>${escapeHtml(item.title)}</strong>
      <small>${escapeHtml((item.languages || []).join(" / "))}</small>
    </button>
  `).join("");
}

function renderAssetSwitcher() {
  const assets = playableAssets(state.manifest);
  $("asset-switcher").innerHTML = assets.map((asset) => `
    <button class="${asset.id === state.activeAssetId ? "active" : ""}" type="button" data-asset-id="${escapeHtml(asset.id)}">
      ${escapeHtml(asset.label)}
    </button>
  `).join("");
  document.querySelectorAll("[data-asset-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const asset = assets.find((item) => item.id === button.dataset.assetId);
      if (asset) setMediaSource(asset, true);
    });
  });
}

function renderTabs() {
  const buttons = [
    `<button class="active" type="button" data-view="all">All</button>`,
    ...state.tracks.map((track) => `
      <button type="button" data-view="${escapeHtml(track.language.code)}">
        ${escapeHtml(track.language.nativeLabel || track.language.label || track.language.code)}
      </button>
    `)
  ];
  $("track-tabs").innerHTML = buttons.join("");
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.view = button.dataset.view;
      applyViewFilter();
    });
  });
}

function renderChords() {
  const list = chords();
  $("chord-strip").hidden = list.length === 0;
  $("chord-strip").innerHTML = list.map((chord, index) => `
    <button class="chord" type="button" data-chord-index="${index}">
      <strong>${escapeHtml(chord.name)}</strong>
      <small>${escapeHtml(chord.degree || "")}</small>
    </button>
  `).join("");
  document.querySelectorAll("[data-chord-index]").forEach((button) => {
    button.addEventListener("click", () => {
      const chord = list[Number(button.dataset.chordIndex)];
      if (!chord || !state.mediaElement) return;
      state.mediaElement.currentTime = chord.start;
      state.mediaElement.play();
    });
  });
}

function renderSourceWords(line) {
  const words = Array.isArray(line.words) ? line.words : [];
  if (!words.length) return escapeHtml(line.sourceText || "");
  return words.map((word) => {
    const joiner = word.joiner ?? " ";
    return `<span class="word" data-word-start="${word.start}" data-word-end="${word.end}">${escapeHtml(word.text)}</span>${escapeHtml(joiner)}`;
  }).join("");
}

function renderTextLines() {
  $("text-lines").innerHTML = manifestLines().map((line, index) => {
    const tracks = state.tracks.map((track) => {
      const trackLine = lineForTrack(track, line.id);
      if (!trackLine) return "";
      const label = track.language.nativeLabel || track.language.label || track.language.code;
      const role = trackLine.role || "text";
      return `
        <div class="translation" data-track-code="${escapeHtml(track.language.code)}">
          <span class="label">${escapeHtml(label)} / ${escapeHtml(role)}</span>
          ${renderTrackLine(track, trackLine)}
          ${trackLine.singableText ? `<p class="singable">${escapeHtml(trackLine.singableText)}</p>` : ""}
        </div>
      `;
    }).join("");
    return `
      <article class="lyric-line" data-line-index="${index}" style="--line-progress:0%">
        <div class="line-progress"></div>
        <div class="source">${renderSourceWords(line)}</div>
        <div class="translations">${tracks}</div>
      </article>
    `;
  }).join("");
  applyViewFilter();
}

function applyViewFilter() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === state.view);
  });
  document.querySelectorAll(".translation").forEach((node) => {
    node.hidden = state.view !== "all" && node.dataset.trackCode !== state.view;
  });
}

function renderFocusLine(line, chord) {
  if (!line) {
    $("active-line").innerHTML = `<span class="muted">No timeline loaded.</span>`;
    return;
  }
  const activeTracks = state.tracks.map((track) => {
    const trackLine = lineForTrack(track, line.id);
    if (!trackLine) return "";
    return `
      <div>
        <span class="label">${escapeHtml(track.language.nativeLabel || track.language.code)}</span>
        ${renderTrackLine(track, trackLine)}
      </div>
    `;
  }).join("");

  $("active-line").innerHTML = `
    <div>
      <span class="label">Canonical line</span>
      <div class="big">${escapeHtml(line.sourceText || "")}</div>
    </div>
    ${activeTracks}
    <div>
      <span class="label">Music</span>
      <p>${escapeHtml(chord?.name || "--")} ${chord?.degree ? `· ${escapeHtml(chord.degree)}` : ""}</p>
    </div>
  `;
}

function updateTokenHighlights(time) {
  document.querySelectorAll("[data-word-start]").forEach((node) => {
    const start = Number(node.dataset.wordStart);
    const end = Number(node.dataset.wordEnd);
    node.classList.toggle("active", time >= start && time < end);
  });
  document.querySelectorAll("[data-token-start]").forEach((node) => {
    const start = Number(node.dataset.tokenStart);
    const end = Number(node.dataset.tokenEnd);
    node.classList.toggle("active", time >= start && time < end);
  });
}

function updateSync() {
  if (!state.manifest || !state.mediaElement) return;
  const media = state.mediaElement;
  const time = media.currentTime || 0;
  const duration = media.duration || state.manifest.duration || 1;
  const line = activeLineAt(time);
  const chord = activeChordAt(time);
  const progress = Math.min(100, Math.max(0, (time / duration) * 100));
  $("current-time").textContent = formatTime(time);
  $("duration").textContent = formatTime(duration);
  $("seek").value = String(Math.round((time / duration) * 1000));
  $("progress-fill").style.width = `${progress}%`;
  $("now-chord").textContent = chord?.name || "--";
  $("now-degree").textContent = chord?.degree || "--";
  $("stage-line").textContent = line?.sourceText || "Playing";
  renderFocusLine(line, chord);

  document.querySelectorAll(".chord").forEach((node, index) => {
    node.classList.toggle("active", chords()[index] === chord);
  });

  document.querySelectorAll(".lyric-line").forEach((node, index) => {
    const item = manifestLines()[index];
    const isActive = item === line;
    node.classList.toggle("active", isActive);
    const span = Math.max(0.001, item.end - item.start);
    const lineProgress = isActive ? ((time - item.start) / span) * 100 : time >= item.end ? 100 : 0;
    node.style.setProperty("--line-progress", `${Math.min(100, Math.max(0, lineProgress))}%`);
    if (isActive && !node.dataset.seen) {
      node.dataset.seen = "1";
      node.scrollIntoView({ block: "center", behavior: "smooth" });
      window.setTimeout(() => { node.dataset.seen = ""; }, 600);
    }
  });
  updateTokenHighlights(time);
}

function initAudioGraph() {
  const media = state.mediaElement;
  if (!media || state.sourceElement === media) return;
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) return;
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
  state.audioReady = true;
}

function drawVisualizer() {
  const width = Math.max(1, canvas.clientWidth * window.devicePixelRatio);
  const height = Math.max(1, canvas.clientHeight * window.devicePixelRatio);
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  ctx.clearRect(0, 0, width, height);
  const grad = ctx.createLinearGradient(0, 0, width, height);
  grad.addColorStop(0, "rgba(82, 218, 205, .34)");
  grad.addColorStop(.45, "rgba(238, 196, 88, .2)");
  grad.addColorStop(1, "rgba(245, 116, 132, .18)");
  ctx.fillStyle = grad;

  const bars = state.frequencyData?.length || 56;
  if (state.analyser && state.frequencyData) state.analyser.getByteFrequencyData(state.frequencyData);
  for (let i = 0; i < bars; i += 1) {
    const fallback = (Math.sin(Date.now() / 680 + i * 0.7) + 1) / 2;
    const value = state.frequencyData ? state.frequencyData[i] / 255 : fallback;
    const barWidth = width / bars * 0.64;
    const x = i * (width / bars) + (width / bars - barWidth) / 2;
    const barHeight = Math.max(12, value * height * 0.56);
    const y = height - barHeight - 28 - Math.sin(i * 0.75) * 10;
    ctx.fillRect(x, y, barWidth, barHeight);
  }

  ctx.strokeStyle = "rgba(255,255,255,.18)";
  ctx.lineWidth = Math.max(1, window.devicePixelRatio);
  ctx.beginPath();
  for (let x = 0; x <= width; x += width / 20) {
    const y = height * 0.34 + Math.sin(x / width * Math.PI * 4 + Date.now() / 1200) * 20;
    if (x === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
  requestAnimationFrame(drawVisualizer);
}

function mediaListeners(element) {
  element.addEventListener("play", () => { $("play-symbol").textContent = "❚❚"; });
  element.addEventListener("pause", () => { $("play-symbol").textContent = "▶"; });
  element.addEventListener("timeupdate", updateSync);
  element.addEventListener("loadedmetadata", updateSync);
}

function bindEvents() {
  $("play").addEventListener("click", async () => {
    initAudioGraph();
    if (state.audioContext?.state === "suspended") await state.audioContext.resume();
    const media = state.mediaElement;
    if (!media) return;
    if (media.paused) await media.play();
    else media.pause();
  });
  $("seek").addEventListener("input", () => {
    const media = state.mediaElement;
    if (!media) return;
    const duration = media.duration || state.manifest.duration || 1;
    media.currentTime = Number($("seek").value) / 1000 * duration;
  });
  mediaListeners(audio);
  mediaListeners(video);
  document.querySelectorAll("[data-kind-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-kind-filter]").forEach((node) => node.classList.remove("active"));
      button.classList.add("active");
      const kind = button.dataset.kindFilter;
      document.querySelectorAll(".media-tile").forEach((tile) => {
        const item = state.catalog.items.find((entry) => entry.id === tile.dataset.mediaId);
        tile.hidden = kind !== "all" && item?.kind !== kind;
      });
    });
  });
}

function renderArtifacts() {
  const manifest = state.manifest;
  const assets = playableAssets(manifest);
  const artifactLinks = [
    ...assets.map((asset) => ({ label: asset.label, href: resolveSitePath(asset.src) })),
    ...(manifest.artifacts || []).map((item) => ({ label: item.label || item.id || item.href, href: resolveSitePath(item.href || item.src || "") })),
    ...state.tracks.map((track) => ({ label: `${track.language.nativeLabel || track.language.code} JSON`, href: track.__url }))
  ].filter((item) => item.href);
  $("artifact-list").innerHTML = artifactLinks.map((item) => `
    <li><a href="${escapeHtml(item.href)}">${escapeHtml(item.label)}</a></li>
  `).join("");
}

async function loadJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to load ${url}: ${response.status}`);
  return response.json();
}

async function loadDefaultMedia() {
  state.catalog = await loadJson("data/catalog.json");
  renderLibrary();
  const item = state.catalog.items.find((entry) => entry.id === state.catalog.defaultMedia) || state.catalog.items[0];
  if (!item) throw new Error("No media item in catalog.");

  state.manifestUrl = resolveSitePath(item.manifest);
  state.manifest = await loadJson(state.manifestUrl);
  state.tracks = await Promise.all((state.manifest.textTracks || []).map(async (trackInfo) => {
    const url = resolveManifestPath(trackInfo.path);
    const track = await loadJson(url);
    track.__url = url;
    return track;
  }));
  state.trackByCode = new Map(state.tracks.map((track) => [track.language.code, track]));

  const musical = state.manifest.musical || {};
  $("kind-label").textContent = labelKind(state.manifest.kind);
  $("media-title").textContent = state.manifest.title;
  $("media-subtitle").textContent = state.manifest.subtitle || state.manifest.description || "";
  $("media-caption").textContent = state.manifest.caption || labelKind(state.manifest.kind);
  $("key-label").textContent = musical.key || "No key";
  $("bpm-label").textContent = musical.bpm ? `${musical.bpm} BPM` : "No BPM";
  $("manifest-link").href = state.manifestUrl;
  $("command-box").textContent = state.manifest.createCommand || "musai website build";
  updateShareMetadata(state.manifest);
  const cover = coverUrl(state.manifest);
  coverArt.src = cover ? resolveSitePath(cover) : "";
  coverArt.alt = state.manifest.assets?.cover?.label || `${state.manifest.title} cover`;
  coverThumb.src = coverArt.src;
  coverThumb.alt = coverArt.alt;

  renderTabs();
  renderChords();
  renderTextLines();
  renderArtifacts();

  const firstAsset = playableAssets(state.manifest)[0];
  if (!firstAsset) throw new Error("No playable media asset in manifest.");
  setMediaSource(firstAsset);
  updateSync();
}

async function boot() {
  bindEvents();
  await loadDefaultMedia();
  drawVisualizer();
}

boot().catch((error) => {
  document.body.innerHTML = `<pre style="padding:24px;color:white">${escapeHtml(error.stack || error.message)}</pre>`;
});
