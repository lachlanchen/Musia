import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { inspectRoundedIcon } from './icon-geometry.mjs';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const convert = ['magick', 'convert'].find(command => spawnSync(command, ['-version']).status === 0);
assert(convert, 'ImageMagick is required for icon pixel validation');
assert.equal(createHash('sha256').update(readFileSync(resolve(root, 'apps/shared/brand/musia-sound-bars.png'))).digest('hex'),
  '165fa7aee650c4519891008f0885b300d96bd375201f3513d219532b2e09a7aa',
  'The original sound-bar master must not be silently redrawn or replaced');
let checked = 0;
function check(file, size, rounded) {
  const path = resolve(root, file);
  const png = readFileSync(path);
  assert.equal(png.readUInt32BE(16), size, file);
  assert.equal(png.readUInt32BE(20), size, file);
  assert.equal(png[24], 8, file);
  assert.equal(png[25], rounded ? 6 : 2, `Wrong PNG color type: ${file}`);
  const decoded = spawnSync(convert, [path, '-depth', '8', 'rgba:-'], { maxBuffer: 16 * 1024 * 1024 });
  assert.equal(decoded.status, 0, file);
  const pixels = decoded.stdout;
  assert.equal(pixels.length, size * size * 4, file);
  if (rounded && size >= 32) {
    try {
      inspectRoundedIcon(pixels, size, { maxExtent: file.includes('/macos/') ? .94 : 1 });
    } catch (error) {
      throw new Error(`${file}: ${error.message}`);
    }
  }
  for (const [x, y] of [[0, 0], [size - 1, 0], [0, size - 1], [size - 1, size - 1]]) {
    const alpha = pixels[(y * size + x) * 4 + 3];
    // Lanczos can leave a one-step alpha fringe when downsampling a mask.
    assert(rounded ? alpha <= 2 : alpha === 255, `Corner alpha: ${file}`);
  }
  const colored = [];
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const i = (y * size + x) * 4;
    const rgb = pixels.subarray(i, i + 3);
    // Teal is the background, not part of the adaptive foreground's bounds.
    const white = rgb[0] > 100 && rgb[1] > 160 && rgb[2] > 160;
    const coral = rgb[0] > 120 && rgb[0] > rgb[1] * 1.5 && rgb[2] < 150;
    if (pixels[i + 3] > 200 && (white || coral)) colored.push([x, y]);
  }
  assert(colored.length > size * size * .05, `Missing visible sound bars: ${file}`);
  checked++;
  return colored;
}

check('apps/ios/Musia/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon.png', 1024, false);
check('apps/ios/WatchResources/Assets.xcassets/AppIcon.appiconset/AppIcon.png', 1024, false);
for (const size of [16, 32, 128, 256, 512]) for (const scale of [1, 2]) {
  check(`apps/macos/Musia/Resources/Assets.xcassets/AppIcon.appiconset/icon-${size}@${scale}x.png`, size * scale, true);
}
for (const [density, size] of Object.entries({ mdpi: 48, hdpi: 72, xhdpi: 96, xxhdpi: 144, xxxhdpi: 192 })) {
  check(`apps/android/app/src/main/res/mipmap-${density}/ic_musia.png`, size, true);
}
const adaptive = check('apps/android/app/src/main/res/drawable-nodpi/musia_icon_art.png', 432, false);
// The XML scales the square to 72dp inside 108dp; colored detail must fit the
// launcher's 66dp-diameter safe circle rather than merely the square's bounds.
const radius = Math.max(...adaptive.map(([x, y]) => Math.hypot((x / 432 - .5) * 72, (y / 432 - .5) * 72)));
assert(radius < 33, `Sound bars cropped by an adaptive mask: radius ${radius}`);
check('store/branding/musia-icon-512.png', 512, false);
console.log(`PASS: ${checked} icon exports, dimensions, opaque iOS/Watch/store PNGs, transparent rounded corners, visible small-size sound bars; adaptive radius ${radius.toFixed(1)}dp < 33dp`);
