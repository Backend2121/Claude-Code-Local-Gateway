"""
server.py — Remote shell command execution server

Usage:
    python server.py                     # uses .env / environment defaults
    python server.py --port 9090
    python server.py --host 0.0.0.0      # listen on all interfaces
    python server.py --shell bash        # force a specific shell

Configuration (via .env or environment variables):
    PORT=8080
    HOST=127.0.0.1
    API_KEY=                 (leave blank to disable auth — NOT recommended)
    FORCE_SHELL=             (e.g. "powershell", "bash", "cmd")
    RESTRICTED_MODE=true     (disables /execute; only /generate-claude works)
    COMMAND_TIMEOUT=30
    MAX_OUTPUT_BYTES=1048576
    MAX_COMMAND_LENGTH=2048
    LOG_FILE=claude_server.log
"""

import argparse
import hmac
import json
import logging
import logging.handlers
import os
import platform
import shlex
import shutil
import subprocess
import sys
import time

# Force UTF-8 on Windows terminals so emoji in Claude responses don't mojibake
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

API_KEY          = os.getenv("API_KEY", "").strip()
COMMAND_TIMEOUT  = int(os.getenv("COMMAND_TIMEOUT", "30"))
MAX_OUTPUT_BYTES = int(os.getenv("MAX_OUTPUT_BYTES", "1048576"))  # 1 MB
MAX_COMMAND_LEN  = int(os.getenv("MAX_COMMAND_LENGTH", "2048"))
HOST             = os.getenv("HOST", "127.0.0.1")
PORT             = int(os.getenv("PORT", "8080"))
FORCE_SHELL      = os.getenv("FORCE_SHELL", "").strip() or None
RESTRICTED_MODE  = os.getenv("RESTRICTED_MODE", "false").lower() == "true"
LOG_FILE         = os.getenv("LOG_FILE", "claude_server.log")

# ── Audit logger ──────────────────────────────────────────────────────────────

_audit = logging.getLogger("audit")
_audit.setLevel(logging.INFO)
_audit_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_audit_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
_audit.addHandler(_audit_handler)

# ── Shell detection ───────────────────────────────────────────────────────────

def _detect_shell() -> list[str]:
    if FORCE_SHELL:
        return [FORCE_SHELL, "-c"]
    if platform.system() == "Windows":
        if shutil.which("powershell"):
            return ["powershell", "-NoProfile", "-Command"]
        return ["cmd", "/c"]
    if shutil.which("bash"):
        return ["bash", "-c"]
    return ["sh", "-c"]


SHELL_CMD = _detect_shell()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_shell_argv(shell_cmd: list[str], command: str) -> list[str]:
    """Build the argv list to run `command` via the configured shell.
    On Windows, bypasses the shell entirely by parsing the command with shlex
    and passing arguments directly to the process — avoids PowerShell 5.1's
    broken argument quoting for native executables.
    On other platforms, delegates to bash/sh as normal.
    """
    if platform.system() == "Windows" and not FORCE_SHELL:
        return shlex.split(command, posix=True)
    return shell_cmd + [command]


def _truncate(text: str, max_bytes: int) -> str:
    """Truncate text at a UTF-8 byte boundary, appending a notice if cut."""
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", errors="ignore") + "\n[output truncated]"


def _check_auth() -> bool:
    """Return True if the request is authorized (or auth is disabled)."""
    if not API_KEY:
        return True
    provided = request.headers.get("X-API-Key", "")
    return hmac.compare_digest(API_KEY, provided)


def _error(status: int, error: str, message: str):
    return jsonify({"success": False, "error": error, "message": message}), status

# ── Flask app ─────────────────────────────────────────────────────────────────

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=[])


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "shell": SHELL_CMD[0],
        "restricted_mode": RESTRICTED_MODE,
        "auth_enabled": bool(API_KEY),
    }), 200


@app.route("/execute", methods=["POST"])
@limiter.limit("30 per minute")
def execute():
    if RESTRICTED_MODE:
        _audit.info("EXECUTE ip=%s blocked=restricted_mode", request.remote_addr)
        return _error(403, "disabled", "Shell execution is disabled in restricted mode. Use /generate-claude instead.")

    if not _check_auth():
        return _error(401, "unauthorized", "Invalid or missing API key")

    if not request.is_json:
        return _error(400, "invalid_request", "Content-Type must be application/json")

    data = request.get_json(silent=True)
    if not data or not isinstance(data.get("command"), str) or not data["command"].strip():
        return _error(400, "invalid_request", "Field 'command' is required and must be a non-empty string")

    command = data["command"]

    if len(command) > MAX_COMMAND_LEN:
        return _error(400, "invalid_request", f"Command exceeds maximum length of {MAX_COMMAND_LEN} characters")

    full_cmd = _build_shell_argv(SHELL_CMD, command)
    start = time.monotonic()
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=COMMAND_TIMEOUT,
            text=False,  # raw bytes — safe for non-UTF-8 output
        )
    except subprocess.TimeoutExpired:
        _audit.info("EXECUTE ip=%s exit=timeout cmd=%r", request.remote_addr, command[:200])
        return _error(408, "timeout", f"Command timed out after {COMMAND_TIMEOUT} seconds")
    except Exception as exc:
        app.logger.error("Subprocess launch failed: %s", exc)
        return _error(500, "internal_error", "Failed to launch subprocess")

    duration_ms = int((time.monotonic() - start) * 1000)
    stdout = _truncate(result.stdout.decode("utf-8", errors="replace"), MAX_OUTPUT_BYTES)
    stderr = _truncate(result.stderr.decode("utf-8", errors="replace"), MAX_OUTPUT_BYTES)

    _audit.info("EXECUTE ip=%s exit=%d duration=%dms cmd=%r",
                request.remote_addr, result.returncode, duration_ms, command[:200])

    return jsonify({
        "success":    result.returncode == 0,
        "stdout":     stdout,
        "stderr":     stderr,
        "exitCode":   result.returncode,
        "durationMs": duration_ms,
    }), 200

@app.route("/generate-claude", methods=["POST"])
@limiter.limit("10 per minute")
def generate_claude():
    if not _check_auth():
        return _error(401, "unauthorized", "Invalid or missing API key")

    if not request.is_json:
        return _error(400, "invalid_request", "Content-Type must be application/json")

    data = request.get_json(silent=True)
    if not data or not isinstance(data.get("user_prompt"), str) or not data["user_prompt"].strip():
        return _error(400, "invalid_request", "Field 'user_prompt' is required and must be a non-empty string")

    user_prompt   = data["user_prompt"]
    system_prompt = data.get("system_prompt", "")
    model         = data.get("model", "claude-haiku-4-5-20251001")

    claude_bin = shutil.which("claude") or "claude"
    cmd = [claude_bin, "-p", user_prompt, "--model", model,
           "--output-format", "json", "--dangerously-skip-permissions"]
    if system_prompt:
        cmd += ["--system-prompt", system_prompt]

    print(f"[generate-claude] model={model} prompt_len={len(user_prompt)}")
    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=COMMAND_TIMEOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        _audit.info("GENERATE ip=%s exit=timeout model=%s prompt_len=%d", request.remote_addr, model, len(user_prompt))
        return _error(408, "timeout", f"Claude timed out after {COMMAND_TIMEOUT} seconds")
    except Exception as exc:
        _audit.info("GENERATE ip=%s exit=error model=%s error=%r", request.remote_addr, model, str(exc))
        app.logger.error("generate-claude subprocess failed: %s", exc)
        return _error(500, "internal_error", f"Failed to launch Claude: {exc}")

    duration_ms = int((time.monotonic() - start) * 1000)
    _audit.info("GENERATE ip=%s exit=%d duration=%dms model=%s prompt_len=%d",
                request.remote_addr, result.returncode, duration_ms, model, len(user_prompt))
    print(f"[generate-claude] exit={result.returncode} duration={duration_ms}ms")

    if result.returncode != 0:
        stderr_snippet = (result.stderr or "")[:500]
        return jsonify({"success": False, "error": f"Claude exited {result.returncode}: {stderr_snippet}"}), 200

    try:
        parsed = json.loads(result.stdout)
    except Exception:
        return _error(500, "internal_error", f"Failed to parse Claude JSON output: {result.stdout[:200]}")

    if parsed.get("is_error") or not parsed.get("result"):
        return jsonify({"success": False, "error": "Claude returned an error or empty result"}), 200

    return jsonify({
        "success":     True,
        "result":      parsed["result"],
        "cost_usd":    parsed.get("cost_usd", 0),
        "duration_ms": duration_ms,
    }), 200


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Remote shell command execution server")
    parser.add_argument("--host",  default=HOST)
    parser.add_argument("--port",  type=int, default=PORT)
    parser.add_argument("--shell", default=None, help="Override shell executable")
    args = parser.parse_args()

    if args.shell:
        global SHELL_CMD
        SHELL_CMD = [args.shell, "-c"]

    if not RESTRICTED_MODE:
        print("\n" + "=" * 62)
        print("  WARNING: SHELL EXECUTION IS ENABLED")
        print("  /execute exposes a full shell over the network.")
        print("  - NEVER run without API_KEY set.")
        print("  - NEVER expose this port to the internet without a firewall.")
        print("  - Set RESTRICTED_MODE=true for safer public deployments.")
        print("  See SECURITY_WARNING.md for full guidance.")
        print("=" * 62)

    mode_label   = "RESTRICTED (shell disabled)" if RESTRICTED_MODE else "UNRESTRICTED (shell enabled)"
    auth_label   = "ENABLED" if API_KEY else "DISABLED — set API_KEY before exposing to network!"
    print(f"""
Claude Code Local Gateway (CCLG)
  Listening:  http://{args.host}:{args.port}
  Web UI:     http://localhost:{args.port}/
  Auth:       {auth_label}
  Shell:      {' '.join(SHELL_CMD)}
  Mode:       {mode_label}
  Audit log:  {LOG_FILE}

Press Ctrl+C to stop.
""")

    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
