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

from msme import config, creds, db
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


def ensure_watch():
    """Create/renew Gmail push watch when a Pub/Sub topic is configured."""
    topic = (config.GMAIL_PUBSUB_TOPIC or "").strip()
    if not topic:
        return None
    state = db.get_gmail_watch()
    now_ms = int(time.time() * 1000)
    if state and int(state.get("expiration") or 0) > now_ms + 24 * 3600 * 1000:
        return state
    service = creds.gmail()
    r = gmail.watch(service, topic)
    db.save_gmail_watch(r.get("historyId", ""), r.get("expiration", 0), topic)
    print(f"[webhook] watch renewed history={r.get('historyId')} expires={r.get('expiration')}")
    return r


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
            if ensure_watch() is None:
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
    if config.ENABLE_WEBHOOK or config.GMAIL_PUBSUB_TOPIC:
        threading.Thread(target=_renew_loop, name="gmail-watch", daemon=True).start()
