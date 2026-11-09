# =============================================================================
# FILE HEADER
# file    : msme/repurpose/repurpose_worker.py
# role    : Repurpose — manual CLI for the in-process runner (T-050 / D40)
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : keep the old operator command working without a subprocess: `--once` runs the
#           pending queue through the in-process engine and exits.
# pages   : n/a (the app starts the daemon worker itself; /repurpose.html shows status)
# calls   : msme.repurpose.runner
# called  : operator CLI: python3 -m msme.repurpose.repurpose_worker --once
# amend   : one article at a time; never run this while the app's worker is busy.
#           Test: python3 -m msme.repurpose.repurpose_worker --once
# =============================================================================
"""Manual runner: the engine is in-process now (T-050); this is the operator command."""
import argparse

from msme.repurpose import runner


def main():
    ap = argparse.ArgumentParser(description="Run the in-process repurpose engine once")
    ap.add_argument("--once", action="store_true", help="process the current pending queue and exit")
    ap.parse_args()
    return runner.run_once()


if __name__ == "__main__":
    raise SystemExit(main())
