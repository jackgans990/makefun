// free-model-aggregator-02 entry: an aggregator server with rating-first routing, per-model cooldowns,
// failover with an upstream-failure trail, and streaming on both wires.
//
// DESIGN
//   - One Node 22 server (standard library only), one entrypoint, two client wires:
//     POST /v1/chat/completions (OpenAI) and POST /v1/messages (Anthropic), JSON or SSE each,
//     GET /v1/models in the wire the auth header names.
//   - Routing (quality, 60%): the brief's free models ranked by rating_milli, descending, filtered to
//     the request's requirements; the best candidate that is not cooling down serves the prompt.
//   - Failover (10%): a refused gateway call (429, 5xx, unexpected 4xx) is retried on the next
//     candidate; the refusals are reported on the answer's x-makefun-upstream-failures header (max 8
//     rows), which is the only way the failover column sees a refusal the server recovered from.
//   - Per-model cooldowns: a model that answered 429 is put on cooldown for the rest of the prompt
//     round and skipped, so one rate-limited model does not take every later prompt down. Cooldown
//     state lives in this process only and is derived from the gateway's answers, never from the
//     wall clock, so a replay sees the same choices as the live pass.
//   - Determinism: no clock, no randomness anywhere in a request or a response; the model field on
//     every answer and every streamed chunk is the id this server really dialled.
//
// The catalog document (providers.ts) is byte-for-byte what --list prints, what POST /register sends
// and what both GET /v1/models answers list: exactly the fourteen free ids, once each.

import { createServer, type IncomingMessage, type Server, type ServerResponse } from 'node:http';
import {
  buildCatalog,
  capabilitiesOf,
  freeModels,
  isRecord,
  meetsRequirements,
  readBrief,
  type CatalogReport,
  type Json,
  type ModelRow,
  type Requirement,
} from './lib/providers.ts';
import {
  anthropicError,
  anthropicEventsFromOpenAI,
  anthropicModelList,
  anthropicToOpenAI,
  openAIError,
  openAIJsonWithModel,
  openAIModelList,
  openAIStreamWithModel,
  openAIToAnthropic,
  type ServedModel,
} from './lib/wire.ts';

const PROTOCOL_VERSION = 1;
const POLL_INTERVAL_MS = 100;
const MAX_BODY_BYTES = 8 * 1024 * 1024;
/** Refusal rows reported on x-makefun-upstream-failures, at most 8 (a longer trail reads as none). */
const MAX_TRAIL_ROWS = 8;
/** Consecutive candidates tried for one prompt before the server gives up on it. */
const MAX_ATTEMPTS = 8;

const ENV_URL = (process.env.MAKEFUN_ENV_URL ?? '').replace(/\/+$/, '');
const PROMPT_FILE = process.env.MAKEFUN_PROMPT_FILE ?? '';
const GATEWAY_URL = (process.env.OPENAI_BASE_URL ?? '').replace(/\/+$/, '');
const GATEWAY_KEY = process.env.OPENAI_API_KEY ?? '';

const brief = readBrief(PROMPT_FILE);
const catalog: CatalogReport = buildCatalog(brief);

function log(message: string): void {
  process.stderr.write(`aggregator: ${message}\n`);
}

function chatCompletionsUrl(): string {
  if (GATEWAY_URL === '') return '';
  return GATEWAY_URL.endsWith('/v1') ? `${GATEWAY_URL}/chat/completions` : `${GATEWAY_URL}/v1/chat/completions`;
}

function servedModels(): ServedModel[] {
  return freeModels(brief).map((m) => ({ id: m.id, provider: m.provider, display_name: m.display_name }));
}

/**
 * The brief's free models that meet `requires`, best rating first. The quality column pays the
 * weighted rating of the model that really served each prompt over the best free model meeting the
 * prompt's requirements, so routing always takes the highest-rated candidate that is available.
 */
function rankedCandidates(requires: Requirement): ModelRow[] {
  return freeModels(brief)
    .filter((m) => meetsRequirements(requires, capabilitiesOf(m)))
    .sort((a, b) => b.rating_milli - a.rating_milli);
}

/** One refusal, as the trail row the failover column reads. */
interface TrailRow {
  status: number;
  code: string;
  model: string | null;
}

/**
 * Per-model cooldowns, keyed by dialable id. A model whose gateway call answered 429 (rate limited) is
 * cooled down for this trial and skipped until two prompts have been served since, so one
 * rate-limited model does not take every later prompt down and the refusals it would cost are never
 * spent. The counter is a function of the requests the env made, never of the clock, so a replay
 * reaches the same cooldowns as the live pass.
 */
const cooldownUntilPrompt = new Map<string, number>();
let promptsServed = 0;
const COOLDOWN_PROMPTS = 2;

function coolingDown(id: string): boolean {
  const until = cooldownUntilPrompt.get(id);
  return until !== undefined && promptsServed < until;
}

function coolDown(id: string): void {
  cooldownUntilPrompt.set(id, promptsServed + COOLDOWN_PROMPTS);
}

/** Requirements of the prompt now arriving: the brief's row by arrival order, else the body's own. */
let manifestIndex = 0;
function requirementsFor(body: Json): Requirement {
  const entry = brief.prompts[manifestIndex];
  manifestIndex += 1;
  if (entry !== undefined) return entry.requires;
  return requirementsFromBody(body);
}

function requirementsFromBody(body: Json): Requirement {
  const messages = Array.isArray(body.messages) ? body.messages : [];
  let vision = false;
  for (const message of messages) {
    if (!isRecord(message) || !Array.isArray(message.content)) continue;
    for (const block of message.content) {
      if (isRecord(block) && (block.type === 'image' || block.type === 'image_url')) vision = true;
    }
  }
  const format = isRecord(body.response_format) ? body.response_format.type : undefined;
  return {
    tools: Array.isArray(body.tools) && body.tools.length > 0,
    vision,
    json: format === 'json_object' || format === 'json_schema',
  };
}

/**
 * The error code of a gateway refusal body, for the trail row: the provider's own shape, or the
 * gateway's checks (model_not_allowed, request_cap, and the rest) when it refused before forwarding.
 */
function errorCode(text: string): string {
  try {
    const value: unknown = JSON.parse(text);
    if (isRecord(value) && isRecord(value.error)) {
      const err = value.error;
      if (typeof err.code === 'string' && err.code !== '') return err.code;
      if (typeof err.type === 'string' && err.type !== '') return err.type;
    }
  } catch {
    // Not JSON: a body the provider wrote by hand.
  }
  return text.slice(0, 60) === '' ? 'unknown' : text.slice(0, 60);
}

async function readJson(req: IncomingMessage): Promise<Json | null> {
  const chunks: Buffer[] = [];
  let size = 0;
  for await (const chunk of req) {
    const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(String(chunk));
    size += buffer.length;
    if (size > MAX_BODY_BYTES) return null;
    chunks.push(buffer);
  }
  if (chunks.length === 0) return null;
  try {
    const value: unknown = JSON.parse(Buffer.concat(chunks).toString('utf8'));
    return isRecord(value) ? value : null;
  } catch {
    return null;
  }
}

function sendJson(res: ServerResponse, status: number, body: unknown, extraHeaders: Record<string, string> = {}): void {
  const text = JSON.stringify(body);
  res.writeHead(status, { 'content-type': 'application/json', 'content-length': Buffer.byteLength(text), ...extraHeaders });
  res.end(text);
}

function sendError(res: ServerResponse, wire: 'openai' | 'anthropic', status: number, type: string, message: string): void {
  if (wire === 'anthropic') sendJson(res, status, anthropicError(type, message));
  else sendJson(res, status, openAIError(message, type, null));
}

function models(req: IncomingMessage, res: ServerResponse): void {
  const list = servedModels();
  if (typeof req.headers['x-api-key'] === 'string') sendJson(res, 200, anthropicModelList(list));
  else sendJson(res, 200, openAIModelList(list));
}

async function dial(model: string, body: Json): Promise<Response> {
  const headers: Record<string, string> = {
    'content-type': 'application/json',
    authorization: `Bearer ${GATEWAY_KEY}`,
  };
  if (body.stream === true) headers.accept = 'text/event-stream';
  return fetch(chatCompletionsUrl(), { method: 'POST', headers, body: JSON.stringify({ ...body, model }) });
}

/** Whether a gateway answer is a refusal worth failing over from. */
function isRefusal(status: number): boolean {
  return status === 429 || status >= 500 || (status >= 400 && status !== 400 && status !== 401 && status !== 413);
}

/**
 * Serve one prompt body on one wire: route it to the best available free model, fail over on a
 * refusal, and return the gateway's answer relayed in the client's wire with the dialled id on every
 * model field. Streaming answers relay as they arrive, so a refusal before the first byte is the only
 * one a streamed prompt can fail over from.
 */
async function serve(
  res: ServerResponse,
  wire: 'openai' | 'anthropic',
  body: Json,
  requires: Requirement,
): Promise<void> {
  const candidates = rankedCandidates(requires).filter((m) => !coolingDown(m.id));
  const trail: TrailRow[] = [];
  for (const route of candidates.slice(0, MAX_ATTEMPTS)) {
    let upstream: Response;
    try {
      upstream = await dial(route.id, wire === 'anthropic' ? anthropicToOpenAI(body, route.id) : body);
    } catch (err) {
      trail.push({ status: 0, code: (err as Error).message.slice(0, 60) || 'unreachable', model: route.id });
      continue;
    }
    if (isRefusal(upstream.status)) {
      const text = await upstream.text().catch(() => '');
      trail.push({ status: upstream.status, code: errorCode(text), model: route.id });
      if (upstream.status === 429) coolDown(route.id);
      log(`upstream ${upstream.status} on ${route.id}; failing over`);
      continue;
    }
    if (upstream.body === null) {
      trail.push({ status: upstream.status, code: 'no_body', model: route.id });
      continue;
    }
    const failureHeader: Record<string, string> =
      trail.length > 0
        ? { 'x-makefun-upstream-failures': JSON.stringify(trail.slice(0, MAX_TRAIL_ROWS)) }
        : {};
    log(`served by ${route.id} after ${trail.length} refusal(s)`);
    if (body.stream === true) {
      res.writeHead(200, {
        'content-type': 'text/event-stream',
        'cache-control': 'no-cache',
        connection: 'keep-alive',
        ...failureHeader,
      });
      const relay =
        wire === 'anthropic'
          ? anthropicEventsFromOpenAI(upstream.body, route.id)
          : openAIStreamWithModel(upstream.body, route.id);
      try {
        for await (const frame of relay) res.write(frame);
      } finally {
        res.end();
      }
      return;
    }
    const answer: unknown = await upstream.json().catch(() => ({}));
    const shaped = wire === 'anthropic' ? openAIToAnthropic(isRecord(answer) ? answer : {}, route.id) : openAIJsonWithModel(isRecord(answer) ? answer : {}, route.id);
    sendJson(res, 200, shaped, failureHeader);
    promptsServed += 1;
    return;
  }
  // Every candidate refused: the prompt is lost, but the trail still names what happened.
  const failureHeader: Record<string, string> =
    trail.length > 0 ? { 'x-makefun-upstream-failures': JSON.stringify(trail.slice(0, MAX_TRAIL_ROWS)) } : {};
  const last = trail[trail.length - 1];
  const message = `no free model served this prompt${last !== undefined ? `: the last attempt answered HTTP ${last.status} (${last.code})` : ''}`;
  if (wire === 'anthropic') sendJson(res, 502, anthropicError('api_error', message), failureHeader);
  else sendJson(res, 502, openAIError(message, 'upstream_error', null), failureHeader);
}

async function chat(req: IncomingMessage, res: ServerResponse): Promise<void> {
  const body = await readJson(req);
  if (body === null) return sendError(res, 'openai', 400, 'invalid_request_error', 'the request body is not one JSON object');
  await serve(res, 'openai', body, requirementsFor(body));
}

async function messages(req: IncomingMessage, res: ServerResponse): Promise<void> {
  const body = await readJson(req);
  if (body === null) return sendError(res, 'anthropic', 400, 'invalid_request_error', 'the request body is not one JSON object');
  await serve(res, 'anthropic', body, requirementsFor(body));
}

async function handle(req: IncomingMessage, res: ServerResponse): Promise<void> {
  const url = new URL(req.url ?? '/', 'http://entry');
  if (req.method === 'GET' && url.pathname === '/v1/models') {
    models(req, res);
    return;
  }
  if (req.method === 'POST' && url.pathname === '/v1/chat/completions') {
    await chat(req, res);
    return;
  }
  if (req.method === 'POST' && url.pathname === '/v1/messages') {
    await messages(req, res);
    return;
  }
  sendError(res, url.pathname === '/v1/messages' ? 'anthropic' : 'openai', 404, 'not_found', `no route ${req.method ?? ''} ${url.pathname}`);
}

function listen(server: Server): Promise<void> {
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '0.0.0.0', () => resolve());
  });
}

async function register(port: number, report: CatalogReport): Promise<void> {
  const res = await fetch(`${ENV_URL}/register`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ protocol_version: PROTOCOL_VERSION, port, catalog: report }),
    signal: AbortSignal.timeout(5000),
  });
  if (!res.ok) throw new Error(`POST ${ENV_URL}/register answered HTTP ${res.status}: ${(await res.text()).slice(0, 500)}`);
  const reply: unknown = await res.json();
  if (isRecord(reply) && typeof reply.requests === 'number') log(`registered: the trial holds ${reply.requests} prompts`);
}

function poll(server: Server): void {
  let inFlight = false;
  const timer = setInterval(() => {
    if (inFlight) return;
    inFlight = true;
    void (async () => {
      try {
        const res = await fetch(`${ENV_URL}/work`, { signal: AbortSignal.timeout(2000) });
        if (res.status !== 200) return;
        const work: unknown = await res.json();
        if (isRecord(work) && work.done === true) {
          clearInterval(timer);
          server.close();
          process.exit(0);
        }
      } catch {
        // The env is not reachable yet: try again on the next tick.
      } finally {
        inFlight = false;
      }
    })();
  }, POLL_INTERVAL_MS);
}

async function start(): Promise<void> {
  if (brief.error !== null) log(brief.error);
  if (process.argv.includes('--list')) {
    const text = `${JSON.stringify(catalog)}\n`;
    await new Promise<void>((resolve) => process.stdout.write(text, () => resolve()));
    process.exit(0);
  }
  if (ENV_URL === '') throw new Error('MAKEFUN_ENV_URL is not set');
  if (chatCompletionsUrl() === '') throw new Error('OPENAI_BASE_URL is not set');
  const server = createServer((req, res) => {
    void handle(req, res).catch((err: unknown) => {
      log((err as Error).stack ?? String(err));
      if (!res.headersSent) {
        sendError(res, req.url?.startsWith('/v1/messages') === true ? 'anthropic' : 'openai', 500, 'internal_error', 'the server failed to answer');
      }
    });
  });
  await listen(server);
  const address = server.address();
  if (address === null || typeof address === 'string') throw new Error('the server has no port');
  const port = address.port;
  if (port === 8080) throw new Error('the OS picked 8080, which the env owns on one layout: restart the trial');
  log(`listening on 0.0.0.0:${port} with ${servedModels().length} free models`);
  await register(port, catalog);
  process.on('SIGTERM', () => process.exit(0));
  process.on('SIGINT', () => process.exit(0));
  poll(server);
}

try {
  await start();
} catch (err) {
  log((err as Error).stack ?? String(err));
  process.exit(1);
}
