# =============================================================================
# FILE HEADER
# file    : msme/receive/receive_queue.py
# role    : Receive — one-at-a-time Gmail message queue
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : accept message IDs from Gmail Push or polling, claim one row, run the existing
#           pipeline, save the checklist row, mark read, and record the outcome.
# pages   : n/a (backs the webhook and scheduler)
# calls   : db, creds, gmail, pipeline, checklist
# called  : combined.py startup; scheduler.py; webhook_gmail.py
# amend   : one worker only; never run two articles in parallel. All state is in SQLite so a
#           restart recovers queued/running rows. Test: python3 -m unittest tests.test_webhook
# =============================================================================
"""One-at-a-time receive queue shared by Gmail Push and polling."""
import threading
import time

from msme import config, creds, db, settings_store
from msme.receive import gmail, pipeline
from msme.receive.checklist import save_checklist

_started = False
_lock = threading.Lock()


def enqueue_ids(message_ids, source="webhook", event_id=""):
    return db.enqueue_webhook_messages(message_ids, source=source, event_id=event_id)


def enqueue_unread(source="poll", query=None):
    """List current unread Gmail messages and enqueue them."""
    service = creds.gmail()
    msgs = gmail.list_unread(service, query=query or config.GMAIL_QUERY)
    return enqueue_ids([m["id"] for m in msgs], source=source), msgs


def webhook_enabled():
    """The live on/off flag (runtime setting first, env default second)."""
    try:
        value = settings_store.get("ENABLE_WEBHOOK")
    except Exception:
        value = None
    return bool(config.ENABLE_WEBHOOK if value is None else value)


def webhook_topic():
    """The live Pub/Sub topic (runtime setting first, env default second)."""
    try:
        value = settings_store.get("GMAIL_PUBSUB_TOPIC")
    except Exception:
        value = None
    return str(value or config.GMAIL_PUBSUB_TOPIC or "").strip()


def ensure_watch(force=False):
    """Create/renew the Gmail push watch when the webhook is ON and a topic is set."""
    topic = webhook_topic()
    if not webhook_enabled() or not topic:
        return None
    state = db.get_gmail_watch()
    now_ms = int(time.time() * 1000)
    if not force and state and int(state.get("expiration") or 0) > now_ms + 24 * 3600 * 1000:
        return state
    service = creds.gmail()
    r = gmail.watch(service, topic)
    db.save_gmail_watch(r.get("historyId", ""), r.get("expiration", 0), topic)
    print(f"[webhook] watch renewed history={r.get('historyId')} expires={r.get('expiration')}")
    return r


def stop_watch():
    """Stop Gmail push notifications and forget the stored cursor."""
    service = creds.gmail()
    try:
        gmail.stop_watch(service)
    finally:
        db.clear_gmail_watch()


def apply_webhook(enabled):
    """Persist the flag and create/stop the Gmail watch immediately.

    The flag is saved even when the Gmail call fails, so the app-side gate and the
    UI stay truthful; the returned `error` tells the operator what is still wrong.
    """
    settings_store.save({"ENABLE_WEBHOOK": bool(enabled)})
    if not enabled:
        error = ""
        try:
            stop_watch()
        except Exception as e:  # noqa: BLE001 — the flag is already off
            error = str(e)[:300]
        return {"enabled": False, "topic": webhook_topic(), "watch": None, "error": error}
    topic = webhook_topic()
    if not topic:
        return {"enabled": True, "topic": "", "watch": None,
                "error": "GMAIL_PUBSUB_TOPIC is empty"}
    try:
        r = ensure_watch(force=True) or {}
        return {
            "enabled": True,
            "topic": topic,
            "watch": {"history_id": r.get("historyId", ""),
                      "expiration": r.get("expiration", 0)},
            "error": "",
        }
    except Exception as e:  # noqa: BLE001
        return {"enabled": True, "topic": topic, "watch": None, "error": str(e)[:300]}


def process_one():
    """Claim and process one queued message. Returns True when work was done."""
    item = db.claim_webhook_message()
    if not item:
        return False
    mid = item["message_id"]
    try:
        service = creds.gmail()
        row = pipeline.process_email(service, mid)
        save_checklist(row)
        try:
            gmail.mark_read(service, mid)
        except Exception as e:
            print(f"[queue] mark read failed {mid}: {e}")
        db.finish_webhook_message(mid, "done")
        print(f"[queue] processed {mid}: {row.get('subject', '')[:60]}")
    except Exception as e:
        err = str(e)[:300]
        db.finish_webhook_message(mid, "error", err)
        print(f"[queue] failed {mid}: {err}")
    return True


def _worker():
    while True:
        try:
            if not process_one():
                time.sleep(2)
        except Exception as e:
            print(f"[queue] worker error: {e}")
            time.sleep(3)


def _renew_loop():
    while True:
        delay = 6 * 3600
        try:
            if not webhook_enabled():
                delay = 3600
            elif ensure_watch() is None:
                delay = 3600
        except Exception as e:
            print(f"[webhook] watch renewal failed: {e}")
            delay = 300
        time.sleep(delay)


def start():
    """Start the worker and watch-renewal threads once."""
    global _started
    with _lock:
        if _started:
            return
        _started = True
    db.recover_webhook_queue()
    threading.Thread(target=_worker, name="receive-queue", daemon=True).start()
    threading.Thread(target=_renew_loop, name="gmail-watch", daemon=True).start()
