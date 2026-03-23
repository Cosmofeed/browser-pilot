# Browser Pilot

**Your browser. Your rules. No external LLM. Zero cost.**

A browser automation toolkit built for AI coding assistants. While tools like [browser-use](https://github.com/browser-use/browser-use) need a separate LLM API key to decide what to click, Browser Pilot doesn't — because the AI assistant you're already talking to IS the brain.

**8-15x faster than browser-use. $0 per scrape. One dependency. 65 commands + 7 extras.**

```
  ____                                   ____  _ _       _
 | __ ) _ __ _____      _____  ___ _ __|  _ \(_) | ___ | |_
 |  _ \| '__/ _ \ \ /\ / / __|/ _ \ '__| |_) | | |/ _ \| __|
 | |_) | | | (_) \ V  V /\__ \  __/ |  |  __/| | | (_) | |_
 |____/|_|  \___/ \_/\_/ |___/\___|_|  |_|   |_|_|\___/ \__|
                                                  v5 — 65+7
```

## Quick Start

```bash
pip install websockets

# Launch Chrome with CDP
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome-Pilot"

# Go
python3 pilot.py navigate "https://example.com"
python3 pilot.py dom
python3 pilot.py click-text "Submit"
python3 pilot.py text
```

## Why Not browser-use?

| | Browser Pilot | browser-use |
|---|---|---|
| **LLM needed** | No — your AI assistant decides | Yes — external API ($0.02/scrape) |
| **Speed** | 6.7s avg | 56.5s avg (8.4x slower) |
| **React dropdowns** | 12.4s | 148.8s (12x slower) |
| **Features** | 65 + 7 extras | ~15 |
| **Dependencies** | 1 (`websockets`) | 30+ |
| **File size** | Single file, 1,548 lines | Full Python package |
| **Highlights** | Pulsing gradient badges | Basic borders |
| **Personality** | Witty quips | Log messages |

*Benchmarked on 15 real pages: GCP Console, AWS MSK, MongoDB Atlas, Vercel, GitHub, Twitter/X, Hacker News, Wikipedia, Product Hunt, and more.*

## All 65 Commands

### Core
```
navigate URL              go to a URL
dom                       compressed DOM with indexed interactive elements
text                      all page text
screenshot [path]         viewport screenshot
screenshot-full [path]    full page screenshot
screenshot-el SEL [path]  element screenshot
pages                     list open tabs
select N                  switch to tab N
wait N                    wait N seconds
wait-for SEL [timeout]    wait for element to appear
spa-wait [timeout]        smart SPA load detection (DOM stability)
```

### Click
```
click SEL                 click by CSS selector (React/Radix compatible)
click-text TEXT           click by visible text
click-index N             click by DOM index (from `dom` output)
click-retry SEL [N]       click with auto-retry + scroll fallback
click-heal TARGET         self-healing click — tries CSS, text, aria-label, title
right-click SEL           right-click context menu
```

### Input
```
fill SEL VALUE            fill input field
type-human SEL TEXT       typewriter mode (30-150ms per keystroke)
select-option SEL VAL     native <select> dropdown
upload SEL PATH           file upload
key COMBO                 keyboard shortcut (ctrl+a, Enter, Escape, etc.)
```

### Scroll
```
scroll [up|down] [px]     scroll by pixels
scroll-to SEL             scroll element into view
scroll-infinite [max]     keep scrolling until no new content
lazy-load                 trigger lazy images/content
```

### Extract
```
eval JS                   run JavaScript
table                     tables as JSON
links                     all links with text, href, internal/external
images                    all images with src, alt, dimensions
forms                     all forms with field details
meta                      OpenGraph, Twitter Cards, JSON-LD, canonical
prices                    extract currency amounts ($, EUR, INR, etc.)
dates                     extract date strings
markdown                  convert page to clean markdown
readable                  clean text from main content area
cookies export|import     cookie management
network start|stop|dump   network request capture
storage                   localStorage + sessionStorage
console                   capture console.log output
```

### Visual
```
highlight SEL [label]     highlight single element
highlight-all             highlight ALL interactive elements with numbered badges
diff URL1 URL2            visual diff — screenshot two pages, compare
annotate SEL TEXT         add text label on the page
record start|stop         screen recording via CDP
```

### Intelligence
```
detect-login              check if page requires login
dismiss-cookies           auto-find and click cookie accept/reject
detect-captcha            detect reCAPTCHA, hCaptcha, Turnstile
detect-error              detect 404, 403, 500, timeout pages
detect-lang               page language detection
health                    comprehensive page health check
perf                      Core Web Vitals (TTFB, FCP, LCP, CLS)
stats                     page stats (DOM nodes, links, images, etc.)
find TEXT                 text search with visual highlighting
monitor URL               change monitor — detect what changed
```

### Advanced
```
hover SEL                 hover with tooltip extraction
drag SEL DX DY            drag element by offset
geo LAT LNG              spoof geolocation
emulate DEVICE            device emulation (iphone, ipad, pixel, desktop)
a11y                      full accessibility tree
landmarks                 page landmarks (nav, main, footer, etc.)
dom-diff                  diff between last two DOM snapshots
pdf [path]                export page as PDF
session save|restore|list full browser state persistence
batch FILE                run commands from file
block TYPE                block resources (images, ads, scripts)
extract TYPE              structured JSON extraction
```

### Multi-Tab
```
TAB=N pilot.py CMD        run any command on a specific tab
pages                     list all tabs
select N                  switch tab
```

## Extras

Seven standalone modules in `extras/` for advanced use cases:

### MCP Server (`extras/mcp_server.py`)
Use browser-pilot natively from Claude Code, Cursor, or any MCP client — no Bash calls.
```json
{
  "mcpServers": {
    "browser-pilot": {
      "command": "python3",
      "args": ["/path/to/extras/mcp_server.py"]
    }
  }
}
```

### Action Recorder (`extras/record.py`)
Record browser interactions, generate pilot.py commands.
```bash
python3 extras/record.py start    # start recording (shows red "REC" badge)
# ...interact with browser...
python3 extras/record.py stop     # prints generated commands
python3 pilot.py batch /tmp/bp-recorded-commands.txt  # replay
```

### Stealth Mode (`extras/stealth.py`)
Anti-bot-detection patches.
```bash
python3 extras/stealth.py apply   # webdriver, UA, plugins, canvas fingerprint
python3 extras/stealth.py check   # verify undetectable
```

### Workflow Engine (`extras/workflow.py`)
YAML-defined multi-step automations.
```bash
python3 extras/workflow.py example > my_flow.yaml
python3 extras/workflow.py run my_flow.yaml
```

### Parallel Execution (`extras/parallel.py`)
Run any command across all tabs simultaneously.
```bash
python3 extras/parallel.py stats        # stats for every tab
python3 extras/parallel.py screenshot   # screenshot every tab
```

### REST API Server (`extras/serve.py`)
HTTP endpoints for all pilot.py commands.
```bash
python3 extras/serve.py 8070
curl -X POST http://localhost:8070/api/navigate -d '{"url":"https://example.com"}'
curl -X POST http://localhost:8070/api/text
```

### Live Demo Panel (`extras/demo_panel.js`)
Floating in-browser panel showing real-time automation steps.
```bash
pilot.py eval "$(cat extras/demo_panel.js)"
```

## How It Works

```
Your AI Assistant (Claude, GPT, Cursor, etc.)
    |  decides what to do
    v
pilot.py
    |  WebSocket (CDP)
    v
Your actual Chrome browser
    (with your cookies, sessions, logins)
```

No middleman LLM. Your AI reads the DOM output, decides the next action, tells pilot.py. The intelligence is in your conversation, not in an API call.

## React/Radix Click Compatibility

Modern UIs (Radix, Headless UI, Material, shadcn) don't respond to raw mouse events. Browser Pilot dispatches the full event chain:

```
PointerEvent('pointerdown') -> MouseEvent('mousedown') ->
PointerEvent('pointerup') -> MouseEvent('mouseup') ->
MouseEvent('click')
```

Dropdowns open. Menus expand. Tabs switch. Just works.

## Visual Highlights

When clicking, Browser Pilot injects visual feedback into the page:
- **Pulsing border** with box-shadow glow
- **Gradient badge** with action label (CLICK, FILL, HOVER, TARGET)
- **Color-coded**: orange (click), green (fill), purple (hover)
- **`highlight-all`** numbers every interactive element on the page
- Auto-removes after 3 seconds

## Using with AI Coding Assistants

### Claude Code (recommended)
```bash
mkdir -p ~/.claude/skills/browser-pilot
cp pilot.py ~/.claude/skills/browser-pilot/
# Then just say: "use browser-pilot to check the billing dashboard"
```

### Claude Code (MCP — native integration)
```bash
# Add to ~/.claude/settings.json:
"mcpServers": {
  "browser-pilot": {
    "command": "python3",
    "args": ["/path/to/extras/mcp_server.py"]
  }
}
```

### Cursor / Other AI editors
Run pilot.py commands in terminal. Your AI reads the output.

### Scripts / Automation
```python
import subprocess
result = subprocess.run(["python3", "pilot.py", "text"], capture_output=True, text=True)
print(result.stdout)
```

### pip install (coming soon)
```bash
pip install browser-pilot
browser-pilot navigate "https://example.com"
```

## Security

- Port 9222 binds to `127.0.0.1` only — not accessible from network
- No data leaves your machine
- No external API calls
- No telemetry
- All cookies/sessions stay local
- `--user-data-dir` creates an isolated profile

## Requirements

- Python 3.8+
- `websockets` pip package
- Chrome/Chromium
- That's it

## Benchmarks

Tested on 15 diverse real-world pages. Same task, same Chrome, same page.

| Page Type | Pilot | browser-use | Speedup |
|---|---|---|---|
| Static (Hacker News) | 5.0s | 31.1s | 6.2x |
| React SPA (GitHub) | 7.1s | 44.5s | 6.3x |
| Dashboard (Vercel) | 6.2s | 38.4s | 6.2x |
| Social (Twitter/X) | 6.1s | 47.0s | 7.8x |
| Heavy SPA (Unsplash) | 6.5s | 99.0s | 15.2x |
| Wiki table (Wikipedia) | 6.3s | 34.5s | 5.4x |
| Billing (DragonflyDB) | 6.1s | 69.8s | 11.4x |
| Radix dropdown (Imply) | 12.4s | 148.8s | 12.0x |
| **Average** | **6.7s** | **56.5s** | **8.4x** |

## License

MIT — Cosmofeed Technologies Private Limited
