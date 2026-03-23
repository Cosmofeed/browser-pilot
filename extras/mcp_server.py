#!/usr/bin/env python3
"""
Browser Pilot MCP Server — expose pilot.py as an MCP server.
Any MCP-compatible AI tool (Claude Code, Cursor, Windsurf) can use it natively.

Usage:
  python3 extras/mcp_server.py                    # start MCP stdio server

Configure in Claude Code (~/.claude/settings.json):
  "mcpServers": {
    "browser-pilot": {
      "command": "python3",
      "args": ["/path/to/extras/mcp_server.py"]
    }
  }
"""

import asyncio
import json
import sys
import os

# Add parent dir for pilot imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Simple MCP stdio server (no external deps beyond websockets)

TOOLS = [
    {"name": "bp_navigate", "description": "Navigate to a URL", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
    {"name": "bp_dom", "description": "Get compressed DOM with interactive element indices", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bp_text", "description": "Extract all text from the page", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bp_click", "description": "Click element by CSS selector (React/Radix compatible)", "inputSchema": {"type": "object", "properties": {"selector": {"type": "string"}}, "required": ["selector"]}},
    {"name": "bp_click_text", "description": "Click element by visible text content", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "bp_click_heal", "description": "Self-healing click — tries CSS, text, aria-label, title fallbacks", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}}, "required": ["target"]}},
    {"name": "bp_fill", "description": "Fill an input field", "inputSchema": {"type": "object", "properties": {"selector": {"type": "string"}, "value": {"type": "string"}}, "required": ["selector", "value"]}},
    {"name": "bp_screenshot", "description": "Take a screenshot", "inputSchema": {"type": "object", "properties": {"full_page": {"type": "boolean", "default": False}}}},
    {"name": "bp_scroll", "description": "Scroll the page", "inputSchema": {"type": "object", "properties": {"direction": {"type": "string", "enum": ["up", "down"], "default": "down"}, "pixels": {"type": "integer", "default": 800}}}},
    {"name": "bp_table", "description": "Extract tables as JSON", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bp_links", "description": "Extract all links", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bp_forms", "description": "Detect all forms with fields", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bp_meta", "description": "Extract OpenGraph, Twitter Cards, JSON-LD metadata", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bp_prices", "description": "Extract currency amounts from the page", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bp_detect_login", "description": "Check if page requires login", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bp_detect_error", "description": "Detect error pages (404, 500, etc.)", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bp_dismiss_cookies", "description": "Find and dismiss cookie banners", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bp_health", "description": "Comprehensive page health check", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bp_stats", "description": "Page statistics (DOM nodes, links, images, etc.)", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bp_pages", "description": "List open browser tabs", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bp_eval", "description": "Run JavaScript on the page", "inputSchema": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}},
    {"name": "bp_wait_for", "description": "Wait for an element to appear", "inputSchema": {"type": "object", "properties": {"selector": {"type": "string"}, "timeout": {"type": "integer", "default": 10}}, "required": ["selector"]}},
    {"name": "bp_key", "description": "Press keyboard shortcut (ctrl+a, Enter, etc.)", "inputSchema": {"type": "object", "properties": {"combo": {"type": "string"}}, "required": ["combo"]}},
    {"name": "bp_markdown", "description": "Convert page to clean markdown", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bp_pdf", "description": "Export page as PDF", "inputSchema": {"type": "object", "properties": {}}},
]

async def run_pilot_command(cmd_args):
    """Run a pilot.py command and capture output."""
    pilot_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pilot.py")
    env = {**os.environ, "BP_QUIET": "1"}
    proc = await asyncio.create_subprocess_exec(
        sys.executable, pilot_path, *cmd_args,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        env=env
    )
    stdout, stderr = await proc.communicate()
    output = stdout.decode("utf-8", errors="replace")
    # Strip ANSI codes
    import re
    output = re.sub(r'\033\[[0-9;]*m', '', output)
    return output.strip()

async def handle_tool_call(name, arguments):
    """Map MCP tool calls to pilot.py commands."""
    cmd_map = {
        "bp_navigate": lambda a: ["navigate", a["url"]],
        "bp_dom": lambda a: ["dom"],
        "bp_text": lambda a: ["text"],
        "bp_click": lambda a: ["click", a["selector"]],
        "bp_click_text": lambda a: ["click-text", a["text"]],
        "bp_click_heal": lambda a: ["click-heal", a["target"]],
        "bp_fill": lambda a: ["fill", a["selector"], a["value"]],
        "bp_screenshot": lambda a: ["screenshot-full" if a.get("full_page") else "screenshot"],
        "bp_scroll": lambda a: ["scroll", a.get("direction", "down"), str(a.get("pixels", 800))],
        "bp_table": lambda a: ["table"],
        "bp_links": lambda a: ["links"],
        "bp_forms": lambda a: ["forms"],
        "bp_meta": lambda a: ["meta"],
        "bp_prices": lambda a: ["prices"],
        "bp_detect_login": lambda a: ["detect-login"],
        "bp_detect_error": lambda a: ["detect-error"],
        "bp_dismiss_cookies": lambda a: ["dismiss-cookies"],
        "bp_health": lambda a: ["health"],
        "bp_stats": lambda a: ["stats"],
        "bp_pages": lambda a: ["pages"],
        "bp_eval": lambda a: ["eval", a["expression"]],
        "bp_wait_for": lambda a: ["wait-for", a["selector"], str(a.get("timeout", 10))],
        "bp_key": lambda a: ["key", a["combo"]],
        "bp_markdown": lambda a: ["markdown"],
        "bp_pdf": lambda a: ["pdf"],
    }

    builder = cmd_map.get(name)
    if not builder:
        return f"Unknown tool: {name}"

    cmd_args = builder(arguments or {})
    return await run_pilot_command(cmd_args)

async def main():
    """MCP stdio server main loop."""
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    async def write(data):
        msg = json.dumps(data)
        sys.stdout.write(f"Content-Length: {len(msg)}\r\n\r\n{msg}")
        sys.stdout.flush()

    # Read MCP messages
    while True:
        # Read headers
        headers = {}
        while True:
            line = (await reader.readline()).decode().strip()
            if not line:
                break
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        content_length = int(headers.get("content-length", 0))
        if content_length == 0:
            continue

        body = await reader.readexactly(content_length)
        msg = json.loads(body)

        method = msg.get("method", "")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        if method == "initialize":
            await write({"jsonrpc": "2.0", "id": msg_id, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "browser-pilot", "version": "4.2"}
            }})
        elif method == "notifications/initialized":
            pass  # No response needed
        elif method == "tools/list":
            await write({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            try:
                result = await handle_tool_call(tool_name, tool_args)
                await write({"jsonrpc": "2.0", "id": msg_id, "result": {
                    "content": [{"type": "text", "text": result}]
                }})
            except Exception as e:
                await write({"jsonrpc": "2.0", "id": msg_id, "result": {
                    "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                    "isError": True
                }})
        elif msg_id:
            await write({"jsonrpc": "2.0", "id": msg_id, "result": {}})

if __name__ == "__main__":
    asyncio.run(main())
