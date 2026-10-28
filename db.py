# =============================================================================
# FILE HEADER
# file    : db.py
# role    : Shared storage — SQLite now, MySQL-ready
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : runs (run log), checklist (14 cols), pipeline_results (per-stage detail + tokens),
#           filter_results (filter verdict linked to one checklist row) — init, write, read.
# pages   : backs /api/logs, /api/pipeline-results, /checklist.json
# calls   : config (DB_ENGINE, SQLITE_PATH), sqlite3
# called  : pipeline, checklist, main, dashboard, filter_service (report reads)
# amend   : schema change = init_db + docs/reference/future-mysql/schema_mysql.sql + every SELECT. JSON columns stay JSON.
#           Test: python3 -c "import db; db.init_db(); print(db.list_runs(1))"
# =============================================================================
"""Storage: SQLite now, MySQL-ready (adapter via config.DB_ENGINE).

Four tables:
  - `runs`             : one row per email run (status, model, error) — logs page
  - `checklist`        : the 14-column checklist rows — checklist page / sheet
  - `pipeline_results` : per-stage detail + tokens for one run — flow page
  - `filter_results`   : filter verdict(s) linked to one checklist row — checklist filter panel

`pipeline_results.stages` is stored as JSON so the Workflow page can show each
stage (decide → load_attachments → drive_fetch → collect → extract → logo_scan →
verify → tokens → archive) with its detail and status.

Example run row:
    {"id": "05d69b47-...", "email_id": "1a0ea6d2dad4b996",
     "subject": "Fwd: [PRESS RELEASE] ...", "status": "success",
     "created_at": "2026-09-30T...", "error": "", "model": "gemini/gemini-2.5-flash"}
"""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone

import config

# The 14 checklist columns — shared by the sheet, the table, and CSV export.
_COLUMNS = [
    "subject", "threadId", "date", "folderId", "folderUrl", "articleFile",
    "hasArticle", "hasPic", "hasLogo", "hasLogoInArticle", "hasImageInArticle",
    "subjectMatch", "subjectScore", "readyToFilter",
]


def _connect():
    os.makedirs(os.path.dirname(config.SQLITE_PATH) or ".", exist_ok=True)
    c = sqlite3.connect(config.SQLITE_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = _connect()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            email_id TEXT,
            subject TEXT,
            status TEXT,
            created_at TEXT,
            error TEXT,
            model TEXT
        )
        """
    )
    c.execute(
        f"""
        CREATE TABLE IF NOT EXISTS checklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {", ".join(f"{col} TEXT" for col in _COLUMNS)},
            created_at TEXT
        )
        """
    )
    # add model column if it doesn't exist (migration)
    try:
        cols = [r[1] for r in c.execute("PRAGMA table_info(runs)")]
        if "model" not in cols:
            c.execute("ALTER TABLE runs ADD COLUMN model TEXT")
    except Exception:
        pass
    # add reply_sent to checklist (migration) — tracks rejection replies to avoid re-sending
    try:
        ccols = [r[1] for r in c.execute("PRAGMA table_info(checklist)")]
        for col in ("replySent", "replyTo", "replyAt"):
            if col not in ccols:
                c.execute(f"ALTER TABLE checklist ADD COLUMN {col} TEXT")
    except Exception:
        pass
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS filter_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checklist_id INTEGER,
            run_id TEXT,
            threadId TEXT,
            status TEXT,
            outcome TEXT,
            weighted INTEGER,
            gate TEXT,
            confidence REAL,
            gates TEXT,
            scores TEXT,
            verdict TEXT,
            battery TEXT,
            config_hash TEXT,
            article_hash TEXT,
            article_text TEXT,
            article_len INTEGER,
            model TEXT,
            error TEXT,
            created_at TEXT
        )
        """
    )
    try:
        fcols = [r[1] for r in c.execute("PRAGMA table_info(filter_results)")]
        for col, typ in (("battery", "TEXT"), ("config_hash", "TEXT"),
                         ("article_hash", "TEXT"), ("article_text", "TEXT"),
                         ("article_len", "INTEGER")):
            if col not in fcols:
                c.execute(f"ALTER TABLE filter_results ADD COLUMN {col} {typ}")
    except Exception:
        pass
    c.execute(
        """CREATE TABLE IF NOT EXISTS gmail_watch (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            history_id TEXT, expiration INTEGER, topic TEXT, updated_at TEXT
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS webhook_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE, email_address TEXT, history_id TEXT,
            status TEXT, error TEXT, created_at TEXT
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS webhook_messages (
            message_id TEXT PRIMARY KEY,
            event_id TEXT, source TEXT, status TEXT, attempts INTEGER DEFAULT 0,
            error TEXT, created_at TEXT, updated_at TEXT
        )"""
    )
    c.commit()
    c.close()


def log_run_start(email_id, subject, model=""):
    c = _connect()
    rid = str(uuid.uuid4())
    c.execute(
        "insert into runs (id, email_id, subject, status, created_at, model) values (?,?,?,?,?,?)",
        (rid, email_id, subject, "running", datetime.now(timezone.utc).isoformat(), model),
    )
    c.commit()
    c.close()
    return rid


def log_run_end(run_id, status, error="", model=""):
    c = _connect()
    if model:
        c.execute("update runs set status=?, error=?, model=? where id=?", (status, error, model, run_id))
    else:
        c.execute("update runs set status=?, error=? where id=?", (status, error, run_id))
    c.commit()
    c.close()


def set_run_subject(run_id, subject):
    """Fill the subject on a run row created before the email was normalized."""
    c = _connect()
    c.execute("update runs set subject=? where id=? and (subject is null or subject='')", (subject, run_id))
    c.commit()
    c.close()


def save_checklist(row):
    """Insert one checklist row and return its new checklist id."""
    c = _connect()
    cols = ", ".join(_COLUMNS)
    marks = ", ".join("?" for _ in _COLUMNS)
    vals = [row.get(col, "") for col in _COLUMNS]
    vals.append(datetime.now(timezone.utc).isoformat())
    cur = c.execute(
        f"insert into checklist ({cols}, created_at) values ({marks}, ?)",
        vals,
    )
    rid = cur.lastrowid
    c.commit()
    c.close()
    return rid


def save_filter_result(checklist_id, run_id, thread_id, result, status="ok", error=""):
    """Persist one filter verdict linked to a checklist row.

    `result` is the dict from `filter.judge()`; on failure pass `{}` and a non-ok
    `status` plus `error`.
    """
    c = _connect()
    c.execute(
        """CREATE TABLE IF NOT EXISTS filter_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checklist_id INTEGER,
            run_id TEXT,
            threadId TEXT,
            status TEXT,
            outcome TEXT,
            weighted INTEGER,
            gate TEXT,
            confidence REAL,
            gates TEXT,
            scores TEXT,
            verdict TEXT,
            battery TEXT,
            config_hash TEXT,
            article_hash TEXT,
            article_text TEXT,
            article_len INTEGER,
            model TEXT,
            error TEXT,
            created_at TEXT
        )"""
    )
    verdict = result or {}
    c.execute(
        """insert into filter_results
           (checklist_id, run_id, threadId, status, outcome, weighted, gate, confidence,
            gates, scores, verdict, battery, config_hash, article_hash, article_text,
            article_len, model, error, created_at)
           values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            checklist_id,
            run_id or "",
            thread_id or "",
            status,
            verdict.get("outcome", ""),
            verdict.get("weighted"),
            verdict.get("gate"),
            verdict.get("confidence"),
            json.dumps(verdict.get("gates", {})),
            json.dumps(verdict.get("scores", {})),
            json.dumps(verdict),
            json.dumps(verdict.get("battery", {})),
            verdict.get("config_hash", ""),
            verdict.get("article_hash", ""),
            verdict.get("article_text", ""),
            verdict.get("article_len"),
            verdict.get("model", ""),
            error or "",
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    rid = c.execute("select last_insert_rowid()").fetchone()[0]
    c.commit()
    c.close()
    return rid


def list_checklist():
    """Return checklist rows with the latest linked filter result (if any)."""
    c = _connect()
    cols = "c.id, " + ", ".join("c." + col for col in _COLUMNS) + ", c.replySent, c.replyTo, c.replyAt, c.created_at"
    try:
        rows = c.execute(
            f"""select {cols},
                       f.status as filterStatus, f.outcome as filterOutcome,
                       f.weighted as filterWeighted, f.gate as filterGate,
                       f.confidence as filterConfidence, f.error as filterError,
                       f.verdict as filterVerdict, f.created_at as filteredAt
                from checklist c
                left join filter_results f on f.id = (
                    select id from filter_results where checklist_id = c.id order by id desc limit 1
                )
                order by c.id desc"""
        ).fetchall()
    except Exception:
        # older DB without filter/reply tables
        try:
            rows = c.execute(
                f"select id, {', '.join(_COLUMNS)}, created_at from checklist order by id desc"
            ).fetchall()
        except Exception:
            rows = []
    c.close()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["filterVerdict"] = json.loads(d.get("filterVerdict") or "{}")
        except Exception:
            d["filterVerdict"] = {}
        out.append(d)
    return out


def _json_or_empty(raw):
    try:
        return json.loads(raw or "{}")
    except Exception:
        return {}


def get_filter_result(result_id):
    """Return one filter result with its checklist subject/date and parsed JSON."""
    c = _connect()
    r = c.execute(
        """select f.*, c.subject as subject, c.date as date, c.articleFile as articleFile
           from filter_results f
           left join checklist c on c.id = f.checklist_id
           where f.id = ?""",
        (result_id,),
    ).fetchone()
    c.close()
    if not r:
        return None
    d = dict(r)
    d["battery"] = _json_or_empty(d.get("battery"))
    d["verdict"] = _json_or_empty(d.get("verdict"))
    d["gates"] = _json_or_empty(d.get("gates"))
    d["scores"] = _json_or_empty(d.get("scores"))
    return d


def list_filter_history(checklist_id=None, thread_id=None, limit=100):
    """Filter versions for one checklist row/email, newest first.

    Pass `checklist_id` for the normal per-email history. `thread_id` is kept
    for callers that still group by thread; it is not used by the history page.
    """
    c = _connect()
    if checklist_id:
        rows = c.execute(
            """select f.*, c.subject as subject, c.date as date, c.articleFile as articleFile
               from filter_results f
               left join checklist c on c.id = f.checklist_id
               where f.checklist_id = ? order by f.id desc limit ?""",
            (int(checklist_id), int(limit)),
        ).fetchall()
    else:
        rows = c.execute(
            """select f.*, c.subject as subject, c.date as date, c.articleFile as articleFile
               from filter_results f
               left join checklist c on c.id = f.checklist_id
               where f.threadId = ? order by f.id desc limit ?""",
            (thread_id or "", int(limit)),
        ).fetchall()
    c.close()
    out = []
    for r in rows:
        d = dict(r)
        d["battery"] = _json_or_empty(d.get("battery"))
        d["verdict"] = _json_or_empty(d.get("verdict"))
        d["gates"] = _json_or_empty(d.get("gates"))
        d["scores"] = _json_or_empty(d.get("scores"))
        out.append(d)
    return out


def mark_reply_sent(thread_id, sent_to, status="true"):
    """Record that a rejection reply was sent for a checklist row (latest match)."""
    c = _connect()
    try:
        c.execute(
            "update checklist set replySent=?, replyTo=?, replyAt=? where threadId=? "
            "and (replySent is null or replySent='')",
            (status, sent_to, datetime.now(timezone.utc).isoformat(), thread_id),
        )
        c.commit()
    except Exception:
        pass
    c.close()


def save_gmail_watch(history_id, expiration, topic):
    c = _connect()
    c.execute(
        """insert into gmail_watch (id, history_id, expiration, topic, updated_at)
           values (1,?,?,?,?)
           on conflict(id) do update set history_id=excluded.history_id,
             expiration=excluded.expiration, topic=excluded.topic, updated_at=excluded.updated_at""",
        (str(history_id or ""), int(expiration or 0), topic or "",
         datetime.now(timezone.utc).isoformat()),
    )
    c.commit(); c.close()


def get_gmail_watch():
    c = _connect()
    r = c.execute("select history_id, expiration, topic, updated_at from gmail_watch where id=1").fetchone()
    c.close()
    return dict(r) if r else None


def begin_webhook_event(event_id, email_address, history_id):
    """Return (should_process, reason). Duplicate completed events are skipped."""
    c = _connect()
    now = datetime.now(timezone.utc).isoformat()
    try:
        c.execute(
            "insert into webhook_events (event_id,email_address,history_id,status,created_at) values (?,?,?,?,?)",
            (event_id, email_address or "", history_id or "", "received", now),
        )
        c.commit(); c.close()
        return True, "new"
    except Exception:
        r = c.execute("select status from webhook_events where event_id=?", (event_id,)).fetchone()
        if r and r["status"] in ("received", "done"):
            c.close()
            return False, r["status"]
        c.execute("update webhook_events set status='received', error='' where event_id=?", (event_id,))
        c.commit(); c.close()
        return True, "retry"


def finish_webhook_event(event_id, status, error=""):
    c = _connect()
    c.execute("update webhook_events set status=?, error=? where event_id=?",
              (status, (error or "")[:500], event_id))
    c.commit(); c.close()


def enqueue_webhook_messages(message_ids, source="webhook", event_id=""):
    """Add new message IDs; retry IDs whose previous attempt errored."""
    c = _connect()
    n = 0
    now = datetime.now(timezone.utc).isoformat()
    for mid in message_ids or []:
        if not mid:
            continue
        cur = c.execute(
            "insert or ignore into webhook_messages (message_id,event_id,source,status,created_at,updated_at) "
            "values (?,?,?,?,?,?)",
            (str(mid), event_id or "", source, "queued", now, now),
        )
        if cur.rowcount:
            n += 1
        else:
            r = c.execute("select status from webhook_messages where message_id=?", (str(mid),)).fetchone()
            if r and r["status"] == "error":
                c.execute("update webhook_messages set status='queued', error='', updated_at=? where message_id=?",
                          (now, str(mid)))
                n += 1
    c.commit(); c.close()
    return n


def claim_webhook_message():
    c = _connect()
    r = c.execute("select * from webhook_messages where status='queued' order by rowid limit 1").fetchone()
    if not r:
        c.close(); return None
    mid = r["message_id"]
    cur = c.execute("update webhook_messages set status='running', attempts=attempts+1, updated_at=? "
                    "where message_id=? and status='queued'",
                    (datetime.now(timezone.utc).isoformat(), mid))
    c.commit(); c.close()
    if not cur.rowcount:
        return None
    return dict(r)


def finish_webhook_message(message_id, status, error=""):
    c = _connect()
    c.execute("update webhook_messages set status=?, error=?, updated_at=? where message_id=?",
              (status, (error or "")[:500], datetime.now(timezone.utc).isoformat(), message_id))
    c.commit(); c.close()


def recover_webhook_queue():
    c = _connect()
    cur = c.execute("update webhook_messages set status='queued', updated_at=? where status='running'",
                    (datetime.now(timezone.utc).isoformat(),))
    c.commit(); c.close()
    return cur.rowcount


def list_runs(limit=100):
    c = _connect()
    rows = c.execute(
        "select id, email_id, subject, status, created_at, error, model from runs "
        "order by rowid desc limit ?",
        (limit,),
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]


def get_run(run_id):
    c = _connect()
    r = c.execute(
        "select id, email_id, subject, status, created_at, error, model from runs where id=?",
        (run_id,),
    ).fetchone()
    c.close()
    return dict(r) if r else None


def save_pipeline_result(run_id, email_id, subject, stages, row, status="success"):
    """Save the per-stage pipeline trace for one run (flow page).

    `status` is "success" or "error" (e.g. an AI failure).

    Example:
        db.save_pipeline_result(run_id, email_id, subject,
                                {"decide": {...}, "verify": {...}}, row_dict)
    """
    c = _connect()
    c.execute(
        """CREATE TABLE IF NOT EXISTS pipeline_results (
            run_id TEXT PRIMARY KEY,
            email_id TEXT,
            subject TEXT,
            status TEXT,
            stages TEXT,
            row TEXT,
            created_at TEXT
        )"""
    )
    c.execute(
        "insert or replace into pipeline_results (run_id, email_id, subject, status, stages, row, created_at) "
        "values (?,?,?,?,?,?,?)",
        (
            run_id,
            email_id,
            subject,
            status,
            json.dumps(stages),
            json.dumps(row),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    c.commit()
    c.close()


def list_pipeline_results(limit=50):
    """Return recent pipeline traces with `stages` and `row` as dicts.

    Example return item:
        {"run_id": "...", "email_id": "...", "subject": "...",
         "status": "success",
         "stages": {"decide": {...}, "tokens": {"detail": {"total": 3177}}},
         "row": {"subject": "...", "hasArticle": "true"}}
    """
    c = _connect()
    c.execute(
        """CREATE TABLE IF NOT EXISTS pipeline_results (
            run_id TEXT PRIMARY KEY,
            email_id TEXT,
            subject TEXT,
            status TEXT,
            stages TEXT,
            row TEXT,
            created_at TEXT
        )"""
    )
    rows = c.execute(
        "select * from pipeline_results order by rowid desc limit ?",
        (limit,),
    ).fetchall()
    c.close()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["stages"] = json.loads(d.get("stages") or "{}")
        except Exception:
            d["stages"] = {}
        try:
            d["row"] = json.loads(d.get("row") or "{}")
        except Exception:
            d["row"] = {}
        out.append(d)
    return out