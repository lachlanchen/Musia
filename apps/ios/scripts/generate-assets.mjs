import { deflateSync } from 'node:zlib';
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { exportNativeIcons } from '../../shared/scripts/export-icons.mjs';

// Keep the First Pulse exercise artwork; the app icon uses the shared master.
function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit++) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
  }
  return (crc ^ 0xffffffff) >>> 0;
}
function chunk(type, data) {
  const name = Buffer.from(type);
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length);
  const checksum = Buffer.alloc(4);
  checksum.writeUInt32BE(crc32(Buffer.concat([name, data])));
  return Buffer.concat([length, name, data, checksum]);
}
function render(size, isIcon) {
  const rows = Buffer.alloc(size * (1 + size * 3));
  const bars = [0.46, 0.30, 0.36, 0.30];
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const u = x / size, v = y / size;
      let color = isIcon ? [0, 110, 110] : [235, 250, 247];
      if (!isIcon && Math.abs(v - 0.70) < 0.002 && u > 0.13 && u < 0.87) color = [137, 190, 179];
      for (let bar = 0; bar < 4; bar++) {
        const left = 0.19 + bar * 0.165;
        if (u >= left && u <= left + 0.11 && v >= 0.5 - bars[bar] / 2 && v <= 0.5 + bars[bar] / 2) {
          color = bar === 0 ? [242, 105, 89] : isIcon ? [255, 255, 255] : [0, 110, 110];
        }
      }
      const offset = y * (1 + size * 3) + 1 + x * 3;
      rows.set(color, offset);
    }
  }
  const header = Buffer.alloc(13);
  header.writeUInt32BE(size, 0); header.writeUInt32BE(size, 4);
  header[8] = 8; header[9] = 2;
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', header),
    chunk('IDAT', deflateSync(rows)), chunk('IEND', Buffer.alloc(0)),
  ]);
}
const root = new URL('../Musia/Resources/Assets.xcassets/', import.meta.url);
exportNativeIcons(['ios']);
writeFileSync(fileURLToPath(new URL('FirstPulseCover.imageset/FirstPulseCover.png', root)), render(512, false));
