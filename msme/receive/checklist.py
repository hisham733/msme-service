# =============================================================================
# FILE HEADER
# file    : msme/receive/checklist.py
# role    : Receive — checklist persistence
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : build the 14-column row and save it to SQLite (the checklist source of truth).
# pages   : feeds the checklist table on :8899
# calls   : db.save_checklist
# called  : dashboard.py, main.py, scheduler.py
# amend   : column names/order are a contract with CSV/report readers — change all together.
#           Test: run one email, then GET /checklist.json
# =============================================================================
"""Checklist: save the 14-column row to SQLite.

A completed run produces a row dict like:
    {"subject": "...", "threadId": "...", "date": "...", "folderId": "",
     "folderUrl": "", "articleFile": "...md", "hasArticle": "true",
     "hasPic": "true", "hasLogo": "true", "hasLogoInArticle": "true",
     "hasImageInArticle": "true", "subjectMatch": "true",
     "subjectScore": "85", "readyToFilter": "true"}

SQLite (`data/msme.sqlite3`) is the checklist source of truth. The Google Sheet
is optional and is not updated by the receive pipeline.
"""
from msme import db, settings_store

COLUMNS = [
    "subject", "threadId", "date", "folderId", "folderUrl", "articleFile",
    "hasArticle", "hasPic", "hasLogo", "hasLogoInArticle", "hasImageInArticle",
    "subjectMatch", "subjectScore", "readyToFilter",
]


def build_row(row):
    """Flatten a row dict into the ordered checklist list."""
    return [row.get(col, "") for col in COLUMNS]


def save_checklist(row):
    """Persist a completed row + its linked filter result to SQLite."""
    checklist_id = None
    try:
        checklist_id = db.save_checklist(row)
    except Exception as e:
        print(f"[checklist] sqlite save failed: {e}")
        return
    # N-3/N-4: persist the captured link + the media index (outside the 14-col contract).
    try:
        link = row.get("_link")
        if link:
            db.save_email_link(checklist_id, row.get("messageId", ""),
                               row.get("subject", ""), link)
        media = row.get("_media")
        if "_media" in row:
            # always replace, even with an empty list, so a re-run clears stale rows
            db.save_email_media(checklist_id, row.get("messageId", ""), media or [])
    except Exception as e:
        print(f"[checklist] link/media save failed: {e}")
    result = row.get("_filter") or {}
    if not result:
        return
    status = "error" if result.get("outcome") == "ERROR" else "ok"
    try:
        db.save_filter_result(
            checklist_id,
            row.get("_runId", ""),
            row.get("threadId", ""),
            result,
            status=status,
            error=result.get("error", "") if status == "error" else "",
        )
    except Exception as e:
        print(f"[checklist] filter result save failed: {e}")
        return
    if status == "ok" and str(result.get("outcome", "")).upper() == "ACCEPT":
        try:
            enabled = settings_store.get("ENABLE_AUTO_REPURPOSE")
            if enabled is None:
                enabled = True
            if enabled:
                from msme.repurpose import repurpose_export
                repurpose_export.export(apply=True)
                print(f"[checklist] repurpose export checked for checklist_id={checklist_id}")
        except Exception as e:
            print(f"[checklist] repurpose export failed: {e}")
