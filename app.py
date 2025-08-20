import os
import subprocess
import sys
import threading
import time
from flask import Flask

app = Flask(__name__)

@app.get("/")
def index():
    return "YO"

def run_git(args, cwd=None):
    result = subprocess.run(["git"] + list(args),
                            cwd=cwd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def check_for_updates_loop(interval_seconds=5):
    repo_dir = os.path.abspath(os.getcwd())
    while True:
        try:
            # Fetch from origin
            rc, out, err = run_git(["fetch", "origin", "--quiet"], cwd=repo_dir)
            if rc != 0:
                print(f"[autoupdate] git fetch failed: {err}", flush=True)
                time.sleep(interval_seconds)
                continue

            # Determine local and upstream SHAs
            rc, local_sha, err = run_git(["rev-parse", "HEAD"], cwd=repo_dir)
            if rc != 0:
                print(f"[autoupdate] git rev-parse HEAD failed: {err}", flush=True)
                time.sleep(interval_seconds)
                continue

            # Try upstream via @{u}; fallback to origin/<branch>
            rc, upstream_sha, err = run_git(["rev-parse", "@{u}"], cwd=repo_dir)
            if rc != 0 or not upstream_sha:
                rc_b, branch, err_b = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir)
                if rc_b != 0 or branch in ("HEAD", ""):
                    print(f"[autoupdate] Cannot determine upstream branch: {err or err_b}", flush=True)
                    time.sleep(interval_seconds)
                    continue
                rc_u, upstream_sha, err_u = run_git([f"rev-parse", f"origin/{branch}"], cwd=repo_dir)
                if rc_u != 0:
                    print(f"[autoupdate] Cannot determine origin/{branch} SHA: {err_u}", flush=True)
                    time.sleep(interval_seconds)
                    continue

            if local_sha != upstream_sha:
                print(f"[autoupdate] Update detected: local {local_sha[:7]} != remote {upstream_sha[:7]}", flush=True)
                # Attempt fast-forward pull
                rc_p, out_p, err_p = run_git(["pull", "--ff-only"], cwd=repo_dir)
                if rc_p != 0:
                    print(f"[autoupdate] git pull failed: {err_p}", flush=True)
                    # Don't restart if pull failed
                    time.sleep(interval_seconds)
                    continue

                print("[autoupdate] Pulled latest changes. Restarting application...", flush=True)
                # Re-exec current process
                python = sys.executable
                os.execv(python, [python] + sys.argv)

        except Exception as e:
            print(f"[autoupdate] Exception in update loop: {e}", flush=True)
        finally:
            time.sleep(interval_seconds)


def start_update_thread():
    t = threading.Thread(target=check_for_updates_loop, kwargs={"interval_seconds": 5}, daemon=True)
    t.start()

if __name__ == "__main__":
    # Start background update checker
    start_update_thread()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, use_reloader=False)
