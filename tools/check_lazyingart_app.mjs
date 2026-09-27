#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { assessReadiness, ContractError } from '../packages/lazyingart-app-kit/src/contracts.mjs';

// Offline only: no credentials, .env reads, network requests or deployment side effects.
const args = process.argv.slice(2);
let manifestPath = fileURLToPath(new URL('../apps/shared/lazyingart-app.json', import.meta.url));
let evidencePath;
let requireReady = false;
try {
  for (let index = 0; index < args.length; index++) {
    const arg = args[index];
    if (arg === '--require-ready') requireReady = true;
    else if (arg === '--manifest' || arg === '--evidence') {
      if (!args[index + 1] || args[index + 1].startsWith('--')) throw new ContractError('missing_argument');
      if (arg === '--manifest') manifestPath = args[++index];
      else evidencePath = args[++index];
    } else if (arg === '--help') {
      console.log('node tools/check_lazyingart_app.mjs [--manifest file.json] [--evidence file.json] [--require-ready]');
      process.exit(0);
    } else throw new ContractError('unknown_argument');
  }
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
  const evidence = evidencePath ? JSON.parse(await readFile(evidencePath, 'utf8')) : {};
  const report = assessReadiness(manifest, evidence);
  console.log(JSON.stringify(report, null, 2));
  if (requireReady && !report.readyForOwnerReview) process.exitCode = 2;
} catch (error) {
  console.error(JSON.stringify({ configurationValid: false,
    code: error instanceof ContractError ? error.code : 'cannot_read_configuration' }));
  process.exitCode = 1;
}
