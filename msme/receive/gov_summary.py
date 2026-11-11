# =============================================================================
# FILE HEADER
# file    : msme/receive/gov_summary.py
# role    : Receive — N-4 government/budget speech capture (capture-only)
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : detect a budget/government email with a speech link and capture the
#           speech URL for the email_links store. Capture-only: it never fetches the
#           speech and never turns an email without an article into a published one.
# pages   : n/a (backs the pipeline `government` stage)
# calls   : report_link (shared hyperlink extractor)
# called  : msme/receive/pipeline.py
# amend   : the summary-vs-speech rule is deferred to MSME (N-4 decision B); do NOT
#           add a threshold or a fetch here until the call answers it.
#           Test: python3 -m unittest tests.test_report_link -v
# =============================================================================
"""N-4 government/budget speech URL capture (docs/new-rules/N-4-government-summary.md).

Capture-only by design: the priority of the email summary over the speech (and the
fetch of the speech) is MSME decision B and is not implemented yet. This records the
speech URL so the case can be picked up once the rule is decided.

Example:
    meta = gov_summary.capture(subject="Budget 2027 POV ...", body=body,
                               links=model["linksFound"], from_email="news@ellerton.co")
    # -> {"linkType": "speech", "url": "https://www.kabinet.gov.my/ucapan/...", ...}
"""
from msme.receive import report_link

_GOV_MARKERS = (
    "budget", "belanjawan", "madani", "speech", "ucapan", "minister", "menteri",
    "kementerian", "government", "pov",
)
_SPEECH_HINTS = (
    "speech", "ucapan", "text-of-speech", "pidato", "minister", "menteri",
    "kementerian", "/pm",
)


def capture(subject="", body="", links=None, files=None, from_email=""):
    """Return a speech-link meta dict (capture-only), or None.

    Fires when the email has a government/budget marker AND a speech-like link.
    Never fetches the speech and never changes the article/needs-human decision.
    """
    hay = f"{subject}\n{body}".lower()
    gov = any(m in hay for m in _GOV_MARKERS) or (from_email or "").lower().endswith(".gov.my")
    if not gov:
        return None

    candidates, detected_by = report_link.collect_candidates(files=files, links=links)
    speech = [u for u in candidates
              if any(h in u.lower() for h in _SPEECH_HINTS)]
    if not speech:
        return None
    return {
        "linkType": "speech",
        "url": speech[0],
        "source": detected_by or "email_body",
        "candidates": speech,
        "confidence": 0.7,
    }
