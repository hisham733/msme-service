# =============================================================================
# FILE HEADER
# file    : msme/receive/email_link.py
# role    : Receive — Gmail web links for a checklist row (N-6)
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : turn a Gmail message id / RFC822 Message-ID into clickable Gmail web links
#           so the checklist and editor can open the original email.
# pages   : checklist.html, editor.html (detail panels)
# calls   : config, settings_store
# called  : dashboard.checklist_json, editor_data._item_for
# amend   : never link a non-Gmail id; validate and URL-encode. Test: tests/test_email_link.py
# =============================================================================
"""Gmail web links for one email.

Two links are produced:

- ``emailUrl``       — ``https://mail.google.com/mail/u/<account>/#all/<message-id>``
- ``emailSearchUrl`` — ``https://mail.google.com/mail/u/<account>/#search/rfc822msgid:<id>``

The first is the short direct link; Gmail can fail to resolve it on a cold load. The
second searches by the email's own ``Message-ID`` header and is the durable fallback.

Example:
    gmail_urls("1a162cc0b30af0e7", "<CAM123@mail.gmail.com>")
    -> {"emailUrl": "https://mail.google.com/mail/u/0/#all/1a162cc0b30af0e7",
        "emailSearchUrl": "https://mail.google.com/mail/u/0/#search/rfc822msgid:CAM123%40mail.gmail.com"}
"""
import re
import urllib.parse

from msme import config, settings_store

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def _account():
    """The ``u/<account>`` segment: the connected mailbox or Gmail's account index."""
    try:
        value = settings_store.get("GMAIL_WEB_USER")
    except Exception:
        value = None
    user = str(value or config.GMAIL_WEB_USER or "0").strip() or "0"
    return urllib.parse.quote(user, safe="@.")


def gmail_urls(message_id, rfc822_message_id):
    """Return ``{"emailUrl": ..., "emailSearchUrl": ...}``; empty strings when unavailable."""
    out = {"emailUrl": "", "emailSearchUrl": ""}
    account = _account()
    mid = str(message_id or "").strip()
    if mid and _SAFE_ID.match(mid):
        out["emailUrl"] = f"https://mail.google.com/mail/u/{account}/#all/{mid}"
    rfc = str(rfc822_message_id or "").strip().strip("<>").strip()
    if rfc:
        encoded = urllib.parse.quote(rfc, safe="")
        out["emailSearchUrl"] = (
            f"https://mail.google.com/mail/u/{account}/#search/rfc822msgid:{encoded}"
        )
    return out


def enrich_row(row):
    """Add the two link keys to a checklist/editor row dict (in place) and return it."""
    row = row if isinstance(row, dict) else {}
    row.update(gmail_urls(row.get("messageId"), row.get("rfc822MessageId")))
    return row
