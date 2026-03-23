#!/usr/bin/env python3
"""
Browser Pilot — Parallel Execution
Run the same command across multiple tabs simultaneously.

Usage:
  python3 extras/parallel.py text              # extract text from ALL tabs
  python3 extras/parallel.py screenshot        # screenshot ALL tabs
  python3 extras/parallel.py dom               # DOM of ALL tabs
  python3 extras/parallel.py eval "expression" # eval on ALL tabs

Results are saved to /tmp/browser-pilot-state/parallel/
"""

import asyncio
import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CDP_URL = os.environ.get("CDP_URL", "http://localhost:9222")
STATE_DIR = os.environ.get("BP_STATE", "/tmp/browser-pilot-state")

async def run_on_tab(tab_idx, cmd_args):
    """Run a pilot.py command on a specific tab."""
    import subprocess
    pilot_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pilot.py")
    env = {**os.environ, "TAB": str(tab_idx), "BP_QUIET": "1"}
    proc = await asyncio.create_subprocess_exec(
        sys.executable, pilot_path, *cmd_args,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        env=env
    )
    stdout, stderr = await proc.communicate()
    import re
    output = re.sub(r'\033\[[0-9;]*m', '', stdout.decode("utf-8", errors="replace")).strip()
    return tab_idx, output, proc.returncode

async def main():
    import urllib.request

    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1:]

    # Get all page tabs
    resp = urllib.request.urlopen(f"{CDP_URL}/json/list")
    pages = [p for p in json.loads(resp.read()) if p.get("type") == "page"]

    print(f"\n  ⚡ Parallel execution: '{' '.join(cmd)}' across {len(pages)} tabs")
    print(f"  {'─' * 50}")

    start = time.time()

    # Run on all tabs in parallel
    tasks = [run_on_tab(i, cmd) for i in range(len(pages))]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    elapsed = time.time() - start

    # Save results
    out_dir = f"{STATE_DIR}/parallel"
    os.makedirs(out_dir, exist_ok=True)

    for result in results:
        if isinstance(result, Exception):
            print(f"  ❌ Error: {result}")
            continue
        tab_idx, output, code = result
        title = pages[tab_idx].get("title", "untitled")[:40]
        url = pages[tab_idx].get("url", "")[:60]

        status = "✅" if code == 0 else "❌"
        print(f"  {status} [{tab_idx}] {title}")
        print(f"       {url}")
        if output:
            lines = output.split("\n")
            print(f"       → {lines[0][:80]}")
            if len(lines) > 1:
                print(f"       ... ({len(lines)-1} more lines)")

        # Save output
        with open(f"{out_dir}/tab-{tab_idx}.txt", "w") as f:
            f.write(f"# Tab {tab_idx}: {title}\n# URL: {url}\n\n{output}")

    print(f"  {'─' * 50}")
    print(f"  Done in {elapsed:.1f}s. Results saved to {out_dir}/\n")

if __name__ == "__main__":
    asyncio.run(main())
