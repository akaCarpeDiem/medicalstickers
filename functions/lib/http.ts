export type Env = {
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
  PRINTFUL_TOKEN?: string;
  PRINTFUL_STORE_ID?: string;
  /** Comma-separated ISO country codes for Stripe shipping_address_collection. Default: US */
  SHIPPING_COUNTRIES?: string;
  PUBLIC_ORIGIN?: string;
  /**
   * Transactional email for order lookup. Either this or the EMAIL binding is required
   * before a receipt can be resent. The from-address domain must be verified with Resend.
   */
  RESEND_API_KEY?: string;
  /** Defaults to Medical Stickers <support@medicalstickers.shop> */
  ORDER_FROM_EMAIL?: string;
  /**
   * Optional Cloudflare Email Workers binding (Pages → Settings → Bindings).
   * Used when RESEND_API_KEY is not set. `from` must be an address on medicalstickers.shop.
   */
  EMAIL?: {
    send(message: unknown): Promise<void>;
  };
};

export function json(data: unknown, status = 200, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...headers },
  });
}

export function methodNotAllowed(allow: string) {
  return json({ error: "Method not allowed" }, 405, { allow });
}
