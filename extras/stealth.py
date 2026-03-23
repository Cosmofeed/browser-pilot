#!/usr/bin/env python3
"""
Browser Pilot — Stealth Mode
Apply anti-detection measures to avoid bot detection.

Usage:
  python3 extras/stealth.py apply     # apply stealth patches
  python3 extras/stealth.py check     # check if detectable

Patches:
- Removes navigator.webdriver flag
- Randomizes user agent
- Hides Chrome automation flags
- Overrides navigator.plugins
- Fixes window.chrome
"""

import asyncio
import json
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CDP_URL = os.environ.get("CDP_URL", "http://localhost:9222")

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

STEALTH_JS = """
(() => {
  // 1. Remove webdriver flag
  Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

  // 2. Fix chrome object
  if (!window.chrome) {
    window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){} };
  }

  // 3. Override permissions query
  const origQuery = window.navigator.permissions?.query;
  if (origQuery) {
    window.navigator.permissions.query = (params) => {
      if (params.name === 'notifications') {
        return Promise.resolve({ state: Notification.permission });
      }
      return origQuery(params);
    };
  }

  // 4. Fix plugins (empty in headless)
  Object.defineProperty(navigator, 'plugins', {
    get: () => [
      { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
      { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
      { name: 'Native Client', filename: 'internal-nacl-plugin' },
    ]
  });

  // 5. Fix languages
  Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
  });

  // 6. Fix platform
  Object.defineProperty(navigator, 'platform', {
    get: () => 'MacIntel'
  });

  // 7. Canvas fingerprint randomization
  const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
  HTMLCanvasElement.prototype.toDataURL = function(type) {
    const ctx = this.getContext('2d');
    if (ctx) {
      ctx.fillStyle = 'rgba(0,0,0,0.001)';
      ctx.fillRect(0, 0, 1, 1);
    }
    return origToDataURL.apply(this, arguments);
  };

  return 'Stealth patches applied';
})()
"""

CHECK_JS = """
(() => {
  const checks = [];
  checks.push({name: 'webdriver', detected: !!navigator.webdriver, value: String(navigator.webdriver)});
  checks.push({name: 'chrome', detected: !window.chrome, value: String(!!window.chrome)});
  checks.push({name: 'plugins', detected: navigator.plugins.length === 0, value: String(navigator.plugins.length)});
  checks.push({name: 'languages', detected: !navigator.languages?.length, value: JSON.stringify(navigator.languages)});
  checks.push({name: 'platform', detected: !navigator.platform, value: navigator.platform});

  const detectable = checks.filter(c => c.detected);
  return {
    stealth: detectable.length === 0,
    checks: checks,
    detectable_count: detectable.length,
    user_agent: navigator.userAgent
  };
})()
"""

async def main():
    import urllib.request, websockets

    action = sys.argv[1] if len(sys.argv) > 1 else "apply"
    resp = urllib.request.urlopen(f"{CDP_URL}/json/list")
    pages = [p for p in json.loads(resp.read()) if p.get("type") == "page"]
    if not pages: print("No pages"); return

    tab = int(os.environ.get("TAB", "0"))
    msg_id = 0

    async with websockets.connect(pages[tab]["webSocketDebuggerUrl"], max_size=100*1024*1024) as ws:
        async def send(method, params=None):
            nonlocal msg_id; msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=15)
                d = json.loads(raw)
                if d.get("id") == msg_id: return d.get("result", {})

        if action == "apply":
            # Set random user agent
            ua = random.choice(USER_AGENTS)
            await send("Emulation.setUserAgentOverride", {"userAgent": ua})
            # Apply JS patches
            r = await send("Runtime.evaluate", {"expression": STEALTH_JS, "returnByValue": True})
            # Set as init script for future navigations
            await send("Page.addScriptToEvaluateOnNewDocument", {"source": STEALTH_JS})
            print(f"  ✅ Stealth mode active")
            print(f"  UA: {ua[:60]}...")
            print(f"  Patches: webdriver, chrome, plugins, languages, platform, canvas")

        elif action == "check":
            r = await send("Runtime.evaluate", {"expression": CHECK_JS, "returnByValue": True})
            val = r.get("result", {}).get("value", {})
            if val.get("stealth"):
                print("  ✅ Undetectable. All checks passed.")
            else:
                print(f"  ⚠️  {val.get('detectable_count', '?')} detection signals found:")
                for c in val.get("checks", []):
                    status = "❌" if c["detected"] else "✅"
                    print(f"    {status} {c['name']}: {c['value']}")

if __name__ == "__main__":
    asyncio.run(main())
