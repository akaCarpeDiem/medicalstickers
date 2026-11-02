/**
 * Basic fixed-window rate limits for order lookup.
 * Counts live in the isolate and, when the runtime allows it, a named Cache
 * (not the CDN cache) so a burst in one location shares a counter.
 * This is not a global atomic limit across every Cloudflare location.
 */

export type LimitDecision = { ok: true } | { ok: false; retryAfterSec: number };

type Bucket = { count: number; reset: number };

const memory = new Map<string, Bucket>();

export function resetRateLimitsForTests(): void {
  memory.clear();
}

function prune(now: number): void {
  if (memory.size < 4000) return;
  for (const [key, row] of memory) {
    if (now >= row.reset) memory.delete(key);
  }
}

async function namedCache(): Promise<Cache | null> {
  try {
    const store = (globalThis as { caches?: { open?: (name: string) => Promise<Cache> } }).caches;
    if (!store || typeof store.open !== "function") return null;
    return await store.open("ms-order-lookup");
  } catch {
    return null;
  }
}

function cacheRequest(key: string): Request {
  return new Request(`https://rl.invalid/ms-order-lookup/${encodeURIComponent(key)}`);
}

async function cacheRead(key: string): Promise<Bucket | null> {
  try {
    const cache = await namedCache();
    if (!cache) return null;
    const hit = await cache.match(cacheRequest(key));
    if (!hit) return null;
    const data = (await hit.json()) as Bucket;
    if (!data || typeof data.count !== "number" || typeof data.reset !== "number") return null;
    return data;
  } catch {
    return null;
  }
}

async function cacheWrite(key: string, row: Bucket, ttlSec: number): Promise<void> {
  try {
    const cache = await namedCache();
    if (!cache) return;
    const res = new Response(JSON.stringify(row), {
      headers: {
        "content-type": "application/json",
        "cache-control": `public, max-age=${Math.max(1, ttlSec)}`,
      },
    });
    await cache.put(cacheRequest(key), res);
  } catch {
    // Named cache is a best-effort extra. The in-isolate counter still applies.
  }
}

export async function hitLimit(
  key: string,
  limit: number,
  windowSec: number,
  now = Date.now(),
): Promise<LimitDecision> {
  prune(now);
  const cached = await cacheRead(key);
  const local = memory.get(key) || null;
  const fresh = [local, cached].filter((row): row is Bucket => Boolean(row && now < row.reset));
  let row: Bucket | null = null;
  for (const candidate of fresh) {
    if (!row || candidate.count > row.count) row = candidate;
    else if (candidate.count === row.count && candidate.reset > row.reset) row = candidate;
  }
  if (!row || now >= row.reset) {
    row = { count: 1, reset: now + windowSec * 1000 };
  } else if (row.count >= limit) {
    memory.set(key, row);
    return { ok: false, retryAfterSec: Math.max(1, Math.ceil((row.reset - now) / 1000)) };
  } else {
    row = { count: row.count + 1, reset: row.reset };
  }
  memory.set(key, row);
  const ttl = Math.max(1, Math.ceil((row.reset - now) / 1000));
  await cacheWrite(key, row, ttl);
  return { ok: true };
}

/** Every check must pass. A denial stops later counters from incrementing. */
export async function hitAll(
  checks: { key: string; limit: number; windowSec: number }[],
  now = Date.now(),
): Promise<LimitDecision> {
  for (const check of checks) {
    const result = await hitLimit(check.key, check.limit, check.windowSec, now);
    if (!result.ok) return result;
  }
  return { ok: true };
}
