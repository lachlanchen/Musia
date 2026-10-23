import { readFile } from 'node:fs/promises';
import Ajv from 'ajv';
import { runJsonSpecialist } from '@lazyingart/agintiflow/src/json-specialist.js';
import { ProxyAgent, fetch } from 'undici';

export const contract = JSON.parse(await readFile(new URL('./contract.json', import.meta.url), 'utf8'));
const ajv = new Ajv({strict: false, allErrors: false});
const requestValid = ajv.compile(contract.request);
const replyValid = ajv.compile(contract.reply);
export function validateRequest(body) {
  return requestValid(body) && (body.history || []).reduce((n, m) => n + m.content.length, 0) <= 16000;
}
export function validateReply(body) { return replyValid(body); }

export async function secret(path) {
  if (!path) throw new Error('Missing private credential file');
  const value = await readFile(path, 'utf8');
  if (!value.trim() || value.length > 8192 || /[\r\n\0]/.test(value.trim())) throw new Error('Invalid private credential');
  return value.trim();
}

export function createProducer({key, model, proxy, specialist = runJsonSpecialist, fetcher = fetch}) {
  if (!key || !/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,100}$/.test(model || '')) throw new Error('Invalid provider configuration');
  if (proxy !== 'http://egress:8888') throw new Error('Use the fixed restricted egress proxy');
  const dispatcher = new ProxyAgent(proxy);
  return async (request, signal) => {
    if (!validateRequest(request)) throw new Error('invalid_request');
    // AgInTi owns schema prompting/validation. This adapter supplies only a
    // bounded text transport, not its shell/browser/runtime or persistent store.
    const client = {chat: {completions: {create: async (payload) => {
      if (signal.aborted) throw new Error('cancelled');
      const response = await fetcher('https://api.deepseek.com/chat/completions', {
        dispatcher, signal, method: 'POST', redirect: 'error',
        headers: {'content-type': 'application/json', authorization: `Bearer ${key}`},
        body: JSON.stringify({...payload, model, stream: false}),
      });
      if (!response.ok) { await response.body?.cancel(); throw new Error('provider_unavailable'); }
      const chunks = []; let length = 0;
      for await (const chunk of response.body) {
        length += chunk.length;
        if (length > 65536) throw new Error('response_too_large');
        chunks.push(chunk);
      }
      const value = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      const choice = value?.choices?.[0];
      if (choice?.finish_reason !== 'stop' || choice?.message?.tool_calls || choice?.message?.refusal) throw new Error('invalid_response');
      return value;
    }}}};
    const result = await specialist({
      task: contract.system, input: request, schema: contract.reply,
      schemaName: 'musia_song_draft', responseFormat: 'json_object',
      fallbackOnInvalid: false, maxTokens: 3500, thinkingMode: 'disabled',
    }, {provider: 'deepseek', model, apiKey: key, baseURL: 'https://api.deepseek.com',
      modelTimeoutMs: 65000, abortSignal: signal, jsonClientFactory: () => client}, null);
    if (signal.aborted || !result.ok || !validateReply(result.result)) throw new Error('invalid_response');
    return result.result;
  };
}
