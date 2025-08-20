# auto-load

Minimal Flask app that runs in a Linux environment, checks the Git origin for updates every 5 seconds, pulls fast-forward changes, and restarts itself.

## Requirements
- Python 3.8+ (system python3 is fine)
- Git installed and available on PATH
- Network access to your Git remote (origin)
- For private repositories: working credentials (SSH agent or Git credential helper)

## How to run (Linux)
1. Clone this repository and ensure an origin remote and tracking branch are configured:
   ```bash
   git clone <repo-url>
   cd auto-load
   git remote -v
   git status -sb   # should show something like: main...origin/main
   ```
2. Install dependencies:
   ```bash
   python3 -m pip install Flask
   ```
   Optional: use a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install Flask
   ```
3. Start the app:
   ```bash
   HOST=0.0.0.0 PORT=5000 python3 app.py
   ```
   Then open http://localhost:5000/ (endpoint returns "OK").

## What it does
- Every 5 seconds it runs:
  - `git fetch origin --quiet`
  - Compares local `HEAD` to the upstream (`@{u}`) or `origin/<branch>`.
  - If different, runs `git pull --ff-only`.
  - On a successful pull, it re-execs the current Python process to apply changes.

## Notes
- Self-restart uses `os.execv`, so the process is replaced cleanly (no orphan processes).
- If a fast-forward pull is not possible (e.g., conflicts or force-push needed), the app logs the error and continues without restarting.
- The Flask reloader is disabled (`use_reloader=False`) to avoid duplicate processes; the app handles its own restarts.
- To run additional steps after pulls (e.g., `pip install -r requirements.txt`), that can be added before the restart.
- Ensure Git credentials are available for private repos (SSH agent loaded or a credential helper configured).
- Suitable to run under a supervisor (systemd, Docker, etc.); logs are printed to stdout.

## Endpoint
- GET `/` → returns "OK"