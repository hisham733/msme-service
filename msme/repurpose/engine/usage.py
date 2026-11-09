# =============================================================================
# FILE HEADER
# file    : msme/repurpose/engine/usage.py
# role    : Repurpose — per-run token usage accumulator for the vendored engine
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : count every DeepSeek chat/vision call made for one article so the publish stage can
#           be priced; reset per folder, read once at the end of a run.
# pages   : n/a (backs repurpose_runs.usage_json / run.json usage)
# calls   : stdlib only
# called  : engine/llm_step.py, engine/vision.py, engine/run.py, repurpose/runner.py
# amend   : one article at a time — never make the accumulator global across folders.
#           Test: python3 -m unittest tests.test_repurpose_usage -v
# =============================================================================
"""Token usage for one repurpose run.

The engine calls DeepSeek directly (not through msme.deepseek), so OpenAI-style
``response["usage"]`` is added here from each call.
"""
import threading

_LOCK = threading.Lock()
_TOTAL = {"prompt": 0, "completion": 0, "total": 0, "calls": 0, "model": ""}


def reset():
    """Zero the accumulator at the start of one article."""
    with _LOCK:
        for key in _TOTAL:
            _TOTAL[key] = 0 if key != "model" else ""


def add(usage, model=""):
    """Add one OpenAI-style usage object/dict to the run total."""
    usage = usage or {}
    try:
        prompt = int(usage.get("prompt_tokens") or usage.get("prompt") or 0)
    except (TypeError, ValueError):
        prompt = 0
    try:
        completion = int(usage.get("completion_tokens") or usage.get("completion") or 0)
    except (TypeError, ValueError):
        completion = 0
    try:
        total = int(usage.get("total_tokens") or usage.get("total") or 0)
    except (TypeError, ValueError):
        total = 0
    if not total:
        total = prompt + completion
    if not (prompt or completion or total):
        return
    with _LOCK:
        _TOTAL["prompt"] += prompt
        _TOTAL["completion"] += completion
        _TOTAL["total"] += total
        _TOTAL["calls"] += 1
        if model:
            _TOTAL["model"] = str(model)


def get():
    """Return a copy of the current run's usage (safe to serialise)."""
    with _LOCK:
        return dict(_TOTAL)
