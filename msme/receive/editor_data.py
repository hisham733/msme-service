# =============================================================================
# FILE HEADER
# file    : msme/receive/editor_data.py
# role    : End-user editor view — received emails, stage, rejection reason
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : combine checklist + runs + pipeline stages + filter + repurpose into
#           editor-facing items, plain-language labels (no article/no media, fail 3R/not relevant,
#           publish not started/issue) and a per-email stage timeline.
# pages   : backs /api/editor/articles and /api/editor/article
# calls   : db, config, json/os/pathlib
# called  : dashboard.py
# amend   : do not expose secrets; stage order is receive → readiness → filter → draft → publish.
#           Test: GET /api/editor/articles after a run.
# =============================================================================
"""Build the MSME editor item list and stage detail from existing stores."""
import json
import os
from pathlib import Path

from msme import config, db, settings_store
from msme.receive import email_link

STAGE_LABEL = {
    "processing": "Processing",
    "receive": "Receive",
    "readiness": "Ready check",
    "filter": "Editorial check",
    "repurpose": "Draft",
    "ready": "Ready to publish",
    "published": "Published locally",
    "received": "Received",
}
STAGE_ORDER = ("receive", "readiness", "filter", "repurpose", "publish")


def _latest(rows, key):
    out = {}
    for r in rows:
        k = key(r)
        if k and k not in out:
            out[k] = r
    return out


def _repurpose_meta():
    """checklist_id -> run.json status, failing rules, page/image URLs."""
    try:
        records = db.list_repurpose_exports()
    except Exception:
        records = []
    if not records:
        data_dir = os.path.dirname(config.SQLITE_PATH) or "."
        manifest = os.path.join(data_dir, "repurpose_export.json")
        try:
            records = (json.load(open(manifest, encoding="utf-8")) or {}).get("exported") or []
        except Exception:
            records = []
    articles = {}
    try:
        raw = Path(config.REPURPOSE_SITE, "data", "articles.js").read_text(encoding="utf-8")
        payload = raw.split("=", 1)[1].strip().rstrip(";") if "=" in raw else raw
        for a in json.loads(payload):
            articles[a.get("title", "")] = a
    except Exception:
        pass
    out = {}
    for rec in records:
        dest = rec.get("dest") or ""
        folder = os.path.basename(dest)
        if not folder or not rec.get("checklist_id"):
            continue
        folder_path = Path(config.REPURPOSE_INBOX, folder)
        run_path = folder_path / "run.json"
        run = {}
        try:
            run = json.loads(run_path.read_text(encoding="utf-8")) or {}
        except Exception:
            pass
        draft_title = ""
        try:
            lines = (folder_path / "draft.md").read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines):
                if line.strip().lower() == "## title":
                    for nxt in lines[i + 1:]:
                        if nxt.strip():
                            draft_title = nxt.strip()
                            break
                    break
        except Exception:
            pass
        art = articles.get(draft_title) or {}
        fails = [r for r in (run.get("validator") or {}).get("results") or []
                 if not r.get("ok") and r.get("level") == "fail"]
        out[str(rec.get("checklist_id"))] = {
            "status": run.get("status") or "queued",
            "folder": folder,
            "draft_title": draft_title,
            "fails": fails,
            "page_url": ("/repurpose-site/" + art["url"]) if art.get("url") else "",
            "image_url": ("/repurpose-site/" + art["image"]) if art.get("image") else "",
            "updated": run.get("updated") or "",
        }
    return out


THREE_R = {"ROYAL_RESPECT", "RELIGIOUS_RESPECT", "RACIAL_RESPECT"}


def _accept_threshold():
    try:
        return float(settings_store.get("ACCEPT_THRESHOLD") or config.ACCEPT_THRESHOLD)
    except (TypeError, ValueError):
        return float(config.ACCEPT_THRESHOLD)


def _reason_for_readiness(row, pr):
    if row.get("emailType") == "library_update":
        return "Library update — logo/building assets stored in the gallery."
    try:
        reason = ((pr or {}).get("stages") or {}).get("verify", {}).get("detail", {}).get("reason", "")
    except Exception:
        reason = ""
    if reason:
        return reason
    if row.get("hasArticle") != "true":
        return "No article."
    if row.get("hasPic") != "true" and row.get("hasLogo") != "true" and row.get("hasImageInArticle") != "true":
        return "No media."
    try:
        if float(row.get("subjectScore") or 0) <= 60:
            return f"Subject match {row.get('subjectScore')}% (needs >60%)."
    except Exception:
        pass
    return "Article did not meet the ready-to-filter rule."


def _filter_state(row, verdict, accept=None):
    """Return (simple label, plain-language reason) for the editor."""
    verdict = verdict or {}
    outcome = (row.get("filterOutcome") or verdict.get("outcome") or "").upper()
    gate = (row.get("filterGate") or verdict.get("gate") or "").strip()
    gate_upper = gate.upper()
    weighted = row.get("filterWeighted")
    if weighted is None:
        weighted = verdict.get("weighted")
    accept = _accept_threshold() if accept is None else accept
    if row.get("filterStatus") == "error" or outcome == "ERROR":
        return "check failed", row.get("filterError") or verdict.get("error") or "Editorial check failed."
    if outcome == "ACCEPT":
        return "accepted", "Passed the editorial check."
    if gate_upper in THREE_R:
        labels = verdict.get("gate_labels") or {}
        label = labels.get(gate.lower()) or gate.replace("_", " ").title()
        return "fail 3R", f"Failed the 3R check: {label}."
    try:
        below = weighted is not None and float(weighted) < accept
    except (TypeError, ValueError):
        below = False
    if below:
        return "not relevant", f"Score {weighted}% is below the {accept:g}% pass mark."
    if outcome == "EDITOR REVIEW":
        return "needs review", "Borderline result; a human decision is needed."
    if outcome == "REJECT":
        return "not accepted", "Did not pass the editorial check."
    return "not filtered", ""


def _reason_for_filter(row, verdict):
    return _filter_state(row, verdict)[1]


def _reason_for_repurpose(meta):
    fails = (meta or {}).get("fails") or []
    if fails:
        return "; ".join(f"{r.get('code')}: {str(r.get('detail') or '')[:100]}" for r in fails[:4])
    return "Draft validation did not pass."


def _item_for(row, run, pr, rep, version_count, accept=None):
    stage = "received"
    reason = ""
    filter_label, filter_reason = _filter_state(row, row.get("filterVerdict"), accept)
    run_status = (run or {}).get("status") or ""
    pr_row = (pr or {}).get("row") or {}
    if run_status in ("running", "drafting"):
        stage, reason = "processing", "Receive/filter is running."
    if run_status == "error" or run_status == "ai_error":
        stage, reason = "receive", (run or {}).get("error") or "Receive failed."
    elif run_status == "needs_human" or pr_row.get("_status") == "needs_human":
        stage = "receive"
        reason = pr_row.get("_needs_human_reason") or (run or {}).get("error") or "Source could not be fetched."
    elif row.get("readyToFilter") != "true":
        stage, reason = "readiness", _reason_for_readiness(row, pr)
    else:
        outcome = (row.get("filterOutcome") or "").upper()
        if row.get("filterStatus") == "error" or outcome == "ERROR":
            stage, reason = "filter", filter_reason
        elif outcome in ("REJECT", "EDITOR REVIEW"):
            stage, reason = "filter", filter_reason
        elif outcome != "ACCEPT":
            stage, reason = "received", "Ready for the editorial check."
        else:
            rs = (rep or {}).get("status") or ""
            if rs in ("HOLD", "validate-failed", "error"):
                stage, reason = "repurpose", _reason_for_repurpose(rep)
            elif rs in ("queued", "pending", "drafting", "drafted", "drafting"):
                stage, reason = "repurpose", "Draft in progress."
            elif rs in ("validated", "rendered"):
                stage = "published" if rs == "rendered" else "ready"
                reason = "Validated local draft." if stage == "ready" else "Local page built."
            else:
                stage, reason = "ready", "Accepted and ready for drafting."
    edited = max([str(row.get("created_at") or ""), str(row.get("filteredAt") or ""),
                  str((run or {}).get("created_at") or ""), str((pr or {}).get("created_at") or ""),
                  str((rep or {}).get("updated") or "")])
    return email_link.enrich_row({
        "id": row.get("id"), "threadId": row.get("threadId", ""),
        "messageId": row.get("messageId", ""),
        "rfc822MessageId": row.get("rfc822MessageId", ""),
        "editedAt": edited,
        "subject": row.get("subject", ""), "date": row.get("date", ""),
        "stage": stage, "stageLabel": STAGE_LABEL.get(stage, stage),
        "reason": reason, "versions": version_count,
        "readyToFilter": row.get("readyToFilter", ""),
        "hasArticle": row.get("hasArticle", ""), "hasPic": row.get("hasPic", ""),
        "hasLogo": row.get("hasLogo", ""), "hasLogoInArticle": row.get("hasLogoInArticle", ""),
        "hasImageInArticle": row.get("hasImageInArticle", ""),
        "subjectMatch": row.get("subjectMatch", ""), "subjectScore": row.get("subjectScore", ""),
        "filterStatus": row.get("filterStatus", ""), "filterOutcome": row.get("filterOutcome", ""),
        "filterWeighted": row.get("filterWeighted"), "filterGate": row.get("filterGate"),
        "filterLabel": filter_label,
        "filterError": row.get("filterError", ""),
        "filterVerdict": row.get("filterVerdict") or {},
        "repurposeStatus": (rep or {}).get("status", ""),
        "repurposeFolder": (rep or {}).get("folder", ""),
        "pageUrl": (rep or {}).get("page_url", ""),
        "imageUrl": (rep or {}).get("image_url", ""),
        "repurposeFails": (rep or {}).get("fails") or [],
        "runStatus": run_status, "runError": (run or {}).get("error", ""),
        "runModel": (run or {}).get("model", ""),
        "emailType": row.get("emailType", ""),
    })


def build_items():
    rows = db.list_checklist()
    runs = _latest(db.list_runs(limit=1000), lambda r: r.get("email_id"))
    prs = _latest(db.list_pipeline_results(limit=1000), lambda r: r.get("email_id"))
    reps = _repurpose_meta()
    accept = _accept_threshold()
    counts = {}
    for r in rows:
        k = r.get("threadId") or r.get("subject") or str(r.get("id"))
        counts[k] = counts.get(k, 0) + 1
    seen, out = set(), []
    for r in rows:
        key = r.get("threadId") or r.get("subject") or str(r.get("id"))
        if key in seen:
            continue
        seen.add(key)
        run = runs.get(key) or {}
        pr = prs.get(key) or {}
        out.append(_item_for(r, run, pr, reps.get(str(r.get("id"))), counts.get(key, 1), accept))
    # Runs that failed before a checklist row existed still count as received email.
    for email_id, run in runs.items():
        if email_id in seen or not email_id:
            continue
        if (run.get("status") or "") not in ("error", "ai_error", "needs_human"):
            continue
        out.append({
            "id": None, "threadId": email_id, "subject": run.get("subject") or "(email)",
            "date": (run.get("created_at") or "")[:10], "stage": "receive",
            "stageLabel": STAGE_LABEL["receive"], "reason": run.get("error") or "Receive failed.",
            "versions": 1, "readyToFilter": "", "hasArticle": "", "hasPic": "",
            "hasLogo": "", "hasLogoInArticle": "", "hasImageInArticle": "",
            "subjectMatch": "", "subjectScore": "", "filterStatus": "",
            "filterOutcome": "", "filterWeighted": None, "filterGate": None,
            "filterLabel": "", "filterError": "", "filterVerdict": {}, "repurposeStatus": "",
            "repurposeFolder": "", "pageUrl": "", "imageUrl": "", "repurposeFails": [],
            "runStatus": run.get("status"), "runError": run.get("error") or "",
            "runModel": run.get("model") or "", "runOnly": True,
            "emailType": "",
            "editedAt": run.get("created_at") or "",
        })
    out.sort(key=lambda x: (x.get("editedAt") or "", x.get("id") or 0), reverse=True)
    return out


def _bucket(item):
    if item.get("stage") in ("receive", "readiness", "filter"):
        return "attention"
    if item.get("stage") == "repurpose":
        if str(item.get("repurposeStatus") or "").lower() in ("hold", "validate-failed", "error"):
            return "attention"
        return "draft"
    if item.get("stage") == "ready":
        return "ready"
    if item.get("stage") == "published":
        return "published"
    return "all"


def query_items(page=1, page_size=20, tab="all", q=""):
    """Sorted by last edit (desc), then page-sliced for the editor."""
    items = build_items()
    counts = {"all": len(items), "attention": 0, "draft": 0, "ready": 0, "published": 0}
    for i in items:
        b = _bucket(i)
        if b in counts and b != "all":
            counts[b] += 1
    q = (q or "").strip().lower()
    if q:
        items = [i for i in items if q in f"{i.get('subject','')} {i.get('date','')} {i.get('reason','')}".lower()]
    if tab in ("attention", "draft", "ready", "published"):
        items = [i for i in items if _bucket(i) == tab]
    try:
        page_size = max(1, min(100, int(page_size)))
        page = max(1, int(page))
    except Exception:
        page_size, page = 20, 1
    total = len(items)
    pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, pages)
    start = (page - 1) * page_size
    return {"items": items[start:start + page_size], "page": page, "page_size": page_size,
            "pages": pages, "total": total, "counts": counts,
            "sort": "editedAt desc"}


def get_article(thread_id):
    rows = [r for r in db.list_checklist() if r.get("threadId") == thread_id]
    if not rows:
        return None
    rows.sort(key=lambda r: int(r.get("id") or 0), reverse=True)
    latest = rows[0]
    runs = _latest(db.list_runs(limit=1000), lambda r: r.get("email_id"))
    prs = _latest(db.list_pipeline_results(limit=1000), lambda r: r.get("email_id"))
    rep = _repurpose_meta().get(str(latest.get("id")))
    item = _item_for(latest, runs.get(thread_id) or {}, prs.get(thread_id) or {}, rep, len(rows))
    item["history"] = [
        {"id": r.get("id"), "date": r.get("date"), "readyToFilter": r.get("readyToFilter"),
         "filterOutcome": r.get("filterOutcome"), "filterWeighted": r.get("filterWeighted"),
         "repurposeStatus": (rep or {}).get("status", "") if r is latest else ""}
        for r in rows
    ]
    item["pipeline"] = prs.get(thread_id) or {}
    item["filterVersions"] = db.list_filter_history(checklist_id=latest.get("id"), limit=50)
    return item
