const state = {
  catalog: null,
  manifest: null,
  manifestUrl: "",
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
  frequencyData: null
};

const $ = (id) => document.getElementById(id);
const audio = $("audio");
const video = $("video");
const externalPlayer = $("external-player");
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
  if (token.pinyin) {
    return `<span class="text-token ruby-token"${attrs}><ruby>${escapeHtml(token.text)}<rt>${escapeHtml(pinyinTone(token.pinyin))}</rt></ruby></span>`;
  }
  if (token.reading) {
    return `<span class="text-token ruby-token"${attrs}><ruby>${escapeHtml(token.text)}<rt>${escapeHtml(token.reading)}</rt></ruby></span>`;
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
  return state.manifest?.musical?.chords || [];
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
  if (tracks.length === state.tracks.length) return "All languages";
  return tracks.map(languageName).join(" · ");
}

function lineForTrack(track, lineId) {
  return track?.lines?.find((line) => line.id === lineId) || null;
}

function activeLineAt(time) {
  const lines = timingLines();
  return lines.find((line) => time >= line.start && time < line.end)
    || [...lines].reverse().find((line) => time >= line.end)
    || null;
}

function activeChordAt(time) {
  const list = chords();
  return list.find((chord) => time >= chord.start && time < chord.end)
    || [...list].reverse().find((chord) => time >= chord.end)
    || null;
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

function setLibraryOpen(open) {
  state.libraryOpen = Boolean(open);
  $("library-panel").hidden = !state.libraryOpen;
  $("library-backdrop").hidden = !state.libraryOpen;
  $("library-toggle").setAttribute("aria-expanded", state.libraryOpen ? "true" : "false");
}

function setSearchOpen(open) {
  state.searchOpen = Boolean(open);
  $("header-search").hidden = !state.searchOpen;
  $("search-toggle").setAttribute("aria-expanded", state.searchOpen ? "true" : "false");
  if (state.searchOpen) {
    $("catalog-search").focus();
    setLibraryOpen(true);
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

function setMediaSource(asset, keepTime = false) {
  const previous = state.mediaElement;
  const previousTime = previous?.currentTime || 0;
  const wasPlaying = previous && !previous.paused;
  if (previous) previous.pause();
  state.activeAssetId = asset.id;

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
    renderAssetSwitcher();
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
  state.mediaElement.src = resolveSitePath(asset.src);
  if (keepTime) state.mediaElement.currentTime = Math.min(previousTime, (state.manifest.duration || previousTime) - 0.1);
  if (wasPlaying) state.mediaElement.play();
  renderAssetSwitcher();
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

function renderAssetSwitcher() {
  const assets = playableAssets(state.manifest);
  $("asset-switcher").innerHTML = assets.map((asset) => `
    <button class="${asset.id === state.activeAssetId ? "active" : ""}" type="button" data-asset-id="${escapeHtml(asset.id)}">
      <span>${escapeHtml(asset.roleLabel || asset.role || asset.type || "audio")}</span>
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

function renderLanguageButtons() {
  if (!state.tracks.length) {
    $("language-tabs").innerHTML = `<span class="soft-note">No lyrics</span>`;
    return;
  }
  const allSelected = state.tracks.every((track) => state.selectedLyricLangs.has(track.language.code));
  $("language-tabs").innerHTML = `
    <button class="${allSelected ? "active" : ""}" type="button" data-lang-all="true" aria-pressed="${allSelected ? "true" : "false"}">All</button>
    ${state.tracks.map((track) => {
      const active = state.selectedLyricLangs.has(track.language.code);
      return `
    <button class="${active ? "active" : ""}" type="button" data-lang="${escapeHtml(track.language.code)}" aria-pressed="${active ? "true" : "false"}">
      ${escapeHtml(track.language.nativeLabel || track.language.label || track.language.code)}
    </button>
      `;
    }).join("")}
  `;
  document.querySelectorAll("[data-lang-all]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedLyricLangs = new Set(state.tracks.map((track) => track.language.code));
      renderLanguageButtons();
      updateSync();
    });
  });
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
  $("chord-row").hidden = list.length === 0;
  $("chord-row").innerHTML = list.map((chord, index) => `
    <button class="chord-pill ${chord === activeChord ? "active" : ""}" type="button" data-chord-index="${index}">
      <strong>${escapeHtml(chord.name)}</strong><span>${escapeHtml(chord.degree || "")}</span>
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

function renderCarousel(activeLine) {
  const tracks = selectedLyricTracks();
  const lines = timingLines();
  if (!tracks.length || !lines.length) {
    $("lyric-carousel").innerHTML = `<div class="empty-state"><h2>${escapeHtml(state.manifest.title)}</h2><p>${escapeHtml(state.manifest.description || "No timed lyrics are attached yet.")}</p></div>`;
    return;
  }
  const rawActiveIndex = activeLine ? lines.findIndex((line) => line.id === activeLine.id) : -1;
  const time = state.mediaElement?.currentTime || 0;
  const upcomingIndex = lines.findIndex((line) => time < line.end);
  const centerIndex = rawActiveIndex >= 0 ? rawActiveIndex : Math.max(0, upcomingIndex);
  const items = [centerIndex - 1, centerIndex, centerIndex + 1]
    .filter((index) => index >= 0 && index < lines.length)
    .map((index) => {
      const active = rawActiveIndex >= 0 && index === rawActiveIndex;
      return `
        <div class="carousel-line ${active ? "active" : ""}">
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
  $("lyric-carousel").innerHTML = items;
}

function renderFullLyrics(activeLine = null) {
  const lines = manifestLines();
  if (!lines.length) {
    $("full-lyrics").innerHTML = "";
    return;
  }
  $("full-lyrics").innerHTML = lines.map((line, index) => `
    <article class="full-row ${line.id === activeLine?.id ? "active" : ""}">
      <div class="line-index">${String(index + 1).padStart(2, "0")}<span>${formatTime(lineStartForDisplay(line))}</span></div>
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
  `).join("");
}

function updateTokenHighlights(time) {
  const activeCode = activePlayableAsset()?.languageCode || "";
  document.querySelectorAll("[data-token-start]").forEach((node) => {
    const start = Number(node.dataset.tokenStart);
    const end = Number(node.dataset.tokenEnd);
    const trackCode = node.closest("[data-track-code]")?.dataset.trackCode || "";
    node.classList.toggle("active", Boolean(activeCode && trackCode === activeCode && time >= start && time < end));
  });
}

function updateSync() {
  if (!state.manifest) return;
  const media = state.mediaElement;
  const time = media?.currentTime || 0;
  const duration = media?.duration || state.manifest.duration || 1;
  const activeLine = activeLineAt(time);
  const activeChord = activeChordAt(time);
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
  $("stage-line").textContent = trackLine?.singableText || trackLine?.text || state.manifest.caption || "";
  $("current-lyric-label").textContent = selectedLyricSummary();
  renderCarousel(activeLine);
  renderFullLyrics(activeLine);
  renderChords(activeChord);
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
  $("library-toggle").addEventListener("click", () => setLibraryOpen(!state.libraryOpen));
  $("library-close").addEventListener("click", () => setLibraryOpen(false));
  $("library-backdrop").addEventListener("click", () => setLibraryOpen(false));
  $("search-toggle").addEventListener("click", () => setSearchOpen(!state.searchOpen));
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
}

async function loadJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to load ${url}: ${response.status}`);
  return response.json();
}

async function loadMediaItem(item, updateHash = false) {
  if (!item) throw new Error("No media item in catalog.");
  if (state.mediaElement) state.mediaElement.pause();
  externalPlayer.src = "about:blank";
  state.activeMediaId = item.id;
  state.manifestUrl = resolveSitePath(item.manifest);
  state.manifest = await loadJson(state.manifestUrl);
  state.tracks = await Promise.all((state.manifest.textTracks || []).map(async (trackInfo) => {
    const url = resolveManifestPath(trackInfo.path);
    const track = await loadJson(url);
    track.__url = url;
    return track;
  }));
  state.trackByCode = new Map(state.tracks.map((track) => [track.language.code, track]));
  state.selectedLyricLangs = new Set(state.tracks.map((track) => track.language.code));

  const musical = state.manifest.musical || {};
  $("kind-label").textContent = labelKind(state.manifest.kind);
  $("media-title").textContent = state.manifest.title;
  $("media-subtitle").textContent = state.manifest.subtitle || state.manifest.description || "";
  $("media-caption").textContent = state.manifest.caption || labelKind(state.manifest.kind);
  $("key-label").textContent = musical.key || "No key";
  $("bpm-label").textContent = musical.bpm ? `${musical.bpm} BPM` : "No BPM";
  updateShareMetadata(state.manifest);
  const cover = coverUrl(state.manifest);
  coverArt.src = cover ? resolveSitePath(cover) : "";
  coverArt.alt = state.manifest.assets?.cover?.label || `${state.manifest.title} cover`;
  coverThumb.src = coverArt.src;
  coverThumb.alt = coverArt.alt;

  renderLibrary();
  renderLanguageButtons();
  const firstAsset = playableAssets(state.manifest)[0];
  if (!firstAsset) throw new Error("No playable media asset in manifest.");
  setMediaSource(firstAsset);
  updateSync();
  if (updateHash) history.replaceState(null, "", `#${encodeURIComponent(item.id)}`);
}

async function boot() {
  bindEvents();
  state.catalog = await loadJson("data/catalog.json");
  const hashId = decodeURIComponent(window.location.hash.replace(/^#/, ""));
  const item = state.catalog.items.find((entry) => entry.id === hashId)
    || state.catalog.items.find((entry) => entry.id === state.catalog.defaultMedia)
    || state.catalog.items[0];
  await loadMediaItem(item);
  drawVisualizer();
}

boot().catch((error) => {
  document.body.innerHTML = `<pre style="padding:24px;color:#111827">${escapeHtml(error.stack || error.message)}</pre>`;
});
