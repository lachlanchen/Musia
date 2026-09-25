export function activeInterval(items, time) {
  return items.find(item => time >= item.start && time < item.end) ?? null;
}

export function activeBeat(beats, time) {
  let index = -1;
  for (let i = 0; i < beats.length && beats[i].time <= time; i++) index = i;
  return index;
}

export function tapOffset(beats, time, rate = 1) {
  if (!beats.length || !Number.isFinite(time) || !Number.isFinite(rate) || rate <= 0) return null;
  const closest = beats.reduce((best, beat) => Math.abs(beat.time - time) < Math.abs(best.time - time) ? beat : best);
  return (time - closest.time) * 1000 / rate;
}

export function tapSummary(offsets) {
  if (offsets.length < 4) return null;
  const sorted = [...offsets].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  const bias = sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
  const spread = Math.sqrt(offsets.reduce((sum, value) => sum + (value - bias) ** 2, 0) / offsets.length);
  return { bias: Math.round(bias), spread: Math.round(spread), count: offsets.length };
}

export function validLoop(start, end, duration) {
  return Number.isFinite(start) && Number.isFinite(end) && Number.isFinite(duration) && start >= 0 && end > start + .25 && end <= duration;
}

export function practiceHistory(value) {
  if (!Array.isArray(value)) return [];
  return value.filter(e => e && typeof e.title === 'string' && typeof e.songId === 'string'
    && Number.isFinite(Date.parse(e.date)) && Number.isFinite(e.seconds) && e.seconds >= 0
    && Number.isFinite(e.rate) && e.rate >= .25 && e.rate <= 2
    && ['listen','tap','play'].includes(e.mode)).slice(0,500);
}

export function clock(seconds) {
  const safe = Math.max(0, Number.isFinite(seconds) ? seconds : 0);
  return `${Math.floor(safe / 60)}:${String(Math.floor(safe % 60)).padStart(2, '0')}`;
}

export function readingText(token) {
  return String(token.reading ?? token.furigana ?? token.pinyin ?? '');
}

export function lyricParts(line) {
  const parts = [];
  let cursor = 0;
  for (const token of line.tokens ?? []) {
    const start = line.text.indexOf(token.text, cursor);
    if (!token.text || start < 0) return [{text:line.text}];
    if (start > cursor) parts.push({text:line.text.slice(cursor,start)});
    parts.push({text:token.text,token});
    cursor = start + token.text.length;
  }
  if (cursor < line.text.length) parts.push({text:line.text.slice(cursor)});
  return parts;
}

export function loadLocal(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}

export function saveLocal(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); return true; } catch { return false; }
}
