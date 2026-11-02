import type { Env } from "./http";
import { sendMail, SUPPORT_EMAIL } from "./mail";
import { printful } from "./printful";
import { hitAll } from "./rate-limit";
import { stripeGet } from "./stripe";

/**
 * Privacy contract:
 * - HTTP responses are chosen from a fixed set of messages. They never echo the
 *   query, say whether an order exists, or include a name, address, phone,
 *   email, card, or line item.
 * - Email is sent only to the address already stored on a paid Medical Stickers
 *   Checkout Session. Callers cannot choose the destination.
 * - At most the five newest paid orders are included when several match an email.
 */

export const STRIPE_VERSION = "2026-10-28.endive";
export const MAX_ORDERS_IN_EMAIL = 5;

export const MSG_OK = "If we find a matching order, we'll email the details to the address on file.";
export const MSG_BAD = "Enter an order number or the email you used at checkout.";
export const MSG_RATE = "Please wait a few minutes and try again.";
export const MSG_DOWN = "Order lookup is temporarily unavailable. Email support@medicalstickers.shop and we'll help.";

const IP_BURST = { limit: 8, windowSec: 15 * 60 };
const IP_DAY = { limit: 30, windowSec: 24 * 60 * 60 };
const KEY_WINDOW = { limit: 3, windowSec: 60 * 60 };

const NO_STORE = {
  "cache-control": "no-store",
  "x-content-type-options": "nosniff",
  "x-robots-tag": "noindex",
};

export type LookupKind =
  | { kind: "email"; email: string }
  | { kind: "session"; id: string }
  | { kind: "payment_intent"; id: string }
  | { kind: "charge"; id: string }
  | { kind: "receipt"; number: string }
  | { kind: "printful"; id: string };

export type OrderSummary = {
  id: string;
  created: number;
  currency: string;
  amountTotal: number;
  amountShipping: number | null;
  amountTax: number | null;
  items: { name: string; qty: number; amount: number }[];
  itemsTruncated: boolean;
  receiptUrl: string | null;
  receiptNumber: string | null;
  email: string;
};

export type FindResult = {
  orders: OrderSummary[];
  more: boolean;
  unavailable: boolean;
};

const EMAIL_RE =
  /^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/i;
const SESSION_RE = /cs_(?:test|live)_[A-Za-z0-9]+/i;
const PI_RE = /^pi_[A-Za-z0-9]+$/;
const CHARGE_RE = /^(?:ch|py)_[A-Za-z0-9]+$/;
const RECEIPT_RE = /^\d{4,6}-\d{4,6}$/;
const PRINTFUL_RE = /^\d{4,12}$/;

function normalizeSessionId(id: string): string {
  return id.replace(/^cs_test_/i, "cs_test_").replace(/^cs_live_/i, "cs_live_");
}

export function classifyLookup(raw: unknown): LookupKind | null {
  if (typeof raw !== "string") return null;
  const trimmed = raw.trim().replace(/^["']+|["']+$/g, "").trim();
  if (!trimmed || trimmed.length > 400) return null;
  if (EMAIL_RE.test(trimmed) && trimmed.length <= 254) {
    return { kind: "email", email: trimmed.toLowerCase() };
  }
  const session = trimmed.match(SESSION_RE);
  if (session && session[0].length >= 16 && session[0].length <= 255) {
    return { kind: "session", id: normalizeSessionId(session[0]) };
  }
  if (PI_RE.test(trimmed)) return { kind: "payment_intent", id: trimmed };
  if (CHARGE_RE.test(trimmed)) return { kind: "charge", id: trimmed };
  if (RECEIPT_RE.test(trimmed)) return { kind: "receipt", number: trimmed };
  if (PRINTFUL_RE.test(trimmed)) return { kind: "printful", id: trimmed };
  return null;
}

export function lookupKeyMaterial(kind: LookupKind): string {
  switch (kind.kind) {
    case "email":
      return `email:${kind.email}`;
    case "receipt":
      return `receipt:${kind.number}`;
    default:
      return `${kind.kind}:${kind.id}`;
  }
}

async function sha256Hex(value: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function enforceLookupLimits(
  ip: string,
  kind: LookupKind | null,
): Promise<{ ok: true } | { ok: false; retryAfterSec: number }> {
  const ipHash = await sha256Hex(`ip:${ip || "unknown"}`);
  const checks = [
    { key: `ip15:${ipHash}`, ...IP_BURST },
    { key: `ip24:${ipHash}`, ...IP_DAY },
  ];
  if (kind) {
    checks.push({ key: `q:${await sha256Hex(lookupKeyMaterial(kind))}`, ...KEY_WINDOW });
  }
  return hitAll(checks);
}

function unavailableStatus(status: number): boolean {
  return status === 401 || status === 403 || status === 429 || status >= 500;
}

async function stripe(env: Env, path: string): Promise<{ ok: boolean; status: number; data: any }> {
  const pinned = await stripeGet(env, path, { "Stripe-Version": STRIPE_VERSION });
  if (pinned.status === 400) return stripeGet(env, path);
  return pinned;
}

function emailOf(session: any): string {
  const raw = session?.customer_details?.email || session?.customer_email || "";
  return typeof raw === "string" ? raw.trim().toLowerCase() : "";
}

function isOurPaidSession(session: any): boolean {
  return Boolean(
    session &&
      session.object === "checkout.session" &&
      session.payment_status === "paid" &&
      session.metadata?.source === "medicalstickers" &&
      typeof session.id === "string" &&
      session.id.startsWith("cs_"),
  );
}

function safeReceiptUrl(url: unknown): string | null {
  if (typeof url !== "string" || url.length > 2000) return null;
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== "https:") return null;
    if (parsed.hostname !== "pay.stripe.com" && parsed.hostname !== "invoice.stripe.com") return null;
    return parsed.toString();
  } catch {
    return null;
  }
}

function moneyNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? Math.round(value) : null;
}

export function summarizeSession(session: any): OrderSummary | null {
  if (!isOurPaidSession(session)) return null;
  const email = emailOf(session);
  if (!email || !EMAIL_RE.test(email)) return null;
  const charge = session?.payment_intent?.latest_charge;
  const chargeObj = charge && typeof charge === "object" ? charge : null;
  const lines = Array.isArray(session?.line_items?.data) ? session.line_items.data : [];
  const items = lines.slice(0, 20).map((line: any) => ({
    name: String(line?.description || line?.price?.product?.name || "Sticker").slice(0, 180),
    qty: Number.isFinite(Number(line?.quantity)) ? Math.max(1, Math.round(Number(line.quantity))) : 1,
    amount: moneyNumber(line?.amount_total) ?? 0,
  }));
  const shipping = moneyNumber(session?.total_details?.amount_shipping);
  const tax = moneyNumber(session?.total_details?.amount_tax);
  return {
    id: session.id,
    created: typeof session.created === "number" ? session.created : 0,
    currency: typeof session.currency === "string" ? session.currency : "usd",
    amountTotal: moneyNumber(session.amount_total) ?? 0,
    amountShipping: shipping,
    amountTax: tax,
    items,
    itemsTruncated: Boolean(session?.line_items?.has_more),
    receiptUrl: safeReceiptUrl(chargeObj?.receipt_url),
    receiptNumber: typeof chargeObj?.receipt_number === "string" ? chargeObj.receipt_number.slice(0, 40) : null,
    email,
  };
}

const SESSION_EXPAND = "expand[]=line_items&expand[]=payment_intent.latest_charge";

async function retrieveSession(env: Env, id: string): Promise<{ session: any | null; unavailable: boolean }> {
  if (!/^cs_(test|live)_[A-Za-z0-9]+$/.test(id)) return { session: null, unavailable: false };
  const res = await stripe(env, `/v1/checkout/sessions/${id}?${SESSION_EXPAND}`);
  if (res.status === 404) return { session: null, unavailable: false };
  if (!res.ok) return { session: null, unavailable: unavailableStatus(res.status) || res.status === 400 };
  return { session: res.data, unavailable: false };
}

async function sessionsForPaymentIntent(env: Env, paymentIntentId: string): Promise<FindResult> {
  if (!/^pi_[A-Za-z0-9]+$/.test(paymentIntentId)) return { orders: [], more: false, unavailable: false };
  const res = await stripe(env, `/v1/checkout/sessions?payment_intent=${paymentIntentId}&limit=1`);
  if (!res.ok) {
    if (res.status === 404 || res.status === 400) return { orders: [], more: false, unavailable: false };
    return { orders: [], more: false, unavailable: unavailableStatus(res.status) };
  }
  const id = res.data?.data?.[0]?.id;
  if (typeof id !== "string") return { orders: [], more: false, unavailable: false };
  return findBySession(env, id);
}

export async function findBySession(env: Env, id: string): Promise<FindResult> {
  const got = await retrieveSession(env, id);
  if (got.unavailable) return { orders: [], more: false, unavailable: true };
  const summary = got.session ? summarizeSession(got.session) : null;
  return { orders: summary ? [summary] : [], more: false, unavailable: false };
}

async function findByCharge(env: Env, id: string): Promise<FindResult> {
  if (!/^(?:ch|py)_[A-Za-z0-9]+$/.test(id)) return { orders: [], more: false, unavailable: false };
  const res = await stripe(env, `/v1/charges/${id}`);
  if (res.status === 404 || res.status === 400) return { orders: [], more: false, unavailable: false };
  if (!res.ok) return { orders: [], more: false, unavailable: unavailableStatus(res.status) };
  const pi = res.data?.payment_intent;
  const piId = typeof pi === "string" ? pi : pi?.id;
  if (typeof piId !== "string") return { orders: [], more: false, unavailable: false };
  return sessionsForPaymentIntent(env, piId);
}

async function findByReceipt(env: Env, number: string): Promise<FindResult> {
  if (!RECEIPT_RE.test(number)) return { orders: [], more: false, unavailable: false };
  const query = encodeURIComponent(`receipt_number:"${number}"`);
  const invoices = await stripe(env, `/v1/invoices/search?query=${query}&limit=5`);
  if (unavailableStatus(invoices.status)) return { orders: [], more: false, unavailable: true };
  const paymentIntents: string[] = [];
  if (invoices.ok && Array.isArray(invoices.data?.data)) {
    for (const invoice of invoices.data.data) {
      if (invoice?.receipt_number !== number) continue;
      const pi = invoice.payment_intent;
      const piId = typeof pi === "string" ? pi : pi?.id;
      if (typeof piId === "string") paymentIntents.push(piId);
    }
  }
  if (!paymentIntents.length) {
    const charges = await stripe(env, `/v1/charges/search?query=${query}&limit=5`);
    if (unavailableStatus(charges.status)) return { orders: [], more: false, unavailable: true };
    if (charges.ok && Array.isArray(charges.data?.data)) {
      for (const charge of charges.data.data) {
        if (charge?.receipt_number !== number) continue;
        const pi = charge.payment_intent;
        const piId = typeof pi === "string" ? pi : pi?.id;
        if (typeof piId === "string") paymentIntents.push(piId);
      }
    }
  }
  for (const piId of paymentIntents.slice(0, 3)) {
    const found = await sessionsForPaymentIntent(env, piId);
    if (found.unavailable) return found;
    if (found.orders.length) return found;
  }
  return { orders: [], more: false, unavailable: false };
}

async function findByPrintful(env: Env, id: string): Promise<FindResult> {
  if (!env.PRINTFUL_TOKEN || !PRINTFUL_RE.test(id)) return { orders: [], more: false, unavailable: false };
  const res = await printful(env, `/orders/${encodeURIComponent(id)}`);
  if (res.status === 404 || res.status === 400) return { orders: [], more: false, unavailable: false };
  if (!res.ok) return { orders: [], more: false, unavailable: unavailableStatus(res.status) };
  const custom = res.data?.result?.packing_slip?.custom_order_id;
  if (typeof custom !== "string") return { orders: [], more: false, unavailable: false };
  const match = custom.match(/^cs_(?:test|live)_[A-Za-z0-9]+$/);
  if (!match) return { orders: [], more: false, unavailable: false };
  return findBySession(env, match[0]);
}

function dedupeSessions(rows: any[]): any[] {
  const seen = new Set<string>();
  const out: any[] = [];
  for (const row of rows) {
    if (!row?.id || seen.has(row.id)) continue;
    seen.add(row.id);
    out.push(row);
  }
  out.sort((a, b) => (b.created || 0) - (a.created || 0));
  return out;
}

async function listSessions(env: Env, path: string): Promise<{ rows: any[]; hasMore: boolean; unavailable: boolean; ignore: boolean }> {
  const res = await stripe(env, path);
  if (res.status === 400) return { rows: [], hasMore: false, unavailable: false, ignore: true };
  if (!res.ok) return { rows: [], hasMore: false, unavailable: unavailableStatus(res.status), ignore: false };
  const rows = Array.isArray(res.data?.data) ? res.data.data : [];
  return { rows, hasMore: Boolean(res.data?.has_more), unavailable: false, ignore: false };
}

async function findByEmail(env: Env, email: string): Promise<FindResult> {
  const params = new URLSearchParams();
  params.set("customer_details[email]", email);
  params.set("status", "complete");
  params.set("limit", "100");
  const direct = await listSessions(env, `/v1/checkout/sessions?${params.toString()}`);
  if (direct.unavailable) return { orders: [], more: false, unavailable: true };

  let rows: any[] = [];
  let more = false;
  if (!direct.ignore) {
    const foreign = direct.rows.some((row) => {
      const got = emailOf(row);
      return got && got !== email;
    });
    if (!foreign) {
      rows = direct.rows;
      more = direct.hasMore;
    }
  }

  const customers = await stripe(env, `/v1/customers?email=${encodeURIComponent(email)}&limit=5`);
  if (unavailableStatus(customers.status)) return { orders: [], more: false, unavailable: true };
  if (customers.ok && Array.isArray(customers.data?.data)) {
    for (const customer of customers.data.data.slice(0, 5)) {
      if (typeof customer?.id !== "string" || !/^cus_[A-Za-z0-9]+$/.test(customer.id)) continue;
      const listed = await listSessions(
        env,
        `/v1/checkout/sessions?customer=${customer.id}&status=complete&limit=20`,
      );
      if (listed.unavailable) return { orders: [], more: false, unavailable: true };
      if (listed.hasMore) more = true;
      rows = rows.concat(listed.rows);
    }
  }

  const matched = dedupeSessions(rows).filter((row) => emailOf(row) === email && isOurPaidSession(row));
  const top = matched.slice(0, MAX_ORDERS_IN_EMAIL);
  const orders: OrderSummary[] = [];
  for (const row of top) {
    const full = await retrieveSession(env, row.id);
    if (full.unavailable) return { orders: [], more: false, unavailable: true };
    const summary = full.session ? summarizeSession(full.session) : null;
    if (summary && summary.email === email) orders.push(summary);
  }
  return {
    orders,
    more: more || matched.length > MAX_ORDERS_IN_EMAIL,
    unavailable: false,
  };
}

export async function findOrders(env: Env, kind: LookupKind): Promise<FindResult> {
  switch (kind.kind) {
    case "email":
      return findByEmail(env, kind.email);
    case "session":
      return findBySession(env, kind.id);
    case "payment_intent":
      return sessionsForPaymentIntent(env, kind.id);
    case "charge":
      return findByCharge(env, kind.id);
    case "receipt":
      return findByReceipt(env, kind.number);
    case "printful":
      return findByPrintful(env, kind.id);
  }
}

function esc(value: string): string {
  return value.replace(/[&<>"']/g, (ch) => {
    if (ch === "&") return "&amp;";
    if (ch === "<") return "&lt;";
    if (ch === ">") return "&gt;";
    if (ch === '"') return "&quot;";
    return "&#39;";
  });
}

function formatMoney(cents: number, currency: string): string {
  const code = (currency || "usd").toUpperCase();
  const amount = (cents / 100).toFixed(2);
  if (code === "USD") return `$${amount}`;
  return `${amount} ${code}`;
}

function formatWhen(unix: number): string {
  if (!unix) return "Unknown date";
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles",
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(unix * 1000));
}

export function renderEmail(orders: OrderSummary[], more: boolean): { subject: string; text: string; html: string } {
  const subject = "Your Medical Stickers order details";
  const blocks: string[] = [];
  const htmlBlocks: string[] = [];
  for (const order of orders) {
    const lines = order.items.map(
      (item) => `${item.name} × ${item.qty} — ${formatMoney(item.amount, order.currency)}`,
    );
    if (order.itemsTruncated) lines.push("Additional items are on the Stripe receipt.");
    if (order.amountShipping != null) lines.push(`Shipping — ${formatMoney(order.amountShipping, order.currency)}`);
    if (order.amountTax != null) lines.push(`Tax — ${formatMoney(order.amountTax, order.currency)}`);
    lines.push(`Total — ${formatMoney(order.amountTotal, order.currency)}`);
    if (order.receiptNumber) lines.push(`Receipt number — ${order.receiptNumber}`);
    if (order.receiptUrl) lines.push(`Stripe receipt — ${order.receiptUrl}`);
    blocks.push(
      [`Order ${order.id}`, `Placed ${formatWhen(order.created)}`, ...lines].join("\n"),
    );
    const itemHtml = lines
      .map((line) => `<li style="margin:0 0 6px">${esc(line)}</li>`)
      .join("");
    const receipt = order.receiptUrl
      ? `<p style="margin:12px 0 0"><a href="${esc(order.receiptUrl)}" style="color:#8E2B2A;font-weight:700">Open the Stripe receipt</a></p>`
      : "";
    htmlBlocks.push(
      `<section style="margin:0 0 18px;padding:16px;border:1px solid #e4d8c8;border-radius:16px;background:#fff">` +
        `<p style="margin:0;font-family:Georgia,serif;font-size:20px">Order ${esc(order.id)}</p>` +
        `<p style="margin:6px 0 10px;color:#5c5346">Placed ${esc(formatWhen(order.created))}</p>` +
        `<ul style="margin:0;padding-left:18px">${itemHtml}</ul>` +
        receipt +
        `</section>`,
    );
  }
  const older = more
    ? "If you need an order that is not listed here, reply with the approximate date or the order number."
    : "";
  const text = [
    "Your Medical Stickers order details",
    "",
    "Someone asked medicalstickers.shop to resend order details to this address. If that was not you, you can ignore this message.",
    "",
    blocks.join("\n\n"),
    "",
    older,
    older ? "" : null,
    `Questions: ${SUPPORT_EMAIL}`,
    "Medical Stickers",
  ]
    .filter((line) => line != null)
    .join("\n");
  const html =
    `<div style="margin:0;padding:24px;background:#f6f1e7;color:#1c1917;font-family:Georgia,serif">` +
    `<div style="max-width:560px;margin:0 auto">` +
    `<p style="margin:0 0 8px;letter-spacing:0.14em;text-transform:uppercase;font-size:12px;color:#8E2B2A;font-family:sans-serif">Medical Stickers</p>` +
    `<h1 style="margin:0 0 12px;font-size:28px;font-weight:500">Your order details</h1>` +
    `<p style="margin:0 0 18px;line-height:1.5;font-family:sans-serif">Someone asked us to resend order details to this address. If that was not you, you can ignore this message. Nothing on the website showed these details.</p>` +
    htmlBlocks.join("") +
    (older ? `<p style="font-family:sans-serif;line-height:1.5">${esc(older)}</p>` : "") +
    `<p style="font-family:sans-serif">Questions: <a href="mailto:${SUPPORT_EMAIL}" style="color:#8E2B2A">${SUPPORT_EMAIL}</a></p>` +
    `</div></div>`;
  return { subject, text, html };
}

export async function deliverOrders(env: Env, result: FindResult): Promise<void> {
  const groups = new Map<string, OrderSummary[]>();
  for (const order of result.orders) {
    const key = order.email.toLowerCase();
    const list = groups.get(key) || [];
    list.push(order);
    groups.set(key, list);
  }
  for (const list of groups.values()) {
    const to = list[0]?.email;
    if (!to) continue;
    const message = renderEmail(list, result.more);
    const sent = await sendMail(env, to, message);
    if (!sent) console.error("[order-lookup] email was not accepted by the mailer");
  }
}

export function publicBody(code: "ok" | "bad" | "rate" | "down"): { ok: boolean; message: string } {
  if (code === "ok") return { ok: true, message: MSG_OK };
  if (code === "bad") return { ok: false, message: MSG_BAD };
  if (code === "rate") return { ok: false, message: MSG_RATE };
  return { ok: false, message: MSG_DOWN };
}

export function jsonPublic(code: "ok" | "bad" | "rate" | "down", retryAfterSec?: number): Response {
  const status = code === "ok" ? 200 : code === "bad" ? 400 : code === "rate" ? 429 : 503;
  const headers: Record<string, string> = { ...NO_STORE, "content-type": "application/json; charset=utf-8" };
  if (code === "rate" && retryAfterSec) headers["retry-after"] = String(retryAfterSec);
  return new Response(JSON.stringify(publicBody(code)), { status, headers });
}
