import type { Env } from "./http";

export const DEFAULT_FROM = "Medical Stickers <support@medicalstickers.shop>";
export const SUPPORT_EMAIL = "support@medicalstickers.shop";

export function mailerConfigured(env: Env): boolean {
  return Boolean(env.RESEND_API_KEY?.trim()) || typeof env.EMAIL?.send === "function";
}

function fromAddress(env: Env): string {
  const custom = env.ORDER_FROM_EMAIL?.trim();
  if (custom && !/[\r\n]/.test(custom)) return custom;
  return DEFAULT_FROM;
}

function safeHeader(value: string): string {
  if (/[\r\n]/.test(value)) throw new Error("refusing header newline");
  return value;
}

function encodeSubject(subject: string): string {
  if (/^[\x20-\x7E]*$/.test(subject)) return subject;
  const bytes = new TextEncoder().encode(subject);
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return `=?UTF-8?B?${btoa(binary)}?=`;
}

export function buildRawMime(from: string, to: string, subject: string, text: string, html: string): string {
  const boundary = `ms_${crypto.randomUUID().replace(/-/g, "")}`;
  const headers = [
    `From: ${safeHeader(from)}`,
    `To: ${safeHeader(to)}`,
    `Reply-To: ${SUPPORT_EMAIL}`,
    `Subject: ${safeHeader(encodeSubject(subject))}`,
    "MIME-Version: 1.0",
    `Content-Type: multipart/alternative; boundary="${boundary}"`,
  ];
  return [
    headers.join("\r\n"),
    "",
    `--${boundary}`,
    "Content-Type: text/plain; charset=utf-8",
    "Content-Transfer-Encoding: 8bit",
    "",
    text.replace(/\r?\n/g, "\r\n"),
    `--${boundary}`,
    "Content-Type: text/html; charset=utf-8",
    "Content-Transfer-Encoding: 8bit",
    "",
    html,
    `--${boundary}--`,
    "",
  ].join("\r\n");
}

async function sendViaResend(
  env: Env,
  to: string,
  subject: string,
  text: string,
  html: string,
): Promise<boolean> {
  const key = env.RESEND_API_KEY?.trim();
  if (!key) return false;
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      authorization: `Bearer ${key}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      from: fromAddress(env),
      to: [to],
      reply_to: SUPPORT_EMAIL,
      subject,
      text,
      html,
    }),
  });
  if (!res.ok) {
    console.error("[order-lookup] resend failed", res.status);
    return false;
  }
  return true;
}

async function sendViaCloudflareEmail(
  env: Env,
  to: string,
  subject: string,
  text: string,
  html: string,
): Promise<boolean> {
  if (typeof env.EMAIL?.send !== "function") return false;
  const from = fromAddress(env);
  const raw = buildRawMime(from, to, subject, text, html);
  const ctor = (globalThis as { EmailMessage?: new (from: string, to: string, raw: string) => unknown }).EmailMessage;
  if (typeof ctor !== "function") {
    console.error("[order-lookup] EMAIL binding is set but EmailMessage is unavailable");
    return false;
  }
  await env.EMAIL.send(new ctor(from, to, raw));
  return true;
}

/** Prefer Resend. Fall back to the Cloudflare Email binding. */
export async function sendMail(
  env: Env,
  to: string,
  message: { subject: string; text: string; html: string },
): Promise<boolean> {
  if (env.RESEND_API_KEY?.trim()) {
    const sent = await sendViaResend(env, to, message.subject, message.text, message.html);
    if (sent) return true;
  }
  return sendViaCloudflareEmail(env, to, message.subject, message.text, message.html);
}
