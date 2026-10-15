import { json, methodNotAllowed, type Env } from "../lib/http";
import { listCatalog } from "../lib/printful";

// Printful products removed from the store (Stable-ish, Chart Now Cry Later).
const REMOVED_PRODUCTS = new Set([481024059, 481018836]);

const CACHE_TTL_SEC = 60; // brief cache

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const catalog = await listCatalog(context.env);
  if (!catalog.ok) {
    return json(
      { products: [], error: catalog.error || "Failed to load products" },
      catalog.status >= 400 ? catalog.status : 502,
    );
  }
  return json(
    { products: catalog.products.filter((p) => !REMOVED_PRODUCTS.has(p.id)) },
    200,
    {
      "cache-control": `public, max-age=${CACHE_TTL_SEC}, s-maxage=${CACHE_TTL_SEC}`,
    },
  );
};

export const onRequest: PagesFunction<Env> = async (context) => {
  if (context.request.method === "GET") return onRequestGet(context);
  return methodNotAllowed("GET");
};
