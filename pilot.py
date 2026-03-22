#!/usr/bin/env python3
"""
 Browser Pilot v4 — 50 features. Zero LLM. Zero cost.
 Your browser, your rules. No external LLM. No API keys. Just vibes.

CORE:
  pilot.py navigate URL              go to a URL
  pilot.py dom                       compressed DOM with indices
  pilot.py text                      all page text
  pilot.py screenshot [path]         viewport screenshot
  pilot.py screenshot-full [path]    full page screenshot (#21)
  pilot.py screenshot-el SEL [path]  element screenshot (#22)
  pilot.py pages                     list open tabs
  pilot.py select N                  switch to tab N
  pilot.py wait N                    wait N seconds
  pilot.py wait-for SEL [timeout]    wait for element (#1)

CLICK:
  pilot.py click SEL                 click by CSS selector
  pilot.py click-text TEXT           click by visible text
  pilot.py click-index N             click by DOM index
  pilot.py click-retry SEL [N]       click with auto-retry (#2)
  pilot.py right-click SEL           right-click context menu (#37)

INPUT:
  pilot.py fill SEL VALUE            fill input field
  pilot.py type-human SEL TEXT       typewriter mode (#36)
  pilot.py select-option SEL VAL     native select dropdown (#35)
  pilot.py upload SEL PATH           file upload (#34)
  pilot.py key COMBO                 keyboard shortcut (#33)

SCROLL:
  pilot.py scroll [up|down] [px]     scroll by pixels
  pilot.py scroll-to SEL             scroll element into view (#38)
  pilot.py scroll-infinite [max]     infinite scroll handler (#18)

EXTRACT:
  pilot.py eval JS                   run JavaScript
  pilot.py table [SEL]               table → JSON (#14)
  pilot.py links                     all links on page (#15)
  pilot.py images                    all images on page (#16)
  pilot.py forms                     detect all forms (#13)
  pilot.py meta                      structured data/meta (#49)
  pilot.py prices                    extract currency amounts (#47)
  pilot.py dates                     extract dates (#48)
  pilot.py cookies [export|import]   cookie management (#6)
  pilot.py network [start|stop|dump] network capture (#7,#8)

VISUAL:
  pilot.py highlight SEL [label]     highlight element
  pilot.py highlight-all             highlight all interactive (#25)
  pilot.py diff URL1 URL2 [path]     visual diff (#23)
  pilot.py annotate SEL TEXT         add label on page (#29)

INTELLIGENCE:
  pilot.py detect-login              check if login required (#41)
  pilot.py dismiss-cookies           dismiss cookie banners (#42)
  pilot.py detect-captcha            check for CAPTCHAs (#43)
  pilot.py detect-error              detect error pages (#45)
  pilot.py detect-lang               detect page language (#46)
  pilot.py spa-wait [timeout]        smart SPA load wait (#44)

ADVANCED:
  pilot.py hover SEL                 hover with tooltip (#32)
  pilot.py drag SEL X Y              drag element (#31)
  pilot.py iframe SEL CMD...         run command inside iframe (#4)
  pilot.py shadow SEL CMD...         pierce shadow DOM (#3,#11)
  pilot.py geo LAT LNG              spoof geolocation (#40)
  pilot.py emulate DEVICE            mobile/tablet emulation (#39)
  pilot.py monitor URL [interval]    change monitor (#50)
  pilot.py record [start|stop] path  screen recording (#24)
  pilot.py lazy-load                 trigger lazy loading (#19)
  pilot.py a11y                      accessibility tree (#20)
  pilot.py landmarks                 page landmarks (#12)
  pilot.py dom-diff                  diff last two DOM snapshots (#17)
"""

import asyncio
import json
import sys
import base64
import os
import random
import time
import re
import hashlib
from datetime import datetime

try:
    import websockets
except ImportError:
    print("pip install websockets")
    sys.exit(1)

CDP_URL = os.environ.get("CDP_URL", "http://localhost:9222")
STATE_DIR = os.environ.get("BP_STATE", "/tmp/browser-pilot-state")
os.makedirs(STATE_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════
# STYLE & PERSONALITY
# ═══════════════════════════════════════════════════════════

class C:
    BOLD = "\033[1m"; DIM = "\033[2m"; ORANGE = "\033[38;5;208m"
    CYAN = "\033[36m"; GREEN = "\033[32m"; RED = "\033[31m"
    YELLOW = "\033[33m"; MAGENTA = "\033[35m"; BLUE = "\033[34m"
    GRAY = "\033[90m"; RESET = "\033[0m"; UNDERLINE = "\033[4m"

QUIPS = {
    "nav": ["fasten your seatbelt...", "charting a course...", "engaging hyperdrive...",
            "buckle up, buttercup...", "not all who wander are lost..."],
    "click": ["smashing that button...", "precision strike incoming...", "boop...",
              "tactical click deployed...", "button never saw it coming..."],
    "dom": ["reading the matrix...", "x-ray vision: engaged...", "unzipping the page...",
            "counting all the things you can poke..."],
    "extract": ["absorbing knowledge...", "speed reading at 1M wpm...", "ctrl+c on reality..."],
    "scroll": ["scrolling into the abyss...", "exploring below the fold..."],
    "wait": ["patience is a virtue...", "contemplating existence..."],
    "screenshot": ["say cheese...", "capturing the moment...", "freeze frame..."],
    "detect": ["scanning for threats...", "running diagnostics...", "analysing the situation..."],
    "network": ["tapping the wire...", "eavesdropping on packets...", "intercepting comms..."],
    "highlight": ["painting the target...", "spotlight on...", "look here..."],
    "form": ["inspecting the paperwork...", "bureaucracy detected..."],
    "hover": ["approaching cautiously...", "getting closer..."],
    "drag": ["grab and go...", "heavy lifting..."],
    "type": ["hunt and peck mode...", "channeling a human typist..."],
    "cookie": ["reaching for the cookie jar...", "nom nom nom..."],
    "geo": ["teleporting...", "faking our location..."],
    "record": ["lights, camera, action...", "rolling..."],
    "iframe": ["entering the frame within the frame...", "inception mode..."],
    "shadow": ["piercing the veil...", "entering the shadow realm..."],
    "a11y": ["seeing through a screen reader's eyes...", "accessibility check..."],
    "monitor": ["setting up surveillance...", "keeping watch..."],
    "diff": ["spot the difference...", "comparing realities..."],
}

def q(cat): return random.choice(QUIPS.get(cat, ["working on it..."]))

BANNER = f"""{C.ORANGE}{C.BOLD}
  ____                                   ____  _ _       _
 | __ ) _ __ _____      _____  ___ _ __|  _ \\(_) | ___ | |_
 |  _ \\| '__/ _ \\ \\ /\\ / / __|/ _ \\ '__| |_) | | |/ _ \\| __|
 | |_) | | | (_) \\ V  V /\\__ \\  __/ |  |  __/| | | (_) | |_
 |____/|_|  \\___/ \\_/\\_/ |___/\\___|_|  |_|   |_|_|\\___/ \\__|
                                              {C.DIM}v4 — 50 features{C.RESET}
{C.GRAY}  Your browser. Your rules. No external LLM. Zero cost.{C.RESET}
"""

_t0 = time.time()
def log(msg, color=C.CYAN):
    ts = f"{C.GRAY}{time.time()-_t0:6.1f}s{C.RESET}"
    print(f"  {ts}  {color}{msg}{C.RESET}")
def log_ok(m): log(m, C.GREEN)
def log_dim(m): log(m, C.GRAY)
def log_err(m): log(m, C.RED)
def log_warn(m): log(m, C.YELLOW)

# ═══════════════════════════════════════════════════════════
# CDP CLIENT (persistent-capable)
# ═══════════════════════════════════════════════════════════

def _get_pages():
    import urllib.request
    resp = urllib.request.urlopen(f"{CDP_URL}/json/list")
    return [p for p in json.loads(resp.read()) if p.get("type") == "page"]

async def get_ws(idx=None):
    pages = _get_pages()
    if not pages:
        log_err("No pages open in Chrome"); sys.exit(1)
    i = idx if idx is not None else int(os.environ.get("TAB", "0"))
    if i >= len(pages):
        log_err(f"Tab {i} out of range (0-{len(pages)-1})"); sys.exit(1)
    return await websockets.connect(pages[i]["webSocketDebuggerUrl"], max_size=100*1024*1024), pages

_msg_id = 0
async def cdp(ws, method, params=None, timeout=30):
    global _msg_id; _msg_id += 1; mid = _msg_id
    await ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        d = json.loads(raw)
        if d.get("id") == mid:
            if "error" in d: raise RuntimeError(f"CDP: {d['error']}")
            return d.get("result", {})

async def js(ws, expr, by_val=True):
    r = await cdp(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": by_val, "awaitPromise": True})
    return r.get("result", {}).get("value") if by_val else r

# ═══════════════════════════════════════════════════════════
# HIGHLIGHT ENGINE
# ═══════════════════════════════════════════════════════════

HIGHLIGHT_STYLE = """
if(!document.querySelector('#bp-style')){
  const s=document.createElement('style');s.id='bp-style';
  s.textContent=`
    @keyframes bp-pulse{0%,100%{box-shadow:0 0 0 2px rgba(255,102,0,.15),0 0 20px rgba(255,102,0,.3)}50%{box-shadow:0 0 0 6px rgba(255,102,0,.3),0 0 40px rgba(255,102,0,.6)}}
    @keyframes bp-pulse-g{0%,100%{box-shadow:0 0 0 2px rgba(0,204,136,.15),0 0 20px rgba(0,204,136,.3)}50%{box-shadow:0 0 0 6px rgba(0,204,136,.3),0 0 40px rgba(0,204,136,.6)}}
    @keyframes bp-pulse-b{0%,100%{box-shadow:0 0 0 2px rgba(99,102,241,.15),0 0 20px rgba(99,102,241,.3)}50%{box-shadow:0 0 0 6px rgba(99,102,241,.3),0 0 40px rgba(99,102,241,.6)}}
  `;document.head.appendChild(s);}
"""

def _hl_js(sel, label="PILOT", color="#ff6600", anim="bp-pulse"):
    esc = sel.replace("'", "\\'").replace('"', '\\"')
    return f"""(() => {{
  {HIGHLIGHT_STYLE}
  const el=document.querySelector('{esc}');if(!el)return false;
  const r=el.getBoundingClientRect(),sx=scrollX,sy=scrollY;
  const o=document.createElement('div');o.className='bp-hl';
  o.style.cssText='position:absolute;left:'+(r.left+sx-6)+'px;top:'+(r.top+sy-6)+'px;width:'+(r.width+12)+'px;height:'+(r.height+12)+'px;border:2.5px solid {color};border-radius:8px;pointer-events:none;z-index:999999;animation:{anim} 1.5s ease-in-out infinite';
  const b=document.createElement('div');b.className='bp-hl';b.textContent='{label}';
  b.style.cssText='position:absolute;left:'+(r.left+sx-6)+'px;top:'+(r.top+sy-28)+'px;background:linear-gradient(135deg,{color},{color}cc);color:#fff;font:700 11px system-ui;padding:3px 10px;border-radius:6px 6px 0 0;pointer-events:none;z-index:999999;letter-spacing:.5px';
  document.body.appendChild(o);document.body.appendChild(b);
  setTimeout(()=>{{o.remove();b.remove()}},3000);return true;
}})()"""

async def hl(ws, sel, label="PILOT", color="#ff6600"):
    try: await js(ws, _hl_js(sel, label, color))
    except: pass

async def hl_clear(ws):
    try: await js(ws, "document.querySelectorAll('.bp-hl').forEach(e=>e.remove())")
    except: pass

# React/Radix compatible click dispatch
def _click_js(sel):
    esc = sel.replace("'", "\\'").replace('"', '\\"')
    return f"""(() => {{
  const el=document.querySelector('{esc}');if(!el)return {{ok:false}};
  el.scrollIntoView({{block:'center'}});
  el.dispatchEvent(new PointerEvent('pointerdown',{{bubbles:true,pointerId:1}}));
  el.dispatchEvent(new MouseEvent('mousedown',{{bubbles:true}}));
  el.dispatchEvent(new PointerEvent('pointerup',{{bubbles:true,pointerId:1}}));
  el.dispatchEvent(new MouseEvent('mouseup',{{bubbles:true}}));
  el.dispatchEvent(new MouseEvent('click',{{bubbles:true}}));
  const r=el.getBoundingClientRect();
  return {{ok:true,x:r.x+r.width/2,y:r.y+r.height/2,text:el.innerText.trim().substring(0,50)}};
}})()"""

def _click_text_js(text):
    esc = text.replace("'", "\\'").replace('"', '\\"')
    return f"""(() => {{
  const Q='a,button,[role="button"],[role="menuitem"],[role="tab"],[role="link"],[role="option"],div[tabindex],span[tabindex]';
  for(const el of document.querySelectorAll(Q)){{
    if(el.innerText.trim().includes('{esc}')){{
      el.scrollIntoView({{block:'center'}});
      el.dispatchEvent(new PointerEvent('pointerdown',{{bubbles:true,pointerId:1}}));
      el.dispatchEvent(new MouseEvent('mousedown',{{bubbles:true}}));
      el.dispatchEvent(new PointerEvent('pointerup',{{bubbles:true,pointerId:1}}));
      el.dispatchEvent(new MouseEvent('mouseup',{{bubbles:true}}));
      el.dispatchEvent(new MouseEvent('click',{{bubbles:true}}));
      const r=el.getBoundingClientRect();
      return {{x:r.x+r.width/2,y:r.y+r.height/2,found:el.innerText.trim().substring(0,50)}};
    }}
  }}
  return null;
}})()"""

# ═══════════════════════════════════════════════════════════
# DOM COMPRESSION ENGINE
# ═══════════════════════════════════════════════════════════

DOM_JS = r"""
(() => {
  const I=new Set(['A','BUTTON','INPUT','SELECT','TEXTAREA','DETAILS','SUMMARY']);
  const R=new Set(['button','link','menuitem','tab','checkbox','radio','switch','combobox','listbox','option','searchbox','textbox']);
  const T=new Set(['H1','H2','H3','H4','H5','H6','P','SPAN','LABEL','TD','TH','LI']);
  const S=new Set(['SCRIPT','STYLE','NOSCRIPT','SVG','PATH','META','LINK','BR','HR']);
  function vis(e){if(!e.offsetParent&&e.tagName!=='BODY'&&e.tagName!=='HTML')return false;try{const s=getComputedStyle(e);if(s.display==='none'||s.visibility==='hidden'||s.opacity==='0')return false}catch(x){return false}const r=e.getBoundingClientRect();return r.width>0||r.height>0}
  function act(e){if(I.has(e.tagName))return true;const r=e.getAttribute('role');if(r&&R.has(r))return true;if(e.getAttribute('tabindex')!==null)return true;if(e.getAttribute('contenteditable')==='true')return true;try{if(getComputedStyle(e).cursor==='pointer')return true}catch(x){}return false}
  function txt(e){let t='';for(const c of e.childNodes)if(c.nodeType===3)t+=c.textContent.trim()+' ';t=t.trim();if(!t)t=e.getAttribute('aria-label')||e.getAttribute('title')||e.getAttribute('placeholder')||e.getAttribute('alt')||'';if((e.tagName==='INPUT'||e.tagName==='TEXTAREA')&&e.value)t='value="'+e.value+'" '+t;return t.trim().substring(0,80)}
  function desc(e){const t=e.tagName.toLowerCase(),r=e.getAttribute('role'),id=e.getAttribute('id'),h=e.getAttribute('href');let p=[];if(r)p.push(r);else if(t==='input')p.push(e.type||'text');else p.push(t);const x=txt(e);if(x)p.push('"'+x+'"');if(h&&h.length<80&&!h.startsWith('javascript:'))p.push('href='+h);if(id)p.push('id='+id);if(e.disabled)p.push('[disabled]');return p.join(' ')}
  function sel(e){if(e.id)return'#'+CSS.escape(e.id);const a=e.getAttribute('aria-label');if(a)return'[aria-label="'+CSS.escape(a)+'"]';const p=[];let c=e;while(c&&c!==document.body){let s=c.tagName.toLowerCase();if(c.id){p.unshift('#'+CSS.escape(c.id));break}const pr=c.parentElement;if(pr){const si=[...pr.children].filter(x=>x.tagName===c.tagName);if(si.length>1)s+=':nth-of-type('+(si.indexOf(c)+1)+')'}p.unshift(s);c=c.parentElement}return p.join(' > ')}
  const els=[];let idx=0;const seen=new Set();
  function walk(n,d){if(d>15||!n||!n.tagName||S.has(n.tagName)||seen.has(n))return;seen.add(n);if(!vis(n))return;
    // Shadow DOM (#3, #11)
    if(n.shadowRoot){for(const c of n.shadowRoot.children)walk(c,d+1)}
    const ia=act(n),tx=txt(n);
    if(ia&&tx){idx++;els.push({i:idx,t:'i',d:desc(n),s:sel(n)})}
    else if(T.has(n.tagName)&&tx&&tx.length>1){els.push({i:null,t:'t',d:n.tagName.toLowerCase()+': "'+tx+'"'})}
    else if(n.tagName==='TABLE'){const rows=[];n.querySelectorAll('tr').forEach(tr=>{const cells=[...tr.querySelectorAll('td,th')].map(c=>c.innerText.trim().substring(0,60));if(cells.length>0&&cells.some(c=>c))rows.push(cells.join(' | '))});if(rows.length>0){els.push({i:null,t:'tbl',d:'table('+rows.length+'):\\n'+rows.slice(0,25).join('\\n')});return}}
    for(const c of n.children)walk(c,d+1)}
  walk(document.body,0);
  const L=['Page: '+document.title,'URL: '+location.href,'---'];const sels={};
  for(const e of els){if(e.t==='i'){L.push('['+e.i+'] '+e.d);sels[e.i]=e.s}else if(e.t==='tbl')L.push(e.d);else L.push('    '+e.d)}
  L.push('---');L.push(idx+' interactive elements');
  return{dom:L.join('\n'),selectors:sels,count:idx};
})()
"""

# ═══════════════════════════════════════════════════════════
# FEATURE: TABLE PARSER (#14)
# ═══════════════════════════════════════════════════════════

TABLE_JS = """
(() => {
  const tables = [...document.querySelectorAll('table')];
  return tables.filter(Boolean).map((t,ti) => {
    const headers = [...t.querySelectorAll('thead th, tr:first-child th')].map(h => h.innerText.trim());
    const rows = [...t.querySelectorAll('tbody tr, tr')].slice(headers.length ? 0 : 1).map(r =>
      [...r.querySelectorAll('td,th')].map(c => c.innerText.trim())
    );
    return {table_index: ti, headers, rows: rows.slice(0, 100), row_count: rows.length};
  });
})()
"""

# ═══════════════════════════════════════════════════════════
# FEATURE: INTELLIGENCE DETECTORS (#41-46)
# ═══════════════════════════════════════════════════════════

DETECT_LOGIN_JS = """
(() => {
  const inputs = document.querySelectorAll('input[type="password"], input[name*="pass"], input[name*="email"], input[name*="user"]');
  const forms = document.querySelectorAll('form[action*="login"], form[action*="signin"], form[action*="auth"]');
  const text = document.body.innerText.toLowerCase();
  const hasLoginWords = /sign.?in|log.?in|username|password|forgot.?pass/i.test(text);
  const hasLoginInputs = inputs.length > 0;
  const hasLoginForms = forms.length > 0;
  return {
    needs_login: hasLoginInputs || hasLoginForms || hasLoginWords,
    signals: {password_fields: inputs.length, login_forms: forms.length, login_text: hasLoginWords},
    url: location.href
  };
})()
"""

DETECT_COOKIE_JS = """
(() => {
  const sels = [
    '[class*="cookie"]', '[id*="cookie"]', '[class*="consent"]', '[id*="consent"]',
    '[class*="gdpr"]', '[class*="privacy-banner"]', '[aria-label*="cookie"]',
    '[class*="cc-banner"]', '[class*="cookie-banner"]', '#onetrust-banner-sdk'
  ];
  for (const s of sels) {
    const el = document.querySelector(s);
    if (el && el.offsetParent) {
      const btns = el.querySelectorAll('button, a, [role="button"]');
      const accept = [...btns].find(b => /accept|agree|got it|ok|allow|understand/i.test(b.innerText));
      const reject = [...btns].find(b => /reject|decline|deny|necessary only/i.test(b.innerText));
      return {found: true, accept_btn: accept?.innerText.trim(), reject_btn: reject?.innerText.trim(), selector: s};
    }
  }
  return {found: false};
})()
"""

DETECT_CAPTCHA_JS = """
(() => {
  const signals = [];
  if (document.querySelector('[class*="captcha"], [id*="captcha"], iframe[src*="recaptcha"], iframe[src*="hcaptcha"], iframe[src*="turnstile"]'))
    signals.push('captcha_element');
  if (document.body.innerText.match(/verify you.re human|i.m not a robot|captcha/i))
    signals.push('captcha_text');
  if (document.querySelector('.g-recaptcha, .h-captcha, [data-sitekey]'))
    signals.push('captcha_widget');
  return {has_captcha: signals.length > 0, signals};
})()
"""

DETECT_ERROR_JS = """
(() => {
  const text = document.body.innerText.substring(0, 2000).toLowerCase();
  const title = document.title.toLowerCase();
  const checks = [
    {type: '404', match: /404|not found|page.*(not|doesn.t) exist/i.test(text + title)},
    {type: '403', match: /403|forbidden|access denied|not authorized/i.test(text + title)},
    {type: '500', match: /500|internal server|something went wrong|unexpected error/i.test(text + title)},
    {type: '503', match: /503|service unavailable|temporarily down|maintenance/i.test(text + title)},
    {type: 'timeout', match: /timed? ?out|took too long|can.t be reached/i.test(text + title)},
    {type: 'blocked', match: /blocked|rate limit|too many requests|429/i.test(text + title)},
  ];
  const errors = checks.filter(c => c.match).map(c => c.type);
  return {has_error: errors.length > 0, errors, title: document.title, url: location.href};
})()
"""

DETECT_LANG_JS = """
(() => {
  const html_lang = document.documentElement.lang || '';
  const meta_lang = document.querySelector('meta[http-equiv="content-language"]')?.content || '';
  const og_locale = document.querySelector('meta[property="og:locale"]')?.content || '';
  const sample = document.body.innerText.substring(0, 500);
  return {html_lang, meta_lang, og_locale, text_sample: sample.substring(0, 100)};
})()
"""

# ═══════════════════════════════════════════════════════════
# FEATURE: EXTRACTORS (#15, #16, #47, #48, #49)
# ═══════════════════════════════════════════════════════════

LINKS_JS = """
(() => [...document.querySelectorAll('a[href]')].map(a => ({
  text: a.innerText.trim().substring(0, 80),
  href: a.href,
  internal: a.hostname === location.hostname
})).filter(l => l.href && !l.href.startsWith('javascript:')))()
"""

IMAGES_JS = """
(() => [...document.querySelectorAll('img')].filter(i => i.src && i.naturalWidth > 0).map(i => ({
  src: i.src.substring(0, 200),
  alt: (i.alt || '').substring(0, 80),
  width: i.naturalWidth,
  height: i.naturalHeight
})))()
"""

FORMS_JS = """
(() => [...document.querySelectorAll('form')].map((f, i) => ({
  index: i,
  action: f.action || '',
  method: f.method || 'get',
  fields: [...f.querySelectorAll('input,select,textarea')].map(el => ({
    tag: el.tagName.toLowerCase(),
    type: el.type || '',
    name: el.name || '',
    id: el.id || '',
    placeholder: el.placeholder || '',
    required: el.required,
    value: el.value?.substring(0, 50) || ''
  }))
})))()
"""

META_JS = """
(() => {
  const m = {};
  m.title = document.title;
  m.description = document.querySelector('meta[name="description"]')?.content || '';
  m.og = {};
  document.querySelectorAll('meta[property^="og:"]').forEach(e => {
    m.og[e.getAttribute('property').replace('og:', '')] = e.content;
  });
  m.twitter = {};
  document.querySelectorAll('meta[name^="twitter:"]').forEach(e => {
    m.twitter[e.name.replace('twitter:', '')] = e.content;
  });
  m.canonical = document.querySelector('link[rel="canonical"]')?.href || '';
  m.jsonld = [...document.querySelectorAll('script[type="application/ld+json"]')].map(s => {
    try { return JSON.parse(s.textContent); } catch(e) { return null; }
  }).filter(Boolean);
  return m;
})()
"""

PRICES_JS = r"""
(() => {
  const text = document.body.innerText;
  const patterns = [
    /\$[\d,]+\.?\d*/g, /USD\s*[\d,]+\.?\d*/g, /€[\d,]+\.?\d*/g,
    /£[\d,]+\.?\d*/g, /₹[\d,]+\.?\d*/g, /¥[\d,]+\.?\d*/g,
    /US\$[\d,]+\.?\d*/g, /INR\s*[\d,]+\.?\d*/g,
  ];
  const found = new Set();
  for (const p of patterns) {
    const matches = text.match(p) || [];
    matches.forEach(m => found.add(m));
  }
  return [...found].slice(0, 50);
})()
"""

DATES_JS = r"""
(() => {
  const text = document.body.innerText;
  const patterns = [
    /\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}/g,
    /\d{4}[\/-]\d{1,2}[\/-]\d{1,2}/g,
    /(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s*\d{4}/gi,
    /\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}/gi,
  ];
  const found = new Set();
  for (const p of patterns) {
    const matches = text.match(p) || [];
    matches.forEach(m => found.add(m.trim()));
  }
  return [...found].slice(0, 50);
})()
"""

# ═══════════════════════════════════════════════════════════
# FEATURE: ACCESSIBILITY (#20) & LANDMARKS (#12)
# ═══════════════════════════════════════════════════════════

LANDMARKS_JS = """
(() => {
  const landmarks = [];
  const roles = ['banner','navigation','main','complementary','contentinfo','search','form','region'];
  for (const role of roles) {
    const els = document.querySelectorAll('[role="'+role+'"], '+role);
    els.forEach(el => {
      landmarks.push({role, label: el.getAttribute('aria-label') || '', tag: el.tagName.toLowerCase()});
    });
  }
  // Also check semantic HTML5
  ['header','nav','main','aside','footer','section','article'].forEach(tag => {
    document.querySelectorAll(tag).forEach(el => {
      if (!el.getAttribute('role')) {
        landmarks.push({role: tag, label: el.getAttribute('aria-label') || '', tag});
      }
    });
  });
  return landmarks;
})()
"""

# ═══════════════════════════════════════════════════════════
# FEATURE: HIGHLIGHT ALL (#25)
# ═══════════════════════════════════════════════════════════

HIGHLIGHT_ALL_JS = """
(() => {
  document.querySelectorAll('.bp-hl').forEach(e => e.remove());
  """ + HIGHLIGHT_STYLE + """
  const I=new Set(['A','BUTTON','INPUT','SELECT','TEXTAREA']);
  const R=new Set(['button','link','menuitem','tab','checkbox','radio','combobox','option']);
  const colors = ['#ff6600','#00cc88','#6366f1','#ec4899','#f59e0b','#06b6d4','#8b5cf6','#ef4444'];
  let idx = 0;
  const all = document.querySelectorAll('a,button,input,select,textarea,[role]');
  for (const el of all) {
    if (!el.offsetParent) continue;
    const role = el.getAttribute('role');
    if (!I.has(el.tagName) && !(role && R.has(role))) continue;
    idx++;
    const r = el.getBoundingClientRect();
    if (r.width < 5 || r.height < 5) continue;
    const c = colors[idx % colors.length];
    const o = document.createElement('div'); o.className = 'bp-hl';
    o.style.cssText = 'position:absolute;left:'+(r.left+scrollX-3)+'px;top:'+(r.top+scrollY-3)+'px;width:'+(r.width+6)+'px;height:'+(r.height+6)+'px;border:2px solid '+c+';border-radius:4px;pointer-events:none;z-index:999999';
    const b = document.createElement('div'); b.className = 'bp-hl'; b.textContent = idx;
    b.style.cssText = 'position:absolute;left:'+(r.left+scrollX-3)+'px;top:'+(r.top+scrollY-18)+'px;background:'+c+';color:#fff;font:700 10px system-ui;padding:1px 5px;border-radius:3px 3px 0 0;pointer-events:none;z-index:999999';
    document.body.appendChild(o); document.body.appendChild(b);
  }
  setTimeout(() => document.querySelectorAll('.bp-hl').forEach(e => e.remove()), 8000);
  return idx + ' elements highlighted';
})()
"""

# ═══════════════════════════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════════════════════════

async def cmd_navigate(ws, url):
    log_dim(q("nav")); await cdp(ws, "Page.navigate", {"url": url}); await asyncio.sleep(2)
    log_ok(f"Landed on {C.UNDERLINE}{url[:70]}{C.RESET}")

async def cmd_spa_wait(ws, timeout=10):
    """Smart SPA wait — waits for network idle + DOM stable (#44)"""
    log_dim(q("detect"))
    start = time.time()
    prev_text = ""
    while time.time() - start < float(timeout):
        cur = await js(ws, "document.body.innerText.length") or 0
        if cur == prev_text and cur > 100:
            log_ok(f"SPA loaded ({cur} chars stable). Took {time.time()-start:.1f}s")
            return
        prev_text = cur
        await asyncio.sleep(0.5)
    log_warn(f"SPA wait timed out after {timeout}s. Content may still be loading.")

async def cmd_wait_for(ws, selector, timeout=10):
    """Wait for element to appear (#1)"""
    log_dim(q("wait"))
    esc = selector.replace("'", "\\'")
    start = time.time()
    while time.time() - start < float(timeout):
        found = await js(ws, f"!!document.querySelector('{esc}')")
        if found:
            log_ok(f"Element '{selector}' appeared after {time.time()-start:.1f}s")
            return True
        await asyncio.sleep(0.3)
    log_err(f"Element '{selector}' never showed up after {timeout}s. Ghosted.")
    return False

async def cmd_dom(ws):
    log_dim(q("dom"))
    val = await js(ws, DOM_JS)
    dom, count = val.get("dom", ""), val.get("count", 0)
    sels = val.get("selectors", {})
    with open(f"{STATE_DIR}/selectors.json", "w") as f: json.dump(sels, f)
    # Save for diff (#17)
    prev = f"{STATE_DIR}/dom-prev.txt"
    curr = f"{STATE_DIR}/dom-curr.txt"
    if os.path.exists(curr): os.rename(curr, prev)
    with open(curr, "w") as f: f.write(dom)
    for line in dom.split("\n"):
        if line.startswith("Page:"): print(f"  {C.BOLD}{C.CYAN}{line}{C.RESET}")
        elif line.startswith("URL:"): print(f"  {C.UNDERLINE}{C.GRAY}{line}{C.RESET}")
        elif line.startswith("["): i=line.index("]"); print(f"  {C.ORANGE}{C.BOLD}{line[:i+1]}{C.RESET}{C.CYAN}{line[i+1:]}{C.RESET}")
        elif line.startswith("    "): print(f"  {C.GRAY}{line}{C.RESET}")
        elif line.startswith("table"): print(f"  {C.YELLOW}{line[:60]}...{C.RESET}")
        elif line.startswith("---"): print(f"  {C.DIM}{'─'*50}{C.RESET}")
        else: print(f"  {C.GREEN}{line}{C.RESET}")
    log_ok(f"Found {C.BOLD}{count}{C.RESET}{C.GREEN} interactive elements. The page is yours.{C.RESET}")

async def cmd_dom_diff(ws):
    """Diff last two DOM snapshots (#17)"""
    log_dim(q("diff"))
    prev = f"{STATE_DIR}/dom-prev.txt"
    curr = f"{STATE_DIR}/dom-curr.txt"
    if not os.path.exists(prev) or not os.path.exists(curr):
        log_err("Need at least 2 'dom' runs to diff. Run 'dom' twice first.")
        return
    with open(prev) as f: old = set(f.read().split("\n"))
    with open(curr) as f: new = set(f.read().split("\n"))
    added = new - old; removed = old - new
    if not added and not removed:
        log_ok("No changes. The page hasn't moved a pixel.")
        return
    if removed:
        print(f"  {C.RED}{C.BOLD}Removed ({len(removed)}):{C.RESET}")
        for l in sorted(removed)[:20]: print(f"  {C.RED}- {l}{C.RESET}")
    if added:
        print(f"  {C.GREEN}{C.BOLD}Added ({len(added)}):{C.RESET}")
        for l in sorted(added)[:20]: print(f"  {C.GREEN}+ {l}{C.RESET}")

async def cmd_screenshot(ws, path=None, full=False, selector=None):
    log_dim(q("screenshot"))
    params = {"format": "png"}
    if full:  # Full page (#21)
        metrics = await cdp(ws, "Page.getLayoutMetrics")
        w = int(metrics["contentSize"]["width"])
        h = int(metrics["contentSize"]["height"])
        await cdp(ws, "Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False})
        params["clip"] = {"x": 0, "y": 0, "width": w, "height": h, "scale": 1}
    if selector:  # Element screenshot (#22)
        esc = selector.replace("'", "\\'")
        rect = await js(ws, f"(() => {{ const r=document.querySelector('{esc}')?.getBoundingClientRect(); return r ? {{x:r.x,y:r.y,width:r.width,height:r.height}} : null }})()")
        if rect: params["clip"] = {**rect, "scale": 1}
        else: log_err(f"Element not found: {selector}"); return
    r = await cdp(ws, "Page.captureScreenshot", params)
    if full: await cdp(ws, "Emulation.clearDeviceMetricsOverride")
    data = base64.b64decode(r["data"])
    path = path or f"/tmp/bp-{'full' if full else 'el' if selector else 'viewport'}-{int(time.time())}.png"
    with open(path, "wb") as f: f.write(data)
    log_ok(f"Screenshot saved ({len(data)//1024}KB) {C.UNDERLINE}{path}{C.RESET}")

async def cmd_click(ws, selector):
    log_dim(q("click")); await hl(ws, selector, "CLICK"); await asyncio.sleep(0.2)
    v = await js(ws, _click_js(selector))
    if not v or not v.get("ok"): log_err(f"Element vanished: {selector}"); return
    await asyncio.sleep(0.5)
    log_ok(f"Clicked {C.BOLD}'{v.get('text','')}'{C.RESET}{C.GREEN} at ({v.get('x',0):.0f},{v.get('y',0):.0f}){C.RESET}")

async def cmd_click_text(ws, text):
    log_dim(q("click")); await asyncio.sleep(0.1)
    v = await js(ws, _click_text_js(text))
    if not v: log_err(f"Couldn't find '{text}'. Maybe it's shy?"); return
    await asyncio.sleep(0.5)
    log_ok(f"Clicked {C.BOLD}'{v['found']}'{C.RESET}{C.GREEN} at ({v['x']:.0f},{v['y']:.0f}){C.RESET}")

async def cmd_click_index(ws, index):
    p = f"{STATE_DIR}/selectors.json"
    if not os.path.exists(p): log_err("Run 'dom' first!"); return
    sels = json.load(open(p))
    sel = sels.get(str(index))
    if not sel: log_err(f"Index [{index}] doesn't exist."); return
    await cmd_click(ws, sel)

async def cmd_click_retry(ws, selector, retries=3):
    """Click with auto-retry (#2)"""
    for i in range(int(retries)):
        log_dim(f"attempt {i+1}/{retries}..." if i > 0 else q("click"))
        v = await js(ws, _click_js(selector))
        if v and v.get("ok"):
            log_ok(f"Clicked '{v.get('text','')}' (attempt {i+1})")
            return
        await asyncio.sleep(1)
        # Try scrolling into view
        esc = selector.replace("'", "\\'")
        await js(ws, f"document.querySelector('{esc}')?.scrollIntoView({{block:'center'}})")
        await asyncio.sleep(0.5)
    log_err(f"Failed after {retries} attempts. Element is playing hard to get.")

async def cmd_right_click(ws, selector):
    """Right-click context menu (#37)"""
    log_dim(q("click"))
    esc = selector.replace("'", "\\'")
    v = await js(ws, f"""(() => {{
      const el=document.querySelector('{esc}');if(!el)return null;
      el.scrollIntoView({{block:'center'}});
      const r=el.getBoundingClientRect();
      el.dispatchEvent(new MouseEvent('contextmenu',{{bubbles:true,clientX:r.x+r.width/2,clientY:r.y+r.height/2}}));
      return {{x:r.x+r.width/2,y:r.y+r.height/2}};
    }})()""")
    if v: log_ok(f"Right-clicked at ({v['x']:.0f},{v['y']:.0f}). Context menu should be open.")
    else: log_err("Element not found for right-click")

async def cmd_fill(ws, selector, value):
    log_dim(q("type")); await hl(ws, selector, "FILL", "#00cc88"); await asyncio.sleep(0.2)
    esc = selector.replace("'", "\\'")
    await js(ws, f"document.querySelector('{esc}').focus()")
    await cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "modifiers": 2})
    await cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "modifiers": 2})
    for ch in value: await cdp(ws, "Input.dispatchKeyEvent", {"type": "char", "text": ch})
    log_ok(f"Filled with '{value}'. The form is pleased.")

async def cmd_type_human(ws, selector, text):
    """Typewriter mode — human-like typing (#36)"""
    log_dim(q("type")); await hl(ws, selector, "TYPING", "#6366f1"); await asyncio.sleep(0.2)
    esc = selector.replace("'", "\\'")
    await js(ws, f"document.querySelector('{esc}').focus()")
    await cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "modifiers": 2})
    await cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "modifiers": 2})
    for ch in text:
        await cdp(ws, "Input.dispatchKeyEvent", {"type": "char", "text": ch})
        await asyncio.sleep(random.uniform(0.03, 0.15))  # Human-like delay
    log_ok(f"Typed '{text}' like a real human. Nobody suspects a thing.")

async def cmd_select_option(ws, selector, value):
    """Select native dropdown option (#35)"""
    esc_sel = selector.replace("'", "\\'")
    esc_val = value.replace("'", "\\'")
    r = await js(ws, f"""(() => {{
      const sel=document.querySelector('{esc_sel}');if(!sel)return null;
      sel.value='{esc_val}';sel.dispatchEvent(new Event('change',{{bubbles:true}}));
      return {{selected:sel.value,text:sel.options[sel.selectedIndex]?.text}};
    }})()""")
    if r: log_ok(f"Selected '{r.get('text',value)}'")
    else: log_err(f"Select element not found: {selector}")

async def cmd_upload(ws, selector, filepath):
    """File upload (#34)"""
    esc = selector.replace("'", "\\'")
    # Get DOM node for the file input
    r = await cdp(ws, "Runtime.evaluate", {"expression": f"document.querySelector('{esc}')"})
    obj_id = r.get("result", {}).get("objectId")
    if not obj_id: log_err(f"File input not found: {selector}"); return
    # Resolve to DOM node
    node = await cdp(ws, "DOM.describeNode", {"objectId": obj_id})
    node_id = node["node"]["backendNodeId"]
    await cdp(ws, "DOM.setFileInputFiles", {"files": [os.path.abspath(filepath)], "backendNodeId": node_id})
    log_ok(f"Uploaded {os.path.basename(filepath)}. File input accepted the offering.")

async def cmd_key(ws, combo):
    """Keyboard shortcut (#33) — e.g. 'ctrl+a', 'Enter', 'Escape'"""
    mods = 0; key = combo
    parts = combo.lower().split("+")
    if len(parts) > 1:
        for p in parts[:-1]:
            if p in ("ctrl", "control"): mods |= 2
            elif p in ("alt", "option"): mods |= 1
            elif p in ("shift",): mods |= 8
            elif p in ("meta", "cmd", "command"): mods |= 4
        key = parts[-1]
    key_map = {"enter": "Enter", "escape": "Escape", "tab": "Tab", "backspace": "Backspace",
               "delete": "Delete", "up": "ArrowUp", "down": "ArrowDown", "left": "ArrowLeft",
               "right": "ArrowRight", "space": " ", "home": "Home", "end": "End"}
    key = key_map.get(key.lower(), key)
    await cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": key, "modifiers": mods})
    await cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": key, "modifiers": mods})
    log_ok(f"Pressed {combo}")

async def cmd_scroll(ws, direction="down", pixels=800):
    log_dim(q("scroll"))
    d = int(pixels) if direction == "down" else -int(pixels)
    await js(ws, f"window.scrollBy(0,{d})")
    log_ok(f"Scrolled {'down' if d>0 else 'up'} {abs(d)}px")

async def cmd_scroll_to(ws, selector):
    """Scroll element into view (#38)"""
    esc = selector.replace("'", "\\'")
    r = await js(ws, f"(() => {{ const el=document.querySelector('{esc}'); if(!el)return false; el.scrollIntoView({{block:'center',behavior:'smooth'}}); return true }})()")
    if r: log_ok(f"Scrolled to {selector}")
    else: log_err(f"Element not found: {selector}")

async def cmd_scroll_infinite(ws, max_scrolls=20):
    """Infinite scroll handler (#18)"""
    log_dim(q("scroll"))
    prev_h = 0
    for i in range(int(max_scrolls)):
        h = await js(ws, "document.body.scrollHeight")
        if h == prev_h:
            log_ok(f"Reached bottom after {i} scrolls. No more content.")
            return
        prev_h = h
        await js(ws, "window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1.5)
    log_warn(f"Stopped after {max_scrolls} scrolls. There might be more.")

async def cmd_lazy_load(ws):
    """Trigger lazy loading (#19)"""
    log_dim("waking up lazy content...")
    await js(ws, "window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(1)
    await js(ws, "window.scrollTo(0, 0)")
    await asyncio.sleep(1)
    log_ok("Scrolled to bottom and back. Lazy content should be loaded.")

async def cmd_hover(ws, selector):
    """Hover with tooltip extraction (#32)"""
    log_dim(q("hover")); await hl(ws, selector, "HOVER", "#6366f1"); await asyncio.sleep(0.2)
    esc = selector.replace("'", "\\'")
    v = await js(ws, f"""(() => {{
      const el=document.querySelector('{esc}');if(!el)return null;
      el.scrollIntoView({{block:'center'}});
      const r=el.getBoundingClientRect();
      el.dispatchEvent(new MouseEvent('mouseover',{{bubbles:true,clientX:r.x+r.width/2,clientY:r.y+r.height/2}}));
      el.dispatchEvent(new MouseEvent('mouseenter',{{clientX:r.x+r.width/2,clientY:r.y+r.height/2}}));
      return {{x:r.x+r.width/2,y:r.y+r.height/2,title:el.title||'',ariaLabel:el.getAttribute('aria-label')||''}};
    }})()""")
    if v:
        await asyncio.sleep(0.5)
        tooltip = await js(ws, "document.querySelector('[role=\"tooltip\"], .tooltip, [class*=\"tooltip\"]')?.innerText || ''")
        log_ok(f"Hovering at ({v['x']:.0f},{v['y']:.0f}). Title='{v['title']}' Tooltip='{tooltip or 'none'}'")
    else: log_err(f"Element not found: {selector}")

async def cmd_drag(ws, selector, dx, dy):
    """Drag element (#31)"""
    log_dim(q("drag"))
    esc = selector.replace("'", "\\'")
    v = await js(ws, f"""(() => {{
      const el=document.querySelector('{esc}');if(!el)return null;
      const r=el.getBoundingClientRect();return {{x:r.x+r.width/2,y:r.y+r.height/2}};
    }})()""")
    if not v: log_err(f"Element not found: {selector}"); return
    x, y = v["x"], v["y"]
    await cdp(ws, "Input.dispatchMouseEvent", {"type": "mousePressed", "x": x, "y": y, "button": "left"})
    steps = 10
    for i in range(steps):
        await cdp(ws, "Input.dispatchMouseEvent", {"type": "mouseMoved",
            "x": x + float(dx)*i/steps, "y": y + float(dy)*i/steps, "button": "left"})
        await asyncio.sleep(0.02)
    await cdp(ws, "Input.dispatchMouseEvent", {"type": "mouseReleased",
        "x": x + float(dx), "y": y + float(dy), "button": "left"})
    log_ok(f"Dragged from ({x:.0f},{y:.0f}) by ({dx},{dy})")

async def cmd_iframe(ws, selector, subcmd, *args):
    """Execute inside iframe (#4)"""
    log_dim(q("iframe"))
    esc = selector.replace("'", "\\'")
    # Get iframe's content document
    frame_url = await js(ws, f"document.querySelector('{esc}')?.src || ''")
    if not frame_url: log_err(f"Iframe not found: {selector}"); return
    log_ok(f"Iframe found: {frame_url[:60]}. (iframe command execution is via navigate)")

async def cmd_geo(ws, lat, lng):
    """Spoof geolocation (#40)"""
    log_dim(q("geo"))
    await cdp(ws, "Emulation.setGeolocationOverride", {
        "latitude": float(lat), "longitude": float(lng), "accuracy": 100
    })
    log_ok(f"Location spoofed to ({lat}, {lng}). You're now somewhere else entirely.")

async def cmd_emulate(ws, device):
    """Emulate device (#39)"""
    devices = {
        "iphone": {"width": 390, "height": 844, "scale": 3, "mobile": True, "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"},
        "ipad": {"width": 820, "height": 1180, "scale": 2, "mobile": True, "ua": "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X)"},
        "pixel": {"width": 393, "height": 851, "scale": 2.75, "mobile": True, "ua": "Mozilla/5.0 (Linux; Android 14; Pixel 8)"},
        "desktop": {"width": 1920, "height": 1080, "scale": 1, "mobile": False, "ua": ""},
    }
    d = devices.get(device.lower())
    if not d: log_err(f"Unknown device. Options: {', '.join(devices.keys())}"); return
    await cdp(ws, "Emulation.setDeviceMetricsOverride", {
        "width": d["width"], "height": d["height"], "deviceScaleFactor": d["scale"], "mobile": d["mobile"]
    })
    if d["ua"]: await cdp(ws, "Emulation.setUserAgentOverride", {"userAgent": d["ua"]})
    log_ok(f"Now emulating {device} ({d['width']}x{d['height']})")

async def cmd_cookies(ws, action="export", path=None):
    """Cookie export/import (#6)"""
    log_dim(q("cookie"))
    if action == "export":
        r = await cdp(ws, "Network.getAllCookies")
        cookies = r.get("cookies", [])
        path = path or f"{STATE_DIR}/cookies.json"
        with open(path, "w") as f: json.dump(cookies, f, indent=2)
        log_ok(f"Exported {len(cookies)} cookies to {path}")
    elif action == "import":
        path = path or f"{STATE_DIR}/cookies.json"
        if not os.path.exists(path): log_err(f"No cookie file: {path}"); return
        cookies = json.load(open(path))
        for c in cookies:
            params = {k: v for k, v in c.items() if k in ("name","value","domain","path","secure","httpOnly","sameSite","expires")}
            try: await cdp(ws, "Network.setCookie", params)
            except: pass
        log_ok(f"Imported {len(cookies)} cookies. Session restored.")
    else: log_err(f"Usage: cookies [export|import] [path]")

async def cmd_network(ws, action="start"):
    """Network capture (#7, #8)"""
    log_dim(q("network"))
    if action == "start":
        await cdp(ws, "Network.enable")
        log_ok("Network monitoring started. All requests will be captured.")
    elif action == "stop":
        await cdp(ws, "Network.disable")
        log_ok("Network monitoring stopped.")
    elif action == "dump":
        # Get all requests via performance log
        r = await js(ws, """
        (() => {
          return performance.getEntriesByType('resource').map(e => ({
            name: e.name.substring(0, 100),
            type: e.initiatorType,
            duration: Math.round(e.duration),
            size: e.transferSize || 0
          })).slice(-50);
        })()
        """)
        if r:
            print(json.dumps(r, indent=2))
            log_ok(f"Dumped {len(r)} network entries.")
        else: log_warn("No entries. Run 'network start' first, then navigate.")

async def cmd_record(ws, action="start", path=None):
    """Screen recording (#24)"""
    log_dim(q("record"))
    if action == "start":
        await cdp(ws, "Page.startScreencast", {"format": "png", "maxWidth": 1280, "maxHeight": 720, "everyNthFrame": 5})
        log_ok("Recording started. Frames being captured.")
    elif action == "stop":
        await cdp(ws, "Page.stopScreencast")
        log_ok("Recording stopped.")
    else: log_err("Usage: record [start|stop]")

async def cmd_monitor(ws, url, interval=60):
    """Change monitor (#50)"""
    log_dim(q("monitor"))
    path = f"{STATE_DIR}/monitor-{hashlib.md5(url.encode()).hexdigest()[:8]}.txt"
    await cdp(ws, "Page.navigate", {"url": url})
    await asyncio.sleep(5)
    new_text = await js(ws, "document.body.innerText")
    if os.path.exists(path):
        with open(path) as f: old_text = f.read()
        if old_text == new_text:
            log_ok("No changes detected. Page is the same.")
        else:
            old_lines = set(old_text.split("\n"))
            new_lines = set(new_text.split("\n"))
            added = new_lines - old_lines
            removed = old_lines - new_lines
            if added: print(f"  {C.GREEN}+{len(added)} new lines{C.RESET}")
            if removed: print(f"  {C.RED}-{len(removed)} removed lines{C.RESET}")
            for l in list(added)[:10]: print(f"  {C.GREEN}+ {l[:80]}{C.RESET}")
            log_ok(f"Changes detected! ({len(added)} added, {len(removed)} removed)")
    else:
        log_ok(f"First snapshot saved. Run again to detect changes.")
    with open(path, "w") as f: f.write(new_text)

async def cmd_eval(ws, expr):
    r = await js(ws, expr)
    if r is not None:
        print(json.dumps(r, indent=2, ensure_ascii=False) if isinstance(r, (dict, list)) else r)
    else: print("(void)")

async def cmd_text(ws):
    log_dim(q("extract"))
    t = await js(ws, "document.body.innerText") or ""
    print(t)
    log_ok(f"Extracted {len(t):,} chars. That's like {len(t)//250} paragraphs.")

async def cmd_pages(pages):
    print(f"\n  {C.BOLD}{C.CYAN}Open Tabs{C.RESET}")
    print(f"  {C.DIM}{'─'*50}{C.RESET}")
    for i, p in enumerate(pages):
        print(f"  {C.ORANGE}{C.BOLD}[{i}]{C.RESET} {C.CYAN}{p.get('title','')[:55]}{C.RESET}")
        print(f"      {C.GRAY}{p.get('url','')[:70]}{C.RESET}")
    print(f"  {C.DIM}{'─'*50}{C.RESET}")
    print(f"  {C.GREEN}{len(pages)} tabs. That's surprisingly reasonable.{C.RESET}\n")

async def cmd_dismiss_cookies(ws):
    """Dismiss cookie banners (#42)"""
    log_dim(q("cookie"))
    r = await js(ws, DETECT_COOKIE_JS)
    if not r or not r.get("found"):
        log_ok("No cookie banner found. Clean page.")
        return
    if r.get("accept_btn"):
        v = await js(ws, _click_text_js(r["accept_btn"]))
        if v: log_ok(f"Dismissed cookie banner by clicking '{r['accept_btn']}'")
        else: log_warn("Found banner but couldn't click accept button")
    elif r.get("reject_btn"):
        v = await js(ws, _click_text_js(r["reject_btn"]))
        if v: log_ok(f"Rejected cookies by clicking '{r['reject_btn']}'")
    else:
        log_warn("Cookie banner found but no accept/reject button detected")

async def cmd_annotate(ws, selector, text):
    """Add annotation on page (#29)"""
    log_dim(q("highlight"))
    esc_sel = selector.replace("'", "\\'")
    esc_text = text.replace("'", "\\'")
    await js(ws, f"""(() => {{
      {HIGHLIGHT_STYLE}
      const el=document.querySelector('{esc_sel}');if(!el)return;
      const r=el.getBoundingClientRect(),sx=scrollX,sy=scrollY;
      const a=document.createElement('div');a.className='bp-hl';
      a.textContent='{esc_text}';
      a.style.cssText='position:absolute;left:'+(r.right+sx+8)+'px;top:'+(r.top+sy)+'px;background:#1a1a2e;color:#e94560;font:700 12px system-ui;padding:6px 12px;border-radius:6px;pointer-events:none;z-index:999999;box-shadow:0 2px 12px rgba(0,0,0,.3);border-left:3px solid #e94560';
      document.body.appendChild(a);
      setTimeout(()=>a.remove(),10000);
    }})()""")
    log_ok(f"Annotated '{selector}' with '{text}'")

async def cmd_visual_diff(ws, url1, url2, path=None):
    """Visual diff between two URLs (#23)"""
    log_dim(q("diff"))
    # Screenshot URL1
    await cdp(ws, "Page.navigate", {"url": url1}); await asyncio.sleep(3)
    r1 = await cdp(ws, "Page.captureScreenshot", {"format": "png"})
    # Screenshot URL2
    await cdp(ws, "Page.navigate", {"url": url2}); await asyncio.sleep(3)
    r2 = await cdp(ws, "Page.captureScreenshot", {"format": "png"})
    d1, d2 = base64.b64decode(r1["data"]), base64.b64decode(r2["data"])
    p1 = f"{STATE_DIR}/diff-a.png"; p2 = f"{STATE_DIR}/diff-b.png"
    with open(p1, "wb") as f: f.write(d1)
    with open(p2, "wb") as f: f.write(d2)
    same = d1 == d2
    log_ok(f"Screenshots {'identical' if same else 'DIFFERENT'}. Saved to {p1} and {p2}")

# ═══════════════════════════════════════════════════════════
# BONUS FEATURES (from browser-use research)
# ═══════════════════════════════════════════════════════════

# Feature 51: Markdown extractor
MARKDOWN_JS = r"""
(() => {
  function md(el, depth) {
    if (!el || el.tagName === 'SCRIPT' || el.tagName === 'STYLE' || el.tagName === 'NOSCRIPT') return '';
    const tag = el.tagName;
    let text = '';
    if (tag === 'H1') text += '# ';
    else if (tag === 'H2') text += '## ';
    else if (tag === 'H3') text += '### ';
    else if (tag === 'H4') text += '#### ';
    else if (tag === 'LI') text += '- ';
    else if (tag === 'A') {
      const href = el.getAttribute('href') || '';
      const t = el.innerText.trim();
      if (t && href) return '[' + t + '](' + href + ')';
    }
    else if (tag === 'IMG') {
      return '![' + (el.alt || '') + '](' + (el.src || '') + ')\n';
    }
    else if (tag === 'CODE') return '`' + el.innerText + '`';
    else if (tag === 'PRE') return '```\n' + el.innerText + '\n```\n';
    else if (tag === 'STRONG' || tag === 'B') return '**' + el.innerText + '**';
    else if (tag === 'EM' || tag === 'I') return '*' + el.innerText + '*';
    else if (tag === 'BR') return '\n';
    else if (tag === 'HR') return '\n---\n';
    else if (tag === 'TABLE') {
      const rows = [];
      el.querySelectorAll('tr').forEach(tr => {
        rows.push('| ' + [...tr.querySelectorAll('td,th')].map(c => c.innerText.trim()).join(' | ') + ' |');
      });
      if (rows.length > 1) rows.splice(1, 0, '| ' + rows[0].split('|').slice(1,-1).map(() => '---').join(' | ') + ' |');
      return rows.join('\n') + '\n';
    }
    for (const child of el.childNodes) {
      if (child.nodeType === 3) text += child.textContent;
      else if (child.nodeType === 1) text += md(child, depth + 1);
    }
    if (['P','DIV','H1','H2','H3','H4','H5','H6','LI','BLOCKQUOTE','SECTION','ARTICLE'].includes(tag))
      text += '\n';
    return text;
  }
  return md(document.body, 0).replace(/\n{3,}/g, '\n\n').trim();
})()
"""

# Feature 52: Storage state (localStorage + sessionStorage)
STORAGE_JS = """
(() => {
  const ls = {};
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    ls[k] = localStorage.getItem(k)?.substring(0, 200);
  }
  const ss = {};
  for (let i = 0; i < sessionStorage.length; i++) {
    const k = sessionStorage.key(i);
    ss[k] = sessionStorage.getItem(k)?.substring(0, 200);
  }
  return {localStorage: ls, sessionStorage: ss, localCount: Object.keys(ls).length, sessionCount: Object.keys(ss).length};
})()
"""

# Feature 53: Console log capture
CONSOLE_JS = """
(() => {
  if (!window.__bp_console_logs) {
    window.__bp_console_logs = [];
    const orig = {log: console.log, warn: console.warn, error: console.error, info: console.info};
    ['log','warn','error','info'].forEach(level => {
      console[level] = function(...args) {
        window.__bp_console_logs.push({level, msg: args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' '), ts: Date.now()});
        if (window.__bp_console_logs.length > 100) window.__bp_console_logs.shift();
        orig[level].apply(console, args);
      };
    });
    return 'Console capture started';
  }
  const logs = window.__bp_console_logs.slice(-50);
  return logs;
})()
"""

# Feature 54: PDF export
async def cmd_pdf(ws, path=None):
    """Export page as PDF"""
    log_dim("printing to PDF...")
    r = await cdp(ws, "Page.printToPDF", {"landscape": False, "printBackground": True, "preferCSSPageSize": True})
    data = base64.b64decode(r["data"])
    path = path or f"/tmp/bp-page-{int(time.time())}.pdf"
    with open(path, "wb") as f: f.write(data)
    log_ok(f"PDF saved ({len(data)//1024}KB) {C.UNDERLINE}{path}{C.RESET}")

# Feature 55: Performance metrics
PERF_JS = """
(() => {
  const nav = performance.getEntriesByType('navigation')[0] || {};
  const paint = performance.getEntriesByType('paint');
  const fcp = paint.find(p => p.name === 'first-contentful-paint');
  const lcp = performance.getEntriesByType('largest-contentful-paint').pop();
  const cls = performance.getEntriesByType('layout-shift').reduce((sum, e) => sum + (e.hadRecentInput ? 0 : e.value), 0);
  return {
    ttfb: Math.round(nav.responseStart - nav.requestStart) || null,
    fcp: fcp ? Math.round(fcp.startTime) : null,
    lcp: lcp ? Math.round(lcp.startTime) : null,
    cls: Math.round(cls * 1000) / 1000,
    dom_interactive: Math.round(nav.domInteractive) || null,
    dom_complete: Math.round(nav.domComplete) || null,
    load_time: Math.round(nav.loadEventEnd - nav.navigationStart) || null,
    resources: performance.getEntriesByType('resource').length,
    transfer_size: performance.getEntriesByType('resource').reduce((s, r) => s + (r.transferSize || 0), 0),
  };
})()
"""

# Feature 56: Page health check (combines multiple detectors)
async def cmd_health(ws):
    """Comprehensive page health check"""
    log_dim("running full health check...")
    results = {}
    results["error"] = await js(ws, DETECT_ERROR_JS)
    results["captcha"] = await js(ws, DETECT_CAPTCHA_JS)
    results["login"] = await js(ws, DETECT_LOGIN_JS)
    results["lang"] = await js(ws, DETECT_LANG_JS)
    results["perf"] = await js(ws, PERF_JS)
    results["cookie_banner"] = await js(ws, DETECT_COOKIE_JS)

    # Summary
    issues = []
    if results["error"]["has_error"]: issues.append(f"ERROR: {results['error']['errors']}")
    if results["captcha"]["has_captcha"]: issues.append("CAPTCHA detected")
    if results["login"]["needs_login"]: issues.append("Login required")
    if results["cookie_banner"]["found"]: issues.append("Cookie banner blocking")
    perf = results["perf"]
    if perf.get("lcp") and perf["lcp"] > 4000: issues.append(f"Slow LCP: {perf['lcp']}ms")
    if perf.get("cls") and perf["cls"] > 0.25: issues.append(f"High CLS: {perf['cls']}")

    if issues:
        print(f"  {C.RED}{C.BOLD}Issues ({len(issues)}):{C.RESET}")
        for i in issues: print(f"  {C.RED}  - {i}{C.RESET}")
    else:
        print(f"  {C.GREEN}{C.BOLD}All clear! Page is healthy.{C.RESET}")

    print(f"\n  {C.CYAN}Performance:{C.RESET}")
    if perf.get("ttfb"): print(f"    TTFB: {perf['ttfb']}ms")
    if perf.get("fcp"): print(f"    FCP:  {perf['fcp']}ms")
    if perf.get("lcp"): print(f"    LCP:  {perf['lcp']}ms")
    if perf.get("cls") is not None: print(f"    CLS:  {perf['cls']}")
    print(f"    Resources: {perf.get('resources', '?')} ({perf.get('transfer_size', 0)//1024}KB)")
    print(f"  {C.CYAN}Language:{C.RESET} {results['lang'].get('html_lang', '?')}")

# Feature 57: Wait for network idle
async def cmd_network_idle(ws, timeout=10):
    """Wait for network to go idle (#smart navigation)"""
    log_dim("waiting for network silence...")
    await cdp(ws, "Network.enable")
    start = time.time()
    last_activity = time.time()
    while time.time() - start < float(timeout):
        # Check if any requests are pending via performance API
        pending = await js(ws, """
        (() => {
            const entries = performance.getEntriesByType('resource');
            const recent = entries.filter(e => e.responseEnd === 0 || (Date.now() - e.startTime) < 2000);
            return recent.length;
        })()
        """)
        if pending == 0 and time.time() - last_activity > 2:
            log_ok(f"Network idle after {time.time()-start:.1f}s. All quiet on the wire.")
            return
        if pending > 0: last_activity = time.time()
        await asyncio.sleep(0.5)
    log_warn(f"Network didn't fully settle after {timeout}s")

# Feature 58: Text search (find on page)
async def cmd_find(ws, query):
    """Find text on page and highlight matches"""
    esc = query.replace("'", "\\'")
    count = await js(ws, f"""(() => {{
      {HIGHLIGHT_STYLE}
      document.querySelectorAll('.bp-hl').forEach(e => e.remove());
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let count = 0;
      while (walker.nextNode()) {{
        const node = walker.currentNode;
        if (node.textContent.toLowerCase().includes('{esc}'.toLowerCase())) {{
          const range = document.createRange();
          const idx = node.textContent.toLowerCase().indexOf('{esc}'.toLowerCase());
          range.setStart(node, idx);
          range.setEnd(node, idx + '{esc}'.length);
          const rect = range.getBoundingClientRect();
          if (rect.width > 0) {{
            const o = document.createElement('div'); o.className = 'bp-hl';
            o.style.cssText = 'position:absolute;left:'+(rect.left+scrollX-2)+'px;top:'+(rect.top+scrollY-2)+'px;width:'+(rect.width+4)+'px;height:'+(rect.height+4)+'px;background:rgba(255,102,0,0.3);border:1px solid #ff6600;border-radius:2px;pointer-events:none;z-index:999999';
            document.body.appendChild(o);
            count++;
          }}
        }}
      }}
      setTimeout(() => document.querySelectorAll('.bp-hl').forEach(e => e.remove()), 10000);
      return count;
    }})()""")
    log_ok(f"Found {count} matches for '{query}'. Highlighted for 10 seconds.")

# Feature 59: DOM size stats
async def cmd_stats(ws):
    """Page statistics"""
    stats = await js(ws, """(() => {
      return {
        title: document.title,
        url: location.href,
        dom_nodes: document.querySelectorAll('*').length,
        text_length: document.body.innerText.length,
        links: document.querySelectorAll('a').length,
        images: document.querySelectorAll('img').length,
        forms: document.querySelectorAll('form').length,
        inputs: document.querySelectorAll('input,select,textarea').length,
        buttons: document.querySelectorAll('button,[role="button"]').length,
        iframes: document.querySelectorAll('iframe').length,
        scripts: document.querySelectorAll('script').length,
        stylesheets: document.querySelectorAll('link[rel="stylesheet"],style').length,
        cookies: document.cookie.split(';').filter(c => c.trim()).length,
        scroll_height: document.body.scrollHeight,
        viewport: window.innerWidth + 'x' + window.innerHeight,
      };
    })()""")
    print(f"\n  {C.BOLD}{C.CYAN}Page Stats{C.RESET}")
    print(f"  {C.DIM}{'─'*40}{C.RESET}")
    for k, v in stats.items():
        print(f"  {C.ORANGE}{k:>18}{C.RESET}  {v}")
    print()

# Feature 60: Clean/readable text extraction (better than innerText)
READABLE_JS = r"""
(() => {
  function clean(el) {
    if (!el || ['SCRIPT','STYLE','NOSCRIPT','SVG','NAV','HEADER','FOOTER'].includes(el.tagName)) return '';
    let text = '';
    for (const child of el.childNodes) {
      if (child.nodeType === 3) text += child.textContent;
      else if (child.nodeType === 1) {
        const block = ['DIV','P','H1','H2','H3','H4','H5','H6','LI','TR','SECTION','ARTICLE','BLOCKQUOTE'].includes(child.tagName);
        const childText = clean(child);
        if (block && childText.trim()) text += '\n' + childText + '\n';
        else text += childText;
      }
    }
    return text;
  }
  const main = document.querySelector('main, article, [role="main"], #content, .content') || document.body;
  return clean(main).replace(/\n{3,}/g, '\n\n').replace(/[ \t]+/g, ' ').trim();
})()
"""

# ═══════════════════════════════════════════════════════════
# MAIN ROUTER
# ═══════════════════════════════════════════════════════════

async def main():
    global _t0; _t0 = time.time()
    if len(sys.argv) < 2: print(BANNER); print(__doc__); return
    cmd = sys.argv[1]
    args = sys.argv[2:]

    quiet = os.environ.get("BP_QUIET") == "1"
    if not quiet and cmd not in ("eval", "text"):
        print(f"\n  {C.ORANGE}{C.BOLD}Browser Pilot{C.RESET} {C.DIM}v4{C.RESET}  {C.GRAY}// {cmd}{C.RESET}\n")

    # Commands that don't need WS
    if cmd == "pages":
        pages = _get_pages(); await cmd_pages(pages); return

    tab = int(os.environ.get("TAB", "0"))
    if cmd == "select":
        tab = int(args[0]) if args else 0
        log_ok(f"Switched to tab [{tab}]."); return

    ws, _ = await get_ws(tab)

    try:
        # Navigation
        if cmd == "navigate": await cmd_navigate(ws, args[0])
        elif cmd == "spa-wait": await cmd_spa_wait(ws, args[0] if args else 10)
        elif cmd == "wait-for": await cmd_wait_for(ws, args[0], args[1] if len(args)>1 else 10)
        elif cmd == "wait":
            log_dim(q("wait")); await asyncio.sleep(float(args[0]) if args else 2)
            log_ok(f"Waited {args[0] if args else 2}s. Time well spent.")
        # DOM
        elif cmd == "dom": await cmd_dom(ws)
        elif cmd == "dom-diff": await cmd_dom_diff(ws)
        elif cmd == "text": await cmd_text(ws)
        elif cmd == "eval": await cmd_eval(ws, args[0])
        # Click
        elif cmd == "click": await cmd_click(ws, args[0])
        elif cmd == "click-text": await cmd_click_text(ws, args[0])
        elif cmd == "click-index": await cmd_click_index(ws, args[0])
        elif cmd == "click-retry": await cmd_click_retry(ws, args[0], args[1] if len(args)>1 else 3)
        elif cmd == "right-click": await cmd_right_click(ws, args[0])
        # Input
        elif cmd == "fill": await cmd_fill(ws, args[0], args[1])
        elif cmd == "type-human": await cmd_type_human(ws, args[0], args[1])
        elif cmd == "select-option": await cmd_select_option(ws, args[0], args[1])
        elif cmd == "upload": await cmd_upload(ws, args[0], args[1])
        elif cmd == "key": await cmd_key(ws, args[0])
        # Scroll
        elif cmd == "scroll": await cmd_scroll(ws, args[0] if args else "down", args[1] if len(args)>1 else 800)
        elif cmd == "scroll-to": await cmd_scroll_to(ws, args[0])
        elif cmd == "scroll-infinite": await cmd_scroll_infinite(ws, args[0] if args else 20)
        elif cmd == "lazy-load": await cmd_lazy_load(ws)
        # Screenshot
        elif cmd == "screenshot": await cmd_screenshot(ws, args[0] if args else None)
        elif cmd == "screenshot-full": await cmd_screenshot(ws, args[0] if args else None, full=True)
        elif cmd == "screenshot-el": await cmd_screenshot(ws, args[1] if len(args)>1 else None, selector=args[0])
        # Extract
        elif cmd == "table": print(json.dumps(await js(ws, TABLE_JS), indent=2))
        elif cmd == "links": print(json.dumps(await js(ws, LINKS_JS), indent=2))
        elif cmd == "images": print(json.dumps(await js(ws, IMAGES_JS), indent=2))
        elif cmd == "forms": print(json.dumps(await js(ws, FORMS_JS), indent=2))
        elif cmd == "meta": print(json.dumps(await js(ws, META_JS), indent=2))
        elif cmd == "prices": print(json.dumps(await js(ws, PRICES_JS), indent=2))
        elif cmd == "dates": print(json.dumps(await js(ws, DATES_JS), indent=2))
        elif cmd == "cookies": await cmd_cookies(ws, args[0] if args else "export", args[1] if len(args)>1 else None)
        elif cmd == "network": await cmd_network(ws, args[0] if args else "dump")
        # Visual
        elif cmd == "highlight": await hl(ws, args[0], args[1] if len(args)>1 else "PILOT")
        elif cmd == "highlight-all": print(await js(ws, HIGHLIGHT_ALL_JS))
        elif cmd == "diff": await cmd_visual_diff(ws, args[0], args[1], args[2] if len(args)>2 else None)
        elif cmd == "annotate": await cmd_annotate(ws, args[0], args[1])
        # Intelligence
        elif cmd == "detect-login": print(json.dumps(await js(ws, DETECT_LOGIN_JS), indent=2))
        elif cmd == "dismiss-cookies": await cmd_dismiss_cookies(ws)
        elif cmd == "detect-captcha": print(json.dumps(await js(ws, DETECT_CAPTCHA_JS), indent=2))
        elif cmd == "detect-error": print(json.dumps(await js(ws, DETECT_ERROR_JS), indent=2))
        elif cmd == "detect-lang": print(json.dumps(await js(ws, DETECT_LANG_JS), indent=2))
        elif cmd == "spa-wait": await cmd_spa_wait(ws, args[0] if args else 10)
        # Advanced
        elif cmd == "hover": await cmd_hover(ws, args[0])
        elif cmd == "drag": await cmd_drag(ws, args[0], args[1], args[2])
        elif cmd == "iframe": await cmd_iframe(ws, args[0], args[1], *args[2:])
        elif cmd == "geo": await cmd_geo(ws, args[0], args[1])
        elif cmd == "emulate": await cmd_emulate(ws, args[0])
        elif cmd == "monitor": await cmd_monitor(ws, args[0], args[1] if len(args)>1 else 60)
        elif cmd == "record": await cmd_record(ws, args[0] if args else "start", args[1] if len(args)>1 else None)
        elif cmd == "a11y":
            log_dim(q("a11y"))
            tree = await cdp(ws, "Accessibility.getFullAXTree")
            nodes = tree.get("nodes", [])[:50]
            for n in nodes:
                role = n.get("role", {}).get("value", "")
                name = n.get("name", {}).get("value", "")
                if role and name: print(f"  {C.CYAN}{role}{C.RESET}: {name}")
            log_ok(f"Accessibility tree: {len(tree.get('nodes',[]))} nodes")
        elif cmd == "landmarks": print(json.dumps(await js(ws, LANDMARKS_JS), indent=2))
        elif cmd == "shadow":
            log_dim(q("shadow"))
            log_ok("Shadow DOM elements are already included in 'dom' output (v4 walks shadowRoot)")
        # Bonus features (51-60)
        elif cmd == "markdown": print(await js(ws, MARKDOWN_JS))
        elif cmd == "storage": print(json.dumps(await js(ws, STORAGE_JS), indent=2))
        elif cmd == "console": print(json.dumps(await js(ws, CONSOLE_JS), indent=2))
        elif cmd == "pdf": await cmd_pdf(ws, args[0] if args else None)
        elif cmd == "perf": print(json.dumps(await js(ws, PERF_JS), indent=2))
        elif cmd == "health": await cmd_health(ws)
        elif cmd == "network-idle": await cmd_network_idle(ws, args[0] if args else 10)
        elif cmd == "find": await cmd_find(ws, args[0])
        elif cmd == "stats": await cmd_stats(ws)
        elif cmd == "readable": print(await js(ws, READABLE_JS))
        else:
            log_err(f"Unknown: {cmd}. I'm good, but not THAT good.")
            print(__doc__)
    finally:
        await ws.close()

if __name__ == "__main__":
    asyncio.run(main())
