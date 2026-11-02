/**
 * Privacy and behavior checks for order lookup.
 * Run: npx tsx tools/order-lookup.test.ts
 */
import assert from "node:assert/strict";
import { onRequest, onRequestPost } from "../functions/api/order-lookup.ts";
import type { Env } from "../functions/lib/http.ts";
import {
  MSG_BAD,
  MSG_DOWN,
  MSG_OK,
  MSG_RATE,
  classifyLookup,
  renderEmail,
  summarizeSession,
  type OrderSummary,
} from "../functions/lib/order-lookup.ts";
import { resetRateLimitsForTests } from "../functions/lib/rate-limit.ts";

const PII = [
  "Casey Patient",
  "123 Hidden Lane",
  "Portland",
  "97201",
  "+15555550123",
  "buyer@example.com",
  "4242",
  "Clinically Tired",
  "pay.stripe.com",
  "cs_test_abc1234567890",
  "1234-5678",
  "visa",
];

const SESSION_ID = "cs_test_abc1234567890";

function fullSession(overrides: Record<string, unknown> = {}) {
  return {
    id: SESSION_ID,
    object: "checkout.session",
    payment_status: "paid",
    metadata: { source: "medicalstickers", cart: "5569500768x2" },
    created: 1762041600,
    currency: "usd",
    amount_total: 1749,
    customer_details: {
      email: "buyer@example.com",
      name: "Casey Patient",
      phone: "+15555550123",
      address: { line1: "123 Hidden Lane", city: "Portland", state: "OR", postal_code: "97201" },
    },
    shipping_details: {
      name: "Casey Patient",
      address: { line1: "123 Hidden Lane", city: "Portland", postal_code: "97201" },
    },
    total_details: { amount_shipping: 499, amount_tax: 100, amount_discount: 0 },
    line_items: {
      object: "list",
      data: [{ description: "Clinically Tired", quantity: 2, amount_total: 1150 }],
      has_more: false,
    },
    payment_intent: {
      id: "pi_3Nabc123",
      latest_charge: {
        id: "ch_3Nabc123",
        receipt_url: "https://pay.stripe.com/receipts/payment/secret-token",
        receipt_number: "1234-5678",
        billing_details: {
          email: "buyer@example.com",
          name: "Casey Patient",
          address: { line1: "123 Hidden Lane", city: "Portland", postal_code: "97201" },
        },
        payment_method_details: { card: { last4: "4242", brand: "visa" } },
      },
    },
    ...overrides,
  };
}

function shallow(session = fullSession()) {
  return {
    id: session.id,
    object: session.object,
    payment_status: session.payment_status,
    metadata: session.metadata,
    created: session.created,
    customer_details: session.customer_details,
    customer_email: null,
  };
}

const env: Env = { STRIPE_SECRET_KEY: "sk_test_x", RESEND_API_KEY: "re_test_x" };

let resendBodies: string[] = [];

function installFetch(mode: "found" | "missing" | "foreign" | "other-store" | "unpaid" | "down" | "session" | "pi" | "charge") {
  resendBodies = [];
  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const body = init?.body ? String(init.body) : "";
    if (url.includes("api.resend.com")) {
      resendBodies.push(body);
      return new Response(JSON.stringify({ id: "email_1" }), { status: 200 });
    }
    if (mode === "down") {
      return new Response(JSON.stringify({ error: { message: "Invalid API key for buyer@example.com" } }), {
        status: 401,
      });
    }
    if (url.includes("/v1/customers?")) {
      return new Response(JSON.stringify({ data: [] }), { status: 200 });
    }
    if (url.includes("/v1/charges/ch_")) {
      return new Response(
        JSON.stringify({
          id: "ch_3Nabc123",
          payment_intent: "pi_3Nabc123",
          billing_details: { name: "Casey Patient", address: { line1: "123 Hidden Lane" } },
          payment_method_details: { card: { last4: "4242" } },
        }),
        { status: 200 },
      );
    }
    if (url.includes("/v1/checkout/sessions/cs_")) {
      if (mode === "missing") {
        return new Response(JSON.stringify({ error: { message: "No such checkout.session" } }), { status: 404 });
      }
      return new Response(JSON.stringify(fullSession()), { status: 200 });
    }
    if (url.includes("payment_intent=")) {
      return new Response(JSON.stringify({ data: [{ id: SESSION_ID }], has_more: false }), { status: 200 });
    }
    if (url.includes("/v1/checkout/sessions?")) {
      if (mode === "missing") return new Response(JSON.stringify({ data: [], has_more: false }), { status: 200 });
      if (mode === "foreign") {
        const row = shallow();
        row.customer_details = { ...row.customer_details, email: "other@example.com", name: "Casey Patient" };
        return new Response(JSON.stringify({ data: [row], has_more: false }), { status: 200 });
      }
      if (mode === "other-store") {
        const row = shallow();
        row.metadata = { source: "naturestickers" };
        return new Response(JSON.stringify({ data: [row], has_more: false }), { status: 200 });
      }
      if (mode === "unpaid") {
        const row = shallow();
        row.payment_status = "unpaid";
        return new Response(JSON.stringify({ data: [row], has_more: false }), { status: 200 });
      }
      if (mode === "found") {
        return new Response(JSON.stringify({ data: [shallow()], has_more: false }), { status: 200 });
      }
      return new Response(JSON.stringify({ data: [], has_more: false }), { status: 200 });
    }
    return new Response(JSON.stringify({ data: [] }), { status: 200 });
  }) as typeof fetch;
}

function post(query: string, ip = "203.0.113.10", useEnv: Env = env) {
  return onRequestPost({
    env: useEnv,
    request: new Request("https://medicalstickers.shop/api/order-lookup", {
      method: "POST",
      headers: { "content-type": "application/json", "cf-connecting-ip": ip },
      body: JSON.stringify({ query }),
    }),
  } as Parameters<typeof onRequestPost>[0]);
}

async function bodyOf(res: Response): Promise<string> {
  return res.text();
}

function assertNoPii(payload: string, label: string) {
  for (const secret of PII) {
    assert.equal(payload.includes(secret), false, `${label} leaked ${secret}`);
  }
}

async function testClassify() {
  assert.deepEqual(classifyLookup("  Buyer@Example.com "), { kind: "email", email: "buyer@example.com" });
  assert.deepEqual(classifyLookup(`https://medicalstickers.shop/thanks/?session_id=${SESSION_ID}`), {
    kind: "session",
    id: SESSION_ID,
  });
  assert.equal(classifyLookup("CS_TEST_abc1234567890")?.kind, "session");
  assert.equal(classifyLookup("pi_3Nabc123")?.kind, "payment_intent");
  assert.equal(classifyLookup("ch_3Nabc123")?.kind, "charge");
  assert.equal(classifyLookup("py_3Nabc123")?.kind, "charge");
  assert.equal(classifyLookup("1234-5678")?.kind, "receipt");
  assert.equal(classifyLookup("18897928")?.kind, "printful");
  assert.equal(classifyLookup(""), null);
  assert.equal(classifyLookup("not an order"), null);
  assert.equal(classifyLookup("a@b"), null);
}

async function testRenderStripsPii() {
  const summary = summarizeSession(fullSession()) as OrderSummary;
  assert.ok(summary);
  assert.equal(summary.email, "buyer@example.com");
  assert.equal(summary.receiptUrl, "https://pay.stripe.com/receipts/payment/secret-token");
  const nasty = summarizeSession(
    fullSession({
      line_items: { data: [{ description: "<script>alert(1)</script>", quantity: 1, amount_total: 100 }] },
      payment_intent: {
        latest_charge: { receipt_url: "javascript:alert(1)", receipt_number: "9999-0000" },
      },
    }),
  ) as OrderSummary;
  assert.equal(nasty.receiptUrl, null);
  const mail = renderEmail([summary, nasty], true);
  assert.equal(mail.html.includes("123 Hidden Lane"), false);
  assert.equal(mail.text.includes("Casey Patient"), false);
  assert.equal(mail.html.includes("+15555550123"), false);
  assert.equal(mail.html.includes("4242"), false);
  assert.equal(mail.html.includes("buyer@example.com"), false);
  assert.equal(mail.html.includes("<script>"), false);
  assert.ok(mail.html.includes("Clinically Tired"));
  assert.ok(mail.html.includes("https://pay.stripe.com/receipts/payment/secret-token"));
  assert.ok(mail.html.includes("&lt;script&gt;"));
  assert.ok(mail.text.includes("not listed here"));
}

async function testSamePublicResponse() {
  resetRateLimitsForTests();
  installFetch("found");
  const found = await post("buyer@example.com", "203.0.113.20");
  const foundText = await bodyOf(found);
  assert.equal(found.status, 200);
  assert.equal(found.headers.get("cache-control"), "no-store");
  assert.equal(resendBodies.length, 1);
  const sent = JSON.parse(resendBodies[0]);
  assert.deepEqual(sent.to, ["buyer@example.com"]);
  assert.ok(sent.html.includes("Clinically Tired"));
  assert.equal(sent.html.includes("123 Hidden Lane"), false);
  assert.equal(sent.html.includes("Casey Patient"), false);
  assert.equal(sent.text.includes("4242"), false);

  resetRateLimitsForTests();
  installFetch("missing");
  const missing = await post("nobody@example.com", "203.0.113.21");
  const missingText = await bodyOf(missing);
  assert.equal(missing.status, 200);
  assert.equal(foundText, missingText);
  assert.equal(foundText, JSON.stringify({ ok: true, message: MSG_OK }));
  assertNoPii(foundText, "found response");
  assert.equal(resendBodies.length, 0);
}

async function testDoesNotMailWrongOrders() {
  for (const mode of ["foreign", "other-store", "unpaid"] as const) {
    resetRateLimitsForTests();
    installFetch(mode);
    const res = await post("buyer@example.com", `203.0.113.${mode.length + 30}`);
    assert.equal(res.status, 200);
    assert.equal(await res.text(), JSON.stringify({ ok: true, message: MSG_OK }));
    assert.equal(resendBodies.length, 0, mode);
  }
}

async function testSessionAndChargeLookup() {
  resetRateLimitsForTests();
  installFetch("session");
  const bySession = await post(SESSION_ID, "203.0.113.40");
  assert.equal(bySession.status, 200);
  assertNoPii(await bySession.text(), "session response");
  assert.equal(resendBodies.length, 1);
  assert.equal(JSON.parse(resendBodies[0]).to[0], "buyer@example.com");

  resetRateLimitsForTests();
  installFetch("pi");
  const byPi = await post("pi_3Nabc123", "203.0.113.41");
  assert.equal(await byPi.text(), JSON.stringify({ ok: true, message: MSG_OK }));
  assert.equal(resendBodies.length, 1);

  resetRateLimitsForTests();
  installFetch("charge");
  const byCharge = await post("ch_3Nabc123", "203.0.113.42");
  assertNoPii(await byCharge.text(), "charge response");
  assert.equal(resendBodies.length, 1);
}

async function testUnknownSessionMatchesMiss() {
  resetRateLimitsForTests();
  installFetch("missing");
  const res = await post("cs_test_doesnotexist999", "203.0.113.50");
  assert.equal(res.status, 200);
  assert.equal(await res.text(), JSON.stringify({ ok: true, message: MSG_OK }));
  assert.equal(resendBodies.length, 0);
}

async function testRateLimitAndValidation() {
  resetRateLimitsForTests();
  installFetch("found");
  const ip = "203.0.113.60";
  for (let i = 0; i < 3; i++) {
    const res = await post("buyer@example.com", ip);
    assert.equal(res.status, 200);
  }
  const blocked = await post("buyer@example.com", ip);
  assert.equal(blocked.status, 429);
  assert.ok(Number(blocked.headers.get("retry-after")) > 0);
  const text = await blocked.text();
  assert.equal(text, JSON.stringify({ ok: false, message: MSG_RATE }));
  assertNoPii(text, "rate limit");

  resetRateLimitsForTests();
  const bad = await post("   ", "203.0.113.61");
  assert.equal(bad.status, 400);
  assert.equal(await bad.text(), JSON.stringify({ ok: false, message: MSG_BAD }));
}

async function testUnconfiguredIsUniform() {
  resetRateLimitsForTests();
  installFetch("found");
  const bare: Env = { STRIPE_SECRET_KEY: "sk_test_x" };
  const a = await post("buyer@example.com", "203.0.113.70", bare);
  const b = await post("nobody@example.com", "203.0.113.70", bare);
  assert.equal(a.status, 503);
  const downText = await a.text();
  assert.equal(downText, await b.text());
  assert.equal(downText, JSON.stringify({ ok: false, message: MSG_DOWN }));
  const again = await post("buyer@example.com", "203.0.113.71", bare);
  assert.equal(await again.text(), JSON.stringify({ ok: false, message: MSG_DOWN }));
  assert.equal(resendBodies.length, 0);
}

async function testStripeFailureDoesNotEcho() {
  resetRateLimitsForTests();
  installFetch("down");
  const res = await post("buyer@example.com", "203.0.113.80");
  assert.equal(res.status, 503);
  const text = await res.text();
  assert.equal(text.includes("buyer@example.com"), false);
  assert.equal(text.includes("Invalid API key"), false);
  assert.equal(text, JSON.stringify({ ok: false, message: MSG_DOWN }));
}

async function testMethod() {
  const res = await onRequest({
    env,
    request: new Request("https://medicalstickers.shop/api/order-lookup", { method: "GET" }),
  } as Parameters<typeof onRequest>[0]);
  assert.equal(res.status, 405);
}

async function main() {
  await testClassify();
  await testRenderStripsPii();
  await testSamePublicResponse();
  await testDoesNotMailWrongOrders();
  await testSessionAndChargeLookup();
  await testUnknownSessionMatchesMiss();
  await testRateLimitAndValidation();
  await testUnconfiguredIsUniform();
  await testStripeFailureDoesNotEcho();
  await testMethod();
  console.log("order lookup tests passed");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
