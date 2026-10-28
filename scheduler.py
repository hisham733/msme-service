# =============================================================================
# FILE HEADER
# file    : scheduler.py
# role    : Receive — background auto-poll
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : when ENABLE_AUTO is true, poll Gmail every SCHEDULE_MINUTES and ENQUEUE each unread email for the
#           single receive worker (the webhook and polling share one queue, so nothing runs twice).
# pages   : n/a
# calls   : config, receive_queue, settings_store; apscheduler
# called  : run.py main() (started at boot; no-op when disabled)
# amend   : OFF by default and must stay single-worker. Change cadence via settings, not code.
#           Test: python3 -m unittest tools.test_webhook -v
# =============================================================================
"""Auto-poll scheduler. Off unless ENABLE_AUTO=true (single uvicorn worker!).

When enabled, it polls Gmail every SCHEDULE_MINUTES minutes and enqueues every
unread message. The shared receive queue processes them one at a time, so a poll
that overlaps a webhook never processes the same email twice.

Example config to turn it on:
    settings_store.save({"ENABLE_AUTO": True, "SCHEDULE_MINUTES": 5})
"""
import config
import receive_queue
import settings_store


def poll_and_process():
    """One poll cycle: enqueue ALL unread emails matching the query.

    The queue dedupes message IDs; the worker saves the checklist row and marks
    each email read. A failure on one email does not stop the others.
    """
    try:
        queued, msgs = receive_queue.enqueue_unread(
            source="poll",
            query=settings_store.get("GMAIL_QUERY") or config.GMAIL_QUERY,
        )
        print(f"[auto] poll: {len(msgs)} unread, {queued} newly queued")
    except Exception as e:
        print(f"[auto] poll failed: {e}")


def start():
    """Start the background scheduler if ENABLE_AUTO is true; else no-op.

    Returns the BackgroundScheduler, or None when disabled.
    """
    if not (settings_store.get("ENABLE_AUTO") or False):
        print("[scheduler] disabled (ENABLE_AUTO=false)")
        return None
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        poll_and_process,
        "interval",
        minutes=int(settings_store.get("SCHEDULE_MINUTES") or config.SCHEDULE_MINUTES),
        id="poll_gmail",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    print(f"[scheduler] polling every {settings_store.get('SCHEDULE_MINUTES')} min")
    return scheduler