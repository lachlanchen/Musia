import { copyFile, mkdir } from 'node:fs/promises';
await mkdir(new URL('../vendor/', import.meta.url), { recursive: true });
await copyFile(new URL('../node_modules/lucide/dist/umd/lucide.min.js', import.meta.url), new URL('../vendor/lucide.js', import.meta.url));
