#!/usr/bin/env python3
"""Backfill the repurpose tables from the inbox + export manifest.

`data/repurpose_export.json` and each `repurpose_inbox/<folder>/run.json` are the
folder contract; this rebuilds the DB mirror (`repurpose_exports`, `repurpose_runs`,
`repurpose_events`) and the P0-1 rows (`validation_results`, `images`) with
`article_id = checklist.id` as the canonical key.

Usage:
    python3 tools/backfill_repurpose.py          # dry-run
    python3 tools/backfill_repurpose.py --apply  # write

Idempotent: validation results / images for an article are replaced, and a folder's
backfill event is written once.
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from msme import db, paths

INBOX = paths.REPURPOSE_INBOX
MANIFEST = paths.DATA / "repurpose_export.json"


def _manifest():
    try:
        data = json.loads(Path(MANIFEST).read_text(encoding="utf-8"))
        return data.get("exported") or []
    except Exception:
        return []


def _run(folder):
    try:
        return json.loads((Path(INBOX) / folder / "run.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def _folder_of(rec):
    return rec.get("folder") or os.path.basename(rec.get("dest") or "")


def _item(rec, run, folder, cid):
    validator = run.get("validator") or {}
    return {
        "checklist_id": cid,
        "folder": folder,
        "dest": rec.get("dest") or str(Path(INBOX) / folder),
        "filter_result_id": rec.get("filter_result_id"),
        "status": run.get("status") or rec.get("status") or "pending",
        "model": run.get("model") or "",
        "usage": run.get("usage") or {},
        "validator": validator,
        "started_at": run.get("started") or run.get("started_at") or "",
        "finished_at": run.get("finished") or run.get("finished_at") or run.get("updated") or "",
        "article_hash": rec.get("article_hash") or "",
        "config_hash": rec.get("config_hash") or "",
        "weighted": rec.get("weighted"),
        "image_file": run.get("image_file") or "",
        "image_rung": run.get("image_rung") or "",
    }


def backfill(apply=False):
    db.init_db()
    seen, plan = set(), []
    for rec in _manifest():
        folder = _folder_of(rec)
        if not folder:
            continue
        seen.add(folder)
        plan.append(_item(rec, _run(folder), folder, rec.get("checklist_id")))
    inbox = Path(INBOX)
    if inbox.is_dir():
        for folder in sorted(os.listdir(inbox)):
            if folder in seen or not (inbox / folder).is_dir():
                continue
            run = _run(folder)
            if run:
                plan.append(_item({}, run, folder, run.get("checklist_id")))
    if apply:
        for item in plan:
            _write(item)
    return plan


def _reset_derived(article_id):
    c = db._connect()
    try:
        c.execute("delete from validation_results where article_id=?", (str(article_id),))
        c.execute("delete from images where article_id=?", (str(article_id),))
        c.commit()
    finally:
        c.close()


def _write(item):
    cid = item["checklist_id"]
    aid = str(cid or "")
    if cid:
        db.save_repurpose_export(
            cid, item["filter_result_id"], folder=item["folder"], dest=item["dest"],
            article_hash=item["article_hash"], config_hash=item["config_hash"],
            weighted=item["weighted"], status="exported")
    db.upsert_repurpose_run(
        item["folder"], checklist_id=cid, filter_result_id=item["filter_result_id"],
        status=item["status"], model=item["model"], usage_json=json.dumps(item["usage"]),
        started_at=item["started_at"], finished_at=item["finished_at"], article_id=aid)
    if not db.list_repurpose_events(item["folder"], limit=1):
        db.add_repurpose_event(item["folder"], "backfill", item["status"],
                               detail="backfilled from run.json", article_id=aid)
    # carry the canonical key onto the folder's existing events
    c = db._connect()
    try:
        c.execute("update repurpose_events set article_id=? where folder=? "
                  "and (article_id is null or article_id='')", (aid, item["folder"]))
        c.commit()
        seen = c.execute("select 1 from article_events where article_id=? and stage='repurpose' limit 1",
                         (aid,)).fetchone()
    finally:
        c.close()
    if cid and not seen:
        db.add_article_event(aid, "repurpose", item["status"], reason_code="backfill",
                             reason_text="backfilled from run.json")
    if cid:
        _reset_derived(aid)
        results = (item["validator"] or {}).get("results") or []
        if results:
            db.add_validation_results(aid, item["folder"], results)
        if item["image_file"]:
            db.add_image(aid, item["image_file"], role="featured", rung=item["image_rung"],
                         selected=1, reason="backfilled from run.json")


def main():
    ap = argparse.ArgumentParser(description="Backfill repurpose tables from the inbox")
    ap.add_argument("--apply", action="store_true", help="write (default: dry-run)")
    a = ap.parse_args()
    plan = backfill(apply=a.apply)
    for p in plan:
        print(f"{p['status']:>12} | cid={p['checklist_id']} | {p['folder'][:64]}")
    print(f"\n{'APPLIED' if a.apply else 'DRY-RUN'} · {len(plan)} folder(s)")


if __name__ == "__main__":
    main()
