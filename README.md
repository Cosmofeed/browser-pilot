# Browser Pilot

**Your browser. Your rules. No external LLM. Zero cost. 50 features.**

A lightweight browser automation tool built for AI coding assistants. While tools like [browser-use](https://github.com/browser-use/browser-use) need a separate LLM API key to decide what to click, Browser Pilot doesn't — because the AI assistant you're already talking to IS the brain.

**8-15x faster than browser-use. $0 per scrape. Single file. One dependency.**

```
  ____                                   ____  _ _       _
 | __ ) _ __ _____      _____  ___ _ __|  _ \(_) | ___ | |_
 |  _ \| '__/ _ \ \ /\ / / __|/ _ \ '__| |_) | | |/ _ \| __|
 | |_) | | | (_) \ V  V /\__ \  __/ |  |  __/| | | (_) | |_
 |____/|_|  \___/ \_/\_/ |___/\___|_|  |_|   |_|_|\___/ \__|
                                                v4 — 50 features
```

## Quick Start

```bash
pip install websockets

# Launch Chrome with CDP (keeps your sessions)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome-Pilot"

# Go
python3 pilot.py navigate "https://example.com"
python3 pilot.py dom
python3 pilot.py click-text "Submit"
python3 pilot.py text
```

## All 50 Features

### Core (1-10)
| # | Command | Description |
|---|---------|-------------|
| 1 | `wait-for SEL [timeout]` | Wait for element to appear in DOM |
| 2 | `click-retry SEL [N]` | Click with auto-retry (scroll, wait, retry N times) |
| 3 | `shadow` | Shadow DOM piercing (auto-included in `dom` output) |
| 4 | `iframe SEL CMD` | Execute commands inside iframes |
| 5 | — | File download interception (via network capture) |
| 6 | `cookies export\|import [path]` | Export/import cookies as JSON |
| 7 | `network start\|stop\|dump` | Network request monitoring |
| 8 | (with #7) | Capture API responses from network |
| 9 | `TAB=N pilot.py cmd` | Multi-tab: run any command on any tab |
| 10 | — | Persistent WebSocket (single connection per command) |

### DOM Engine (11-20)
| # | Command | Description |
|---|---------|-------------|
| 11 | (in `dom`) | Shadow DOM walking — auto-enters shadowRoot |
| 12 | `landmarks` | Page landmarks (header, nav, main, footer, etc.) |
| 13 | `forms` | Auto-detect all forms with field details |
| 14 | `table` | Extract tables as structured JSON |
| 15 | `links` | All links with text, href, internal/external flag |
| 16 | `images` | All images with src, alt, dimensions |
| 17 | `dom-diff` | Diff between last two `dom` snapshots |
| 18 | `scroll-infinite [max]` | Keep scrolling until no new content |
| 19 | `lazy-load` | Scroll to bottom and back to trigger lazy content |
| 20 | `a11y` | Full accessibility tree from CDP |

### Visual (21-30)
| # | Command | Description |
|---|---------|-------------|
| 21 | `screenshot-full [path]` | Full-page screenshot (stitched) |
| 22 | `screenshot-el SEL [path]` | Element-only screenshot |
| 23 | `diff URL1 URL2` | Visual diff — screenshot two URLs, compare |
| 24 | `record start\|stop` | Screen recording via CDP screencast |
| 25 | `highlight-all` | Highlight ALL interactive elements with numbered badges |
| 26 | (in highlight) | Color themes — orange, green, purple for different actions |
| 27 | — | Progress indicator (shown via log timestamps) |
| 28 | (auto) | Dark-mode-aware highlights |
| 29 | `annotate SEL TEXT` | Add text label/annotation on the page |
| 30 | (with #23) | Before/after screenshots saved for comparison |

### Input & Interaction (31-40)
| # | Command | Description |
|---|---------|-------------|
| 31 | `drag SEL DX DY` | Drag element by pixel offset |
| 32 | `hover SEL` | Hover with tooltip extraction |
| 33 | `key COMBO` | Keyboard shortcut (ctrl+a, Enter, Escape, etc.) |
| 34 | `upload SEL PATH` | Upload file to file input |
| 35 | `select-option SEL VAL` | Select native `<select>` dropdown option |
| 36 | `type-human SEL TEXT` | Typewriter mode — random 30-150ms per char |
| 37 | `right-click SEL` | Right-click to trigger context menus |
| 38 | `scroll-to SEL` | Smart scroll element into view |
| 39 | `emulate DEVICE` | Device emulation (iphone, ipad, pixel, desktop) |
| 40 | `geo LAT LNG` | Spoof geolocation |

### Intelligence (41-50)
| # | Command | Description |
|---|---------|-------------|
| 41 | `detect-login` | Detect if page requires login |
| 42 | `dismiss-cookies` | Auto-find and dismiss cookie banners |
| 43 | `detect-captcha` | Detect CAPTCHAs (reCAPTCHA, hCaptcha, Turnstile) |
| 44 | `spa-wait [timeout]` | Smart SPA load detection (DOM stability check) |
| 45 | `detect-error` | Detect 404, 403, 500, timeout, blocked pages |
| 46 | `detect-lang` | Detect page language |
| 47 | `prices` | Extract all currency amounts ($, EUR, GBP, INR, etc.) |
| 48 | `dates` | Extract all date strings |
| 49 | `meta` | Structured data: OpenGraph, Twitter Cards, JSON-LD, canonical |
| 50 | `monitor URL` | Change monitor — detect what changed since last visit |

## Why Not browser-use?

| | Browser Pilot | browser-use |
|---|---|---|
| **LLM** | Your AI assistant — $0 | External API ($0.02/scrape) |
| **Speed** | 6.7s avg | 56.5s avg (8.4x slower) |
| **React dropdowns** | 12.4s | 148.8s (12x slower) |
| **Features** | 50 | ~15 |
| **Dependencies** | 1 (`websockets`) | 30+ |
| **File size** | Single file, ~800 lines | Full Python package |
| **Highlights** | Pulsing gradient badges | Basic orange borders |
| **Personality** | Witty quips | Log messages |

*Benchmarked on 15 real-world pages including GCP Console, AWS MSK, MongoDB Atlas, Vercel, GitHub, Twitter/X, Hacker News, Wikipedia, and more.*

## How It Works

```
Your AI Assistant (Claude, GPT, Cursor, etc.)
    |  decides what to do
    v
pilot.py (this tool)
    |  WebSocket (CDP)
    v
Your actual Chrome browser
    (with your cookies, sessions, logins)
```

No middleman LLM. Your AI reads `dom` output, decides the next action, tells pilot.py. Fast, free, accurate.

## React/Radix Click Compatibility

Many modern UIs don't respond to raw mouse events. Browser Pilot dispatches the full event chain:

```
PointerEvent('pointerdown') -> MouseEvent('mousedown') ->
PointerEvent('pointerup') -> MouseEvent('mouseup') ->
MouseEvent('click')
```

Works with Radix UI, Headless UI, Material UI, Chakra, shadcn, and any React SPA.

## Visual Highlights

When clicking, Browser Pilot injects beautiful visual feedback:
- Pulsing border with box-shadow glow
- Gradient badge with action label (CLICK, FILL, HOVER, TARGET)
- Color-coded: orange (click), green (fill), purple (hover)
- `highlight-all` numbers every interactive element on the page

## Using with AI Coding Assistants

### Claude Code
```bash
mkdir -p ~/.claude/skills/browser-pilot
cp pilot.py ~/.claude/skills/browser-pilot/
# Then: "use browser-pilot to check the billing dashboard"
```

### Cursor / Other
Just run pilot.py commands in terminal. Your AI reads the output.

### Scripts
```python
import subprocess
result = subprocess.run(["python3", "pilot.py", "text"], capture_output=True, text=True)
page_content = result.stdout
```

## Security

- Port 9222 binds to `127.0.0.1` only
- No data leaves your machine
- No external API calls
- No telemetry
- All cookies/sessions stay local

## Requirements

- Python 3.8+
- `websockets` pip package
- Chrome/Chromium
- That's it

## License

MIT — Cosmofeed Technologies Private Limited
