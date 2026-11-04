# =============================================================================
# FILE HEADER
# file    : msme/receive/workflow_lab.py
# role    : Receive — interactive workflow lab (:8899)
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : expose the receive stages, their real code, sample inputs/outputs and a safe
#           sandbox runner (simulated AI by default, dry-run live mode) for the Workflow Lab page.
# pages   : workflow-lab.html
# calls   : pipeline, normalize, decide, extract, verify, checklist, archive, db, llm
# called  : dashboard.py (router mount); tests/test_workflow_lab.py
# amend   : the lab must never write the checklist, archive or DB (dry_run only); stage ids are the
#           contract with static/workflow-lab.html. Test: python3 -m unittest tests.test_workflow_lab
# =============================================================================
"""Workflow Lab backend — explain, inspect and run the receive stages safely.

Endpoints (mounted by dashboard.py):
    GET  /api/workflow/stages       stage metadata + code locations
    GET  /api/workflow/code         curated source excerpt for one stage
    GET  /api/workflow/files        every .py: purpose, importers, needed?
    GET  /api/workflow/samples      built-in samples + recent real traces
    POST /api/workflow/run          start an example / stage / live dry-run
    GET  /api/workflow/run-status   poll a run
    GET  /api/workflow/run/{id}     full run
    POST /api/workflow/upload       PDF/DOCX → text + media scan (no writes)

Safety: every run uses `pipeline` with `dry_run=True`; the archive, reply
and DB logs are skipped. Only one lab run executes at a time.
"""
import ast
import base64
import inspect
import os
import re
import struct
import threading
import time
import uuid
import zlib

from fastapi import APIRouter, File, HTTPException, UploadFile

from msme import creds, db, llm, paths
from msme.receive import (
    archive,
    checklist,
    decide,
    drive_fetch,
    extract,
    gmail,
    normalize,
    pipeline,
    reply,
    verify,
    web_fetch,
)

router = APIRouter()

_RUNS = {}
_RUN_BUSY = threading.Lock()
_RUN_TTL = 3600
_MAX_INPUT_CHARS = 60000
_UPLOAD_MAX = 20 * 1024 * 1024

# ---------------------------------------------------------------------------
# Stage knowledge base — the contract with static/workflow-lab.html
# ---------------------------------------------------------------------------
STAGES = [
    {
        "id": "receive", "n": 1, "title": "Receive", "type": "trigger", "icon": "📥",
        "summary": "Find the press-release emails that are waiting in the inbox.",
        "why": "Nothing enters the service unless Gmail returns a message. The query keeps promotions out.",
        "risk": "Gmail rate limits or an expired OAuth token stop the run before any work starts.",
        "inputs": ["Gmail query (default: in:inbox -category:promotions)"],
        "outputs": ["A list of unread message ids + subject/from/date"],
        "details": [
            "Query: in:inbox -category:promotions (editable on the Config page).",
            "Only unread messages; one email = one run.",
            "The dashboard list is cached; Refresh fetches fresh from Gmail.",
            "After a successful run the email is marked read, so it leaves the queue.",
            "A Gmail rate limit or an expired OAuth token stops the run before any work starts.",
        ],
        "code": [
            {"file": "gmail.py", "symbol": "list_unread", "label": "List unread messages"},
            {"file": "gmail.py", "symbol": "get_message", "label": "Fetch one full message"},
        ],
        "runnable": "none",
    },
    {
        "id": "normalize", "n": 2, "title": "Read & clean", "type": "code", "icon": "🧹",
        "summary": "Turn the raw Gmail message into a clean package: sender, subject, body, attachments and links.",
        "why": "The AI should read the release, not the editor's cover note, the forward headers or the disclaimer.",
        "risk": "A release that is only in an image or inside a linked PDF has almost no text here — later stages must fetch it.",
        "inputs": ["Raw Gmail message payload"],
        "outputs": ["{subject, from, date, bodyText, cleanBody, attachments, linksFound, bodyImageUrls}"],
        "details": [
            "Reads Subject, From, Date, text/plain and text/html.",
            "Attachment inventory: filename, MIME type, size and attachment id; bytes are downloaded later.",
            "Strips Fwd:/Re:, [PRESS RELEASE], the editor's cover note, disclaimers and forwarded headers.",
            "Collects every link from the visible text and the HTML hrefs.",
            "Follows up to 8 short/branded/tracker links to reveal the real Drive/OneDrive/Box destination.",
            "Keeps body-image URLs and the full body for the archive; only the AI prompt gets cleanBody.",
        ],
        "code": [
            {"file": "normalize.py", "symbol": "build_email_model", "label": "Build the email model"},
            {"file": "normalize.py", "symbol": "_clean_body", "label": "Strip covers/disclaimers"},
        ],
        "runnable": "stage",
    },
    {
        "id": "decide", "n": 3, "title": "Choose source", "type": "ai", "icon": "🎯",
        "summary": "The AI reads the email package and chooses which attachment is the real press release.",
        "why": "One email often carries English, Malay and Chinese versions plus captions. The extractor should start from the right one.",
        "risk": "Ambiguous filenames can make the AI choose the wrong document; the later collect step is the safety net.",
        "inputs": ["The normalized email model"],
        "outputs": ["{chosenAttachmentKey, chosenFileName, chosenDocType, isEnglish, linkToFetch, confidence, reason}"],
        "details": [
            "Input: subject, from, date, clean body, attachment names/types/sizes and links.",
            "Chooses the attachment key/name (English preferred) and the document type.",
            "Flags whether images are available and whether a media-kit link should be fetched.",
            "Link guard: a chosen link is trusted only if it actually appears in the email.",
            "Returns confidence + reason; it never reads file contents.",
            "When no file is suitable, it can choose the email body as the source.",
        ],
        "code": [
            {"file": "decide.py", "symbol": "build_decision_input", "label": "Build the AI input"},
            {"file": "decide.py", "symbol": "decide", "label": "Ask the AI"},
        ],
        "runnable": "stage",
    },
    {
        "id": "fetch", "n": 4, "title": "Fetch content", "type": "code", "icon": "📎",
        "summary": "Download every source and keep the text of each one as a candidate article.",
        "why": "The live pipeline can pull Gmail attachments, Google Drive media kits, OneDrive, Box, public web pages, body images and direct asset links.",
        "risk": "A view-only Drive file or a blocked page cannot be fetched; the run is marked needs_human instead of guessing.",
        "inputs": ["Attachments + every link found in the email"],
        "outputs": ["Candidate pool [{source, name, textLen, score}]", "Downloaded media and failures"],
        "details": [
            "Attachments: every file is downloaded (not only the chosen one); PDF/DOCX/DOC text is extracted.",
            "PDF text: first 30 pages, capped at 150k chars; DOCX images: 10 kept / 25 examined.",
            "Drive: folders and single files, shared drives, Google-native exports (Slides/Sheets→PDF, Drawings→PNG, Docs→text), English release pick.",
            "OneDrive public shares, Box press kits and public web article/speech pages.",
            "Email-body images and direct asset links are downloaded and classified.",
            "Caps: Drive file 60 MB, Box 25 MB; every fetched text becomes a candidate (deduped by content).",
            "A view-only/refused Drive file or a blocked page → needs_human, never a fake article.",
        ],
        "code": [
            {"file": "pipeline.py", "symbol": "_load_attachments", "label": "Download attachments"},
            {"file": "extract.py", "symbol": "extract_text_from_bytes", "label": "PDF/DOCX → text"},
            {"file": "drive_fetch.py", "symbol": "fetch_media_kit", "label": "Drive media kit"},
            {"file": "web_fetch.py", "symbol": "fetch_article", "label": "Public article/speech"},
        ],
        "runnable": "full-only",
    },
    {
        "id": "extract", "n": 5, "title": "Extract article", "type": "ai", "icon": "📄",
        "summary": "The AI compares the candidates and returns the verbatim article that should be published.",
        "why": "This is the text the editor will publish. It must be the release, not the cover note or the media kit index.",
        "risk": "If every candidate is empty, the run has no article and is not ready to filter.",
        "inputs": ["Email model + candidate texts"],
        "outputs": ["{bodyText, articleSource, chosenCandidate, evidence, confidence}"],
        "details": [
            "Input: raw email + clean body + ranked candidates C1..Cn (plus the legacy attachment text).",
            "Returns the verbatim bodyText, articleSource, chosenCandidate, evidence and confidence.",
            "chosenCandidate can be a C# label, email_body or none.",
            "Fallback: if the AI returns no text but a candidate exists, the candidate text is used.",
            "Text-only logo/image flags are trusted only when an article exists.",
            "mediaKitLink is kept only if it appears in the email links (link guard).",
            "No article → hasArticle=false and the row is not ready.",
        ],
        "code": [
            {"file": "pipeline.py", "symbol": "_rank_candidates", "label": "Rank the candidates"},
            {"file": "extract.py", "symbol": "build_extract_user", "label": "Build the AI input"},
            {"file": "extract.py", "symbol": "extract", "label": "Ask the AI"},
        ],
        "runnable": "stage",
    },
    {
        "id": "media", "n": 6, "title": "Check media", "type": "deterministic", "icon": "🖼️",
        "summary": "Find every image and decide where it lives — in the email or inside the article — then classify it as a logo or a photo.",
        "why": "The checklist has four separate media flags. An image inside the article is NOT hasPic; it is hasImageInArticle (photo) or hasLogoInArticle (logo). hasPic means a real photo file from the email, Drive/OneDrive/Box or a web page.",
        "risk": "A vector-only logo is detected only in a PDF header; a text-only wordmark is not detected. A photo inside the article never counts as hasPic.",
        "inputs": [
            "PDF/DOCX bytes (the article)",
            "attached image files",
            "images in the email HTML body",
            "Drive / OneDrive / Box media-kit images",
            "images from a fetched web page",
        ],
        "outputs": [
            "hasPic — a real photo file from the email / Drive / web",
            "hasLogo — a standalone logo file, body logo or asset-link logo",
            "hasImageInArticle — a photo embedded inside the article PDF/DOCX",
            "hasLogoInArticle — a logo/header embedded inside the article PDF/DOCX",
            "images[] — name, width, height, pages, kind (logo / photo / unknown)",
        ],
        "details": [
            "Sources: article PDF/DOCX, attached images, email body images, Drive/OneDrive/Box/web images.",
            "PDF: image XObjects; a vector logo drawn in the PDF /Header counts.",
            "DOCX: word/media/*; a header image is always a logo.",
            "Limits: 10 images kept per document, 25 examined; PDF text first 30 pages / 150k chars.",
            "Classification: ≤300 px, a wide/short strip or a repeated header/footer → logo; ≥500 px → photo.",
            "hasPic = a real photo file from the email/Drive/web; hasLogo = a standalone logo.",
            "hasImageInArticle = a photo inside the article; hasLogoInArticle = a logo inside the article.",
            "An image inside the article is never hasPic.",
        ],
        "code": [
            {"file": "extract.py", "symbol": "classify_doc_images", "label": "Classify the images"},
            {"file": "extract.py", "symbol": "_pdf_images", "label": "PDF image scan"},
            {"file": "extract.py", "symbol": "_docx_images", "label": "DOCX image scan"},
        ],
        "runnable": "upload",
    },
    {
        "id": "verify", "n": 7, "title": "Decide readiness", "type": "ai", "icon": "✅",
        "summary": "The AI compares the subject to the headline, scores the match and sets the checklist flags.",
        "why": "This is the verdict the editor sees: does the email contain an article, a photo, a logo, and is it ready to filter?",
        "risk": "The model can hallucinate a logo it never saw; deterministic evidence overrides the AI, and readyToFilter is recomputed in code.",
        "inputs": ["Article + media flags"],
        "outputs": ["{headline, subjectMatch, subjectScore, hasArticle, hasPic, hasLogo, hasLogoInArticle, hasImageInArticle, readyToFilter}"],
        "details": [
            "The prompt sees the headline, a 1,000-char article gist, image names, media flags and the extract evidence.",
            "Output: headline, subjectMatch, subjectScore 0–100, hasArticle, hasPic, hasLogo, hasLogoInArticle, hasImageInArticle, readyToFilter, reason.",
            "Subject match also accepts an exact headline/filename or ≥60% key-token coverage in the headline + first paragraph (D10).",
            "Deterministic guard: a logo/photo inside the article requires an article + real evidence.",
            "Deterministic document evidence overrides the AI's in-article flags (D8).",
            "readyToFilter = hasArticle AND (hasPic OR hasLogo OR hasLogoInArticle OR hasImageInArticle OR hasLogoFile) AND subjectScore > 60.",
            "A blocked source sets needs_human and hasArticle=false.",
        ],
        "code": [
            {"file": "verify.py", "symbol": "verify", "label": "Ask the AI"},
            {"file": "verify.py", "symbol": "_finalize", "label": "Deterministic consistency"},
        ],
        "runnable": "stage",
    },
    {
        "id": "filter", "n": 8, "title": "Filter (Jev)", "type": "ai", "icon": "⚖️",
        "summary": "Run Jev on a ready article and link ACCEPT/REJECT/EDITOR REVIEW to its checklist row.",
        "why": "The editorial verdict is part of the same run; the dashboard shows the gates and weighted scores without a second click.",
        "risk": "A Jev failure must not fail receive: the row is kept, filterStatus=error, and it can be retried.",
        "inputs": ["Extracted article + subject/from/date"],
        "outputs": ["filter_results row (outcome, weighted, gates, scores)", "Verdict JSONL audit entry"],
        "details": [
            "Runs only when readyToFilter=true and ENABLE_AUTO_FILTER is on.",
            "Calls filter.judge() in-process; no dependency on the old :8900 port.",
            "Writes filter_results linked by checklist_id; the 14-column checklist row is unchanged.",
            "Also appends to data/filter_verdicts.jsonl for the existing Verdicts/Logs/report pages.",
            "Dry-run skips the filter by default; the Workflow Lab can run it explicitly.",
        ],
        "code": [
            {"file": "pipeline.py", "symbol": "filter_judge.judge", "label": "Run Jev after readiness"},
            {"file": "filter.py", "symbol": "judge", "label": "Jev battery + routing"},
            {"file": "checklist.py", "symbol": "save_checklist", "label": "Link the verdict to the row"},
        ],
        "runnable": "none",
    },
    {
        "id": "save", "n": 9, "title": "Save", "type": "output", "icon": "💾",
        "summary": "Build the 14-column row and save the article + media to the local archive.",
        "why": "This row is what the dashboard and the filter stage read; the archive keeps the publishable text and images.",
        "risk": "A failed SQLite save loses the row; a Sheet write is no longer part of the run, and the reply is only sent when the row is not ready.",
        "inputs": ["Verdict + article text + media"],
        "outputs": ["14-column checklist row", "Archive folder (article.md, images/, originals/)", "Reply status"],
        "details": [
            "14 columns: subject, threadId, date, folderId, folderUrl, articleFile, hasArticle, hasPic, hasLogo, hasLogoInArticle, hasImageInArticle, subjectMatch, subjectScore, readyToFilter.",
            "Writes the 14-column row to SQLite, the checklist source of truth; the Google Sheet is optional and is not synced.",
            "Archive: all_emails/<received-date-bucket>/<subject>/ with article.md, images/ and originals/; a collision gets _N, never overwritten.",
            "Reply: only when readyToFilter=false; disabled in Docker (REPLY_ENABLED=false); the lab dry-run skips it.",
            "Run log: model, tokens and status (success / needs_human / error); pipeline_results powers the flow pages.",
            "needs_human: no article file, no archive, status needs_human.",
        ],
        "code": [
            {"file": "checklist.py", "symbol": "build_row", "label": "Order the 14 columns"},
            {"file": "archive.py", "symbol": "archive_email", "label": "Write the archive folder"},
            {"file": "reply.py", "symbol": "send_reply_for_row", "label": "Optional rejection reply"},
        ],
        "runnable": "stage",
    },
]

_STAGE_BY_ID = {s["id"]: s for s in STAGES}
_MODULES = {
    "gmail": gmail, "normalize": normalize, "decide": decide, "extract": extract,
    "verify": verify, "pipeline": pipeline, "checklist": checklist, "archive": archive,
    "reply": reply, "drive_fetch": drive_fetch, "web_fetch": web_fetch,
}

# ---------------------------------------------------------------------------
# .py purpose map — what is needed and why
# ---------------------------------------------------------------------------
_FILE_STATUS = {
    "run.py": ("core", True, "Entrypoint: one combined :8899 app + scheduler."),
    "main.py": ("core", True, "Legacy receive API; not started by run.py."),
    "dashboard.py": ("core", True, "Receive pages + same-origin /api on :8899."),
    "filter_service.py": ("core", True, "Filter sub-app behind combined :8899."),
    "pipeline.py": ("core", True, "Per-email orchestrator: normalize → decide → fetch → extract → verify → save."),
    "config.py": ("core", True, "Environment-overridable settings and paths."),
    "settings_store.py": ("core", True, "Runtime settings edited from the Config page."),
    "db.py": ("core", True, "SQLite: checklist cache, run log, pipeline traces."),
    "creds.py": ("core", True, "Google OAuth services (Gmail, Sheets, Drive)."),
    "gmail.py": ("core", True, "Read/download/send Gmail messages."),
    "normalize.py": ("core", True, "Turn a Gmail message into the clean email model."),
    "decide.py": ("core", True, "AI step 1: choose the press-release source."),
    "extract.py": ("core", True, "PDF/DOCX text + image extraction; AI step 2: extract the article."),
    "verify.py": ("core", True, "AI step 3: checklist verdict + deterministic consistency."),
    "checklist.py": ("core", True, "Write the 14-column row to SQLite."),
    "archive.py": ("core", True, "Save article.md, images and originals to the local archive."),
    "filter.py": ("core", True, "Jev judge core: 3 gates + 11 scores."),
    "prefilter.py": ("core", True, "Deterministic checks used by the filter judge."),
    "filter_llm.py": ("feature", True, "Optional DeepSeek assist for the filter; off by default."),
    "llm.py": ("core", True, "Provider switch for DeepSeek/Gemini."),
    "deepseek.py": ("core", True, "DeepSeek client + retry/error handling."),
    "reply.py": ("feature", True, "Rejection reply to the sender; disabled in Docker (REPLY_ENABLED=false)."),
    "scheduler.py": ("feature", True, "Auto-poll loop; only runs when ENABLE_AUTO=true."),
    "drive_fetch.py": ("core", True, "Google Drive media kits and file links."),
    "onedrive_fetch.py": ("core", True, "Public OneDrive share links."),
    "box_fetch.py": ("core", True, "Public Box press kits."),
    "web_fetch.py": ("core", True, "Public article/speech pages."),
    "archive_layout.py": ("core", True, "Report version grouping + received-date lookup."),
    "workflow_lab.py": ("feature", True, "Backend for the Workflow Lab page (this module)."),
    "combined.py": ("core", True, "One ASGI entrypoint: receive at root, filter paths on :8899."),
    "filter_log.py": ("core", True, "Shared JSONL verdict/error logger."),
    "repurpose_export.py": ("feature", True, "Export ACCEPT articles to the external engine inbox."),
    "repurpose_worker.py": ("ops", False, "Host worker: runs the external engine for new inbox folders."),
    "connection_test.py": ("support", True, "Config page 'test connection' checks."),
    "check_deepseek_key.py": ("one-off", False, "One-off DeepSeek key check; not part of the service."),
    "export_creds.py": ("one-off", False, "One-off export of n8n credentials into creds/."),
    "reauth_google.py": ("one-off", False, "Manual Google OAuth re-authorisation."),
    "oauth_catch.py": ("one-off", False, "Manual OAuth callback helper."),
    "learn_jev_way.py": ("analysis", False, "Filter-tuning experiment; not imported at runtime."),
    "run_all_emails.py": ("ops", False, "Bulk receive pass for a date range; operator tool."),
    "test_jev_weakness.py": ("analysis", False, "Filter weakness runner; not imported at runtime."),
    "build_register_indexes.py": ("tooling", True, "Regenerates decisions/todo INDEX files."),
    "reorganize_archive.py": ("one-off", False, "One-time archive sort; keeps a manifest and never deletes."),
    "test_collect_select.py": ("test", False, "Unit tests for the collect/select pipeline."),
    "test_report_versions.py": ("test", False, "Unit tests for report versions/dates."),
    "test_workflow_lab.py": ("test", False, "Unit tests for this lab."),
}

_NEEDED_LABEL = {
    "core": "NEEDED — runtime",
    "feature": "NEEDED — feature (may be off)",
    "support": "NEEDED — support",
    "tooling": "TOOLING",
    "ops": "TOOLING — operator",
    "analysis": "NOT RUNTIME — analysis",
    "one-off": "NOT RUNTIME — one-off",
    "test": "NOT RUNTIME — test",
}


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def _header(text):
    out = {}
    for line in text.splitlines()[:18]:
        m = re.match(r"#\s*(file|role|purpose|calls|called)\s*:\s*(.*)", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def _doc_first(text):
    """First docstring line, for the older scripts that have no FILE HEADER."""
    m = re.search(r'(?:"""(.*?)"""|\'\'\'(.*?)\'\'\')', text, re.S)
    if not m:
        return ""
    body = (m.group(1) or m.group(2) or "").strip()
    return body.splitlines()[0].strip() if body else ""


def _py_files():
    """Every service module plus the developer scripts, for the purpose map."""
    files = [str(paths.ROOT / "run.py")]
    for folder in ("msme", "tools", "tests"):
        root = paths.ROOT / folder
        if not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
            files += [os.path.join(dirpath, f) for f in sorted(filenames)
                      if f.endswith(".py")]
    return files


def _imported_modules(src):
    """Module basenames imported by `src` (handles `import x`, `from a.b import x`)."""
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        return set()
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name.split(".")[-1])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module.split(".")[-1])
            for alias in node.names:
                mods.add(alias.name)
    return mods


def file_map():
    """Every .py with role, purpose, importers and whether it is needed."""
    sources = {p: _read(p) for p in _py_files()}
    imports = {p: _imported_modules(src) for p, src in sources.items()}
    out = []
    for path, text in sources.items():
        name = os.path.basename(path)
        rel = os.path.relpath(path, paths.ROOT)
        mod = os.path.splitext(name)[0]
        used_by = []
        for other, mods in imports.items():
            if other == path:
                continue
            if mod in mods:
                used_by.append(os.path.basename(other))
        status, needed, reason = _FILE_STATUS.get(
            name, ("support", True, "Supporting module; review before removing.")
        )
        h = _header(text)
        fallback = _doc_first(text)
        out.append({
            "file": rel,
            "module": mod,
            "role": h.get("role") or fallback or reason,
            "purpose": h.get("purpose") or fallback or reason,
            "calls": h.get("calls", ""),
            "called": h.get("called", ""),
            "lines": len(text.splitlines()),
            "status": status,
            "needed": needed,
            "needed_label": _NEEDED_LABEL.get(status, status),
            "reason": reason,
            "imported_by": sorted(set(used_by)),
        })
    order = {"core": 0, "feature": 1, "support": 2, "tooling": 3, "ops": 3,
             "analysis": 4, "one-off": 4, "test": 5}
    out.sort(key=lambda x: (order.get(x["status"], 9), x["file"]))
    summary = {}
    for item in out:
        summary[item["status"]] = summary.get(item["status"], 0) + 1
    return {"files": out, "summary": summary, "total": len(out)}


# ---------------------------------------------------------------------------
# Code excerpts
# ---------------------------------------------------------------------------
@router.get("/api/workflow/stages")
def api_stages():
    return {
        "stages": [{k: v for k, v in s.items() if k != "code"} | {
            "code": [{"file": c["file"], "label": c["label"]} for c in s["code"]]
        } for s in STAGES],
        "file_map": file_map(),
    }


@router.get("/api/workflow/code")
def api_code(stage: str = ""):
    st = _STAGE_BY_ID.get(stage)
    if not st:
        raise HTTPException(404, "unknown stage")
    excerpts = []
    for c in st["code"]:
        mod_name = os.path.splitext(c["file"])[0]
        mod = _MODULES.get(mod_name)
        if mod is None:
            continue
        try:
            src, start = inspect.getsourcelines(getattr(mod, c["symbol"]))
        except Exception as e:
            excerpts.append({"file": c["file"], "symbol": c["symbol"], "label": c["label"],
                             "error": str(e), "code": ""})
            continue
        lines = len(src)
        code = "".join(src)
        if lines > 220:
            code = "".join(src[:220]) + f"\n# … {lines - 220} more lines in {c['file']}\n"
        excerpts.append({"file": c["file"], "symbol": c["symbol"], "label": c["label"],
                         "start": start, "lines": lines, "code": code})
    return {"stage": stage, "title": st["title"], "excerpts": excerpts}


@router.get("/api/workflow/files")
def api_files():
    return file_map()


# ---------------------------------------------------------------------------
# Samples
# ---------------------------------------------------------------------------
_RELEASE = (
    "FOR IMMEDIATE RELEASE\n\n"
    "Acme Robotics Opens New SME Innovation Hub in Penang\n\n"
    "PENANG, 20 October 2026 — Acme Robotics today opened a new innovation hub in Penang "
    "designed to help small and medium enterprises adopt affordable automation. The hub offers "
    "shared robotics labs, training and a test floor for local manufacturers.\n\n"
    "The company said the facility will support 60 SMEs in its first year and create 120 jobs. "
    "It is working with a local university on a skills programme for technicians and engineers.\n\n"
    "\"SMEs do not need to buy a robot to start. They can test a production line here and only "
    "invest when the numbers work,\" said Acme Robotics chief executive Mei Lim.\n\n"
    "The hub is supported by a state agency and opens to companies in Penang, Kedah and Perak.\n\n"
    "About Acme Robotics\n"
    "Acme Robotics builds affordable automation for small manufacturers in Southeast Asia.\n\n"
    "Media contact: press@acmerobotics.example"
)
_COVER = (
    "Hi Editor,\n\n"
    "Please find below our press release for publication. Let me know if you need a photo.\n\n"
)
_DISCLAIMER = (
    "\n\nThis email and any attachments are confidential and intended only for the recipient. "
    "If you received it in error, please delete it."
)


def _b64(text):
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii").rstrip("=")


def _message(subject, date, body, attachment=None):
    parts = [{"mimeType": "text/plain", "body": {"data": _b64(body)}}]
    if attachment:
        parts.append({
            "mimeType": attachment.get("mimeType", "application/octet-stream"),
            "filename": attachment["filename"],
            "body": {"attachmentId": attachment.get("attachmentId", "lab-file"),
                     "size": attachment.get("size", 0)},
        })
    return {
        "id": "lab-sample",
        "threadId": "lab-thread",
        "payload": {
            "mimeType": "multipart/mixed",
            "headers": [
                {"name": "Subject", "value": subject},
                {"name": "From", "value": "Editor MSME <editor@malaysiasme.com.my>"},
                {"name": "Date", "value": date},
            ],
            "parts": parts,
        },
    }


def _png(width=320, height=96):
    """A valid PNG so the media scan can read real dimensions."""
    sig = b"\x89PNG\r\n\x1a\n"

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def _sample_specs():
    return {
        "simple_release": {
            "label": "Simple release (text-only)",
            "description": "A body-only press release. Shows the full path and an honest not-ready "
                           "verdict because there is no photo or logo.",
            "message": _message(
                "Fwd: [PRESS RELEASE] Acme Robotics Opens New SME Innovation Hub in Penang",
                "Mon, 20 Oct 2026 09:15:00 +0800",
                _COVER + _RELEASE + _DISCLAIMER,
            ),
            "article": _RELEASE,
            "headline": "Acme Robotics Opens New SME Innovation Hub in Penang",
            "logo": False,
            "has_article": True,
        },
        "ready_release": {
            "label": "Release with a logo (ready)",
            "description": "The same release plus a small logo attachment. The deterministic scan "
                           "classifies it as a logo, so the row becomes readyToFilter=true.",
            "message": _message(
                "Fwd: [PRESS RELEASE] Acme Robotics Opens New SME Innovation Hub in Penang",
                "Mon, 20 Oct 2026 09:15:00 +0800",
                _COVER + _RELEASE + _DISCLAIMER,
                attachment={"filename": "Acme-Robotics-logo.png", "mimeType": "image/png",
                            "size": 1234, "attachmentId": "lab-logo"},
            ),
            "article": _RELEASE,
            "headline": "Acme Robotics Opens New SME Innovation Hub in Penang",
            "logo": True,
            "has_article": True,
        },
        "no_article": {
            "label": "No article (media only)",
            "description": "A short email with photos but no release. Shows the not-ready path and "
                           "the skipped reply.",
            "message": _message(
                "Fwd: Photos from our SME event",
                "Mon, 20 Oct 2026 10:00:00 +0800",
                "Hi Editor,\n\nPlease find attached photos from our event. Captions are in the file.\n\n"
                "Best,\nEvents team" + _DISCLAIMER,
            ),
            "article": "",
            "headline": "",
            "logo": False,
            "has_article": False,
        },
    }


def _sample(kind):
    specs = _sample_specs()
    spec = specs.get(kind) or specs["simple_release"]
    model = normalize.build_email_model(None, "lab-sample", message=spec["message"])
    return {"kind": kind, "spec": spec, "model": model}


def _public_model(model):
    out = {}
    for key in ("subject", "from", "fromName", "fromEmail", "date", "threadId", "messageId",
                "attachments", "linksFound", "bodyImageUrls"):
        out[key] = model.get(key)
    for key in ("bodyText", "cleanBody"):
        text = model.get(key, "") or ""
        out[key] = text[:20000] + ("\n… truncated" if len(text) > 20000 else "")
    out["cleanBodyPreview"] = (model.get("cleanBody", "") or "")[:700]
    out["bodyTextLen"] = len(model.get("bodyText", "") or "")
    out["cleanBodyLen"] = len(model.get("cleanBody", "") or "")
    return out


# ---------------------------------------------------------------------------
# Simulated AI + fake attachment service
# ---------------------------------------------------------------------------
class _FakeClient:
    provider = "simulated"
    model = "lab-sim"
    last_usage = {"prompt": 120, "completion": 60, "total": 180}

    def __init__(self, decision, extraction, verdict):
        self.decision = decision
        self.extraction = extraction
        self.verdict = verdict
        self.calls = []

    def chat_json(self, system, user, max_tokens=4000, temperature=0.2):
        llm._TOKEN_TALLY["prompt"] += 120
        llm._TOKEN_TALLY["completion"] += 60
        llm._TOKEN_TALLY["total"] += 180
        text = (system or "").lower()
        if "press source decider" in text:
            self.calls.append("decide")
            return dict(self.decision)
        if "submission extractor" in text:
            self.calls.append("extract")
            return dict(self.extraction)
        if "archive verifier" in text:
            self.calls.append("verify")
            return dict(self.verdict)
        return {}


def _fake_client(spec):
    decision = {
        "chosenAttachmentKey": "",
        "chosenFileName": "",
        "chosenDocType": "body" if spec["has_article"] else "none",
        "isEnglish": True,
        "imagesAvailable": bool(spec["logo"]),
        "imagesInAttachments": bool(spec["logo"]),
        "imagesViaLink": False,
        "linkToFetch": "",
        "linkIsPressKit": False,
        "confidence": 0.93,
        "reason": ("The email body contains the complete release." if spec["has_article"]
                   else "There is no press-release text in this email."),
    }
    extraction = {
        "bodyText": spec["article"],
        "articleSource": "email_body" if spec["article"] else "none",
        "chosenCandidate": "email_body" if spec["article"] else "none",
        "hasLogoInArticle": False,
        "hasImageInArticle": False,
        "needsHumanFetch": False,
        "evidence": ("The release text is in the cleaned email body." if spec["article"]
                     else "No article text found."),
        "confidence": 0.95,
        "mediaKitLink": "",
    }
    verdict = {
        "headline": spec["headline"],
        "subjectMatch": bool(spec["headline"]),
        "subjectScore": 88 if spec["has_article"] else 0,
        "hasArticle": spec["has_article"],
        "hasPic": False,
        "hasLogo": spec["logo"],
        "hasLogoInArticle": False,
        "hasImageInArticle": False,
        "readyToFilter": False,
        "reason": ("Subject and headline match; the release text is present." if spec["has_article"]
                   else "No article text was found in the email."),
    }
    return _FakeClient(decision, extraction, verdict)


class _FakeAttachmentReq:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return {"data": base64.urlsafe_b64encode(self.data).decode("ascii")}


class _FakeAttachments:
    def __init__(self, data):
        self.data = data

    def get(self, **kwargs):
        return _FakeAttachmentReq(self.data)


class _FakeMessages:
    def __init__(self, data):
        self.data = data

    def attachments(self):
        return _FakeAttachments(self.data)


class _FakeUsers:
    def __init__(self, data):
        self.data = data

    def messages(self):
        return _FakeMessages(self.data)


class _FakeService:
    """Minimal Gmail service: returns a PNG for any attachment id."""

    def __init__(self, data):
        self.data = data

    def users(self):
        return _FakeUsers(self.data)


# ---------------------------------------------------------------------------
# Run registry
# ---------------------------------------------------------------------------
class _Trace:
    def __init__(self, run):
        self.run = run
        self.last = time.time()

    def __call__(self, stage, status, detail):
        now = time.time()
        self.run["stages"].append({
            "stage": stage,
            "status": status,
            "detail": detail,
            "ms": round((now - self.last) * 1000, 1),
            "ts": now,
        })
        self.last = now
        self.run["updated"] = now


def _new_run(mode, meta):
    run_id = "lab-" + uuid.uuid4().hex[:10]
    now = time.time()
    _RUNS[run_id] = {
        "id": run_id, "mode": mode, "status": "running", "started": now,
        "updated": now, "stages": [], "result": None, "error": "", "meta": meta or {},
    }
    return run_id


def _cleanup():
    cutoff = time.time() - _RUN_TTL
    for rid in [r for r, v in _RUNS.items() if v.get("updated", 0) < cutoff]:
        _RUNS.pop(rid, None)


def _start(run_id, fn):
    run = _RUNS[run_id]

    def worker():
        try:
            run["result"] = fn(_Trace(run))
            run["status"] = "done"
        except Exception as e:
            run["error"] = str(e)
            run["status"] = "error"
            run["updated"] = time.time()
            run["stages"].append({"stage": "error", "status": "error",
                                  "detail": {"error": str(e)}, "ms": 0, "ts": time.time()})
        finally:
            run["updated"] = time.time()
            try:
                _RUN_BUSY.release()
            except RuntimeError:
                pass
            _RUNS[run_id] = run

    threading.Thread(target=worker, daemon=True).start()


def _run_example(kind, trace):
    sample = _sample(kind)
    model = sample["model"]
    trace("normalize", "done", pipeline._model_summary(model))
    client = _fake_client(sample["spec"])
    service = _FakeService(_png()) if sample["spec"]["logo"] else None
    llm.reset_token_tally()
    row = pipeline.process_model(model, service=service, dry_run=True, trace=trace, client=client)
    return {
        "sample": kind,
        "label": sample["spec"]["label"],
        "row": row,
        "model": _public_model(model),
        "simulated": True,
    }


def _model_from_input(data):
    data = data or {}
    if isinstance(data.get("model"), dict):
        model = dict(data["model"])
    elif isinstance(data.get("message"), dict):
        model = normalize.build_email_model(None, "lab-stage", message=data["message"])
    else:
        model = _sample("simple_release")["model"]
    for key in ("bodyText", "cleanBody"):
        if isinstance(model.get(key), str) and len(model[key]) > _MAX_INPUT_CHARS:
            model[key] = model[key][:_MAX_INPUT_CHARS]
    return model


def _run_stage(stage, data, ai_mode, trace):
    data = data or {}
    client = None
    if ai_mode != "live":
        client = _fake_client(_sample("simple_release")["spec"])
    llm.reset_token_tally()
    trace("input", "done", {"stage": stage, "input": data})

    if stage == "normalize":
        msg = data.get("message") or _sample("simple_release")["spec"]["message"]
        model = normalize.build_email_model(None, "lab-stage", message=msg)
        output = _public_model(model)
    elif stage == "decide":
        model = _model_from_input(data)
        output = decide.decide(model, client=client)
    elif stage == "extract":
        model = _model_from_input(data)
        candidates = data.get("candidates") or []
        output = extract.extract(model, data.get("attachment_text", ""),
                                 candidates=candidates, client=client)
    elif stage == "verify":
        sample = _sample("simple_release")["spec"]
        article = data.get("article") or {
            "subject": sample["message"]["payload"]["headers"][0]["value"],
            "from": "Editor MSME <editor@malaysiasme.com.my>",
            "date": "Mon, 20 Oct 2026 09:15:00 +0800",
            "bodyText": sample["article"],
        }
        flags = data.get("flags") or {
            "hasPic": False, "hasLogo": False, "docLogo": False, "docPhoto": False,
            "visionLogo": False, "aiLogo": False, "aiImage": False, "hasLogoFile": False,
        }
        output = verify.verify(article, data.get("image_names") or [], flags,
                               data.get("evidence", ""), client=client)
    elif stage == "save":
        output = {"columns": checklist.COLUMNS,
                  "values": checklist.build_row(data.get("row") or {})}
    else:
        raise HTTPException(400, f"stage '{stage}' is not runnable on its own")

    trace("output", "done", {"stage": stage, "output": output})
    return {"stage": stage, "ai": ai_mode, "output": output}


def _run_live(email_id, trace):
    service = creds.gmail()
    trace("receive", "done", {"email_id": email_id, "source": "gmail"})
    row = pipeline.process_email(service, email_id, dry_run=True, trace=trace)
    return {"email_id": email_id, "row": row, "dry_run": True}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@router.get("/api/workflow/samples")
def api_samples():
    specs = _sample_specs()
    try:
        recent = db.list_pipeline_results(limit=10)
    except Exception:
        recent = []
    return {
        "samples": [{"id": k, "label": v["label"], "description": v["description"]}
                    for k, v in specs.items()],
        "recent_runs": recent,
    }


@router.post("/api/workflow/run")
def api_run(req: dict):
    _cleanup()
    req = req or {}
    mode = str(req.get("mode") or "example")
    if mode not in ("example", "stage", "live"):
        raise HTTPException(400, "mode must be example, stage or live")
    if not _RUN_BUSY.acquire(blocking=False):
        raise HTTPException(409, "A workflow-lab run is already in progress")

    if mode == "example":
        kind = str(req.get("sample") or "simple_release")
        if kind not in _sample_specs():
            _RUN_BUSY.release()
            raise HTTPException(400, "unknown sample")
        run_id = _new_run(mode, {"sample": kind})
        _start(run_id, lambda trace: _run_example(kind, trace))
    elif mode == "stage":
        stage = str(req.get("stage") or "")
        if stage not in _STAGE_BY_ID or _STAGE_BY_ID[stage].get("runnable") not in ("stage",):
            _RUN_BUSY.release()
            raise HTTPException(400, "stage is not runnable on its own")
        ai_mode = str(req.get("ai") or "sim")
        run_id = _new_run(mode, {"stage": stage, "ai": ai_mode})
        _start(run_id, lambda trace: _run_stage(stage, req.get("input") or {}, ai_mode, trace))
    else:
        email_id = str(req.get("email_id") or "").strip()
        if not email_id or not re.fullmatch(r"[A-Za-z0-9_-]{6,64}", email_id):
            _RUN_BUSY.release()
            raise HTTPException(400, "invalid email_id")
        run_id = _new_run(mode, {"email_id": email_id})
        _start(run_id, lambda trace: _run_live(email_id, trace))
    return {"run_id": run_id, "status": "running", "mode": mode}


@router.get("/api/workflow/run-status")
def api_run_status(run_id: str = ""):
    _cleanup()
    run = _RUNS.get(run_id)
    if not run:
        raise HTTPException(404, "unknown run")
    out = dict(run)
    out["elapsed"] = round(time.time() - run.get("started", time.time()), 1)
    return out


@router.get("/api/workflow/run/{run_id}")
def api_run_detail(run_id: str):
    run = _RUNS.get(run_id)
    if not run:
        raise HTTPException(404, "unknown run")
    return run


@router.post("/api/workflow/upload")
async def api_upload(file: UploadFile = File(...)):
    name = (file.filename or "").lower()
    if not name.endswith((".pdf", ".docx", ".doc")):
        raise HTTPException(400, "only PDF/DOCX/DOC uploads are supported")
    data = await file.read()
    if len(data) > _UPLOAD_MAX:
        raise HTTPException(413, "file is larger than 20 MB")
    if not data:
        raise HTTPException(400, "empty file")
    try:
        info = extract.classify_doc_images(data, name)
        text = extract.extract_text_from_bytes(data, name)
    except Exception as e:
        raise HTTPException(500, f"could not read the document: {e}")
    return {
        "filename": file.filename,
        "size": len(data),
        "textLen": len(text),
        "textPreview": text[:1500],
        "truncated": info.get("truncated", False),
        "hasImage": info.get("has_image", False),
        "hasLogo": info.get("has_logo", False),
        "hasPhoto": info.get("has_photo", False),
        "images": info.get("images", []),
    }
