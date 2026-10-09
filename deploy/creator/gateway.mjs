import http from 'node:http';
import { isIP } from 'node:net';
import { readFile, open, realpath } from 'node:fs/promises';
import { constants } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { pathToFileURL } from 'node:url';
import { security, proxy } from './lazyedge.mjs';

const { assertSecretToken, constantTimeEqual, getSingleHeader, getRequestHost,
  normalizeMethod, parseRequestTarget, normalizeLoopbackUrl, RELAY_HEADER } = security;
const { proxyHttpRequest, sendJsonError, sanitizeRequestHeaders } = proxy;
export const CLIENT_AUTH = 'x-musia-client-authorization';
export const CLIENT_IP = 'x-musia-ingress-ip';
export const POLICY = Object.freeze(JSON.parse(await readFile(new URL('./policy.json', import.meta.url))));
const host = new URL(POLICY.origin).host;
const routes = POLICY.routes.map(([method, path]) => [method,
  new RegExp('^' + path.split('{id}').map(p => p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('[0-9a-f]{32}') + '$')]);

export function allowed(method, target) {
  const parsed = parseRequestTarget(target);
  normalizeMethod(method);
  return routes.some(([verb, pattern]) => method === verb && pattern.test(parsed.path));
}

// Open once with O_NOFOLLOW; values never enter argv, diagnostics or logs.
export async function privateText(path) {
  if (typeof path !== 'string' || resolve(path) !== await realpath(path)) throw new Error('Unsafe private file path');
  const file = await open(path, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const stat = await file.stat();
    // Some systemd versions use root:service-group 0440 credential mounts.
    // That exception is confined to the unit's actual protected credential dir.
    const credentialDir = process.env.CREDENTIALS_DIRECTORY;
    const mountedCredential = credentialDir && credentialDir.startsWith('/run/credentials/')
      && dirname(path) === credentialDir && await realpath(credentialDir) === credentialDir
      && stat.uid === 0 && [0, process.getgid()].includes(stat.gid) && (stat.mode & 0o777) === 0o440;
    if (!stat.isFile() || ((stat.mode & 0o077) && !mountedCredential) || ![0, process.getuid()].includes(stat.uid) || stat.size > 16384) {
      throw new Error('Private file must be owned, regular and mode 0600 or 0400');
    }
    return (await file.readFile('utf8')).replace(/\n$/, '');
  } finally { await file.close(); }
}

function rateLimiter() {
  const entries = new Map();
  return (ip, auth) => {
    const now = Date.now();
    for (const [key, value] of entries) if (now >= value.until) entries.delete(key);
    let entry = entries.get(ip);
    if (!entry) {
      if (entries.size >= POLICY.maxRateEntries) return false;
      entry = { until: now + POLICY.rateWindowMs, general: 0, auth: 0 };
      entries.set(ip, entry);
    }
    entry.general += 1;
    if (auth) entry.auth += 1;
    return entry.general <= POLICY.generalRequestsPerIP && entry.auth <= POLICY.authRequestsPerIP;
  };
}

function clientBearer(request) {
  const value = getSingleHeader(request, CLIENT_AUTH);
  if (value === null && request.headers[CLIENT_AUTH] !== undefined) throw new Error('Duplicate native credential');
  if (value && !/^Bearer [A-Za-z0-9._~+/-]{1,249}={0,2}$/.test(value)) throw new Error('Malformed native credential');
  if (value && value.length > 256) throw new Error('Oversized native credential');
  return value || null;
}

export async function startGuard({ role, relayToken, upstreamToken, target,
  port = role === 'edge' ? 18896 : 18898, timeoutMs = POLICY.timeoutMs } = {}) {
  if (!['edge', 'worker'].includes(role)) throw new Error('Invalid guard role');
  assertSecretToken(relayToken);
  if (role === 'edge' && upstreamToken !== undefined) throw new Error('Upstream credential is worker-only');
  if (role === 'worker') {
    assertSecretToken(upstreamToken);
    if (constantTimeEqual(relayToken, upstreamToken)) throw new Error('Transport credentials must differ');
  }
  target = normalizeLoopbackUrl(target ?? (role === 'edge' ? 'http://127.0.0.1:18897' : 'http://127.0.0.1:8797'));
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > POLICY.timeoutMs) throw new Error('Invalid deadline');
  const permitRate = rateLimiter();
  let concurrent = 0;
  const sockets = new Set();
  const server = http.createServer({ maxHeaderSize: 16384 }, async (request, response) => {
    const deny = (status, code) => { sendJsonError(response, status, code); request.resume(); };
    try {
      // Caddy removes raw Authorization. No user bearer is ever a transport token.
      if (request.headers.authorization !== undefined) return deny(400, 'raw_authorization_forbidden');
      if (role === 'worker') {
        const relay = getSingleHeader(request, RELAY_HEADER);
        if (!relay || !constantTimeEqual(relay, `Bearer ${relayToken}`)) return deny(401, 'unauthorized_relay');
      }
      if (getRequestHost(request) !== host || ![host, `${host}:443`].includes(getSingleHeader(request, 'host'))) {
        return deny(400, 'invalid_host');
      }
      const parsed = parseRequestTarget(request.url);
      const ip = getSingleHeader(request, CLIENT_IP);
      if (!ip || !isIP(ip)) return deny(400, 'invalid_ingress_ip');
      if (!permitRate(ip, parsed.path.startsWith('/creator/auth/'))) return deny(429, 'rate_limited');
      if (!allowed(request.method, request.url)) return deny(404, 'route_not_allowed');
      const native = clientBearer(request);
      if (native && (constantTimeEqual(native, `Bearer ${relayToken}`) ||
          (upstreamToken && constantTimeEqual(native, `Bearer ${upstreamToken}`)))) return deny(401, 'transport_is_not_session');
      if (concurrent >= POLICY.maxConcurrentRequests) return deny(429, 'too_many_requests');
      // Sanitize before reinjecting only the values owned by this hop. In particular,
      // client-supplied x-musia-* and x-lazyedge-* transport headers cannot survive.
      const safe = sanitizeRequestHeaders(request.headers, {}, { forwardCookies: true });
      for (const key of Object.keys(safe)) if (key.startsWith('x-musia-') && key !== 'x-musia-request') delete safe[key];
      request.headers = safe;
      const injectHeaders = { host, [CLIENT_IP]: ip };
      if (native) injectHeaders[CLIENT_AUTH] = native;
      if (role === 'edge') injectHeaders[RELAY_HEADER] = `Bearer ${relayToken}`;
      else injectHeaders.authorization = `Bearer ${upstreamToken}`;
      concurrent += 1;
      // LazyEdge's timeout is an idle timeout. Add a wall-clock deadline so a
      // trickling upload/stream cannot hold one of the 32 slots indefinitely.
      const deadline = setTimeout(() => {
        sendJsonError(response, 503, 'request_deadline');
        // proxyHttpRequest owns the upstream handles and cleans them on aborted.
        // Emit even for a complete request whose response is still streaming.
        request.emit('aborted');
        if (!request.complete) request.destroy();
      }, timeoutMs);
      deadline.unref();
      // Never reflect dedicated credentials even if an upstream sets such headers.
      const writeHead = response.writeHead;
      response.writeHead = function (status, reason, headers) {
        if (typeof reason === 'object') { headers = reason; reason = undefined; }
        for (const key of Object.keys(headers ?? {})) {
          if (key.toLowerCase().startsWith('x-musia-') && key.toLowerCase() !== 'x-musia-request') delete headers[key];
        }
        return reason === undefined ? writeHead.call(this, status, headers) : writeHead.call(this, status, reason, headers);
      };
      try {
        await proxyHttpRequest(request, response, { target, injectHeaders, maxBodyBytes: POLICY.maxBodyBytes,
          timeoutMs, forwardCookies: true, unavailableStatusCode: 503 });
      } finally { clearTimeout(deadline); concurrent -= 1; }
    } catch { deny(400, 'invalid_request'); }
  });
  server.headersTimeout = 10000;
  server.requestTimeout = POLICY.timeoutMs;
  server.keepAliveTimeout = 1000;
  server.maxHeadersCount = 64;
  server.on('connection', socket => {
    sockets.add(socket);
    socket.setTimeout(POLICY.timeoutMs, () => socket.destroy());
    socket.once('close', () => sockets.delete(socket));
  });
  server.on('clientError', (_error, socket) => socket.end('HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n'));
  server.on('upgrade', (_request, socket) => socket.end('HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n'));
  server.on('connect', (_request, socket) => socket.end('HTTP/1.1 405 Method Not Allowed\r\nConnection: close\r\n\r\n'));
  await new Promise((ok, fail) => { server.once('error', fail); server.listen(port, '127.0.0.1', ok); });
  return { server, port: server.address().port, close: () => new Promise(ok => {
    server.close(ok);
    for (const socket of sockets) socket.destroy();
  }) };
}

async function main() {
  const binding = JSON.parse(await privateText(process.argv[2]));
  const fields = binding.role === 'worker' ? ['role', 'relaySecretFile', 'upstreamSecretFile'] : ['role', 'relaySecretFile'];
  if (Object.keys(binding).sort().join() !== fields.sort().join()) throw new Error('Invalid role binding');
  const relayToken = await privateText(binding.relaySecretFile);
  const upstreamToken = binding.role === 'worker' ? await privateText(binding.upstreamSecretFile) : undefined;
  const guard = await startGuard({ role: binding.role, relayToken, upstreamToken });
  for (const signal of ['SIGTERM', 'SIGINT']) process.once(signal, () => guard.close().then(() => process.exit(0)));
  process.stdout.write(`creator-${binding.role} listening on 127.0.0.1:${guard.port}\n`);
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch(() => { process.stderr.write('Creator guard startup refused\n'); process.exitCode = 1; });
}
