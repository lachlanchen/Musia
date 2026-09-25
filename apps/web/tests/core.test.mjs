import test from 'node:test';
import assert from 'node:assert/strict';
import { activeInterval, activeBeat, tapOffset, tapSummary, validLoop, clock, practiceHistory, lyricParts } from '../core.js';

test('instrumental gaps and half-open chord boundaries stay empty', () => {
  const cues = [{start: 2, end: 3}, {start: 4, end: 5}];
  assert.equal(activeInterval(cues, 1), null);
  assert.equal(activeInterval(cues, 3), null);
  assert.equal(activeInterval(cues, 4), cues[1]);
});
test('beat clock never starts before first detected beat', () => {
  assert.equal(activeBeat([{time: 2}, {time: 3}], 1), -1);
  assert.equal(activeBeat([{time: 2}, {time: 3}], 3), 1);
});
test('tap offset uses real elapsed time at slow playback', () => {
  assert.ok(Math.abs(tapOffset([{time: 1}], 1.1, .5) - 200) < .001);
  assert.equal(tapOffset([], 1), null);
  assert.equal(tapOffset([{time:1}], 1, NaN), null);
});
test('constant device latency is separated from steadiness', () => {
  assert.deepEqual(tapSummary([100, 100, 100, 100]), {bias:100, spread:0, count:4});
  assert.equal(tapSummary([3, 5]), null);
});
test('loop bounds and display are guarded', () => {
  assert.equal(validLoop(4, 8, 22), true);
  assert.equal(validLoop(8, 4, 22), false);
  assert.equal(validLoop(4, 30, 22), false);
  assert.equal(validLoop(NaN, 8, 22), false);
  assert.equal(validLoop(4, 8, Infinity), false);
  assert.equal(clock(NaN), '0:00');
  assert.equal(clock(138), '2:18');
});
test('malformed saved progress cannot break app startup', () => {
  assert.deepEqual(practiceHistory({}), []);
  assert.deepEqual(practiceHistory([null, {title:'broken'}]), []);
  const entry = {title:'Song',songId:'song',date:'2026-09-25T00:00:00Z',seconds:10,rate:.75,mode:'tap'};
  assert.deepEqual(practiceHistory([entry]), [entry]);
});
test('word highlighting preserves original multilingual spacing and punctuation', () => {
  const text = 'Rain, rain 君と 雨';
  const parts = lyricParts({text,tokens:['Rain',',','rain','君','と','雨'].map(text=>({text}))});
  assert.equal(parts.map(p=>p.text).join(''),text);
  assert.equal(parts.filter(p=>p.token).length,6);
  assert.deepEqual(lyricParts({text:'Different words',tokens:[{text:'missing'}]}),[{text:'Different words'}]);
});
