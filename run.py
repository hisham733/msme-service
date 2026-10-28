# =============================================================================
# FILE HEADER
# file    : run.py
# role    : Entrypoint — one combined receive+filter app on :8899
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : boot one uvicorn worker with `combined:app` plus the optional auto-poll scheduler.
# pages   : all pages, served through combined.py (receive + filter sub-apps)
# calls   : uvicorn, config.py, scheduler.py; app `combined:app`
# called  : docker CMD / `python run.py`
# amend   : keep ONE worker (scheduler double-fire). One port: config.DASH_PORT.
#           Test: python3 -m compileall -q run.py; curl -s localhost:8899/health
# =============================================================================
"""Entrypoint: one combined receive + filter app on :8899.

Run inside Docker (single uvicorn worker for the scheduler).

Example:
    python run.py            # starts the combined app + (optional) auto-poll scheduler
"""
import uvicorn

import config
import scheduler


def main():
    # Auto-poll scheduler (off unless ENABLE_AUTO=true). Must be single worker.
    scheduler.start()
    server = uvicorn.Server(
        uvicorn.Config(
            "combined:app",
            host=config.API_HOST,
            port=config.DASH_PORT,
            log_level="info",
        )
    )
    server.run()


if __name__ == "__main__":
    main()
