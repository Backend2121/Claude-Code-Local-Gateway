# Security Warning

This server can expose a **full shell** to the network. Read this document before deploying.

---

## The risk

The `/execute` endpoint runs any command on the host machine as the user running the server. If an attacker can reach the endpoint and knows (or guesses) your API key, they have full control of the machine.

This is by design — the server is a remote execution gateway. The security model is: **you control access, we help you do it safely**.

---

## Recommended configuration for public deployments

```
RESTRICTED_MODE=true    # disables /execute entirely
API_KEY=<strong random key>
HOST=127.0.0.1          # only accept connections from a local proxy
```

With `RESTRICTED_MODE=true`, only `/generate-claude` is available. No shell access is possible regardless of the API key.

---

## Generating a strong API key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

This generates 256 bits of cryptographically secure randomness. Do not use short or guessable values.

---

## Checklist before exposing to the internet

- [ ] `API_KEY` is set to a long random value
- [ ] `RESTRICTED_MODE=true` (unless you explicitly need shell access)
- [ ] Server is behind a TLS reverse proxy (Caddy / nginx) — see README
- [ ] `HOST=127.0.0.1` so the server only accepts local proxy connections
- [ ] Firewall blocks direct access to the server port (8642)
- [ ] You understand that the process running the server has OS-level access

---

## If you need shell access (`RESTRICTED_MODE=false`)

Additional precautions:

- **Run the server as a dedicated low-privilege user** with no sudo rights
- **Use a firewall allowlist** — restrict the port to known IP ranges only
- **Monitor the audit log** (`claude_server.log`) for unexpected commands
- **Consider a VPN** instead of public internet exposure
- **Never run as root or Administrator**

---

## What the server does NOT do

- Does not sandbox or restrict commands in any way (when shell is enabled)
- Does not enforce command allowlists beyond the optional `RESTRICTED_MODE`
- Does not encrypt traffic — use a TLS proxy
- Does not log command output (only command text, IP, exit code, duration)

---

## Reporting security issues

If you find a vulnerability, please open a private GitHub Security Advisory rather than a public issue.
