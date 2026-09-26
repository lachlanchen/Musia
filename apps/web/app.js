import { activeInterval, activeBeat, tapOffset, tapSummary, validLoop, clock, readingText, loadLocal, saveLocal, practiceHistory, lyricParts } from './core.js';
import { guitarShape } from './guitar-shapes.js';

const $ = id => document.getElementById(id);
const audio = $('audio');
const state = { library: [], song: null, asset: null, lessons: [], lesson: 0, mode: 'listen', loop: null, offsets: [], lastTapBeat: null, seconds: 0, history: practiceHistory(loadLocal('musia.practice.v1', [])), lastTime: performance.now(), lastLyric: null, lastChord: null, loadingId: 0 };
new ResizeObserver(entries => {
  document.documentElement.style.setProperty('--practice-footer-height', `${entries[0].target.getBoundingClientRect().height}px`);
}).observe(document.querySelector('.practice-footer'));
const icons = () => window.lucide?.createIcons();
function node(tag, text, className) { const e = document.createElement(tag); if (text !== undefined) e.textContent = text; if (className) e.className = className; return e; }
function notice(text) { $('notice').textContent = text; $('notice').hidden = !text; }
function view(name) {
  document.querySelectorAll('.view').forEach(e => e.hidden = e.id !== `${name}-view`);
  document.querySelectorAll('[data-view]').forEach(e => e.classList.toggle('selected', e.dataset.view === name));
  $('page-title').textContent = ({practice:'Practice', library:'Songbook', progress:'My progress', create:'Create'})[name];
  if (name === 'progress') renderHistory();
  if (name === 'library') renderLibrary();
  window.scrollTo({top:0, behavior:'instant'});
}
async function request(path) {
  const response = await fetch(path, { signal: AbortSignal.timeout(15000) });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
}
function renderLibrary() {
  const query = $('search').value.toLocaleLowerCase().trim();
  const list = state.library.filter(s => `${s.title} ${s.artist}`.toLocaleLowerCase().includes(query));
  $('song-count').textContent = `${list.length} tracks`;
  $('library').replaceChildren(...list.map(s => {
    const button = node('button', undefined, 'song-card');
    const image = node('img'); image.src = s.coverUrl; image.alt = ''; image.loading = 'lazy'; image.onerror = () => { image.onerror = null; image.src = '/assets/brand.png'; };
    button.append(image, node('h3', s.title), node('p', `${s.kind === 'exercise' ? 'Foundations' : s.artist} · ${clock(s.duration)}`));
    button.onclick = () => { selectSong(s.id); view('practice'); };
    return button;
  }));
  if (!list.length) $('library').append(node('p', 'No matching songs.', 'empty-message'));
}
async function selectSong(id) {
  const requestId = ++state.loadingId;
  audio.pause(); saveSession(false); state.asset = null; state.song = null; state.loop = null;
  $('play').disabled = true; $('floating-play').disabled = true; $('vocal').disabled = true;
  $('phrases').replaceChildren(); $('song-title').textContent = 'Loading…'; notice('');
  try {
    const song = await request(`/api/v1/songs/${encodeURIComponent(id)}`);
    if (requestId !== state.loadingId) return;
    state.song = song; $('song-title').textContent = song.title; $('artist').textContent = song.artist;
    $('cover').src = song.coverUrl; $('track-kind').textContent = id === 'first-pulse' ? 'FOUNDATIONS' : 'YOUR SONGBOOK';
    $('cover').onerror = () => { $('cover').onerror = null; $('cover').src = '/assets/brand.png'; };
    $('vocal').replaceChildren(...song.assets.map(a => { const o = node('option', a.label); o.value = a.id; return o; }));
    $('vocal').value = song.defaultAssetId;
    selectAsset(song.defaultAssetId); $('play').disabled = false; $('floating-play').disabled = false; $('vocal').disabled = false;
    history.replaceState(null, '', `?song=${encodeURIComponent(id)}`);
  } catch (error) { if (requestId === state.loadingId) { $('song-title').textContent = 'Music is unavailable'; notice(`${error.message}. Choose a track again to retry.`); } }
}
function selectAsset(id) {
  if (!state.song?.assets?.length) return;
  audio.pause(); saveSession(false);
  const asset = state.song.assets.find(a => a.id === id) ?? state.song.assets[0];
  if (!asset) { notice('No playable audio in this song.'); return; }
  state.asset = asset; state.loop = null; state.offsets = []; state.lastTapBeat = null; state.lastLyric = null; state.lastChord = null;
  $('loop').setAttribute('aria-pressed','false'); audio.src = asset.audioUrl; audio.load(); audio.preservesPitch = true; audio.playbackRate = Number($('speed').value)/100;
  $('duration').textContent = clock(asset.duration); $('seek').max = asset.duration;
  $('tempo-label').textContent = asset.bpm ? `${Math.round(asset.bpm)} BPM` : 'Tempo unavailable';
  const verified = asset.confidence?.beats === 'verified' && asset.confidence?.chords === 'verified';
  $('evidence-label').textContent = verified ? 'Reference exercise' : 'AI estimate · not a verified score';
  $('evidence-label').classList.toggle('verified', verified);
  $('vocal').parentElement.hidden = state.song.assets.length < 2;
  const reference = state.song.id === 'first-pulse';
  $('pulse-lane').classList.toggle('unmetered', !reference);
  $('pulse-lane').replaceChildren(...(reference ? [0,1,2,3] : [0]).map(i => { const el = node('div', undefined, 'beat'); el.append(node('span', reference ? String(i+1) : 'Pulse')); return el; }));
  $('phrases').replaceChildren(...(asset.phrases ?? []).map((p,i) => { const button = node('button', p.text || `Phrase ${i+1}`, 'phrase'); button.append(node('span', `${clock(p.start)} – ${clock(p.end)}`)); button.dataset.phrase = p.id; button.onclick = () => selectPhrase(p); return button; }));
  updateSpeed(); render(); updateTap(); renderLesson();
  if ('mediaSession' in navigator) {
    navigator.mediaSession.metadata = new MediaMetadata({title:state.song.title,artist:state.song.artist,artwork:[{src:state.song.coverUrl}]});
  }
}
function selectPhrase(phrase) {
  if (!state.asset) return;
  if (!validLoop(phrase.start, phrase.end, state.asset.duration)) return notice('This phrase needs a timing review.');
  state.loop = { ...phrase }; $('loop').setAttribute('aria-pressed','true'); audio.currentTime = phrase.start;
  document.querySelectorAll('[data-phrase]').forEach(e => e.classList.toggle('selected', e.dataset.phrase === phrase.id));
  state.offsets = []; state.lastTapBeat = null; updateTap(); render();
}
function setMode(mode) {
  state.mode = mode; document.querySelectorAll('[data-mode]').forEach(e => e.classList.toggle('selected', e.dataset.mode === mode));
  $('tap-section').hidden = mode !== 'tap';
  state.lesson = {listen:0,tap:1,play:2}[mode]; renderLesson();
}
function renderLesson() {
  if (state.song && state.song.id !== 'first-pulse') {
    const guidance = {
      listen:['Listen for a Change','Choose a short phrase. Listen once without playing.',['Listen for a repeating pulse beneath the melody.','Replay and notice when the harmony changes.','Treat detected chords as suggestions; compare them by ear.']],
      tap:['Find the Pulse','Keep your taps light and steady.',['Listen before you begin tapping.','Aim for even spacing, not a perfect score.','Detected beats can be wrong; trust a clear audible pulse over an estimate.']],
      play:['One Small Phrase','Begin with one comfortable chord change.',['Slow the phrase to a comfortable speed.','Try one strum on each chord change, then leave space.','If the harmony sounds wrong, stop and check the chord with a reviewed score or teacher.']]
    }[state.mode];
    $('lesson-title').textContent = guidance[0]; $('lesson-body').textContent = guidance[1];
    $('lesson-steps').replaceChildren(...guidance[2].map(text=>node('li',text)));
    $('next-lesson').innerHTML = 'Foundations <i data-lucide="arrow-right"></i>'; icons(); return;
  }
  const lesson = state.lessons[state.lesson]; if (!lesson) return;
  $('lesson-title').textContent = lesson.title; $('lesson-body').textContent = lesson.body;
  $('lesson-steps').replaceChildren(...lesson.steps.map(text => node('li',text)));
  $('next-lesson').innerHTML = state.lesson === 2 ? 'Back to listening <i data-lucide="arrow-left"></i>' : 'Next step <i data-lucide="arrow-right"></i>'; icons();
}
function updateSpeed() {
  const speed = Number($('speed').value) / 100; audio.playbackRate = speed;
  $('speed-value').textContent = `${Math.round(speed*100)}%`; $('effective-tempo').textContent = state.asset?.bpm ? `${Math.round(state.asset.bpm*speed)} BPM` : '— BPM';
  state.offsets = []; state.lastTapBeat = null; updateTap();
}
async function togglePlay() {
  if (!state.asset) return;
  if (!audio.paused) { audio.pause(); return; }
  if (state.loop && (audio.currentTime < state.loop.start || audio.currentTime >= state.loop.end)) audio.currentTime = state.loop.start;
  try { await audio.play(); notice(''); } catch { notice('Audio could not start. Check your connection and press play to retry.'); }
}
function drawShape(chord) {
  const shape = guitarShape(chord); const root = $('fretboard'); root.replaceChildren(); root.classList.toggle('empty', !shape);
  root.removeAttribute('aria-label'); root.removeAttribute('data-start-fret');
  if (!shape) { root.textContent = chord === '—' ? 'Listen for the next chord' : `Diagram not available for ${chord} yet`; return; }
  root.dataset.startFret = shape.startFret;
  root.classList.toggle('shifted', shape.startFret > 1);
  const top = fret => `${(fret - shape.startFret + .5) * 100 / shape.fretCount}%`;
  for (let i = 0; i < shape.fretCount; i++) {
    const label = node('span', String(shape.startFret+i), 'fret-label'); label.style.top = top(shape.startFret+i); root.append(label);
  }
  for (const [fret, first, last] of shape.barres) {
    const bar = node('span', undefined, 'fret-barre'); bar.style.left = `${first*20}%`; bar.style.width = `${(last-first)*20}%`; bar.style.top = top(fret); root.append(bar);
  }
  shape.frets.forEach((fret, string) => {
    if (fret <= 0) { const mark = node('span', fret < 0 ? '×' : '○', 'string-mark'); mark.style.left = `${string*20}%`; root.append(mark); }
    else { const dot = node('span', String(shape.fingers[string]), 'fret-dot'); dot.style.left = `${string*20}%`; dot.style.top = top(fret); root.append(dot); }
  });
  root.setAttribute('aria-label', `${chord}. Frets from low E: ${shape.frets.map(f => f < 0 ? 'muted' : f === 0 ? 'open' : f).join(', ')}. ${shape.barres.map(([f, first, last, finger]) => `Barre fret ${f}, finger ${finger}, strings ${first+1} to ${last+1}`).join('. ')}`);
}
function renderLyric(line) {
  const root = $('current-lyric'); root.replaceChildren();
  if (!line) {
    if (state.song?.id === 'first-pulse') {
      root.textContent = audio.currentTime < 4 ? 'One. Two. Three. Four.' : 'Keep the pulse. Let the chord ring.';
    } else { const mark = node('span', '♪'); mark.setAttribute('aria-label','Instrumental'); root.append(mark); }
    $('next-lyric').textContent = ''; return;
  }
  if (!line.tokens?.length) root.textContent = line.text;
  else for (const part of lyricParts(line)) {
    const token = part.token;
    if (!token) { root.append(document.createTextNode(part.text)); continue; }
    const span = node('span',undefined,'lyric-token'); span.dataset.start = token.start; span.dataset.end = token.end;
    const reading = readingText(token);
    if (reading) { const ruby = node('ruby',token.text); ruby.append(node('rt',reading)); span.append(ruby); } else span.textContent = token.text;
    root.append(span);
  }
  const index = state.asset.lyrics.indexOf(line); $('next-lyric').textContent = state.asset.lyrics[index+1]?.text ?? '';
}
function render() {
  const asset = state.asset; if (!asset) return;
  const time = audio.currentTime;
  $('time').textContent = clock(time); if (document.activeElement !== $('seek')) $('seek').value = time;
  const beat = activeBeat(asset.beats ?? [], time);
  const reference = state.song.id === 'first-pulse';
  [...$('pulse-lane').children].forEach((el,i) => {
    const pulse = reference ? beat % 4 === i && time < 20 : beat >= 0 && time - asset.beats[beat].time < .16 * audio.playbackRate;
    el.classList.toggle('active', beat >= 0 && pulse && !audio.paused);
    el.classList.toggle('count-in',reference && time < 4);
  });
  $('pulse-status').textContent = audio.paused ? 'Ready' : reference && time < 4 ? 'Count-in' : reference ? `Bar ${Math.min(4, Math.floor((time-4)/4)+1)} / 4` : 'Detected pulses · downbeat unverified';
  const line = activeInterval(asset.lyrics ?? [], time);
  const lyricKey = line?.id ?? (reference && time < 4 ? 'count-in' : 'instrumental');
  if (lyricKey !== state.lastLyric) { state.lastLyric = lyricKey; renderLyric(line); }
  document.querySelectorAll('.lyric-token').forEach(e => e.classList.toggle('singing', time >= Number(e.dataset.start) && time < Number(e.dataset.end)));
  const chord = activeInterval(asset.chords ?? [], time);
  const chordKey = `${chord?.start ?? 'gap'}:${chord?.name ?? '—'}:${$('capo').value}:${$('simplify').checked}`;
  if (chordKey !== state.lastChord) {
    state.lastChord = chordKey;
    const transformed = window.Musia?.displayChord(chord?.name ?? '—', {capo:Number($('capo').value),simplify:$('simplify').checked});
    const name = transformed?.guitar ?? chord?.name ?? '—'; $('chord-name').textContent = name; drawShape(name);
    const next = asset.chords?.find(c => c.start > time);
    $('next-chord').textContent = next ? `Next · ${window.Musia?.displayChord(next.name,{capo:Number($('capo').value),simplify:$('simplify').checked}).guitar ?? next.name}` : '—';
    $('shape-status').textContent = Number($('capo').value) ? `Shape ${name} · capo ${$('capo').value} · concert ${chord?.name ?? '—'}` : 'Standard tuning · E A D G B e';
  }
}
function updateTap() {
  const summary = tapSummary(state.offsets);
  $('tap-feedback').textContent = summary ? `Tap spread: ${summary.spread} ms` : state.offsets.length ? `${state.offsets.length} taps` : 'Find the pulse';
  $('tap-detail').textContent = summary ? `Median offset ${summary.bias > 0 ? '+' : ''}${summary.bias} ms · device latency not calibrated` : 'Timing only · device latency can affect the offset.';
}
function tap() {
  if (audio.paused || !state.asset) return notice('Start the music before tapping.');
  const beats = state.asset.beats ?? []; if (!beats.length) return notice('This track does not have a beat analysis.');
  if (audio.currentTime < beats[0].time || audio.currentTime > beats.at(-1).time + .5) return;
  const closest = beats.reduce((best,b,i) => Math.abs(b.time-audio.currentTime)<Math.abs(beats[best].time-audio.currentTime)?i:best,0);
  if (closest === state.lastTapBeat) return;
  state.lastTapBeat = closest; const offset = tapOffset(beats,audio.currentTime,audio.playbackRate);
  if (offset !== null) { state.offsets.push(offset); state.offsets = state.offsets.slice(-32); updateTap(); }
}
function saveSession(show = true) {
  if (state.seconds < 2 || !state.song) { if (show) notice('Play a little music first.'); return; }
  const entry = {id:crypto.randomUUID(),songId:state.song.id,title:state.song.title,date:new Date().toISOString(),seconds:Math.round(state.seconds),mode:state.mode,rate:audio.playbackRate,taps:tapSummary(state.offsets)};
  state.history.unshift(entry); state.history = state.history.slice(0,500);
  const saved = saveLocal('musia.practice.v1',state.history); state.seconds = 0; updateToday();
  if (show) { audio.pause(); notice(saved ? 'Practice saved. A little time with music counts.' : 'Browser storage is unavailable. Export your history to keep this session.'); view('progress'); }
}
function updateToday() {
  const today = new Date().toLocaleDateString();
  const seconds = state.history.filter(e=>new Date(e.date).toLocaleDateString()===today).reduce((sum,e)=>sum+e.seconds,0);
  $('today-progress').querySelector('span').textContent = `${Math.floor(seconds/60)} min today`;
}
function renderHistory() {
  const root = $('history'); root.replaceChildren();
  if (!state.history.length) return root.append(node('p','Your first session is a beginning, not a test.','empty-message'));
  for (const entry of state.history) {
    const row = node('article',undefined,'history-item'); const details = node('div'); details.append(node('strong',entry.title),node('p',`${new Date(entry.date).toLocaleString()} · ${entry.mode} · ${Math.round(entry.rate*100)}%`));
    row.append(details,node('strong',clock(entry.seconds))); root.append(row);
  }
}
function download(name,data) {
  const blob = new Blob([JSON.stringify(data,null,2)],{type:'application/json'}); const url = URL.createObjectURL(blob); const a=node('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
document.querySelectorAll('[data-view]').forEach(e=>e.onclick=()=>view(e.dataset.view));
document.querySelectorAll('[data-mode]').forEach(e=>e.onclick=()=>setMode(e.dataset.mode));
$('change-song').onclick=()=>view('library');$('search').oninput=renderLibrary;$('vocal').onchange=()=>selectAsset($('vocal').value);
$('play').onclick=togglePlay;$('floating-play').onclick=togglePlay;$('restart').onclick=()=>{audio.currentTime=state.loop?.start??0;render();};$('seek').oninput=()=>{audio.currentTime=Number($('seek').value);render();};$('speed').oninput=updateSpeed;
$('loop').onclick=()=>{if(state.loop){state.loop=null;$('loop').setAttribute('aria-pressed','false');document.querySelectorAll('.phrase').forEach(e=>e.classList.remove('selected'));}else if(state.asset)selectPhrase({id:'all',start:0,end:state.asset.duration});};
$('whole-song').onclick=()=>{state.loop=null;$('loop').setAttribute('aria-pressed','false');document.querySelectorAll('.phrase').forEach(e=>e.classList.remove('selected'));audio.currentTime=0;};
$('capo').onchange=render;$('simplify').onchange=render;$('tap').onpointerdown=tap;
$('tap').onclick=e=>{if(e.detail===0)tap();};
$('tap').onkeydown=e=>{if(e.key===' '||e.key==='Enter'){e.preventDefault();if(!e.repeat)tap();}};
$('clear-taps').onclick=()=>{state.offsets=[];state.lastTapBeat=null;updateTap();};
$('next-lesson').onclick=()=>state.song?.id !== 'first-pulse' ? selectSong('first-pulse') : setMode(['listen','tap','play'][(state.lesson+1)%3]);$('finish').onclick=()=>saveSession();$('today-progress').onclick=()=>view('progress');
$('export-progress').onclick=()=>download('musia-practice-history.json',{version:1,sessions:state.history});
$('reset-progress').onclick=()=>{if(confirm('Clear practice history on this device?')){state.history=[];saveLocal('musia.practice.v1',[]);updateToday();renderHistory();}};
const brief = loadLocal('musia.brief.v1',{});for(const [key,value] of Object.entries(brief))if($('brief-form').elements[key])$('brief-form').elements[key].value=value;
$('brief-form').oninput=()=>saveLocal('musia.brief.v1',Object.fromEntries(new FormData($('brief-form'))));
$('brief-form').onsubmit=e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.target));saveLocal('musia.brief.v1',data);download('musia-song-brief.json',{version:1,type:'song-brief',...data});$('brief-status').textContent='Brief exported. No generation job was submitted.';};
audio.addEventListener('play',()=>{state.lastTime=performance.now();for(const id of ['play','floating-play']){$(id).innerHTML='<i data-lucide="pause"></i>';$(id).setAttribute('aria-label','Pause');}icons();});
audio.addEventListener('pause',()=>{for(const id of ['play','floating-play']){$(id).innerHTML='<i data-lucide="play"></i>';$(id).setAttribute('aria-label','Play');}icons();render();});
audio.addEventListener('error',()=>{if(state.asset)notice('The audio is unavailable. Check the connection or choose another track.');});
audio.addEventListener('ended',()=>{if(state.loop){audio.currentTime=state.loop.start;audio.play().catch(()=>notice('Press play to continue.'));}else saveSession(false);});
audio.addEventListener('seeked',()=>{state.lastTapBeat=null;render();});
if('mediaSession' in navigator){navigator.mediaSession.setActionHandler('play',()=>audio.play().catch(()=>{}));navigator.mediaSession.setActionHandler('pause',()=>audio.pause());}
let loopTimer;
function checkLoop() {
  clearTimeout(loopTimer);
  if (!state.loop || audio.paused || audio.seeking) return;
  const remaining = (state.loop.end-audio.currentTime)/audio.playbackRate;
  if (remaining <= .005) { audio.currentTime=state.loop.start;state.lastTapBeat=null;return; }
  loopTimer=setTimeout(checkLoop,Math.max(1,Math.min(250,remaining*1000)));
}
for(const event of ['playing','pause','seeked','ratechange','timeupdate'])audio.addEventListener(event,checkLoop);
setInterval(()=>{const now=performance.now();if(!audio.paused&&!audio.seeking&&audio.readyState>=2)state.seconds+=Math.min(2,(now-state.lastTime)/1000);state.lastTime=now;$('session-time').textContent=`${clock(state.seconds)} practiced`;},100);
function frame(){if(state.loop&&!audio.paused&&audio.currentTime>=state.loop.end)checkLoop();render();requestAnimationFrame(frame);}requestAnimationFrame(frame);
window.addEventListener('pagehide',()=>saveSession(false));
async function boot(){
  icons();updateToday();$('play').disabled=true;
  try{const catalog=await request('/api/v1/library');state.library=catalog.items;const lessons=await request('/api/v1/lessons');state.lessons=lessons.lessons;renderLesson();renderLibrary();const wanted=new URLSearchParams(location.search).get('song');await selectSong(state.library.some(s=>s.id===wanted)?wanted:'first-pulse');}
  catch(error){notice(`Could not load Musia: ${error.message}. Refresh to retry.`);$('song-title').textContent='Connection unavailable';}
}
boot();
