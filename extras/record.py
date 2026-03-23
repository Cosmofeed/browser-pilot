#!/usr/bin/env python3
"""
Browser Pilot — Action Recorder (Codegen)
Records user browser interactions and generates pilot.py commands.

Usage:
  python3 extras/record.py start    # start recording
  python3 extras/record.py stop     # stop and print commands

Inject a listener into the page that captures clicks, inputs, navigations,
and scrolls, then outputs equivalent pilot.py commands.
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CDP_URL = os.environ.get("CDP_URL", "http://localhost:9222")

RECORDER_JS = """
(() => {
  if (window.__bpRecording) {
    // Stop recording, return commands
    window.__bpRecording = false;
    const cmds = window.__bpRecordedCommands || [];
    window.__bpRecordedCommands = [];
    return {status: 'stopped', commands: cmds};
  }

  // Start recording
  window.__bpRecording = true;
  window.__bpRecordedCommands = [];
  const cmds = window.__bpRecordedCommands;

  // Record initial URL
  cmds.push('navigate ' + location.href);

  // Click handler
  document.addEventListener('click', function(e) {
    if (!window.__bpRecording) return;
    const el = e.target;
    // Build best selector
    let sel = '';
    if (el.id) sel = '#' + el.id;
    else if (el.getAttribute('aria-label')) sel = '[aria-label="' + el.getAttribute('aria-label') + '"]';
    else {
      const text = el.innerText?.trim().substring(0, 30);
      if (text) {
        cmds.push('click-text ' + text);
        return;
      }
      sel = el.tagName.toLowerCase();
    }
    cmds.push('click ' + sel);
  }, true);

  // Input handler
  document.addEventListener('input', function(e) {
    if (!window.__bpRecording) return;
    const el = e.target;
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
      let sel = '';
      if (el.id) sel = '#' + el.id;
      else if (el.name) sel = '[name="' + el.name + '"]';
      else if (el.placeholder) sel = '[placeholder="' + el.placeholder + '"]';
      else sel = el.tagName.toLowerCase() + '[type="' + (el.type || 'text') + '"]';
      // Debounce — replace last fill for same selector
      const last = cmds[cmds.length - 1];
      if (last && last.startsWith('fill ' + sel)) cmds.pop();
      cmds.push('fill ' + sel + ' ' + el.value);
    }
  }, true);

  // Scroll handler (debounced)
  let scrollTimer;
  document.addEventListener('scroll', function() {
    if (!window.__bpRecording) return;
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(() => {
      cmds.push('scroll down 500');
    }, 500);
  }, true);

  // Navigation handler
  const origPush = history.pushState;
  history.pushState = function() {
    origPush.apply(this, arguments);
    if (window.__bpRecording) {
      cmds.push('navigate ' + location.href);
    }
  };

  // Select handler
  document.addEventListener('change', function(e) {
    if (!window.__bpRecording) return;
    const el = e.target;
    if (el.tagName === 'SELECT') {
      let sel = '';
      if (el.id) sel = '#' + el.id;
      else if (el.name) sel = '[name="' + el.name + '"]';
      cmds.push('select-option ' + sel + ' ' + el.value);
    }
  }, true);

  // Visual indicator
  const badge = document.createElement('div');
  badge.id = 'bp-rec-badge';
  badge.style.cssText = 'position:fixed;top:16px;right:16px;background:#ff0000;color:white;padding:6px 14px;border-radius:20px;font:700 13px system-ui;z-index:999999;box-shadow:0 2px 12px rgba(255,0,0,0.4);animation:bp-rec-blink 1s ease-in-out infinite';
  badge.textContent = '● REC';
  if (!document.querySelector('#bp-rec-style')) {
    const s = document.createElement('style');
    s.id = 'bp-rec-style';
    s.textContent = '@keyframes bp-rec-blink{0%,100%{opacity:1}50%{opacity:0.5}}';
    document.head.appendChild(s);
  }
  document.body.appendChild(badge);

  return {status: 'recording', message: 'Recording started. Interact with the page, then run stop.'};
})()
"""

STOP_JS = """
(() => {
  window.__bpRecording = false;
  const badge = document.getElementById('bp-rec-badge');
  if (badge) badge.remove();
  const cmds = window.__bpRecordedCommands || [];
  window.__bpRecordedCommands = [];
  return {status: 'stopped', commands: cmds, count: cmds.length};
})()
"""

async def main():
    import urllib.request
    import websockets

    action = sys.argv[1] if len(sys.argv) > 1 else "start"

    resp = urllib.request.urlopen(f"{CDP_URL}/json/list")
    pages = [p for p in json.loads(resp.read()) if p.get("type") == "page"]
    if not pages:
        print("No Chrome pages found"); return

    tab = int(os.environ.get("TAB", "0"))
    ws_url = pages[tab]["webSocketDebuggerUrl"]

    msg_id = 0
    async with websockets.connect(ws_url, max_size=100*1024*1024) as ws:
        async def send(method, params=None):
            nonlocal msg_id; msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=15)
                d = json.loads(raw)
                if d.get("id") == msg_id:
                    return d.get("result", {})

        if action == "start":
            r = await send("Runtime.evaluate", {"expression": RECORDER_JS, "returnByValue": True, "awaitPromise": True})
            val = r.get("result", {}).get("value", {})
            print(f"\n  🔴 Recording started!")
            print(f"  Interact with the page. When done, run:")
            print(f"  python3 extras/record.py stop\n")

        elif action == "stop":
            r = await send("Runtime.evaluate", {"expression": STOP_JS, "returnByValue": True, "awaitPromise": True})
            val = r.get("result", {}).get("value", {})
            commands = val.get("commands", [])

            print(f"\n  ✅ Recording stopped. {len(commands)} actions captured.\n")
            print("  # Generated pilot.py commands:")
            print("  # Save to a .txt file and run with: pilot.py batch commands.txt")
            print("  " + "─" * 50)
            for cmd in commands:
                print(f"  {cmd}")
            print("  " + "─" * 50)

            # Save to file
            out_path = os.environ.get("BP_RECORD_FILE", "/tmp/bp-recorded-commands.txt")
            with open(out_path, "w") as f:
                f.write("# Recorded by Browser Pilot\n")
                for cmd in commands:
                    f.write(cmd + "\n")
            print(f"\n  Saved to {out_path}")

        else:
            print("Usage: record.py [start|stop]")

if __name__ == "__main__":
    asyncio.run(main())
