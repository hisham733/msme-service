# =============================================================================
# FILE HEADER
# file    : dashboard.py
# role    : Receive dashboard — pages + same-origin /api/* on :8899
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : serve the receive pages and their API so the browser has no CORS/hostname issues.
# pages   : checklist.html, flow.html, workflow-lab.html, receive-logs.html, config.html, pipeline-config.html
# calls   : pipeline (via _process_one), gmail, db, creds, settings_store, connection_test, config,
#           webhook_gmail (POST /webhooks/gmail)
# called  : combined.py (as a sub-app); the static pages
# amend   : page list must match static/INDEX.md; main.py is legacy and not served.
#           Test: curl -s localhost:8899/api/health
# =============================================================================
"""Dashboard app on :8899. Serves static pages AND same-origin API endpoints.

The pages fetch relative /api/* URLs (no CORS/hostname issues) which proxy to
the same service logic.

Pages:
  /              -> checklist.html   (the 14-col table, Run/Refresh/CSV)
  /flow.html     -> animated pipeline + recent runs with stage detail/tokens
  /logs.html     -> run history (status, model, subject, error)
  /config.html   -> combined receive + filter config (pipeline-config.html)

Example calls:
  curl -s localhost:8899/api/emails                    # cached list of unread
  curl -s -X POST 'localhost:8899/api/run?email_id=1a0...'   # async run
  curl -s localhost:8899/api/run-status?run_id=...     # poll a run
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

import config
import connection_test
import creds
import db
import editor_data
import filter as filter_judge
import filter_log
import gmail
import pipeline
import settings_store
import webhook_gmail
import workflow_lab

app = FastAPI(title="MSME Newsbot Dashboard")
app.include_router(workflow_lab.router)

_static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def _serve(name):
    """Serve a static dashboard page from the static/ folder (404 if missing)."""
    path = os.path.join(_static_dir, name)
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail=f"{name} not built yet")


@app.get("/")
def index():
    return _serve("checklist.html")


@app.get("/checklist.html")
def checklist_html():
    return _serve("checklist.html")


@app.get("/flow.html")
def flow_html():
    return _serve("flow.html")


@app.get("/workflow-lab.html")
def workflow_lab_html():
    """Interactive receive-workflow walkthrough + codebase map."""
    return _serve("workflow-lab.html")


# The receive dashboard has its OWN logs + config pages. static/logs.html and
# static/config.html are the FILTER app's pages (they call /logs.json, /config.json
# and /clear, which only exist on the filter port :8900). Serving them here made
# the tabs render empty and 404, so the receive UI uses receive-* instead.
@app.get("/logs.html")
@app.get("/receive-logs.html")
def logs_html():
    return _serve("receive-logs.html")


@app.get("/config.html")
def config_html():
    return _serve("pipeline-config.html")


@app.get("/receive-config.html")
def receive_config_html():
    return _serve("receive-config.html")


@app.get("/filter-config.html")
def filter_config_html():
    return _serve("config.html")


@app.get("/filter-history.html")
def filter_history_html():
    return _serve("filter-history.html")


@app.get("/editor.html")
def editor_html():
    return _serve("editor.html")


# ---- same-origin API (pages call these instead of :8898) ----

@app.get("/api/health")
def api_health():
    """Liveness + whether the auto-poll scheduler is on."""
    return {
        "status": "ok",
        "auto": settings_store.get("ENABLE_AUTO") or False,
        "schedule_minutes": settings_store.get("SCHEDULE_MINUTES") or config.SCHEDULE_MINUTES,
        "webhook": config.ENABLE_WEBHOOK,
    }


@app.post("/webhooks/gmail")
async def webhook_gmail_push(request: Request):
    """Gmail Push endpoint called by the Pub/Sub subscription (public, OIDC-guarded)."""
    status, payload = webhook_gmail.handle_push_request(
        request.headers.get("authorization", ""),
        await request.body(),
    )
    return JSONResponse(payload, status_code=status)


# Gmail list is SLOW (~10s) — keep a persistent cache file so the page can stay
# open all day WITHOUT hitting the Gmail API. Emails are re-fetched ONLY when
# the user clicks Refresh (force=1); otherwise the cached list is returned.
import os
_EMAILS_CACHE_SECS = 60  # in-memory safety net
_emails_cache = {"t": 0.0, "data": None}
_EMAILS_CACHE_FILE = os.path.join(os.path.dirname(config.SQLITE_PATH) or ".", "emails_cache.json")


def _read_emails_cache():
    try:
        with open(_EMAILS_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write_emails_cache(data):
    try:
        os.makedirs(os.path.dirname(_EMAILS_CACHE_FILE) or ".", exist_ok=True)
        with open(_EMAILS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[emails] cache write failed: {e}")


@app.get("/api/emails")
def api_emails(force: int = 0):
    """List unread emails as [{id, subject, from, date}].

    force=0 (default): return the persistent cache if it exists (even if old) —
    the dashboard shows whatever was last fetched until the user clicks Refresh.
    force=1 (Refresh button): fetch fresh from Gmail and overwrite the cache.

    Sequential fetch (threaded fetch exceeded Gmail quota -> HTTP 000).
    """
    import time
    now = time.time()

    # 1) non-forced call: serve from persistent cache when available
    if not force:
        cached = _read_emails_cache()
        if cached and cached.get("emails") is not None:
            return {"emails": cached["emails"]}
        # in-memory safety net (short TTL)
        if _emails_cache["data"] is not None and now - _emails_cache["t"] < _EMAILS_CACHE_SECS:
            return _emails_cache["data"]

    # 2) fresh fetch from Gmail
    try:
        service = creds.gmail()
        msgs = gmail.list_unread(service, query=settings_store.get("GMAIL_QUERY") or config.GMAIL_QUERY)
    except gmail.GmailRateLimitError as e:
        return {"emails": [], "error": "Gmail rate limit reached. Try again in a few minutes.", "rate_limited": True}
    except Exception as e:
        return {"emails": [], "error": str(e)[:200]}

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
        except gmail.GmailRateLimitError:
            # stop mid-list to avoid hammering further; keep what we have
            break
        except Exception as e:
            out.append({"id": m["id"], "subject": "(error)", "from": str(e), "date": ""})

    data = {"emails": out}
    _emails_cache["t"] = now
    _emails_cache["data"] = data
    _write_emails_cache(data)
    return data


def _process_one(email_id, run_id=None):
    """Run the full pipeline for one email + persist the checklist row.

    Returns the checklist row dict on success; raises HTTPException(500) on error.
    """
    service = creds.gmail()
    if not run_id:
        run_id = db.log_run_start(email_id, "")
    try:
        row = pipeline.process_email(service, email_id, run_id=run_id)
    except pipeline.AIError as e:
        db.log_run_end(run_id, "ai_error", str(e))
        raise HTTPException(status_code=502, detail=f"AI_ERROR: {e}")
    except Exception as e:
        db.log_run_end(run_id, "error", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    try:
        from checklist import save_checklist
        save_checklist(row)
    except Exception as e:
        db.log_run_end(run_id, "error", f"checklist save failed: {e}")
        raise HTTPException(status_code=500, detail=f"checklist save failed: {e}")
    try:
        gmail.mark_read(service, email_id)
    except Exception as e:
        print(f"[run] mark read failed for {email_id}: {e}")
    return row


@app.post("/api/run")
def api_run(email_id: str):
    """Start processing ONE email asynchronously; returns run_id immediately.

    The UI polls /api/run-status until it flips to success/error.
    """
    import threading
    run_id = db.log_run_start(email_id, "")

    def worker():
        try:
            row = _process_one(email_id, run_id=run_id)
        except Exception as e:
            print(f"[run] {email_id} failed: {e}")
            # Don't clobber a more specific status (e.g. "ai_error") already set
            # by _process_one / the pipeline.
            cur = db.get_run(run_id) or {}
            if cur.get("status") in (None, "", "running"):
                db.log_run_end(run_id, "error", str(e))

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return {"run_id": run_id, "email_id": email_id, "status": "running"}


@app.get("/api/run-status")
def api_run_status(run_id: str):
    """Return the current status of an async run: running / success / needs_human / error."""
    row = None
    try:
        row = db.get_run(run_id)
    except Exception:
        pass
    if not row:
        return {"run_id": run_id, "status": "unknown"}
    return {"run_id": run_id, "email_id": row.get("email_id"), "status": row.get("status"), "error": row.get("error")}


@app.post("/api/run-all")
def api_run_all():
    """Process ALL unread emails synchronously and mark each read.

    Example response:
        {"processed": 18, "results": [{"email_id": "...", "ok": true, "subject": "..."}]}
    """
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


@app.get("/api/repurpose")
def api_repurpose():
    """Map checklist id -> Repurpose engine status from the exported inbox."""
    manifest = os.path.join(os.path.dirname(config.SQLITE_PATH) or ".", "repurpose_export.json")
    try:
        with open(manifest, encoding="utf-8") as f:
            records = (json.load(f) or {}).get("exported") or []
    except Exception:
        records = []
    out = {}
    for rec in records:
        if not rec.get("dest"):
            continue
        folder = os.path.basename(rec.get("dest") or "")
        run_path = os.path.join(config.REPURPOSE_INBOX, folder, "run.json")
        status = "queued" if os.path.isdir(os.path.join(config.REPURPOSE_INBOX, folder)) else "pending"
        rung = ""
        try:
            with open(run_path, encoding="utf-8") as f:
                run = json.load(f) or {}
            status = run.get("status") or "queued"
            rung = run.get("image_rung") or ""
        except Exception:
            pass
        out[str(rec.get("checklist_id"))] = {
            "status": status,
            "folder": folder,
            "dashboard": config.REPURPOSE_DASHBOARD,
            "rung": rung,
        }
    return {"items": out, "dashboard": config.REPURPOSE_DASHBOARD}


@app.get("/api/editor/articles")
def api_editor_articles(page: int = 1, page_size: int = 20, tab: str = "all", q: str = ""):
    """Paginated editor items, sorted by last edit (newest first)."""
    try:
        return editor_data.query_items(page=page, page_size=page_size, tab=tab, q=q)
    except Exception as e:
        return {"items": [], "page": 1, "pages": 1, "total": 0, "error": str(e)}


@app.get("/api/editor/article")
def api_editor_article(thread_id: str):
    """Full stage detail + history for one email/thread."""
    try:
        item = editor_data.get_article(thread_id)
    except Exception as e:
        return {"error": str(e)}
    if not item:
        return {"error": "not found"}
    return item


@app.get("/repurpose-site/{path:path}")
def repurpose_site_file(path: str):
    """Serve the local built Repurpose site (read-only)."""
    base = Path(config.REPURPOSE_SITE).resolve()
    target = (base / (path or "index.html")).resolve()
    if target != base and base not in target.parents:
        raise HTTPException(404, "not found")
    if target.is_dir():
        target = target / "index.html"
    if not target.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(target)


@app.get("/api/filter-history")
def api_filter_history(checklist_id: int = 0, thread_id: str = "", limit: int = 100):
    """Filter versions for one checklist row/email, newest first.

    `thread_id` remains as a fallback for old links; the history page uses
    `checklist_id`, so two emails in one thread never share version numbers.
    """
    if not checklist_id and not thread_id:
        return {"versions": []}
    try:
        versions = db.list_filter_history(
            checklist_id=checklist_id or None, thread_id=thread_id or None, limit=limit
        )
        total = len(versions)
        for i, v in enumerate(versions):
            v["version"] = total - i
            v.pop("article_text", None)
            v.pop("verdict", None)
        return {"versions": versions}
    except Exception as e:
        return {"versions": [], "error": str(e)}


@app.get("/api/filter-result")
def api_filter_result(filter_result_id: int):
    """One filter version with its saved rubric and article text."""
    try:
        r = db.get_filter_result(filter_result_id)
    except Exception as e:
        return {"error": str(e)}
    if not r:
        return {"error": "not found"}
    return r


@app.post("/api/filter/rerun")
def api_filter_rerun(filter_result_id: int):
    """Re-run Jev on the stored article with the CURRENT rubric.

    A new filter_results row is added to the SAME checklist row; no new receive
    row/archive is created.
    """
    try:
        r = db.get_filter_result(filter_result_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    if not r:
        return {"ok": False, "error": "filter result not found"}
    text = r.get("article_text") or ""
    if not text.strip():
        return {"ok": False, "error": "no saved article text for this result"}
    inp = (r.get("verdict") or {}).get("input") or {}
    article = {
        "subject": inp.get("subject") or r.get("subject") or "",
        "from": inp.get("from") or "",
        "date": inp.get("date") or r.get("date") or "",
        "bodyText": text,
    }
    try:
        verdict = filter_judge.judge(article)
        verdict["input"] = {
            "subject": article["subject"][:120],
            "from": article["from"][:80],
            "date": article["date"],
            "bodyTextLen": len(text),
        }
        verdict["article_text"] = text[:12000]
        verdict["article_len"] = len(verdict["article_text"])
        verdict["article_hash"] = hashlib.sha256(
            verdict["article_text"].encode("utf-8")).hexdigest()[:12]
        filter_log.log_verdict(article, verdict, source="refilter")
        new_id = db.save_filter_result(
            r.get("checklist_id"), r.get("run_id", ""), r.get("threadId", ""), verdict
        )
        return {"ok": True, "filter_result_id": new_id,
                "outcome": verdict.get("outcome"),
                "weighted": verdict.get("weighted"),
                "config_hash": verdict.get("config_hash")}
    except Exception as e:
        err = str(e)[:300]
        try:
            db.save_filter_result(
                r.get("checklist_id"), r.get("run_id", ""), r.get("threadId", ""),
                {}, status="error", error=err)
        except Exception:
            pass
        return {"ok": False, "error": err}


@app.get("/api/pipeline-results")
def api_pipeline_results():
    """Return recent pipeline traces for the Workflow page (stage detail + tokens + model)."""
    try:
        return {"results": db.list_pipeline_results(limit=30)}
    except Exception as e:
        return {"results": [], "error": str(e)}


@app.post("/api/clear")
def api_clear():
    """Clear all checklist/runs/pipeline data from SQLite."""
    cleared = {"sqlite": False}
    # SQLite
    try:
        import sqlite3
        import os
        c = sqlite3.connect(config.SQLITE_PATH)
        for t in ("checklist", "runs", "pipeline_results"):
            try:
                c.execute(f"delete from {t}")
            except Exception:
                pass
        c.commit()
        c.close()
        cleared["sqlite"] = True
    except Exception as e:
        cleared["sqlite_error"] = str(e)
    return cleared


@app.get("/api/download.csv")
def api_download_csv():
    """Download the checklist as CSV (commas in cells replaced with ';')."""
    import io
    rows = []
    try:
        rows = db.list_checklist()
    except Exception:
        rows = []
    cols = ["subject", "threadId", "date", "folderId", "folderUrl", "articleFile",
            "hasArticle", "hasPic", "hasLogo", "hasLogoInArticle", "hasImageInArticle",
            "subjectMatch", "subjectScore", "readyToFilter",
            "filterStatus", "filterOutcome", "filterWeighted", "filterGate"]
    buf = io.StringIO()
    buf.write(",".join(cols) + "\n")
    for r in rows:
        vals = [str(r.get(c, "") or "").replace(",", ";").replace("\n", " ") for c in cols]
        buf.write(",".join(vals) + "\n")
    from fastapi.responses import Response
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=checklist.csv"},
    )


@app.get("/api/logs")
def api_logs():
    """Return recent run logs (status, model, subject, error) for the Logs page."""
    try:
        return {"logs": db.list_runs(limit=200)}
    except Exception as e:
        return {"logs": [], "error": str(e)}


@app.get("/api/config")
def api_get_config():
    """Return current settings with secret values masked."""
    return {"config": settings_store.get_all(mask_secrets=True)}


class ConfigPatch(BaseModel):
    """Schema for PUT /api/config — only these keys are editable from the page."""
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


@app.put("/api/config")
def api_put_config(patch: ConfigPatch):
    """Save edited settings. '********' = unchanged secret (dropped), empty = dropped."""
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
            data.pop(k)
    settings_store.save(data)
    return {"config": settings_store.get_all(mask_secrets=True)}


# Test-connection cooldown: repeated clicks in a short window were tripping
# Gmail's per-user rate limit (GetProfile 429). Block re-runs for 10s.
import time as _time
_TEST_COOLDOWN_SECS = 10.0
_last_test = [0.0]


@app.post("/api/test-connection")
def api_test_connection():
    """Test Gmail / Sheets / Drive / AI provider connectivity (Config page button).

    Cooldown 10s: rapid repeated clicks return {cooldown:true} instead of
    calling the APIs, preventing Gmail rate-limit 429s.
    """
    now = _time.monotonic()
    elapsed = now - _last_test[0]
    if elapsed < _TEST_COOLDOWN_SECS:
        return {"cooldown": True, "wait": round(_TEST_COOLDOWN_SECS - elapsed, 1), "results": {}}
    _last_test[0] = now
    return {"cooldown": False, "results": connection_test.test_all()}


@app.get("/checklist.json")
def checklist_json():
    """Checklist data in the legacy format (articles key) for the dashboard."""
    try:
        rows = db.list_checklist()
    except Exception:
        rows = []
    return {"generated": "", "articles": rows}


@app.post("/api/reply")
def api_reply(email_id: str, dry: int = 0):
    """Send (or preview) the rejection reply for a not-ready article.

    `email_id` may be a Gmail message id OR a threadId (we resolve threadId to a
    message if needed). dry=1 returns the would-be email WITHOUT sending.
    """
    try:
        service = creds.gmail()
        # resolve: is it a message id or a thread id?
        msg = None
        try:
            msg = gmail.get_message(service, email_id, "full")
        except Exception:
            msg = None
        if msg is None:
            # treat as threadId -> find the first message in the thread
            msgs = gmail.list_unread(service, query=f"thread:{email_id} in:anywhere",
                                     unread_only=False)
            msg = None
            for m in msgs:
                try:
                    msg = gmail.get_message(service, m["id"], "full")
                    break
                except Exception:
                    continue
            if msg is None:
                return {"ok": False, "error": f"could not resolve message for {email_id}"}
        import normalize as _n
        model = _n.build_email_model(service, msg.get("id", email_id), message=msg)
        # find the matching checklist row (latest by threadId)
        row = None
        for r in db.list_checklist():
            if r.get("threadId") == model.get("threadId"):
                row = r
        if row is None:
            return {"ok": False, "error": f"no checklist row for {email_id}"}
        import reply
        if dry:
            return {"ok": True, "preview": reply.preview_reply(row, model)}
        result = reply.send_reply_for_row(service, model, row,
                                          thread_id=model.get("threadId"),
                                          msg_id=model.get("messageId"),
                                          force=True)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/logs.json")
def logs_json():
    """Logs in the legacy format for the dashboard."""
    try:
        rows = db.list_runs(limit=200)
    except Exception as e:
        return {"logs": [], "error": str(e)}
    return {"logs": rows}