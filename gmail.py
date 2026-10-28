# =============================================================================
# FILE HEADER
# file    : gmail.py
# role    : Receive — Gmail API client
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : list unread (query enforces is:unread unless explicitly disabled), get a message, parse its
#           payload, download attachments, mark read, send a reply, read thread headers.
# pages   : n/a
# calls   : creds (the service object is passed in); email/base64/time
# called  : pipeline, scheduler, normalize, reply, main, dashboard
# amend   : keep the throttle + GmailRateLimitError retry; parse_message is the email-model contract.
#           list_unread(unread_only=False) is only for the reply thread resolver.
#           Test: python3 -m unittest tools.test_gmail_unread -v; GET /api/emails
# =============================================================================
"""Gmail interaction: list unread, fetch message, download attachments, mark read.

All functions take a Google API `service` object (from creds.gmail()).

Example usage:
    svc = creds.gmail()
    for msg in gmail.list_unread(svc):
        print(msg["id"])          # e.g. "1a0ea6d2dad4b996"
        full = gmail.get_message(svc, msg["id"])
        parsed = gmail.parse_message(full["payload"])
        print(parsed["headers"]["subject"])
"""
import base64
import email
import re
import time
from email import policy

import creds

# --- Simple request throttle ------------------------------------------------
# Gmail's per-user rate limit is easy to trip with bursts (polling, run-all).
# A tiny token bucket keeps us at a safe ~15 requests/sec. It applies to every
# Gmail API call in this module.
_MAX_RPS = 15.0
_min_interval = 1.0 / _MAX_RPS
_last_req = [0.0]


def _throttle():
    """Sleep just enough to keep the call rate under ~15 req/s."""
    now = time.monotonic()
    wait = _last_req[0] + _min_interval - now
    if wait > 0:
        time.sleep(wait)
    _last_req[0] = time.monotonic()


class GmailRateLimitError(Exception):
    """Raised when Gmail returns HTTP 429 (user-rate limit exceeded)."""


def _execute(req):
    """Execute a Gmail API request, surfacing 429 as GmailRateLimitError.

    Other HTTP errors propagate as normal googleapiclient HttpError.
    """
    try:
        return req.execute()
    except Exception as e:
        code = getattr(e, "resp", None) and getattr(e.resp, "status", None)
        if code == 429 or "rateLimitExceeded" in str(e) or "User-rate limit exceeded" in str(e):
            raise GmailRateLimitError(str(e)) from e
        raise


_UNREAD_RE = re.compile(r"(?<!-)(?:is:unread|label:unread)\b", re.I)


def _unread_query(q):
    """Ensure a Gmail query asks for UNREAD messages; never duplicate the operator."""
    q = (q or "").strip()
    if not q:
        return "in:inbox is:unread -category:promotions"
    if _UNREAD_RE.search(q):
        return q
    return q + " is:unread"


def list_unread(service, query=None, max_results=50, unread_only=True):
    """Return [{id, threadId}] for UNREAD inbox messages matching the query.

    `unread_only=True` appends `is:unread` when the query lacks it. Pass False for
    a deliberate `in:anywhere`/thread lookup (the reply resolver).

    Example:
        gmail.list_unread(svc, "in:inbox is:unread -category:promotions")
        -> [{'id': '1a0ea6d2dad4b996', 'threadId': '1a0ea6d2dad4b996'}, ...]
    """
    _throttle()
    q = (query or "in:inbox -category:promotions").strip()
    if unread_only:
        q = _unread_query(q)
    result = _execute(
        service.users()
        .messages()
        .list(userId="me", q=q, maxResults=max_results)
    )
    return result.get("messages", [])


def get_message(service, msg_id, fmt="full"):
    """Fetch a full message (payload + all parts) by id."""
    _throttle()
    return _execute(service.users().messages().get(userId="me", id=msg_id, format=fmt))


def profile(service):
    """Return the connected mailbox profile (emailAddress, counts)."""
    return _execute(service.users().getProfile(userId="me"))


def watch(service, topic):
    """Start Gmail push notifications for INBOX to a Pub/Sub topic."""
    return _execute(service.users().watch(
        userId="me", body={"topicName": topic, "labelIds": ["INBOX"]}
    ))


def stop_watch(service):
    """Stop Gmail push notifications for this mailbox."""
    return _execute(service.users().stop(userId="me", body={}))


def history_list(service, start_history_id, max_results=500):
    """Return (new INBOX message IDs, latest historyId) since start_history_id."""
    ids, latest, token = [], [str(start_history_id or "")], None
    while True:
        params = {
            "userId": "me",
            "startHistoryId": str(start_history_id),
            "historyTypes": ["messageAdded"],
            "labelId": "INBOX",
            "maxResults": int(max_results),
        }
        if token:
            params["pageToken"] = token
        r = _execute(service.users().history().list(**params))
        latest[0] = str(r.get("historyId") or latest[0])
        for h in r.get("history", []) or []:
            for added in h.get("messagesAdded", []) or []:
                m = added.get("message", {}) or {}
                mid = m.get("id")
                labels = set(m.get("labelIds") or [])
                if mid and not ({"SENT", "DRAFT", "TRASH"} & labels) and mid not in ids:
                    ids.append(mid)
        token = r.get("nextPageToken")
        if not token:
            break
    return ids, latest[0]


def mark_read(service, msg_id):
    """Remove the UNREAD label so the message leaves the inbox queue."""
    _throttle()
    _execute(service.users().messages().modify(userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]}))


def _decode_body(part):
    """Gmail bodies are base64url-encoded — decode to utf-8 text."""
    data = part.get("body", {}).get("data")
    if not data:
        return ""
    raw = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
    return raw.decode("utf-8", "replace")


def parse_message(payload):
    """Walk a Gmail payload and return dict with headers, text, html, and attachments.

    Walks nested `parts` recursively (multipart/alternative, multipart/mixed).

    Example return:
        {
          "headers": {"subject": "...", "from": "...", "date": "..."},
          "text": "plain-text body",
          "html": "<html>...",
          "attachments": [
            {"filename": "press.docx", "mimeType": "...", "attachmentId": "...", "size": 12345}
          ],
        }
    """
    headers = {}
    if payload.get("headers"):
        for h in payload["headers"]:
            headers[h["name"].lower()] = h["value"]
    text = ""
    html = ""
    attachments = []

    def walk(part):
        nonlocal text, html
        mime = part.get("mimeType", "")
        filename = part.get("filename", "")
        body = part.get("body", {})
        if filename:
            att = {"filename": filename, "mimeType": mime}
            if body.get("attachmentId"):
                att["attachmentId"] = body["attachmentId"]
            att["size"] = body.get("size", 0)
            attachments.append(att)
        elif mime == "text/plain" and body.get("data"):
            text += _decode_body(part)
        elif mime == "text/html" and body.get("data"):
            html += _decode_body(part)
        for child in part.get("parts", []):
            walk(child)

    walk(payload)
    return {"headers": headers, "text": text, "html": html, "attachments": attachments}


def download_attachment(service, msg_id, attachment_id):
    """Download one attachment's bytes by its attachmentId.

    Example:
        gmail.download_attachment(svc, "1a0ea6d2dad4b996", "ANGEL123...")
        -> b"PK\x03\x04..."  (raw file bytes)
    """
    _throttle()
    result = _execute(
        service.users()
        .messages()
        .attachments()
        .get(userId="me", messageId=msg_id, id=attachment_id)
    )
    data = result.get("data", "")
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def get_thread_headers(service, msg_id):
    """Return the In-Reply-To/References/Message-ID of an existing message.

    Used to thread a reply into the same conversation as the original email.

    Example:
        gmail.get_thread_headers(svc, "1a0ea6d2dad4b996")
        -> {"message_id": "...", "references": "..."}
    """
    _throttle()
    msg = _execute(service.users().messages().get(userId="me", id=msg_id, format="metadata"))
    hdrs = {}
    for h in msg.get("payload", {}).get("headers", []):
        name = (h.get("name") or "").lower()
        if name in ("message-id", "references", "in-reply-to"):
            hdrs[name] = h.get("value", "")
    return hdrs


def send_message(service, to, subject, body, thread_id=None, msg_id=None):
    """Send an email via the Gmail API. Returns the sent message id.

    If `msg_id` is given, we pull the original Message-ID/References headers so
    the new mail lands in the same thread (a true reply). `thread_id` groups it
    under the same Gmail thread.

    Requires the Gmail scope to include send (mail.google.com covers it).

    Example:
        gmail.send_message(svc, "fhwvdu@gmail.com", "Re: ...", body,
                           thread_id="1a0ea6d2dad4b996", msg_id="1a0ea6d2dad4b996")
    """
    _throttle()
    msg = email.message.EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject

    # thread the reply into the original conversation
    if msg_id:
        orig = get_thread_headers(service, msg_id)
        if orig.get("message-id"):
            msg["In-Reply-To"] = orig["message-id"]
        refs = orig.get("references", "")
        if orig.get("message-id"):
            refs = (refs + " " + orig["message-id"]).strip()
        if refs:
            msg["References"] = refs

    msg.set_content(body)

    encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    send_body = {"raw": encoded}
    if thread_id:
        send_body["threadId"] = thread_id
    result = _execute(service.users().messages().send(userId="me", body=send_body))
    return result.get("id", "")