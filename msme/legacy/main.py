# =============================================================================
# FILE HEADER
# file    : msme/legacy/main.py
# role    : Legacy receive API — same operations as dashboard /api/*
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : HTTP entry to the receive pipeline: run one/all emails, health, emails, logs, config, test-connection,
#           checklist.json — the non-/api twin of dashboard.py.
# pages   : /checklist.html (static file only)
# calls   : pipeline (via _process_one), gmail, db, creds, settings_store, connection_test, config
# called  : none (not started by run.py; kept for reference/legacy tests)
# amend   : every /api/* twin lives in dashboard.py — mirror a behaviour fix in both (todo/T-006).
#           Test: curl -s localhost:8899/api/health
# =============================================================================
"""Legacy receive API (bare paths); the live app is combined on :8899.

Endpoints:
  POST /run?email_id=...   process one email -> checklist row
  POST /run-all            process every unread email (manual)
  GET  /health
  GET  /emails             list unread emails (metadata only)
  GET  /logs               recent run logs (status, model, error)
  GET  /config / PUT /config    read/update settings (provider, keys, ...)
  POST /test-connection    test Gmail/Sheets/Drive/AI connectivity
  GET  /checklist.json     checklist rows (for the dashboard)

Example:
  curl -X POST 'http://localhost:8898/run?email_id=1a0ea6d2dad4b996'
  -> the 14-col checklist row for that email
"""
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from msme import config, connection_test, creds, db, paths, settings_store
from msme.receive import gmail, pipeline

app = FastAPI(title="MSME Newsbot Service")

# Allow the dashboard page (served on :8899) to call this API (:8898)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_static_dir = str(paths.STATIC)


def _process_one(email_id):
    """Synchronous: full pipeline for one email + save checklist row.

    Returns the checklist row; raises HTTPException(500) on any failure.
    """
    service = creds.gmail()
    run_id = db.log_run_start(email_id, "")
    try:
        row = pipeline.process_email(service, email_id, run_id=run_id)
    except Exception as e:
        db.log_run_end(run_id, "error", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    try:
        from msme.receive.checklist import save_checklist
        save_checklist(row)
    except Exception as e:
        db.log_run_end(run_id, "error", f"checklist save failed: {e}")
        raise HTTPException(status_code=500, detail=f"checklist save failed: {e}")
    try:
        gmail.mark_read(service, email_id)
    except Exception as e:
        print(f"[run] mark read failed for {email_id}: {e}")
    return row


@app.on_event("startup")
def startup():
    db.init_db()


@app.post("/run")
def run(email_id: str):
    """Process ONE email synchronously and return the checklist row."""
    return _process_one(email_id)


@app.post("/run-all")
def run_all():
    """Process ALL unread emails synchronously and mark each read."""
    service = creds.gmail()
    msgs = gmail.list_unread(service, query=settings_store.get("GMAIL_QUERY") or config.GMAIL_QUERY)
    results = []
    for m in msgs:
        try:
            row = _process_one(m["id"])
            results.append({"email_id": m["id"], "ok": True, "subject": row.get("subject")})
        except Exception as e:
            results.append({"email_id": m["id"], "ok": False, "error": str(e)})
    return {"processed": len(results), "results": results}


@app.get("/health")
def health():
    """Liveness + auto-poll scheduler state."""
    return {
        "status": "ok",
        "auto": settings_store.get("ENABLE_AUTO") or False,
        "schedule_minutes": settings_store.get("SCHEDULE_MINUTES") or config.SCHEDULE_MINUTES,
    }


@app.get("/emails")
def emails():
    """List unread emails as [{id, subject, from, date}] (metadata only)."""
    service = creds.gmail()
    msgs = gmail.list_unread(service, query=settings_store.get("GMAIL_QUERY") or config.GMAIL_QUERY)
    out = []
    for m in msgs:
        try:
            msg = gmail.get_message(service, m["id"], "metadata")
            hdrs = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            out.append({
                "id": m["id"],
                "subject": hdrs.get("Subject", ""),
                "from": hdrs.get("From", ""),
                "date": hdrs.get("Date", ""),
            })
        except Exception as e:
            out.append({"id": m["id"], "subject": "(error)", "from": str(e), "date": ""})
    return {"emails": out}


@app.get("/logs")
def logs():
    """Return recent run logs (status, model, subject, error)."""
    try:
        rows = db.list_runs(limit=200)
    except Exception as e:
        return {"logs": [], "error": str(e)}
    return {"logs": rows}


class ConfigPatch(BaseModel):
    """Schema for PUT /config — editable settings from the Config page."""
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = ""
    LLM_PROVIDER: str = ""
    GMAIL_QUERY: str = ""
    CHECKLIST_SHEET_ID: str = ""
    CHECKLIST_TAB: str = ""
    ARCHIVE_PARENT_FOLDER: str = ""
    ENABLE_AUTO: bool = False
    SCHEDULE_MINUTES: int = 5
    ENABLE_AUTO_FILTER: Optional[bool] = None
    ENABLE_AUTO_REPURPOSE: Optional[bool] = None
    WEB_FETCH_MODE: Optional[str] = None
    WEB_KNOWN_SITES: Optional[str] = None


@app.get("/config")
def get_config():
    """Return current settings (secret values masked)."""
    return {"config": settings_store.get_all(mask_secrets=True)}


@app.put("/config")
def put_config(patch: ConfigPatch):
    """Save edited settings; masked ('********') or empty values are skipped."""
    data = patch.dict()
    for k in list(data):
        if data[k] == "********":
            data.pop(k)
        elif k == "ENABLE_AUTO":
            continue
        elif k == "ENABLE_AUTO_FILTER":
            if data[k] is None:
                data.pop(k)
        elif k == "ENABLE_AUTO_REPURPOSE":
            if data[k] is None:
                data.pop(k)
        elif k == "SCHEDULE_MINUTES":
            if not data[k]:
                data.pop(k)
        elif k == "WEB_FETCH_MODE":
            if data[k] is None:
                data.pop(k)
            else:
                m = str(data[k]).strip().lower()
                data[k] = m if m in ("off", "known", "probe") else "probe"
        elif k == "WEB_KNOWN_SITES":
            if data[k] is None:
                data.pop(k)
            continue
        elif data[k] == "" or data[k] is None:
            # don't wipe an existing value with an empty string
            data.pop(k)
    settings_store.save(data)
    return {"config": settings_store.get_all(mask_secrets=True)}


# Test-connection cooldown (mirrors dashboard) — prevents Gmail rate-limit 429s
# from rapid repeated clicks.
import time as _time

_TEST_COOLDOWN_SECS = 10.0
_last_test = [0.0]


@app.post("/test-connection")
def test_connection():
    """Run connectivity checks for Gmail/Sheets/Drive + the active AI provider."""
    now = _time.monotonic()
    elapsed = now - _last_test[0]
    if elapsed < _TEST_COOLDOWN_SECS:
        return {"cooldown": True, "wait": round(_TEST_COOLDOWN_SECS - elapsed, 1), "results": {}}
    _last_test[0] = now
    return {"cooldown": False, "results": connection_test.test_all()}


@app.get("/checklist.json")
def checklist_json():
    try:
        rows = db.list_checklist()
    except Exception:
        rows = []
    return {"generated": "", "articles": rows}


@app.get("/checklist.html")
def checklist_html():
    path = os.path.join(_static_dir, "checklist.html")
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="dashboard not built yet")
