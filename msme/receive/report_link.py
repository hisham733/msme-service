# =============================================================================
# FILE HEADER
# file    : msme/receive/report_link.py
# role    : Receive — N-3 report-link capture (report emails)
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : when an email offers a press release + a full report, find the report
#           URL (DOCX hyperlink rels, PDF /URI annotations, email-body links), score
#           the candidates, and return the linkType + url for the email_links store.
# pages   : n/a (backs the pipeline `report` stage)
# calls   : config, pypdf (lazy), zipfile/io/re
# called  : msme/receive/pipeline.py; msme/receive/gov_summary.py (shared extractor)
# amend   : no AI, no network; a miss is safe (normal article). The link is injected
#           into the published page at engine build time (never draft.md, which the
#           validator rejects for containing URLs).
#           Test: python3 -m unittest tests.test_report_link -v
# =============================================================================
"""N-3 report-link capture (docs/new-rules/N-3-report-link.md).

The report URL is not in the release paragraph text: in a DOCX it lives in
``word/_rels/document.xml.rels`` (Type=hyperlink), in a PDF in the page
``/Annots -> /A -> /URI``. We read both deterministically, add the email body
links, then score by path/anchor and pick the best public report URL.

Example:
    meta = report_link.detect(
        subject="Fifteen years of Digital reports ...",
        body=release_text,
        links=model["linksFound"],
        files={"release.docx": docx_bytes},
    )
    # -> {"linkType": "report",
    #     "url": "https://wearesocial.com/digital-2027",
    #     "candidates": [...], "detectedBy": "docx_rels", "confidence": 0.9}
"""
import io
import re
import zipfile

from msme import config

_REPORT_SIGNALS = (
    "full report", "insights report", "download the report", "read the report",
    "report", "insights", "survey", "whitepaper", "white paper",
)
_EXCLUDE_HOSTS = (
    "facebook.com", "twitter.com", "x.com", "instagram.com", "linkedin.com",
    "youtube.com", "tiktok.com", "pinterest.com", "wa.me", "whatsapp.com",
    "bit.ly", "t.co", "doubleclick.net", "google-analytics.com", "appspot.com",
)
_EXCLUDE_PATH = ("unsubscribe", "preferences", "privacy-policy", "terms", "cookie")

# (substring, points) — path/query hints that a URL points at a report.
_HINTS = (
    ("digital-20", 3), ("digital_20", 3),
    ("report", 2), ("insights", 2), ("survey", 2), ("whitepaper", 2), ("white-paper", 2),
    ("trends", 1), ("download", 1),
)


def _dedupe(items):
    seen, out = set(), []
    for u in items:
        u = str(u or "").strip().rstrip(".,;)")
        if not u.lower().startswith(("http://", "https://")) or u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def _strip_utm(url):
    """Drop utm_* query params (keep the rest of the URL)."""
    if "?" not in url:
        return url
    base, _, query = url.partition("?")
    keep = [p for p in query.split("&") if p and not p.lower().startswith("utm_")]
    return base + ("?" + "&".join(keep) if keep else "")


def _rels_hyperlinks(rels_xml):
    """Hyperlink Target values from a .rels document (attribute order independent)."""
    out = []
    for m in re.finditer(r"<Relationship\b[^>]*/?>", rels_xml):
        el = m.group(0)
        tm = re.search(r'Type="([^"]+)"', el)
        gm = re.search(r'Target="([^"]+)"', el)
        if tm and gm and tm.group(1).rstrip("/").endswith("/hyperlink"):
            out.append(gm.group(1))
    return out


def extract_docx_links(data):
    """Hyperlink targets from a DOCX (any *_rels part). Returns a deduped list."""
    out = []
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        for name in z.namelist():
            if not name.endswith(".rels"):
                continue
            try:
                rels = z.read(name).decode("utf-8", "replace")
            except Exception:
                continue
            out += _rels_hyperlinks(rels)
    except Exception:
        pass
    return _dedupe(out)


def extract_pdf_links(data):
    """URI annotation targets from a PDF (/Annots -> /A -> /URI), first pages only."""
    out = []
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        max_pages = min(len(reader.pages), max(1, int(config.REPORT_LINK_MAX_PDF_PAGES)))
        for page in list(reader.pages)[:max_pages]:
            try:
                annots = page.get("/Annots") or []
            except Exception:
                continue
            for a in annots:
                try:
                    obj = a.get_object()
                    action = obj.get("/A")
                    if action is None:
                        continue
                    action = action.get_object() if hasattr(action, "get_object") else action
                    uri = action.get("/URI")
                    if uri:
                        out.append(str(uri))
                except Exception:
                    continue
    except Exception:
        pass
    if not out:
        # fallback: raw /URI (…) strings (also lets tests use a small PDF byte blob)
        out = [m.decode("latin-1", "replace")
               for m in re.findall(rb"/URI\s*\((https?://[^)]+)\)", data or b"")]
    return _dedupe(out)


def score_url(url):
    """Score a URL for 'report-likeness'; negative = excluded."""
    u = (url or "").lower()
    if any(h in u for h in _EXCLUDE_HOSTS):
        return -99
    if any(p in u for p in _EXCLUDE_PATH):
        return -99
    score = 0
    for hint, pts in _HINTS:
        if hint in u:
            score += pts
    return score


def collect_candidates(files=None, links=None):
    """All candidate URLs from DOCX rels, PDF /URI, and the email body links."""
    files = files or {}
    out, detected_by = [], ""
    for name, data in files.items():
        low = (name or "").lower()
        if low.endswith((".docx", ".doc")):
            got = extract_docx_links(data)
            if got:
                out += got
                detected_by = detected_by or "docx_rels"
        elif low.endswith(".pdf"):
            got = extract_pdf_links(data)
            if got:
                out += got
                detected_by = detected_by or "pdf_uri"
    body_links = [u for u in (links or []) if isinstance(u, str)]
    if body_links:
        out += body_links
        detected_by = detected_by or "email_body"
    return _dedupe([_strip_utm(u) for u in out]), detected_by


def detect(subject="", body="", links=None, files=None):
    """Return the report link meta dict, or None for a normal article.

    A hit needs the subject/body to talk about a report AND at least one
    report-like URL (scored > 0). Cautious by design: no link -> normal path.
    """
    candidates, detected_by = collect_candidates(files=files, links=links)
    hay = f"{subject}\n{body}".lower()
    has_signal = any(s in hay for s in _REPORT_SIGNALS)
    if not has_signal:
        return None

    scored = [(u, score_url(u)) for u in candidates]
    positive = sorted([(u, s) for u, s in scored if s > 0], key=lambda x: -x[1])
    if not positive:
        return None

    best_url, best_score = positive[0]
    confidence = 0.9 if best_score >= 3 else 0.7
    return {
        "linkType": "report",
        "articleType": "report",
        "url": best_url,
        "source": detected_by or "email_body",
        "candidates": [u for u, _ in positive],
        "confidence": confidence,
    }
