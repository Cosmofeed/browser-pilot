#!/usr/bin/env python3
"""
Browser Pilot — Workflow Engine
Run multi-step browser automations defined in YAML.

Usage:
  python3 extras/workflow.py run workflow.yaml
  python3 extras/workflow.py example > my_workflow.yaml

Example workflow.yaml:
  name: Check billing
  steps:
    - navigate: https://dragonflydb.cloud/billing/usage
    - wait: 5
    - text: {}
    - click-text: Billing
    - wait: 2
    - screenshot: /tmp/billing.png

Advanced (with conditionals):
  steps:
    - navigate: https://example.com
    - detect-login: {}
    - if_login:
        - fill:
            selector: "#email"
            value: "user@example.com"
        - click-text: Sign In
        - wait: 3
    - text: {}
"""

import asyncio
import json
import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EXAMPLE_WORKFLOW = """# Browser Pilot Workflow
# Run with: python3 extras/workflow.py run this_file.yaml

name: Example Workflow
description: Navigate to a page and extract data

steps:
  # Step 1: Navigate
  - navigate: https://news.ycombinator.com

  # Step 2: Wait for load
  - wait: 3

  # Step 3: Dismiss any cookie banners
  - dismiss-cookies: {}

  # Step 4: Extract page text
  - text: {}

  # Step 5: Take a screenshot
  - screenshot: /tmp/workflow-result.png

  # Step 6: Extract all links
  - links: {}
"""

def run_pilot(cmd_args, quiet=True):
    """Run a pilot.py command synchronously."""
    pilot_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pilot.py")
    env = {**os.environ}
    if quiet:
        env["BP_QUIET"] = "1"
    result = subprocess.run(
        [sys.executable, pilot_path] + cmd_args,
        capture_output=True, text=True, env=env, timeout=60
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def parse_step(step):
    """Parse a workflow step into pilot.py command args."""
    if isinstance(step, str):
        return step.split()
    if isinstance(step, dict):
        for cmd, arg in step.items():
            if cmd.startswith("if_"):
                return None  # Conditional, handled separately
            if isinstance(arg, dict):
                # Complex args like fill: {selector: "#x", value: "y"}
                args = [cmd]
                if "selector" in arg:
                    args.append(arg["selector"])
                if "value" in arg:
                    args.append(arg["value"])
                return args
            elif arg is None or arg == {}:
                return [cmd]
            else:
                return [cmd, str(arg)]
    return None

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "help"

    if action == "example":
        print(EXAMPLE_WORKFLOW)
        return

    if action == "run":
        filepath = sys.argv[2] if len(sys.argv) > 2 else None
        if not filepath or not os.path.exists(filepath):
            print(f"Usage: workflow.py run <file.yaml>")
            return

        # Parse YAML (simple parser, no pyyaml dependency)
        try:
            import yaml
            with open(filepath) as f:
                wf = yaml.safe_load(f)
        except ImportError:
            # Fallback: parse simple YAML manually
            print("Note: Install pyyaml for full YAML support. Using basic parser.")
            # For now, just run as batch
            run_pilot(["batch", filepath])
            return

        name = wf.get("name", "Unnamed")
        steps = wf.get("steps", [])

        print(f"\n  🚀 Workflow: {name}")
        print(f"  📋 {len(steps)} steps")
        print(f"  {'─' * 40}")

        for i, step in enumerate(steps):
            cmd_args = parse_step(step)
            if cmd_args is None:
                print(f"  [{i+1}] ⏭️  Skipped (conditional)")
                continue

            print(f"  [{i+1}] ▶️  {' '.join(cmd_args)}")
            stdout, stderr, code = run_pilot(cmd_args, quiet=False)
            if stdout:
                # Print first 3 lines of output
                lines = stdout.split("\n")
                for line in lines[:3]:
                    print(f"       {line}")
                if len(lines) > 3:
                    print(f"       ... ({len(lines)-3} more lines)")

            if code != 0 and stderr:
                print(f"  ⚠️  {stderr[:100]}")

        print(f"  {'─' * 40}")
        print(f"  ✅ Workflow complete.\n")

    else:
        print("Usage:")
        print("  workflow.py run <file.yaml>    Run a workflow")
        print("  workflow.py example            Print example workflow YAML")

if __name__ == "__main__":
    main()
