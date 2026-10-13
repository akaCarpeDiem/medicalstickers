var e=`ms-cart-v2`,t=`ms-consent`;function n(){let e=document.getElementById(`shop-config`);return e?.textContent?JSON.parse(e.textContent):{directEnabled:!1,checkoutEndpoint:`/api/checkout`,newsletterPreview:!0,products:[]}}var r=n();try{localStorage.removeItem(`ms-cart`)}catch{}
function i(){try{let t=JSON.parse(localStorage.getItem(e)||`[]`);return Array.isArray(t)?t.filter(e=>e&&e.variant&&e.qty>0):[]}catch{return[]}}
function a(t){localStorage.setItem(e,JSON.stringify(t)),l()}
function o(e){return new Intl.NumberFormat(`en-US`,{style:`currency`,currency:`USD`}).format(e)}
function s(e){return e.reduce((e,t)=>e+t.qty,0)}
function c(e){return String(e??``).replace(/[&<>"']/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`,"'":`&#39;`})[e]??e)}
var FREE=25,SHIP=4.99;
function l(){let e=i(),t=s(e);document.querySelectorAll(`[data-cart-count]`).forEach(e=>{e.textContent=t>0?String(t):``,e.classList.toggle(`hidden`,t===0)});
let n=`
    <div class="rounded-2xl border border-line bg-card p-5">
      <p class="font-serif text-2xl text-ink">Nothing in the cart.</p>
      <p class="mt-2 text-sm leading-relaxed text-muted">Pick a sticker, choose 3″ or 4″, and it will wait here. Free U.S. shipping on orders $25+.</p>
      <div class="mt-4 flex flex-col gap-2 sm:flex-row"><a class="btn btn-primary" href="/shop/">Browse stickers</a></div>
    </div>`,
a=e.map(e=>`
      <div class="flex gap-3 border-b border-line py-3">
        <img src="${c(e.image)}" alt="" width="72" height="72" class="h-[72px] w-[72px] object-contain" />
        <div class="min-w-0 flex-1">
          <a class="font-medium text-ink hover:text-red" href="/products/${c(e.slug)}/">${c(e.title)}</a>
          <p class="text-sm text-muted">${c(e.size)} · ${o(e.price)}</p>
          <div class="mt-2 flex items-center gap-2">
            <button type="button" class="h-9 w-9 rounded-full border border-line" data-qty="-1" data-variant="${c(e.variant)}" aria-label="Decrease quantity">−</button>
            <span>${e.qty}</span>
            <button type="button" class="h-9 w-9 rounded-full border border-line" data-qty="1" data-variant="${c(e.variant)}" aria-label="Increase quantity">+</button>
            <button type="button" class="ml-auto text-sm underline" data-remove="${c(e.variant)}">Remove</button>
          </div>
        </div>
      </div>`).join(``),
u=e.reduce((e,t)=>e+t.price*t.qty,0),ship=u>=FREE?`Free U.S. shipping`:`Shipping $4.99 (free on orders $25+, ${o(FREE-u)} to go)`,
f=`
    <p class="flex items-center justify-between font-semibold text-ink"><span>Subtotal</span><span>${o(u)}</span></p>
    <p class="mt-1 text-sm text-muted">${ship}. Tax, if any, is shown at checkout.</p>
    <button type="button" class="btn btn-primary mt-3 w-full" data-checkout>Check out securely</button>
    <p class="mt-2 text-xs text-muted" data-checkout-msg hidden></p>`,
p=document.querySelector(`[data-cart-body]`),m=document.querySelector(`[data-cart-footer]`),h=document.querySelector(`[data-cart-page]`);
if(e.length===0){p&&(p.innerHTML=n),m&&(m.innerHTML=``),h&&(h.innerHTML=n);return}
p&&(p.innerHTML=a),m&&(m.innerHTML=`${f}<a class="btn btn-secondary mt-2 w-full" href="/cart/">View cart page</a>`),h&&(h.innerHTML=`${a}<div class="mt-4">${f}</div>`)}
function u(e,t=1){let n=i(),r=n.find(t=>String(t.variant)===String(e.variant));r?r.qty=Math.min(99,r.qty+t):n.push({...e,qty:t}),a(n)}
async function checkout(btn){let items=i();if(!items.length)return;let msg=btn.parentElement.querySelector(`[data-checkout-msg]`);btn.disabled=!0;let label=btn.textContent;btn.textContent=`Opening secure checkout…`;
try{let res=await fetch(r.checkoutEndpoint||`/api/checkout`,{method:`POST`,headers:{"content-type":`application/json`},body:JSON.stringify({cart:items.map(e=>({sync_variant_id:Number(e.variant),qty:e.qty}))})});let d=await res.json().catch(()=>({}));if(res.ok&&d.url){window.location.href=d.url;return}throw new Error(d.error||`Checkout is not available right now.`)}
catch(err){btn.disabled=!1;btn.textContent=label;if(msg){msg.hidden=!1;msg.textContent=`${err.message} Please try again, or email support@medicalstickers.shop.`}}}
function d(){let e=document.querySelector(`[data-cart-drawer]`),t=document.querySelector(`[data-cart-button]`);e&&(e.hidden=!1,t?.setAttribute(`aria-expanded`,`true`),document.body.classList.add(`menu-open`),e.querySelector(`[data-cart-close]`)?.focus())}function f(){let e=document.querySelector(`[data-cart-drawer]`),t=document.querySelector(`[data-cart-button]`);e&&!e.hidden&&(e.hidden=!0,t?.setAttribute(`aria-expanded`,`false`),document.body.classList.remove(`menu-open`),t?.focus())}function p(){let e=document.querySelector(`[data-menu-button]`),t=document.querySelector(`[data-menu-panel]`);if(!e||!t)return;let n=()=>{t.hidden=!0,e.setAttribute(`aria-expanded`,`false`),document.body.classList.remove(`menu-open`)},r=()=>{t.hidden=!1,e.setAttribute(`aria-expanded`,`true`),document.body.classList.add(`menu-open`)};e.addEventListener(`click`,()=>{t.hidden?r():n()}),t.querySelectorAll(`a`).forEach(e=>e.addEventListener(`click`,n)),document.querySelectorAll(`details.nav-drop`).forEach(e=>{e.addEventListener(`toggle`,()=>{e.open&&document.querySelectorAll(`details.nav-drop`).forEach(t=>{t!==e&&(t.open=!1)})})}),document.addEventListener(`click`,e=>{let t=e.target;document.querySelectorAll(`details.nav-drop[open]`).forEach(e=>{e.contains(t)||(e.open=!1)})}),document.addEventListener(`keydown`,e=>{e.key===`Escape`&&(n(),f(),document.querySelectorAll(`details.nav-drop[open]`).forEach(e=>{e.open=!1}))})}function m(){document.querySelector(`[data-cart-button]`)?.addEventListener(`click`,()=>{document.querySelector(`[data-cart-drawer]`)?.hidden?d():f()}),document.querySelectorAll(`[data-cart-close]`).forEach(e=>e.addEventListener(`click`,f)),document.addEventListener(`click`,e=>{let t=e.target,n=t.closest(`[data-add-cart]`);if(n){if(!n.dataset.variant)return;u({variant:n.dataset.variant,size:n.dataset.size||``,slug:n.dataset.slug||``,title:n.dataset.title||``,price:Number(n.dataset.price||0),image:n.dataset.image||``}),d();return}let k=t.closest(`[data-checkout]`);if(k){checkout(k);return}let r=t.closest(`[data-qty]`);if(r){let e=i(),t=e.find(e=>String(e.variant)===r.dataset.variant);if(!t)return;t.qty=Math.min(99,t.qty+Number(r.dataset.qty||0)),a(e.filter(e=>e.qty>0));return}let o=t.closest(`[data-remove]`);o&&a(i().filter(e=>String(e.variant)!==o.dataset.remove))});if(new URLSearchParams(window.location.search).get(`checkout`)===`done`){a([])}}function h(){document.querySelectorAll(`[data-newsletter]`).forEach(e=>{e.addEventListener(`submit`,t=>{if(!r.newsletterPreview)return;t.preventDefault();let n=e.querySelector(`[data-newsletter-msg]`);n&&(n.hidden=!1,n.textContent=`You're noted for the Shift Report. This preview does not save email addresses. Connect a mailing tool in the site settings before launch and this form will start sending.`),e.reset()})}),document.querySelectorAll(`[data-mailto-form]`).forEach(e=>{e.addEventListener(`submit`,t=>{t.preventDefault();let n=e.dataset.email||``,r=new FormData(e),i=String(r.get(`topic`)||`Message from the website`),a=[...r.entries()].filter(([e])=>e!==`topic`).map(([e,t])=>`${e}: ${String(t)}`).join(`
`);window.location.href=`mailto:${n}?subject=${encodeURIComponent(i)}&body=${encodeURIComponent(a)}`;let o=e.querySelector(`[data-form-msg]`);o&&(o.hidden=!1,o.textContent=`Your email app should open addressed to ${n}. If it does not, write us there directly.`)})})}function g(){let e=document.querySelector(`[data-cookie]`);e&&(localStorage.getItem(t)||(e.hidden=!1),e.querySelectorAll(`[data-consent]`).forEach(n=>{n.addEventListener(`click`,()=>{localStorage.setItem(t,n.dataset.consent||`essential`),e.hidden=!0})}))}function _(){let e=document.querySelector(`[data-poll]`);if(!e)return;let t=`ms-poll-next`,n=e.querySelector(`[data-poll-thanks]`),r=localStorage.getItem(t);r&&n&&(n.hidden=!1,n.textContent=`Saved on this device: ${r}. This preview poll is not sent to us.`),e.querySelectorAll(`[data-poll-choice]`).forEach(e=>{e.addEventListener(`click`,()=>{let r=e.dataset.pollChoice||``;localStorage.setItem(t,r),n&&(n.hidden=!1,n.textContent=`Saved on this device: ${r}. This preview poll is not sent to us.`)})})}p(),m(),h(),g(),_(),l();
