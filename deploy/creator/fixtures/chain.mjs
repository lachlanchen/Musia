// Test-only Caddy and SSH stand-ins. All listeners use ephemeral loopback ports.
import http from 'node:http';
import net from 'node:net';
import readline from 'node:readline';
import { startGuard, CLIENT_AUTH, CLIENT_IP } from '../gateway.mjs';
import { proxy } from '../lazyedge.mjs';
const lines = readline.createInterface({ input: process.stdin });
const config = JSON.parse(await new Promise(ok => lines.once('line', ok)));
const worker = await startGuard({ role: 'worker', relayToken: config.relay, upstreamToken: config.upstream,
  target: config.target, port: 0, timeoutMs: config.timeoutMs });
const sockets = new Set();
const tunnel = net.createServer(client => {
  const upstream = net.connect(worker.port, '127.0.0.1');
  for (const socket of [client, upstream]) {
    sockets.add(socket);
    socket.on('error', () => { client.destroy(); upstream.destroy(); });
    socket.on('close', () => { sockets.delete(socket); client.destroy(); upstream.destroy(); });
  }
  client.pipe(upstream).pipe(client);
});
await new Promise(ok => tunnel.listen(0, '127.0.0.1', ok));
const tunnelPort = tunnel.address().port;
const edge = await startGuard({ role: 'edge', relayToken: config.relay,
  target: `http://127.0.0.1:${tunnelPort}`, port: 0, timeoutMs: config.timeoutMs });
const ingress = http.createServer((req, res) => {
  const native = req.headers.authorization;
  delete req.headers[CLIENT_AUTH];
  delete req.headers[CLIENT_IP];
  const injectHeaders = { host: req.headers.host, [CLIENT_IP]: req.socket.remoteAddress };
  if (native) injectHeaders[CLIENT_AUTH] = native;
  try {
    proxy.proxyHttpRequest(req, res, { target: `http://127.0.0.1:${edge.port}`, injectHeaders,
      forwardCookies: true, maxBodyBytes: 100000, timeoutMs: config.timeoutMs + 500 }).catch(() => res.destroy());
  } catch { proxy.sendJsonError(res, 400, 'invalid_request'); req.resume(); }
});
await new Promise(ok => ingress.listen(0, '127.0.0.1', ok));
process.stdout.write(JSON.stringify({ ingress: ingress.address().port, edge: edge.port,
  worker: worker.port, tunnel: tunnelPort }) + '\n');
lines.on('line', async line => {
  if (line === 'drop') {
    for (const socket of sockets) socket.destroy();
    await new Promise(ok => tunnel.close(ok));
    process.stdout.write('dropped\n');
  } else if (line === 'restore') {
    await new Promise(ok => tunnel.listen(tunnelPort, '127.0.0.1', ok));
    process.stdout.write('restored\n');
  } else if (line === 'stop') {
    ingress.closeAllConnections();
    await new Promise(ok => ingress.close(ok));
    await edge.close();
    for (const socket of sockets) socket.destroy();
    if (tunnel.listening) await new Promise(ok => tunnel.close(ok));
    await worker.close();
    lines.close();
    process.exit(0);
  }
});
