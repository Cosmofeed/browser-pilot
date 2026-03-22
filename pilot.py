#!/usr/bin/env python3
"""
 Browser Pilot v3
 Your browser, your rules. No external LLM. No API keys. Just vibes.

Usage:
  pilot.py navigate "https://example.com"
  pilot.py dom                          # compressed DOM
  pilot.py screenshot [path]            # save screenshot
  pilot.py click "css-selector"         # click element
  pilot.py click-text "Button Text"     # click by visible text
  pilot.py click-index 5                # click by DOM index
  pilot.py fill "css-selector" "value"  # fill input
  pilot.py eval "js expression"         # run JS
  pilot.py text                         # all page text
  pilot.py pages                        # list tabs
  pilot.py scroll [up|down] [pixels]    # scroll
  pilot.py wait <seconds>               # wait
"""

import asyncio
import json
import sys
import base64
import os
import random
import time

import websockets

CDP_URL = os.environ.get("CDP_URL", "http://localhost:9222")

# ═══════════════════════════════════════════════════════════
# STYLE
# ═══════════════════════════════════════════════════════════

class C:
    """ANSI colors"""
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ORANGE = "\033[38;5;208m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"
    GRAY = "\033[90m"
    RESET = "\033[0m"
    UNDERLINE = "\033[4m"

QUIPS_NAVIGATE = [
    "fasten your seatbelt...",
    "off we go...",
    "charting a course...",
    "engaging hyperdrive...",
    "the internet awaits...",
    "buckle up, buttercup...",
    "dialing up the modem...",
    "not all who wander are lost, but we know exactly where we're going...",
]

QUIPS_CLICK = [
    "smashing that button...",
    "precision strike incoming...",
    "applying finger to screen...",
    "the click heard around the world...",
    "one small click for bot, one giant leap for automation...",
    "button never saw it coming...",
    "tactical click deployed...",
    "boop...",
]

QUIPS_DOM = [
    "reading the matrix...",
    "parsing the digital tea leaves...",
    "deconstructing reality...",
    "counting all the things you can poke...",
    "surveying the land...",
    "x-ray vision: engaged...",
    "unzipping the page...",
]

QUIPS_EXTRACT = [
    "absorbing knowledge...",
    "speed reading at 1,000,000 wpm...",
    "photographic memory activated...",
    "downloading the vibes...",
    "ctrl+c on reality...",
]

QUIPS_SCROLL = [
    "scrolling into the abyss...",
    "exploring below the fold...",
    "there's always more content...",
    "the scroll of truth reveals...",
]

QUIPS_WAIT = [
    "patience is a virtue...",
    "contemplating existence...",
    "counting sheep...",
    "good things come to those who wait...",
]

QUIPS_SCREENSHOT = [
    "say cheese...",
    "capturing the moment...",
    "one for the album...",
    "freeze frame...",
]

BANNER = f"""{C.ORANGE}{C.BOLD}
  ____                                   ____  _ _       _
 | __ ) _ __ _____      _____  ___ _ __|  _ \\(_) | ___ | |_
 |  _ \\| '__/ _ \\ \\ /\\ / / __|/ _ \\ '__| |_) | | |/ _ \\| __|
 | |_) | | | (_) \\ V  V /\\__ \\  __/ |  |  __/| | | (_) | |_
 |____/|_|  \\___/ \\_/\\_/ |___/\\___|_|  |_|   |_|_|\\___/ \\__|
                                                    {C.DIM}v3{C.RESET}
{C.GRAY}  Your browser. Your rules. No external LLM. Zero cost.{C.RESET}
"""

def quip(category):
    return random.choice(category)

def log(icon, msg, color=C.CYAN):
    elapsed = time.time() - _start_time
    ts = f"{C.GRAY}{elapsed:6.1f}s{C.RESET}"
    print(f"  {ts}  {color}{icon}{C.RESET}  {msg}")

def log_success(msg):
    log("", msg, C.GREEN)

def log_action(msg):
    log("", msg, C.ORANGE)

def log_info(msg):
    log("", msg, C.CYAN)

def log_dim(msg):
    log("", msg, C.GRAY)

def log_error(msg):
    log("", msg, C.RED)

_start_time = time.time()

# ═══════════════════════════════════════════════════════════
# HIGHLIGHT ENGINE (injected into page)
# ═══════════════════════════════════════════════════════════

HIGHLIGHT_JS = """
(function(el, label) {
    // Remove previous highlights
    document.querySelectorAll('.bp-highlight').forEach(e => e.remove());

    if (!el) return;

    const rect = el.getBoundingClientRect();
    const scrollX = window.scrollX;
    const scrollY = window.scrollY;

    // Create highlight overlay
    const overlay = document.createElement('div');
    overlay.className = 'bp-highlight';
    overlay.style.cssText = `
        position: absolute;
        left: ${rect.left + scrollX - 4}px;
        top: ${rect.top + scrollY - 4}px;
        width: ${rect.width + 8}px;
        height: ${rect.height + 8}px;
        border: 2px solid #ff6600;
        border-radius: 6px;
        pointer-events: none;
        z-index: 999999;
        box-shadow: 0 0 0 2px rgba(255,102,0,0.15), 0 0 20px rgba(255,102,0,0.3);
        animation: bp-pulse 1.5s ease-in-out infinite;
    `;

    // Create label badge
    const badge = document.createElement('div');
    badge.className = 'bp-highlight';
    badge.style.cssText = `
        position: absolute;
        left: ${rect.left + scrollX - 4}px;
        top: ${rect.top + scrollY - 22}px;
        background: linear-gradient(135deg, #ff6600, #ff8533);
        color: white;
        font-size: 11px;
        font-weight: 700;
        font-family: system-ui, -apple-system, sans-serif;
        padding: 2px 8px;
        border-radius: 4px 4px 0 0;
        pointer-events: none;
        z-index: 999999;
        letter-spacing: 0.5px;
        box-shadow: 0 -2px 8px rgba(255,102,0,0.3);
    `;
    badge.textContent = label || 'PILOT';

    // Add pulse animation
    if (!document.querySelector('#bp-style')) {
        const style = document.createElement('style');
        style.id = 'bp-style';
        style.textContent = `
            @keyframes bp-pulse {
                0%, 100% { box-shadow: 0 0 0 2px rgba(255,102,0,0.15), 0 0 20px rgba(255,102,0,0.3); }
                50% { box-shadow: 0 0 0 4px rgba(255,102,0,0.25), 0 0 30px rgba(255,102,0,0.5); }
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(overlay);
    document.body.appendChild(badge);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        overlay.remove();
        badge.remove();
    }, 3000);
})
"""

CLEAR_HIGHLIGHTS_JS = """
document.querySelectorAll('.bp-highlight').forEach(e => e.remove());
"""

# ═══════════════════════════════════════════════════════════
# CDP CLIENT
# ═══════════════════════════════════════════════════════════

async def get_ws_url(target_idx=None):
    import urllib.request
    resp = urllib.request.urlopen(f"{CDP_URL}/json/list")
    pages = json.loads(resp.read())
    real_pages = [p for p in pages if p.get("type") == "page"]
    if not real_pages:
        log_error("No pages open in Chrome")
        sys.exit(1)
    if target_idx is not None:
        if target_idx < len(real_pages):
            return real_pages[target_idx]["webSocketDebuggerUrl"], real_pages
        else:
            log_error(f"Tab {target_idx} out of range (0-{len(real_pages)-1})")
            sys.exit(1)
    return real_pages[0]["webSocketDebuggerUrl"], real_pages


async def send_cdp(ws, method, params=None, msg_id=[0]):
    msg_id[0] += 1
    mid = msg_id[0]
    msg = {"id": mid, "method": method, "params": params or {}}
    await ws.send(json.dumps(msg))
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=30)
        data = json.loads(raw)
        if data.get("id") == mid:
            if "error" in data:
                raise RuntimeError(f"CDP error: {data['error']}")
            return data.get("result", {})


async def highlight(ws, selector, label="PILOT"):
    """Inject beautiful highlight on target element."""
    escaped = selector.replace("'", "\\'").replace('"', '\\"')
    js = f"({HIGHLIGHT_JS})(document.querySelector('{escaped}'), '{label}')"
    try:
        await send_cdp(ws, "Runtime.evaluate", {"expression": js})
    except:
        pass  # Non-critical


async def highlight_by_text(ws, text, label="PILOT"):
    """Highlight element found by text content."""
    escaped = text.replace("'", "\\'")
    js = f"""({HIGHLIGHT_JS})(
        [...document.querySelectorAll('a, button, [role="button"], [role="menuitem"], [role="tab"], [role="link"], [role="option"]')]
            .find(el => el.innerText.trim().includes('{escaped}')),
        '{label}'
    )"""
    try:
        await send_cdp(ws, "Runtime.evaluate", {"expression": js})
    except:
        pass


# ═══════════════════════════════════════════════════════════
# DOM COMPRESSION ENGINE
# ═══════════════════════════════════════════════════════════

DOM_EXTRACT_JS = r"""
(() => {
  const INTERACTIVE_TAGS = new Set(['A','BUTTON','INPUT','SELECT','TEXTAREA','DETAILS','SUMMARY']);
  const INTERACTIVE_ROLES = new Set(['button','link','menuitem','tab','checkbox','radio','switch','combobox','listbox','option','searchbox','textbox']);
  const TEXT_TAGS = new Set(['H1','H2','H3','H4','H5','H6','P','SPAN','LABEL','TD','TH','LI']);
  const SKIP_TAGS = new Set(['SCRIPT','STYLE','NOSCRIPT','SVG','PATH','META','LINK','BR','HR']);

  function isVisible(el) {
    if (!el.offsetParent && el.tagName !== 'BODY' && el.tagName !== 'HTML') return false;
    try {
      const s = window.getComputedStyle(el);
      if (s.display==='none'||s.visibility==='hidden'||s.opacity==='0') return false;
    } catch(e) { return false; }
    const r = el.getBoundingClientRect();
    return r.width > 0 || r.height > 0;
  }

  function isInteractive(el) {
    if (INTERACTIVE_TAGS.has(el.tagName)) return true;
    const role = el.getAttribute('role');
    if (role && INTERACTIVE_ROLES.has(role)) return true;
    if (el.getAttribute('tabindex') !== null) return true;
    if (el.getAttribute('contenteditable')==='true') return true;
    try { if (window.getComputedStyle(el).cursor==='pointer') return true; } catch(e) {}
    return false;
  }

  function getText(el) {
    let t = '';
    for (const c of el.childNodes) {
      if (c.nodeType === 3) t += c.textContent.trim() + ' ';
    }
    t = t.trim();
    if (!t) t = el.getAttribute('aria-label')||el.getAttribute('title')||el.getAttribute('placeholder')||el.getAttribute('alt')||'';
    if ((el.tagName==='INPUT'||el.tagName==='TEXTAREA') && el.value) t = 'value="'+el.value+'" '+t;
    return t.trim().substring(0,80);
  }

  function getDesc(el) {
    const tag = el.tagName.toLowerCase();
    const role = el.getAttribute('role');
    const id = el.getAttribute('id');
    const href = el.getAttribute('href');
    let p = [];
    if (role) p.push(role); else if (tag==='input') p.push(el.type||'text'); else p.push(tag);
    const t = getText(el);
    if (t) p.push('"'+t+'"');
    if (href && href.length<80 && !href.startsWith('javascript:')) p.push('href='+href);
    if (id) p.push('id='+id);
    if (el.disabled) p.push('[disabled]');
    return p.join(' ');
  }

  function getSelector(el) {
    if (el.id) return '#'+CSS.escape(el.id);
    const al = el.getAttribute('aria-label');
    if (al) return '[aria-label="'+CSS.escape(al)+'"]';
    const parts = [];
    let cur = el;
    while (cur && cur !== document.body) {
      let sel = cur.tagName.toLowerCase();
      if (cur.id) { parts.unshift('#'+CSS.escape(cur.id)); break; }
      const parent = cur.parentElement;
      if (parent) {
        const sibs = [...parent.children].filter(c=>c.tagName===cur.tagName);
        if (sibs.length>1) sel+=':nth-of-type('+(sibs.indexOf(cur)+1)+')';
      }
      parts.unshift(sel);
      cur = cur.parentElement;
    }
    return parts.join(' > ');
  }

  const elements = [];
  let idx = 0;
  const seen = new Set();

  function walk(node, depth) {
    if (depth>15||!node||!node.tagName||SKIP_TAGS.has(node.tagName)||seen.has(node)) return;
    seen.add(node);
    if (!isVisible(node)) return;

    const interactive = isInteractive(node);
    const text = getText(node);

    if (interactive && text) {
      idx++;
      elements.push({i:idx, t:'i', d:getDesc(node), s:getSelector(node)});
    } else if (TEXT_TAGS.has(node.tagName) && text && text.length>1) {
      elements.push({i:null, t:'t', d:node.tagName.toLowerCase()+': "'+text+'"'});
    } else if (node.tagName==='TABLE') {
      const rows=[];
      node.querySelectorAll('tr').forEach(tr=>{
        const cells=[...tr.querySelectorAll('td,th')].map(c=>c.innerText.trim().substring(0,60));
        if(cells.length>0&&cells.some(c=>c)) rows.push(cells.join(' | '));
      });
      if(rows.length>0){elements.push({i:null,t:'tbl',d:'table('+rows.length+' rows):\\n'+rows.slice(0,25).join('\\n')});return;}
    }
    for (const child of node.children) walk(child, depth+1);
  }

  walk(document.body, 0);

  const lines = ['Page: '+document.title, 'URL: '+window.location.href, '---'];
  const selectors = {};
  for (const el of elements) {
    if (el.t==='i') { lines.push('['+el.i+'] '+el.d); selectors[el.i]=el.s; }
    else if (el.t==='tbl') lines.push(el.d);
    else lines.push('    '+el.d);
  }
  lines.push('---');
  lines.push(idx+' interactive elements');
  return {dom:lines.join('\n'), selectors:selectors, count:idx};
})()
"""

# ═══════════════════════════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════════════════════════

async def cmd_navigate(ws, url):
    log_dim(quip(QUIPS_NAVIGATE))
    await send_cdp(ws, "Page.navigate", {"url": url})
    await asyncio.sleep(2)
    log_success(f"Landed on {C.UNDERLINE}{url[:70]}{C.RESET}")


async def cmd_dom(ws):
    log_dim(quip(QUIPS_DOM))
    result = await send_cdp(ws, "Runtime.evaluate", {
        "expression": DOM_EXTRACT_JS, "returnByValue": True, "awaitPromise": True,
    })
    value = result.get("result", {}).get("value", {})
    dom = value.get("dom", "")
    count = value.get("count", 0)

    # Save selectors
    selectors = value.get("selectors", {})
    with open("/tmp/browser-pilot-selectors.json", "w") as f:
        json.dump(selectors, f)

    # Pretty print the DOM
    for line in dom.split("\n"):
        if line.startswith("Page:"):
            print(f"  {C.BOLD}{C.CYAN}{line}{C.RESET}")
        elif line.startswith("URL:"):
            print(f"  {C.UNDERLINE}{C.GRAY}{line}{C.RESET}")
        elif line.startswith("["):
            idx_end = line.index("]")
            idx_str = line[:idx_end+1]
            rest = line[idx_end+1:]
            print(f"  {C.ORANGE}{C.BOLD}{idx_str}{C.RESET}{C.CYAN}{rest}{C.RESET}")
        elif line.startswith("    "):
            print(f"  {C.GRAY}{line}{C.RESET}")
        elif line.startswith("table"):
            print(f"  {C.YELLOW}{line[:60]}...{C.RESET}")
        elif line.startswith("---"):
            print(f"  {C.DIM}{'─' * 50}{C.RESET}")
        else:
            print(f"  {C.GREEN}{line}{C.RESET}")

    log_success(f"Found {C.BOLD}{count}{C.RESET}{C.GREEN} interactive elements. The page is yours.{C.RESET}")


async def cmd_screenshot(ws, path=None):
    log_dim(quip(QUIPS_SCREENSHOT))
    result = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"})
    img_data = base64.b64decode(result["data"])
    path = path or "/tmp/browser-pilot-screenshot.png"
    with open(path, "wb") as f:
        f.write(img_data)
    size_kb = len(img_data) // 1024
    log_success(f"Screenshot saved ({size_kb}KB) {C.UNDERLINE}{path}{C.RESET}")


async def cmd_click(ws, selector):
    log_dim(quip(QUIPS_CLICK))
    # Highlight first
    await highlight(ws, selector, "CLICK")
    await asyncio.sleep(0.3)

    escaped = selector.replace("'", "\\'").replace('"', '\\"')
    js = """(() => {
        const el = document.querySelector('""" + escaped + """');
        if (!el) return {ok: false};
        el.scrollIntoView({block:'center'});
        el.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true, pointerId: 1}));
        el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
        el.dispatchEvent(new PointerEvent('pointerup', {bubbles: true, pointerId: 1}));
        el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
        el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
        const r = el.getBoundingClientRect();
        return {ok: true, x: r.x + r.width/2, y: r.y + r.height/2, text: el.innerText.trim().substring(0,50)};
    })()"""
    result = await send_cdp(ws, "Runtime.evaluate", {"expression": js, "returnByValue": True})
    value = result.get("result", {}).get("value", {})
    if not value or not value.get("ok"):
        log_error(f"Element vanished into thin air: {selector}")
        return
    await asyncio.sleep(0.5)
    text = value.get("text", "")
    log_success(f"Clicked {C.BOLD}'{text}'{C.RESET}{C.GREEN} at ({value.get('x',0):.0f}, {value.get('y',0):.0f}){C.RESET}")


async def cmd_click_text(ws, text):
    log_dim(quip(QUIPS_CLICK))
    # Highlight first
    await highlight_by_text(ws, text, "CLICK")
    await asyncio.sleep(0.3)

    escaped = text.replace("'", "\\'").replace('"', '\\"')
    js = """(() => {
        const all = document.querySelectorAll('a, button, [role="button"], [role="menuitem"], [role="tab"], [role="link"], [role="option"], div[tabindex], span[tabindex]');
        for (const el of all) {
            if (el.innerText.trim().includes('""" + escaped + """')) {
                el.scrollIntoView({block:'center'});
                el.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true, pointerId: 1}));
                el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                el.dispatchEvent(new PointerEvent('pointerup', {bubbles: true, pointerId: 1}));
                el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                const r = el.getBoundingClientRect();
                return {x: r.x + r.width/2, y: r.y + r.height/2, found: el.innerText.trim().substring(0,50)};
            }
        }
        return null;
    })()"""
    result = await send_cdp(ws, "Runtime.evaluate", {"expression": js, "returnByValue": True})
    coords = result.get("result", {}).get("value")
    if not coords:
        log_error(f"Looked everywhere, couldn't find '{text}'. Maybe it's shy?")
        return
    await asyncio.sleep(0.5)
    log_success(f"Clicked {C.BOLD}'{coords['found']}'{C.RESET}{C.GREEN} at ({coords['x']:.0f}, {coords['y']:.0f}){C.RESET}")


async def cmd_click_index(ws, index):
    sel_path = "/tmp/browser-pilot-selectors.json"
    if not os.path.exists(sel_path):
        log_error("Run 'dom' first — I need a map before I can navigate!")
        return
    with open(sel_path) as f:
        selectors = json.load(f)
    selector = selectors.get(str(index))
    if not selector:
        log_error(f"Index [{index}] doesn't exist. Try 'dom' to see what's available.")
        return
    await cmd_click(ws, selector)


async def cmd_fill(ws, selector, value):
    log_action(f"Typing '{value}' into the void...")
    await highlight(ws, selector, "FILL")
    await asyncio.sleep(0.3)

    escaped_sel = selector.replace("'", "\\'")
    js = "document.querySelector('" + escaped_sel + "').focus()"
    await send_cdp(ws, "Runtime.evaluate", {"expression": js})
    await send_cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "modifiers": 2})
    await send_cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "modifiers": 2})
    for char in value:
        await send_cdp(ws, "Input.dispatchKeyEvent", {"type": "char", "text": char})
    log_success(f"Filled with '{value}'. The form is pleased.")


async def cmd_eval(ws, expression):
    log_dim("executing arbitrary javascript... what could go wrong?")
    result = await send_cdp(ws, "Runtime.evaluate", {
        "expression": expression, "returnByValue": True, "awaitPromise": True,
    })
    value = result.get("result", {}).get("value")
    if value is not None:
        if isinstance(value, (dict, list)):
            print(json.dumps(value, indent=2, ensure_ascii=False))
        else:
            print(value)
    else:
        desc = result.get("result", {}).get("description", "")
        print(desc or "(the void stares back)")


async def cmd_text(ws):
    log_dim(quip(QUIPS_EXTRACT))
    result = await send_cdp(ws, "Runtime.evaluate", {
        "expression": "document.body.innerText", "returnByValue": True,
    })
    text = result.get("result", {}).get("value", "")
    print(text)
    log_success(f"Extracted {len(text):,} characters. That's like {len(text)//250} paragraphs.")


async def cmd_pages(ws_url_unused, pages):
    print(f"\n  {C.BOLD}{C.CYAN}Open Tabs{C.RESET}")
    print(f"  {C.DIM}{'─' * 50}{C.RESET}")
    for i, p in enumerate(pages):
        title = p.get("title", "untitled")[:55]
        url = p.get("url", "")[:70]
        print(f"  {C.ORANGE}{C.BOLD}[{i}]{C.RESET} {C.CYAN}{title}{C.RESET}")
        print(f"      {C.GRAY}{url}{C.RESET}")
    print(f"  {C.DIM}{'─' * 50}{C.RESET}")
    print(f"  {C.GREEN}{len(pages)} tabs open. That's surprisingly reasonable.{C.RESET}\n")


async def cmd_scroll(ws, direction="down", pixels=800):
    log_dim(quip(QUIPS_SCROLL))
    d = int(pixels) if direction == "down" else -int(pixels)
    await send_cdp(ws, "Runtime.evaluate", {"expression": f"window.scrollBy(0, {d})"})
    arrow = "down" if d > 0 else "up"
    log_success(f"Scrolled {arrow} {abs(d)}px. New horizons await.")


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

async def main():
    global _start_time
    _start_time = time.time()

    if len(sys.argv) < 2:
        print(BANNER)
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    # Show banner for interactive commands
    if cmd not in ("eval", "text") and os.environ.get("BP_QUIET") != "1":
        print(f"\n  {C.ORANGE}{C.BOLD}Browser Pilot{C.RESET} {C.DIM}v3{C.RESET}  {C.GRAY}// {cmd}{C.RESET}\n")

    if cmd == "pages":
        _, pages = await get_ws_url()
        real_pages = [p for p in pages if p.get("type") == "page"]
        await cmd_pages(None, real_pages)
        return

    tab_idx = int(os.environ.get("TAB", "0"))

    if cmd == "select":
        tab_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        ws_url, _ = await get_ws_url(tab_idx)
        log_success(f"Switched to tab [{tab_idx}]. New perspective acquired.")
        return

    ws_url, _ = await get_ws_url(tab_idx)

    async with websockets.connect(ws_url, max_size=100*1024*1024) as ws:
        if cmd == "navigate":
            await cmd_navigate(ws, sys.argv[2])
        elif cmd == "dom":
            await cmd_dom(ws)
        elif cmd == "screenshot":
            path = sys.argv[2] if len(sys.argv) > 2 else None
            await cmd_screenshot(ws, path)
        elif cmd == "click":
            await cmd_click(ws, sys.argv[2])
        elif cmd == "click-text":
            await cmd_click_text(ws, sys.argv[2])
        elif cmd == "click-index":
            await cmd_click_index(ws, sys.argv[2])
        elif cmd == "fill":
            await cmd_fill(ws, sys.argv[2], sys.argv[3])
        elif cmd == "eval":
            await cmd_eval(ws, sys.argv[2])
        elif cmd == "text":
            await cmd_text(ws)
        elif cmd == "scroll":
            direction = sys.argv[2] if len(sys.argv) > 2 else "down"
            pixels = sys.argv[3] if len(sys.argv) > 3 else "800"
            await cmd_scroll(ws, direction, pixels)
        elif cmd == "wait":
            secs = float(sys.argv[2]) if len(sys.argv) > 2 else 2
            log_dim(quip(QUIPS_WAIT))
            await asyncio.sleep(secs)
            log_success(f"Waited {secs}s. Time well spent.")
        else:
            log_error(f"Unknown command: {cmd}. I'm good, but not THAT good.")
            print(__doc__)

    # Cleanup highlights
    if cmd in ("click", "click-text", "click-index"):
        try:
            async with websockets.connect(ws_url, max_size=100*1024*1024) as ws2:
                await send_cdp(ws2, "Runtime.evaluate", {"expression": CLEAR_HIGHLIGHTS_JS})
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
