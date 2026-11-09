# =============================================================================
# FILE HEADER
# file    : msme/receive/pipeline.py
# role    : Receive — per-email orchestrator
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : one email -> normalize -> decide -> collect every source (attachments, Drive, OneDrive, Box,
#           web, body images) -> select the article from the candidate pool -> N-2 library-update check
#           -> verify -> 14-column checklist row -> local archive; records each stage for the Workflow
#           page. Media is classified by dimensions, never by file size (D24).
# pages   : n/a (the row feeds checklist.html)
# calls   : config, creds, db, decide, drive_fetch, onedrive_fetch, box_fetch, extract, gmail, normalize,
#           verify, library_update, gallery; archive (lazy)
# called  : main.py / dashboard.py `_process_one`, scheduler.py
# amend   : stage order and row keys are the contract read by the checklist, reports and archive lookups.
#           A new stage must also call db.save_pipeline_result. Test: run one email end-to-end.
# =============================================================================
"""Pipeline: process one email end-to-end -> checklist row.

Flow:
    Decide -> load attachments / drive media kit -> extract -> logo scan
        -> library-update check (N-2, skips verify/filter/reply on a hit)
        -> verify -> build 14-col checklist row -> archive to PC.

Example of what this returns (the checklist row):
    {
      "subject": "Fwd: [PRESS RELEASE] MALAYSIA'S EXPORTS ...",
      "threadId": "1a0c6a780d5e67d8",
      "date": "Tue, 22 Se",
      "folderId": "",                      # local archive, not Drive
      "folderUrl": "",
      "articleFile": "MALAYSIAS-EXPORTS-....md",
      "hasArticle": "true", "hasPic": "true", "hasLogo": "true",
      "hasLogoInArticle": "true", "hasImageInArticle": "true",
      "subjectMatch": "true", "subjectScore": "85", "readyToFilter": "true",
    }
"""
import hashlib
import os
import re
import urllib.request

from msme import config, creds, db, settings_store
from msme.filtering import filter as filter_judge
from msme.filtering import filter_log
from msme.receive import (
    box_fetch,
    decide,
    drive_fetch,
    extract,
    gallery,
    gmail,
    normalize,
    onedrive_fetch,
    verify,
    web_fetch,
)


def _ai_ok(tokens, verdict):
    """True only if the AI produced a real verdict (tokens used + a hasArticle value).

    An empty verdict with 0 tokens means the provider failed — NOT "no article".

    Example:
        _ai_ok({"total": 0}, {"hasArticle": None})   # -> False  (AI failed)
        _ai_ok({"total": 500}, {"hasArticle": True}) # -> True
    """
    try:
        total = int((tokens or {}).get("total", 0) or 0)
    except Exception:
        total = 0
    return total > 0 and isinstance(verdict, dict) and verdict.get("hasArticle") is not None


class AIError(RuntimeError):
    """Raised when the AI provider failed to produce a verdict.

    This is NOT "no article" — it means the model call failed (out of balance,
    invalid key, unreachable, or empty output). The caller must NOT treat it as a
    rejection and must NOT send a reply to the sender.
    """


def _load_attachments(service, model, chosen_key=None, chosen_name=None):
    """Download every attachment; one failure must not abort the run.

    Returns ({filename: bytes}, [{"name", "error"}]). If the AI already picked a
    press-release file (`chosen_name`), we still load ALL attachments because
    any of them may hold text or media (D24: collect, then select).

    Example return:
        ({"Press Release - MRCA...docx": b"PK...", "logo.png": b"\x89PNG..."}, [])
    """
    files = {}
    failures = []
    for a in model["attachments"]:
        if not a.get("attachmentId"):
            continue
        name = a.get("filename") or "attachment"
        try:
            files[name] = gmail.download_attachment(
                service, model["messageId"], a["attachmentId"]
            )
        except Exception as e:
            failures.append({"name": name, "error": str(e)[:160]})
    return files, failures


def _attachment_texts(files, chosen_name=""):
    """Extract text from EVERY PDF/DOCX attachment, chosen file first.

    D24: all document attachments are article candidates, not just the one the
    decide step picked. Long documents are capped by extract.expect later.
    """
    order = list(files.keys())
    if chosen_name:
        order.sort(key=lambda n: 0 if chosen_name.lower() in n.lower() else 1)
    out = []
    for name in order:
        if name.lower().endswith((".pdf", ".docx", ".doc")):
            try:
                text = extract.extract_text_from_bytes(files[name], name)
            except Exception:
                text = ""
            if text and text.strip():
                out.append({"name": name, "text": text})
    return out


def _attachment_text(files, chosen_name=""):
    """Return the first non-empty attachment text (chosen file first).

    Kept as the legacy fallback; `_attachment_texts` is the candidate source.
    """
    docs = _attachment_texts(files, chosen_name)
    return docs[0]["text"] if docs else ""


def _sha1_text(text):
    return hashlib.sha1((text or "")[:8000].encode("utf-8", "replace")).hexdigest()


def _add_candidate(candidates, seen, source, name, text, url=""):
    """Add a fetched source to the article pool (dedupe by content)."""
    text = (text or "").strip()
    if len(text) < 120:
        return
    key = _sha1_text(text)
    if key in seen:
        return
    seen.add(key)
    candidates.append({"source": source, "name": name or source, "url": url or "", "text": text})


_RELEASE_RE = re.compile(
    r"for\s+immediate\s+release|news\s+provided\s+by|media\s+release|press\s+release|"
    r"siaran\s+akhbar|kenyataan\s+media|kuala\s+lumpur|petaling\s+jaya|putrajaya",
    re.I,
)
_NOT_ARTICLE = re.compile(
    r"agenda|programme|program\b|schedule|itinerary|invitation|invite|report|summary|"
    r"fact\s*sheet|backgrounder|speech|ucapan|remarks|perasmian",
    re.I,
)


def _candidate_score(subject, cand):
    """Deterministic pre-rank so the AI sees the most release-like sources first."""
    text = cand.get("text") or ""
    name = cand.get("name") or ""
    head = text[:2500]
    score = 0.0
    trust = {"attachment_pdf": 4, "attachment_docx": 4, "attachment_text": 3,
             "drive_link": 3, "onedrive_link": 3, "box_link": 3, "web_link": 2}
    score += trust.get(cand.get("source"), 1)
    if _RELEASE_RE.search(head):
        score += 3
    if len(_RELEASE_RE.findall(head)) >= 2:
        score += 1
    if _NOT_ARTICLE.search(name):
        score -= 3
    if _NOT_ARTICLE.search(head[:500]):
        score -= 1
    score += min(len(text) / 2000.0, 2.0)
    subj_tokens = _key_tokens(_norm_text(subject))
    if subj_tokens:
        head_tokens = _key_tokens(_norm_text(head))
        score += 4.0 * (len(subj_tokens & head_tokens) / len(subj_tokens))
    return score


def _rank_candidates(subject, candidates, chosen_text=""):
    """Return the top-N candidates, always keeping the chosen attachment text."""
    ranked = sorted(candidates, key=lambda c: _candidate_score(subject, c), reverse=True)
    top = ranked[:max(1, config.COLLECT_CANDIDATE_TOP_N)]
    if chosen_text:
        key = _sha1_text(chosen_text)
        if not any(_sha1_text(c["text"]) == key for c in top):
            chosen = next((c for c in ranked if _sha1_text(c["text"]) == key), None)
            if chosen:
                top = top[: max(1, config.COLLECT_CANDIDATE_TOP_N - 1)] + [chosen]
    return top


def _trusted_links(model, decision_link=""):
    """All links literally present in the email (dedupe), decision link guarded.

    The decide AI can hallucinate a URL; only follow it when normalize also saw
    it in the body. Short links were already resolved into `linksFound`.
    """
    links = list(model.get("linksFound", []) or [])
    if decision_link:
        a2 = re.sub(r"[#?].*$", "", decision_link).rstrip("/")
        for l in links:
            a1 = re.sub(r"[#?].*$", "", l).rstrip("/")
            if a1 == a2 or a1 in a2 or a2 in a1:
                links.insert(0, decision_link)
                break
    out = []
    for l in links:
        u = (l or "").strip()
        if not u.startswith(("http://", "https://")):
            continue
        if u not in out:
            out.append(u)
    return out


def _usable_doc_logo(doc_images_detail):
    """True when a document contains a logo that is actually usable (N-1 option B).

    A 40x20 letterhead icon is a ``logo`` in the classifier but is not usable;
    a vector header logo or a raster logo with max side >= BODY_LOGO_MIN_DIM is.
    """
    for doc in doc_images_detail or []:
        for image in doc.get("images") or []:
            if image.get("kind") != "logo":
                continue
            if image.get("vector"):
                return True
            try:
                if max(int(image.get("width") or 0),
                       int(image.get("height") or 0)) >= config.BODY_LOGO_MIN_DIM:
                    return True
            except (TypeError, ValueError):
                continue
    return False


def _usable_logo_files(model, files):
    """True when a logo-named attachment is usable (raster >= 200 px or SVG)."""
    for att in model.get("attachments", []):
        name = str(att.get("filename") or "")
        if "logo" not in name.lower():
            continue
        data = files.get(name) or b""
        if not data:
            continue
        if name.lower().endswith(".svg"):
            return True                      # vector: scalable, no pixel floor
        w, h = extract._image_dims(data)
        if max(w, h) >= config.BODY_LOGO_MIN_DIM:
            return True
    return False


def _gallery_filenames(model, files, media_kit):
    """Attachment + Drive media-kit filenames passed to the gallery matcher."""
    names = [a.get("filename") or "" for a in model.get("attachments", [])]
    names += list(files.keys())
    if media_kit:
        names += [i.get("name") or "" for i in media_kit.get("images", [])]
        names += [i.get("name") or "" for i in media_kit.get("originals", [])]
    out = []
    for name in names:
        if name and name not in out:
            out.append(name)
    return out


def _image_names(files, min_bytes=0):
    """Return filenames that look like images (png/jpg/gif/webp/bmp/svg).

    `min_bytes`: only count files at least this big — tiny KB-range images
    (social-media logos, email signature icons) are excluded so they don't
    count as real article photos.

    Example:
        _image_names({"a.pdf": b"..", "photo.jpg": b"x"*500000})
        -> ["photo.jpg"]   (passes with min_bytes=100_000)
    """
    return [n for n in files
            if n.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"))
            and len(files[n]) >= min_bytes]


# Generic label + stop words dropped before subject/source similarity.
_SUBJECT_STOP = set(
    "press statement release news media advisory update commentary op ed fwd re ref "
    "the and for from with this that a an on of to in by at as is are was were be been "
    "its it their we our you your "
    "dan untuk yang dengan ke di ini itu bagi serta akan pada oleh dari dalam adalah "
    "telah boleh tidak lebih sebagai baru tahun".split()
)


def _norm_text(s):
    """Lowercase, strip Fwd/Re, turn punctuation into spaces, collapse."""
    s = re.sub(r"^(fwd|fw|re|ref)\s*:\s*", "", s or "", flags=re.I)
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def _key_tokens(s):
    return {w for w in _norm_text(s).split() if len(w) >= 3 and w not in _SUBJECT_STOP}


def _subject_match_basis(subject, headline, body_text, source_name=""):
    """Deterministic subject↔source check (D10).

    Returns ("exact", 1.0), ("coverage", ratio) or (None, 0). The subject may be
    a label ("PRESS STATEMENT ON…"); compare it with the headline, the first
    paragraph after the headline, the raw article head and the attachment name.
    """
    ns = _norm_text(subject)
    if len(ns) < 20:
        return None, 0.0
    raw = body_text or ""
    if ns in _norm_text((raw[:2000] or "") + " " + (source_name or "")):
        return "exact", 1.0
    idx = -1
    if headline:
        idx = raw.lower().find((headline or "").lower()[:60])
    if idx >= 0:
        first = raw[idx + len(headline): idx + len(headline) + 1200]
    else:
        first = raw[:1200]
    source = " ".join([headline or "", first, source_name or ""])
    ks = _key_tokens(subject)
    ka = _key_tokens(source)
    if len(ks) >= 2:
        coverage = len(ks & ka) / len(ks)
        if coverage >= 0.60:
            return "coverage", coverage
    return None, 0.0


def _drive_block_reason(df):
    """Turn a refused Drive-file result into one editor-readable sentence."""
    owner = (df.get("owner") or "").strip()
    who = f" (owner: {owner})" if owner else ""
    reason = df.get("reason") or "unknown"
    if reason == "cannotDownloadFile":
        return (f"The Google Drive file{who} is view-only — its owner disabled download, "
                "so the PDF cannot be fetched. Ask the sender to enable download or re-share it.")
    if reason == "file_too_large":
        return f"The Google Drive file{who} is larger than the download cap, so it was not fetched."
    if reason == "unsupported_google_file":
        return "The Google Drive link points at a Google-native file that is not a document/PDF."
    if reason == "trashed":
        return "The Google Drive file is in the trash."
    if reason == "export_failed":
        return "The Google Doc could not be exported as text."
    if reason == "download_failed":
        return "The Google Drive file could not be downloaded (permission or network error)."
    if reason == "fetch_error":
        return f"The Google Drive file could not be checked: {df.get('error', '')}"
    return "The linked Google Drive file could not be used."


def _emit(trace, stage, status, detail):
    """Send one stage result to an optional live-trace callback (lab page)."""
    if not trace:
        return
    try:
        trace(stage, status, detail)
    except Exception as e:
        print(f"[pipeline] trace callback failed for {stage}: {e}")


def _model_summary(model):
    """A compact, safe summary of the normalized email for the Workflow Lab."""
    return {
        "subject": model.get("subject", ""),
        "from": model.get("from", ""),
        "date": model.get("date", ""),
        "threadId": model.get("threadId", ""),
        "messageId": model.get("messageId", ""),
        "attachments": [
            {"filename": a.get("filename", ""), "mimeType": a.get("mimeType", ""),
             "size": a.get("size", 0)}
            for a in model.get("attachments", [])
        ],
        "linksFound": model.get("linksFound", []),
        "bodyTextLen": len(model.get("bodyText", "") or ""),
        "cleanBodyLen": len(model.get("cleanBody", "") or ""),
        "bodyPreview": (model.get("cleanBody", "") or "")[:700],
    }


def process_email(service, email_id, run_id=None, dry_run=False, trace=None, prompt_version=None,
                  client=None, capture_text=False):
    """Process one email and return the checklist row. Logs run + errors to db.

    `run_id` is supplied by the HTTP callers so one run has one row and the final
    status (success | needs_human | error) lands on it. The scheduler omits it.

    `dry_run=True` (Workflow Lab) skips every write: no run log, no pipeline
    result, no archive, no reply. `trace` receives (stage, status, detail) as
    each stage completes.

    Example:
        row = pipeline.process_email(gmail_service, "1a0ea6d2dad4b996")
        row["hasArticle"]  # -> "true"
        row.get("_status") # -> None | "needs_human"
    """
    model = normalize.build_email_model(service, email_id)
    _emit(trace, "normalize", "done", _model_summary(model))
    try:
        from msme.llm import LLMClient
        _lc = LLMClient()
        _model = _lc.provider + "/" + _lc.model
    except Exception:
        _model = "unknown"
    if dry_run:
        run_id = run_id or ("lab-" + str(email_id))
    elif not run_id:
        run_id = db.log_run_start(email_id, model.get("subject", ""), model=_model)
    else:
        try:
            db.set_run_subject(run_id, model.get("subject", ""))
        except Exception:
            pass
    try:
        return _run_pipeline(service, email_id, model, run_id, dry_run=dry_run, trace=trace,
                             prompt_version=prompt_version, client=client,
                             capture_text=capture_text)
    except AIError as e:
        if not dry_run:
            db.log_run_end(run_id, "ai_error", str(e), model=_model)
        raise
    except Exception as e:
        if not dry_run:
            db.log_run_end(run_id, "error", str(e), model=_model)
        raise


def process_model(model, service=None, run_id=None, dry_run=True, trace=None, client=None,
                  prompt_version=None, capture_text=False):
    """Run the stages on an already-normalized model (Workflow Lab / tests).

    This bypasses Gmail: the caller supplies a model built by
    `normalize.build_email_model(..., message=...)` or a sample. Defaults to a
    dry run so nothing is written.
    """
    if dry_run:
        run_id = run_id or ("lab-" + str(model.get("messageId", "sample")))
    elif not run_id:
        run_id = db.log_run_start(model.get("messageId", ""), model.get("subject", ""))
    return _run_pipeline(service, model.get("messageId", ""), model, run_id,
                         dry_run=dry_run, trace=trace, client=client,
                         prompt_version=prompt_version, capture_text=capture_text)


def _run_pipeline(service, email_id, model, run_id, dry_run=False, trace=None, client=None,
                  prompt_version=None, capture_text=False):
    """Execute all stages for one email and collect a `stages` trace.

    The `stages` dict powers the Workflow page ("recent runs" detail):
    each entry is {status, detail} describing what happened at that step.
    `dry_run` skips DB writes, the archive and replies; `trace` streams stages.
    """
    from msme.llm import get_token_tally, reset_token_tally
    reset_token_tally()
    stages = {}
    subject = model.get("subject", "")
    # Record the received email's envelope early; a later AI/archive failure must not lose it.
    if not dry_run:
        try:
            db.save_email(model)
        except Exception as e:
            print(f"[pipeline] save_email failed: {e}")
    try:
        web_mode = str(settings_store.get("WEB_FETCH_MODE") or config.WEB_FETCH_MODE or "probe").strip().lower()
    except Exception:
        web_mode = "probe"
    if web_mode not in ("off", "known", "probe"):
        web_mode = "probe"
    web_allowed = web_mode != "off"
    try:
        auto_filter = bool(settings_store.get("ENABLE_AUTO_FILTER"))
    except Exception:
        auto_filter = config.ENABLE_AUTO_FILTER

    # 1) Decide — AI picks which attachment is the press release + any link.
    decision = decide.decide(model, client=client, prompt_version=prompt_version)
    chosen_name = decision.get("chosenFileName", "") or ""
    chosen_type = decision.get("chosenDocType", "none") or "none"
    stages["decide"] = {
        "status": "done",
        "detail": {
            "chosenAttachmentKey": decision.get("chosenAttachmentKey", ""),
            "chosenFileName": chosen_name,
            "chosenDocType": chosen_type,
            "isEnglish": decision.get("isEnglish"),
            "imagesAvailable": decision.get("imagesAvailable"),
            "linkToFetch": decision.get("linkToFetch", ""),
            "confidence": decision.get("confidence"),
            "reason": decision.get("reason", ""),
        },
    }
    _emit(trace, "decide", "done", stages["decide"]["detail"])

    # 2) Load attachments and extract text from the chosen PDF/DOCX.
    files, attachment_failures = _load_attachments(service, model, chosen_name=chosen_name)
    attachment_text = _attachment_text(files, chosen_name)
    # D24 collect-then-select: every fetched text becomes an article candidate.
    candidates = []
    seen_candidates = set()
    _chosen_docs = _attachment_texts(files, chosen_name)
    for d in _chosen_docs:
        _src = "attachment_pdf" if d["name"].lower().endswith(".pdf") else "attachment_docx"
        _add_candidate(candidates, seen_candidates, _src, d["name"], d["text"])
    stages["load_attachments"] = {
        "status": "done",
        "detail": {
            "attachmentCount": len(files),
            "attachments": [{"name": n, "size": len(d)} for n, d in files.items()],
            "attachmentTextLen": len(attachment_text),
            "texts": [{"name": d["name"], "textLen": len(d["text"])} for d in _chosen_docs],
            "failures": attachment_failures,
        },
    }
    _emit(trace, "load_attachments", "done", stages["load_attachments"]["detail"])

    # 2a) Pull embedded PHOTOS out of EVERY article DOCX/PDF (not only the one
    # the decide step picked). Names are prefixed per file so two docs cannot
    # overwrite each other; identical bytes are de-duplicated.
    embed_images = {}
    try:
        _seen_embed = set()
        for fn, b in files.items():
            if not fn.lower().endswith((".docx", ".doc", ".pdf")):
                continue
            try:
                imgs = extract.extract_doc_images(b, fn)
            except Exception as e:
                print(f"[pipeline] embedded image extract failed for {fn}: {e}")
                continue
            stem = re.sub(r"[^\w-]", "_", os.path.splitext(os.path.basename(fn))[0])[:24]
            for k, v in imgs.items():
                h = hashlib.sha1(v).hexdigest()
                if h in _seen_embed:
                    continue
                _seen_embed.add(h)
                embed_images[f"{stem}-{k}"] = v
    except Exception as e:
        print(f"[pipeline] embedded image extract failed: {e}")

    # 2b) Drive media kit. Fetch it whenever ANY Google Drive folder link is
    # present in the email — even when an attachment article exists — so the
    # richer Drive media (higher-res photos, other-language PDFs) is merged too.
    # link-guard: only links literally present in the email (or revealed by
    # redirect resolution in normalize) count, which kills hallucinated links.
    media_kit = None
    media_kit_formatted = None
    media_source = "drive"
    drive_logo = False
    # Link-guard: a decide link is trusted only when normalize also saw it.
    _decision_link = decision.get("linkToFetch", "") or ""
    trusted_links = _trusted_links(model, _decision_link)
    media_link = _decision_link if (_decision_link and _decision_link in trusted_links) else ""

    drive_link = ""
    drive_release_name = ""
    # (a) prefer the decider's link when it is itself a Drive folder link
    if "drive.google.com" in media_link and "/folders/" in media_link:
        drive_link = media_link
    # (b) otherwise trust any Drive folder link found in the email
    if not drive_link:
        for l in trusted_links:
            if "drive.google.com" in l and "/folders/" in l:
                drive_link = l
                break
    # (c) a short/branded media-kit link (bit.ly/…) may itself resolve to Drive/OneDrive.
    if media_link and not drive_link:
        low = media_link.lower()
        if ("drive.google.com" not in low and "onedrive.live.com" not in low
                and "1drv.ms" not in low and not box_fetch.is_box_link(media_link)):
            final = normalize._resolve_redirect(media_link)
            if final:
                if "drive.google.com" in final:
                    if "/folders/" in final:
                        drive_link = final
                    else:
                        media_link = final
                elif "1drv.ms" in final or "onedrive.live.com" in final:
                    media_link = final
    if drive_link:
        fm = re.search(r"/folders/([A-Za-z0-9_-]+)", drive_link)
        folder_id = fm.group(1) if fm else None
        if folder_id:
            media_kit = drive_fetch.fetch_media_kit(folder_id)
            media_kit_formatted = drive_fetch.format_media_kit(media_kit)
            drive_logo = media_kit.get("docHasEmbeddedImage", False)
            # position-aware classification of the media-kit docs
            drive_doc_logo = media_kit.get("docLogos", False)
            drive_doc_photo = media_kit.get("docPhotos", False)
            # Prefer the release-named doc (multilingual), never the longest
            # speech/deck. The picker is shared with format_media_kit.
            release_doc = drive_fetch.pick_release_doc(media_kit)
            if release_doc and (release_doc.get("text") or "").strip():
                drive_release_name = release_doc.get("name", "")
                if not attachment_text:
                    attachment_text = release_doc["text"]
            # D24: every doc in the kit is a candidate, not only the picked one.
            for d in media_kit.get("mediaKit", []):
                _add_candidate(candidates, seen_candidates, "drive_link",
                               d.get("name", ""), d.get("text", ""), drive_link)
            stages["drive_fetch"] = {
                "status": "done",
                "detail": {
                    "folderId": folder_id,
                    "docs": [{"name": d["name"], "textLen": len(d["text"])} for d in media_kit.get("mediaKit", [])],
                    "images": len(media_kit.get("images", [])),
                    "imagesTruncated": media_kit.get("imagesTruncated", False),
                    "docHasEmbeddedImage": drive_logo,
                    "docLogos": drive_doc_logo,
                    "docPhotos": drive_doc_photo,
                    "selected": drive_release_name,
                    "docImageDetails": media_kit.get("docImageDetails", []),
                },
            }
        else:
            stages["drive_fetch"] = {"status": "done", "detail": {"folderId": None, "note": "no folder id in link"}}

    # 2b-2) Drive FILE link — one PDF/DOCX (e.g. /file/d/<id>/view), not a
    # media-kit folder. Some senders link a single 30+ MB PDF instead of attaching
    # it. A refused download (owner disabled download) is a deliberate outcome:
    # record it and mark the run needs_human — never archive the cover note.
    needs_human = False
    needs_human_reason = ""
    drive_file_pics = {}
    drive_file_logos = {}
    # 2b-1) Google Doc link (docs.google.com/document/d/<id>) — a Drive-native
    # document, not a Drive file link. Export its text (D23).
    doc_ids = []
    if not drive_link:
        for l in ([media_link] if media_link else []) + trusted_links:
            _d = drive_fetch.doc_id_from_link(l)
            if _d and _d not in doc_ids:
                doc_ids.append(_d)
            if len(doc_ids) >= 2:
                break
    doc_id = doc_ids[0] if doc_ids else ""
    if doc_id and not drive_link:
        try:
            df = drive_fetch.fetch_file(doc_id)
            if df.get("ok"):
                drive_release_name = df.get("name") or drive_release_name
                _add_candidate(candidates, seen_candidates, "drive_link",
                               df.get("name", "Google Doc"), df.get("text") or "",
                               f"https://docs.google.com/document/d/{doc_id}")
                if not attachment_text:
                    attachment_text = df.get("text") or ""
                stages["google_doc_fetch"] = {
                    "status": "done",
                    "detail": {"docId": doc_id, "name": df.get("name", ""),
                               "mimeType": df.get("mimeType", ""),
                               "textLen": len(df.get("text") or ""),
                               "extraDocIds": doc_ids[1:]},
                }
                if not attachment_text.strip():
                    needs_human = True
                    needs_human_reason = "The linked Google Doc was exported but contained no text."
            else:
                stages["google_doc_fetch"] = {
                    "status": "blocked",
                    "detail": {"docId": doc_id, "reason": df.get("reason", ""),
                               "error": df.get("error", "")},
                }
                if not attachment_text:
                    needs_human = True
                    needs_human_reason = _drive_block_reason(df)
        except Exception as e:
            stages["google_doc_fetch"] = {"status": "error", "detail": {"error": str(e)[:160]}}
            if not attachment_text:
                needs_human = True
                needs_human_reason = f"Google Doc fetch failed: {str(e)[:140]}"
    file_link = ""
    if not drive_link:
        if drive_fetch.file_id_from_link(media_link):
            file_link = media_link
        if not file_link:
            for l in trusted_links:
                if drive_fetch.file_id_from_link(l):
                    file_link = l
                    break
    if file_link and not drive_link:
        file_id = drive_fetch.file_id_from_link(file_link)
        try:
            df = drive_fetch.fetch_file(file_id)
        except Exception as e:
            df = {"ok": False, "reason": "fetch_error", "error": str(e),
                  "name": "", "size": 0, "owner": ""}
        if df.get("ok"):
            fname = df.get("name") or "drive-file"
            raw = df.get("bytes", b"")
            files[fname] = raw
            drive_release_name = fname
            mime = (df.get("mimeType") or "").lower()
            is_image = (mime.startswith("image/")
                        or fname.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")))
            fetched_text = ""
            kind = ""
            if is_image:
                # A linked IMAGE is media, not the article source: keep the body
                # article and count the image (photo or logo). Never needs_human.
                w, h = extract._image_dims(raw)
                kind = ("logo" if "logo" in fname.lower()
                        else extract._kind_from_bytes(raw))
                if kind == "photo":
                    drive_file_pics[fname] = raw
                elif kind == "logo" and max(w, h) >= config.BODY_LOGO_MIN_DIM:
                    drive_file_logos[fname] = raw
            else:
                fetched_text = (df.get("text") or "")
                _src = "attachment_pdf" if fname.lower().endswith(".pdf") else "drive_link"
                _add_candidate(candidates, seen_candidates, _src, fname, fetched_text, file_link)
                if not attachment_text:
                    attachment_text = fetched_text
            stages["drive_file_fetch"] = {
                "status": "done",
                "detail": {
                    "fileId": file_id,
                    "name": fname,
                    "mimeType": mime,
                    "kind": kind or "document",
                    "size": df.get("size", 0),
                    "owner": df.get("owner", ""),
                    "textLen": len(fetched_text),
                    "canDownload": df.get("canDownload", True),
                },
            }
            if not is_image and not attachment_text.strip():
                needs_human = True
                needs_human_reason = ("The Google Drive file was downloaded but no text could be "
                                      "extracted (likely a scanned/image-only PDF).")
        elif df.get("reason") == "is_folder":
            # A /file/d/<id> link can point at a FOLDER (MATRADE). Treat it as a
            # media kit, not a failed file.
            folder_id = df.get("folderId") or file_id
            try:
                media_kit = drive_fetch.fetch_media_kit(folder_id)
                media_kit_formatted = drive_fetch.format_media_kit(media_kit)
                media_source = "drive"
                drive_logo = media_kit.get("docHasEmbeddedImage", False)
                release_doc = drive_fetch.pick_release_doc(media_kit)
                if release_doc and (release_doc.get("text") or "").strip():
                    drive_release_name = release_doc.get("name", "")
                    if not attachment_text:
                        attachment_text = release_doc["text"]
                for d in media_kit.get("mediaKit", []):
                    _add_candidate(candidates, seen_candidates, "drive_link",
                                   d.get("name", ""), d.get("text", ""), file_link)
                stages["drive_fetch"] = {
                    "status": "done",
                    "detail": {
                        "folderId": folder_id,
                        "docs": [{"name": d["name"], "textLen": len(d["text"])}
                                 for d in media_kit.get("mediaKit", [])],
                        "images": len(media_kit.get("images", [])),
                        "docLogos": media_kit.get("docLogos", False),
                        "docPhotos": media_kit.get("docPhotos", False),
                        "selected": drive_release_name,
                        "docImageDetails": media_kit.get("docImageDetails", []),
                    },
                }
                if not (media_kit.get("mediaKit") or media_kit.get("images")
                        or media_kit.get("originals")):
                    needs_human = True
                    needs_human_reason = "The Google Drive folder is empty (no documents or images)."
            except Exception as e:
                needs_human = True
                needs_human_reason = f"Google Drive folder fetch failed: {str(e)[:140]}"
                stages["drive_fetch"] = {"status": "error", "detail": {"error": str(e)[:160]}}
        else:
            needs_human_reason = _drive_block_reason(df)
            stages["drive_file_fetch"] = {
                "status": "blocked",
                "detail": {
                    "fileId": file_id,
                    "name": df.get("name", ""),
                    "mimeType": df.get("mimeType", ""),
                    "size": df.get("size", 0),
                    "owner": df.get("owner", ""),
                    "canDownload": df.get("canDownload", False),
                    "reason": df.get("reason", ""),
                    "error": df.get("error", ""),
                },
            }
            if not attachment_text:
                needs_human = True

    # 2c) Fix B — Box.com press kit. If the email (or decider) points at a PUBLIC
    # Box shared folder, fetch its photos/docs directly (no login).
    box_images = {}
    box_originals = {}
    box_link = ""
    if media_link and box_fetch.is_box_link(media_link):
        box_link = media_link
    if not box_link:
        for l in trusted_links:
            if box_fetch.is_box_link(l):
                box_link = l
                break
    if box_link:
        try:
            box_kit = box_fetch.fetch_press_kit(box_link)
            for im in box_kit.get("images", []):
                box_images[im["name"]] = im["bytes"]
            for o in box_kit.get("originals", []):
                box_originals[o["name"]] = o["bytes"]
            docs = sorted(box_kit.get("docs", []), key=lambda d: len(d.get("text", "")), reverse=True)
            for d in docs:
                _add_candidate(candidates, seen_candidates, "box_link",
                               d.get("name", ""), d.get("text", ""), box_link)
            if not attachment_text and docs and docs[0].get("text"):
                attachment_text = docs[0]["text"]
            stages["box_fetch"] = {"status": "done", "detail": box_kit.get("detail", {})}
        except Exception as e:
            stages["box_fetch"] = {"status": "error", "detail": {"error": str(e)[:150]}}

    # 2c-2) OneDrive public share (1drv.ms / onedrive.live.com) — folder or file.
    # Same kit shape as Drive; guest cookie + v2.0 item API (D15).
    onedrive_images = {}
    onedrive_originals = {}
    onedrive_link = ""
    for l in trusted_links:
        if onedrive_fetch.is_onedrive_link(l):
            onedrive_link = l
            break
    if onedrive_link:
        try:
            od = onedrive_fetch.fetch_kit(onedrive_link)
            if od.get("mediaKit") or od.get("images") or od.get("originals"):
                if not media_kit:
                    media_kit = od
                    media_source = "onedrive"
                    media_kit_formatted = drive_fetch.format_media_kit(od)
                drive_logo = drive_logo or od.get("docHasEmbeddedImage", False)
                release_doc = drive_fetch.pick_release_doc(od)
                if release_doc and (release_doc.get("text") or "").strip():
                    drive_release_name = drive_release_name or release_doc.get("name", "")
                    if not attachment_text:
                        attachment_text = release_doc["text"]
                for d in od.get("mediaKit", []):
                    _add_candidate(candidates, seen_candidates, "onedrive_link",
                                   d.get("name", ""), d.get("text", ""), onedrive_link)
                onedrive_images = {i["name"]: i["bytes"] for i in od.get("images", []) if i.get("bytes")}
                onedrive_originals = {d["name"]: d["bytes"] for d in od.get("originals", []) if d.get("bytes")}
            stages["onedrive_fetch"] = {"status": "done", "detail": od.get("detail", {})}
        except Exception as e:
            stages["onedrive_fetch"] = {"status": "error", "detail": {"error": str(e)[:160]}}

    # 2c-3) Public web article/speech links. D24: follow them even when the
    # email already has an attachment/Drive article, because the page may hold
    # the full-size photo or a more complete release. Text is a candidate; the
    # extract AI decides which source is the article.
    web_images = {}
    web_logos = {}
    web_attempts = []
    web_articles = []
    web_publisher_logos = []
    web_urls = (web_fetch.candidate_links(trusted_links, model.get("linkTexts") or {},
                                          mode=web_mode)
                if web_allowed else [])
    for web_url in web_urls:
        wf = web_fetch.fetch_article(web_url)
        if wf.get("ok") and wf.get("is_article"):
            _title = (wf.get("title") or "").strip()
            _text = wf["text"]
            if _title and _title.lower() not in _text[:200].lower():
                _text = _title + "\n\n" + _text
            _add_candidate(candidates, seen_candidates, "web_link",
                           _title or web_url, _text, web_url)
            drive_release_name = drive_release_name or _title
            if not attachment_text:
                attachment_text = _text
            web_images.update({i["name"]: i["bytes"] for i in wf.get("images", [])})
            # All site brand logos are publisher_logos, never hasLogo.
            web_publisher_logos += wf.get("publisher_logos", [])
            web_articles.append({"url": web_url, "title": _title[:120],
                                 "textLen": len(_text),
                                 "images": len(wf.get("images", []))})
            web_attempts.append({"url": web_url, "result": "article",
                                 "textLen": len(_text),
                                 "images": len(wf.get("images", []))})
        else:
            web_attempts.append({"url": web_url, "result": "not article",
                                 "reason": wf.get("reason", "")})
    if web_mode == "off":
        stages["web_fetch"] = {"status": "skipped",
                               "detail": {"reason": "WEB_FETCH_MODE=off", "mode": web_mode}}
    elif web_urls:
        stages["web_fetch"] = {
            "status": "done" if (web_articles or web_images) else "empty",
            "detail": {"mode": web_mode, "tried": len(web_urls),
                       "articles": web_articles[:6], "attempts": web_attempts[:6],
                       "images": list(web_images),
                       "publisherLogos": web_publisher_logos[:10]},
        }

    # 2d) Images embedded in the HTML body (<img src="https://...">). Many
    # senders inline press photos/logos instead of attaching them. Web-sized
    # photos are 30-100 KB, so the 1 MB attachment rule does NOT apply:
    #   - photo dimensions  -> body_pics  (hasPic)
    #   - logo >= 200 px    -> body_logos (hasLogo); icons/signature <= 200 skipped
    body_pics = {}
    body_logos = {}
    body_image_skips = []
    body_urls = (model.get("bodyImageUrls", []) or []) if web_allowed else []

    def _ext_for(data):
        if data[:2] == b"\xff\xd8":
            return ".jpg"
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return ".png"
        if data[:6] in (b"GIF87a", b"GIF89a"):
            return ".gif"
        if data[:2] == b"BM":
            return ".bmp"
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return ".webp"
        return ".img"

    for idx, url in enumerate(body_urls, 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=config.BODY_IMAGE_TIMEOUT) as resp:
                data = resp.read(config.BODY_IMAGE_MAX_BYTES + 1)
            if len(data) > config.BODY_IMAGE_MAX_BYTES:
                body_image_skips.append({"url": url, "reason": "too_large"})
                continue
            if len(data) < config.BODY_IMAGE_MIN_BYTES:
                body_image_skips.append({"url": url, "reason": "empty_or_error"})
                continue
            # D24: dimensions decide, never the file size. An 8.6 KB 250x87
            # logo is media; a 1x1 tracker still fails the 200 px logo floor.
            w, h = extract._image_dims(data)
            if w <= 0 or h <= 0:
                body_image_skips.append({"url": url, "reason": "unreadable_dimensions"})
                continue
            kind = extract._kind_from_bytes(data)
            if kind == "photo":
                body_pics[f"bodyphoto-{idx}{_ext_for(data)}"] = data
            elif kind == "logo" and max(w, h) >= config.BODY_LOGO_MIN_DIM:
                body_logos[f"bodylogo-{idx}{_ext_for(data)}"] = data
            else:
                body_image_skips.append({"url": url, "reason": f"kind={kind}",
                                         "dims": [w, h]})
        except Exception as e:
            body_image_skips.append({"url": url, "reason": str(e)[:100]})
    if not web_allowed:
        stages["body_images"] = {"status": "skipped",
                                 "detail": {"reason": "WEB_FETCH_MODE=off"}}
    elif body_urls:
        stages["body_images"] = {
            "status": "done" if (body_pics or body_logos) else "empty",
            "detail": {
                "found": len(body_urls),
                "photos": list(body_pics),
                "logos": list(body_logos),
                "skipped": body_image_skips[:8],
            },
        }

    # 2e) Direct asset links ("Click to download" PNG/logo). Only a response that
    # IS an image is accepted; an HTML page is not parsed (T-013). A filename/URL
    # containing "logo" wins over dimensions (a 1220x1281 logo is not a photo).
    asset_pics = {}
    asset_logos = {}
    asset_attempts = []
    asset_candidates = []
    _asset_hints = ("/download/", "press-kit", "presskit", "media-kit", "mediakit",
                    "media_outreach", "/asset", ".png", ".jpg", ".jpeg", ".gif")

    def _add_asset(u):
        u = (u or "").strip()
        if not u.startswith(("http://", "https://")):
            return
        low = u.lower()
        if any(h in low for h in ("facebook.com", "twitter.com", "linkedin.com",
                                  "instagram.com", "sendgrid.net", "/wf/open")):
            return
        if "drive.google.com" in low or box_fetch.is_box_link(u):
            return
        if u not in asset_candidates:
            asset_candidates.append(u)

    for u in (([media_link] + list(model.get("linksFound", []))) if web_allowed else []):
        if any(h in (u or "").lower() for h in _asset_hints):
            _add_asset(u)
    for url in asset_candidates[:config.ASSET_LINK_MAX_LINKS]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=config.ASSET_LINK_TIMEOUT) as resp:
                ctype = (resp.headers.get("Content-Type") or "").lower()
                disp = resp.headers.get("Content-Disposition") or ""
                data = resp.read(config.ASSET_LINK_MAX_BYTES + 1)
            if "image/" not in ctype:
                asset_attempts.append({"url": url, "result": f"not an image ({ctype[:40]})"})
                continue
            if len(data) > config.ASSET_LINK_MAX_BYTES:
                asset_attempts.append({"url": url, "result": "too_large"})
                continue
            m = re.search(r'filename="?([^";]+)', disp, re.I)
            fname = os.path.basename(m.group(1).strip()) if m else os.path.basename(url.split("?")[0])
            w, h = extract._image_dims(data)
            hint = (fname + " " + url).lower()
            kind = "logo" if "logo" in hint else extract._kind_from_bytes(data)
            ext = _ext_for(data)
            n = len(asset_pics) + len(asset_logos) + 1
            if kind == "logo" and max(w, h) >= config.BODY_LOGO_MIN_DIM:
                name = f"assetlogo-{n}{ext}"
                asset_logos[name] = data
                asset_attempts.append({"url": url, "result": f"logo {w}x{h}", "name": name})
            elif kind == "photo":
                name = f"assetphoto-{n}{ext}"
                asset_pics[name] = data
                asset_attempts.append({"url": url, "result": f"photo {w}x{h}", "name": name})
            else:
                asset_attempts.append({"url": url, "result": f"kind={kind}", "dims": [w, h]})
        except Exception as e:
            asset_attempts.append({"url": url, "result": str(e)[:100]})
    if not web_allowed:
        stages["asset_link"] = {"status": "skipped",
                                "detail": {"reason": "WEB_FETCH_MODE=off"}}
    elif asset_candidates:
        stages["asset_link"] = {
            "status": "done" if (asset_pics or asset_logos) else "empty",
            "detail": {"tried": len(asset_candidates[:config.ASSET_LINK_MAX_LINKS]),
                       "photos": list(asset_pics), "logos": list(asset_logos),
                       "attempts": asset_attempts[:4]},
        }

    # 3) Collect -> select. The AI sees the email body plus the best fetched
    #    candidates (attachments, Drive, OneDrive, Box, web) and chooses the
    #    actual article. Nothing is chosen by source priority before this point.
    _fetch_keys = ("drive_fetch", "drive_file_fetch", "google_doc_fetch", "box_fetch",
                   "onedrive_fetch", "web_fetch", "body_images", "asset_link")
    _fetch_detail = {k: stages[k]["detail"] for k in _fetch_keys if k in stages}
    if _fetch_detail:
        _emit(trace, "fetch", "done", _fetch_detail)
    ranked_candidates = _rank_candidates(subject, candidates, attachment_text)
    for i, c in enumerate(ranked_candidates, 1):
        c["label"] = f"C{i}"
    stages["collect"] = {
        "status": "done",
        "detail": {
            "candidates": len(candidates),
            "selectedForAI": [
                {"label": c["label"], "source": c["source"], "name": c["name"],
                 "textLen": len(c["text"]), "score": round(_candidate_score(subject, c), 2)}
                for c in ranked_candidates
            ],
            "dropped": max(0, len(candidates) - len(ranked_candidates)),
        },
    }
    _emit(trace, "collect", "done", stages["collect"]["detail"])
    extraction = extract.extract(
        model, attachment_text, drive_media=media_kit_formatted, drive_logo=drive_logo,
        candidates=ranked_candidates, client=client, prompt_version=prompt_version,
    )
    body_text = str(extraction.get("bodyText", "") or "").strip()
    # Fallback: if the extract AI returned nothing but we DID read a candidate,
    # keep that real text instead of discarding it.
    extract_fallback = ""
    chosen_label = str(extraction.get("chosenCandidate", "") or "").strip()
    chosen_cand = next((c for c in ranked_candidates if c.get("label") == chosen_label), None)
    if not body_text and chosen_cand:
        body_text = chosen_cand["text"].strip()
        extract_fallback = f"candidate:{chosen_cand['source']}"
    if not body_text and attachment_text:
        body_text = attachment_text.strip()
        extract_fallback = "attachment_text"
    if chosen_label == "email_body":
        article_source = "email_body"
    elif chosen_cand:
        article_source = chosen_cand["source"]
    else:
        article_source = str(extraction.get("articleSource", "uncertain") or "uncertain")
    # A blocked source is not fatal when the body or another candidate supplied
    # the article. Keep needs_human only when the AI still cannot find one.
    if needs_human and body_text and not extraction.get("needsHumanFetch"):
        stages["collect"]["detail"]["clearedNeedsHuman"] = needs_human_reason
        needs_human = False
        needs_human_reason = ""
    # The extract agent is text-only: it cannot see images, and it hallucinates
    # "logo in article" for emails that contain no article at all (e.g. a pitch
    # whose real article is behind an unfetched Drive link). Only trust its
    # logo/image flags when we actually retrieved article text.
    ai_logo = extraction.get("hasLogoInArticle") in (True, "true", "True") and bool(body_text)
    ai_image = extraction.get("hasImageInArticle") in (True, "true", "True") and bool(body_text)
    stages["extract"] = {
        "status": "done",
        "detail": {
            "articleSource": article_source,
            "chosenCandidate": chosen_label,
            "chosenName": (chosen_cand or {}).get("name", ""),
            "bodyTextLen": len(body_text),
            "fallback": extract_fallback,
            "hasLogoInArticle": ai_logo,
            "hasImageInArticle": ai_image,
            "needsHumanFetch": extraction.get("needsHumanFetch"),
            "confidence": extraction.get("confidence"),
            "evidence": extraction.get("evidence", ""),
            "bodyTextPreview": body_text[:200],
        },
    }
    if capture_text:
        stages["extract"]["detail"]["bodyText"] = body_text
    _emit(trace, "extract", "done", stages["extract"]["detail"])

    # 4) Logo flags — signals that a logo/photo exists. The deterministic
    #    classifier (classify_doc_images) reads real image dimensions from the
    #    PDF/DOCX, so a small badge is "logo" and a large image is "photo" —
    #    no more guessing from a raw byte pattern.
    #   docLogo      : a LOGO image embedded in the attachment doc
    #   docPhoto     : a PHOTO/hero image embedded in the attachment doc
    #   visionLogo   : (optional) AI vision call on an image — not wired yet
    #   aiLogo       : kept for the verify prompt (set from docLogo; the text-only
    #                  extract agent cannot see images, so we do not trust its guess)
    #   hasLogoFile  : true only if an ATTACHMENT FILE NAME contains "logo".
    #                  hasLogo (row) also counts body/asset-link logos (D9).
    doc_logo = False
    doc_photo = False
    doc_images_detail = []
    for name, data in files.items():
        if name.lower().endswith((".pdf", ".docx", ".doc")):
            info = extract.classify_doc_images(data, name)
            doc_images_detail.append({"file": name, "hasImage": info["has_image"],
                                      "images": info["images"],
                                      "truncated": info.get("truncated", False)})
            if info["has_logo"]:
                doc_logo = True
            if info["has_photo"]:
                doc_photo = True
    # Merge Drive media-kit doc signals (position-aware classifier already ran
    # during fetch_media_kit) so a header logo in a Drive DOCX also counts.
    if media_kit:
        doc_images_detail += media_kit.get("docImageDetails", [])
        doc_logo = doc_logo or media_kit.get("docLogos", False)
        doc_photo = doc_photo or media_kit.get("docPhotos", False)
    # The extract AI is text-only and cannot see images — replace its guess with
    # the deterministic doc-level signals (Option D).
    ai_logo = doc_logo or bool(ai_logo)
    vision_logo = False
    # hasLogo column = filename check OR a standalone attachment image that
    # classifies as a logo (e.g. Jobstreet's inline_image 1033x275 PNG).
    has_logo_file = any("logo" in (a.get("filename") or "").lower() for a in model.get("attachments", []))
    attachment_logos = {}
    _al_n = 0
    for _name, _data in files.items():
        _w, _h = extract._image_dims(_data)
        if _w <= 0 or _h <= 0:
            continue
        if extract._kind_from_bytes(_data) == "logo" and max(_w, _h) >= config.BODY_LOGO_MIN_DIM:
            _al_n += 1
            attachment_logos[f"attachmentlogo-{_al_n}{_ext_for(_data)}"] = _data
    stages["logo_scan"] = {
        "status": "done",
        "detail": {
            "docLogo": doc_logo,
            "docPhoto": doc_photo,
            "visionLogo": vision_logo,
            "aiLogo": ai_logo,
            "hasLogoFile": has_logo_file,
            "attachmentLogos": list(attachment_logos),
            "docImages": doc_images_detail,
        },
    }
    _emit(trace, "logo_scan", "done", stages["logo_scan"]["detail"])

    # 5) Verify — the AI turns everything into the final checklist verdict.
    # Only images >= MIN_IMAGE_BYTES (MB-range) count as pics (KB-range email logos don't).
    # hasPic = real photo IMAGE FILES present: either attached to the email OR
    # in the Drive media kit (both get downloaded to the local images/ folder).
    # Images embedded inside the article PDF/DOCX are NOT hasPic — they are
    # hasImageInArticle (driven by docPhoto).
    real_image_names = _image_names(files, config.MIN_IMAGE_BYTES)
    # Drive media-kit image files that are actual photos (not logos) AND at
    # least MIN_IMAGE_BYTES (MB-range) — small logo/social thumbnails don't count.
    drive_kit_pics = []
    if media_kit:
        for _img in media_kit.get("images", []):
            _n = (_img.get("name") or "").lower()
            if "logo" not in _n and int(_img.get("size", 0) or 0) >= config.MIN_IMAGE_BYTES:
                drive_kit_pics.append(_img["name"])
    embed_pics = [n for n, b in embed_images.items() if len(b) >= config.MIN_IMAGE_BYTES]
    box_pics = [n for n, b in box_images.items() if len(b) >= config.MIN_IMAGE_BYTES]
    body_pic_names = list(body_pics)
    body_logo_names = list(body_logos)
    asset_pic_names = list(asset_pics)
    asset_logo_names = list(asset_logos)
    drive_file_pic_names = list(drive_file_pics)
    drive_file_logo_names = list(drive_file_logos)
    web_pic_names = list(web_images)
    web_logo_names = list(web_logos)
    attachment_logo_names = list(attachment_logos)
    has_pic = (bool(real_image_names) or bool(drive_kit_pics) or bool(embed_pics)
               or bool(box_pics) or bool(body_pic_names) or bool(asset_pic_names)
               or bool(drive_file_pic_names) or bool(web_pic_names))
    has_logo = (bool(has_logo_file) or bool(attachment_logo_names)
                or bool(body_logo_names) or bool(asset_logo_names)
                or bool(drive_file_logo_names))
    # N-1 option B: a logo only counts as USABLE when it is vector or its max
    # side is >= BODY_LOGO_MIN_DIM. A 40x20 icon or a tiny logo-named file is
    # still a factual hasLogo, but it must not suppress the gallery.
    doc_logo_usable = _usable_doc_logo(doc_images_detail)
    has_logo_file_usable = _usable_logo_files(model, files)
    has_usable_logo = (bool(attachment_logo_names) or bool(body_logo_names)
                       or bool(asset_logo_names) or bool(drive_file_logo_names)
                       or doc_logo_usable or has_logo_file_usable)
    ai_logo = doc_logo_usable or bool(ai_logo)

    # N-2 library update — an email that only distributes a logo/building photo
    # is a gallery update, not "no article". Detect before the N-1 gallery and
    # Verify so the wrong paths (gallery match, verify, filter, reply, archive)
    # never run for it.
    _lu = None
    try:
        from msme.receive import library_update
        _lu = library_update.classify({
            "subject": model.get("subject", ""),
            "raw_body": model.get("bodyText") or model.get("cleanBody") or "",
            "body_text": body_text,
            "candidates": ranked_candidates,
            "decision": decision,
            "attachments": model.get("attachments", []),
            "files": files,
            "needs_human": needs_human,
            "media": {"hasPic": has_pic, "hasLogo": has_logo,
                      "docLogo": doc_logo, "docPhoto": doc_photo},
            "from_email": model.get("fromEmail", ""),
            "from_name": model.get("fromName", ""),
            "message_id": model.get("messageId", ""),
            "date": model.get("date", ""),
        })
    except Exception as e:  # noqa: BLE001 — a detector error must not fail the run
        stages["library_update"] = {"status": "error", "detail": {"error": str(e)[:300]}}
        _emit(trace, "library_update", "error", stages["library_update"]["detail"])
        print(f"[pipeline] library_update detect error: {e}")

    if _lu:
        _stored = {}
        if not dry_run:
            try:
                _stored = library_update.store_update(_lu, dry_run=False)
            except Exception as e:  # noqa: BLE001 — a store error must not fail the run
                print(f"[pipeline] library_update store failed: {e}")
                _stored = {"error": str(e)[:300]}
        stages["library_update"] = {"status": "done", "detail": {
            "brand": _lu.get("brand", ""),
            "confidence": _lu.get("confidence", ""),
            "files": len(_lu.get("files") or {}),
            "store": _stored,
        }}
        _emit(trace, "library_update", "done", stages["library_update"]["detail"])
        print(f"[pipeline] library_update brand={_lu.get('brand') or '(unknown)'} "
              f"files={len(_lu.get('files') or {})} promoted={_stored.get('promoted', 0)}")
        # Skip verify/filter/archive/reply: build the row inline and return.
        lu_row = {
            "subject": model["subject"],
            "threadId": model.get("threadId", ""),
            "messageId": model.get("messageId", ""),
            "rfc822MessageId": model.get("rfc822MessageId", ""),
            "date": model.get("date", "")[:10],
            "folderId": "", "folderUrl": "",
            "articleFile": "",
            "hasArticle": "false",
            "hasPic": "true" if has_pic else "false",
            "hasLogo": "true" if has_logo else "false",
            "hasUsableLogo": "true" if has_usable_logo else "false",
            "hasLogoInArticle": "false",
            "hasImageInArticle": "false",
            "subjectMatch": "false",
            "subjectScore": "0",
            "readyToFilter": "false",
            "emailType": "library_update",
        }
        lu_row["_runId"] = run_id
        if not dry_run:
            db.save_pipeline_result(run_id, email_id, model["subject"], stages, lu_row)
            db.log_run_end(run_id, "success")
        return lu_row

    # N-1 gallery — only with an article and no usable image. The stage never
    # fails the run: a miss continues to the normal ask email.
    gallery_logos = {}
    if not config.GALLERY_ENABLED:
        stages["gallery"] = {"status": "skipped",
                             "detail": {"reason": "GALLERY_ENABLED=false"}}
    elif not body_text:
        stages["gallery"] = {"status": "skipped", "detail": {"reason": "no article"}}
    elif has_pic or has_usable_logo or doc_photo:
        stages["gallery"] = {"status": "skipped", "detail": {
            "reason": "usable image present",
            "hasPic": has_pic, "hasUsableLogo": has_usable_logo,
            "docPhoto": doc_photo}}
    else:
        try:
            index = gallery.load_index()
            result = gallery.match({
                "subject": model.get("subject", ""),
                "from_name": model.get("fromName", ""),
                "from_email": model.get("fromEmail", ""),
                "filenames": _gallery_filenames(model, files, media_kit),
                "body": body_text,
            }, index)
            if result.get("status") == "hit":
                picked = gallery.pick(result["detail"])
                gallery_logos[picked["name"]] = picked["bytes"]
                has_usable_logo = True
                has_logo = True
                stages["gallery"] = {"status": "hit", "detail": result["detail"]}
                print(f"[gallery] hit {result['detail'].get('brand')} "
                      f"tier={result['detail'].get('tier')} file={picked['name']}")
            else:
                stages["gallery"] = {"status": "miss",
                                     "detail": result.get("detail", {})}
        except Exception as e:  # noqa: BLE001 — a gallery error must not fail the run
            stages["gallery"] = {"status": "error", "detail": {"error": str(e)[:300]}}
            print(f"[gallery] error: {e}")
    _emit(trace, "gallery", stages["gallery"]["status"], stages["gallery"]["detail"])
    stages["logo_scan"]["detail"]["hasUsableLogo"] = has_usable_logo
    stages["logo_scan"]["detail"]["docLogoUsable"] = doc_logo_usable

    flags = {
        "hasPic": has_pic,
        "hasLogo": has_usable_logo,
        "docLogo": doc_logo_usable,
        "docPhoto": doc_photo,
        "visionLogo": vision_logo,
        "aiLogo": ai_logo,
        "aiImage": ai_image,
        "hasLogoFile": has_logo_file_usable,
        "hasUsableLogo": has_usable_logo,
    }
    # Body/asset LOGOS are not "images in the article" (they are standalone
    # assets); flags.hasLogo carries them. Only photos/doc images go to verify.
    image_names = (list(real_image_names) + body_pic_names + asset_pic_names
                   + drive_file_pic_names + web_pic_names)
    if media_kit:
        image_names += [i["name"] for i in media_kit.get("images", [])]
    article = {
        "subject": model["subject"],
        "from": model["from"],
        "date": model["date"],
        "bodyText": body_text,
    }
    verdict = verify.verify(article, image_names, flags, evidence=extraction.get("evidence", ""),
                             client=client, prompt_version=prompt_version)
    # D10: a label subject ("PRESS STATEMENT ON …") may not resemble the
    # headline. Accept it when it appears verbatim in the article head/filename,
    # or when ≥60% of its key tokens appear in headline + first paragraph.
    subject_source = ((chosen_cand or {}).get("name") or chosen_name
                      or drive_release_name)
    match_basis, match_cov = _subject_match_basis(
        model.get("subject", ""), verdict.get("headline", ""), body_text, subject_source
    )
    if match_basis:
        verdict["subjectMatch"] = True
        try:
            _ai_score = int(verdict.get("subjectScore") or 0)
        except Exception:
            _ai_score = 0
        if match_basis == "exact":
            verdict["subjectScore"] = max(_ai_score, 85)
        else:
            verdict["subjectScore"] = max(_ai_score, min(95, round(70 + 25 * match_cov)))
    # Deterministic evidence wins: the AI is text-only and cannot see a raster or
    # vector logo inside the document. If classify_doc_images found one, the
    # checklist must say so (verify._finalize only downgrades today).
    if verdict.get("hasArticle"):
        if doc_logo_usable:
            verdict["hasLogoInArticle"] = True
        if doc_photo:
            verdict["hasImageInArticle"] = True
    # Recompute readyToFilter after the deterministic overrides above; the AI
    # computed it from the original (possibly wrong) subject score / flags.
    _media_asset = (has_pic or has_usable_logo or bool(doc_photo)
                    or bool(verdict.get("hasLogoInArticle"))
                    or bool(verdict.get("hasImageInArticle")))
    try:
        _final_score = int(verdict.get("subjectScore") or 0)
    except Exception:
        _final_score = 0
    verdict["readyToFilter"] = bool(verdict.get("hasArticle") and _media_asset and _final_score > 60)
    stages["verify"] = {
        "status": "done",
        "detail": {
            "headline": verdict.get("headline", ""),
            "subjectMatch": verdict.get("subjectMatch"),
            "subjectScore": verdict.get("subjectScore"),
            "subjectMatchBasis": match_basis or "",
            "subjectCoverage": round(match_cov, 2) if match_basis else None,
            "hasArticle": verdict.get("hasArticle"),
            "hasPic": verdict.get("hasPic"),
            "hasLogo": verdict.get("hasLogo"),
            "hasLogoInArticle": verdict.get("hasLogoInArticle"),
            "hasImageInArticle": verdict.get("hasImageInArticle"),
            "readyToFilter": verdict.get("readyToFilter"),
            "reason": verdict.get("reason", ""),
        },
    }
    if needs_human:
        verdict["hasArticle"] = False
        verdict["readyToFilter"] = False
        verdict["reason"] = needs_human_reason or verdict.get("reason", "")
        stages["verify"]["detail"].update({
            "hasArticle": False,
            "readyToFilter": False,
            "reason": verdict["reason"],
            "needsHumanFetch": True,
        })
        stages["needs_human"] = {
            "status": "blocked",
            "detail": {"reason": needs_human_reason},
        }
        _emit(trace, "needs_human", "blocked", stages["needs_human"]["detail"])
    _emit(trace, "verify", "done", stages["verify"]["detail"])
    print(f"[pipeline] email={email_id} body_len={len(body_text)} "
          f"doc_logo={doc_logo} ai_logo={ai_logo} verdict_article={verdict.get('hasArticle')} "
          f"verdict_match={verdict.get('subjectMatch')} score={verdict.get('subjectScore')}")

    # Token usage across the 3 AI calls + which model/provider ran.
    tokens = get_token_tally()
    try:
        from msme.llm import LLMClient
        _lc = LLMClient()
        tokens["model"] = _lc.provider + "/" + _lc.model
    except Exception:
        tokens["model"] = "unknown"
    stages["tokens"] = {"status": "done", "detail": tokens}
    _emit(trace, "tokens", "done", tokens)

    # --- AI-failure guard: an empty verdict (0 tokens / no hasArticle) is NOT
    # "no article" — it means the AI provider failed. Fail loudly: mark the run
    # as ai_error, build no checklist row, and never send a rejection reply.
    if not _ai_ok(tokens, verdict):
        try:
            from msme import llm as _llm
            _err = _llm.last_error()
        except Exception:
            _err = {"error": "", "status": None}
        msg = ("AI provider returned no verdict (out of balance, invalid key, "
               "unreachable, or empty output)")
        if _err.get("error"):
            msg += f": {_err['error']}"
        vd = stages.get("verify", {}).get("detail", {})
        vd["error"] = msg
        stages["verify"] = {"status": "error", "detail": vd}
        stages["ai_error"] = {
            "status": "error",
            "detail": {"error": msg, "tokens": tokens,
                       "provider_status": _err.get("status")},
        }
        _emit(trace, "ai_error", "error", stages["ai_error"]["detail"])
        if not dry_run:
            db.save_pipeline_result(run_id, email_id, subject, stages, {}, status="error")
            db.log_run_end(run_id, "ai_error", msg, model=tokens.get("model", ""))
        raise AIError(msg)

    # 6) Build checklist row (14 cols)
    headline = str(verdict.get("headline", "") or "")
    article_name = re.sub(r"[^\w\s-]", "", headline).replace(" ", "-") or "article"
    article_name = re.sub(r"-+", "-", article_name).strip("-")[:80]

    # 7) Archive to PC: a folder named after the subject containing the article,
    #    images/, and originals/ (PDF/DOCX). No Google Drive upload.
    folder_id = ""
    folder_url = ""
    local_path = ""
    if needs_human:
        # The real source was never fetched — do not archive the cover note as
        # if it were an article. The run is marked needs_human instead.
        stages["archive"] = {
            "status": "skipped",
            "detail": {"reason": "source not fetched — needs human", "why": needs_human_reason},
        }
    elif dry_run:
        _all_media = {**files, **embed_images, **box_images, **body_pics, **body_logos,
                      **asset_pics, **asset_logos, **drive_file_pics,
                      **drive_file_logos, **onedrive_images,
                      **web_images, **web_logos, **attachment_logos, **gallery_logos}
        _img_ext = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".heic", ".tiff")
        _doc_ext = (".pdf", ".docx", ".doc", ".txt", ".md")
        try:
            from msme.receive import archive as _archive
            _folder = _archive._clean_subject(model.get("subject", "")) or "article"
        except Exception:
            _folder = "article"
        stages["archive"] = {
            "status": "preview",
            "detail": {
                "dryRun": True,
                "wouldWrite": os.path.join(config.LOCAL_ARCHIVE_DIR, _folder),
                "folderName": _folder,
                "articleFile": (article_name or "article") + ".md",
                "images": [n for n in _all_media if n.lower().endswith(_img_ext)],
                "originals": ([n for n in _all_media if n.lower().endswith(_doc_ext)]
                              + list(box_originals) + list(onedrive_originals)),
            },
        }
    else:
        try:
            from msme.receive import archive
            folder_path, uploaded = archive.archive_email(
                model,
                body_text,
                article_name,
                email_images={**files, **embed_images, **box_images, **body_pics, **body_logos,
                             **asset_pics, **asset_logos, **drive_file_pics,
                             **drive_file_logos, **onedrive_images,
                             **web_images, **web_logos, **attachment_logos, **gallery_logos},
                email_originals={**box_originals, **onedrive_originals},
                drive_images=(media_kit.get("images", []) if (media_kit and media_source == "drive") else []),
                drive_originals=(media_kit.get("originals", []) if (media_kit and media_source == "drive") else []),
                drive=creds.drive() if (media_kit and media_source == "drive"
                                        and (media_kit.get("images") or media_kit.get("originals"))) else None,
            )
            local_path = folder_path or ""
            stages["archive"] = {
                "status": "done",
                "detail": {
                    "localPath": local_path,
                    "folderName": (model.get("subject") or "")[:60],
                    "articleFile": (article_name or "article") + ".md",
                    "images": (uploaded or {}).get("images", 0),
                    "originals": (uploaded or {}).get("originals", 0),
                    "files": (uploaded or {}).get("files", []),
                },
            }
            print(f"[pipeline] archived local path={local_path} images={(uploaded or {}).get('images',0)}")
        except Exception as e:
            stages["archive"] = {"status": "error", "detail": {"error": str(e)}}
            print(f"[pipeline] archive failed: {e}")
    _emit(trace, "archive", stages["archive"]["status"], stages["archive"]["detail"])

    # 8) Build the 14-column checklist row (stored as strings for the sheet).
    row = {
        "subject": model["subject"],
        "threadId": model.get("threadId", ""),
        "messageId": model.get("messageId", ""),
        "rfc822MessageId": model.get("rfc822MessageId", ""),
        "date": model.get("date", "")[:10],
        "folderId": folder_id,
        "folderUrl": folder_url,
        "articleFile": (article_name or "article") + ".md",
        "hasArticle": "true" if verdict.get("hasArticle") else "false",
        # hasPic = deterministic: real photo image FILES present (email attachments
        # >= MIN_IMAGE_BYTES OR Drive media-kit photos). Images inside the
        # article PDF/DOCX are hasImageInArticle, not hasPic.
        "hasPic": "true" if has_pic else "false",
        # hasLogo = a standalone logo asset was provided: an attachment filename
        # contains "logo", OR an inline body logo, OR a direct asset-link logo.
        # hasUsableLogo is the N-1 option-B flag (>= 200 px or vector) and is
        # used by the ready/reply decision; it is not a 14-column checklist field.
        "hasLogo": "true" if has_logo else "false",
        "hasUsableLogo": "true" if has_usable_logo else "false",
        "hasLogoInArticle": "true" if verdict.get("hasLogoInArticle") else "false",
        "hasImageInArticle": "true" if verdict.get("hasImageInArticle") else "false",
        "subjectMatch": "true" if verdict.get("subjectMatch") else "false",
        "subjectScore": str(verdict.get("subjectScore", 0) or 0),
        "readyToFilter": "true" if verdict.get("readyToFilter") else "false",
    }
    row["_runId"] = run_id
    if needs_human:
        row["articleFile"] = ""
        row["_status"] = "needs_human"
        row["_needs_human_reason"] = needs_human_reason

    # 8b) Editorial filter — only for ready articles, inside the same pipeline.
    # The verdict is linked to the checklist row by checklist.save_checklist().
    if row["readyToFilter"] != "true":
        stages["filter"] = {"status": "skipped",
                            "detail": {"reason": "not ready to filter"}}
    elif dry_run:
        stages["filter"] = {"status": "skipped",
                            "detail": {"reason": "dry_run"}}
    elif not auto_filter:
        stages["filter"] = {"status": "skipped",
                            "detail": {"reason": "ENABLE_AUTO_FILTER=false"}}
    else:
        _farticle = {
            "subject": model.get("subject", ""),
            "from": model.get("from", ""),
            "date": model.get("date", ""),
            "bodyText": body_text,
        }
        try:
            _fresult = filter_judge.judge(_farticle)
            _fresult["input"] = {
                "subject": _farticle["subject"][:120],
                "from": _farticle["from"][:80],
                "date": _farticle["date"],
                "bodyTextLen": len(_farticle["bodyText"] or ""),
            }
            _ftext = (_farticle.get("bodyText") or "")[:12000]
            _fresult["article_text"] = _ftext
            _fresult["article_hash"] = hashlib.sha256(_ftext.encode("utf-8")).hexdigest()[:12]
            _fresult["article_len"] = len(_ftext)
            row["_filter"] = _fresult
            filter_log.log_verdict(_farticle, _fresult, source="receive")
            stages["filter"] = {
                "status": "done",
                "detail": {
                    "outcome": _fresult.get("outcome"),
                    "weighted": _fresult.get("weighted"),
                    "gate": _fresult.get("gate"),
                    "confidence": _fresult.get("confidence"),
                    "model": _fresult.get("model"),
                    "gates": _fresult.get("gates", {}),
                    "scores": _fresult.get("scores", {}),
                },
            }
        except Exception as e:
            _ferr = str(e)[:300]
            filter_log.log_error({**_farticle, "_source": "receive"}, e)
            row["_filter"] = {"outcome": "ERROR", "error": _ferr}
            stages["filter"] = {"status": "error", "detail": {"error": _ferr}}
    _emit(trace, "filter", stages["filter"]["status"], stages["filter"]["detail"])

    if not dry_run:
        db.save_pipeline_result(run_id, email_id, subject, stages, row)

    # 9) If the article is NOT ready to filter, email the sender an apology that
    #    explains why + what's missing + how to resend. For development this goes
    #    to config.REPLY_TO_EMAIL (fixed_email mode); later REPLY_MODE="sender"
    #    switches to the email's real From address.
    if row["readyToFilter"] == "false":
        if dry_run:
            stages["reply"] = {"status": "skipped", "detail": {"reason": "dry_run"}}
            _emit(trace, "reply", "skipped", stages["reply"]["detail"])
        else:
            try:
                from msme.receive import reply
                result = reply.send_reply_for_row(
                    service, model, row,
                    thread_id=model.get("threadId"),
                    msg_id=model.get("messageId"),
                )
                if result.get("skipped"):
                    print(f"[pipeline] reply skipped: {result['skipped']}")
                else:
                    print(f"[pipeline] rejection reply sent to {result.get('sent_to')} (id={result.get('id')})")
                    row["replySent"] = "true"
            except Exception as e:
                print(f"[pipeline] reply failed for {email_id}: {e}")
                row["replySent"] = "error"

    if not dry_run:
        db.log_run_end(
            run_id,
            "needs_human" if needs_human else "success",
            error=needs_human_reason if needs_human else "",
            model=tokens.get("model", ""),
        )
    return row
