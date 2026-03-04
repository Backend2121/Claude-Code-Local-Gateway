"""
client.py — CLI client for the Python remote shell server

Usage:
    python client.py "dir"                        # single command
    python client.py                              # interactive REPL
    python client.py --url http://host:8080 "pwd"
    python client.py --claude "What does the auth module do?"
    python client.py --claude "Explain server.py" --output result.json

Configuration (via .env or environment variables):
    SERVER_URL=http://localhost:8080   (default server address)
    API_KEY=                           (set if server requires auth)
"""

import argparse
import json
import os
import subprocess
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_URL = os.getenv("SERVER_URL", "http://localhost:8080")
API_KEY     = os.getenv("API_KEY", "").strip()

# ── API call ──────────────────────────────────────────────────────────────────

def execute(command: str, base_url: str) -> tuple[int, dict]:
    url = f"{base_url.rstrip('/')}/execute"
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY

    try:
        resp = requests.post(url, json={"command": command}, headers=headers, timeout=120)
        return resp.status_code, resp.json()
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to {url}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out.", file=sys.stderr)
        sys.exit(1)
    except ValueError:
        print("ERROR: Server returned non-JSON response.", file=sys.stderr)
        sys.exit(1)

# ── Output formatting ─────────────────────────────────────────────────────────

def print_result(status: int, data: dict) -> None:
    if data.get("success"):
        stdout = data.get("stdout", "")
        stderr = data.get("stderr", "")
        if stdout:
            print(stdout, end="")
        if stderr:
            print(stderr, end="", file=sys.stderr)
    else:
        error   = data.get("error", "error")
        message = data.get("message", "unknown error")
        print(f"[{status}] {error}: {message}", file=sys.stderr)


def exit_code_of(data: dict) -> int:
    return data.get("exitCode", 0) if data.get("success") else 1

# ── Claude execution ───────────────────────────────────────────────────────────

CLAUDE_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt":      {"type": "string"},
        "response":    {"type": "string"},
        "tokens_used": {"type": "integer"},
    },
    "required": ["prompt", "response", "tokens_used"],
}


def run_claude(prompt: str, output_file: str, style: str, constraint: str) -> None:
    """Run `claude -p <prompt> --output-format json --json-schema <schema>` and save output."""
    cmd = [
        "claude", "-p", prompt,
        "--system-prompt-file", "./prompts/X_Viral.txt",
        "--output-format", "json",
        "--json-schema", json.dumps(CLAUDE_SCHEMA, separators=(",", ":")),
        "--append-system-prompt", style,
        "--append-system-prompt", constraint,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        print("ERROR: 'claude' CLI not found. Make sure Claude Code is installed and on PATH.", file=sys.stderr)
        sys.exit(1)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"raw_output": result.stdout, "stderr": result.stderr}

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Output written to {output_file}")
    if result.returncode != 0:
        sys.exit(result.returncode)

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Remote shell client")
    parser.add_argument("command", nargs="?", help="Command to run (omit for interactive REPL)")
    parser.add_argument("--url", default=DEFAULT_URL, metavar="URL",
                        help=f"Server URL (default: {DEFAULT_URL})")
    parser.add_argument("--claude", metavar="PROMPT",
                        help="Run 'claude -p PROMPT' and save output to a JSON file")
    parser.add_argument("--output", default="output.json", metavar="FILE",
                        help="JSON output file for --claude mode (default: output.json)")
    parser.add_argument("--style", default="Style: Excited", metavar="PROMPT",
                        help="First appended system prompt (default: 'Style: Excited')")
    parser.add_argument("--constraint", default="DO NOT EXCEED 30 CHARACTERS", metavar="PROMPT",
                        help="Second appended system prompt (default: 'DO NOT EXCEED 30 CHARACTERS')")
    args = parser.parse_args()

    if args.claude:
        run_claude(args.claude, args.output, args.style, args.constraint)
        return

    if args.command:
        status, data = execute(args.command, args.url)
        print_result(status, data)
        sys.exit(exit_code_of(data))
    else:
        print(f"Remote shell  {args.url}  (Ctrl-C or 'exit' to quit)")
        while True:
            try:
                command = input("$ ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not command:
                continue
            if command in ("exit", "quit"):
                break
            status, data = execute(command, args.url)
            print_result(status, data)


if __name__ == "__main__":
    main()
