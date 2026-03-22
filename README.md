# Browser Pilot

**Your browser. Your rules. No external LLM. Zero cost.**

A lightweight browser automation tool built for AI coding assistants. While tools like [browser-use](https://github.com/browser-use/browser-use) need a separate LLM API key to decide what to click, Browser Pilot doesn't — because the AI assistant you're already talking to IS the brain.

**8-15x faster than browser-use. $0 per scrape. Single file. One dependency.**

```
  ____                                   ____  _ _       _
 | __ ) _ __ _____      _____  ___ _ __|  _ \(_) | ___ | |_
 |  _ \| '__/ _ \ \ /\ / / __|/ _ \ '__| |_) | | |/ _ \| __|
 | |_) | | | (_) \ V  V /\__ \  __/ |  |  __/| | | (_) | |_
 |____/|_|  \___/ \_/\_/ |___/\___|_|  |_|   |_|_|\___/ \__|
```

## Why Browser Pilot?

| | browser-use | Browser Pilot |
|---|---|---|
| **LLM** | External API (OpenAI/Anthropic) | Your AI assistant — $0 |
| **Speed** | ~40s per page (LLM roundtrips) | ~6s per page (direct CDP) |
| **API keys** | Required | None |
| **Install** | pip install + Python deps | Single file + `websockets` |
| **React/Radix** | Works (Playwright) | Works (PointerEvent dispatch) |
| **Highlights** | Orange borders | Pulsing gradient borders with badges |
| **Personality** | Logs | Witty quips throughout |

*Benchmarked on 15 real-world pages: GCP Console, AWS MSK, MongoDB Atlas, Vercel, GitHub, Hacker News, Twitter/X, Product Hunt, Wikipedia, and more.*

## Quick Start

### 1. Install

```bash
pip install websockets
```

That's it. One dependency.

### 2. Launch Chrome with CDP

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome-Pilot"

# Linux
google-chrome --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.config/google-chrome-pilot"
```

This opens Chrome with all your cookies and sessions intact, plus a debug port that only `localhost` can access.

### 3. Use it

```bash
# Navigate
python3 pilot.py navigate "https://news.ycombinator.com"

# See the page (compressed DOM)
python3 pilot.py dom

# Extract all text
python3 pilot.py text

# Click by visible text (React/Radix compatible)
python3 pilot.py click-text "Billing"

# Click by CSS selector
python3 pilot.py click "#submit-button"

# Click by DOM index (from `dom` output)
python3 pilot.py click-index 5

# Fill a form field
python3 pilot.py fill "#email" "hello@example.com"

# Take a screenshot
python3 pilot.py screenshot

# Run JavaScript
python3 pilot.py eval "document.title"

# List open tabs
python3 pilot.py pages

# Scroll
python3 pilot.py scroll down 800

# Wait
python3 pilot.py wait 3
```

## How It Works

```
Your AI Assistant (Claude, GPT, etc.)
    ↓ decides what to do
    ↓
pilot.py (this tool)
    ↓ WebSocket connection
    ↓
Chrome DevTools Protocol (CDP)
    ↓
Your actual Chrome browser
    (with your cookies, sessions, logins)
```

No middleman LLM. Your AI assistant reads the DOM output, decides the next action, and tells pilot.py what to do. The AI is already smart — it doesn't need a second AI to click buttons.

## Features

### DOM Compression Engine

The `dom` command doesn't just dump raw HTML. It walks the DOM tree and produces a compressed, indexed representation:

```
Page: Hacker News
URL: https://news.ycombinator.com/
──────────────────────────────────
[1] a "new" href=/newest
[2] a "past" href=/front
[3] a "comments" href=/newcomments
    h1: "The Future of Version Control"
    span: "221 points"
table(30 rows):
  1. | The Future of Version Control | 221 points | 128 comments
  2. | Flash-MoE: Running a 397B Model on a Laptop | 237 points
──────────────────────────────────
3 interactive elements
```

Interactive elements get indices. Text gets context. Tables get structured. Your AI reads this and knows exactly what to click.

### React/Radix Compatible Clicks

Many modern UIs (Radix, Headless UI, Material) don't respond to raw mouse events. Browser Pilot dispatches the full event chain that React expects:

```
PointerEvent('pointerdown') → MouseEvent('mousedown') →
PointerEvent('pointerup') → MouseEvent('mouseup') →
MouseEvent('click')
```

Dropdowns open. Menus expand. Tabs switch. Just works.

### Beautiful Highlights

When clicking an element, Browser Pilot injects a visual highlight into the page:

- Pulsing border with box-shadow glow
- Gradient badge showing the action ("CLICK", "FILL", "TARGET")
- Smooth animation
- Auto-removes after 3 seconds

You can see exactly what the AI is about to interact with.

### Witty Personality

```
  0.0s  charting a course...
  2.9s  Landed on https://news.ycombinator.com

  0.0s  tactical click deployed...
  0.8s  Clicked 'Submit' at (450, 320)

  0.0s  speed reading at 1,000,000 wpm...
  0.1s  Extracted 4,270 characters. That's like 17 paragraphs.
```

Because automation doesn't have to be boring.

## Using with AI Coding Assistants

### Claude Code

Add as a skill:

```bash
# Copy to skills directory
mkdir -p ~/.claude/skills/browser-pilot
cp pilot.py ~/.claude/skills/browser-pilot/
```

Then tell Claude: "use browser-pilot to check the billing dashboard"

### Cursor / Other AI Editors

Just run pilot.py commands in the terminal. Your AI assistant reads the output and decides next steps.

### Headless / Scripts

```python
import subprocess

# Navigate
subprocess.run(["python3", "pilot.py", "navigate", "https://example.com"])

# Get page text
result = subprocess.run(["python3", "pilot.py", "text"], capture_output=True, text=True)
page_content = result.stdout
```

## Tab Management

```bash
# List all open tabs
python3 pilot.py pages

# Use a specific tab (by index)
TAB=3 python3 pilot.py dom

# Navigate in a specific tab
TAB=2 python3 pilot.py navigate "https://example.com"
```

## Security

- Port 9222 binds to `127.0.0.1` only — not accessible from network
- No data leaves your machine
- No external API calls
- No telemetry
- Your Chrome sessions and cookies stay local
- The `--user-data-dir` flag creates an isolated profile (or you can point it to your real one)

## Requirements

- Python 3.8+
- `websockets` pip package
- Chrome/Chromium browser
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
| Billing dashboard | 6.1s | 69.8s | 11.4x |
| Radix dropdown (Imply) | 12.4s | 148.8s | 12.0x |
| **Average** | **6.7s** | **56.5s** | **8.4x** |

## How It Compares

**browser-use** is an excellent autonomous agent framework — it decides what to do, handles errors, and works independently. Browser Pilot is different: it's a **tool** that your AI assistant drives. The intelligence is in your conversation, not in a separate API call.

Think of it this way:
- **browser-use** = self-driving car (needs its own brain)
- **Browser Pilot** = manual car driven by a very smart driver (your AI assistant)

Both get you there. One is 8x faster and free.

## License

MIT
