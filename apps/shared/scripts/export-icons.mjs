import { mkdirSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const square = resolve(root, 'apps/shared/brand/musia-ribbon-square.png');
const rounded = resolve(root, 'apps/shared/brand/musia-ribbon-rounded.png');

export function exportNativeIcons(platforms = ['ios', 'macos', 'android']) {
  const convert = ['magick', 'convert'].find(command => spawnSync(command, ['-version']).status === 0);
  if (!convert) throw new Error('Icon export requires ImageMagick (magick or convert). Normal app builds use the checked-in PNGs.');
  for (const file of [square, rounded]) {
    if (!readFileSync(file).subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) {
      throw new Error(`Expected generated PNG master: ${file}`);
    }
  }
  function raster(source, size, destination, { alpha = false, inset = false } = {}) {
    const target = resolve(root, destination);
    mkdirSync(dirname(target), { recursive: true });
    const args = [source, '-colorspace', 'sRGB', '-filter', 'Lanczos', '-resize', `${inset ? Math.round(size * .9) : size}x${inset ? Math.round(size * .9) : size}`];
    if (inset) args.push('-background', 'none', '-gravity', 'center', '-extent', `${size}x${size}`);
    args.push('-depth', '8', '-strip');
    if (!alpha) args.push('-alpha', 'off');
    args.push(`${alpha ? 'PNG32' : 'PNG24'}:${target}`);
    const result = spawnSync(convert, args, { encoding: 'utf8' });
    if (result.status !== 0) throw new Error(result.stderr || `Icon export failed: ${target}`);
  }
  if (platforms.includes('ios')) {
    // iOS supplies its own corner mask; the submitted 1024px source is opaque.
    raster(square, 1024, 'apps/ios/Musia/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon.png');
  }
  if (platforms.includes('macos')) {
    for (const size of [16, 32, 128, 256, 512]) {
      for (const scale of [1, 2]) {
        raster(rounded, size * scale, `apps/macos/Musia/Resources/Assets.xcassets/AppIcon.appiconset/icon-${size}@${scale}x.png`, { alpha: true, inset: true });
      }
    }
  }
  if (platforms.includes('android')) {
    for (const [density, size] of Object.entries({ mdpi: 48, hdpi: 72, xhdpi: 96, xxhdpi: 144, xxxhdpi: 192 })) {
      raster(rounded, size, `apps/android/app/src/main/res/mipmap-${density}/ic_musia.png`, { alpha: true });
    }
    // XML insets this source to 72dp inside the launcher's 108dp adaptive layer.
    raster(square, 432, 'apps/android/app/src/main/res/drawable-nodpi/musia_icon_art.png');
    raster(square, 512, 'store/branding/musia-icon-512.png');
  }
  console.log(`Exported Musia ribbon icon: ${platforms.join(', ')}`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const selected = process.argv.slice(2);
  if (selected.some(value => !['ios', 'macos', 'android'].includes(value))) throw new Error('Use ios, macos, android, or no arguments for all.');
  exportNativeIcons(selected.length ? selected : undefined);
}
