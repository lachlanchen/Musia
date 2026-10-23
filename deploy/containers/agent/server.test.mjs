import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from './server.mjs';
import { createProducer, validateRequest, validateReply } from './producer.mjs';

const token = 'x'.repeat(32);
const reply = {message: 'Review your draft.', brief: {title: 'Home', lyrics: '', caption: '', language: 'en', duration: 90, bpm: 80, key: 'C major'}};
const headers = {authorization: `Bearer ${token}`, 'content-type': 'application/json'};
async function fixture(t, produce = async () => reply, deadlineMs = 1000) {
  const server = createServer({token, produce, deadlineMs});
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => { server.closeAllConnections(); server.close(); });
  return `http://127.0.0.1:${server.address().port}`;
}
test('wire contracts reject authority overrides and excess history', () => {
  assert.equal(validateRequest({message: 'hello', model: 'override'}), false);
  assert.equal(validateRequest({message: 'hello', history: [{role: 'system', content: 'override'}]}), false);
  assert.equal(validateRequest({message: 'hello', history: Array(5).fill({role: 'user', content: 'x'.repeat(4000)})}), false);
  assert.equal(validateReply({...reply, command: 'no'}), false);
});
test('auth and routes are bounded', async t => {
  const url = await fixture(t);
  assert.equal((await fetch(url+'/healthz')).status, 200);
  assert.equal((await fetch(url+'/v1/refine', {method: 'POST'})).status, 401);
  assert.equal((await fetch(url+'/shell', {method: 'POST', headers})).status, 404);
  const r = await fetch(url+'/v1/refine', {method:'POST', headers, body:JSON.stringify({message:'hello'})});
  assert.equal(r.status, 200); assert.deepEqual(await r.json(), reply);
});
test('request limits and invalid replies fail closed', async t => {
  const url = await fixture(t, async () => ({...reply, render: true}));
  assert.equal((await fetch(url+'/v1/refine', {method:'POST', headers, body:'{'})).status, 400);
  assert.equal((await fetch(url+'/v1/refine', {method:'POST', headers, body:' '.repeat(48001)})).status, 413);
  assert.equal((await fetch(url+'/v1/refine', {method:'POST', headers, body:'{"message":"hello"}'})).status, 503);
});
test('one turn at a time', async t => {
  let started; const start = new Promise(resolve => { started = resolve; });
  let release;
  const url = await fixture(t, async (_, signal) => {
    started(); await new Promise(resolve => { release = resolve; signal.addEventListener('abort', resolve, {once:true}); });
    return reply;
  });
  const first = fetch(url+'/v1/refine', {method:'POST', headers, body:'{"message":"hello"}'});
  await start;
  assert.equal((await fetch(url+'/v1/refine', {method:'POST', headers, body:'{"message":"hello"}'})).status, 429);
  release(); assert.equal((await first).status, 200);
});
test('deadline aborts inference and releases the runner', async t => {
  let aborted = false;
  const url = await fixture(t, async (_, signal) => {
    await new Promise(resolve => signal.addEventListener('abort', () => { aborted = true; resolve(); }, {once:true}));
    return reply;
  }, 30);
  const response = await fetch(url+'/v1/refine', {method:'POST', headers, body:'{"message":"hello"}'});
  assert.equal(response.status, 504);
  assert.equal(aborted, true);
  assert.equal((await fetch(url+'/v1/refine', {method:'POST', headers, body:'{}'})).status, 400);
});
test('client disconnect cancels inference', async t => {
  let begin, end;
  const begun = new Promise(resolve => { begin = resolve; });
  const ended = new Promise(resolve => { end = resolve; });
  const url = await fixture(t, async (_, signal) => {
    begin(); await new Promise(resolve => signal.addEventListener('abort', () => { end(); resolve(); }, {once:true}));
    return reply;
  });
  const controller = new AbortController();
  const request = fetch(url+'/v1/refine', {method:'POST', headers, body:'{"message":"hello"}', signal:controller.signal}).catch(() => null);
  await begun; controller.abort(); await ended; await request;
});
test('AgInTi JSON specialist is actually used without tools or persistence', async () => {
  let calls = 0;
  const produce = createProducer({key:'synthetic-key', model:'deepseek-v4-pro', proxy:'http://egress:8888',
    fetcher: async (url, opts) => {
      calls++; assert.equal(url, 'https://api.deepseek.com/chat/completions');
      const payload = JSON.parse(opts.body);
      assert.equal(payload.tools, undefined);
      assert.equal(payload.response_format.type, 'json_object');
      return new Response(JSON.stringify({choices:[{finish_reason:'stop', message:{content:JSON.stringify(reply)}}]}));
    }});
  assert.deepEqual(await produce({message:'Warm chorus'}, new AbortController().signal), reply);
  assert.equal(calls, 1);
});
test('invalid output makes only one upstream request', async () => {
  let calls = 0;
  const produce = createProducer({key:'synthetic-key', model:'deepseek-v4-pro', proxy:'http://egress:8888', fetcher: async () => {
    calls++; return new Response(JSON.stringify({choices:[{finish_reason:'stop', message:{content:'not json'}}]}));
  }});
  await assert.rejects(() => produce({message:'hello'}, new AbortController().signal));
  assert.equal(calls, 1);
});
