#!/usr/bin/env python3
"""
Browser Pilot — REST API Server
Expose all pilot.py commands as HTTP endpoints.

Usage:
  python3 extras/serve.py [port]          # default: 8070

Endpoints:
  POST /api/navigate    {"url": "..."}
  POST /api/dom         {}
  POST /api/text        {}
  POST /api/click       {"selector": "..."}
  POST /api/click-text  {"text": "..."}
  POST /api/fill        {"selector": "...", "value": "..."}
  POST /api/screenshot  {"full": false}
  POST /api/eval        {"expression": "..."}
  GET  /api/pages
  GET  /api/health
  POST /api/run         {"commands": ["navigate https://...", "dom", "text"]}

All POST endpoints accept JSON body. Returns JSON response.
"""

import asyncio
import json
import sys
import os
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PILOT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pilot.py")

def run_pilot(cmd_args):
    """Run pilot.py and return cleaned output."""
    env = {**os.environ, "BP_QUIET": "1"}
    try:
        result = subprocess.run(
            [sys.executable, PILOT_PATH] + cmd_args,
            capture_output=True, text=True, env=env, timeout=30
        )
        output = re.sub(r'\033\[[0-9;]*m', '', result.stdout).strip()
        # Try to parse as JSON
        try:
            return json.loads(output)
        except:
            return output
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out"}
    except Exception as e:
        return {"error": str(e)}

class PilotHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/pages":
            result = run_pilot(["pages"])
            self._respond(200, result)
        elif self.path == "/api/health":
            self._respond(200, {"status": "ok", "version": "4.2", "tool": "browser-pilot"})
        elif self.path == "/":
            self._respond(200, {
                "name": "Browser Pilot API",
                "version": "4.2",
                "endpoints": [
                    "POST /api/navigate", "POST /api/dom", "POST /api/text",
                    "POST /api/click", "POST /api/click-text", "POST /api/fill",
                    "POST /api/screenshot", "POST /api/eval", "POST /api/run",
                    "GET /api/pages", "GET /api/health"
                ]
            })
        else:
            self._respond(404, {"error": "Not found"})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}

        route = self.path.replace("/api/", "")

        cmd_map = {
            "navigate": lambda b: ["navigate", b.get("url", "")],
            "dom": lambda b: ["dom"],
            "text": lambda b: ["text"],
            "click": lambda b: ["click", b.get("selector", "")],
            "click-text": lambda b: ["click-text", b.get("text", "")],
            "click-heal": lambda b: ["click-heal", b.get("target", "")],
            "fill": lambda b: ["fill", b.get("selector", ""), b.get("value", "")],
            "screenshot": lambda b: ["screenshot-full" if b.get("full") else "screenshot"],
            "eval": lambda b: ["eval", b.get("expression", "")],
            "table": lambda b: ["table"],
            "links": lambda b: ["links"],
            "meta": lambda b: ["meta"],
            "prices": lambda b: ["prices"],
            "health": lambda b: ["health"],
            "stats": lambda b: ["stats"],
            "markdown": lambda b: ["markdown"],
            "detect-login": lambda b: ["detect-login"],
            "detect-error": lambda b: ["detect-error"],
        }

        if route == "run":
            # Batch mode — run multiple commands
            commands = body.get("commands", [])
            results = []
            for cmd_str in commands:
                parts = cmd_str.split(None, 1)
                cmd = parts[0]
                cmd_args = [cmd] + (parts[1:] if len(parts) > 1 else [])
                result = run_pilot(cmd_args)
                results.append({"command": cmd_str, "result": result})
            self._respond(200, {"results": results, "count": len(results)})
        elif route in cmd_map:
            cmd_args = cmd_map[route](body)
            result = run_pilot(cmd_args)
            self._respond(200, {"command": route, "result": result})
        else:
            self._respond(404, {"error": f"Unknown endpoint: {route}"})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        print(f"  {args[0]}")

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8070
    server = HTTPServer(("127.0.0.1", port), PilotHandler)
    print(f"""
  Browser Pilot API Server
  ════════════════════════
  Listening on http://127.0.0.1:{port}
  Endpoints: /api/navigate, /api/dom, /api/text, /api/click, ...
  Press Ctrl+C to stop.
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")

if __name__ == "__main__":
    main()
