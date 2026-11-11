# =============================================================================
# FILE HEADER
# file    : msme/receive/media_index.py
# role    : Receive — N-3/N-4 media index (images/logos per email)
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : turn the pipeline's collected media groups (email attachments, doc embeds,
#           body/asset/drive/web images, gallery fallback) into one row per image for
#           the email_media table, with dims/kind/source/usable/chosen.
# pages   : n/a (the editor/repurpose read it via db.list_email_media)
# calls   : config, extract (dims + kind)
# called  : msme/receive/pipeline.py
# amend   : no AI, no network; records where an image came from so repurpose can see
#           the gallery fallback (source=gallery, chosen=1). Test: tests.test_email_media
# =============================================================================
"""Build the email_media rows from the pipeline's media groups.

Example:
    rows = media_index.build_rows([
        (files, "email_attachment", None),
        (embed_images, "doc_embed", None),
        (body_pics, "body", "photo"),
        (gallery_logos, "gallery", "logo"),
    ])
    # -> [{"name": ..., "kind": "photo"/"logo", "source": ...,
    #      "usable": True/False, "chosen": True only for the gallery fallback, ...}]
"""
import hashlib
from pathlib import Path

from msme import config
from msme.receive import extract


def _is_vector(name, data):
    return (str(name or "").lower().endswith(".svg")
            or (data or b"").lstrip().startswith(b"<svg"))


def _resolve_path(archive_dir, name):
    """The archived file path for `name` under `archive_dir` (or the bare name)."""
    if not archive_dir:
        return str(name)
    base = Path(archive_dir)
    for sub in ("images", "originals", ""):
        d = base / sub if sub else base
        cand = d / name
        if cand.is_file():
            return str(cand)
    # archive.py never overwrites: a collision gets a `_1` suffix.
    stem, dot, ext = str(name).rpartition(".")
    for sub in ("images", "originals"):
        d = base / sub
        if d.is_dir():
            hits = sorted(d.glob(f"{stem}*.{ext}" if dot else f"{stem}*"))
            if hits:
                return str(hits[0])
    return str(name)


def build_rows(groups, archive_dir=None):
    """groups: list of (data_map, source, kind_hint). Returns a list of row dicts.

    `archive_dir` (the email's archive folder) is used to store the real file path,
    so the repurpose export can copy the exact image instead of guessing a folder.
    """
    rows = []
    for data_map, source, kind_hint in groups or []:
        for name, data in (data_map or {}).items():
            if not data:
                continue
            w, h = extract._image_dims(data)
            vector = _is_vector(name, data)
            if not vector and (w <= 0 or h <= 0):
                continue  # not an image (a PDF/DOCX/other attachment) — not media
            kind = kind_hint or extract._kind_from_bytes(data)
            usable = bool(vector or max(w, h) >= config.BODY_LOGO_MIN_DIM)
            chosen = (source == "gallery")  # N-1 fallback is the intended image
            rows.append({
                "name": name,
                "kind": kind or "unknown",
                "source": source,
                "role": "featured" if chosen else ("logo" if kind == "logo" else "candidate"),
                "path": _resolve_path(archive_dir, name),
                "width": w,
                "height": h,
                "bytes": len(data),
                "sha1": hashlib.sha1(data).hexdigest(),
                "usable": usable,
                "chosen": chosen,
            })
    return rows
