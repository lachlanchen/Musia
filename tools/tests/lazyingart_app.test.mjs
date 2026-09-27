import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { assessReadiness, featureDecision } from '../../packages/lazyingart-app-kit/src/contracts.mjs';

test('Musia adoption manifest preserves guest playback and has no guessed endpoints', async () => {
  const manifest = JSON.parse(await readFile(new URL('../../apps/shared/lazyingart-app.json', import.meta.url), 'utf8'));
  assert.equal(manifest.appId, 'musia');
  assert.deepEqual(assessReadiness(manifest).blockers, ['disabled_by_default', 'no_registered_clients']);
  for (const feature of manifest.features) {
    const guestAvailable = ['library', 'lessons', 'exerciseAudio'].includes(feature.id);
    assert.equal(featureDecision(feature), guestAvailable ? 'available' : 'unavailable');
    if (!guestAvailable) assert.equal(feature.explicitConfirmation, true);
  }
});

test('offline doctor distinguishes valid configuration from release readiness', () => {
  const script = new URL('../check_lazyingart_app.mjs', import.meta.url);
  for (const [args, status] of [[[], 0], [['--require-ready'], 2], [['--unknown'], 1], [['--manifest'], 1]]) {
    const result = spawnSync(process.execPath, [script.pathname, ...args], { encoding: 'utf8' });
    assert.equal(result.status, status, result.stderr);
    assert.equal(JSON.parse(result.stdout || result.stderr).liveServiceVerifiedByThisTool, status === 1 ? undefined : false);
  }
});
