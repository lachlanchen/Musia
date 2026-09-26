import test from 'node:test';
import assert from 'node:assert/strict';
import {guitarShape} from './guitar-shapes.js';

test('every catalog triad has exactly its chord tones and all dots fit', () => {
  const roots = ['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B'];
  const tuning = [40,45,50,55,59,64];
  roots.forEach((root, pitch) => {
    for (const suffix of ['', 'm']) {
      const shape = guitarShape(root+suffix);
      assert.ok(shape, root+suffix);
      const notes = shape.frets.flatMap((f,i) => f < 0 ? [] : [(tuning[i]+f)%12]);
      assert.deepEqual(new Set(notes), new Set([pitch, (pitch+(suffix ? 3 : 4))%12, (pitch+7)%12]));
      assert.equal(notes[0], pitch);
      shape.frets.filter(f => f > 0).forEach(f => assert.ok(f >= shape.startFret && f < shape.startFret+shape.fretCount));
    }
  });
  assert.equal(guitarShape('Eb').startFret, 6);
  assert.equal(guitarShape('B').barres.length, 2);
});

test('aliases retain exact quality; unknown chords are not silently simplified', () => {
  for (const [alias, name] of [['Db','C#'],['G\u266dm','F#m'],['D#:min','Ebm'],['C:maj','C']]) {
    assert.deepEqual(guitarShape(alias).frets, guitarShape(name).frets);
  }
  for (const name of ['',null,'N','C7','Cmaj7','C/E','H','Em/G']) assert.equal(guitarShape(name), null);
});
