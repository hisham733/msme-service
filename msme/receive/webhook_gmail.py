# =============================================================================
# FILE HEADER
# file    : msme/receive/webhook_gmail.py
# role    : Receive — Gmail Push webhook handler
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : verify the Pub/Sub OIDC token, decode the Gmail notification, dedupe it, turn the
#           mailbox history into message IDs and enqueue them for the single receive worker.
# pages   : n/a (backs POST /webhooks/gmail)
# calls   : config, db, creds, gmail, receive_queue, google.oauth2.id_token
# called  : dashboard.py route
# amend   : auth is mandatory — never process a push before the audience + service account match.
#           A disabled webhook answers 200 {"status":"disabled"} before any Gmail call (D41).
#           Failures: 401 bad token, 400 malformed body, 500 retryable (history/watch error).
#           Test: python3 -m unittest tests.test_webhook -v
# =============================================================================
"""Gmail Push notifications → queue.

Pub/Sub pushes a base64 body like ``{"emailAddress": "...", "historyId": "123"}``.
The real work is listed from Gmail history starting at the last ID we stored, so
a dropped or duplicated notification never loses an email.

Example:
    status, body = webhook_gmail.handle_push_request(
        "Bearer <google-id-token>", raw_pubsub_bytes)
    # -> (200, {"status": "queued", "messages": 1, ...})
"""
import base64
import json

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from msme import config, creds, db
from msme.receive import gmail, receive_queue


class WebhookAuthError(Exception):
    """The Pub/Sub OIDC token is missing, invalid, or from the wrong identity."""


class WebhookPayloadError(Exception):
    """The push body is not a Gmail Push notification (never retryable)."""


class WebhookRetryError(Exception):
    """A transient failure (history/watch) — Pub/Sub should redeliver."""


def bearer_token(authorization):
    """Extract the token from an `Authorization: Bearer <token>` header."""
    header = (authorization or "").strip()
    parts = header.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise WebhookAuthError("missing bearer token")
    return parts[1].strip()


def verify_push_token(token):
    """Verify the Google-signed OIDC token and return its claims.

    Enforces the configured audience and the Pub/Sub service-account email.
    """
    audience = (config.WEBHOOK_AUDIENCE or "").strip()
    expected = (config.WEBHOOK_SERVICE_ACCOUNT or "").strip()
    if not audience or not expected:
        raise WebhookAuthError("WEBHOOK_AUDIENCE/WEBHOOK_SERVICE_ACCOUNT are not configured")
    try:
        claims = id_token.verify_oauth2_token(
            token, google_requests.Request(), audience, clock_skew_in_seconds=30
        )
    except Exception as e:
        raise WebhookAuthError(f"token verification failed: {e}") from e
    if not claims.get("email_verified", False):
        raise WebhookAuthError("token email is not verified")
    if (claims.get("email") or "").lower() != expected.lower():
        raise WebhookAuthError(f"unexpected service account: {claims.get('email') or '(none)'}")
    return claims


def _json_body(body):
    if isinstance(body, dict):
        return body
    try:
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        return json.loads(body)
    except Exception as e:
        raise WebhookPayloadError("body is not valid JSON") from e


def decode_push(body):
    """Return (event_id, email_address, history_id) from a Pub/Sub push body."""
    body = _json_body(body)
    message = body.get("message") if isinstance(body, dict) else None
    if not isinstance(message, dict):
        raise WebhookPayloadError("missing message")
    data = message.get("data")
    if not data:
        raise WebhookPayloadError("missing message.data")
    try:
        raw = base64.b64decode(data + "=" * (-len(data) % 4))
        payload = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise WebhookPayloadError("message.data is not base64 JSON") from e
    if not isinstance(payload, dict):
        raise WebhookPayloadError("message.data is not an object")
    email_address = str(payload.get("emailAddress") or "").strip()
    history_id = str(payload.get("historyId") or "").strip()
    if not history_id:
        raise WebhookPayloadError("message.data has no historyId")
    event_id = str(message.get("messageId") or "").strip()
    if not event_id:
        event_id = f"{email_address}:{history_id}"
    return event_id, email_address, history_id


def _status_code(error):
    resp = getattr(error, "resp", None)
    return getattr(resp, "status", None) or getattr(error, "status_code", None)


def _history_too_old(error):
    code = _status_code(error)
    text = str(error).lower()
    return code == 404 or ("history" in text and ("expired" in text or "too old" in text))


def _current_unread(service):
    msgs = gmail.list_unread(service, query=config.GMAIL_QUERY)
    return [m["id"] for m in msgs]


def _resolve_new_ids(service, start_history_id, push_history_id):
    """Return (message IDs, latest history ID, mode).

    A missing/expired history cursor falls back to the unread inbox so a mailbox
    reset never silently drops the notification that triggered this run.
    """
    if not start_history_id:
        return _current_unread(service), push_history_id, "bootstrap"
    try:
        ids, latest = gmail.history_list(service, start_history_id)
        return ids, latest or push_history_id, "history"
    except Exception as e:
        if not _history_too_old(e):
            raise
        print(f"[webhook] history cursor {start_history_id} too old: {e}")
        return _current_unread(service), push_history_id, "recover"


def handle_push_request(authorization, body, service=None):
    """Verify + process one push. Returns (http_status, response_body)."""
    # A disabled webhook answers 200 so Pub/Sub does not retry; no Gmail call is made.
    if not receive_queue.webhook_enabled():
        return 200, {"status": "disabled"}
    try:
        verify_push_token(bearer_token(authorization))
    except WebhookAuthError as e:
        print(f"[webhook] rejected: {e}")
        return 401, {"error": "unauthorized"}
    try:
        event_id, email_address, push_history_id = decode_push(body)
    except WebhookPayloadError as e:
        print(f"[webhook] bad payload: {e}")
        return 400, {"error": str(e)}

    should_process, reason = db.begin_webhook_event(event_id, email_address, push_history_id)
    if not should_process:
        return 200, {"status": "duplicate", "event_id": event_id, "reason": reason}

    try:
        service = service or creds.gmail()
        state = db.get_gmail_watch() or {}
        start_history_id = str(state.get("history_id") or "")
        ids, latest, mode = _resolve_new_ids(service, start_history_id, push_history_id)
        queued = receive_queue.enqueue_ids(ids, source="webhook", event_id=event_id)
        db.save_gmail_watch(
            latest or push_history_id or start_history_id,
            state.get("expiration") or 0,
            state.get("topic") or config.GMAIL_PUBSUB_TOPIC,
        )
        db.finish_webhook_event(event_id, "done")
        print(f"[webhook] {event_id} {mode}: {len(ids)} id(s), {queued} queued")
        return 200, {
            "status": "queued",
            "event_id": event_id,
            "mode": mode,
            "messages": len(ids),
            "queued": queued,
            "history_id": latest,
        }
    except Exception as e:
        error = str(e)[:300]
        db.finish_webhook_event(event_id, "error", error)
        print(f"[webhook] {event_id} retryable: {error}")
        return 500, {"error": "retry"}
