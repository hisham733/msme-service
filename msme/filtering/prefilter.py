# =============================================================================
# FILE HEADER
# file    : msme/filtering/prefilter.py
# role    : Filter — deterministic pre-checks (no AI)
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : compute date staleness, contact details and sponsored/advertorial string signals for the verdict.
# pages   : n/a
# calls   : datetime, re
# called  : filter.py (lazy; result goes into verdict.deterministic)
# amend   : pure functions, no network; add a check in `run()` and its key is read by the pages/reports.
#           Test: python3 -c "import prefilter; print(prefilter.run({'bodyText':'KUALA LUMPUR'}))"
# =============================================================================
"""Deterministic pre-filter checks for the Jev filter.

These are things a model is weak at or that need external data: date staleness,
contact details, and sponsored/advertorial string signals. They are computed in
code (no AI) and added to the verdict as `deterministic`.

Example:
    prefilter.run(article, prep)
    -> {"stale": {...}, "contacts": {...}, "sponsored": {...}}
"""
import datetime as _dt
import re

_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
# Malaysian phone numbers: 01x-xxxxxxx, +60..., 03-xxxx xxxx
PHONE_RE = re.compile(r"(?:\+?60[\s\-]?)?0?1\d[\s\-]?\d{3,4}[\s\-]?\d{4}|\+?60[\s\-]?\d{1,2}[\s\-]?\d{3,4}[\s\-]?\d{4}")

_SPONSORED_PATTERNS = {
    "backlink": r"\b(back\s?link|link\s?back|dofollow|do-follow|anchor\s?text)\b",
    "seo_placement": r"\b(seo\s+placement|for\s+seo|guest\s+post|link\s+placement|paid\s+link)\b",
    "promo_code": r"\b(promo\s?code|discount\s?code|coupon\s?code|voucher\s?code|promo\s?code)\b",
    "guaranteed_publication": r"\b(guarantee[ds]?\s+(to\s+)?publish|guaranteed\s+publication|in\s+exchange\s+for\s+(a\s+)?(link|backlink|coverage)|we\s+will\s+publish\s+if)\b",
    "paid_placement": r"\b(paid\s+(post|placement|article)|sponsored\s+(post|article|content)|advertorial)\b",
}


def parse_date(text, default_year=None):
    """Best-effort parse of a date string -> datetime.date | None.

    Handles: '2026-10-01', '24 September 2026', 'Wed, 30 Sep 2026',
    'Thu, 1 Oct' (uses default_year/current year).
    """
    if not text:
        return None
    s = str(text).strip()
    # ISO yyyy-mm-dd
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        try:
            return _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    # dd Month yyyy  OR  Month dd, yyyy  (year optional)
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3,9})\.?\s*(\d{4})?", s)
    if not m:
        m = re.search(r"([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s*(\d{4})?", s)
        if m:
            mon = _MONTHS.get(m.group(1).lower())
            day = int(m.group(2)); year = int(m.group(3)) if m.group(3) else (default_year or _dt.date.today().year)
            if mon:
                try:
                    return _dt.date(year, mon, day)
                except ValueError:
                    return None
    else:
        mon = _MONTHS.get(m.group(2).lower())
        day = int(m.group(1)); year = int(m.group(3)) if m.group(3) else (default_year or _dt.date.today().year)
        if mon:
            try:
                return _dt.date(year, mon, day)
            except ValueError:
                return None
    return None


def staleness(article, prep=None, today=None, max_days=180):
    """Return {'is_stale', 'days_old', 'parsed', 'source'} from the article date."""
    today = today or _dt.date.today()
    prep = prep or {}
    candidates = []
    if article.get("date"):
        candidates.append(("article.date", article["date"]))
    for d in (prep.get("dates") or [])[:3]:
        candidates.append(("prep.dates", d))
    for source, raw in candidates:
        parsed = parse_date(raw, default_year=today.year)
        if parsed:
            days = (today - parsed).days
            return {"is_stale": days > max_days, "days_old": days,
                    "parsed": parsed.isoformat(), "source": source}
    return {"is_stale": False, "days_old": None, "parsed": None, "source": None}


def contacts(text, prep=None):
    """Return {'emails', 'phones', 'has_contact'} found in the text/prep."""
    prep = prep or {}
    t = (text or "") + " " + " ".join(prep.get("dates") or [])  # keep cheap
    emails = list(dict.fromkeys([e for e in (prep.get("contacts", {}).get("emails") or [])] + EMAIL_RE.findall(text or "")))
    phones = list(dict.fromkeys(PHONE_RE.findall(text or "")[:10]))
    media = (prep.get("contacts", {}) or {}).get("media_contact", "")
    return {"emails": emails[:10], "phones": phones[:10],
            "media_contact": media, "has_contact": bool(emails or phones or media)}


def sponsored_signals(text, links=None, prep=None):
    """Return {signal: [matched snippets]} for sponsored/advertorial strings."""
    blob = ((text or "") + " " + " ".join(links or []) + " " + " ".join((prep or {}).get("links") or [])).lower()
    out = {}
    for name, pat in _SPONSORED_PATTERNS.items():
        hits = re.findall(pat, blob)
        if hits:
            out[name] = list(dict.fromkeys([h if isinstance(h, str) else " ".join(h) for h in hits]))[:5]
    return out


def run(article, prep=None):
    """Run all deterministic checks and return a single dict."""
    text = article.get("bodyText", "") or ""
    return {
        "stale": staleness(article, prep),
        "contacts": contacts(text, prep),
        "sponsored": sponsored_signals(text, prep=prep),
    }
