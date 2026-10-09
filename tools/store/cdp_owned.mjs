#!/usr/bin/env node
// Scoped fallback when shared-browser context discovery stalls on unrelated tabs.
// Only operate a target ID retained by this task. Never restart the shared browser.
import { readFileSync } from 'node:fs';
const [target, expectedOrigin] = process.argv.slice(2);
if (!/^[A-F0-9]{32}$/.test(target ?? '') || !expectedOrigin?.startsWith('https://')) throw Error('Target and exact origin required');
const pages = await (await fetch('http://127.0.0.1:9485/json/list')).json();
const page = pages.find(p => p.id === target && p.type === 'page');
if (!page || new URL(page.url).origin !== expectedOrigin) throw Error('Owned target changed origin');
const expression = readFileSync(0, 'utf8');
const ws = new WebSocket(page.webSocketDebuggerUrl);
const timer = setTimeout(() => { ws.close(); process.exitCode = 2; }, 20000);
ws.onopen = () => ws.send(JSON.stringify({id:1, method:'Runtime.evaluate', params:{expression, returnByValue:true, awaitPromise:true}}));
ws.onerror = () => { clearTimeout(timer); process.exitCode = 1; };
ws.onmessage = event => {
  const result = JSON.parse(event.data);
  if (result.id !== 1) return;
  clearTimeout(timer);
  console.log(JSON.stringify(result.result ?? result.error));
  if (result.error || result.result?.exceptionDetails) process.exitCode = 1;
  ws.close();
};
