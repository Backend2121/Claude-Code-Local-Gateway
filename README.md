# Claude Gateway

A lightweight, self-hosted HTTP server that gives you remote access to **Claude AI** and (optionally) a shell over a simple REST API — with a built-in web UI.

```
Browser / HTTP client
        |
        v
  Flask Server (this repo)
        |
        +-- /generate-claude --> claude CLI --> Anthropic API
        +-- /execute         --> local shell  (optional, see security)
```

> **Security notice:** If you enable shell execution (`RESTRICTED_MODE=false`), read [SECURITY_WARNING.md](SECURITY_WARNING.md) before exposing this server to any network.

---

## Features

- **Web UI** at `/` — no client needed, works in any browser
- **`/generate-claude`** — send prompts to Claude, get structured responses back
- **`/execute`** — run shell commands remotely (disabled by default via `RESTRICTED_MODE`)
- **API key auth** with constant-time comparison (timing-attack safe)
- **Rate limiting** — 10 req/min on Claude, 30 req/min on shell
- **Audit logging** — every shell call logged to a rotating file
- **Docker support** — one command to deploy

---

## Quickstart

### Option A — Docker (recommended for new users)

```bash
git clone https://github.com/YOUR_USERNAME/claude-gateway
cd claude-gateway

cp .env.example .env
# Edit .env: set API_KEY to a strong random value
python -c "import secrets; print(secrets.token_hex(32))"  # generate a key

docker compose up
```

Open `http://localhost:8642` in your browser.

### Option B — Python (local / development)

```bash
git clone https://github.com/YOUR_USERNAME/claude-gateway
cd claude-gateway

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env: set API_KEY

python server.py
```

---

## Configuration

All settings live in `.env` (copy from `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8642` | Listening port |
| `HOST` | `127.0.0.1` | Bind address (`0.0.0.0` for all interfaces) |
| `API_KEY` | _(empty)_ | Required for auth. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `RESTRICTED_MODE` | `true` | When `true`, disables `/execute` — only Claude endpoint works |
| `FORCE_SHELL` | _(auto)_ | Override shell: `bash`, `sh`, `powershell`, `cmd` |
| `COMMAND_TIMEOUT` | `120` | Max seconds per shell command |
| `MAX_OUTPUT_BYTES` | `1048576` | Max output size captured (1 MB) |
| `MAX_COMMAND_LENGTH` | `8192` | Max command string length |
| `LOG_FILE` | `claude_server.log` | Rotating audit log path |

---

## API Reference

All endpoints that require auth expect the header:
```
X-API-Key: your-api-key
```

### `GET /health`
No auth required.
```json
{ "status": "ok", "shell": "bash", "restricted_mode": true, "auth_enabled": true }
```

### `POST /generate-claude`
Rate limit: 10 requests/minute per IP.
```json
// Request
{
  "user_prompt": "Explain recursion in one sentence.",
  "system_prompt": "Be concise.",         // optional
  "model": "claude-haiku-4-5-20251001"   // optional
}

// Response
{
  "success": true,
  "result": "Recursion is a function calling itself...",
  "cost_usd": 0.0002,
  "duration_ms": 1240
}
```

### `POST /execute`
Disabled when `RESTRICTED_MODE=true`. Rate limit: 30 requests/minute per IP.
```json
// Request
{ "command": "claude --version" }

// Response
{
  "success": true,
  "stdout": "claude 1.x.x\n",
  "stderr": "",
  "exitCode": 0,
  "durationMs": 85
}
```

---

## Deployment behind a reverse proxy (HTTPS)

Never expose the server directly on port 80/443. Use Caddy or nginx for TLS termination.

**Caddyfile:**
```
yourdomain.com {
    reverse_proxy localhost:8642
}
```

**nginx snippet:**
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    # ... ssl_certificate config ...

    location / {
        proxy_pass http://127.0.0.1:8642;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Set `HOST=127.0.0.1` in `.env` so the server only accepts connections from the proxy.

---

## Security

See [SECURITY_WARNING.md](SECURITY_WARNING.md) for the full security guide.

**TL;DR:**
- Always set `API_KEY`
- Keep `RESTRICTED_MODE=true` unless you specifically need shell access
- Put the server behind a TLS reverse proxy before exposing to the internet
- Never commit your `.env` file (it is gitignored)

---

## Prerequisites

- Python 3.10+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated (`claude` available in PATH)

---

## Contributing

PRs and issues welcome. Keep changes focused and minimal.

1. Fork the repo
2. Create a branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Open a pull request

---

## License

MIT
