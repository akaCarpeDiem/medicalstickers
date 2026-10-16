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
print('fixups done')
