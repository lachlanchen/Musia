// Reuse the reviewed installed modules; never install or patch LazyEdge here.
import { readFile, realpath } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = process.env.MUSIA_LAZYEDGE_ROOT;
if (!root || resolve(root) !== await realpath(root)) {
  throw new Error('MUSIA_LAZYEDGE_ROOT must be an absolute, immutable real directory');
}
const pin = JSON.parse(await readFile(new URL('./lazyedge-pin.json', import.meta.url)));
for (const [name, expected] of Object.entries(pin.files)) {
  const bytes = await readFile(join(root, name));
  if (createHash('sha256').update(bytes).digest('hex') !== expected) {
    throw new Error('Reviewed LazyEdge module digest mismatch');
  }
}
if (JSON.parse(await readFile(join(root, 'package.json'))).version !== pin.version) {
  throw new Error('Reviewed LazyEdge version mismatch');
}
export const security = await import(pathToFileURL(join(root, 'src/security.js')));
export const proxy = await import(pathToFileURL(join(root, 'src/proxy.js')));
