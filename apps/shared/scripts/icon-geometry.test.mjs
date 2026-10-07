import assert from 'node:assert/strict';
import test from 'node:test';
import { inspectRoundedIcon } from './icon-geometry.mjs';

function fixture({ radius = 20, padding = 6, size = 100 } = {}) {
  const pixels = Buffer.alloc(size * size * 4);
  for (let y = padding; y < size - padding; y++) for (let x = padding; x < size - padding; x++) {
    const dx = Math.max(padding + radius - x, x - (size - padding - 1 - radius), 0);
    const dy = Math.max(padding + radius - y, y - (size - padding - 1 - radius), 0);
    if (Math.hypot(dx, dy) <= radius) pixels[(y * size + x) * 4 + 3] = 255;
  }
  return pixels;
}

test('rounded tile with balanced Dock padding passes', () => {
  assert.equal(inspectRoundedIcon(fixture(), 100, { maxExtent: .94 }).extent, .88);
});
test('transparent canvas cannot disguise a square tile', () => {
  assert.throws(() => inspectRoundedIcon(fixture({ radius: 0 }), 100), /square corners/);
});
test('clipping only the extreme corner pixels is insufficient', () => {
  assert.throws(() => inspectRoundedIcon(fixture({ radius: 2 }), 100), /square corners/);
});
test('empty, undersized and oversized silhouettes are rejected', () => {
  assert.throws(() => inspectRoundedIcon(Buffer.alloc(40000), 100), /No opaque/);
  assert.throws(() => inspectRoundedIcon(fixture({ padding: 20 }), 100), /too small/);
  assert.throws(() => inspectRoundedIcon(fixture({ padding: 0 }), 100, { maxExtent: .94 }), /padding/);
});
test('small antialiased corners pass without accepting a small square', () => {
  const pixels = fixture({ size: 32, radius: 6, padding: 2 });
  for (const [x, y] of [[3, 3], [28, 3], [3, 28], [28, 28]]) pixels[(y * 32 + x) * 4 + 3] = 72;
  inspectRoundedIcon(pixels, 32);
  assert.throws(() => inspectRoundedIcon(fixture({ size: 32, radius: 0, padding: 2 }), 32), /square corners/);
});
