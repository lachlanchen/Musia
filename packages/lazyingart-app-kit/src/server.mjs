// Server-only transport for EchoMind's v1 candidate, not an OIDC/provider SDK.
import { createHash, randomBytes, timingSafeEqual } from 'node:crypto';
import {
  ContractError, boundedText, requireContract, validateDiscovery, validateProfile, validateRegistration,
} from './contracts.mjs';

const MAX_BODY = 32 * 1024;
const FLOW_TTL = 10 * 60 * 1000;
const tokenText = value => boundedText(value, 4096) && !/\s/u.test(value);
const digest = value => createHash('sha256').update(value).digest();
const equals = (a, b) => typeof a === 'string' && typeof b === 'string'
  && timingSafeEqual(digest(a), digest(b));

export function validateTokens(value) {
  requireContract(value && tokenText(value.access_token) && tokenText(value.refresh_token)
    && value.token_type === 'Bearer' && value.scope === 'profile'
    && Number.isInteger(value.expires_in) && value.expires_in > 0 && value.expires_in <= 600, 'invalid_token_response');
  return { access_token: value.access_token, refresh_token: value.refresh_token,
    token_type: 'Bearer', scope: 'profile', expires_in: value.expires_in };
}

function localReturn(value) {
  requireContract(boundedText(value, 1024) && value.startsWith('/') && !value.startsWith('//')
    && !/[\\%#]/u.test(value), 'invalid_return_path');
  return value;
}

async function readJson(response) {
  requireContract(response.ok, `account_http_${response.status}`);
  requireContract((response.headers.get('content-type') || '').split(';')[0].trim() === 'application/json', 'invalid_response_type');
  requireContract(response.body, 'empty_account_response');
  const reader = response.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.length;
      requireContract(size <= MAX_BODY, 'account_response_too_large');
      chunks.push(value);
    }
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
  try { return JSON.parse(Buffer.concat(chunks).toString('utf8')); }
  catch { throw new ContractError('invalid_account_json'); }
}

/** flowStore must atomically create/take records scoped to a browser-session binding.
 * A shared durable store is required for multi-process BFFs; never put flows in URLs/cookies.
 */
export function createAccountClient({ registration, clientSecret, flowStore,
  fetchImpl = globalThis.fetch, now = Date.now, timeoutMs = 10_000 }) {
  const config = validateRegistration(registration);
  requireContract(typeof fetchImpl === 'function' && Number.isInteger(timeoutMs)
    && timeoutMs >= 1 && timeoutMs <= 30_000, 'invalid_transport');
  requireContract(flowStore && typeof flowStore.create === 'function'
    && typeof flowStore.take === 'function', 'flow_store_required');
  requireContract(config.type === 'confidential' ? tokenText(clientSecret) : clientSecret === undefined, 'invalid_client_secret');
  const fields = { client_id: config.clientId, audience: config.audience,
    ...(clientSecret ? { client_secret: clientSecret } : {}) };
  const bindingKey = binding => {
    requireContract(boundedText(binding) && binding.length >= 32, 'session_binding_required');
    return digest(binding).toString('hex');
  };

  async function request(path, body, accessToken) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetchImpl(config.issuer + path, {
        method: body ? 'POST' : 'GET', redirect: 'error', cache: 'no-store', credentials: 'omit',
        signal: controller.signal,
        headers: { Accept: 'application/json', ...(body ? { 'Content-Type': 'application/x-www-form-urlencoded' } : {}),
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}) },
        ...(body ? { body: new URLSearchParams(body).toString() } : {}),
      });
      try { return await readJson(response); }
      catch (error) {
        await response.body?.cancel().catch(() => {});
        throw error;
      }
    } catch (error) {
      if (error instanceof ContractError) throw error;
      // Do not propagate provider bodies, request URLs or credentials into logs.
      throw new ContractError(controller.signal.aborted ? 'account_timeout' : 'account_network_error');
    } finally { clearTimeout(timer); }
  }

  return Object.freeze({
    async discover() {
      return validateDiscovery(await request('/.well-known/lazyingart-account'), config.issuer);
    },
    async begin({ binding, returnTo = '/' }) {
      const sessionBinding = bindingKey(binding);
      localReturn(returnTo);
      const discovery = await this.discover();
      const state = randomBytes(32).toString('base64url');
      const verifier = randomBytes(32).toString('base64url');
      const flow = { state, verifier, binding: sessionBinding, returnTo, expiresAt: now() + FLOW_TTL,
        issuer: config.issuer, clientId: config.clientId, audience: config.audience, redirectUri: config.redirectUri };
      try { await flowStore.create(flow); }
      catch { throw new ContractError('session_storage_unavailable'); }
      const url = new URL(discovery.authorization_endpoint);
      url.search = new URLSearchParams({ response_type: 'code', client_id: config.clientId,
        audience: config.audience, redirect_uri: config.redirectUri, scope: 'profile', state,
        code_challenge: digest(verifier).toString('base64url'), code_challenge_method: 'S256' }).toString();
      return { url: url.href, expiresAt: flow.expiresAt };
    },
    async complete({ binding, callbackUrl }) {
      const sessionBinding = bindingKey(binding);
      requireContract(boundedText(callbackUrl, 8192), 'invalid_callback');
      let url;
      try { url = new URL(callbackUrl); } catch { throw new ContractError('invalid_callback'); }
      requireContract(!url.hash && !url.username && !url.password
        && callbackUrl.split('?')[0] === config.redirectUri, 'callback_mismatch');
      const allowed = new Set(['state', 'iss', 'code', 'error']);
      requireContract([...url.searchParams.keys()].every(key => allowed.has(key)
        && url.searchParams.getAll(key).length === 1), 'invalid_callback_parameters');
      const state = url.searchParams.get('state');
      requireContract(typeof state === 'string' && /^[A-Za-z0-9_-]{43}$/.test(state), 'invalid_state');
      let flow;
      try { flow = await flowStore.take(state, sessionBinding, now()); }
      catch { throw new ContractError('session_storage_unavailable'); }
      requireContract(flow && equals(flow.state, state) && equals(flow.binding, sessionBinding)
        && flow.expiresAt > now() && flow.expiresAt <= now() + FLOW_TTL
        && flow.issuer === config.issuer && flow.clientId === config.clientId
        && flow.audience === config.audience && flow.redirectUri === config.redirectUri
        && /^[A-Za-z0-9_-]{43}$/.test(flow.verifier), 'invalid_or_consumed_flow');
      requireContract(url.searchParams.get('iss') === config.issuer, 'callback_issuer_mismatch');
      requireContract(!(url.searchParams.has('code') && url.searchParams.has('error')), 'invalid_callback_parameters');
      localReturn(flow.returnTo);
      if (url.searchParams.has('error')) {
        requireContract(url.searchParams.get('error') === 'access_denied', 'authorization_failed');
        return { status: 'cancelled', returnTo: flow.returnTo };
      }
      const code = url.searchParams.get('code');
      requireContract(tokenText(code), 'invalid_code');
      const tokens = validateTokens(await request('/account/token', {
        ...fields, grant_type: 'authorization_code', code, redirect_uri: config.redirectUri, code_verifier: flow.verifier,
      }));
      try {
        const profile = await this.profile(tokens.access_token);
        return { status: 'authenticated', issuer: config.issuer, profile, tokens, returnTo: flow.returnTo };
      } catch (error) {
        await this.revoke(tokens.refresh_token).catch(() => {});
        throw error;
      }
    },
    async profile(accessToken) {
      requireContract(tokenText(accessToken), 'invalid_access_token');
      return validateProfile(await request('/account/profile', fields, accessToken), config.clientId);
    },
    async refresh(refreshToken) {
      requireContract(tokenText(refreshToken), 'invalid_refresh_token');
      return validateTokens(await request('/account/token', { ...fields, grant_type: 'refresh_token', refresh_token: refreshToken }));
    },
    async revoke(token) {
      requireContract(tokenText(token), 'invalid_revoke_token');
      const result = await request('/account/revoke', { ...fields, token });
      requireContract(result?.success === true, 'invalid_revoke_response');
    },
  });
}

/** claimRefresh must durably consume the old credential BEFORE network IO.
 * commitRefresh must compare the lease and refuse after logout/revocation.
 * A crash/lost response requires a new sign-in, never replaying the old token.
 */
export function createRefreshCoordinator({ client, vault }) {
  for (const method of ['claimRefresh', 'commitRefresh', 'requireSignIn']) {
    requireContract(typeof vault?.[method] === 'function', 'refresh_vault_required');
  }
  const active = new Map();
  return function refreshSession(sessionId) {
    requireContract(boundedText(sessionId), 'invalid_session_id');
    if (active.has(sessionId)) return active.get(sessionId);
    const operation = (async () => {
      let claim;
      try { claim = await vault.claimRefresh(sessionId); }
      catch { throw new ContractError('session_storage_unavailable'); }
      requireContract(claim?.status !== 'busy', 'refresh_in_progress');
      requireContract(claim && boundedText(claim.lease) && tokenText(claim.refreshToken), 'reauth_required');
      let tokens;
      try {
        tokens = validateTokens(await client.refresh(claim.refreshToken));
        requireContract(await vault.commitRefresh(sessionId, claim.lease, tokens) === true, 'session_changed');
        return { status: 'refreshed' };
      } catch {
        if (tokens) await client.revoke(tokens.refresh_token).catch(() => {});
        try { await vault.requireSignIn(sessionId, claim.lease); }
        catch { throw new ContractError('session_storage_unavailable'); }
        throw new ContractError('reauth_required');
      }
    })();
    active.set(sessionId, operation);
    const clear = () => { if (active.get(sessionId) === operation) active.delete(sessionId); };
    operation.then(clear, clear);
    return operation;
  };
}
