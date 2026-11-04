# =============================================================================
# FILE HEADER
# file    : msme/filtering/filter_log.py
# role    : Filter — append-only verdict/error trail
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : write data/filter_verdicts.jsonl and data/filter_errors.jsonl for the verdict/log/report pages.
# pages   : backs /verdicts, /logs.json, report history
# calls   : json/os/time
# called  : filter_service.py, pipeline.py (auto-filter)
# amend   : keep the existing JSON keys; add new keys only. Test: POST /filter then GET /verdicts
# =============================================================================
"""Append-only filter verdict and error logs.

Both the manual filter service and the receive auto-filter write here, so the
existing Verdicts/Logs pages and report tooling see one trail.
"""
import json
import os
import time

from msme import paths

VERDICT_LOG = str(paths.DATA / "filter_verdicts.jsonl")
ERROR_LOG = str(paths.DATA / "filter_errors.jsonl")


def log_verdict(article, verdict, source="manual"):
    """Append one successful verdict; `source` is manual|receive."""
    try:
        os.makedirs(os.path.dirname(VERDICT_LOG) or ".", exist_ok=True)
        row = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": source,
            "subject": (article.get("subject") or "")[:120],
            "from": (article.get("from") or "")[:80],
            "date": (article.get("date") or "")[:40],
            "outcome": verdict.get("outcome", ""),
            "gate": verdict.get("gate"),
            "weighted": verdict.get("weighted"),
            "threshold": verdict.get("threshold"),
            "confidence": verdict.get("confidence"),
            "gates": verdict.get("gates", {}),
            "scores": verdict.get("scores", {}),
            "reasons": verdict.get("reasons", []),
            "model": verdict.get("model"),
            "usage": verdict.get("usage", {}),
            "preprocess": verdict.get("preprocess", {}),
            "deterministic": verdict.get("deterministic", {}),
            "assist": verdict.get("assist", {}),
            "extra": verdict.get("extra", {}),
        }
        with open(VERDICT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except Exception as e:
        print(f"[filter] log failed: {e}")


def log_error(article, error):
    """Append one failed judgement."""
    try:
        os.makedirs(os.path.dirname(ERROR_LOG) or ".", exist_ok=True)
        row = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": "receive" if article.get("_source") == "receive" else "manual",
            "subject": (article.get("subject") or "")[:120],
            "from": (article.get("from") or "")[:80],
            "error": str(error)[:300],
        }
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass
