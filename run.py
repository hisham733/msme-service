# =============================================================================
# FILE HEADER
# file    : run.py
# role    : Entrypoint — one combined receive+filter app on :8899
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : launch the service package (`msme.__main__`): one uvicorn worker with
#           `msme.combined:app` plus the optional auto-poll scheduler.
# pages   : all pages, served through msme/combined.py (receive + filter sub-apps)
# calls   : msme.__main__ (config, scheduler, uvicorn)
# called  : docker CMD / `python run.py` / `python -m msme`
# amend   : keep ONE worker (scheduler double-fire). One port: config.DASH_PORT.
#           Test: python3 -m compileall -q run.py; curl -s localhost:8899/health
# =============================================================================
"""Entrypoint: one combined receive + filter app on :8899.

Example:
    python run.py            # starts the combined app + (optional) auto-poll scheduler
"""
from msme.__main__ import main

if __name__ == "__main__":
    main()
