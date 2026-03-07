# Raspberry Pi Installation Guide

This guide walks you through setting up CCLG on a Raspberry Pi 4 or 5 from scratch.

> **Compatibility:** Raspberry Pi 4 and 5 only. The RPi Zero, Zero 2W, and RPi 3 are not supported — Node.js 18+ requires ARM64, and those models either use ARMv6 or have too little RAM.

---

## Recommended: Docker (skip Steps 2, 3, and 4)

> **Docker is the preferred way to run CCLG on a Raspberry Pi.** The image bundles Python, Node.js, and the Claude CLI — you don't install any of them manually.
>
> If you have Docker (or plan to install it in Step 6), skip Steps 2, 3, and 4. Just clone the repo, configure `.env`, mount your `~/.claude` credentials, and run `docker compose up`.

---

## What You Need Before Starting

- A **Claude PRO or MAX subscription** (a free account will not work)
- A Raspberry Pi 4 (2GB RAM minimum, 4GB recommended) or Raspberry Pi 5
- **64-bit Raspberry Pi OS** (Bookworm or Bullseye) — the 32-bit image will not work
- An internet connection (Ethernet or Wi-Fi)
- SSH access or a keyboard/monitor connected to the Pi

> **Using Docker?** You only need Docker installed — skip Steps 2, 3, and 4.

---

## Step 0 — Verify You Are Running 64-bit OS

Node.js 18+ requires a 64-bit OS. Check before proceeding:

```bash
uname -m
```

If the output is `aarch64`, you are on 64-bit and can continue. If it shows `armv7l` or `armhf`, you need to re-flash your SD card with the **64-bit** Raspberry Pi OS image from [https://www.raspberrypi.com/software/](https://www.raspberrypi.com/software/).

---

## Step 1 — Update the System

```bash
sudo apt update && sudo apt upgrade -y
```

---

## Step 2 — Install Python

> **Docker users: skip this step.**

Python 3 is pre-installed on Raspberry Pi OS. Verify the version:

```bash
python3 --version
```

You need 3.10 or higher. Raspberry Pi OS Bullseye ships with 3.9 — if that's the case, upgrade to Bookworm or install a newer Python:

```bash
sudo apt install -y python3 python3-pip python3-venv
```

Verify:

```bash
python3 --version
pip3 --version
```

---

## Step 3 — Install Node.js

> **Docker users: skip this step.**

The version of Node.js in the default Raspberry Pi OS repos is outdated. Install the current LTS via NodeSource:

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
```

Verify:

```bash
node --version
npm --version
```

Both should print a version number (e.g. `v20.x.x`). If `node --version` still shows an old version, reboot and try again.

---

## Step 4 — Install Claude Code CLI

> **Docker users: skip this step.**

```bash
sudo npm install -g @anthropic-ai/claude-code
```

Verify:

```bash
claude --version
```

---

## Step 5 — Log In to Claude Code

```bash
claude
```

Follow the prompts to log in via your browser. Once authenticated, exit the interactive session:

```
/exit
```

---

## Step 6 — Install Docker (recommended)

Skip this step only if you plan to run the server directly with Python. **Docker is the recommended way to run CCLG** — it handles Python, Node.js, and the Claude CLI automatically inside the container.

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
```

Verify:

```bash
docker --version
docker compose version
```

> The convenience script (`get.docker.com`) is the easiest way to install Docker on Raspberry Pi OS and handles the ARM architecture automatically.

---

## Step 7 — Download This Project

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

## Step 8 — Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

---

## Step 9 — Create Your Configuration File

Copy the template:

```bash
cp .env.example .env
```

Open it in a text editor:

```bash
nano .env
```

### Setting your API key (required)

Generate a strong random key:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output into `.env`:

```
API_KEY=paste_your_generated_key_here
```

### Other settings to review

| Setting | Default | What it does |
|---|---|---|
| `PORT` | `8642` | The port the server listens on. Fine to leave as-is. |
| `HOST` | `127.0.0.1` | `127.0.0.1` means only the Pi itself can connect. Use `0.0.0.0` to accept connections from other devices on your network (e.g. your laptop). |
| `RESTRICTED_MODE` | `true` | When `true`, only `/generate-claude` works. The shell execution endpoint is disabled. Recommended to leave as `true`. |

Save and exit: `Ctrl+O`, `Enter`, `Ctrl+X`.

---

## Step 10 — Run the Server

**Option A — Docker (recommended):**

First, make sure you are logged in to Claude Code (run `claude` and follow the login steps if you haven't already). Then:

```bash
docker compose up
```

The image will build on first run (this takes a few minutes on the Pi). Subsequent starts are instant.

**Option B — Python directly:**

```bash
python3 server.py
```

You should see:

```
 * Running on http://127.0.0.1:8642
```

---

## Step 11 — Access the Web UI

If you set `HOST=0.0.0.0`, open a browser on another device on the same network and go to:

```
http://raspberry-pi-ip:8642
```

Replace `raspberry-pi-ip` with the Pi's IP address (`hostname -I` on the Pi to find it).

If `HOST=127.0.0.1`, you can still reach the UI from your laptop by forwarding the port over SSH:

```bash
ssh -L 8642:localhost:8642 pi@raspberry-pi-ip
```

Then open `http://localhost:8642` in your local browser.

Enter your API key when prompted and send a test prompt in the Claude tab.

---

## Stopping the Server

Press `Ctrl + C` in the terminal where the server is running.

---

## Running as a systemd Service (recommended for always-on use)

This makes CCLG start automatically on boot and run in the background — ideal for a Pi that stays plugged in 24/7.

1. Create a service file (replace `/home/pi/CCLG` and `pi` with your actual path and username):

```bash
sudo nano /etc/systemd/system/cclg.service
```

Paste this content:

```ini
[Unit]
Description=Claude Code Local Gateway
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/CCLG
ExecStart=/usr/bin/python3 server.py
Restart=on-failure
EnvironmentFile=/home/pi/CCLG/.env

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

If using systemd, it starts automatically on boot. To start it manually:

```bash
sudo systemctl start cclg
```

If running manually:

```bash
cd ~/CCLG
python3 server.py
```

---

## Troubleshooting

**`uname -m` shows `armv7l`**
You are on a 32-bit OS. Re-flash your SD card with the 64-bit Raspberry Pi OS image.

**`node --version` shows an old version after NodeSource install**
Reboot the Pi (`sudo reboot`) and check again. If still old, remove the existing package first: `sudo apt remove nodejs` then re-run the NodeSource install.

**`claude` is not recognized**
Make sure Node.js installed correctly (`node --version` works), then re-run the npm install command from Step 4.

**`pip3 install` fails with permission errors**
Do not use `sudo pip3`. Instead: `pip3 install --user -r requirements.txt`.

**Can't reach the web UI from another device**
Make sure `HOST=0.0.0.0` is set in `.env` and the server has been restarted after the change. Also check the Pi's firewall: `sudo ufw status`.

**Claude returns an error about authentication**
Run `claude` in the terminal and follow the login steps again (Step 5).

---

## Security Note

Your `.env` file contains your API key — do not share it. The `.gitignore` already excludes it.

If you expose the Pi directly on your local network (`HOST=0.0.0.0`), make sure `API_KEY` is set and consider enabling your router's firewall. For internet-facing access, place CCLG behind a TLS reverse proxy (Caddy is the easiest option) — see the [README](../README.md) for configuration examples.
