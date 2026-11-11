# =============================================================================
# FILE HEADER
# file    : msme/db.py
# role    : Shared storage — SQLite now, MySQL-ready
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : runs, checklist, pipeline_results, filter_results, webhook queue; plus T-047 users,
#           sessions, login_attempts, audit_log and filter_config_versions — init, write, read.
# pages   : backs /api/logs, /api/pipeline-results, /checklist.json
# calls   : config (DB_ENGINE, SQLITE_PATH), sqlite3
# called  : pipeline, checklist, main, dashboard, filter_service (report reads)
# amend   : schema change = init_db + docs/reference/future-mysql/schema_mysql.sql + every SELECT. JSON columns stay JSON.
#           Test: python3 -c "import db; db.init_db(); print(db.list_runs(1))"
# =============================================================================
"""Storage: SQLite now, MySQL-ready (adapter via config.DB_ENGINE).

Tables:
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
import time
import uuid
from datetime import datetime, timezone

from msme import config

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
    try:
        c.execute("PRAGMA busy_timeout = 5000")
    except Exception:
        pass
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
        for col in ("replySent", "replyTo", "replyAt", "messageId", "rfc822MessageId",
                    "emailType"):
            if col not in ccols:
                c.execute(f"ALTER TABLE checklist ADD COLUMN {col} TEXT")
    except Exception:
        pass
    # N-9 follow-up: one compact row per received email (no body, no attachment bytes).
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS emails (
            message_id TEXT PRIMARY KEY,
            from_name TEXT,
            from_email TEXT,
            subject TEXT,
            received_at TEXT,
            links_json TEXT,
            attachment_count INTEGER DEFAULT 0
        )
        """
    )
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_checklist_message_id ON checklist(messageId)")
    except Exception:
        pass
    # N-3/N-4: links (report/speech/source) and media (images/logos incl. the gallery
    # fallback) captured for an email. Both are keyed by message_id; checklist_id is
    # the latest row. The repurpose export materialises them into the inbox folder.
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS email_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT,
            checklist_id INTEGER,
            link_type TEXT,
            url TEXT,
            source TEXT,
            anchor TEXT,
            confidence REAL,
            is_primary INTEGER DEFAULT 0,
            candidates_json TEXT,
            created_at TEXT
        )
        """
    )
    for _idx in ("idx_email_links_msg", "idx_email_links_type"):
        try:
            _col = "message_id" if _idx == "idx_email_links_msg" else "link_type"
            c.execute(f"CREATE INDEX IF NOT EXISTS {_idx} ON email_links({_col})")
        except Exception:
            pass
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS email_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT,
            checklist_id INTEGER,
            name TEXT,
            kind TEXT,
            source TEXT,
            role TEXT,
            path TEXT,
            width INTEGER,
            height INTEGER,
            bytes INTEGER,
            sha1 TEXT,
            usable INTEGER,
            chosen INTEGER,
            created_at TEXT
        )
        """
    )
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_email_media_msg ON email_media(message_id)")
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
    c.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin','editor')),
            active INTEGER NOT NULL DEFAULT 1,
            must_change_password INTEGER NOT NULL DEFAULT 0,
            created_at TEXT, updated_at TEXT, last_login_at TEXT
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            csrf_token TEXT NOT NULL,
            created_at TEXT, expires_at INTEGER NOT NULL,
            ip TEXT, user_agent TEXT
        )"""
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)")
    c.execute(
        """CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT, ip TEXT, ok INTEGER NOT NULL,
            attempted_at INTEGER NOT NULL
        )"""
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_attempts_time ON login_attempts(attempted_at)")
    c.execute(
        """CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_id INTEGER, actor_username TEXT,
            action TEXT NOT NULL, target_type TEXT, target_id TEXT,
            before_json TEXT, after_json TEXT,
            ip TEXT, user_agent TEXT, created_at TEXT
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS filter_config_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_hash TEXT NOT NULL,
            snapshot_json TEXT NOT NULL,
            actor_id INTEGER, actor_username TEXT,
            action TEXT NOT NULL,
            restored_from INTEGER,
            created_at TEXT
        )"""
    )
    # T-050 / D40: the repurpose engine's state lives in the same DB.
    c.execute(
        """CREATE TABLE IF NOT EXISTS repurpose_exports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checklist_id INTEGER UNIQUE,
            filter_result_id INTEGER,
            folder TEXT,
            dest TEXT,
            article_hash TEXT,
            config_hash TEXT,
            weighted INTEGER,
            status TEXT,
            exported_at TEXT
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS repurpose_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder TEXT UNIQUE,
            checklist_id INTEGER,
            filter_result_id INTEGER,
            status TEXT,
            model TEXT,
            started_at TEXT,
            finished_at TEXT,
            error TEXT,
            usage_json TEXT,
            run_json TEXT,
            draft_path TEXT,
            site_path TEXT,
            updated_at TEXT
        )"""
    )
    # D40/T-055: usage was added after the first in-process runs — migrate old DBs.
    try:
        rpos = [r[1] for r in c.execute("PRAGMA table_info(repurpose_runs)")]
        if "usage_json" not in rpos:
            c.execute("ALTER TABLE repurpose_runs ADD COLUMN usage_json TEXT")
    except Exception:
        pass
    c.execute(
        """CREATE TABLE IF NOT EXISTS repurpose_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder TEXT,
            stage TEXT,
            status TEXT,
            detail TEXT,
            created_at TEXT
        )"""
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_repurpose_events_folder ON repurpose_events(folder)")
    # P0-1 (partner handoff 2026-11-11): article-keyed stage / event / validation / image tables.
    # article_id = checklist.id (the canonical key); article_hash flags duplicate emails.
    c.execute(
        """CREATE TABLE IF NOT EXISTS stage_runs (
            run_id TEXT PRIMARY KEY,
            article_id TEXT,
            stage TEXT,
            service TEXT,
            status TEXT,
            started_at TEXT,
            ended_at TEXT,
            error_code TEXT,
            error_text TEXT
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS article_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT,
            stage TEXT,
            status TEXT,
            reason_code TEXT,
            reason_text TEXT,
            notes TEXT,
            actor TEXT,
            created_at TEXT,
            payload_json TEXT
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS validation_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT,
            run_id TEXT,
            rule_code TEXT,
            level TEXT,
            ok INTEGER,
            detail TEXT
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS images (
            image_id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT,
            path TEXT,
            role TEXT,
            rung TEXT,
            selected INTEGER,
            reason TEXT
        )"""
    )
    for _t in ("stage_runs", "article_events", "validation_results", "images"):
        try:
            c.execute(f"CREATE INDEX IF NOT EXISTS idx_{_t}_article ON {_t}(article_id)")
        except Exception:
            pass
    # migrations + backfill (idempotent: fills only empty values)
    try:
        ccols = [r[1] for r in c.execute("PRAGMA table_info(checklist)")]
        if "article_hash" not in ccols:
            c.execute("ALTER TABLE checklist ADD COLUMN article_hash TEXT")
    except Exception:
        pass
    for _t in ("repurpose_runs", "repurpose_events"):
        try:
            _cols = [r[1] for r in c.execute(f"PRAGMA table_info({_t})")]
            if "article_id" not in _cols:
                c.execute(f"ALTER TABLE {_t} ADD COLUMN article_id TEXT")
        except Exception:
            pass
    try:
        c.execute("UPDATE repurpose_runs SET article_id = CAST(checklist_id AS TEXT) "
                  "WHERE (article_id IS NULL OR article_id='') AND checklist_id IS NOT NULL")
        c.execute("UPDATE repurpose_events SET article_id = (SELECT CAST(re.checklist_id AS TEXT) "
                  "FROM repurpose_exports re WHERE re.folder = repurpose_events.folder LIMIT 1) "
                  "WHERE (article_id IS NULL OR article_id='')")
        c.execute("UPDATE checklist SET article_hash = (SELECT f.article_hash FROM filter_results f "
                  "WHERE f.checklist_id = checklist.id AND f.article_hash IS NOT NULL "
                  "ORDER BY f.id DESC LIMIT 1) WHERE (article_hash IS NULL OR article_hash='')")
    except Exception:
        pass
    c.commit()
    c.close()


# --- P0-1: article-keyed stage / event / validation / image writers ---------

def add_stage_run(run_id, article_id, stage, service="", status="", started_at="",
                  ended_at="", error_code="", error_text=""):
    """Record one stage execution (`article_id` = checklist.id)."""
    c = _connect()
    try:
        c.execute(
            """insert or replace into stage_runs
               (run_id, article_id, stage, service, status, started_at, ended_at, error_code, error_text)
               values (?,?,?,?,?,?,?,?,?)""",
            (str(run_id), str(article_id or ""), stage or "", service or "", status or "",
             started_at or "", ended_at or "", error_code or "", error_text or ""),
        )
        c.commit()
    finally:
        c.close()


def add_article_event(article_id, stage, status, reason_code="", reason_text="", notes="",
                      actor="", payload=None):
    """Append one dashboard event; returns the event_id."""
    c = _connect()
    try:
        payload_json = json.dumps(payload) if payload is not None else ""
        cur = c.execute(
            """insert into article_events
               (article_id, stage, status, reason_code, reason_text, notes, actor, created_at, payload_json)
               values (?,?,?,?,?,?,?,?,?)""",
            (str(article_id or ""), stage or "", status or "", reason_code or "", reason_text or "",
             notes or "", actor or "", datetime.now(timezone.utc).isoformat(), payload_json),
        )
        c.commit()
        return cur.lastrowid
    finally:
        c.close()


def add_validation_results(article_id, run_id, results):
    """Store a validator run's per-rule results (list of {code, level, ok, detail})."""
    c = _connect()
    try:
        n = 0
        for r in results or []:
            c.execute(
                """insert into validation_results (article_id, run_id, rule_code, level, ok, detail)
                   values (?,?,?,?,?,?)""",
                (str(article_id or ""), str(run_id or ""),
                 r.get("code") or r.get("rule_code") or "", r.get("level") or "",
                 1 if r.get("ok") else 0, str(r.get("detail") or "")[:500]),
            )
            n += 1
        c.commit()
        return n
    finally:
        c.close()


def add_image(article_id, path, role="", rung="", selected=0, reason=""):
    """Record one image-selection provenance row."""
    c = _connect()
    try:
        c.execute(
            "insert into images (article_id, path, role, rung, selected, reason) values (?,?,?,?,?,?)",
            (str(article_id or ""), path or "", role or "", rung or "", 1 if selected else 0, reason or ""),
        )
        c.commit()
    finally:
        c.close()


def article_timeline(article_id):
    """The acceptance join: receive → filter → repurpose → validation for one article_id."""
    c = _connect()
    try:
        aid = str(article_id)
        chk = c.execute(
            "select id, subject, hasArticle, hasPic, hasLogo, readyToFilter, emailType, article_hash, messageId "
            "from checklist where id=? limit 1", (aid,)).fetchone()
        if not chk:
            return None
        fil = c.execute(
            "select outcome, weighted, gate, confidence, created_at from filter_results "
            "where checklist_id=? order by id desc limit 1", (chk["id"],)).fetchone()
        rep = c.execute(
            "select folder, status, model, usage_json, started_at, finished_at from repurpose_runs "
            "where checklist_id=? or article_id=? order by id desc limit 1", (chk["id"], aid)).fetchone()
        vals = [dict(r) for r in c.execute(
            "select rule_code, level, ok, detail from validation_results "
            "where article_id=? order by result_id", (aid,))]
        events = [dict(r) for r in c.execute(
            "select stage, status, reason_code, reason_text, actor, created_at "
            "from article_events where article_id=? order by event_id", (aid,))]
        return {"article_id": aid, "checklist": dict(chk),
                "filter": dict(fil) if fil else None,
                "repurpose": dict(rep) if rep else None,
                "validation": vals, "events": events}
    finally:
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


def save_email(model, received_at=None):
    """Record one received email in the compact `emails` table.

    Stores the envelope + link/attachment summary only — no body and no attachment
    bytes. A re-run updates the fields but keeps the first `received_at`.
    `received_at` can be overridden for a backfill (use the email's Date header).
    Returns True when a row was written, False when the message id is missing.
    """
    model = model or {}
    message_id = str(model.get("messageId") or "").strip()
    if not message_id:
        return False
    links = model.get("linksFound") or []
    attachments = model.get("attachments") or []
    when = received_at or datetime.now(timezone.utc).isoformat()
    c = _connect()
    c.execute(
        """insert into emails
           (message_id, from_name, from_email, subject, received_at, links_json, attachment_count)
           values (?,?,?,?,?,?,?)
           on conflict(message_id) do update set
             from_name=excluded.from_name,
             from_email=excluded.from_email,
             subject=excluded.subject,
             links_json=excluded.links_json,
             attachment_count=excluded.attachment_count""",
        (
            message_id,
            model.get("fromName", ""),
            model.get("fromEmail", ""),
            model.get("subject", ""),
            when,
            json.dumps(list(links), ensure_ascii=False),
            len(attachments),
        ),
    )
    c.commit()
    c.close()
    return True


def get_email(message_id):
    """Return one `emails` row (with parsed links) or None."""
    c = _connect()
    try:
        r = c.execute("select * from emails where message_id=?", (str(message_id or ""),)).fetchone()
    except Exception:
        r = None
    c.close()
    if not r:
        return None
    d = dict(r)
    try:
        d["links"] = json.loads(d.get("links_json") or "[]")
    except Exception:
        d["links"] = []
    return d


def list_emails(limit=100):
    """Newest received emails (compact rows, parsed links)."""
    c = _connect()
    try:
        rows = c.execute(
            "select * from emails order by received_at desc limit ?", (int(limit),)
        ).fetchall()
    except Exception:
        rows = []
    c.close()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["links"] = json.loads(d.get("links_json") or "[]")
        except Exception:
            d["links"] = []
        out.append(d)
    return out


def sender_summary():
    """One row per sender: from_email, from_name, email count, last received.

    The count comes from `emails` (one row per message), never from `checklist` —
    a re-run creates extra checklist rows and would double-count.
    """
    c = _connect()
    try:
        rows = c.execute(
            """select case when trim(from_email)='' then '(unknown sender)' else from_email end
                      as from_email,
                      max(from_name) as from_name,
                      count(*) as emails,
                      max(received_at) as last_received
               from emails
               group by from_email
               order by emails desc, last_received desc"""
        ).fetchall()
    except Exception:
        rows = []
    c.close()
    return [dict(r) for r in rows]


def sender_emails(email):
    """One sender's emails, each with its latest checklist row (ready flag)."""
    target = str(email or "")
    c = _connect()
    try:
        rows = c.execute(
            """select e.message_id, e.from_name, e.from_email, e.subject,
                      e.received_at, e.links_json, e.attachment_count,
                      c.id as checklistId, c.readyToFilter, c.hasArticle,
                      c.date as emailDate
               from emails e
               left join checklist c on c.id = (
                   select id from checklist where messageId = e.message_id order by id desc limit 1
               )
               where case when trim(e.from_email)='' then '(unknown sender)' else e.from_email end = ?
               order by e.received_at desc""",
            (target,),
        ).fetchall()
    except Exception:
        rows = []
    c.close()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["links"] = json.loads(d.get("links_json") or "[]")
        except Exception:
            d["links"] = []
        out.append(d)
    return out


def model_rows():
    """One row per email: the latest receive run, its model and the latest checklist status.

    The page is built from `runs` (not `emails`) so it works before the Gmail backfill;
    `from_email`/`from_name` fill in automatically once `emails` has the message.
    """
    c = _connect()
    try:
        rows = c.execute(
            """select r.email_id, r.subject, r.model, r.status,
                      r.created_at, r.created_at as run_at,
                      e.from_email, e.from_name, c.readyToFilter,
                      (select count(*) from runs r2 where r2.email_id=r.email_id) as run_count
               from runs r
               join (select email_id, max(rowid) rid from runs group by email_id) x on x.rid=r.rowid
               left join emails e on e.message_id=r.email_id
               left join checklist c on c.id = (
                   select id from checklist where messageId=r.email_id order by id desc limit 1)
               order by r.rowid desc"""
        ).fetchall()
    except Exception:
        rows = []
    c.close()
    return [dict(r) for r in rows]


def model_summary():
    """Models seen in `runs`, with email/run counts and the last run time."""
    out = {}
    for r in model_rows():
        model = r.get("model") or "(unknown)"
        item = out.setdefault(model, {"model": model, "emails": 0, "runs": 0, "last_run": ""})
        item["emails"] += 1
        item["runs"] += int(r.get("run_count") or 0)
        if (r.get("created_at") or "") > item["last_run"]:
            item["last_run"] = r.get("created_at") or ""
    return sorted(out.values(), key=lambda x: (-x["emails"], x["model"]))


def jev_rows():
    """One row per checklist item: the latest Jev filter verdict."""
    c = _connect()
    try:
        rows = c.execute(
            """select f.id, f.checklist_id, f.outcome, f.weighted, f.gate, f.confidence,
                      f.model, f.created_at, f.verdict,
                      c.messageId, c.subject, c.date, c.readyToFilter
               from filter_results f
               join (select checklist_id, max(id) fid from filter_results group by checklist_id) y
                 on y.fid=f.id
               left join checklist c on c.id=f.checklist_id
               order by f.id desc"""
        ).fetchall()
    except Exception:
        rows = []
    c.close()
    out = []
    for r in rows:
        d = dict(r)
        try:
            verdict = json.loads(d.pop("verdict") or "{}")
        except Exception:
            verdict = {}
        d["usage"] = verdict.get("usage") or {}
        out.append(d)
    return out


def jev_summary():
    """Count the latest Jev verdicts by outcome."""
    counts = {}
    for r in jev_rows():
        outcome = r.get("outcome") or "(unknown)"
        counts[outcome] = counts.get(outcome, 0) + 1
    return [{"outcome": k, "n": v} for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]


def cost_receive_rows(limit=5000):
    """Every successful receive run with token usage (the Cost tab picks the latest)."""
    c = _connect()
    try:
        rows = c.execute(
            "select run_id, email_id, subject, status, stages, created_at "
            "from pipeline_results order by rowid desc limit ?", (int(limit),)
        ).fetchall()
    except Exception:
        rows = []
    c.close()
    out = []
    for r in rows:
        d = dict(r)
        try:
            stages = json.loads(d.pop("stages") or "{}")
        except Exception:
            stages = {}
        tokens = (stages.get("tokens") or {}).get("detail") or {}
        if not tokens.get("total"):
            continue
        d["tokens"] = {
            "prompt": int(tokens.get("prompt") or 0),
            "completion": int(tokens.get("completion") or 0),
            "total": int(tokens.get("total") or 0),
        }
        d["model"] = tokens.get("model") or ""
        out.append(d)
    return out


def cost_filter_rows(limit=5000):
    """Every filter result with its Jev usage (the Cost tab picks the latest)."""
    c = _connect()
    try:
        rows = c.execute(
            """select f.id, f.checklist_id, f.outcome, f.model, f.created_at, f.verdict,
                      c.messageId, c.subject
               from filter_results f left join checklist c on c.id=f.checklist_id
               order by f.id desc limit ?""", (int(limit),)
        ).fetchall()
    except Exception:
        rows = []
    c.close()
    out = []
    for r in rows:
        d = dict(r)
        try:
            verdict = json.loads(d.pop("verdict") or "{}")
        except Exception:
            verdict = {}
        d["usage"] = verdict.get("usage") or {}
        out.append(d)
    return out


def cost_repurpose_rows(limit=5000):
    """Every repurpose run with the engine usage captured at run time (may be empty on old runs)."""
    c = _connect()
    try:
        rows = c.execute(
            """select pr.folder, pr.checklist_id, pr.status, pr.model, pr.started_at,
                      pr.finished_at, pr.updated_at, pr.usage_json,
                      c.messageId, c.subject
               from repurpose_runs pr left join checklist c on c.id=pr.checklist_id
               order by pr.updated_at desc limit ?""", (int(limit),)
        ).fetchall()
    except Exception:
        rows = []
    c.close()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["usage"] = json.loads(d.pop("usage_json") or "{}")
        except Exception:
            d["usage"] = {}
        d["created_at"] = d.get("finished_at") or d.get("updated_at") or ""
        out.append(d)
    return out


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
    # N-6: Gmail identity columns live outside the 14-column contract.
    try:
        c.execute(
            "update checklist set messageId=?, rfc822MessageId=?, emailType=? where id=?",
            (row.get("messageId", ""), row.get("rfc822MessageId", ""),
             row.get("emailType") or "press_release", rid),
        )
    except Exception:
        pass
    c.commit()
    c.close()
    return rid


def save_email_link(checklist_id, message_id, subject, meta):
    """Insert one N-3/N-4 link (report/speech/source) for an email.

    `meta` carries the detector output: linkType, url, source, anchor, confidence,
    candidates. A re-run deletes the same (message_id, link_type) row first so the
    table keeps one current row per kind. Returns True on success.
    """
    meta = meta or {}
    link_type = str(meta.get("linkType") or meta.get("articleType") or "report").lower()
    cands = meta.get("reportCandidates") or meta.get("candidates") or []
    if not isinstance(cands, str):
        cands = json.dumps(cands)
    c = _connect()
    try:
        c.execute(
            """CREATE TABLE IF NOT EXISTS email_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT, message_id TEXT, checklist_id INTEGER,
                link_type TEXT, url TEXT, source TEXT, anchor TEXT, confidence REAL,
                is_primary INTEGER DEFAULT 0, candidates_json TEXT, created_at TEXT)"""
        )
        if message_id:
            c.execute("delete from email_links where message_id=? and link_type=?",
                      (message_id, link_type))
        c.execute(
            """insert into email_links
               (message_id, checklist_id, link_type, url, source, anchor, confidence,
                is_primary, candidates_json, created_at)
               values (?,?,?,?,?,?,?,?,?,?)""",
            (message_id or "", checklist_id, link_type, meta.get("url") or "",
             meta.get("source") or meta.get("detectedBy") or "", meta.get("anchor") or "",
             meta.get("confidence"), 1, cands,
             datetime.now(timezone.utc).isoformat()),
        )
        c.commit()
        return True
    finally:
        c.close()


def list_email_links(message_id):
    """All link rows for one email (dicts)."""
    c = _connect()
    try:
        rows = c.execute("select * from email_links where message_id=? order by id",
                         (message_id or "",)).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
    finally:
        c.close()


def primary_links(message_id):
    """Convenience: {link_type: url} for the primary link of each type."""
    out = {}
    for row in list_email_links(message_id):
        t = str(row.get("link_type") or "").lower()
        if t and t not in out and row.get("url"):
            out[t] = row["url"]
    return out


def save_email_media(checklist_id, message_id, rows):
    """Replace the media index for one email (one row per collected image/logo)."""
    rows = rows or []
    c = _connect()
    try:
        c.execute(
            """CREATE TABLE IF NOT EXISTS email_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT, message_id TEXT, checklist_id INTEGER,
                name TEXT, kind TEXT, source TEXT, role TEXT, path TEXT,
                width INTEGER, height INTEGER, bytes INTEGER, sha1 TEXT,
                usable INTEGER, chosen INTEGER, created_at TEXT)"""
        )
        if message_id:
            c.execute("delete from email_media where message_id=?", (message_id,))
        now = datetime.now(timezone.utc).isoformat()
        for r in rows:
            c.execute(
                """insert into email_media
                   (message_id, checklist_id, name, kind, source, role, path, width, height,
                    bytes, sha1, usable, chosen, created_at)
                   values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (message_id or "", checklist_id, r.get("name") or "", r.get("kind") or "",
                 r.get("source") or "", r.get("role") or "", r.get("path") or "",
                 r.get("width"), r.get("height"), r.get("bytes"), r.get("sha1") or "",
                 1 if r.get("usable") else 0, 1 if r.get("chosen") else 0, now),
            )
        c.commit()
        return len(rows)
    finally:
        c.close()


def list_email_media(message_id):
    """All media rows for one email (dicts)."""
    c = _connect()
    try:
        rows = c.execute("select * from email_media where message_id=? order by id",
                         (message_id or "",)).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
    finally:
        c.close()


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
    cols = "c.id, " + ", ".join("c." + col for col in _COLUMNS) + ", c.replySent, c.replyTo, c.replyAt, c.messageId, c.rfc822MessageId, c.emailType, c.created_at"
    try:
        rows = c.execute(
            f"""select {cols},
                       e.from_name as emailFromName, e.from_email as emailFrom,
                       e.links_json as emailLinks, e.attachment_count as emailAttachments,
                       f.status as filterStatus, f.outcome as filterOutcome,
                       f.weighted as filterWeighted, f.gate as filterGate,
                       f.confidence as filterConfidence, f.error as filterError,
                       f.verdict as filterVerdict, f.created_at as filteredAt,
                       (select url from email_links where message_id=c.messageId and link_type='report' limit 1) as reportUrl,
                       (select url from email_links where message_id=c.messageId and link_type='speech' limit 1) as speechUrl,
                       (select count(*) from email_media where message_id=c.messageId) as mediaCount,
                       (select count(*) from email_media where message_id=c.messageId and source='gallery') as galleryMedia
                from checklist c
                left join emails e on e.message_id = c.messageId
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


def clear_gmail_watch():
    """Forget the stored watch cursor (used when the webhook is switched off)."""
    c = _connect()
    c.execute("delete from gmail_watch where id=1")
    c.commit()
    c.close()


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

# --- Local auth + audit (T-047) ---------------------------------------------

def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def count_users():
    c = _connect()
    n = c.execute("select count(*) from users").fetchone()[0]
    c.close()
    return n


def get_user_by_username(username):
    c = _connect()
    r = c.execute("select * from users where username=?", ((username or "").strip(),)).fetchone()
    c.close()
    return dict(r) if r else None


def get_user(user_id):
    c = _connect()
    r = c.execute("select * from users where id=?", (user_id,)).fetchone()
    c.close()
    return dict(r) if r else None


def list_users():
    c = _connect()
    rows = c.execute(
        "select id, username, role, active, must_change_password, created_at, updated_at, last_login_at "
        "from users order by username collate nocase"
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]


def create_user(username, password_hash, role, must_change_password=0):
    username = (username or "").strip()
    now = _now_iso()
    c = _connect()
    cur = c.execute(
        "insert into users (username,password_hash,role,active,must_change_password,created_at,updated_at) "
        "values (?,?,?,?,?,?,?)",
        (username, password_hash, role, 1, 1 if must_change_password else 0, now, now),
    )
    uid = cur.lastrowid
    c.commit()
    c.close()
    return uid


def update_user(user_id, role=None, active=None, must_change_password=None):
    fields, vals = [], []
    if role is not None:
        fields.append("role=?")
        vals.append(role)
    if active is not None:
        fields.append("active=?")
        vals.append(1 if active else 0)
    if must_change_password is not None:
        fields.append("must_change_password=?")
        vals.append(1 if must_change_password else 0)
    if not fields:
        return
    fields.append("updated_at=?")
    vals.append(_now_iso())
    vals.append(user_id)
    c = _connect()
    c.execute(f"update users set {', '.join(fields)} where id=?", vals)
    c.commit()
    c.close()


def set_user_password(user_id, password_hash, must_change_password=0):
    c = _connect()
    c.execute(
        "update users set password_hash=?, must_change_password=?, updated_at=? where id=?",
        (password_hash, 1 if must_change_password else 0, _now_iso(), user_id),
    )
    c.commit()
    c.close()


def set_last_login(user_id):
    c = _connect()
    c.execute("update users set last_login_at=? where id=?", (_now_iso(), user_id))
    c.commit()
    c.close()


def count_active_admins(exclude_id=None):
    c = _connect()
    sql = "select count(*) from users where role='admin' and active=1"
    args = ()
    if exclude_id is not None:
        sql += " and id<>?"
        args = (exclude_id,)
    n = c.execute(sql, args).fetchone()[0]
    c.close()
    return n


def create_session(token_hash, user_id, csrf_token, expires_at, ip="", user_agent=""):
    c = _connect()
    c.execute(
        "insert into sessions (token_hash,user_id,csrf_token,created_at,expires_at,ip,user_agent) "
        "values (?,?,?,?,?,?,?)",
        (token_hash, user_id, csrf_token, _now_iso(), int(expires_at), ip or "", user_agent or ""),
    )
    c.commit()
    c.close()


def get_session(token_hash):
    """Return the session + user fields, or None when missing/expired/inactive."""
    c = _connect()
    r = c.execute(
        "select s.token_hash, s.user_id, u.id as id, s.csrf_token, s.created_at, s.expires_at, s.ip, s.user_agent, "
        "u.username, u.role, u.active, u.must_change_password, u.last_login_at "
        "from sessions s join users u on u.id=s.user_id "
        "where s.token_hash=? and s.expires_at>? and u.active=1",
        (token_hash, int(time.time())),
    ).fetchone()
    c.close()
    return dict(r) if r else None


def delete_session(token_hash):
    c = _connect()
    c.execute("delete from sessions where token_hash=?", (token_hash,))
    c.commit()
    c.close()


def delete_user_sessions(user_id, except_hash=None):
    c = _connect()
    if except_hash:
        c.execute("delete from sessions where user_id=? and token_hash<>?", (user_id, except_hash))
    else:
        c.execute("delete from sessions where user_id=?", (user_id,))
    c.commit()
    c.close()


def cleanup_sessions():
    c = _connect()
    cur = c.execute("delete from sessions where expires_at<=?", (int(time.time()),))
    c.commit()
    c.close()
    return cur.rowcount


def record_login_attempt(username, ip, ok):
    c = _connect()
    c.execute(
        "insert into login_attempts (username,ip,ok,attempted_at) values (?,?,?,?)",
        ((username or "").strip(), ip or "", 1 if ok else 0, int(time.time())),
    )
    c.commit()
    c.close()


def count_login_failures(username, ip, since_epoch):
    c = _connect()
    n = c.execute(
        "select count(*) from login_attempts where ok=0 and attempted_at>=? "
        "and (lower(username)=lower(?) or ip=?)",
        (int(since_epoch), (username or "").strip(), ip or ""),
    ).fetchone()[0]
    c.close()
    return n


def clear_login_attempts(username):
    c = _connect()
    c.execute("delete from login_attempts where lower(username)=lower(?)", ((username or "").strip(),))
    c.commit()
    c.close()


def cleanup_login_attempts(before_epoch):
    c = _connect()
    cur = c.execute("delete from login_attempts where attempted_at<?", (int(before_epoch),))
    c.commit()
    c.close()
    return cur.rowcount


def add_audit(actor_id, actor_username, action, target_type="", target_id="",
              before_json="", after_json="", ip="", user_agent=""):
    c = _connect()
    c.execute(
        "insert into audit_log (actor_id,actor_username,action,target_type,target_id,"
        "before_json,after_json,ip,user_agent,created_at) values (?,?,?,?,?,?,?,?,?,?)",
        (actor_id, actor_username or "", action, target_type or "", str(target_id or ""),
         before_json or "", after_json or "", ip or "", user_agent or "", _now_iso()),
    )
    c.commit()
    c.close()


def list_audit(limit=100):
    c = _connect()
    rows = c.execute(
        "select id,actor_id,actor_username,action,target_type,target_id,before_json,after_json,"
        "ip,user_agent,created_at from audit_log order by id desc limit ?",
        (int(limit),),
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]


def add_filter_version(config_hash, snapshot_json, actor_id, actor_username, action, restored_from=None):
    c = _connect()
    cur = c.execute(
        "insert into filter_config_versions (config_hash,snapshot_json,actor_id,actor_username,"
        "action,restored_from,created_at) values (?,?,?,?,?,?,?)",
        (config_hash, snapshot_json, actor_id, actor_username or "", action,
         restored_from, _now_iso()),
    )
    vid = cur.lastrowid
    c.commit()
    c.close()
    return vid


def list_filter_versions(limit=50):
    c = _connect()
    rows = c.execute(
        "select id,config_hash,actor_id,actor_username,action,restored_from,created_at "
        "from filter_config_versions order by id desc limit ?",
        (int(limit),),
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]


def get_filter_version(version_id):
    c = _connect()
    r = c.execute("select * from filter_config_versions where id=?", (version_id,)).fetchone()
    c.close()
    if not r:
        return None
    d = dict(r)
    try:
        d["snapshot"] = json.loads(d.get("snapshot_json") or "{}")
    except Exception:
        d["snapshot"] = {}
    return d


# --- Repurpose engine state (T-050 / D40) ------------------------------------

_REPURPOSE_RUN_FIELDS = ("checklist_id", "filter_result_id", "status", "model", "started_at",
                         "finished_at", "error", "usage_json", "run_json", "draft_path", "site_path",
                         "article_id")


def save_repurpose_export(checklist_id, filter_result_id=None, folder="", dest="",
                          article_hash="", config_hash="", weighted=None,
                          status="exported"):
    """Record one ACCEPT -> inbox export, keyed by the checklist row."""
    c = _connect()
    c.execute(
        """insert into repurpose_exports
           (checklist_id, filter_result_id, folder, dest, article_hash, config_hash,
            weighted, status, exported_at)
           values (?,?,?,?,?,?,?,?,?)
           on conflict(checklist_id) do update set
             filter_result_id=excluded.filter_result_id, folder=excluded.folder,
             dest=excluded.dest, article_hash=excluded.article_hash,
             config_hash=excluded.config_hash, weighted=excluded.weighted,
             status=excluded.status, exported_at=excluded.exported_at""",
        (int(checklist_id), filter_result_id, folder, dest, article_hash or "",
         config_hash or "", weighted, status, _now_iso()),
    )
    c.commit()
    c.close()


def list_repurpose_exports(limit=500):
    c = _connect()
    rows = c.execute("select * from repurpose_exports order by id desc limit ?",
                     (int(limit),)).fetchall()
    c.close()
    return [dict(r) for r in rows]


def get_repurpose_export(checklist_id):
    c = _connect()
    r = c.execute("select * from repurpose_exports where checklist_id=?",
                  (int(checklist_id),)).fetchone()
    c.close()
    return dict(r) if r else None


def upsert_repurpose_run(folder, **fields):
    """Mirror one folder's `run.json` into the DB (the file stays the contract)."""
    data = {k: v for k, v in fields.items() if k in _REPURPOSE_RUN_FIELDS}
    data["folder"] = folder
    data["updated_at"] = _now_iso()
    cols = ", ".join(data)
    marks = ", ".join("?" for _ in data)
    updates = ", ".join(f"{k}=excluded.{k}" for k in data if k != "folder")
    c = _connect()
    c.execute(f"insert into repurpose_runs ({cols}) values ({marks}) "
              f"on conflict(folder) do update set {updates}", tuple(data.values()))
    c.commit()
    c.close()
    return get_repurpose_run(folder)


def get_repurpose_run(folder):
    c = _connect()
    r = c.execute("select * from repurpose_runs where folder=?", (folder,)).fetchone()
    c.close()
    return dict(r) if r else None


def list_repurpose_runs(limit=200):
    c = _connect()
    rows = c.execute("select * from repurpose_runs order by updated_at desc limit ?",
                     (int(limit),)).fetchall()
    c.close()
    return [dict(r) for r in rows]


def add_repurpose_event(folder, stage, status, detail="", article_id=""):
    c = _connect()
    c.execute("insert into repurpose_events (folder,stage,status,detail,article_id,created_at) "
              "values (?,?,?,?,?,?)", (folder or "", stage or "", status or "",
                                       detail or "", str(article_id or ""), _now_iso()))
    c.commit()
    c.close()


def list_repurpose_events(folder=None, limit=100):
    c = _connect()
    if folder:
        rows = c.execute("select * from repurpose_events where folder=? order by id desc limit ?",
                         (folder, int(limit))).fetchall()
    else:
        rows = c.execute("select * from repurpose_events order by id desc limit ?",
                         (int(limit),)).fetchall()
    c.close()
    return [dict(r) for r in rows]
