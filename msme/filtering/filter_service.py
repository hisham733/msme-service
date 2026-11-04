# =============================================================================
# FILE HEADER
# file    : msme/filtering/filter_service.py
# role    : Filter — FastAPI sub-app behind the combined :8899 entrypoint
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : serve the filter/lab/testfilter/report pages and the verdict dashboard; run reports and write
#           Excel/CSV/TSV outputs into docs/; record versioned filter-config saves and admin restores.
# pages   : filter, verdicts, workflow, logs, config, lab, testfilter, report (served at /reportmanager.html)
# calls   : filter.judge, filter_log, docs/*.xlsx|json, settings_store (lazy)
# called  : combined.py (as a sub-app); the browser pages
# amend   : report paths are hard-coded to docs/ (decisions/D4); the report reads
#           config.REPORT_ARCHIVE_DIR (all_emails), one version per group via archive_layout;
#           page routes must match static/INDEX.md. Test: curl -s localhost:8899/filters.json and
#           GET /report/duplicates
# =============================================================================
"""Filter routes — the Jev Stage-1 editorial judge.

Mounted behind the combined :8899 entrypoint. The receive pipeline calls the
same judge in-process for ready articles; these routes remain for manual,
lab and report use.

Example:
    curl -X POST :8900/filter -H 'Content-Type: application/json' -d '{
      "subject": "Fwd: [PRESS RELEASE] ...",
      "from": "Editor MSME <editor@malaysiasme.com.my>",
      "date": "Wed, 30 Sep 2026",
      "bodyText": "KUALA LUMPUR, 29 Sep 2026 - ..."
    }'
    -> {"outcome": "ACCEPT", "weighted": 78, "gate": null, ...}
"""
import json
import os
import time

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from msme import auth, config, db, paths
from msme.filtering import filter as filter_judge
from msme.filtering import filter_log
from msme.receive import archive_layout as AL

app = FastAPI(title="MSME Filter Service (Jev)")

_STATIC_DIR = str(paths.STATIC)

# Simple verdict log so each judgement leaves a trail (JSONL line appended).
_VERDICT_LOG = filter_log.VERDICT_LOG
# Error trail (failed/exception judgements) for the Logs page.
_ERROR_LOG = filter_log.ERROR_LOG
# Report-run trail + live progress (so you can see the Jev calls when you click RUN).
_RUN_LOG = str(paths.DOCS / "report-runs.jsonl")
REPORT_STATE = {"running": False, "done": 0, "total": 0, "source": "", "started": None, "rows": 0, "last": None}


def _log_run(rec):
    try:
        with open(_RUN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    try:
        print(f"[report] run source={rec.get('source')} rows={rec.get('rows')} "
              f"jev_calls={rec.get('jev_calls')} tokens={rec.get('tokens')} sec={rec.get('seconds')}", flush=True)
    except Exception:
        pass


def _serve(name):
    path = os.path.join(_STATIC_DIR, name)
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail=f"{name} not found")


@app.get("/")
def index():
    return _serve("filter.html")


@app.get("/filter.html")
def filter_html():
    return _serve("filter.html")


@app.get("/verdicts.html")
def verdicts_html():
    return _serve("verdicts.html")


@app.get("/workflow.html")
def workflow_html():
    return _serve("workflow.html")


@app.get("/logs.html")
def logs_html():
    return _serve("logs.html")


@app.get("/config.html")
def config_html():
    return _serve("config.html")


class ArticleIn(BaseModel):
    subject: str = ""
    from_email: str = ""
    date: str = ""
    bodyText: str = ""


def _log(article, verdict):
    """Append one verdict to the shared filter verdict trail."""
    filter_log.log_verdict(article, verdict, source="manual")

def _log_error(article, error):
    """Append a failed judgement to the shared error trail."""
    filter_log.log_error(article, error)


def _read_jsonl(path, limit=200):
    out = []
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            out.append(json.loads(line))
                        except Exception:
                            pass
    except Exception:
        pass
    return out[-limit:]


@app.get("/health")
def health():
    return {"status": "ok", "service": "filter", "model": config.JEV_MODEL}


@app.get("/filters.json")
def filters_json():
    """Return the 14-rule battery for reference."""
    return {"battery": filter_judge.battery()}


@app.post("/filter")
def run_filter(article: ArticleIn):
    """Judge one article -> {outcome: ACCEPT|REJECT, weighted, gate, ...}."""
    a = {"subject": article.subject, "from": article.from_email, "date": article.date, "bodyText": article.bodyText}
    try:
        verdict = filter_judge.judge(a)
        verdict["input"] = {
            "subject": a["subject"][:120],
            "from": a["from"][:80],
            "date": a["date"],
            "bodyTextLen": len(a["bodyText"] or ""),
        }
        _log(a, verdict)
        return verdict
    except Exception as e:
        _log_error(a, e)
        return {"outcome": "ERROR", "error": str(e)}


def _extract_upload(data: bytes, filename: str) -> str:
    """Extract plain text from an uploaded .md/.txt/.pdf/.docx file."""
    name = (filename or "").lower()
    if name.endswith((".pdf", ".docx", ".doc")):
        from msme.receive.extract import extract_text_from_bytes

        return extract_text_from_bytes(data, filename) or ""
    # plain text (md/txt) — strip UTF-8 BOM if present
    return data.decode("utf-8", "replace").lstrip("\ufeff")


@app.post("/filter-upload")
async def run_filter_upload(
    file: UploadFile = File(...),
    subject: str = Form(""),
    from_email: str = Form(""),
    date: str = Form(""),
):
    """Upload an article file (.md/.txt/.pdf/.docx) and judge it with Jev.

    PDF/DOCX text is extracted server-side (browsers can't read those formats).
    Returns the same verdict shape as /filter, plus `extracted` text preview.
    """
    data = await file.read()
    filename = file.filename or "article"
    try:
        text = _extract_upload(data, filename)
    except Exception as e:
        return {"outcome": "ERROR", "error": f"could not read {filename}: {e}"}

    if not text.strip():
        return {"outcome": "ERROR", "error": f"no readable text found in {filename}"}

    # subject defaults to the file name if not provided
    a = {
        "subject": subject or os.path.splitext(os.path.basename(filename))[0],
        "from": from_email,
        "date": date,
        "bodyText": text[:12000],
    }
    try:
        verdict = filter_judge.judge(a)
        verdict["input"] = {
            "subject": a["subject"][:120],
            "from": a["from"][:80],
            "date": a["date"],
            "file": filename,
            "bodyTextLen": len(a["bodyText"] or ""),
        }
        verdict["extracted"] = text[:600]
        _log(a, verdict)
        return verdict
    except Exception as e:
        _log_error(a, e)
        return {"outcome": "ERROR", "error": str(e)}


@app.get("/verdicts")
def verdicts():
    """Return recent verdicts from the JSONL trail (for review)."""
    return {"verdicts": _read_jsonl(_VERDICT_LOG, limit=50)}


@app.post("/clear")
def clear_data():
    """Empty the verdict + error trails (keeps the files, just truncates them)."""
    cleared = {"verdicts": 0, "errors": 0}
    for path, key in ((_VERDICT_LOG, "verdicts"), (_ERROR_LOG, "errors")):
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8"):
                pass
            cleared[key] = 1
        except Exception as e:
            cleared[key + "_error"] = str(e)
    return {"ok": True, "cleared": cleared}


@app.get("/logs.json")
def logs_json():
    """Return combined logs: successful verdicts + errors (for the Logs page)."""
    verdicts_list = _read_jsonl(_VERDICT_LOG, limit=200)
    errors = _read_jsonl(_ERROR_LOG, limit=200)
    return {"logs": verdicts_list, "errors": errors}


@app.get("/config.json")
def config_json():
    """Return the filter's live configuration (masked) + the 14-rule battery."""
    from msme import config as cfg
    from msme.filtering import filter_llm

    return {
        "config": {
            "model": cfg.JEV_MODEL,
            "gateThreshold": cfg.GATE_THRESHOLD,
            "acceptThreshold": filter_judge.accept_threshold(),
            "apiKeyMasked": (cfg.TYPESAFE_API_KEY[:12] + "…" if cfg.TYPESAFE_API_KEY else ""),
            "baseUrl": cfg.TYPESAFE_BASE_URL,
            "llmAssist": filter_llm.enabled(),
        },
        "battery": filter_judge.battery(),
    }


def _actor(request):
    return auth.actor_from_scope(getattr(request, "scope", {})) if request is not None else None


def _record_filter_version(action, request, before, before_hash, restored_from=None):
    """Persist the effective battery after a config change and write an audit row."""
    actor = _actor(request) or {}
    snap, chash = filter_judge.config_version_snapshot()
    diff = filter_judge.config_diff((before or {}).get("battery") or {},
                                    snap.get("battery") or {})
    vid = db.add_filter_version(chash, json.dumps(snap, ensure_ascii=False),
                                actor.get("id"), actor.get("username", ""), action, restored_from)
    auth.audit(f"filter_config.{action}", actor=actor, target_type="filter_config",
               target_id=vid, before={"config_hash": before_hash},
               after={"config_hash": chash, "changed": diff,
                      **({"restored_from": restored_from} if restored_from else {})},
               scope=getattr(request, "scope", None))
    return vid, chash, diff


@app.put("/config.json")
def update_config_json(patch: dict, request: Request):
    """Save live rubric edits + filter settings, recording a version.

    Body: {"gates": {"is_it_commercial_intent": {"instructions": "..."}},
           "scores": {"no_substance": {"weight": 3}},
           "settings": {"ENABLE_LLM_ASSIST": false}}
    Changes take effect on the NEXT judgement (no restart).
    """
    try:
        before, before_hash = filter_judge.config_version_snapshot()
        saved = {}
        # Editors may only change the filter rubric settings — never receive/AI keys.
        settings_patch = {k: v for k, v in (patch.get("settings") or {}).items()
                          if k in ("ENABLE_LLM_ASSIST", "ACCEPT_THRESHOLD")}
        if settings_patch:
            from msme import settings_store
            settings_store.save(settings_patch)
            saved["settings"] = settings_patch
        rubric_patch = {k: v for k, v in (patch or {}).items() if k in ("gates", "scores")}
        if rubric_patch:
            saved["rubric"] = filter_judge.update_settings(rubric_patch)
        vid, chash, diff = _record_filter_version("save", request, before, before_hash)
        return {"ok": True, "saved": saved, "version": vid,
                "config_hash": chash, "changed": diff}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/config-versions")
def config_versions(limit: int = 50):
    """Filter-config version history (newest first, full snapshots on detail)."""
    return {"versions": db.list_filter_versions(max(1, min(int(limit), 200)))}


@app.get("/config-versions/{version_id}")
def config_version(version_id: int):
    version = db.get_filter_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="version not found")
    return version


@app.post("/config-versions/{version_id}/restore")
def config_version_restore(version_id: int, request: Request):
    """Admin-only restore; always creates a NEW version (history is never rewritten)."""
    actor = _actor(request) or {}
    if actor.get("role") != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    version = db.get_filter_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="version not found")
    before, before_hash = filter_judge.config_version_snapshot()
    filter_judge.restore_config_version(version.get("snapshot") or {})
    vid, chash, diff = _record_filter_version("restore", request, before, before_hash,
                                              restored_from=version_id)
    return {"ok": True, "version": vid, "config_hash": chash,
            "restored_from": version_id, "changed": diff}


@app.get("/lab.html")
def lab_page():
    """Serve the Jev Lab dashboard (test any question alone or batched)."""
    return _serve("lab.html")


@app.get("/lab/payload")
def lab_payload(file: str = "artical.json"):
    """Return a JSON payload from docs/ (default artical.json) for the Lab to preload.

    `file` is a basename only (path traversal blocked). Examples:
        /lab/payload                         -> docs/artical.json
        /lab/payload?file=jev-variants.json  -> docs/jev-variants.json
    """
    docs = str(paths.DOCS)
    name = os.path.basename(file or "artical.json")
    p = os.path.join(docs, name)
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return {"ok": True, "file": name, "payload": json.load(f)}
        except Exception as e:
            return {"ok": False, "error": f"{name} invalid: {e}"}
    return {"ok": False, "error": f"no docs/{name}"}


@app.post("/lab/ask")
def lab_ask(req: dict):
    """Run the given questions against Jev, ALONE (one call per question) or BATCH (one call).

    Body:
      {
        "state":     {subject, from, date, bodyText},
        "questions": {id: {type, instructions, criteria}},   # optional -> live battery
        "mode":      "alone" | "batch"
      }
    Returns per-question noul (+ errors + token usage).
    """
    from msme import config as cfg
    from msme.filtering import filter as F
    state = req.get("state") or {}
    questions = req.get("questions") or F.build_questions()
    mode = (req.get("mode") or "batch").lower()
    results, errors = {}, {}
    usage_total = 0
    model = cfg.JEV_MODEL

    def _usage(resp):
        u = resp.get("usage") or {}
        return u.get("total") or (u.get("input_tokens", 0) + u.get("output_tokens", 0))

    if mode == "alone":
        for qid, q in questions.items():
            try:
                resp = F._post({"state": state, "model": cfg.JEV_MODEL, "questions": {qid: q}})
                ans = (resp.get("answers") or {}).get(qid) or {}
                results[qid] = ans.get("noul")
                usage_total += _usage(resp)
                model = resp.get("model", model)
            except Exception as e:
                errors[qid] = str(e)
    else:
        try:
            resp = F._post({"state": state, "model": cfg.JEV_MODEL, "questions": questions})
            for qid in questions:
                ans = (resp.get("answers") or {}).get(qid) or {}
                if ans:
                    results[qid] = ans.get("noul")
            usage_total += _usage(resp)
            model = resp.get("model", model)
        except Exception as e:
            errors["_batch"] = str(e)
    return {"mode": mode, "model": model, "results": results, "errors": errors, "usage_total": usage_total}


def _test_root():
    return os.path.join(_archived_dir(), "test filter emails")


def _tests_main_md(folder_path):
    if not os.path.isdir(folder_path):
        return ""
    mds = [f for f in os.listdir(folder_path)
           if f.endswith(".md") and f.lower() != "link.md"]
    if not mds:
        return ""
    return max(mds, key=lambda f: os.path.getsize(os.path.join(folder_path, f)))


@app.get("/testfilter.html")
def testfilter_page():
    """Serve the per-article filter-variant dashboard."""
    return _serve("testfilter.html")


@app.get("/testfilter/articles")
def testfilter_articles():
    """List ALL archived articles under emails/ (incl. the 'test filter emails' subfolder)."""
    root = _archived_dir()
    out = []
    if os.path.isdir(root):
        for dirpath, _dirs, _files in os.walk(root):
            md = _tests_main_md(dirpath)
            if md:
                out.append({"folder": os.path.relpath(dirpath, root), "md": md, "hasArticle": True})
    out.sort(key=lambda r: r["folder"])
    return {"articles": out}


@app.get("/testfilter/article")
def testfilter_article(folder: str = ""):
    """Return one archived article's subject + bodyText (folder relative to emails/)."""
    root = _archived_dir()
    rel = os.path.normpath(folder or "")
    if rel.startswith("..") or os.path.isabs(rel):
        return {"error": "invalid folder"}
    d = os.path.join(root, rel)
    md = _tests_main_md(d)
    if not md:
        return {"error": f"no article in {folder}"}
    try:
        with open(os.path.join(d, md), encoding="utf-8", errors="replace") as f:
            body = f.read()
    except Exception as e:
        return {"error": str(e)}
    return {"subject": os.path.basename(rel), "md": md, "bodyText": body}


@app.get("/reportmanager.html")
def reportmanager_page():
    """Serve the report-manager UI (pick a variant, run, download the Excel)."""
    return _serve("report.html")


def _folder_param(folder):
    """Validate a report folder selection (relative to the archive root)."""
    rel = os.path.normpath(str(folder or "")).strip()
    if rel in ("", "."):
        return ""
    if os.path.isabs(rel) or rel.startswith("..") or rel.startswith(("_", ".")):
        raise HTTPException(status_code=400, detail="invalid folder")
    return rel.replace(os.sep, "/")


def _version_groups(folder=""):
    """Group the report root's article folders by version base, optionally one folder."""
    groups = AL.group_versions(_archive_root())
    if folder:
        for base in list(groups):
            groups[base] = AL.filter_by_folder(groups[base], folder)
            if not groups[base]:
                del groups[base]
    return groups


def _chosen_articles(folder=""):
    """One article folder per version group: keep-map, else newest complete copy."""
    keep = AL.load_keepmap(_keepmap_path())
    chosen = []
    for base, items in _version_groups(folder).items():
        pick = AL.choose_version(items, keep=keep, base=base)
        if pick:
            chosen.append((base, pick, items))
    chosen.sort(key=lambda x: x[1]["rel"])
    return chosen


def _list_articles(folder=""):
    """Report rows: one chosen version per base folder under the live archive.

    `folder` limits the run to one top-level bucket (e.g. the 15+ or 14- folder).
    Returns (folder_rel, path, md).
    """
    return [(pick["rel"], pick["path"], pick["md"])
            for _base, pick, _items in _chosen_articles(folder)]


def _versions_payload(folder=""):
    """Every version group with its used copy and the skipped copies."""
    keep = AL.load_keepmap(_keepmap_path())
    groups = []
    for base, items in sorted(_version_groups(folder).items()):
        pick = AL.choose_version(items, keep=keep, base=base)
        groups.append({
            "base": base,
            "used": pick["name"] if pick else "",
            "used_rel": pick["rel"] if pick else "",
            "versions": [{
                "name": item["name"],
                "rel": item["rel"],
                "md": item["md"],
                "chars": item["chars"],
                "mtime": item["mtime"],
                "used": bool(pick and item["rel"] == pick["rel"]),
                "empty": not bool(item["md"]),
            } for item in sorted(items, key=lambda i: i["mtime"])],
        })
    dupes = [g for g in groups if len(g["versions"]) > 1]
    return {"root": _archive_root(), "folder": folder, "groups": groups,
            "duplicates": dupes, "duplicate_groups": len(dupes),
            "folders_in_duplicates": sum(len(g["versions"]) for g in dupes)}


def _report_folders():
    """Top-level report folders with their article counts (for the UI selector)."""
    folders = AL.top_folders(_archive_root())
    total = len(_list_articles())
    return {"root": _archive_root(), "folders": folders, "total": total}


def _report_norm(s):
    import re
    s = re.sub(r"^(fwd|fw|re):\s*", "", (s or "").strip(), flags=re.I)
    s = re.sub(r"\[[^\]]*\]", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _read_questions_from_xlsx(path):
    """Read {name: {instructions, criteria}} from a gates-def Excel (one sheet per question)."""
    from openpyxl import load_workbook
    wb = load_workbook(path, data_only=True)
    out = {}
    for ws in wb.worksheets:
        if ws.title == "index":
            continue
        d = {}
        for r in ws.iter_rows(values_only=True):
            if r and r[0] is not None:
                d[str(r[0])] = r[1] if len(r) > 1 else ""
        name = (d.get("Name") or "").strip()
        instr = d.get("Instruction") or ""
        if not name or not instr:
            continue
        out[name] = {"type": "noul", "instructions": instr,
                     "criteria": {"true": d.get("True") or "", "false": d.get("False") or ""},
                     "kind": (str(d.get("Kind") or "")).strip().lower(),
                     "label": (str(d.get("Label") or "").strip() or name),
                     "threshold": d.get("Threshold"), "weight": d.get("Weight")}
    return out


@app.get("/report/files")
def report_files():
    """List selectable question Excel files in docs/."""
    docs = str(paths.DOCS)
    files = []
    if os.path.isdir(docs):
        for f in sorted(os.listdir(docs)):
            if f.endswith(".xlsx") and (f.startswith("gates-def") or f.startswith("gates def")):
                files.append(f)
    return {"files": files}


@app.get("/report/folders")
def report_folders():
    """Top-level archive folders the report can run against (with article counts)."""
    return _report_folders()


@app.get("/report/duplicates")
def report_duplicates(folder: str = ""):
    """Every version group in the report archive + the copy each run will use."""
    return _versions_payload(_folder_param(folder))


@app.get("/report/status")
def report_status():
    """Live progress of the current report run (so you can see Jev calls happening)."""
    st = dict(REPORT_STATE)
    if st.get("started") and st.get("running"):
        st["elapsed"] = round(time.time() - st["started"], 1)
    return st


@app.get("/report/history")
def report_history(limit: int = 20):
    """Recent report runs (ts, source, rows, jev_calls, tokens, seconds, file)."""
    runs = []
    if os.path.exists(_RUN_LOG):
        try:
            with open(_RUN_LOG, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        runs.append(json.loads(line))
        except Exception:
            runs = []
    return {"runs": runs[-limit:][::-1]}



def _do_report(variant, xfile, include_neg, since="2026-10-05", until="", folder=""):
    """Run the whole battery using the SELECTED Excel/variant wordings and write an Excel report."""
    from msme import config as cfg
    from msme.filtering import filter as F
    variant = str(variant or "base")          # base | 1 | 2 | 3
    xfile = str(xfile or "").strip()          # e.g. gates-def-2.xlsx (source Excel)
    include_neg = include_neg is not False
    since = (str(since or "")).strip()        # YYYY-MM-DD (default 2026-10-05)
    until = (str(until or "")).strip()
    folder = _folder_param(folder)
    lab = (F._load_lab().get("questions") or {})

    src = {}
    if xfile:
        docs0 = str(paths.DOCS)
        xp = os.path.join(docs0, os.path.basename(xfile))
        if os.path.exists(xp):
            try:
                src = _read_questions_from_xlsx(xp)
            except Exception:
                src = {}

    if src:
        # the chosen Excel FULLY defines the battery (names, kind, weights, thresholds, wording)
        gates = [n for n, v in src.items() if (v.get("kind") or "") == "gate"]
        scores = [n for n, v in src.items() if (v.get("kind") or "") == "score"]
        THR = {n: float(src[n].get("threshold") or 0.85) for n in gates}
        W = {n: float(src[n].get("weight") or 0) for n in scores}
        Q = {n: {"type": "noul", "instructions": src[n]["instructions"],
                 "criteria": src[n]["criteria"]} for n in gates + scores}
        source = os.path.basename(xfile)
    else:
        gates, scores = list(F.gates()), list(F.scores())
        THR = {n: q.get("threshold", cfg.GATE_THRESHOLD) for n, q in F.gates().items()}
        W = {n: q["weight"] for n, q in F.scores().items()}

        def wording(name):
            qid = name if variant == "base" else name + "_" + variant
            q = lab.get(qid) or lab.get(name) or {}
            return {"type": "noul", "instructions": q.get("instructions", ""),
                    "criteria": q.get("criteria", {"true": "", "false": ""})}
        Q = {n: wording(n) for n in gates + scores}
        source = "lab:" + variant

    negs = []
    neg_path = str(paths.DOCS / "negative-dataset.json")
    if os.path.exists(neg_path):
        try:
            negs = json.load(open(neg_path, encoding="utf-8"))
        except Exception:
            negs = []
    NEG = {_report_norm(n.get("subject", "")) for n in negs}

    def is_neg(subj):
        k = _report_norm(subj)
        return any(nk and (k[:45] in nk or nk[:45] in k) for nk in NEG)

    # ---- received-date lookup (sidecar rejects > negatives > checklist DB) ----
    DATEMAP = AL.build_date_map(
        str(paths.DOCS),
        str(paths.DATA),
        str(paths.DATA / "msme.sqlite3"),
    )
    for n in negs:
        _key = _report_norm(n.get("subject", ""))
        if _key and _key not in DATEMAP:
            _d = AL.parse_date(n.get("date", ""))
            if _d:
                DATEMAP[_key] = (_d, "negatives")

    def recv_date(subj, md=""):
        date, _source = AL.received_date(subj, md, DATEMAP)
        return date

    stats = {"calls": 0, "tokens": 0}

    def run_one(subject, body):
        try:
            resp = F._post({"state": {"subject": subject, "from": "", "date": "", "bodyText": body},
                            "model": cfg.JEV_MODEL, "questions": Q})
            ans = resp.get("answers", {})
            stats["calls"] += 1
            _u = resp.get("usage") or {}
            stats["tokens"] += _u.get("total") or (_u.get("input_tokens", 0) + _u.get("output_tokens", 0))
        except Exception:
            ans = {}
        good = {n: (round(float((ans.get(n) or {}).get("noul", 0) or 0) * 100) if ans.get(n) is not None else None)
                for n in gates + scores}
        fired = any(good.get(n) is not None and (100 - good[n]) / 100.0 >= THR[n] for n in gates)
        w = round(sum((good.get(n) or 0) * W[n] for n in scores) / sum(W.values()))
        oc = "REJECT" if fired else ("ACCEPT" if w >= filter_judge.accept_threshold() else "REJECT")
        return good, oc, w

    versions = _versions_payload(folder)
    arts = _list_articles(folder)
    t_start = time.time()
    REPORT_STATE.update({"running": True, "done": 0, "total": len(arts) + (len(negs) if include_neg else 0),
                         "source": source, "started": t_start, "rows": 0})
    rows = []
    email_norms = []
    for rel, d, md in arts:
        try:
            body = open(os.path.join(d, md), encoding="utf-8", errors="replace").read()
        except Exception:
            REPORT_STATE["done"] += 1
            continue
        subj = os.path.basename(rel)
        email_norms.append(_report_norm(subj))
        good, oc, w = run_one(subj, body)
        rows.append((subj, recv_date(subj, md), "REJECT" if is_neg(subj) else "ACCEPT", good, oc, w, rel))
        REPORT_STATE["done"] += 1
        REPORT_STATE["rows"] = len(rows)

    added = 0
    for n in (negs if include_neg else []):
        nk = _report_norm(n.get("subject", ""))
        if any(nk and (nk[:45] in ek or ek[:45] in nk) for ek in email_norms):
            REPORT_STATE["done"] += 1
            continue  # already present among the emails
        good, oc, w = run_one(n.get("subject", ""), n.get("bodyText", ""))
        rows.append((n.get("subject", ""), recv_date(n.get("subject", "")), "REJECT", good, oc, w, ""))
        added += 1
        REPORT_STATE["done"] += 1
        REPORT_STATE["rows"] = len(rows)

    # ---- date-range filter (default: since 2026-10-05; undated dropped when a range is set) ----
    if since or until:
        def _in_range(r):
            d = r[1]
            if not d:
                return False
            if since and d < since:
                return False
            if until and d > until:
                return False
            return True
        rows = [r for r in rows if _in_range(r)]

    # ---- sort by received date (newest first; undated last) ----
    rows.sort(key=lambda r: (r[1] != "", r[1]), reverse=True)

    # ---- write Excel ----
    def _lbl(n):
        lab = (src.get(n, {}).get("label") if src else "") or F.GATE_LABELS.get(n) or ""
        return lab or n
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    wb = Workbook(); ws = wb.active; ws.title = f"filter report {variant}"
    hdr = (["Article", "Received", "Original status"] +
           [f"g{i} {_lbl(g)}" for i, g in enumerate(gates, 1)] +
           [f"c{i} {_lbl(s)}" for i, s in enumerate(scores, 1)] + ["Outcome", "Weighted"])
    ws.append(hdr)
    for c in ws[1]:
        c.font = Font(bold=True, size=10); c.alignment = Alignment(wrap_text=True, vertical="top")
    for subj2, recv, orig, good, oc, w, _f in rows:
        ws.append([subj2, recv, orig] + [good[n] for n in gates + scores] + [oc, w])
    ws.freeze_panes = "D2"
    ws.column_dimensions["A"].width = 58; ws.column_dimensions["B"].width = 12; ws.column_dimensions["C"].width = 13
    for col in range(4, 4 + len(gates) + len(scores) + 2):
        ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = 9
    fill = PatternFill("solid", fgColor="FCE4E4")
    for row in range(2, ws.max_row + 1):
        if ws.cell(row=row, column=3).value == "REJECT":
            ws.cell(row=row, column=3).fill = fill
        ws.cell(row=row, column=3).font = Font(bold=True)
    # Outcome cell RED when it differs from the original email status (mismatch)
    outcome_col = len(hdr) - 1
    red_fill = PatternFill("solid", fgColor="FFC7CE")
    red_font = Font(bold=True, color="9C0006")
    for i, (subj2, recv, orig, good, oc, w, _f) in enumerate(rows, start=2):
        if orig != oc:
            cell = ws.cell(row=i, column=outcome_col)
            cell.fill = red_fill
            cell.font = red_font
    # light-red any gate/score cell with a LOW good% (low YES = bad) — where to focus
    low_fill = PatternFill("solid", fgColor="FDE2E1")
    for i, (subj2, recv, orig, good, oc, w, _f) in enumerate(rows, start=2):
        for ci, name in enumerate(gates + scores, start=4):
            v = good.get(name)
            if isinstance(v, (int, float)) and v < 50:
                ws.cell(row=i, column=ci).fill = low_fill
    # ---- control sheet (select questions Excel + RUN link) ----
    from openpyxl.worksheet.datavalidation import DataValidation
    ctrl = wb.create_sheet("control", 0)
    ctrl["A1"] = "Report Manager"; ctrl["A1"].font = Font(bold=True, size=14)
    ctrl["A2"] = "Select the questions Excel, then click RUN."; ctrl["A2"].font = Font(color="8B93A3")
    ctrl["A4"] = "Questions Excel:"; ctrl["A4"].font = Font(bold=True)
    d0 = str(paths.DOCS)
    avail = [f for f in sorted(os.listdir(d0)) if f.startswith("gates-def") and f.endswith(".xlsx")] if os.path.isdir(d0) else []
    if not avail:
        avail = ["gates-def-base.xlsx", "gates-def-1.xlsx", "gates-def-2.xlsx", "gates-def-3.xlsx"]
    ctrl["B4"] = (os.path.basename(xfile) if src else "gates-def-base.xlsx")
    dv = DataValidation(type="list", formula1='"' + ",".join(avail) + '"', allow_blank=False)
    ctrl.add_data_validation(dv); dv.add(ctrl["B4"])
    ctrl["A5"] = "Since (YYYY-MM-DD):"; ctrl["A5"].font = Font(bold=True)
    ctrl["B5"] = since or "2026-10-05"
    ctrl["A6"] = "Until (YYYY-MM-DD):"; ctrl["A6"].font = Font(bold=True)
    ctrl["B6"] = until or ""
    ctrl["A7"] = "Archive folder:"; ctrl["A7"].font = Font(bold=True)
    ctrl["B7"] = folder or "(all)"
    ctrl["A8"] = '=HYPERLINK("http://localhost:8900/report/run?file="&B4&"&since="&B5&"&until="&B6&"&folder="&B7,"▶ RUN filter & download report")'
    ctrl["A8"].font = Font(bold=True, size=12, color="2DD4BF")
    ctrl["A10"] = "Runs every archived article (within the date range and selected folder) with the selected Excel's gates+scores, then downloads the report."
    ctrl["A10"].font = Font(color="8B93A3")
    ctrl.column_dimensions["A"].width = 64
    ctrl.column_dimensions["B"].width = 30

    vws = wb.create_sheet("versions")
    vws.append(["Group", "Used", "Version", "Article", "Chars", "Used?"])
    for c in vws[1]:
        c.font = Font(bold=True, size=10)
    for group in versions["duplicates"]:
        for ver in group["versions"]:
            vws.append([group["base"], group["used"], ver["name"], ver["md"],
                        ver["chars"], "YES" if ver["used"] else ""])
    vws.column_dimensions["A"].width = 48
    vws.column_dimensions["B"].width = 48
    vws.column_dimensions["C"].width = 48
    vws.column_dimensions["D"].width = 48

    docs = str(paths.DOCS)
    tag = os.path.splitext(os.path.basename(xfile))[0] if src else variant
    import datetime as _dt2
    stamp = _dt2.datetime.now(_dt2.timezone(_dt2.timedelta(hours=8))).strftime("%Y%m%d-%H%M")
    folder_tag = folder.replace("received-2026-", "").replace("-and-", "-") if folder else "all"
    base = f"FILTER-REPORT-{tag}-{folder_tag}-{stamp}"
    fname = base + ".xlsx"
    wb.save(os.path.join(docs, fname))
    # CSV twin (for the Excel/VBA macro to consume): adds a Match column.
    import csv as _csv
    csvp = os.path.join(docs, base + ".csv")
    header = (["Article", "Received", "Original status", "Match"] +
              [f"g{i} {_lbl(g)}" for i, g in enumerate(gates, 1)] +
              [f"c{i} {_lbl(s)}" for i, s in enumerate(scores, 1)] + ["Outcome", "Weighted"])
    def _row(r):
        subj2, recv, orig, good, oc, wv, _f = r
        return [subj2, recv, orig, ("MATCH" if orig == oc else "MISMATCH")] + [good[n] for n in gates + scores] + [oc, wv]
    with open(csvp, "w", newline="", encoding="utf-8") as cf:
        cw = _csv.writer(cf); cw.writerow(header)
        for r in rows: cw.writerow(_row(r))
    tsvp = os.path.join(docs, base + ".tsv")
    with open(tsvp, "w", newline="", encoding="utf-8") as tf:
        tw = _csv.writer(tf, delimiter="\t"); tw.writerow(header)
        for r in rows: tw.writerow(_row(r))

    rej = sum(1 for r in rows if r[2] == "REJECT")
    import datetime as _dt
    rec = {"ts": _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=8))).isoformat(timespec="seconds"), "source": source, "variant": variant,
           "folder": folder, "rows": len(rows), "negatives_added": added, "original_rejects": rej,
           "archive": versions["root"], "version_groups": len(versions["groups"]),
           "duplicate_groups": versions["duplicate_groups"],
           "jev_calls": stats["calls"], "tokens": stats["tokens"],
           "seconds": round(time.time() - t_start, 1), "file": fname}
    _log_run(rec)
    REPORT_STATE.update({"running": False, "last": rec})
    return {"ok": True, "variant": variant, "source": source, "rows": len(rows),
            "folder": folder, "from_emails": len(rows) - added, "from_archive": len(rows) - added,
            "archive": versions["root"], "version_groups": len(versions["groups"]),
            "duplicates": versions["duplicate_groups"],
            "duplicate_folders": versions["folders_in_duplicates"],
            "negatives_added": added, "original_rejects": rej,
            "jev_calls": stats["calls"], "tokens": stats["tokens"],
            "seconds": round(time.time() - t_start, 1),
            "file": fname, "csv": base + ".csv", "tsv": base + ".tsv",
            "download": f"/report/download?file={fname}",
            "gates": gates, "scores": scores}


@app.post("/report/run")
def report_run(req: dict):
    req = req or {}
    return _do_report(req.get("variant") or "base", req.get("file") or "", req.get("negatives", True),
                      req.get("since", "2026-10-05"), req.get("until", ""), req.get("folder", ""))


@app.get("/report/run")
def report_run_get(file: str = "", variant: str = "base", negatives: int = 1,
                   since: str = "2026-10-05", until: str = "", folder: str = ""):
    """Run from a hyperlink (the Excel RUN button): run, then return the report file."""
    res = _do_report(variant, file, bool(negatives), since, until, folder)
    docs = str(paths.DOCS)
    return FileResponse(os.path.join(docs, res["file"]), filename=res["file"])


@app.get("/report/run.json")
def report_run_json(file: str = "", variant: str = "base", negatives: int = 1,
                    since: str = "2026-10-05", until: str = "", folder: str = ""):
    """Run and return the report as JSON (for macros / programmatic use)."""
    res = _do_report(variant, file, bool(negatives), since, until, folder)
    docs = str(paths.DOCS)
    csvp = os.path.join(docs, res["csv"])
    rows = []
    try:
        import csv as _csv
        with open(csvp, encoding="utf-8") as f:
            r = _csv.reader(f); hdr = next(r, [])
            for line in r:
                rows.append(dict(zip(hdr, line)))
    except Exception:
        pass
    return {"ok": True, "source": res.get("source"), "summary": res, "columns": list(rows[0].keys()) if rows else [], "rows": rows}


@app.get("/report/run.csv")
def report_run_csv(file: str = "", variant: str = "base", negatives: int = 1,
                   since: str = "2026-10-05", until: str = "", folder: str = ""):
    """Run and return the report as CSV (this is what the Excel macro fetches)."""
    res = _do_report(variant, file, bool(negatives), since, until, folder)
    docs = str(paths.DOCS)
    csvp = os.path.join(docs, res["csv"])
    return FileResponse(csvp, media_type="text/csv", filename=res["csv"])


@app.get("/report/run.tsv")
def report_run_tsv(file: str = "", variant: str = "base", negatives: int = 1,
                   since: str = "2026-10-05", until: str = "", folder: str = ""):
    """Run and return the report as TSV (tab-separated — parsed by the Excel macro)."""
    res = _do_report(variant, file, bool(negatives), since, until, folder)
    docs = str(paths.DOCS)
    tsvp = os.path.join(docs, res["tsv"])
    return FileResponse(tsvp, media_type="text/tab-separated-values", filename=res["tsv"])


@app.get("/report/download")
def report_download(file: str = ""):
    base = os.path.basename(file or "")
    docs = str(paths.DOCS)
    p = os.path.join(docs, base)
    if not base.startswith("FILTER-REPORT") or not os.path.exists(p):
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(p, filename=base)



@app.post("/testfilter/learn")
def testfilter_learn():
    """Learn the best <q>_jev_best_qu per question from docs/article-records.json.

    separation = mean YES%(rejects) − mean YES%(accepts); the best variant's
    instruction+criteria is written into <question>_jev_best_qu in docs/jev-variants.json.
    """
    docs = str(paths.DOCS)
    try:
        D = json.load(open(os.path.join(docs, "article-records.json"), encoding="utf-8"))
        V = json.load(open(os.path.join(docs, "jev-variants.json"), encoding="utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)}
    G, S_, COLS = D["gates"], D["scores"], D["cols"]
    ALLQ = G + S_
    recs = [r for r in D["records"] if r.get("hasArticle") and r.get("results")]
    REJ = [r for r in recs if r.get("outcome") == "REJECT"]
    ACC = [r for r in recs if r.get("outcome") == "ACCEPT"]

    def idFor(b, c):
        return b if c == "base" else b + "_" + c

    def mean(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs)) if xs else None

    def yes(r, vid):
        return r["results"].get(vid)

    Q = V["questions"]
    learned = []
    for b in ALLQ:
        seps = {}
        for c in COLS:
            vid = idFor(b, c)
            rv = mean([yes(r, vid) for r in REJ])
            av = mean([yes(r, vid) for r in ACC])
            if rv is not None and av is not None:
                seps[c] = rv - av
        if not seps:
            continue
        best = max(seps, key=lambda k: seps[k])
        src = Q.get(idFor(b, best))
        if not src:
            continue
        Q[idFor(b, "jev_best_qu")] = {"type": "noul", "instructions": src["instructions"], "criteria": src["criteria"]}
        conf = "strong" if seps[best] >= 30 else ("weak" if seps[best] >= 10 else "none")
        learned.append({"question": b, "from": idFor(b, best), "sep": seps[best], "confidence": conf})
    try:
        json.dump(V, open(os.path.join(docs, "jev-variants.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    except Exception as e:
        return {"ok": False, "error": f"write failed (docs read-only?): {e}"}
    return {"ok": True, "learned": learned, "rejects": len(REJ), "accepts": len(ACC)}


@app.post("/testfilter/promote")
def testfilter_promote(request: Request):
    """Write each <q>_jev_best_qu wording into the live filter (data/filter_settings.json)."""
    before, before_hash = filter_judge.config_version_snapshot()
    docs = str(paths.DOCS)
    try:
        V = json.load(open(os.path.join(docs, "jev-variants.json"), encoding="utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)}
    Q = V["questions"]
    patch = {"gates": {}, "scores": {}}
    for name in list(filter_judge.gates().keys()):
        jw = Q.get(name + "_jev_best_qu")
        if jw:
            patch["gates"][name] = {"instructions": jw["instructions"], "criteria": jw["criteria"]}
    for name in list(filter_judge.scores().keys()):
        jw = Q.get(name + "_jev_best_qu")
        if jw:
            patch["scores"][name] = {"instructions": jw["instructions"], "criteria": jw["criteria"]}
    try:
        filter_judge.update_settings(patch)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    vid, chash, diff = _record_filter_version("promote", request, before, before_hash)
    return {"ok": True, "promoted": {"gates": list(patch["gates"]), "scores": list(patch["scores"])},
            "version": vid, "config_hash": chash, "changed": diff}


@app.post("/testfilter/sync")
def testfilter_sync(request: Request):
    """Copy the current Jev Lab base wording into data/filter_settings.json (lab -> live)."""
    before, before_hash = filter_judge.config_version_snapshot()
    lab = (filter_judge._load_lab().get("questions") or {})
    patch = {"gates": {}, "scores": {}}
    for name in list(filter_judge.gates().keys()):
        q = lab.get(name)
        if q:
            patch["gates"][name] = {"instructions": q.get("instructions"), "criteria": q.get("criteria")}
    for name in list(filter_judge.scores().keys()):
        q = lab.get(name)
        if q:
            patch["scores"][name] = {"instructions": q.get("instructions"), "criteria": q.get("criteria")}
    try:
        filter_judge.update_settings(patch)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    vid, chash, diff = _record_filter_version("sync", request, before, before_hash)
    return {"ok": True, "synced": {"gates": len(patch["gates"]), "scores": len(patch["scores"])},
            "version": vid, "config_hash": chash, "changed": diff}


@app.post("/testfilter/rollback")
def testfilter_rollback(request: Request):
    """Rollback: restore built-in wording in the Lab file and clear filter_settings overrides."""
    before, before_hash = filter_judge.config_version_snapshot()
    try:
        lab_ok = filter_judge.reset_lab_base()
        filter_judge.reset_overrides()
    except Exception as e:
        return {"ok": False, "error": str(e)}
    vid, chash, diff = _record_filter_version("rollback", request, before, before_hash)
    return {"ok": True, "lab_restored_to_builtin": lab_ok,
            "version": vid, "config_hash": chash, "changed": diff}


@app.get("/workflow.json")
def workflow_json():
    """Return data for the Workflow page: config + battery + recent verdicts."""
    from msme import config as cfg

    return {
        "config": {
            "model": cfg.JEV_MODEL,
            "gateThreshold": cfg.GATE_THRESHOLD,
            "acceptThreshold": filter_judge.accept_threshold(),
        },
        "battery": filter_judge.battery(),
        "verdicts": _read_jsonl(_VERDICT_LOG, limit=30),
        "counts": {
            "accepted": sum(1 for v in _read_jsonl(_VERDICT_LOG, limit=1000) if v.get("outcome") == "ACCEPT"),
            "rejected": sum(1 for v in _read_jsonl(_VERDICT_LOG, limit=1000) if v.get("outcome") == "REJECT"),
            "editor_review": sum(1 for v in _read_jsonl(_VERDICT_LOG, limit=1000) if v.get("outcome") == "EDITOR REVIEW"),
        },
    }


def _archived_dir():
    """The folder the TEST-ARTICLE pages scan (independent of the receive save path)."""
    return os.environ.get("FILTER_ARCHIVE_DIR") or str(paths.LEGACY_ARCHIVE)


def _archive_root():
    """The REPORT input root: the live archive, not the legacy test store."""
    env = os.environ.get("FILTER_ARCHIVE_DIR")
    if env:
        return env
    return getattr(config, "REPORT_ARCHIVE_DIR", str(paths.ARCHIVE))


def _keepmap_path():
    return str(paths.DOCS / "archive-versions.json")


def _archived_roots():
    """Roots the ready-to-filter list may read.

    Receive archives to `emails/` or `all_emails/` depending on the deployment;
    the ready list must see both or half its rows cannot be opened. An explicit
    FILTER_ARCHIVE_DIR still wins (single root). The live archive is searched
    first so a moved/kept version wins over a legacy copy.
    """
    env = os.environ.get("FILTER_ARCHIVE_DIR")
    if env:
        return [env]
    live = _archive_root()
    roots = [live]
    legacy = str(paths.LEGACY_ARCHIVE)
    if legacy not in roots:
        roots.append(legacy)
    return roots


def _build_archive_index(root):
    """Map basename -> [paths] from ONE walk of the archive tree (or several roots).

    Receive-stage archives live at emails/<clean subject>/*.md (folder name may
    differ from the subject due to sanitization + duplicate suffixes), so we map
    the unique .md filename to its path once instead of re-walking per row.
    """
    roots = root if isinstance(root, (list, tuple)) else [root]
    index = {}
    for r in roots:
        if not r or not os.path.isdir(r):
            continue
        for dirpath, dirs, files in os.walk(r):
            dirs[:] = [d for d in dirs if not d.startswith(("_", "."))]
            for f in files:
                index.setdefault(f, []).append(os.path.join(dirpath, f))
    return index


def _find_article_file(folder_name, article_file):
    """Locate an archived article .md inside the archive tree (single lookup)."""
    if not article_file:
        return []
    found = _build_archive_index(_archived_roots()).get(os.path.basename(article_file), [])
    return found[:1]


@app.get("/archived")
def archived():
    """Return checklist rows that are READY TO FILTER, with their article files.

    This connects the receive stage to the filter: you pick an email that the
    receive pipeline already accepted (readyToFilter=true) and run it through Jev.

    Example item:
        {"subject": "...", "threadId": "...", "date": "...",
         "articleFile": "Lion-....md", "path": "emails/Lion-.../Lion-....md",
         "readyToFilter": true, "hasArticle": true}
    """
    rows = []
    try:
        import sqlite3

        from msme import config as cfg

        c = sqlite3.connect(cfg.SQLITE_PATH)
        c.row_factory = sqlite3.Row
        q = c.execute(
            "select subject, threadId, date, articleFile, readyToFilter, hasArticle "
            "from checklist where readyToFilter='true' order by id desc"
        )
        index = _build_archive_index(_archived_roots())
        for r in q.fetchall():
            path = ""
            if r["articleFile"]:
                found = index.get(os.path.basename(r["articleFile"]), [])
                path = found[0] if found else ""
            rows.append({
                "subject": r["subject"],
                "threadId": r["threadId"],
                "date": r["date"],
                "articleFile": r["articleFile"],
                "readyToFilter": r["readyToFilter"] == "true",
                "hasArticle": r["hasArticle"] == "true",
                "path": path,
            })
        c.close()
    except Exception as e:
        return {"articles": [], "error": str(e)}
    return {"articles": rows}


@app.get("/archived/read")
def archived_read(path: str = ""):
    """Read an archived article .md by its stored path (for the filter page)."""
    roots = [os.path.abspath(r) for r in _archived_roots()]
    p = os.path.abspath(path) if path else ""
    if not p or not any(p.startswith(r + os.sep) for r in roots):
        return {"error": "invalid path"}
    if not os.path.exists(p):
        return {"error": f"not found: {path}"}
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            return {"subject": os.path.basename(os.path.dirname(p)), "bodyText": f.read()}
    except Exception as e:
        return {"error": str(e)}
