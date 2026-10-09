// Secret-free, read-only release evidence. Import also verifies LazyEdge pins.
import './lazyedge.mjs';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const canonical = value => Array.isArray(value) ? value.map(canonical) :
  value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])])) : value;
const policy = JSON.parse(await readFile(new URL('./policy.json', import.meta.url)));
const pin = JSON.parse(await readFile(new URL('./lazyedge-pin.json', import.meta.url)));
console.log(JSON.stringify({ lazyedge: pin, manifestSha256:
  createHash('sha256').update(JSON.stringify(canonical(policy))).digest('hex') }, null, 2));
