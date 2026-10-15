#!/usr/bin/env python3
"""Swap medicalstickers.shop (static Astro output) to the 48 Printful products + direct Stripe checkout.
Run from the repo root. Idempotent-ish: works on the Etsy-era pages (keeps a pristine copy of templates)."""
import json, re, os, glob, html, shutil
ROOT = os.getcwd()
CAT = json.load(open('/workspace/medicalstickers-printful/site-catalog.json'))
E = html.escape
SPEC = {"emergency":"Emergency / ER","nursing":"Nursing","night-shift":"Night Shift","icu":"ICU","ems":"EMS / Paramedic","respiratory":"Respiratory Therapy","lab":"Lab / Phlebotomy","radiology":"Radiology / CT / MRI","pharmacy":"Pharmacy","pediatrics":"Pediatrics","ld-nicu":"L&D / NICU","or-pacu":"OR / PACU","general":"General Healthcare","dental":"Dental"}
COLL = {"dark-humor":"Dark Humor","skeleton":"Skeleton Series","retro":"Retro Medical","minimal":"Minimal","cute-playful":"Cute / Playful","anatomy":"Anatomy","night-shift":"Night Shift","clinical-sarcasm":"Clinical Sarcasm"}
FROM = "$5.75"
def money(x): return f"${x:.2f}"
def desc(p):
    return (f"{p['title']} as a die-cut satin vinyl sticker, cut to the shape of the art. "
            f"Pick 3″ × 3″ for a badge reel, phone case, or clipboard, or 4″ × 4″ for a laptop, water bottle, or locker.")

# ---------- helpers ----------
def html_files():
    return [f for f in glob.glob('**/*.html', recursive=True) if not f.startswith('.git')]
def strip_uc(s):
    s = s.replace('<link rel="stylesheet" href="/assets/ms-uc-note.css">', '')
    while True:
        i = s.find('<div class="ms-uc"')
        if i < 0: break
        depth = 0; j = i
        for m in re.finditer(r'<div\b|</div>', s[i:]):
            depth += 1 if m.group(0) == '<div' else -1
            if depth == 0: j = i + m.end(); break
        s = s[:i] + s[j:].lstrip('\n')
    return s
def card(p):
    s = p['specialty']; c = p['collection']
    search = " ".join([p['title'].lower(), SPEC[s].lower(), COLL[c].lower(), s, c, p['slug'].replace('-', ' '), "die cut sticker 3x3 4x4"])
    badge = '<div class="absolute top-1 left-1 flex flex-col items-start gap-1"><span class="rounded-full bg-ink px-2 py-0.5 text-[10px] font-semibold tracking-wide text-white uppercase">Bestseller</span></div>' if p['bestseller'] else ''
    return (f'<article class="flex h-full flex-col rounded-2xl border border-line bg-card p-3 sm:p-4" data-product data-specialty="{s}" data-collection="{c}" data-new="1" data-bestseller="{1 if p["bestseller"] else 0}" data-price="5.75" data-title="{E(p["title"])}" data-search="{E(search)}">'
            f'<a href="/products/{p["slug"]}/" class="group block"><div class="relative grid aspect-square place-items-center"><img src="{p["thumb"]}" alt="{E(p["title"])} sticker" width="400" height="400" class="sticker-shadow h-[88%] w-[88%] object-contain transition group-hover:-translate-y-0.5" loading="lazy">{badge}</div>'
            f'<h3 class="mt-2 font-serif text-[1.05rem] leading-snug text-ink group-hover:text-red-dark">{E(p["title"])}</h3></a>'
            f'<p class="mt-1 text-sm text-muted"><a class="hover:text-ink" href="/specialties/{s}/">{E(SPEC[s])}</a><span aria-hidden="true"> · </span><a class="hover:text-ink" href="/collections/{c}/">{E(COLL[c])}</a></p>'
            f'<div class="mt-auto flex items-end justify-between gap-3 pt-3"><p class="font-semibold text-red">From {FROM}<span class="mt-0.5 block text-[10px] font-medium tracking-wide text-muted uppercase">3″ or 4″</span></p>'
            f'<a class="inline-flex min-h-11 items-center text-sm font-semibold text-red hover:text-red-dark" href="/products/{p["slug"]}/">Choose size<span aria-hidden="true"> →</span></a></div></article>')
def config():
    return json.dumps({"directEnabled": True, "checkoutEndpoint": "/api/checkout", "newsletterPreview": True,
        "products": [{"slug": p["slug"], "title": p["title"], "image": p["thumb"],
                      "variants": [{"id": v["sync_variant_id"], "size": v["size"], "price": v["price"]} for v in p["variants"]]} for p in CAT]},
        ensure_ascii=False, separators=(',', ':'))
GRID_OPEN = '<div class="grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-5">'
def replace_grid(s, opener, items_html):
    i = s.find(opener)
    if i < 0: return s, False
    start = i + len(opener); depth = 1; j = start
    for m in re.finditer(r'<div\b|</div>', s[start:]):
        depth += 1 if m.group(0) == '<div' else -1
        if depth == 0: j = start + m.start(); break
    return s[:start] + items_html + s[j:], True
EMPTY = '<p class="col-span-2 rounded-2xl border border-line bg-card px-4 py-8 text-center text-muted lg:col-span-4">No stickers for this one yet. <a class="font-semibold text-red" href="/shop/">See the whole board</a>.</p>'

# ---------- copy text: Etsy era -> direct checkout ----------
TEXT = [
 ('Sample price. The live Etsy listing is the price you pay.', ''),
 ('Checkout currently processed securely through Etsy. This page keeps a direct-checkout cart for later.', 'Secure checkout through Stripe. Free U.S. shipping on orders $25+.'),
 ('Checkout currently processed securely through Etsy.', 'Secure checkout through Stripe.'),
 ('Turn on JavaScript to see items saved in this browser, or shop the Etsy store from the header.', 'Turn on JavaScript to see items saved in this browser and check out.'),
 ('Shop our Etsy store ↗', 'Shop all stickers'),
 ('Shop our Etsy store', 'Shop all stickers'),
 ('Buy on Etsy', 'Shop stickers'),
 ('MedicalStickers.shop is not affiliated with, endorsed by, or sponsored by Etsy, Inc. Sample prices shown until listings are final. ', ''),
 ('Prices on this preview are samples. The Etsy listing is the price you pay once it is connected.', 'Every sticker comes in 3″ × 3″ ($5.75) or 4″ × 4″ ($6.50). The price in your cart is the price you pay, plus shipping and any tax shown at checkout.'),
 ('Options listed on Etsy: 2 inch, 3 inch.', 'Sizes: 3″ × 3″ and 4″ × 4″.'),
 ('Choose Buy on Etsy. Checkout currently runs on Etsy, which handles payment, reviews, and tracking. This website is the brand home.', 'Pick a size on the sticker page, add it to your cart, and check out. Payment is handled securely by Stripe, and your order is printed and shipped by our fulfillment partner, Printful.'),
 ('Are you endorsed by Etsy?', 'Who prints and ships my order?'),
 ('No. We are an independent seller. Etsy is a marketplace we use for checkout. Etsy® is a trademark of Etsy, Inc.', 'Orders are printed and shipped by Printful, our print-on-demand partner. Payments are processed by Stripe; we never see your full card number.'),
 ('Free U.S. shipping on orders $25+ inside the United States, as offered on the Etsy listing. Processing time and carriers are confirmed at Etsy checkout.', 'Free U.S. shipping on orders $25+. Orders under $25 ship for a flat $4.99.'),
 ('Unused stickers can be returned within 14 days of delivery. See the returns page. If the order was placed on Etsy, start there so the receipt stays attached.', 'If a sticker arrives damaged or misprinted, email us within 14 days of delivery and we will make it right. See the returns page.'),
 ('If international shipping is offered, it appears at Etsy checkout. We don&#39;t promise a country that the listing doesn&#39;t ship to.', 'We ship within the United States for now.'),
 ('The plan is durable vinyl. Exact material, finish, and size are confirmed on each Etsy listing so the claim matches the object you receive.', 'Die-cut satin vinyl stickers, printed to order. Each design comes in 3″ × 3″ and 4″ × 4″.'),
 ('Orders placed on Etsy are easiest to track from your Etsy receipt. For everything else, email is the direct line.', 'Tracking is emailed when your order ships. For everything else, email is the direct line.'),
 ('Orders are currently completed on Etsy. The shipping method you choose there is the one that applies. This page is the plain-language version.', 'Orders are paid on this site through Stripe and printed and shipped by Printful. This page is the plain-language version.'),
 ('Free U.S. shipping on orders $25+ when the offer is shown on the listing. The threshold is set in the shop settings and can change. Tax, if any, is calculated by Etsy at checkout.', 'Free U.S. shipping on orders $25+. Orders under $25 ship for a flat $4.99. Any tax is shown at checkout before you pay.'),
 ('Plan on a few business days before a package moves, unless the listing says otherwise. Weekends and hospital holidays are not promised as ship days.', 'Stickers are printed to order. Plan on a few business days before a package moves. Weekends and holidays are not ship days.'),
 ("The United States is the home lane. International shipping appears at Etsy checkout only when that listing offers it. We don't collect a second shipping address on this website.", 'We ship within the United States for now. Your shipping address is collected at checkout.'),
 ("Tracking, when the carrier provides it, shows on your Etsy receipt. We don't run a separate tracking portal on this site yet.", 'Tracking, when the carrier provides it, is emailed to you when your order ships.'),
 ('with your Etsy order number. We\'ll look with you.', 'with your order email and date. We\'ll look with you.'),
 ('with your Etsy order number. We&#39;ll look with you.', 'with your order email and date. We&#39;ll look with you.'),
 ('If you checked out on Etsy, open the order there and message the shop, or email', 'Email'),
 ('with the Etsy order number. Keeping the request on the same order avoids a second thread.', 'with your order email and date, and a photo if something arrived damaged.'),
]

def main():
    # template product page before we delete products/
    TPL = 'lab-life'
    tpl_prod = open(f'products/{TPL}/index.html').read() if os.path.exists(f'products/{TPL}/index.html') else open('/workspace/medicalstickers-printful/site/product-template.html').read()
    open('/workspace/medicalstickers-printful/site/product-template.html', 'w').write(tpl_prod)
    old_slugs = [os.path.basename(d.rstrip('/')) for d in glob.glob('products/*/')]
    new_slugs = {p['slug'] for p in CAT}
    shutil.rmtree('products', ignore_errors=True)
    for f in glob.glob('stickers/*.png'): os.remove(f)
    cfg = config()
    for f in html_files():
        s = open(f).read(); o = s
        s = strip_uc(s)
        s = re.sub(r'(<script id="shop-config" type="application/json">).*?(</script>)', lambda m: m.group(1) + cfg + m.group(2), s, flags=re.S)
        s = s.replace('/_astro/BaseLayout.astro_astro_type_script_index_0_lang.DMc51piq.js', '/_astro/site-cart.v2.js')
        for a, b in TEXT: s = s.replace(a, b)
        # any remaining Etsy shop links -> shop page
        s = re.sub(r'href="https://www\.etsy\.com/shop/medicalstickershop"( target="_blank")?( rel="noopener noreferrer")?', 'href="/shop/"', s)
        s = s.replace('<span aria-hidden="true">↗</span><span class="sr-only"> (opens in a new tab)</span>', '')
        if s != o: open(f, 'w').write(s)
    # shop grid
    s = open('shop/index.html').read()
    s, ok = replace_grid(s, '<div data-product-grid class="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-5">', ''.join(card(p) for p in CAT)); assert ok
    s = re.sub(r'<p data-result-count class="text-muted">\d+ stickers</p>', f'<p data-result-count class="text-muted">{len(CAT)} stickers</p>', s)
    if 'value="dental"' not in s: s = s.replace('<option value="general">General Healthcare</option>', '<option value="general">General Healthcare</option>')
    open('shop/index.html', 'w').write(s)
    # specialties / collections
    for kind, key in (('specialties', 'specialty'), ('collections', 'collection')):
        for d in glob.glob(f'{kind}/*/index.html'):
            slug = d.split('/')[1]; items = [p for p in CAT if p[key] == slug]
            s = open(d).read()
            s, ok = replace_grid(s, GRID_OPEN, ''.join(card(p) for p in items) or EMPTY)
            if not ok: print('WARN no grid', d)
            open(d, 'w').write(s)
    # product pages
    tpl = strip_uc(tpl_prod)
    tpl = re.sub(r'(<script id="shop-config" type="application/json">).*?(</script>)', lambda m: m.group(1) + cfg + m.group(2), tpl, flags=re.S)
    tpl = tpl.replace('/_astro/BaseLayout.astro_astro_type_script_index_0_lang.DMc51piq.js', '/_astro/site-cart.v2.js')
    for a, b in TEXT: tpl = tpl.replace(a, b)
    tpl = re.sub(r'href="https://www\.etsy\.com/shop/medicalstickershop"( target="_blank")?( rel="noopener noreferrer")?', 'href="/shop/"', tpl)
    i = tpl.find('<main'); j = tpl.find('</main>')
    for p in CAT:
        s_, c_ = p['specialty'], p['collection']
        related = [q for q in CAT if q['specialty'] == s_ and q['slug'] != p['slug']][:4]
        if len(related) < 4: related += [q for q in CAT if q['collection'] == c_ and q['slug'] != p['slug'] and q not in related][:4 - len(related)]
        radios = ''.join(
            f'<label class="flex min-h-11 cursor-pointer items-center justify-between gap-3 rounded-xl border border-line bg-card px-4 py-2 has-[:checked]:border-red"><span><input type="radio" name="size" value="{v["sync_variant_id"]}" data-size="{v["size"]}" data-price="{v["price"]}" class="mr-2 accent-[#c8102e]"{" checked" if k == 0 else ""}><span class="font-medium">{v["size"]}</span></span><span class="font-semibold text-red">{money(v["price"])}</span></label>'
            for k, v in enumerate(p['variants']))
        badge = '<div class="flex flex-wrap gap-2"><span class="rounded-full bg-ink px-3 py-1 text-xs font-semibold tracking-wide text-white uppercase">Bestseller</span></div>' if p['bestseller'] else ''
        main = (f'<main id="main"><article class="container-shop py-8 sm:py-12"><nav aria-label="Breadcrumb" class="text-sm text-muted"><ol class="flex flex-wrap items-center gap-x-2 gap-y-1"><li><a class="hover:text-ink" href="/">Home</a></li><li aria-hidden="true">/</li><li><a class="hover:text-ink" href="/shop/">Shop</a></li><li aria-hidden="true">/</li><li><a class="hover:text-ink" href="/specialties/{s_}/">{E(SPEC[s_])}</a></li><li aria-hidden="true">/</li><li class="text-ink">{E(p["title"])}</li></ol></nav>'
                f'<div class="mt-6 grid items-start gap-8 lg:grid-cols-2"><div class="rounded-3xl border border-line bg-card p-6 sm:p-10"><img src="{p["image"]}" alt="{E(p["title"])} die-cut sticker" width="800" height="800" class="sticker-shadow mx-auto w-full max-w-md object-contain"></div><div>{badge}'
                f'<h1 class="mt-3 font-serif text-4xl leading-tight sm:text-5xl">{E(p["title"])}</h1><p class="mt-3 text-sm text-muted"><a class="font-semibold text-ink hover:text-red" href="/specialties/{s_}/">{E(SPEC[s_])}</a><span aria-hidden="true"> · </span><a class="font-semibold text-ink hover:text-red" href="/collections/{c_}/">{E(COLL[c_])}</a></p>'
                f'<p class="mt-4 text-2xl font-semibold text-red" data-price-display>{money(p["variants"][0]["price"])}</p>'
                f'<p class="mt-4 max-w-xl leading-relaxed text-muted">{E(desc(p))}</p>'
                f'<fieldset class="mt-5 grid max-w-md gap-2" data-size-picker><legend class="mb-2 text-xs font-semibold tracking-wide text-muted uppercase">Size</legend>{radios}</fieldset>'
                f'<dl class="mt-4 grid max-w-md grid-cols-2 gap-3 text-sm"><div class="rounded-xl bg-card px-3 py-2"><dt class="text-muted">Type</dt><dd class="font-medium">Die-cut sticker</dd></div><div class="rounded-xl bg-card px-3 py-2"><dt class="text-muted">Finish</dt><dd class="font-medium">Satin vinyl</dd></div></dl>'
                f'<div class="mt-6 flex flex-col items-start gap-3"><button type="button" class="btn btn-primary" data-add-cart data-slug="{p["slug"]}" data-title="{E(p["title"])}" data-image="{p["thumb"]}" data-variant="{p["variants"][0]["sync_variant_id"]}" data-size="{p["variants"][0]["size"]}" data-price="{p["variants"][0]["price"]}">Add to cart</button>'
                f'<p class="max-w-md text-sm leading-relaxed text-muted">Secure checkout through Stripe. Printed to order and shipped by Printful. Free U.S. shipping on orders $25+.</p></div>'
                f'<p class="mt-4 max-w-md text-sm leading-relaxed text-muted">Stickers are novelty goods. They are not medical devices and not a substitute for training, protocol, or judgment.</p></div></div>'
                f'<section class="mt-14" aria-labelledby="related-heading"><h2 id="related-heading" class="font-serif text-3xl">Also on this unit</h2><div class="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-5">{"".join(card(q) for q in related)}</div></section></article>'
                '<script type="module">const f=document.querySelector("[data-size-picker]"),b=document.querySelector("[data-add-cart]"),d=document.querySelector("[data-price-display]");f&&f.addEventListener("change",e=>{const r=e.target;if(!r.matches("input[name=size]"))return;b.dataset.variant=r.value;b.dataset.size=r.dataset.size;b.dataset.price=r.dataset.price;d.textContent=new Intl.NumberFormat("en-US",{style:"currency",currency:"USD"}).format(Number(r.dataset.price))});</script></main>')
        page = tpl[:i] + main + tpl[j + len('</main>'):]
        # head: title/description/canonical/og
        page = re.sub(r'<title>.*?</title>', f'<title>{E(p["title"])} Sticker | MedicalStickers.shop</title>', page, flags=re.S)
        page = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + E(desc(p)) + m.group(2), page)
        page = re.sub(r'(<meta property="og:title" content=")[^"]*(")', lambda m: m.group(1) + E(p["title"]) + ' Sticker' + m.group(2), page)
        page = re.sub(r'(<meta property="og:description" content=")[^"]*(")', lambda m: m.group(1) + E(desc(p)) + m.group(2), page)
        page = page.replace(f'/products/{TPL}/', f'/products/{p["slug"]}/').replace(f'/stickers/{TPL}', '/stickers/' + p['slug'])
        page = re.sub(r'<script type="application/ld\+json">.*?</script>', '', page, flags=re.S)
        ld = {"@context": "https://schema.org", "@type": "Product", "name": p["title"] + " Sticker", "image": "https://medicalstickers.shop" + p["image"], "description": desc(p), "brand": {"@type": "Brand", "name": "MedicalStickers.shop"},
              "offers": [{"@type": "Offer", "priceCurrency": "USD", "price": f'{v["price"]:.2f}', "name": v["size"], "availability": "https://schema.org/InStock", "url": f"https://medicalstickers.shop/products/{p['slug']}/"} for v in p["variants"]]}
        page = page.replace('</head>', '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script></head>', 1)
        os.makedirs(f'products/{p["slug"]}', exist_ok=True)
        open(f'products/{p["slug"]}/index.html', 'w').write(page)
    # redirects for retired product URLs
    gone = sorted(set(old_slugs) - new_slugs)
    red = open('_redirects').read() if os.path.exists('_redirects') else ''
    red = re.sub(r'# retired Etsy-era products.*?# end retired\n', '', red, flags=re.S)
    red += '# retired Etsy-era products\n' + ''.join(f'/products/{g}/ /shop/ 301\n/products/{g} /shop/ 301\n' for g in gone) + '# end retired\n'
    open('_redirects', 'w').write(red)
    print('old products', len(old_slugs), 'retired->redirect', len(gone), 'new', len(CAT))
if __name__ == '__main__': main()
