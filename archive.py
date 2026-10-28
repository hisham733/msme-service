# =============================================================================
# FILE HEADER
# file    : archive.py
# role    : Receive — local article archive
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : create emails/<Subject>/ with the article .md, images/ and originals/.
# pages   : n/a (the filter pages read the result)
# calls   : config.LOCAL_ARCHIVE_DIR, os/re
# called  : pipeline.py (lazy import)
# amend   : folder and file naming are looked up by filter_service archive routes — never change silently.
#           Test: run one email and confirm the folder appears under emails/
# =============================================================================
"""Archive: save article + images + originals to the LOCAL PC filesystem.

A folder is created per email under config.LOCAL_ARCHIVE_DIR, named after the
subject. Inside: article.md, images/, and originals/ (original PDF/DOCX).
No Google Drive upload.

Example on-disk layout:
    emails/MALAYSIAS-EXPORTS-RISE-31.4-PERCENT/
        MALAYSIAS-EXPORTS-RISE-31.4-PERCENT.md   <- the article
        images/hero.jpg
        originals/EN_RELEASE.docx
"""
import os
import re

import config


def _sanitize(name):
    """Make a filesystem-safe name (keep letters/numbers/space/dash/dot)."""
    s = re.sub(r"[^\w\s.-]", "", name or "").strip()
    s = re.sub(r"\s+", " ", s).strip()
    s = s[:90]
    return s or "article"


def _clean_subject(subject):
    """Folder name = subject minus Fwd/Re/[PRESS RELEASE] prefixes.

    Example:
        _clean_subject("Fwd: [PRESS RELEASE] Company Launches Product")
        -> "Company Launches Product"
    """
    s = re.sub(r"^(fwd|fw|re|ref):\s*", "", subject or "", flags=re.IGNORECASE).strip()
    s = re.sub(r"^[\[\(\s]*(for immediate release|press release|news release|media release)[\]:\)\s]*",
               "", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"^\[[^\]]*\]\s*", "", s).strip()
    return _sanitize(s)


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def _safe_name(name):
    """Filesystem-safe filename with a hard length cap (avoids Errno 36)."""
    base = os.path.basename(name or "file")
    stem, ext = os.path.splitext(base)
    stem = re.sub(r"[^\w\s.-]", "", stem).strip() or "file"
    stem = re.sub(r"\s+", " ", stem).strip()
    if len(stem) > 100:
        stem = stem[:100]
    if len(ext) > 10:
        ext = ext[:10]
    return stem + ext


def archive_email(model, article_text, article_name, email_images, email_originals=None,
                  drive_images=None, drive_originals=None, drive=None, run_id=None):
    """Save article + images + originals to the local PC filesystem.

    Args:
        model:          the normalized email model (subject/date used for naming)
        article_text:   the article markdown/text to save as article.md
        article_name:   base name for the article file (e.g. "Company-Launches")
        email_images:   dict {filename: bytes} (email attachments)
        email_originals: dict {filename: bytes} (extra originals, e.g. Box docs)
        drive_images:   list of {name, id} to download from Drive into images/
        drive_originals: list of {name, id} to download from Drive into originals/
        drive:          Drive service needed to download drive_images/originals

    Returns:
        (folder_path, uploaded_info) where uploaded_info = {
            "article": "X.md", "images": n, "originals": n, "files": [...], "path": ...}
    """
    subject = model.get("subject", "")
    date = (model.get("date", "") or "")[:10]
    folder_name = _clean_subject(subject) or "article"

    root = config.LOCAL_ARCHIVE_DIR
    _ensure_dir(root)

    # avoid clobbering: if folder exists, append a numeric suffix
    folder_path = os.path.join(root, folder_name)
    n = 1
    while os.path.exists(folder_path):
        folder_path = os.path.join(root, f"{folder_name}_{n}")
        n += 1
    _ensure_dir(folder_path)
    _ensure_dir(os.path.join(folder_path, "images"))
    _ensure_dir(os.path.join(folder_path, "originals"))

    uploaded = {"article": None, "images": 0, "originals": 0, "files": [], "path": folder_path}

    # article .md (markdown file with the verbatim release text)
    if article_text and article_name:
        file_name = _sanitize(article_name) + ".md"
        with open(os.path.join(folder_path, file_name), "w", encoding="utf-8") as f:
            f.write(article_text)
        uploaded["article"] = file_name
        uploaded["files"].append(file_name)

    def _save(name, data, sub):
        """Write bytes to folder_path/[sub/]name and count it.

        Never overwrites: an existing name gets a numeric suffix (e.g. an image
        with the same filename coming from both the email and the Drive kit).
        """
        name = _safe_name(name)
        dest = os.path.join(folder_path, sub, name) if sub else os.path.join(folder_path, name)
        _ensure_dir(os.path.dirname(dest))
        if os.path.exists(dest):
            stem, ext = os.path.splitext(dest)
            n = 1
            while os.path.exists(dest):
                dest = f"{stem}_{n}{ext}"
                n += 1
        with open(dest, "wb") as f:
            f.write(data)
        uploaded["files"].append(os.path.basename(dest))

    # email attachments: images -> images/ , pdf/docx -> originals/ , else -> root
    for name, data in (email_images or {}).items():
        try:
            low = (name or "").lower()
            if low.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".heic", ".tiff")):
                sub = "images"; uploaded["images"] += 1
            elif low.endswith((".pdf", ".docx", ".doc", ".txt", ".md")):
                sub = "originals"; uploaded["originals"] += 1
            else:
                sub = ""
            _save(name, data, sub)
        except Exception as e:
            print(f"[archive] failed to save {name}: {e}")

    # extra originals passed as bytes (e.g. docs downloaded from a Box press kit)
    for name, data in (email_originals or {}).items():
        try:
            _save(name, data, "originals")
            uploaded["originals"] += 1
        except Exception as e:
            print(f"[archive] failed to save original {name}: {e}")

    # drive media kit images (download from Drive into images/)
    if drive_images and drive:
        from drive_fetch import _download
        for img in drive_images:
            try:
                data = _download(drive, img.get("id"))
                if data:
                    _save(img.get("name") or "image", data, "images")
                    uploaded["images"] += 1
            except Exception as e:
                print(f"[archive] drive image copy failed {img.get('name')}: {e}")

    # drive media kit originals (PDF/DOCX downloaded into originals/)
    if drive_originals and drive:
        from drive_fetch import _download
        for doc in drive_originals:
            try:
                data = _download(drive, doc.get("id"))
                if data:
                    _save(doc.get("name") or "doc", data, "originals")
                    uploaded["originals"] += 1
            except Exception as e:
                print(f"[archive] drive original copy failed {doc.get('name')}: {e}")

    return folder_path, uploaded