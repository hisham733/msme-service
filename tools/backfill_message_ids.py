# =============================================================================
# FILE HEADER
# file    : tools/backfill_message_ids.py
# role    : Maintenance — fill checklist.messageId for rows saved before N-6
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : match old checklist rows to pipeline_results by threadId and copy the Gmail message id,
#           so the "Open email" link appears on older rows too.
# pages   : n/a
# calls   : msme.db, msme.config
# called  : operator CLI
# amend   : read-only by default; --apply writes. Test: run once without --apply and read the plan.
# =============================================================================
"""Backfill Gmail message ids on old checklist rows (N-6).

New rows already store `messageId`; this tool fills rows created before N-6 using the
`pipeline_results` run that processed the same thread.

Usage:
    python3 tools/backfill_message_ids.py            # show what would change
    python3 tools/backfill_message_ids.py --apply    # write
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from msme import db


def main(apply=False):
    db.init_db()
    c = db._connect()
    results = c.execute(
        "select email_id, row from pipeline_results order by rowid desc"
    ).fetchall()
    by_thread = {}
    for r in results:
        try:
            row = json.loads(r["row"] or "{}")
        except Exception:
            continue
        tid = str(row.get("threadId") or "").strip()
        mid = str(r["email_id"] or "").strip()
        if tid and mid and tid not in by_thread:
            by_thread[tid] = mid

    targets = c.execute(
        "select id, threadId from checklist where (messageId is null or messageId='')"
    ).fetchall()
    plan = []
    for t in targets:
        tid = str(t["threadId"] or "").strip()
        mid = by_thread.get(tid, "")
        if mid:
            plan.append((t["id"], mid))
    print(f"checklist rows missing messageId: {len(targets)}")
    print(f"backfillable from pipeline_results: {len(plan)}")
    for cid, mid in plan[:20]:
        print(f"  checklist {cid} -> {mid}")
    if apply and plan:
        c.executemany("update checklist set messageId=? where id=?", [(m, i) for i, m in plan])
        c.commit()
        print(f"updated: {len(plan)}")
    elif plan:
        print("dry run — add --apply to write")
    c.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Backfill checklist.messageId from pipeline_results")
    ap.add_argument("--apply", action="store_true", help="write the updates")
    args = ap.parse_args()
    main(apply=args.apply)
