import { json, methodNotAllowed, type Env } from "../lib/http";
import { listCatalog } from "../lib/printful";

// Printful products removed from the store (Stable-ish, Chart Now Cry Later).
const REMOVED_PRODUCTS = new Set([481024059, 481018836]);

// Nothing on the site calls this (checkout reads Printful sync variants directly), but one uncached
// request costs ~50 Printful calls and repeated hits trip Printful's rate limit for checkout too.
// So successful responses are kept in the edge cache: at most one Printful sweep per location per 10 min.
const CACHE_TTL_SEC = 600;
const BROWSER_TTL_SEC = 60;

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const url = new URL(context.request.url);
  const cacheKey = new Request(`${url.origin}/api/products`, { method: "GET" }); // ignore query strings (no cache-busting)
  const cache = (caches as unknown as { default: Cache }).default;
  const hit = await cache.match(cacheKey);
  if (hit) return hit;

  const catalog = await listCatalog(context.env);
  if (!catalog.ok) {
    return json(
      { products: [], error: catalog.error || "Failed to load products" },
      catalog.status >= 400 ? catalog.status : 502,
      { "cache-control": "no-store" },
    );
  }
  const res = json(
    { products: catalog.products.filter((p) => !REMOVED_PRODUCTS.has(p.id)) },
    200,
    { "cache-control": `public, max-age=${BROWSER_TTL_SEC}, s-maxage=${CACHE_TTL_SEC}` },
  );
  context.waitUntil(cache.put(cacheKey, res.clone()));
  return res;
};

export const onRequest: PagesFunction<Env> = async (context) => {
  if (context.request.method === "GET") return onRequestGet(context);
  return methodNotAllowed("GET");
};
