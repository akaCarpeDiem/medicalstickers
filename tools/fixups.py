#!/usr/bin/env python3
"""Second pass after build_catalog.py: home cards, header button icon, footer + policy copy, meta descriptions, thanks page."""
import json, re, glob, html
CAT = json.load(open('/workspace/medicalstickers-printful/site-catalog.json')); BY = {p['code']: p for p in CAT}; E = html.escape
R = [
 # header button: drop Etsy logo + "opens in new tab"
 (re.compile(r'<svg fill="#F1641E" class="etsy-store-btn__logo".*?</svg>', re.S), ''),
 ('<span class="etsy-store-btn__label">Shop all stickers</span><span class="sr-only"> (opens in a new tab)</span>', '<span class="etsy-store-btn__label">Shop all stickers</span>'),
 # footer
 ('<p>Some purchases are completed on Etsy, which handles that checkout, reviews, and tracking.MedicalStickers.shop is not affiliated with, endorsed by, or sponsored by Etsy, Inc. Etsy® is a trademark of Etsy, Inc. Designs are independent and are not affiliated with any hospital, health system, school, or brand.</p>',
  '<p>Payments are processed securely by Stripe. Stickers are printed to order and shipped by Printful. Designs are independent and are not affiliated with any hospital, health system, school, or brand.</p>'),
 ('<p>Prices shown are samples until listings are final. Sticker images are sample artwork to replace with photos of the printed designs. The Etsy listing, once connected, is the record for price, size, and materials.</p>',
  '<p>Every design comes as a die-cut satin vinyl sticker in 3″ × 3″ ($5.75) or 4″ × 4″ ($6.50). Free U.S. shipping on orders $25+.</p>'),
 ('<p class="fine">Checkout goes to <a href="/shop/">our Etsy shop</a>. Novelty stickers, not medical devices. © 2026 MedicalStickers.shop</p>',
  '<p class="fine">Secure checkout by Stripe. Printed and shipped by Printful. Novelty stickers, not medical devices. © 2026 MedicalStickers.shop</p>'),
 ('aria-label="Cart — checkout on Etsy"', 'aria-label="Shop stickers"'),
 # meta descriptions
 ('Your MedicalStickers.shop cart. Checkout currently runs through Etsy.', 'Your MedicalStickers.shop cart. Secure checkout through Stripe.'),
 ('Terms for using MedicalStickers.shop, including Etsy checkout, novelty stickers, and trademark notices.', 'Terms for using MedicalStickers.shop, including orders, checkout, novelty stickers, and trademark notices.'),
 ('Answers about buying MedicalStickers.shop stickers, Etsy checkout, shipping, returns, and what the stickers are not.', 'Answers about buying MedicalStickers.shop stickers, checkout, shipping, returns, and what the stickers are not.'),
 ('Accounts open when direct checkout does. Orders placed today are tracked on Etsy.', 'No account needed. Check out as a guest; order updates come by email.'),
 ("Privacy policy for MedicalStickers.shop. What we collect, what we don't, and how Etsy checkout is separate.", "Privacy policy for MedicalStickers.shop. What we collect, what we don't, and how Stripe and Printful handle your order."),
 ('Returns for MedicalStickers.shop. Unused stickers can come back within 14 days. Etsy orders start from the Etsy receipt.', 'All sales are final. Damaged, misprinted, or wrong stickers are replaced or refunded within 14 days of delivery.'),
 ('Shipping for MedicalStickers.shop. Free U.S. shipping on orders $25+. Orders currently check out on Etsy.', 'Shipping for MedicalStickers.shop. Free U.S. shipping on orders $25+; $4.99 flat under $25.'),
 # policy bodies
 ("<p>MedicalStickers.shop is an independent sticker shop for healthcare workers. The website is the brand home. Purchases are currently completed on Etsy unless a product page clearly offers direct checkout. Etsy's own terms cover that transaction, including payment processing.</p>",
  "<p>MedicalStickers.shop is an independent sticker shop for healthcare workers. Purchases are completed on this site. Payments are processed by Stripe, and orders are printed and shipped by our fulfillment partner, Printful.</p>"),
 ('<p>An order exists when Etsy (or, later, our own checkout) accepts payment. A product page is an invitation to buy, not a promise that a listing is still open. Descriptions are written in a dry, joking voice. They are not care plans. If a sample-price note is showing, the Etsy listing is the price that controls.</p>',
  '<p>An order exists when our checkout accepts payment. A product page is an invitation to buy, not a promise that a design will stay available. Descriptions are written in a dry, joking voice. They are not care plans. The price shown at checkout, before you pay, is the price that controls.</p>'),
 ('<p>Checkout may occur on Etsy. MedicalStickers.shop is not affiliated with, endorsed by, or sponsored by Etsy, Inc. Etsy® is a trademark of Etsy, Inc. We use the name only to tell you where checkout happens.</p>',
  '<p>Checkout is provided by Stripe and fulfillment by Printful. MedicalStickers.shop is not affiliated with, endorsed by, or sponsored by Stripe or Printful; we use their names only to tell you who handles payment and shipping.</p>'),
 ('<h2>Etsy and other sites</h2>', '<h2>Payments, fulfillment, and other sites</h2>'),
 ("<p>When you choose Shop stickers, you leave this site for Etsy. Etsy's privacy policy covers that checkout, including payment, reviews, and order messages.MedicalStickers.shop is not endorsed by Etsy. Social links (Instagram, TikTok, Pinterest) are their own sites with their own policies.</p>",
  "<p>When you check out, you go to a secure Stripe checkout page. Stripe collects your payment details, email, and shipping address under its own privacy policy; we never see your full card number. To fill your order we share your name, shipping address, email, and the items you bought with Printful, which prints and ships it. Your cart is stored only in this browser (local storage) until you check out. Social links are their own sites with their own policies.</p>"),
 ('<p class="pb-3 text-sm leading-relaxed text-muted">Choose Shop stickers. Checkout currently runs on Etsy, which handles payment, reviews, and tracking. This website is the brand home.</p>',
  '<p class="pb-3 text-sm leading-relaxed text-muted">Open a sticker, choose 3″ × 3″ or 4″ × 4″, add it to your cart, and check out. Payment is handled securely by Stripe.</p>'),
 ("Staff accounts aren't open yet. When direct checkout arrives, this is where orders on this site will live. For now, track a purchase from your Etsy receipt.",
  "There are no accounts to manage. Check out as a guest; your receipt and shipping updates arrive by email. Questions about an order? Write to support@medicalstickers.shop."),
 ("<p>Refunds go back to the original payment method after we have the return. Etsy processes those payments, so the timing follows Etsy's payout rules. We don't refund shipping you already used unless the mistake was ours.</p>",
  "<p>Refunds go back to the original payment method through Stripe, usually within 5–10 business days of approval depending on your bank. We don't refund shipping you already used unless the mistake was ours.</p>"),
 ('Right now, checkout runs through Etsy so payment, reviews, and tracking sit somewhere sturdy while the brand lives here.', 'Checkout runs right here: Stripe handles payment, and Printful prints and ships every order.'),
]
def home_card(p, new=False):
    t = E(p['title'])
    return (f'        <article class="card" data-product="{t}">\n' + ('          <span class="badge-new">New</span>\n' if new else '') +
            f'          <a href="/products/{p["slug"]}/"><div class="die"><img src="{p["thumb"]}" alt="{t} sticker" loading="lazy" /></div></a>\n'
            f'          <h3>{t}</h3>\n          <div class="meta"><span class="price">From $5.75</span><a class="plus" href="/products/{p["slug"]}/" aria-label="Choose a size for {t}">+</a></div>\n        </article>\n')
def swap_div(s, opener, inner):
    i = s.find(opener); assert i >= 0, opener
    st = i + len(opener); d = 1
    for m in re.finditer(r'<div\b|</div>', s[st:]):
        d += 1 if m.group(0) == '<div' else -1
        if d == 0: return s[:st] + '\n' + inner + '      ' + s[st + m.start():]
# ---- 2026-10-21: homepage cart, no Account links, GA consent mode, WebP images, per-sticker share images,
# ---- Night Shift collection title, shipping/returns in Product JSON-LD. Idempotent; runs last (also: --oct21-only).
GA_SNIPPET = """<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  var msConsent = null; try { msConsent = localStorage.getItem('ms-consent'); } catch (e) {}
  gtag('consent', 'default', { analytics_storage: msConsent === 'all' ? 'granted' : 'denied', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied' });
  gtag('js', new Date());
  gtag('config', 'G-Y6495SSEDC', { page_location: location.origin + location.pathname, page_referrer: document.referrer.split('?')[0] });
  document.addEventListener('click', function (e) { var b = e.target.closest && e.target.closest('[data-consent="all"]'); if (b) gtag('consent', 'update', { analytics_storage: 'granted' }); });
</script>"""
OFFER_EXTRA = {
    "shippingDetails": {"@type": "OfferShippingDetails", "shippingRate": {"@type": "MonetaryAmount", "value": "4.99", "currency": "USD"}, "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "US"}},
    # matches Merchant Center (defective items only, 14 days, US) and /returns/ (customer keeps the item: KeepProduct).
    # of.update() below replaces the whole policy, so an older ReturnByMail value is converted on every run.
    "hasMerchantReturnPolicy": {"@type": "MerchantReturnPolicy", "applicableCountry": "US", "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow", "merchantReturnDays": 14, "returnFees": "https://schema.org/FreeReturn", "returnMethod": "https://schema.org/KeepProduct", "merchantReturnLink": "https://medicalstickers.shop/returns/"},
}
HOME_CART_BTN = ('<button type="button" class="iconbtn" data-cart-button aria-expanded="false" aria-controls="cart-drawer"><span class="sr">Open cart</span>\n'
    '        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1c1917" stroke-width="1.8" aria-hidden="true"><path d="M6 7h15l-1.5 9h-12z"/><path d="M6 7L5 4H2"/><circle cx="9" cy="20" r="1.3" fill="#1c1917"/><circle cx="17" cy="20" r="1.3" fill="#1c1917"/></svg>\n'
    '        <span class="badge hidden" data-cart-count></span>\n      </button>')
def _between(s, start, end_marker):
    i = s.find(start); assert i >= 0, start
    j = s.find(end_marker, i); assert j >= 0, end_marker
    return s[i:j + len(end_marker)]
def oct21_fixes():
    import os
    shop = open('shop/index.html').read()
    drawer = _between(shop, '<div id="cart-drawer"', '</div></div></div>')          # backdrop + panel
    cookie = _between(shop, '<div data-cookie', '</div></div></div>')
    config = _between(shop, '<script id="shop-config" type="application/json">', '</script>')
    loader = '<script type="module" src="/_astro/site-cart.v2.js"></script>'
    assert loader in shop
    for f in glob.glob('**/*.html', recursive=True):
        s = open(f).read(); o = s
        # 3. GA follows the cookie choice (gtag/js loader left as is)
        s = re.sub(r"<script>\s*window\.dataLayer = window\.dataLayer \|\| \[\];.*?gtag\('config', 'G-Y6495SSEDC'.*?</script>", lambda m: GA_SNIPPET, s, count=1, flags=re.S)
        # 2. no Account links (the /account/ page stays, noindex)
        s = re.sub(r'\s*<a class="iconbtn icon-account" href="/account/"[^>]*>.*?</a>', '', s, flags=re.S)
        s = s.replace('<a class="rounded-xl px-2 py-2 hover:bg-card" href="/account/">Account</a>', '')
        s = s.replace('<li><a class="hover:underline" href="/account/">Account</a></li>', '')
        s = re.sub(r'\n[ \t]*<a href="/account/">Account</a>', '', s)
        # 4. WebP logo (PNG kept on disk)
        s = s.replace('src="/assets/home/logo-exact.png"', 'src="/assets/home/logo-exact.webp"')
        if f == 'account/index.html' and '<meta name="robots"' not in s:
            s = s.replace('</head>', '<meta name="robots" content="noindex"></head>', 1)
        if f == 'index.html':
            # 1. homepage cart works like every other page
            s = re.sub(r'<a class="iconbtn" href="/shop/" aria-label="Shop stickers">.*?<span class="badge" id="cart-count">0</span>\s*</a>', lambda m: HOME_CART_BTN, s, flags=re.S)
            if 'ms-home-cart.css' not in s:
                s = s.replace('<link rel="stylesheet" href="/assets/ms-footer-polish.css', '<link rel="stylesheet" href="/assets/ms-home-cart.css?v=20261021">\n<link rel="stylesheet" href="/assets/ms-footer-polish.css', 1)
            s = re.sub(r'\n?<div id="cart-drawer".*?</div></div></div>', '', s, flags=re.S)
            s = re.sub(r'\n?<div data-cookie.*?</div></div></div>', '', s, flags=re.S)
            s = re.sub(r'\n?<script id="shop-config" type="application/json">.*?</script>', '', s, flags=re.S)
            s = s.replace('\n' + loader, '')
            s = s.replace('</body>', '\n'.join([drawer, cookie, config, loader]) + '\n</body>', 1)
            # the homepage's own menu script runs first; stop the cart script's menu handler from toggling it straight back
            s = s.replace("btn.addEventListener('click', function () {\n      setOpen(panel.hidden);", "btn.addEventListener('click', function (e) {\n      e.stopImmediatePropagation();\n      setOpen(panel.hidden);")
            # 4. lighter About image
            s = s.replace('<img src="/assets/home/about-be-a-nurse-they-said.png" alt="Be a nurse, they said. It\'ll be fun, they said. Skeleton nurse sticker" width="360" height="425" />',
                          '<img src="/assets/home/about-be-a-nurse-they-said.webp" alt="Be a nurse, they said. It\'ll be fun, they said. Skeleton nurse sticker" width="360" height="425" loading="lazy" />')
        m = re.fullmatch(r'products/([^/]+)/index\.html', f)
        if m:
            slug = m.group(1); assert os.path.exists(f'og/{slug}.jpg'), f'missing share image og/{slug}.jpg'
            img = f'https://medicalstickers.shop/og/{slug}.jpg'
            # 5. per-sticker share image
            s = s.replace('<meta property="og:image" content="https://medicalstickers.shop/og.png">', f'<meta property="og:image" content="{img}">')
            s = s.replace('<meta name="twitter:image" content="https://medicalstickers.shop/og.png">', f'<meta name="twitter:image" content="{img}">')
            if 'og:image:width' not in s:
                s = s.replace(f'<meta property="og:image" content="{img}">', f'<meta property="og:image" content="{img}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">', 1)
            # 7. shipping + returns on every Offer
            def addoffer(mm):
                d = json.loads(mm.group(1))
                if d.get('@type') == 'Product':
                    offers = d['offers'] if isinstance(d['offers'], list) else [d['offers']]
                    for of in offers: of.update(OFFER_EXTRA)
                return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False).replace('</', '<\\/') + '</script>'
            s = re.sub(r'<script type="application/ld\+json">(.*?)</script>', addoffer, s, flags=re.S)
        if f == 'collections/night-shift/index.html':
            # 6. distinct from the Night Shift specialty page
            s = s.replace('<title>Night Shift stickers · MedicalStickers.shop</title>', '<title>Night Shift collection · MedicalStickers.shop</title>')
            s = s.replace('<meta property="og:title" content="Night Shift stickers · MedicalStickers.shop">', '<meta property="og:title" content="Night Shift collection · MedicalStickers.shop">')
            s = s.replace('<meta name="twitter:title" content="Night Shift stickers · MedicalStickers.shop">', '<meta name="twitter:title" content="Night Shift collection · MedicalStickers.shop">')
        if s != o: open(f, 'w').write(s)
    print('oct21 fixes done')
import sys
# ---- 2026-10-22 (launch audit): home page twitter card; specialty pages with no stickers yet are noindex and left out
# ---- of the sitemap (they come back automatically once they list stickers). Idempotent; runs last (also: --oct22-only).
EMPTY_SPECIALTY = 'No stickers for this one yet.'
def oct22_fixes():
    f = 'index.html'; s = o = open(f).read()
    if 'name="twitter:card"' not in s:
        m = re.search(r'<meta property="og:image" content="([^"]+)" />', s); assert m, 'home og:image'
        t = re.search(r'<meta property="og:title" content="([^"]*)" />', s).group(1)
        d = re.search(r'<meta property="og:description" content="([^"]*)" />', s).group(1)
        s = s.replace(m.group(0), m.group(0) + f'\n<meta name="twitter:card" content="summary_large_image" />\n<meta name="twitter:title" content="{t}" />'
                      f'\n<meta name="twitter:description" content="{d}" />\n<meta name="twitter:image" content="{m.group(1)}" />', 1)
    if s != o: open(f, 'w').write(s)
    empty = []
    for f in sorted(glob.glob('specialties/*/index.html')):
        s = o = open(f).read(); slug = f.split('/')[1]
        if EMPTY_SPECIALTY in s:
            empty.append(slug)
            if '<meta name="robots"' not in s: s = s.replace('<meta name="theme-color"', '<meta name="robots" content="noindex"><meta name="theme-color"', 1)
        if s != o: open(f, 'w').write(s)
    sm = o = open('sitemap-0.xml').read()
    for slug in empty:
        sm = re.sub(r'<url><loc>https://medicalstickers\.shop/specialties/' + re.escape(slug) + r'/</loc>.*?</url>', '', sm, flags=re.S)
    if sm != o: open('sitemap-0.xml', 'w').write(sm)
    print('oct22 fixes done; noindex + out of sitemap:', ', '.join(empty))
if '--oct22-only' in sys.argv:
    oct22_fixes(); sys.exit(0)
if '--oct21-only' in sys.argv:
    oct21_fixes(); sys.exit(0)
# ---- Bigger ideas (2026-10-21, preview first): bottle mockup on product pages, one-line "who it's for" descriptions,
# ---- free-shipping nudge, phone hero order (CSS), homepage header/footer links matching every other page.
def _nav_lists(shop):
    def links(panel_start):
        i = shop.find(panel_start); j = shop.find('</div>', shop.find('<div class="nav-panel">', i))
        return re.findall(r'<a class="block rounded-lg[^"]*" href="([^"]+)">([^<]+)</a>', shop[i:j])
    spec = links('nav-drop-label">Specialties'); coll = links('<summary class="rounded-full px-2.5 py-2 text-sm font-medium hover:bg-card">Collections')
    i = shop.find('<div id="mobile-nav"'); j = shop.find('</header>', i)
    mob_spec = re.findall(r'<a class="rounded-xl px-2 py-2 text-sm hover:bg-card" href="(/specialties/[^"]+)">([^<]+)</a>', shop[i:j])
    assert len(spec) > 10 and len(coll) > 5 and len(mob_spec) > 10, (len(spec), len(coll), len(mob_spec))
    return spec, coll, mob_spec
def bigger_ideas():
    import os, math
    E2 = lambda t: html.escape(t, quote=True)
    desc = json.load(open('tools/descriptions.json'))
    cat = json.load(open('tools/catalog.json')); by_slug = {p['slug']: p for p in cat}
    # free-shipping nudge from the real numbers: functions/lib/stripe.ts threshold (free at >= threshold) and the cheapest variant
    m = re.search(r'FREE_SHIPPING_MIN_CENTS\s*=\s*(\d+)', open('functions/lib/stripe.ts').read()); free_min = int(m.group(1))
    cheapest = min(round(v['price'] * 100) for p in cat for v in p['variants'])
    n_min = math.ceil(free_min / cheapest)
    nudge = f'Free U.S. shipping on orders over ${free_min // 100}. Grab {n_min} or more.'
    shop = open('shop/index.html').read(); spec, coll, mob_spec = _nav_lists(shop)
    for f in glob.glob('products/*/index.html'):
        slug = f.split('/')[1]; prod = by_slug[slug]; line = desc[slug]; s = o = open(f).read()
        title = prod['title']; sizes = ' or '.join(v['size'] for v in prod['variants'])
        # 1. bottle mockup as a second gallery image
        if 'data-bottle-mockup' not in s:
            assert os.path.exists(f'stickers/bottle/{slug}.webp'), slug
            mm = re.search(r'<div class="rounded-3xl border border-line bg-card p-6 sm:p-10"><img src="/stickers/' + re.escape(slug) + r'\.webp"[^>]*></div>', s); assert mm, f
            fig = (f'<figure class="overflow-hidden rounded-3xl border border-line bg-card" data-bottle-mockup><img src="/stickers/bottle/{slug}.webp" '
                   f'alt="{E2(title)} sticker on a green water bottle (mockup)" width="800" height="800" loading="lazy" decoding="async" class="block w-full">'
                   f'<figcaption class="px-4 py-3 text-sm text-muted">Mockup on a water bottle. Comes in {sizes}.</figcaption></figure>')
            s = s[:mm.start()] + '<div class="grid gap-4">' + mm.group(0) + fig + '</div>' + s[mm.end():]
        # 3. free-shipping nudge under the price
        s = re.sub(r'<p class="mt-1 text-sm font-semibold text-ink" data-ship-nudge>.*?</p>', '', s)
        s = re.sub(r'(<p class="mt-4 text-2xl font-semibold text-red" data-price-display>[^<]*</p>)', lambda mm: mm.group(1) + f'<p class="mt-1 text-sm font-semibold text-ink" data-ship-nudge>{E2(nudge)}</p>', s, count=1)
        # 2. one-line "who it's for" description: visible copy + JSON-LD keep the template sentence after it; meta gets the line + short facts
        s = re.sub(r'(<p class="mt-4 max-w-xl leading-relaxed text-muted">)(.*?)(</p>)', lambda mm: mm.group(1) + (mm.group(2) if mm.group(2).startswith(E2(line)) else E2(line) + ' ' + mm.group(2)) + mm.group(3), s, count=1, flags=re.S)
        short = f'{line} Die-cut satin vinyl sticker in {sizes}.'
        for attr in ['name="description"', 'property="og:description"', 'name="twitter:description"']:
            s = re.sub(r'(<meta ' + re.escape(attr) + r' content=")[^"]*(")', lambda mm: mm.group(1) + E2(short) + mm.group(2), s, count=1)
        def ld(mm):
            d = json.loads(mm.group(1))
            if d.get('@type') == 'Product' and not d['description'].startswith(line): d['description'] = line + ' ' + d['description']
            return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False).replace('</', '<\\/') + '</script>'
        s = re.sub(r'<script type="application/ld\+json">(.*?)</script>', ld, s, flags=re.S)
        if s != o: open(f, 'w').write(s)
    # homepage: same menu items, mobile links and footer columns as every other page; phone hero order via CSS
    f = 'index.html'; s = o = open(f).read()
    dd = lambda items: ''.join(f'\n            <a href="{h}">{t}</a>' for h, t in items)
    nav = ('<nav aria-label="Primary">\n      <a href="/">Home</a>\n      <a href="/shop/">Shop</a>\n'
           f'      <div class="drop">\n        <a href="/specialties/">Specialties ▾</a>\n        <div class="menu">{dd(spec)}\n        </div>\n      </div>\n'
           f'      <div class="drop">\n        <a href="/collections/">Collections ▾</a>\n        <div class="menu">{dd(coll)}\n        </div>\n      </div>\n'
           '      <a href="/community/">Community</a>\n      <a href="/about/">About</a>\n      <a href="/contact/">Contact</a>\n    </nav>')
    s = re.sub(r'<nav aria-label="Primary">.*?</nav>', lambda mm: nav, s, count=1, flags=re.S)
    mob = ('<div aria-label="Mobile" class="mobile-links" role="navigation">\n        <a href="/">Home</a>\n        <a href="/shop/">Shop</a>\n        <a href="/community/">Community</a>\n        <a href="/about/">About</a>\n        <a href="/contact/">Contact</a>\n'
           '        <a class="mobile-sub" href="/specialties/">Specialties</a>\n        <div class="mobile-grid">' + ''.join(f'<a href="{h}">{t}</a>' for h, t in mob_spec) + '</div>\n'
           '        <p class="mobile-sub">Collections</p>\n        <div class="mobile-grid mobile-grid-1">' + ''.join(f'<a href="{h}">{t}</a>' for h, t in coll if h != '/collections/') + '</div>\n      </div>')
    s = re.sub(r'<div aria-label="Mobile" class="mobile-links" role="navigation">.*?\n      </div>', lambda mm: mob, s, count=1, flags=re.S)
    fi = shop.find('<footer'); fj = shop.find('</footer>', fi); sf = shop[fi:fj]
    blurb = re.search(r'<p class="mt-4 max-w-sm[^"]*">(.*?)</p>', sf).group(1)
    shop_col = re.findall(r'<li><a class="hover:underline" href="([^"]+)">([^<]+)</a></li>', sf[sf.find('>Shop</h2>'):sf.find('</ul>', sf.find('>Shop</h2>'))])
    visit_col = re.findall(r'<li><a class="hover:underline" href="([^"]+)">([^<]+)</a></li>', sf[sf.find('>Visit</h2>'):sf.find('</ul>', sf.find('>Visit</h2>'))])
    legal = re.findall(r'<li><a class="hover:underline" href="([^"]+)">([^<]+)</a></li>', sf[sf.find('<ul class="flex flex-wrap gap-x-4 gap-y-2">'):sf.find('</ul>', sf.find('<ul class="flex flex-wrap gap-x-4 gap-y-2">'))])
    fine = re.findall(r'<p>(.*?)</p>', sf[sf.find('text-footer-ink/70'):])
    col = lambda name, items: f'      <div>\n        <h3>{name}</h3>' + ''.join(f'\n        <a href="{h}">{t}</a>' for h, t in items) + '\n      </div>\n'
    logo = re.search(r'<a href="/" aria-label="Medical Stickers shop home" class="footer-brand">.*?</a>', s, re.S).group(0)
    foot = ('<div class="wrap foot foot-3">\n      <div>\n        ' + logo + f'\n        <p class="foot-blurb">{blurb}</p>\n        <p style="margin:10px 0 0"><a href="/shop/">Shop all stickers</a></p>\n      </div>\n'
            + col('Shop', shop_col) + col('Visit', visit_col) + '    </div>\n    <div class="wrap">\n        <div class="legal-row">' + ''.join(f'\n          <a href="{h}">{t}</a>' for h, t in legal)
            + '\n        </div>' + ''.join(f'\n      <p class="fine">{t}</p>' for t in fine) + '\n    </div>\n  ')
    i = s.find('<footer>'); j = s.find('</footer>', i); assert i > 0 and j > 0
    s = s[:i + len('<footer>')] + '\n    ' + foot + s[j:]
    if 'ms-home-layout.css' not in s:
        s = s.replace('<link rel="stylesheet" href="/assets/ms-red-theme.css', '<link rel="stylesheet" href="/assets/ms-home-layout.css?v=20261021">\n<link rel="stylesheet" href="/assets/ms-red-theme.css', 1)
        # red theme stays last
        s = s.replace('<link rel="stylesheet" href="/assets/ms-home-layout.css?v=20261021">\n<link rel="stylesheet" href="/assets/ms-red-theme.css?v=20261015r">', '<link rel="stylesheet" href="/assets/ms-red-theme.css?v=20261015r">\n<link rel="stylesheet" href="/assets/ms-home-layout.css?v=20261021">', 1)
    if s != o: open(f, 'w').write(s)
    print('bigger ideas done')
if '--bigger-only' in sys.argv:
    bigger_ideas(); sys.exit(0)
for f in glob.glob('**/*.html', recursive=True):
    s = open(f).read(); o = s
    for a, b in R: s = a.sub(b, s) if hasattr(a, 'sub') else s.replace(a, b)
    if f == 'index.html':
        s = swap_div(s, '<div class="cards">', ''.join(home_card(BY[c]) for c in ['B07', 'B13', 'B01', 'A10', 'B19', 'B15']))
        s = swap_div(s, '<div class="arrivals">', ''.join(home_card(BY[c], True) for c in ['B09', 'B08', 'B21', 'B10', 'B02', 'B11']))
    # no social links until real accounts exist
    s = re.sub(r'<ul class="flex items-center gap-4">(?:<li><a[^>]*(?:instagram|tiktok|pinterest)[^>]*>.*?</a></li>)+</ul>', '', s)
    s = re.sub(r'\s*<div class="news">\s*<div class="social".*?</div>\s*</div>', '', s, flags=re.S)
    # one-color red theme: last stylesheet, right after ms-footer-polish.css
    if 'ms-red-theme.css' not in s:
        s = re.sub(r'(<link rel="stylesheet" href="/assets/ms-footer-polish\.css[^"]*">)', lambda m: m.group(1) + ('\n' if f == 'index.html' else '') + '<link rel="stylesheet" href="/assets/ms-red-theme.css?v=20261015r">', s, count=1)
    if s != o: open(f, 'w').write(s)
# thanks page from the cart page shell
s = open('cart/index.html').read(); i = s.find('<main'); j = s.find('</main>') + 7
main = ('<main id="main"><section class="container-shop max-w-2xl py-12"><p class="eyebrow">Order received</p><h1 class="mt-2 font-serif text-4xl">Thank you. Your stickers are on the board.</h1>'
        '<p class="mt-4 leading-relaxed text-muted">Your payment went through and your order is headed to print. A receipt is on its way to your email, and tracking follows when the package ships. Stickers are printed to order, so give it a few business days before it moves.</p>'
        '<p class="mt-3 leading-relaxed text-muted">Questions about your order? Email <a class="font-semibold text-red" href="mailto:support@medicalstickers.shop">support@medicalstickers.shop</a> with the email you used at checkout.</p>'
        '<div class="mt-6 flex flex-col gap-3 sm:flex-row"><a class="btn btn-primary" href="/shop/">Keep browsing</a><a class="btn btn-secondary" href="/shipping/">Shipping details</a></div></section>'
        '<script>try{localStorage.removeItem("ms-cart-v2")}catch(e){}</script></main>')
s = s[:i] + main + s[j:]
s = re.sub(r'<title>.*?</title>', '<title>Thank you | MedicalStickers.shop</title>', s, flags=re.S)
s = re.sub(r'(<meta name="description" content=")[^"]*', r'\1Thank you for your MedicalStickers.shop order.', s)
s = s.replace('/cart/"', '/thanks/"')
if '<meta name="robots"' not in s: s = s.replace('</head>', '<meta name="robots" content="noindex"></head>', 1)
import os; os.makedirs('thanks', exist_ok=True); open('thanks/index.html', 'w').write(s)
oct21_fixes()  # last, so the thanks page built above gets the same changes
bigger_ideas()
oct22_fixes()
print('fixups done')
