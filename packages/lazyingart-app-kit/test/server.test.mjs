import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createAccountClient, createRefreshCoordinator, validateTokens } from '../src/server.mjs';
import { binding, callback, fixture, harness, json, MemoryFlows, MemoryVault } from './helpers.mjs';

test('S256 begin/exchange/profile; tokens stay server-side and return target survives', async () => {
  const { client, calls, flows } = harness();
  const start = await client.begin({ binding, returnTo: '/lesson/first-pulse' });
  const url = new URL(start.url);
  const flow = [...flows.rows.values()][0];
  assert.equal(url.searchParams.get('code_challenge'), createHash('sha256').update(flow.verifier).digest('base64url'));
  assert.equal(url.searchParams.get('code_challenge_method'), 'S256');
  assert.equal(url.searchParams.get('audience'), fixture.registration.audience);
  assert(!start.url.includes('synthetic-confidential-secret'));
  assert(!start.url.includes(flow.verifier));
  const result = await client.complete({ binding, callbackUrl: callback(start.url) });
  assert.equal(result.status, 'authenticated');
  assert.deepEqual(result.profile, fixture.profile);
  assert.equal(result.returnTo, '/lesson/first-pulse');
  assert.equal(flows.rows.size, 0);
  const exchange = calls.find(call => call.url.endsWith('/account/token'));
  const form = new URLSearchParams(exchange.body);
  assert.equal(form.get('code_verifier'), flow.verifier);
  assert.equal(form.get('client_secret'), 'synthetic-confidential-secret');
  for (const call of calls) {
    assert.equal(call.redirect, 'error');
    assert.equal(call.credentials, 'omit');
    assert.equal(call.cache, 'no-store');
    assert(!call.url.includes('secret'));
  }
  await assert.rejects(client.complete({ binding, callbackUrl: callback(start.url) }), { code: 'invalid_or_consumed_flow' });
});

test('cancel returns draft target without exchanging a code', async () => {
  const { client, calls } = harness();
  const start = await client.begin({ binding, returnTo: '/draft/123' });
  const url = new URL(callback(start.url, { error: 'access_denied' }));
  url.searchParams.delete('code');
  assert.deepEqual(await client.complete({ binding, callbackUrl: url.href }), { status: 'cancelled', returnTo: '/draft/123' });
  assert.equal(calls.length, 1);
});

test('callback from another browser cannot consume the bound flow', async () => {
  const { client } = harness();
  const start = await client.begin({ binding });
  await assert.rejects(client.complete({ binding: binding + '-other', callbackUrl: callback(start.url) }), { code: 'invalid_or_consumed_flow' });
  assert.equal((await client.complete({ binding, callbackUrl: callback(start.url) })).status, 'authenticated');
});

for (const [name, mutate, code] of [
  ['issuer', url => url.searchParams.set('iss', 'https://evil.example.test'), 'callback_issuer_mismatch'],
  ['state', url => url.searchParams.set('state', 'x'.repeat(43)), 'invalid_or_consumed_flow'],
  ['duplicate code', url => url.searchParams.append('code', 'second'), 'invalid_callback_parameters'],
  ['fragment', url => { url.hash = 'token=x'; }, 'callback_mismatch'],
  ['wrong path', url => { url.pathname = '/other'; }, 'callback_mismatch'],
  ['wrong origin', url => { url.hostname = 'evil.example.test'; }, 'callback_mismatch'],
  ['mixed result', url => url.searchParams.set('error', 'access_denied'), 'invalid_callback_parameters'],
  ['access token in callback', url => url.searchParams.set('access_token', 'x'), 'invalid_callback_parameters'],
]) {
  test(`reject callback ${name} before token exchange`, async () => {
    const { client, calls } = harness();
    const start = await client.begin({ binding });
    const url = new URL(callback(start.url));
    mutate(url);
    await assert.rejects(client.complete({ binding, callbackUrl: url.href }), { code });
    assert.equal(calls.length, 1);
  });
}

test('expired flow and unsafe return URL rejected', async () => {
  const { client, advance } = harness();
  const start = await client.begin({ binding });
  advance(600_001);
  await assert.rejects(client.complete({ binding, callbackUrl: callback(start.url) }), { code: 'invalid_or_consumed_flow' });
  for (const returnTo of ['https://evil.example.test', '//evil.example.test', '/\\evil', '/%2f%2fevil']) {
    await assert.rejects(client.begin({ binding, returnTo }), { code: 'invalid_return_path' });
  }
});

test('public clients never send a confidential secret', async () => {
  assert.throws(() => harness({ registration: { ...fixture.registration, type: 'public' } }), { code: 'invalid_client_secret' });
  const { client, calls } = harness({ registration: { ...fixture.registration, type: 'public' }, clientSecret: undefined });
  await client.refresh('synthetic-refresh');
  assert.equal(new URLSearchParams(calls[0].body).has('client_secret'), false);
});

test('failed exchange is not retried; flow remains consumed', async () => {
  let exchanges = 0;
  const { client } = harness({ fetchImpl: async url => {
    if (url.endsWith('/.well-known/lazyingart-account')) return json(fixture.discovery);
    exchanges++;
    throw new Error('PRIVATE response with secret');
  } });
  const start = await client.begin({ binding });
  await assert.rejects(client.complete({ binding, callbackUrl: callback(start.url) }), { message: 'account_network_error' });
  await assert.rejects(client.complete({ binding, callbackUrl: callback(start.url) }), { code: 'invalid_or_consumed_flow' });
  assert.equal(exchanges, 1);
});

test('failed profile triggers best-effort revocation of newly issued token', async () => {
  const paths = [];
  const { client } = harness({ fetchImpl: async url => {
    paths.push(url);
    if (url.endsWith('/.well-known/lazyingart-account')) return json(fixture.discovery);
    if (url.endsWith('/account/token')) return json(fixture.tokens);
    if (url.endsWith('/account/profile')) return json({ ...fixture.profile, client_id: 'other-app' });
    return json({ success: true });
  } });
  const start = await client.begin({ binding });
  await assert.rejects(client.complete({ binding, callbackUrl: callback(start.url) }), { code: 'profile_client_mismatch' });
  assert(paths.at(-1).endsWith('/account/revoke'));
});

test('timeouts and upstream HTTP failures are bounded and sanitized', async () => {
  const { client } = harness({ timeoutMs: 5, fetchImpl: async (url, { signal }) =>
    new Promise((resolve, reject) => signal.addEventListener('abort', () => reject(new Error('PRIVATE')))) });
  await assert.rejects(client.discover(), { code: 'account_timeout' });
  for (const status of [401, 403, 404, 429, 503]) {
    let calls = 0;
    const failed = harness({ fetchImpl: async () => { calls++; return json({ error: 'private details' }, status); } });
    await assert.rejects(failed.client.discover(), { message: `account_http_${status}` });
    assert.equal(calls, 1);
  }
});

test('reject redirects, malformed JSON and oversized streams', async () => {
  for (const [response, code] of [
    [new Response('', { status: 302, headers: { Location: 'https://evil.example.test' } }), 'account_http_302'],
    [new Response('no json'), 'invalid_response_type'],
    [new Response('broken', { headers: { 'Content-Type': 'application/json' } }), 'invalid_account_json'],
    [json({ x: 'x'.repeat(40_000) }), 'account_response_too_large'],
  ]) {
    const { client } = harness({ fetchImpl: async () => response });
    await assert.rejects(client.discover(), { code });
  }
});

test('token response validation rejects arbitrary lifetimes and scopes', () => {
  assert.deepEqual(validateTokens(fixture.tokens), fixture.tokens);
  for (const override of [{ scope: 'admin' }, { token_type: 'JWT' }, { expires_in: 601 }, { expires_in: 0 },
    { expires_in: '600' }, { access_token: 'bad\r\nheader' }, { refresh_token: '' }]) {
    assert.throws(() => validateTokens({ ...fixture.tokens, ...override }));
  }
});

test('refresh is single-flight and stores rotation before acknowledging success', async () => {
  const vault = new MemoryVault();
  let resolve;
  let calls = 0;
  const pending = new Promise(done => { resolve = done; });
  const refresh = createRefreshCoordinator({ vault, client: { refresh: async () => { calls++; await pending; return fixture.tokens; } } });
  const one = refresh('session-one');
  const two = refresh('session-one');
  assert.equal(one, two);
  resolve();
  assert.deepEqual(await one, { status: 'refreshed' });
  assert.equal(calls, 1);
  assert.deepEqual(vault.committed, fixture.tokens);
});

test('lost refresh response is not replayed even by a new coordinator', async () => {
  const vault = new MemoryVault();
  let calls = 0;
  const client = { refresh: async () => { calls++; throw new Error('network gone'); } };
  const refresh = createRefreshCoordinator({ vault, client });
  await assert.rejects(refresh('session'), { code: 'reauth_required' });
  assert.equal(vault.phase, 'reauth_required');
  await assert.rejects(createRefreshCoordinator({ vault, client })('session'), { code: 'reauth_required' });
  assert.equal(calls, 1);
});

test('a crash after durable claim requires sign-in; no replay from another worker', async () => {
  const vault = new MemoryVault();
  await vault.claimRefresh('session');
  const refresh = createRefreshCoordinator({ vault, client: { refresh: async () => assert.fail('must not replay') } });
  await assert.rejects(refresh('session'), { code: 'reauth_required' });
});

test('logout during refresh cannot resurrect a session; revoke unused rotation', async () => {
  const vault = new MemoryVault();
  let revoked;
  const client = {
    refresh: async () => { vault.phase = 'signed_out'; return fixture.tokens; },
    revoke: async token => { revoked = token; },
  };
  await assert.rejects(createRefreshCoordinator({ vault, client })('session'), { code: 'reauth_required' });
  assert.equal(vault.phase, 'signed_out');
  assert.equal(revoked, fixture.tokens.refresh_token);
  assert.equal(vault.committed, null);
});

test('failed rotation persistence revokes new credential and requires sign-in', async () => {
  const vault = new MemoryVault();
  vault.commitRefresh = async () => { throw new Error('storage unavailable'); };
  let revoked = false;
  const client = { refresh: async () => fixture.tokens, revoke: async () => { revoked = true; } };
  await assert.rejects(createRefreshCoordinator({ vault, client })('session'), { code: 'reauth_required' });
  assert.equal(revoked, true);
  assert.equal(vault.phase, 'reauth_required');
});

test('explicit durable store contracts are required', () => {
  assert.throws(() => createAccountClient({ registration: fixture.registration, clientSecret: 'test' }), { code: 'flow_store_required' });
  assert.throws(() => createRefreshCoordinator({ client: {}, vault: {} }), { code: 'refresh_vault_required' });
  assert.throws(() => createAccountClient({ registration: fixture.registration,
    clientSecret: 'test', flowStore: new MemoryFlows(), timeoutMs: 1_000_000 }), { code: 'invalid_transport' });
});

test('another worker holding a refresh lease is busy, not an invalid account', async () => {
  const vault = new MemoryVault();
  vault.claimRefresh = async () => ({ status: 'busy' });
  const client = { refresh: async () => assert.fail('must not refresh twice') };
  await assert.rejects(createRefreshCoordinator({ vault, client })('session'), { code: 'refresh_in_progress' });
  assert.equal(vault.phase, 'active');
});

test('storage errors cannot expose credentials in a refresh failure', async () => {
  const vault = new MemoryVault();
  vault.requireSignIn = async () => { throw new Error('PRIVATE'); };
  const client = { refresh: async () => { throw new Error('PRIVATE'); } };
  await assert.rejects(createRefreshCoordinator({ vault, client })('session'), { message: 'session_storage_unavailable' });
});

test('flow and refresh claim storage failures expose only a safe code', async () => {
  const flows = new MemoryFlows();
  const { client } = harness({ flowStore: flows });
  flows.create = async () => { throw new Error('PRIVATE FLOW'); };
  await assert.rejects(client.begin({ binding }), { message: 'session_storage_unavailable' });
  const other = harness();
  const start = await other.client.begin({ binding });
  other.flows.take = async () => { throw new Error('PRIVATE FLOW'); };
  await assert.rejects(other.client.complete({ binding, callbackUrl: callback(start.url) }), { message: 'session_storage_unavailable' });
  const vault = new MemoryVault();
  vault.claimRefresh = async () => { throw new Error('PRIVATE TOKEN'); };
  await assert.rejects(createRefreshCoordinator({ vault, client: {} })('session'), { message: 'session_storage_unavailable' });
});
