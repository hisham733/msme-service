# =============================================================================
# FILE HEADER
# file    : msme/repurpose/repurpose_worker.py
# role    : Host-side worker — runs the Repurpose engine for new exported articles
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : watch repurpose_inbox/; run `pipeline.run run --folder` one article at a time;
#           skip folders that already have draft.md/run.json (validated/HOLD).
# pages   : engine dashboard :8765 reads the same inbox
# calls   : subprocess, MSME_AI_News pipeline, repurpose_inbox
# called  : operator/host: python3 repurpose_worker.py (or nohup)
# amend   : one article at a time; do not run two engines; never touch all_emails.
#           Test: python3 repurpose_worker.py --once
# =============================================================================
"""Run the external Repurpose engine for new folders in repurpose_inbox.

The app exports accepted articles into the inbox. This worker is the automatic
engine trigger; it is intentionally a host process because the engine and its
DeepSeek `.env` live outside the msme-service container.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from msme import paths

ROOT = paths.ROOT
ENGINE = Path(os.environ.get(
    "REPURPOSE_ENGINE_ROOT", "/home/hisham/Desktop/new_div/MSME_AI_News"))
INBOX = paths.REPURPOSE_INBOX
POLL = int(os.environ.get("REPURPOSE_POLL_SECONDS", "5"))


def _release_text(folder):
    for p in sorted(folder.glob("*.md")):
        if p.name.lower() not in ("link.md", "draft.md", "draft.prev.md", "readme.md"):
            return p
    return None


def pending():
    if not INBOX.is_dir():
        return []
    out = []
    for d in sorted(INBOX.iterdir()):
        if not d.is_dir() or not _release_text(d):
            continue
        if (d / "run.json").exists() or (d / "draft.md").exists():
            continue
        out.append(d)
    return out


def run_one(folder):
    print(f"[worker] run {folder.name}", flush=True)
    proc = subprocess.run(
        [sys.executable, "-m", "pipeline.run", "run", "--folder", folder.name],
        cwd=str(ENGINE), text=True, capture_output=True, timeout=1800,
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    print(out[-4000:] if out else "(no stdout)", flush=True)
    if err:
        print("[worker stderr] " + err[-2000:], flush=True)
    return proc.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="process the current pending queue once")
    a = ap.parse_args()
    print(f"[worker] engine={ENGINE} inbox={INBOX}", flush=True)
    while True:
        items = pending()
        if not items:
            if a.once:
                print("[worker] no pending folders", flush=True)
                return 0
            time.sleep(POLL)
            continue
        for d in items:
            try:
                run_one(d)
            except Exception as e:
                print(f"[worker] failed {d.name}: {e}", flush=True)
            if a.once:
                return 0
        if a.once:
            return 0
        time.sleep(POLL)


if __name__ == "__main__":
    raise SystemExit(main())
