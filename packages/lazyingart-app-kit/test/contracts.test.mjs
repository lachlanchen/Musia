import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  ACCEPTANCE_GATES, accountKey, assessReadiness, featureDecision, validateAppManifest,
  validateDiscovery, validateIssuer, validateProfile, validateRegistration,
} from '../src/contracts.mjs';
import { fixture } from './helpers.mjs';

const manifest = JSON.parse(await readFile(new URL('../fixtures/app.json', import.meta.url), 'utf8'));

test('sample defaults to guest features and unconfigured account service', () => {
  const result = assessReadiness(manifest);
  assert.equal(result.readyForOwnerReview, false);
  assert.equal(result.liveServiceVerifiedByThisTool, false);
  assert.deepEqual(result.blockers, ['disabled_by_default', 'no_registered_clients']);
  for (const feature of manifest.features) {
    assert.equal(featureDecision(feature), feature.available ? 'available' : 'unavailable');
  }
});

for (const value of ['http://account.example.test', 'https://account.example.test/',
  'https://a:b@account.example.test', 'https://account.example.test?token=x', 'https://account.example.test/path',
  'https://account.example.test#x', 'https://ACCOUNT.example.test']) {
  test(`reject non-pinned issuer ${value}`, () => assert.throws(() => validateIssuer(value)));
}

test('registration requires exact HTTPS redirect and separate client binding', () => {
  assert.equal(validateRegistration(fixture.registration).issuer, fixture.registration.issuer);
  for (const redirectUri of ['musia://login', 'http://localhost/callback', 'https://app.example.test/*',
    'https://app.example.test/callback?next=x', 'https://app.example.test/callback#x',
    'https://app.example.test/callback?', 'https://app.example.test/callback#']) {
    assert.throws(() => validateRegistration({ ...fixture.registration, redirectUri }));
  }
});

test('discovery validates actual EchoMind candidate wire format', () => {
  const discovery = validateDiscovery(fixture.discovery, fixture.registration.issuer);
  assert.equal(discovery.providers.apple, false);
  for (const override of [{ issuer: 'https://wrong.example.test' }, { contract_version: 2 },
    { token_endpoint: 'https://wrong.example.test/account/token' }, { code_challenge_methods_supported: ['plain'] },
    { registration_requires_invitation: true }, { providers: { apple: 'true' } }]) {
    assert.throws(() => validateDiscovery({ ...fixture.discovery, ...override }, fixture.registration.issuer));
  }
});

test('profile returns minimal identity, not provider, email or wallet privileges', () => {
  assert.deepEqual(validateProfile({ ...fixture.profile, email: 'private@example.test', wallet: 'secret' },
    fixture.registration.clientId), fixture.profile);
  assert.throws(() => validateProfile({ ...fixture.profile, client_id: 'coin' }, fixture.registration.clientId));
  assert.throws(() => validateProfile({ ...fixture.profile, account_status: 'suspended' }, fixture.registration.clientId));
  assert.notEqual(accountKey(fixture.registration.issuer, 'id'), accountKey('https://other.example.test', 'id'));
});

for (const item of fixture.featureDecisions) {
  test(`feature guidance ${item.session}/${item.access}/${item.requiresAccount}: ${item.expected}`, () => {
    assert.equal(featureDecision({ available: true, ...item }, item.session, item.access), item.expected);
  });
}

test('unknown capability and malformed booleans fail closed', () => {
  assert.throws(() => featureDecision({ available: 'true', requiresAccount: false, requiresAccess: false }));
  assert.throws(() => featureDecision({ available: true, requiresAccount: false, requiresAccess: false }, 'unknown'));
});

test('readiness evidence is bound to candidate, platform, audience and exact callback', () => {
  const candidate = structuredClone(manifest);
  candidate.account = { enabled: true, registrations: [fixture.registration] };
  const key = JSON.stringify([fixture.registration.issuer, fixture.registration.clientId]);
  const receipt = { ...fixture.registration, candidate: candidate.candidate, verifiedAt: '2026-09-27T00:00:00Z',
    checks: Object.fromEntries(ACCEPTANCE_GATES.map(gate => [gate, true])) };
  assert.equal(assessReadiness(candidate, { clients: { [key]: receipt } }).readyForOwnerReview, true);
  for (const override of [{ candidate: 'old-build' }, { audience: 'coin' }, { platform: 'ios' },
    { redirectUri: 'https://wrong.example.test/callback' }, { verifiedAt: 'not-a-date' }, { checks: {} }]) {
    assert.equal(assessReadiness(candidate, { clients: { [key]: { ...receipt, ...override } } }).readyForOwnerReview, false);
  }
});

test('invalid manifests and duplicate clients are rejected', () => {
  for (const override of [{ appId: undefined }, { features: [null] }, { features: [{}] },
    { account: { enabled: 'false', registrations: [] } },
    { account: { enabled: true, registrations: [fixture.registration, fixture.registration] } }]) {
    assert.throws(() => validateAppManifest({ ...manifest, ...override }));
  }
});
