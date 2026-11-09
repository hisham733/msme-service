# =============================================================================
# FILE HEADER
# file    : tools/backfill_emails.py
# role    : Maintenance — fill the compact `emails` table for old checklist rows
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : fetch each checklist message id from Gmail once, then record its envelope in `emails`
#           (from, subject, received_at, links, attachment count) so the by-sender dashboard works.
# pages   : backs the /by-email.html page (indirectly)
# calls   : msme.creds, msme.receive.gmail, msme.receive.normalize, msme.db
# called  : operator CLI
# amend   : needs a valid Gmail token. Read-only on Gmail; --apply writes only the local `emails` table.
#           Test: run once without --apply and read the plan.
# =============================================================================
"""Backfill `emails` from Gmail for old checklist rows (by-sender dashboard).

Usage:
    python3 tools/backfill_emails.py                 # show what would be fetched
    python3 tools/backfill_emails.py --apply         # fetch + write
    python3 tools/backfill_emails.py --apply --limit 20

The email's own Date header becomes `received_at` (not the backfill time), so the
dashboard timeline stays correct.
"""
import argparse
import sys
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from msme import creds, db
from msme.receive import gmail, normalize


def _iso_date(raw):
    try:
        dt = parsedate_to_datetime(str(raw or ""))
    except Exception:
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def main(apply=False, limit=0):
    db.init_db()
    c = db._connect()
    rows = c.execute(
        """select distinct c.messageId
           from checklist c
           left join emails e on e.message_id = c.messageId
           where c.messageId is not null and c.messageId != '' and e.message_id is null
           order by c.id desc"""
    ).fetchall()
    c.close()
    targets = [r["messageId"] for r in rows]
    if limit:
        targets = targets[:int(limit)]
    print(f"checklist messages missing from emails: {len(rows)}")
    print(f"this run: {len(targets)}")
    if not apply:
        for mid in targets[:20]:
            print(f"  would fetch {mid}")
        if targets:
            print("dry run — add --apply to fetch and write")
        return

    service = creds.gmail()
    ok = failed = 0
    for i, mid in enumerate(targets, 1):
        try:
            model = normalize.build_email_model(service, mid)
            db.save_email(model, received_at=_iso_date(model.get("date")))
            ok += 1
        except Exception as e:
            failed += 1
            print(f"  {mid}: {str(e)[:140]}")
        if i % 10 == 0:
            print(f"  … {i}/{len(targets)}")
    print(f"done: written={ok} failed={failed}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Backfill the emails table from Gmail")
    ap.add_argument("--apply", action="store_true", help="fetch from Gmail and write")
    ap.add_argument("--limit", type=int, default=0, help="max messages this run")
    args = ap.parse_args()
    main(apply=args.apply, limit=args.limit)
