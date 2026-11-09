# =============================================================================
# FILE HEADER
# file    : msme/repurpose/runner.py
# role    : Repurpose — in-process engine runner (T-050 / D40)
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : run the vendored repurpose engine inside the app: one daemon worker thread, one
#           article at a time, mirroring run.json into the repurpose_runs table.
# pages   : backs /repurpose.html + /api/repurpose/status
# calls   : msme.config, msme.db, msme.paths, engine.config, engine.scan, engine.run, engine.manifest
# called  : msme/__main__.py (start), dashboard.py (status/trigger)
# amend   : never run two engine calls at once; never block the web request; run.json stays the
#           folder contract and the DB is the mirror. Test: python3 -m unittest tests.test_repurpose_runner
# =============================================================================
"""In-process repurpose runner: the engine, one article at a time."""
import json
import threading
import time
from datetime import datetime, timezone

from msme import config, db, paths, settings_store
from msme.repurpose.engine import config as engine_config
from msme.repurpose.engine import manifest, run as engine_run, scan

_LOCK = threading.Lock()
_THREAD = None
_STOP = threading.Event()
_STATE = {"running": False, "folder": "", "last_error": ""}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_cfg():
    return engine_config.load_config()


def pending_folders(cfg=None):
    """Folders with a release text and no draft/run yet (the engine's 'pending')."""
    cfg = cfg or build_cfg()
    return [i for i in scan.scan_all(cfg) if i.get("status") == "pending"]


def _export_for_folder(folder):
    for rec in db.list_repurpose_exports(limit=2000):
        if rec.get("folder") == folder:
            return rec
    return {}


def run_folder(folder, call=None):
    """Run one folder through the engine and mirror the result into the DB."""
    cfg = build_cfg()
    items = scan.select_queue(cfg, folder=folder)
    if not items:
        raise RuntimeError(f"folder not found in the inbox: {folder}")
    item = items[0]
    started = _now()
    db.add_repurpose_event(folder, "run", "started", "")
    try:
        result, status = engine_run.run_one(cfg, item, call=call)
    except Exception as e:
        db.upsert_repurpose_run(folder, status="error", model=cfg["llm"]["model"],
                                started_at=started, finished_at=_now(), error=str(e)[:500])
        db.add_repurpose_event(folder, "run", "error", str(e)[:500])
        raise
    run = manifest.read(paths.REPURPOSE_INBOX / folder) or {}
    export = _export_for_folder(folder)
    db.upsert_repurpose_run(
        folder,
        checklist_id=export.get("checklist_id"),
        filter_result_id=export.get("filter_result_id"),
        status=status,
        model=cfg["llm"]["model"],
        started_at=started,
        finished_at=_now(),
        error="" if status in ("validated", "rendered") else run.get("error", ""),
        usage_json=json.dumps(run.get("usage") or {}, ensure_ascii=False),
        run_json=json.dumps(run, ensure_ascii=False),
        draft_path=str(paths.REPURPOSE_INBOX / folder / "draft.md"),
        site_path=str(paths.REPURPOSE_SITE),
    )
    db.add_repurpose_event(folder, "run", status,
                           "ok" if result.get("ok") else "validator failed")
    return {"folder": folder, "status": status, "ok": bool(result.get("ok"))}


def _poll_seconds():
    try:
        return int(settings_store.get("REPURPOSE_POLL_SECONDS") or config.REPURPOSE_POLL_SECONDS)
    except (TypeError, ValueError):
        return config.REPURPOSE_POLL_SECONDS


def _loop(once=False, stop_event=None):
    stop = stop_event or _STOP
    while not stop.is_set():
        items = pending_folders()
        if not items:
            if once:
                return
            stop.wait(_poll_seconds())
            continue
        for item in items:
            if stop.is_set():
                return
            with _LOCK:
                _STATE.update(running=True, folder=item["folder"], last_error="")
                try:
                    run_folder(item["folder"])
                except Exception as e:
                    _STATE["last_error"] = str(e)[:500]
                finally:
                    _STATE.update(running=False, folder="")
            if once:
                return
        if once:
            return


def start():
    """Start the daemon worker when REPURPOSE_INPROCESS=true (called by msme.__main__)."""
    global _THREAD
    if not config.REPURPOSE_INPROCESS:
        print("[repurpose] in-process runner disabled (REPURPOSE_INPROCESS=false)")
        return None
    if _THREAD and _THREAD.is_alive():
        return _THREAD
    db.init_db()
    _THREAD = threading.Thread(target=_loop, name="repurpose-worker", daemon=True)
    _THREAD.start()
    print("[repurpose] in-process runner started")
    return _THREAD


def trigger(folder=None):
    """Run one folder (or the next pending) in a short-lived thread; false when busy."""
    if _STATE["running"]:
        return False

    def work():
        with _LOCK:
            _STATE.update(running=True, folder=folder or "", last_error="")
            try:
                if folder:
                    run_folder(folder)
                else:
                    items = pending_folders()
                    if items:
                        run_folder(items[0]["folder"])
            except Exception as e:
                _STATE["last_error"] = str(e)[:500]
            finally:
                _STATE.update(running=False, folder="")

    threading.Thread(target=work, name="repurpose-trigger", daemon=True).start()
    return True


def status():
    return {
        "inprocess": bool(config.REPURPOSE_INPROCESS),
        "running": bool(_STATE["running"]),
        "folder": _STATE["folder"],
        "last_error": _STATE["last_error"],
        "pending": len(pending_folders()),
        "runs": db.list_repurpose_runs(50),
        "exports": db.list_repurpose_exports(50),
    }


def run_once():
    """CLI: process the current pending queue once."""
    db.init_db()
    _loop(once=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_once())
