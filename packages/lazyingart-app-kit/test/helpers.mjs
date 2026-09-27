import { readFile } from 'node:fs/promises';
import { createAccountClient } from '../src/server.mjs';

export const fixture = JSON.parse(await readFile(new URL('../fixtures/account-v1.json', import.meta.url), 'utf8'));
export const binding = 'synthetic-browser-binding-32-characters';
export const json = (value, status = 200) => new Response(JSON.stringify(value), {
  status, headers: { 'content-type': 'application/json' },
});

// TEST ONLY: no restart durability, eviction or production encryption.
export class MemoryFlows {
  rows = new Map();
  async create(flow) { this.rows.set(flow.state, structuredClone(flow)); }
  async take(state, bound, now) {
    const row = this.rows.get(state);
    if (!row || row.binding !== bound) return null;
    this.rows.delete(state);
    return row.expiresAt > now ? row : null;
  }
}

export function harness(overrides = {}) {
  const calls = [];
  const flows = new MemoryFlows();
  let time = Date.now();
  const fetchImpl = async (url, options) => {
    calls.push({ url, ...options });
    if (url.endsWith('/.well-known/lazyingart-account')) return json(fixture.discovery);
    if (url.endsWith('/account/token')) return json(fixture.tokens);
    if (url.endsWith('/account/profile')) return json(fixture.profile);
    if (url.endsWith('/account/revoke')) return json({ success: true });
    throw new Error('unexpected route');
  };
  const client = createAccountClient({ registration: fixture.registration,
    clientSecret: 'synthetic-confidential-secret', flowStore: flows, now: () => time,
    fetchImpl, ...overrides });
  return { client, calls, flows, advance: delta => { time += delta; } };
}

export function callback(authorizationUrl, changes = {}) {
  const start = new URL(authorizationUrl);
  const url = new URL(fixture.registration.redirectUri);
  url.search = new URLSearchParams({ state: start.searchParams.get('state'),
    iss: fixture.registration.issuer, code: 'synthetic-code', ...changes }).toString();
  return url.href;
}

export class MemoryVault {
  phase = 'active';
  claimed = 0;
  committed = null;
  async claimRefresh() {
    if (this.phase !== 'active') return null;
    this.phase = 'refreshing';
    this.claimed++;
    return { lease: `lease-${this.claimed}`, refreshToken: 'synthetic-refresh-token' };
  }
  async commitRefresh(id, lease, tokens) {
    if (this.phase !== 'refreshing' || lease !== `lease-${this.claimed}`) return false;
    this.phase = 'active';
    this.committed = tokens;
    return true;
  }
  async requireSignIn(id, lease) {
    if (this.phase === 'refreshing' && lease === `lease-${this.claimed}`) this.phase = 'reauth_required';
  }
}
