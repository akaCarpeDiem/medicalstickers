#!/usr/bin/env python3
"""Bottle mockups for product pages: puts each real sticker (stickers/<slug>.webp) on the hero bottle photo using the
same StickerBottle code the homepage animation uses (assets/hero-bottle/sticker-bottle.js, reduced motion, held frame),
then crops a square around the bottle -> stickers/bottle/<slug>.webp (800x800). No generated imagery.
Run from the repo root: python3 tools/make_bottle_mockups.py [slug ...]   (needs Pillow + Playwright + Chrome)"""
import json, base64, io, sys, os, threading, functools, tempfile, http.server
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT = os.getcwd(); TMP = tempfile.mkdtemp()
cat = json.load(open('tools/catalog.json')); only = sys.argv[1:]
for p in cat:   # trim transparent margins so every design is sized like the hero stickers
    im = Image.open('.' + p['image']).convert('RGBA'); im.crop(im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()).save(f"{TMP}/{p['slug']}.png")
open(f'{TMP}/render.html', 'w').write('''<!doctype html><body style="margin:0"><div id="b" style="width:1519px"></div><script src="/site/assets/hero-bottle/sticker-bottle.js"></script><script>
window.render=function(src){return new Promise(function(res){var el=document.getElementById('b');el.innerHTML='';var h=StickerBottle.mount(el,{base:'/site/assets/hero-bottle/base.jpg',startAt:1200,stickers:[src],label:''});
var t0=performance.now();(function c(){if(performance.now()-t0>1500){h.stop();res(h.canvas.toDataURL('image/png'))}else setTimeout(c,100)})()})}</script>''')
os.symlink(ROOT, f'{TMP}/site')
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=TMP))
threading.Thread(target=srv.serve_forever, daemon=True).start(); base = f'http://127.0.0.1:{srv.server_port}'
os.makedirs('stickers/bottle', exist_ok=True)
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    pg = b.new_context(viewport={'width': 1600, 'height': 1100}, reduced_motion='reduce').new_page()
    pg.goto(base + '/render.html'); pg.wait_for_function('window.StickerBottle && window.render')
    for p in cat:
        if only and p['slug'] not in only: continue
        url = pg.evaluate('s => render(s)', f"/{p['slug']}.png")
        im = Image.open(io.BytesIO(base64.b64decode(url.split(',')[1]))).convert('RGB')   # 1519x1036, bottle centred at x=602
        im.crop((84, 0, 1120, 1036)).resize((800, 800), Image.LANCZOS).save(f"stickers/bottle/{p['slug']}.webp", 'WEBP', quality=80, method=6)
        print(p['slug'])
    b.close()
srv.shutdown()
