import http from 'node:http';
import { timingSafeEqual } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { createProducer, secret, validateRequest, validateReply } from './producer.mjs';

export function createServer({token, produce, deadlineMs = 70000}) {
  if (!/^[A-Za-z0-9_-]{32,128}$/.test(token)) throw new Error('Invalid RPC credential');
  let running = false;
  const send = (res, status, body) => {
    if (res.destroyed) return;
    res.writeHead(status, {'content-type': 'application/json', 'cache-control': 'no-store'});
    res.end(JSON.stringify(body));
  };
  const server = http.createServer(async (req, res) => {
    if (req.method === 'GET' && req.url === '/healthz') return send(res, 200, {ok: true});
    const supplied = Buffer.from(req.headers.authorization || '');
    const expected = Buffer.from(`Bearer ${token}`);
    if (supplied.length !== expected.length || !timingSafeEqual(supplied, expected)) return send(res, 401, {error: 'unauthorized'});
    if (req.method !== 'POST' || req.url !== '/v1/refine') return send(res, 404, {error: 'not_found'});
    if ((req.headers['content-type'] || '').split(';')[0] !== 'application/json') return send(res, 415, {error: 'json_required'});
    if (running) return send(res, 429, {error: 'busy'});
    running = true;
    const controller = new AbortController();
    const onClose = () => { if (!res.writableEnded) controller.abort(); };
    res.on('close', onClose);
    const timer = setTimeout(() => { controller.abort(); send(res, 504, {error: 'deadline'}); req.destroy(); }, deadlineMs);
    try {
      let length = 0; const chunks = [];
      for await (const chunk of req) {
        length += chunk.length;
        if (length > 48000) { send(res, 413, {error: 'body_too_large'}); return; }
        chunks.push(chunk);
      }
      let body;
      try { body = JSON.parse(Buffer.concat(chunks)); }
      catch { return send(res, 400, {error: 'invalid_json'}); }
      if (!validateRequest(body)) return send(res, 400, {error: 'invalid_request'});
      const answer = await produce(body, controller.signal);
      if (controller.signal.aborted) return;
      if (!validateReply(answer) || Buffer.byteLength(JSON.stringify(answer)) > 65536) throw new Error('Invalid reply');
      send(res, 200, answer);
    } catch {
      if (!res.writableEnded) send(res, 503, {error: 'agent_unavailable'});
    } finally {
      clearTimeout(timer); res.off('close', onClose); running = false;
    }
  });
  server.requestTimeout = 80000;
  server.headersTimeout = 5000;
  server.keepAliveTimeout = 1000;
  server.maxConnections = 8;
  return server;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const token = await secret(process.env.MUSIA_AGENT_TOKEN_FILE);
    const key = await secret(process.env.MUSIA_AGENT_KEY_FILE);
    const produce = createProducer({key, model: process.env.MUSIA_AGENT_MODEL, proxy: process.env.MUSIA_AGENT_PROXY});
    const server = createServer({token, produce});
    server.listen(8081, '0.0.0.0');
    process.on('SIGTERM', () => { server.close(() => process.exit(0)); setTimeout(() => process.exit(1), 75000).unref(); });
  } catch {
    console.error('Musia agent configuration failed; inspect private configuration, not user prompts.');
    process.exit(1);
  }
}
