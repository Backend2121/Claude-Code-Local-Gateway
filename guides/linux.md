# Linux Installation Guide

This guide walks you through setting up CCLG on Linux from scratch. Commands are written for Ubuntu/Debian. For Fedora/RHEL, swap `apt` for `dnf`.

---

## Recommended: Docker (skip Steps 1–3)

> **If you have Docker installed, skip straight to [Step 4 — Log In to Claude Code](#step-4--log-in-to-claude-code), then [Step 5 — Install Docker](#step-5--install-docker) (already done), then jump to [Step 6](#step-6--download-this-project).**
>
> Docker bundles Python, Node.js, and the Claude CLI inside the image — you don't need to install any of them manually. Just clone the repo, configure `.env`, and run `docker compose up`.

---

## What You Need Before Starting

- A **Claude PRO or MAX subscription** (a free account will not work)
- A Linux machine running Ubuntu 20.04+ or any modern Debian-based distro
- A terminal
- An internet connection

> **Using Docker?** You only need Docker installed — skip Steps 1, 2, and 3.

---

## Step 1 — Install Python

> **Docker users: skip this step.**

Python 3.10+ is required. Most modern distros include it, but verify first:

```bash
python3 --version
```

If you see `Python 3.10.x` or higher, skip to Step 2. Otherwise, install it:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

Verify:

```bash
python3 --version
pip3 --version
```

---

## Step 2 — Install Node.js

> **Docker users: skip this step.**

Claude Code is distributed as a Node.js package. The recommended way is via NodeSource, which gives you the latest LTS version:

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
```

Verify:

```bash
node --version
npm --version
```

Both should print a version number (e.g. `v20.x.x`).

---

## Step 3 — Install Claude Code CLI

> **Docker users: skip this step.**

```bash
sudo npm install -g @anthropic-ai/claude-code
```

Verify:

```bash
claude --version
```

---

## Step 4 — Log In to Claude Code

```bash
claude
```

Follow the prompts to log in via your browser. Once authenticated, exit the interactive session:

```
/exit
```

### Headless VPS (no browser available)

If your server has no display, the browser-based login won't work. Use one of these approaches instead:

**Option A — Copy credentials from a machine where you're already logged in (recommended)**

On your local machine (where `claude` is already authenticated), run:

```bash
scp -r ~/.claude/ user@your-vps-ip:~/.claude/
```

Claude Code stores its auth tokens in `~/.claude/` — copying this folder to the VPS is enough.

**Option B — SSH port forwarding**

Connect to the VPS with a port forward before running `claude`:

```bash
ssh -L 9876:localhost:9876 user@your-vps-ip
```

Then run `claude` inside that SSH session. When it prints a `localhost` URL for the OAuth flow, open it in your **local** browser — the tunnel makes it reachable. Complete the login, then run `/exit`.

---

## Step 5 — Install Docker (recommended)

Skip this step only if you plan to run the server directly with Python. **Docker is the recommended way to run CCLG** — it handles Python, Node.js, and the Claude CLI automatically inside the container.

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Add your user to the `docker` group so you don't need `sudo` for every Docker command:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Verify:

```bash
docker --version
docker compose version
```

---

## Step 6 — Download This Project

**Option A — Release download (recommended):**
1. Go to the [Releases page](https://github.com/Backend2121/CCLG/releases) on GitHub.
2. Under the latest release, copy the link to the `.zip` or `.tar.gz` file and download it:
```bash
wget https://github.com/Backend2121/CCLG/releases/download/vX.X.X/CCLG.zip
unzip CCLG.zip
cd CCLG
```

**Option B — Using Git:**
```bash
git clone https://github.com/Backend2121/CCLG.git
cd CCLG
```

> All remaining steps assume you are inside this folder in your terminal.

---

## Step 7 — Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

You should see several packages being downloaded and installed.

---

## Step 8 — Create Your Configuration File

Copy the template:

```bash
cp .env.example .env
```

Open it in a text editor:

```bash
nano .env
```

### Setting your API key (required)

The API key protects your server from unauthorized access. Generate a strong random one:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste it as the value for `API_KEY` in `.env`:

```
API_KEY=paste_your_generated_key_here
```

### Other settings to review

| Setting | Default | What it does |
|---|---|---|
| `PORT` | `8642` | The port the server listens on. Fine to leave as-is. |
| `HOST` | `127.0.0.1` | `127.0.0.1` means only this machine can connect. Use `0.0.0.0` to accept connections from other devices on your network. |
| `RESTRICTED_MODE` | `true` | When `true`, only `/generate-claude` works. The shell execution endpoint is disabled. Recommended to leave as `true`. |

Save and exit: `Ctrl+O`, `Enter`, `Ctrl+X`.

---

## Step 9 — Run the Server

**Option A — Docker (recommended):**

```bash
docker compose up
```

The image will build on first run (this takes a few minutes). Subsequent starts are instant.

**Option B — Python directly:**

```bash
python3 server.py
```

You should see:

```
 * Running on http://127.0.0.1:8642
```

Leave the terminal open — closing it stops the server.

---

## Step 10 — Open the Web UI

Open your browser and go to:

```
http://localhost:8642
```

Enter your API key when prompted (the same value you set for `API_KEY` in `.env`).

Type a prompt in the Claude tab and click Send to test it.

---

## Stopping the Server

Press `Ctrl + C` in the terminal where the server is running.

---

## Running as a systemd Service (optional, for always-on use)

If you want CCLG to start automatically on boot and run in the background:

1. Create a service file (replace `/home/youruser/CCLG` with your actual path):

```bash
sudo nano /etc/systemd/system/cclg.service
```

Paste this content:

```ini
[Unit]
Description=Claude Code Local Gateway
After=network.target

[Service]
User=youruser
WorkingDirectory=/home/youruser/CCLG
ExecStart=/usr/bin/python3 server.py
Restart=on-failure
EnvironmentFile=/home/youruser/CCLG/.env

[Install]
WantedBy=multi-user.target
```

2. Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cclg
sudo systemctl start cclg
```

3. Check it is running:

```bash
sudo systemctl status cclg
```

4. View logs:

```bash
journalctl -u cclg -f
```

---

## Starting the Server Again Later

If running manually, navigate to the project folder and run:

```bash
python3 server.py
```

If using systemd, it starts automatically on boot. To start it manually:

```bash
sudo systemctl start cclg
```

---

## Troubleshooting

**`python3` not found**
Run `sudo apt install -y python3` and try again.

**`claude` is not recognized**
Make sure Node.js installed correctly (`node --version` works), then re-run the npm install command from Step 3.

**`pip3 install` fails with permission errors**
Do not use `sudo pip3`. Instead, install to user space: `pip3 install --user -r requirements.txt`.

**`npm install -g` fails with permission errors**
The NodeSource install (Step 2) should avoid this. If it persists, check that Node.js was installed system-wide via the NodeSource script, not via `snap` or `nvm`.

**Browser shows "This site can't be reached"**
Make sure the server is still running. Also confirm you're visiting `http://` (not `https://`) and port `8642`.

**Claude returns an error about authentication**
Run `claude` in the terminal and follow the login steps again (Step 4).

---

## Security Note

Your `.env` file contains your API key — do not share it or commit it to Git. The `.gitignore` already excludes it.

For internet-facing deployments, place the server behind a TLS reverse proxy (Caddy is the easiest option) and keep `HOST=127.0.0.1`. See the [README](../README.md) for reverse proxy configuration examples.
