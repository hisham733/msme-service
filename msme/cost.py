# =============================================================================
# FILE HEADER
# file    : msme/cost.py
# role    : Shared — estimated token cost for one receive → filter → repurpose chain
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : turn stored token usage (pipeline tokens, Jev usage, engine usage) into USD at the
#           editable, measured rates; build the chain/all-runs summary for the AI Model page.
# pages   : backs /api/costs.json (the AI Model → Cost tab)
# calls   : settings_store
# called  : dashboard.py
# amend   : prices are settings, never hardcoded in a page; a model with no rate is flagged, not $0.
#           Test: python3 -m unittest tests.test_cost -v
# =============================================================================
"""Cost estimation for the pipeline.

Rates are editable settings and default to the measured values in
`docs/operations/PROCESS-TOKEN-COST.md`:

    COST_DEEPSEEK_PER_M  = 0.65   USD per 1M total tokens (D27 measured blended rate)
    COST_JEV_INPUT_PER_M = 0.042  USD per 1M input tokens (output free)
    COST_GEMINI_PER_M    = 0.65   fallback when the provider is Gemini
    COST_BUDGET_USD      = 0      manual credit/budget; 0 = bar hidden

A rate of 0 means "not priced" — the amount is still returned but `priced` is False
so the UI can show a warning instead of a confident $0.
"""
from datetime import datetime, timedelta, timezone

from msme import settings_store

CURRENCY = "USD"


def _num(key, default):
    try:
        value = settings_store.get(key)
        if value is None or value == "":
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def prices():
    """Return the live price table (USD)."""
    return {
        "currency": CURRENCY,
        "deepseek_per_m": _num("COST_DEEPSEEK_PER_M", 0.65),
        "jev_input_per_m": _num("COST_JEV_INPUT_PER_M", 0.042),
        "gemini_per_m": _num("COST_GEMINI_PER_M", 0.65),
        "budget_usd": _num("COST_BUDGET_USD", 0.0),
    }


def _model_lower(model):
    return str(model or "").lower()


def _usage_int(usage, *keys):
    for key in keys:
        try:
            value = (usage or {}).get(key)
            if value not in (None, ""):
                return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def receive_cost(tokens, model=""):
    """USD for a receive run's prompt+completion tokens."""
    tokens = tokens or {}
    total = _usage_int(tokens, "total", "total_tokens")
    if total <= 0:
        total = _usage_int(tokens, "prompt", "completion")
    if total <= 0:
        return 0.0
    p = prices()
    rate = p["gemini_per_m"] if "gemini" in _model_lower(model) else p["deepseek_per_m"]
    return total / 1_000_000.0 * rate


def filter_cost(usage, model=""):
    """USD for one filter result (Jev is input-priced; other models use the blended rate)."""
    usage = usage or {}
    inp = _usage_int(usage, "input_tokens", "prompt_tokens", "prompt")
    out = _usage_int(usage, "output_tokens", "completion_tokens", "completion", "total_tokens", "total")
    p = prices()
    low = _model_lower(model)
    if "jev" in low or "typesafe" in low:
        return inp / 1_000_000.0 * p["jev_input_per_m"]
    rate = p["gemini_per_m"] if "gemini" in low else p["deepseek_per_m"]
    return (inp + out) / 1_000_000.0 * rate


def repurpose_cost(usage, model=""):
    """USD for one repurpose engine run (DeepSeek/Gemini chat + vision tokens)."""
    return receive_cost(usage, model)


def total_cost(receive=0.0, filter=0.0, repurpose=0.0):
    return float(receive or 0) + float(filter or 0) + float(repurpose or 0)


def _latest(rows, key):
    """Keep the newest row per key (rows must carry created_at/finished_at)."""
    out = {}
    for row in rows or []:
        k = row.get(key)
        if not k:
            continue
        stamp = row.get("created_at") or row.get("finished_at") or row.get("updated_at") or ""
        old = out.get(k)
        old_stamp = (old.get("created_at") or old.get("finished_at") or old.get("updated_at") or "") if old else ""
        if old is None or str(stamp) > str(old_stamp):
            out[k] = row
    return out


def _email_key(row):
    return row.get("email_id") or row.get("messageId") or ""


def build_rows(receive_rows, filter_rows, repurpose_rows):
    """One cost row per email, joining the latest stage result for that email."""
    latest_receive = _latest(receive_rows, "email_id")
    latest_filter = _latest(filter_rows, "messageId")
    latest_repo = _latest(repurpose_rows, "messageId")

    keys = set(latest_receive) | set(latest_filter) | set(latest_repo)
    rows = []
    for key in keys:
        rec = latest_receive.get(key) or {}
        fil = latest_filter.get(key) or {}
        rep = latest_repo.get(key) or {}
        r_cost = receive_cost(rec.get("tokens") or {}, rec.get("model"))
        f_cost = filter_cost(fil.get("usage") or {}, fil.get("model"))
        p_cost = repurpose_cost(rep.get("usage") or {}, rep.get("model"))
        status = str(rep.get("status") or "").lower()
        rows.append({
            "email_id": key,
            "subject": rec.get("subject") or fil.get("subject") or rep.get("subject") or "",
            "receive_model": rec.get("model") or "",
            "receive_cost": round(r_cost, 6),
            "receive_at": rec.get("created_at") or "",
            "filter_model": fil.get("model") or "",
            "filter_cost": round(f_cost, 6),
            "filter_at": fil.get("created_at") or "",
            "filter_outcome": fil.get("outcome") or "",
            "repurpose_model": rep.get("model") or "",
            "repurpose_cost": round(p_cost, 6),
            "repurpose_at": rep.get("finished_at") or rep.get("updated_at") or "",
            "repurpose_status": rep.get("status") or "",
            "published": bool(rep) and status in ("validated", "rendered", "done"),
            "repurpose_priced": bool((rep.get("usage") or {}).get("total")),
            "total_cost": round(total_cost(r_cost, f_cost, p_cost), 6),
            "emailUrl": rec.get("emailUrl") or fil.get("emailUrl") or rep.get("emailUrl") or "",
            "emailSearchUrl": (rec.get("emailSearchUrl") or fil.get("emailSearchUrl")
                               or rep.get("emailSearchUrl") or ""),
        })
    rows.sort(key=lambda r: (-r["total_cost"], r["email_id"]))
    return rows


def paginate(rows, page=1, page_size=20, q=""):
    """Slice the cost rows for one page; returns (rows, total, page, pages, page_size).

    The API returns only this slice so the browser never receives every record; the
    summary (cards) is still computed once from the full set.
    """
    try:
        page = max(1, int(page))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = max(1, min(100, int(page_size)))
    except (TypeError, ValueError):
        page_size = 20
    query = str(q or "").strip().lower()
    if query:
        rows = [r for r in rows
                if query in str(r.get("email_id") or "").lower()
                or query in str(r.get("subject") or "").lower()]
    total = len(rows)
    pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, pages)
    start = (page - 1) * page_size
    return rows[start:start + page_size], total, page, pages, page_size


def _sum(rows, field):
    return round(sum(float(r.get(field) or 0) for r in rows), 6)


def _day(stamp):
    return str(stamp or "")[:10]


def daily_totals(receive_rows, filter_rows, repurpose_rows, days=14):
    """Daily spend for the last `days` calendar days (UTC), zero-filled, oldest first."""
    by_day = {}
    for r in receive_rows or []:
        d = _day(r.get("created_at"))
        if d:
            by_day[d] = by_day.get(d, 0.0) + receive_cost(r.get("tokens") or {}, r.get("model"))
    for r in filter_rows or []:
        d = _day(r.get("created_at"))
        if d:
            by_day[d] = by_day.get(d, 0.0) + filter_cost(r.get("usage") or {}, r.get("model"))
    for r in repurpose_rows or []:
        d = _day(r.get("finished_at") or r.get("updated_at"))
        if d:
            by_day[d] = by_day.get(d, 0.0) + repurpose_cost(r.get("usage") or {}, r.get("model"))
    today = datetime.now(timezone.utc).date()
    out = []
    for offset in range(days - 1, -1, -1):
        d = (today - timedelta(days=offset)).isoformat()
        out.append({"date": d, "total": round(by_day.get(d, 0.0), 6)})
    return out


def build_summary(receive_rows, filter_rows, repurpose_rows):
    """Totals for the Cost tab: all runs, latest-per-email chain, stages, tokens, budget."""
    rows = build_rows(receive_rows, filter_rows, repurpose_rows)
    chain_receive = _sum(rows, "receive_cost")
    chain_filter = _sum(rows, "filter_cost")
    chain_repurpose = _sum(rows, "repurpose_cost")
    chain_total = round(chain_receive + chain_filter + chain_repurpose, 6)

    all_receive = round(sum(receive_cost(r.get("tokens") or {}, r.get("model"))
                            for r in (receive_rows or [])), 6)
    all_filter = round(sum(filter_cost(r.get("usage") or {}, r.get("model"))
                           for r in (filter_rows or [])), 6)
    all_repurpose = round(sum(repurpose_cost(r.get("usage") or {}, r.get("model"))
                              for r in (repurpose_rows or [])), 6)
    all_total = round(all_receive + all_filter + all_repurpose, 6)

    emails = len(rows)
    published = [r for r in rows if r["published"]]
    avg_email = round(chain_total / emails, 6) if emails else 0.0
    avg_published = round(chain_repurpose / len(published), 6) if published else 0.0

    most = max(rows, key=lambda r: r["total_cost"], default=None)
    p = prices()
    budget = float(p["budget_usd"] or 0)
    remaining = round(budget - all_total, 6) if budget > 0 else None
    emails_left = int(remaining / avg_email) if (remaining is not None and avg_email > 0) else None

    tokens = {
        "receive_prompt": sum(_usage_int((r.get("tokens") or {}), "prompt") for r in (receive_rows or [])),
        "receive_completion": sum(_usage_int((r.get("tokens") or {}), "completion") for r in (receive_rows or [])),
        "receive_total": sum(_usage_int((r.get("tokens") or {}), "total") for r in (receive_rows or [])),
        "filter_input": sum(_usage_int((r.get("usage") or {}), "input_tokens", "prompt") for r in (filter_rows or [])),
        "filter_output": sum(_usage_int((r.get("usage") or {}), "output_tokens", "completion") for r in (filter_rows or [])),
        "repurpose_total": sum(_usage_int((r.get("usage") or {}), "total") for r in (repurpose_rows or [])),
    }

    unpriced = [r["email_id"] for r in rows if r.get("repurpose_status") and not r.get("repurpose_priced")]

    return {
        "currency": CURRENCY,
        "prices": p,
        "all_runs": {
            "receive": all_receive, "filter": all_filter,
            "repurpose": all_repurpose, "total": all_total,
        },
        "chain": {
            "receive": chain_receive, "filter": chain_filter,
            "repurpose": chain_repurpose, "total": chain_total,
        },
        "emails": emails,
        "published": len(published),
        "avg_per_email": avg_email,
        "avg_per_published": avg_published,
        "most_expensive": most,
        "daily": daily_totals(receive_rows, filter_rows, repurpose_rows),
        "tokens": tokens,
        "budget": {
            "usd": budget if budget > 0 else None,
            "remaining": remaining,
            "emails_left": emails_left,
        },
        "unpriced_repurpose": unpriced[:20],
    }
