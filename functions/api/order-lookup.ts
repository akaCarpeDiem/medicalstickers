import { methodNotAllowed, type Env } from "../lib/http";
import { mailerConfigured } from "../lib/mail";
import {
  classifyLookup,
  deliverOrders,
  enforceLookupLimits,
  findOrders,
  jsonPublic,
} from "../lib/order-lookup";

/**
 * POST /api/order-lookup  { "query": "<order number or email>" }
 *
 * Always answers with the same success message whether or not an order matched.
 * Order details are emailed to the address on the Stripe Checkout Session only.
 */
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const ip = context.request.headers.get("cf-connecting-ip") || "unknown";

  let raw = "";
  try {
    raw = await context.request.text();
  } catch {
    return jsonPublic("bad");
  }
  if (raw.length > 2000) {
    const limited = await enforceLookupLimits(ip, null);
    if (!limited.ok) return jsonPublic("rate", limited.retryAfterSec);
    return jsonPublic("bad");
  }

  let body: any;
  try {
    body = JSON.parse(raw);
  } catch {
    const limited = await enforceLookupLimits(ip, null);
    if (!limited.ok) return jsonPublic("rate", limited.retryAfterSec);
    return jsonPublic("bad");
  }

  const kind = classifyLookup(body?.query);
  const limited = await enforceLookupLimits(ip, kind);
  if (!limited.ok) return jsonPublic("rate", limited.retryAfterSec);
  if (!kind) return jsonPublic("bad");

  if (!context.env.STRIPE_SECRET_KEY || !mailerConfigured(context.env)) {
    return jsonPublic("down");
  }

  let result;
  try {
    result = await findOrders(context.env, kind);
  } catch (err) {
    console.error("[order-lookup] lookup failed");
    return jsonPublic("down");
  }
  if (result.unavailable) return jsonPublic("down");

  if (result.orders.length) {
    try {
      await deliverOrders(context.env, result);
    } catch (err) {
      // Same public response as a miss, so a mailer failure cannot confirm a match.
      console.error("[order-lookup] send failed");
    }
  }

  return jsonPublic("ok");
};

export const onRequest: PagesFunction<Env> = async (context) => {
  if (context.request.method === "POST") return onRequestPost(context);
  return methodNotAllowed("POST");
};
