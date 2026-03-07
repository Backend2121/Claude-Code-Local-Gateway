# Windows Installation Guide

This guide walks you through setting up CCLG on Windows from scratch.

---

## What You Need Before Starting

- A **Claude PRO or MAX subscription** (a free account will not work)
- A Windows PC running Windows 10 or 11
- An internet connection

---

## Step 1 — Install Python

Python is the programming language this server is written in.

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/) and click **Download Python 3.x.x** (the big yellow button).
2. Run the installer.
3. **Important:** On the first screen, check the box that says **"Add python.exe to PATH"** before clicking Install Now. If you miss this, commands in later steps will fail.
4. Click **Install Now** and wait for it to finish.

To verify it worked, open **Command Prompt** (press `Win + R`, type `cmd`, press Enter) and run:

```
python --version
```

You should see something like `Python 3.12.x`. If you get an error, re-run the installer and make sure the PATH checkbox is ticked.

---

## Step 2 — Install Claude Code CLI

Claude Code is the command-line tool this server wraps. Follow the official installation instructions here:

**[Claude Code — Installation & Setup](https://code.claude.com/docs/en/overview#desktop-app)**

Once installed, verify it worked by running in Command Prompt:

```
claude --version
```

---

## Step 3 — Log In to Claude Code

You need to authenticate Claude Code with your Anthropic account.

```
claude
```

Follow the prompts to log in via your browser. Once authenticated, you can close the interactive session by typing `/exit`.

---

## Step 4 — Download This Project

If you haven't already, download this project to your PC.

**Option A — Release download (recommended):**
1. Go to the [Releases page](https://github.com/Backend2121/CCLG/releases) on GitHub.
2. Under the latest release, download the `.zip` file.
3. Extract it somewhere easy to find (e.g. `C:\Users\YourName\CCLG`).
4. Open Command Prompt and navigate to the folder:
```
cd C:\Users\YourName\CCLG
```

**Option B — Using Git** (if you have Git installed):
```
git clone https://github.com/Backend2121/CCLG.git
cd CCLG
```

**Option C — Download ZIP from GitHub:**
1. On the repository page, click the green **Code** button, then **Download ZIP**.
2. Extract it and navigate to the folder in Command Prompt as above.

> All remaining steps assume you are inside this folder in Command Prompt.

---

## Step 5 — Install Python Dependencies

This installs the Python packages the server needs:

```
pip install -r requirements.txt
```

You should see several packages being downloaded and installed. If `pip` is not found, make sure you ticked "Add to PATH" in Step 1.

---

## Step 6 — Create Your Configuration File

The server reads its settings from a file called `.env`. A template is included.

Rename `.env.example` to `.env`.

### Setting your API key (required)

The API key protects your server from unauthorized access. Generate a strong random one by running:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output (a long string of letters and numbers) and paste it as the value for `API_KEY` in `.env`:

```
API_KEY=paste_your_generated_key_here
```

### Other settings to review

| Setting | Default | What it does |
|---|---|---|
| `PORT` | `8642` | The port the server listens on. Fine to leave as-is. |
| `HOST` | `127.0.0.1` | `127.0.0.1` means only your own PC can connect. Use `0.0.0.0` only if you need other devices on your network to connect. |
| `RESTRICTED_MODE` | `true` | When `true`, only `/generate-claude` works. The shell execution endpoint is disabled. Recommended to leave as `true`. |

Save and close Notepad when done.

---

## Step 7 — Run the Server

```
python server.py
```

You should see output like:

```
 * Running on http://127.0.0.1:8642
```

The server is now running. **Leave this Command Prompt window open** — closing it stops the server.

---

## Step 8 — Open the Web UI

Open your browser and go to:

```
http://localhost:8642
```

You should see the CCLG web interface. Enter your API key when prompted (the same value you set for `API_KEY` in `.env`).

Type a prompt in the Claude tab and click Send to test it.

---

## Stopping the Server

Click the Command Prompt window and press `Ctrl + C`. The server will shut down.

---

## Starting the Server Again Later

Every time you want to use the server, open Command Prompt, navigate to the project folder, and run:

```
python server.py
```

---

## Troubleshooting

**`python` is not recognized**
Re-run the Python installer and make sure "Add python.exe to PATH" is checked.

**`claude` is not recognized**
Re-follow the official Claude Code installation instructions linked in Step 2.

**`pip install` fails with permission errors**
Try running Command Prompt as Administrator: right-click the Start menu, choose "Terminal (Admin)" or "Command Prompt (Admin)".

**Browser shows "This site can't be reached"**
Make sure the server is still running in Command Prompt. Also check that you're visiting `http://` (not `https://`) and port `8642`.

**Claude returns an error about authentication**
Run `claude` in Command Prompt and follow the login steps again (Step 3).

---

## Security Note

Your `.env` file contains your API key — do not share it or commit it to Git. The `.gitignore` already excludes it, but be careful if you copy the project folder anywhere.