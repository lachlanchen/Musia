import assert from 'node:assert/strict';

// Inspect the visible silhouette, not just the outer canvas. A padded square
// has transparent canvas corners too, but must still fail this check.
export function inspectRoundedIcon(pixels, size, { minExtent = .8, maxExtent = 1 } = {}) {
  assert.equal(pixels.length, size * size * 4, 'Unexpected RGBA data length');
  const alpha = (x, y) => pixels[(y * size + x) * 4 + 3];
  let left = size, top = size, right = -1, bottom = -1;
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    if (alpha(x, y) > 200) {
      left = Math.min(left, x); right = Math.max(right, x);
      top = Math.min(top, y); bottom = Math.max(bottom, y);
    }
  }
  assert(right >= left && bottom >= top, 'No opaque icon silhouette');
  const width = right - left + 1, height = bottom - top + 1;
  assert(width / size >= minExtent && height / size >= minExtent, 'Icon is too small');
  assert(width / size <= maxExtent && height / size <= maxExtent, 'Missing icon padding');
  assert(Math.abs(width - height) <= Math.max(2, size * .02), 'Icon silhouette is not square');
  assert(Math.abs(left - (size - 1 - right)) <= Math.max(2, size * .02), 'Unbalanced horizontal padding');
  assert(Math.abs(top - (size - 1 - bottom)) <= Math.max(2, size * .02), 'Unbalanced vertical padding');
  const dx = Math.max(1, Math.floor(width * .05));
  const dy = Math.max(1, Math.floor(height * .05));
  const corners = [[left + dx, top + dy], [right - dx, top + dy],
    [left + dx, bottom - dy], [right - dx, bottom - dy]];
  // At 32px a curved edge can occupy most of one pixel after downsampling.
  const cornerLimit = size < 64 ? 96 : 32;
  assert(corners.every(([x, y]) => alpha(x, y) < cornerLimit), 'Visible silhouette has square corners');
  const cx = Math.floor((left + right) / 2), cy = Math.floor((top + bottom) / 2);
  for (const [x, y] of [[cx, top + dy], [cx, bottom - dy], [left + dx, cy], [right - dx, cy], [cx, cy]]) {
    assert(alpha(x, y) > 240, 'Rounded tile has a hole or missing edge');
  }
  return { bounds: { left, top, right, bottom }, extent: width / size };
}
