/**
 * Browser Pilot — Live Demo Panel
 * Inject into any page to show real-time automation steps.
 *
 * Usage from pilot.py:
 *   pilot.py eval "$(cat extras/demo_panel.js)"
 * Or inject via CDP:
 *   Runtime.evaluate({expression: "..."})
 *
 * Then log messages:
 *   window.__bp_log('action', 'Clicking Submit button')
 *   window.__bp_log('success', 'Form submitted')
 *   window.__bp_log('error', 'Element not found')
 */

(function() {
  if (window.__bpPanelLoaded) return;
  window.__bpPanelLoaded = true;

  const PANEL_ID = 'bp-demo-panel';
  const MAX_MESSAGES = 50;
  const messages = [];

  // Styles
  const style = document.createElement('style');
  style.textContent = `
    #${PANEL_ID} {
      position: fixed;
      bottom: 16px;
      right: 16px;
      width: 380px;
      max-height: 400px;
      background: #1a1a2e;
      border: 1px solid #2a2a4e;
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,102,0,0.1);
      font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
      font-size: 12px;
      z-index: 999999;
      overflow: hidden;
      color: #e0e0e0;
      transition: all 0.3s ease;
    }
    #${PANEL_ID}.bp-collapsed {
      width: 52px;
      height: 52px;
      border-radius: 50%;
      cursor: pointer;
      background: linear-gradient(135deg, #ff6600, #ff8533);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    #${PANEL_ID} .bp-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      background: linear-gradient(135deg, #ff6600, #ff8533);
      color: white;
      font-weight: 700;
      font-size: 13px;
      letter-spacing: 0.5px;
      cursor: pointer;
      user-select: none;
    }
    #${PANEL_ID} .bp-header .bp-logo {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    #${PANEL_ID} .bp-header .bp-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #00ff88;
      animation: bp-dot-pulse 2s ease-in-out infinite;
    }
    @keyframes bp-dot-pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.3; }
    }
    #${PANEL_ID} .bp-body {
      max-height: 320px;
      overflow-y: auto;
      padding: 8px 0;
    }
    #${PANEL_ID} .bp-body::-webkit-scrollbar {
      width: 4px;
    }
    #${PANEL_ID} .bp-body::-webkit-scrollbar-thumb {
      background: #ff6600;
      border-radius: 2px;
    }
    #${PANEL_ID} .bp-msg {
      padding: 6px 14px;
      display: flex;
      align-items: flex-start;
      gap: 8px;
      border-bottom: 1px solid #2a2a3e;
      animation: bp-slide-in 0.3s ease;
    }
    @keyframes bp-slide-in {
      from { opacity: 0; transform: translateX(20px); }
      to { opacity: 1; transform: translateX(0); }
    }
    #${PANEL_ID} .bp-msg .bp-icon { flex-shrink: 0; font-size: 14px; }
    #${PANEL_ID} .bp-msg .bp-text { flex: 1; word-break: break-word; line-height: 1.4; }
    #${PANEL_ID} .bp-msg .bp-time { color: #666; font-size: 10px; flex-shrink: 0; }
    #${PANEL_ID} .bp-msg.bp-action .bp-text { color: #ff8533; }
    #${PANEL_ID} .bp-msg.bp-success .bp-text { color: #00cc88; }
    #${PANEL_ID} .bp-msg.bp-error .bp-text { color: #ff4444; }
    #${PANEL_ID} .bp-msg.bp-info .bp-text { color: #6366f1; }
    #${PANEL_ID} .bp-msg.bp-thought .bp-text { color: #a78bfa; font-style: italic; }
    #${PANEL_ID} .bp-footer {
      padding: 8px 14px;
      background: #151528;
      color: #555;
      font-size: 10px;
      text-align: center;
      border-top: 1px solid #2a2a3e;
    }
  `;
  document.head.appendChild(style);

  // Panel
  const panel = document.createElement('div');
  panel.id = PANEL_ID;
  panel.innerHTML = `
    <div class="bp-header" onclick="document.getElementById('${PANEL_ID}').classList.toggle('bp-collapsed')">
      <div class="bp-logo"><div class="bp-dot"></div> Browser Pilot</div>
      <span style="font-size:10px;opacity:0.7">v4</span>
    </div>
    <div class="bp-body" id="bp-log-body"></div>
    <div class="bp-footer">Your browser. Your rules. Zero LLM.</div>
  `;
  document.body.appendChild(panel);

  const ICONS = {
    action: '▶️', success: '✅', error: '❌', info: 'ℹ️',
    thought: '💭', warning: '⚠️', click: '🖱️', navigate: '🧭',
    extract: '📄', screenshot: '📸', scroll: '📜', type: '⌨️',
  };

  window.__bp_log = function(level, text) {
    const body = document.getElementById('bp-log-body');
    if (!body) return;

    const now = new Date();
    const time = now.toLocaleTimeString('en', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });

    messages.push({ level, text, time });
    if (messages.length > MAX_MESSAGES) messages.shift();

    const msg = document.createElement('div');
    msg.className = `bp-msg bp-${level}`;
    msg.innerHTML = `
      <span class="bp-icon">${ICONS[level] || '•'}</span>
      <span class="bp-text">${text}</span>
      <span class="bp-time">${time}</span>
    `;
    body.appendChild(msg);
    body.scrollTop = body.scrollHeight;

    // Remove old messages from DOM
    while (body.children.length > MAX_MESSAGES) {
      body.removeChild(body.firstChild);
    }
  };

  // Welcome message
  window.__bp_log('info', 'Browser Pilot connected. Watching for actions...');
})();
