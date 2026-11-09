# =============================================================================
# FILE HEADER
# file    : msme/receive/library_update.py
# role    : Receive — N-2 "library update" intake (logo/building-photo only)
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : when an email distributes only a logo/building photo (no article),
#           classify it as a gallery update, store the assets, and skip
#           verify/filter/reply so it is never shown as "no article".
# pages   : n/a (backs the pipeline `library_update` stage)
# calls   : config, gallery, extract
# called  : msme/receive/pipeline.py
# amend   : no AI, no network; a false hit stores assets but never publishes
#           (N-1 matches only `active` entries and promotion is conservative).
#           Test: python3 -m unittest tests.test_library_update -v
# =============================================================================
"""N-2 library-update detector + store (docs/new-rules/N-2-library-update.md).

Detection runs after extract (the article text is known) and before verify. A
hit needs **all three**:

1. no article text (< ``LIBRARY_UPDATE_MIN_CHARS``) and no candidate that long,
2. >= 2 positive signals (phrase / image-only attachments / decide empty+images),
3. zero negative signals ("for immediate release", report/contribute markers).

On a hit the assets are stored under ``GALLERY_UPDATES_DIR`` and each logo file
is promoted auto-active only under N-2 decision C; everything else stays pending.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from msme import config
from msme.receive import extract, gallery

_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg")
_DOC_EXTS = (".pdf", ".docx", ".doc")


def _slug(value):
    return re.sub(r"[^A-Za-z0-9-]+", "-", str(value or "")).strip("-").lower() or "update"


def _is_image(name):
    return str(name or "").lower().endswith(_IMAGE_EXTS)


def _is_doc(name):
    return str(name or "").lower().endswith(_DOC_EXTS)


def _load_index_data():
    """Read the gallery index as a dict ({"images": [...]}); never raises."""
    try:
        data = json.loads(Path(config.GALLERY_INDEX).read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("images"), list):
            return data
        return {"version": 1, "updated": "", "images": data if isinstance(data, list) else []}
    except Exception:
        return {"version": 1, "updated": "", "images": []}


def classify(ctx):
    """Return a library-update hit dict, or None to run the normal path.

    ``ctx`` keys: subject, raw_body, body_text (extracted article), candidates
    (list of {text}), decision (dict), attachments (list of {filename}), files
    (dict name->bytes), needs_human (bool), media (dict), from_email, from_name,
    message_id, date.
    """
    article_text = ctx.get("body_text") or ""
    candidates = ctx.get("candidates") or []
    raw = (ctx.get("raw_body") or "").lower()
    subject = (ctx.get("subject") or "").lower()
    hay = subject + "\n" + raw
    decision = ctx.get("decision") or {}
    attachments = ctx.get("attachments") or []
    files = ctx.get("files") or {}
    media = ctx.get("media") or {}
    needs_human = bool(ctx.get("needs_human"))

    # 1) no article text (extracted body and every candidate below the floor)
    if len(article_text) >= config.LIBRARY_UPDATE_MIN_CHARS:
        return None
    if any(len(c.get("text") or "") >= config.LIBRARY_UPDATE_MIN_CHARS for c in candidates):
        return None

    # a needs_human with no collected asset is a real "no article" fetch failure
    has_asset = bool(files) or bool(media.get("hasPic")) or bool(media.get("hasLogo")) \
        or bool(media.get("docLogo")) or bool(media.get("docPhoto"))
    if needs_human and not has_asset:
        return None

    # 3) zero negative signals
    for neg in config.LIBRARY_UPDATE_NEGATIVE:
        if neg in hay:
            return None

    # 2) at least two positive signals
    positives = 0
    if any(p in hay for p in config.LIBRARY_UPDATE_PHRASES):
        positives += 1
    names = [str(a.get("filename") or "") for a in attachments]
    if names and all(_is_image(n) for n in names) and not any(_is_doc(n) for n in names):
        positives += 1
    if not decision.get("chosenFileName") and decision.get("imagesAvailable"):
        positives += 1
    if positives < 2:
        return None

    # brand + confidence: sender domain match (tier 1) or exact subject alias
    brand, confidence, aliases, domains = "", "low", [], []
    from_email = ctx.get("from_email") or ""
    from_name = ctx.get("from_name") or ""
    try:
        index = gallery.load_index()
    except Exception:
        index = []
    for e in index:
        for d in (e.get("domains") or []):
            if gallery._domain_matches(from_email, d):
                brand = str(e.get("brand") or "")
                aliases = list(e.get("aliases") or [])
                domains = list(e.get("domains") or [])
                confidence = "high"
                break
        if brand:
            break
    if not brand:
        for e in index:
            for a in (e.get("aliases") or []):
                if gallery._whole(a, subject) and gallery._count(a, raw) >= 1:
                    brand = str(e.get("brand") or "")
                    aliases = list(e.get("aliases") or [])
                    domains = list(e.get("domains") or [])
                    confidence = "high"
                    break
            if brand:
                break

    return {
        "brand": brand, "confidence": confidence, "aliases": aliases, "domains": domains,
        "subject": ctx.get("subject") or "", "from_email": from_email,
        "from_name": from_name, "message_id": ctx.get("message_id") or "",
        "date": ctx.get("date") or "", "files": files, "attachments": attachments,
    }


def _classify_file(name, data):
    """Return (kind, width, height, ext) for one captured file."""
    name_l = (name or "").lower()
    if name_l.endswith(".svg") or (data or b"").lstrip().startswith(b"<svg"):
        return "logo", 0, 0, "svg"  # vector: scalable, no pixel floor
    w, h = extract._image_dims(data)
    kind = extract._kind_from_bytes(data)
    if "logo" in name_l or kind == "logo":
        kind = "logo"
    elif kind == "photo":
        kind = "photo"
    else:
        kind = "unknown"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        ext = "png"
    elif data[:2] == b"\xff\xd8":
        ext = "jpg"
    elif data[:2] == b"GI":
        ext = "gif"
    else:
        ext = "img"
    return kind, w, h, ext


def store_update(hit, dry_run=False):
    """Write the update store folder + update.json/images/originals and run promotion.

    Returns a dict with the folder, per-file records and promotion tallies.
    """
    subject = hit.get("subject") or "library-update"
    brand = hit.get("brand") or ""
    capture = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    folder_name = f"{capture}_{_slug(brand or subject[:40])}"
    base = Path(config.GALLERY_UPDATES_DIR) / folder_name
    images_dir = base / "images"
    originals_dir = base / "originals"

    files = hit.get("files") or {}
    idx = _load_index_data()
    if not dry_run:
        images_dir.mkdir(parents=True, exist_ok=True)
        originals_dir.mkdir(parents=True, exist_ok=True)

    records, promoted, pending = [], 0, 0
    for name, data in files.items():
        kind, w, h, ext = _classify_file(name, data)
        sha1 = hashlib.sha1(data).hexdigest() if data else ""
        rec = {"name": name, "sha1": sha1, "bytes": len(data or b""),
               "width": w, "height": h, "kind": kind}
        cand = {"brand": brand, "aliases": hit.get("aliases") or [],
                "domains": hit.get("domains") or [], "filename": name, "bytes": data,
                "kind": kind, "width": w, "height": h,
                "confidence": hit.get("confidence") or "low"}
        result = gallery.promote_if_safe(cand, idx)
        rec["promoted"] = bool(result.get("promoted"))
        rec["promotionBlockedReason"] = "" if rec["promoted"] else result.get("reason", "")
        if rec["promoted"]:
            promoted += 1
        else:
            pending += 1
        if not dry_run and data:
            if _is_image(name):
                (images_dir / name).write_bytes(data)
            else:
                (originals_dir / name).write_bytes(data)
        records.append(rec)

    meta = {
        "id": folder_name, "brand": brand, "aliases": hit.get("aliases") or [],
        "domains": hit.get("domains") or [], "fromEmail": hit.get("from_email") or "",
        "fromName": hit.get("from_name") or "", "subject": subject,
        "messageId": hit.get("message_id") or "",
        "date": (hit.get("date") or "")[:10], "captured": capture,
        "status": "active" if promoted else "pending", "files": records, "notes": "",
    }
    if not dry_run:
        (base / "update.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if promoted:
            gallery.write_index(idx)

    return {"folder": folder_name, "update_id": folder_name, "files": records,
            "promoted": promoted, "pending": pending}
