# =============================================================================
# FILE HEADER
# file    : msme/receive/gallery.py
# role    : Receive — local logo gallery matcher (N-1) + N-2 promotion helpers
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : when an article has no usable image, match its brand against the local gallery
#           with the hybrid priority ladder (domain → subject → display name → file+body →
#           lead+body repeat → fuzzy → ambiguity) and return the logo bytes. Also N-2 helpers:
#           promote_if_safe (auto-active decision C), supersede_brand, gallery_name, write_index.
# pages   : n/a (backs the pipeline `gallery` stage)
# calls   : config, paths, stdlib (json, difflib, re)
# called  : msme/receive/pipeline.py, msme/receive/library_update.py, tools/gallery_admin.py
# amend   : no AI, no network; a miss is safe (ask email), a false hit publishes the wrong logo.
#           Test: python3 -m unittest tests.test_gallery tests.test_library_update -v
# =============================================================================
"""Local logo gallery matcher (N-1).

The gallery is a curated folder + ``index.json``. Matching follows the hybrid
priority ladder in ``docs/new-rules/N-1-logo-gallery.md`` §6:

1. sender domain in ``domains``
2. exact alias in the subject/headline
3. exact alias in the sender display name
4. exact alias in an attachment filename **and** the body
5. exact alias in the first ``GALLERY_BODY_LEAD_CHARS`` chars **and** >= 2x in the body
6. fuzzy >= ``GALLERY_FUZZY_MIN`` in the subject/display name
7. ambiguity: two brands within 10 points -> miss

Example:
    index = gallery.load_index()
    result = gallery.match(email, index)
    # -> {"status": "hit", "detail": {"brand": "BPMB", "tier": 2, ...}}
    picked = gallery.pick(result["detail"])
    # -> {"name": "BPMB_11-November-2026_MALAYSIA-SME.png", "bytes": b"..."}
"""
import difflib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from msme import config, paths

_TIER_SCORE = {1: 100, 2: 95, 3: 90, 4: 85, 5: 80}
_AMBIGUITY_WINDOW = 10


def _norm(value):
    """Lowercase, turn punctuation into spaces, collapse whitespace."""
    text = str(value or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _whole(alias, text):
    """Whole-word/phrase match on normalised text; alias >= 3 characters."""
    a = _norm(alias)
    if not a or len(a.replace(" ", "")) < 3:
        return False
    t = _norm(text)
    return f" {a} " in f" {t} "


def _count(alias, text):
    """How many whole-word/phrase occurrences of `alias` are in `text`."""
    a = _norm(alias)
    if not a:
        return 0
    return f" {_norm(text)} ".count(f" {a} ")


def _domain(email):
    email = str(email or "").strip().lower()
    return email.rsplit("@", 1)[-1] if "@" in email else ""


def _domain_matches(domain, registered):
    """`mail.bpmb.com.my` matches `bpmb.com.my`; an agency domain never maps."""
    domain = str(domain or "").lower().strip()
    registered = str(registered or "").lower().strip()
    if not domain or not registered:
        return False
    return domain == registered or domain.endswith("." + registered)


def is_agency(value):
    """True when the sender domain (or a full email) is a known PR agency/newswire."""
    domain = _domain(value) or str(value or "").lower().strip()
    return any(_domain_matches(domain, d) for d in config.GALLERY_AGENCY_DOMAINS)


def _fuzzy(alias, text):
    """Best ratio between `alias` and a 1-3 token window of `text`.

    Spaces are removed before comparing so "May Bank" vs "Maybank" scores 1.0.
    Returns (ratio, matched_text).
    """
    a = _norm(alias).replace(" ", "")
    if len(a) < 3:
        return 0.0, ""
    tokens = _norm(text).split()
    best_ratio, best_text = 0.0, ""
    for i in range(len(tokens)):
        for span in range(1, 4):
            window = tokens[i:i + span]
            if not window:
                continue
            joined = "".join(window)
            ratio = difflib.SequenceMatcher(None, a, joined).ratio()
            if ratio > best_ratio:
                best_ratio, best_text = ratio, " ".join(window)
    return best_ratio, best_text


def load_index(path=None):
    """Read the gallery index; a list of entries (raises on a missing/corrupt file)."""
    index_path = Path(path or config.GALLERY_INDEX)
    data = json.loads(index_path.read_text(encoding="utf-8"))
    images = data.get("images") if isinstance(data, dict) else data
    if not isinstance(images, list):
        raise ValueError("gallery index has no images list")
    return [e for e in images if isinstance(e, dict)]


def active_entries(index):
    """Only `active` logo entries are usable by N-1."""
    out = []
    for entry in index or []:
        status = str(entry.get("status") or "active").lower()
        kind = str(entry.get("type") or "logo").lower()
        if status == "active" and kind == "logo":
            out.append(entry)
    return out


def _candidate(entry, tier, field, alias, score, matched_text=""):
    return {
        "brand": str(entry.get("brand") or entry.get("id") or ""),
        "entry_id": str(entry.get("id") or ""),
        "tier": tier,
        "field": field,
        "alias": alias,
        "matched_text": matched_text,
        "score": int(score),
        "file": str(entry.get("file") or ""),
        "updated": str(entry.get("updated") or ""),
    }


def _better(current, candidate):
    """Keep the highest score; on a tie keep the newest entry."""
    if current is None:
        return candidate
    if candidate["score"] > current["score"]:
        return candidate
    if candidate["score"] == current["score"] and candidate["updated"] > current["updated"]:
        return candidate
    return current


def match(email, index):
    """Match one email against the gallery; returns {status, detail}.

    `email` keys: subject, from_name, from_email, filenames (list), body.
    """
    entries = active_entries(index)
    domain = _domain(email.get("from_email"))
    subject = email.get("subject") or ""
    from_name = email.get("from_name") or ""
    body = email.get("body") or ""
    filenames = [str(f) for f in (email.get("filenames") or []) if f]

    by_brand = {}
    for entry in entries:
        brand = str(entry.get("brand") or entry.get("id") or "")
        aliases = [str(a) for a in (entry.get("aliases") or []) if str(a).strip()]
        best = None

        # 1) sender domain
        for registered in entry.get("domains") or []:
            if _domain_matches(domain, registered):
                best = _candidate(entry, 1, "sender_domain", str(registered), 100)
                break

        # 2) exact alias in the subject
        if best is None:
            for alias in aliases:
                if _whole(alias, subject):
                    best = _candidate(entry, 2, "subject", alias, 95)
                    break

        # 3) exact alias in the sender display name
        if best is None:
            for alias in aliases:
                if _whole(alias, from_name):
                    best = _candidate(entry, 3, "sender_name", alias, 90)
                    break

        # 4) exact alias in a filename AND in the body
        if best is None:
            for alias in aliases:
                if any(_whole(alias, f) for f in filenames) and _whole(alias, body):
                    best = _candidate(entry, 4, "filename+body", alias, 85)
                    break

        # 5) exact alias in the first GALLERY_BODY_LEAD_CHARS chars AND >= 2x in
        #    the body (any sender). The lead carries the brand in the headline or
        #    first paragraph, which is a stronger signal than the old agency gate;
        #    that gate excluded forwarded editor emails where the brand appears
        #    only in the release text.
        if best is None:
            lead = body[:int(config.GALLERY_BODY_LEAD_CHARS)]
            for alias in aliases:
                if _whole(alias, lead) and _count(alias, body) >= 2:
                    best = _candidate(entry, 5, "body", alias, 80)
                    break

        # 6) fuzzy in the subject/display name (single top only, checked later)
        if best is None:
            for alias in aliases:
                ratio, matched = _fuzzy(alias, subject)
                ratio_name, matched_name = _fuzzy(alias, from_name)
                if ratio_name > ratio:
                    ratio, matched = ratio_name, matched_name
                if ratio >= float(config.GALLERY_FUZZY_MIN):
                    best = _candidate(entry, 6, "fuzzy", alias,
                                      round(ratio * 100), matched)
                    break

        if best is not None:
            by_brand[brand] = _better(by_brand.get(brand), best)

    candidates = sorted(by_brand.values(), key=lambda c: (-c["score"], c["brand"]))
    if not candidates:
        return {"status": "miss", "detail": {"reason": "no alias matched",
                                             "best_score": 0, "candidates": []}}

    top = candidates[0]
    if len(candidates) > 1 and (top["score"] - candidates[1]["score"]) <= _AMBIGUITY_WINDOW:
        return {"status": "miss", "detail": {
            "reason": "ambiguous", "tier": 7,
            "brands": [top["brand"], candidates[1]["brand"]],
            "scores": [top["score"], candidates[1]["score"]],
        }}

    return {"status": "hit", "detail": top}


def _safe_path(entry, gallery_dir=None):
    """Resolve `entry["file"]` inside the gallery; reject `..` and absolute paths."""
    base = Path(gallery_dir or config.GALLERY_DIR).resolve()
    raw = str(entry.get("file") or "").strip()
    if not raw:
        raise ValueError("gallery entry has no file")
    candidate = (base / raw).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        raise ValueError("gallery file escapes the gallery directory")
    return candidate


def pick(entry, gallery_dir=None):
    """Read the matched gallery file; returns {name, bytes, path}."""
    path = _safe_path(entry, gallery_dir)
    if not path.exists():
        raise FileNotFoundError("gallery file not found: %s" % path.name)
    if not path.is_file():
        raise ValueError("gallery entry is not a file")
    size = path.stat().st_size
    if size <= 0:
        raise ValueError("gallery file is empty")
    if size > config.GALLERY_MAX_FILE_BYTES:
        raise ValueError("gallery file is too large (%d bytes)" % size)
    return {"name": path.name, "bytes": path.read_bytes(), "path": str(path)}


# --- N-2 helpers (docs/new-rules/N-2-library-update.md) ----------------------

def write_index(data, path=None):
    """Persist the index dict; sets ``version`` and ``updated``."""
    index_path = Path(path or config.GALLERY_INDEX)
    data["version"] = data.get("version", 1)
    data["updated"] = datetime.now(timezone.utc).date().isoformat()
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")


def supersede_brand(images, brand, kind="logo"):
    """Mark every active entry of ``brand``/``kind`` as superseded (keep history)."""
    changed = False
    for entry in images or []:
        if (str(entry.get("brand") or "").lower() == str(brand).lower()
                and str(entry.get("type") or "logo").lower() == kind
                and str(entry.get("status") or "active").lower() == "active"):
            entry["status"] = "superseded"
            changed = True
    return changed


def gallery_name(brand, date_str=None, ext="png"):
    """AG-05 filename: ``Brand_07-November-2026_MALAYSIA-SME.png``."""
    if not date_str:
        date_str = datetime.now(timezone.utc).strftime("%d-%B-%Y")
    safe = re.sub(r"[^A-Za-z0-9-]+", "-", str(brand or "")).strip("-") or "logo"
    ext = str(ext or "png").lstrip(".")
    return f"{safe}_{date_str}_MALAYSIA-SME.{ext}"


def promote_if_safe(candidate, data):
    """Promote a captured logo into the active index (N-2 decision C).

    ``candidate`` is a fully-classified file from the update store::

        {"brand", "aliases", "domains", "filename", "bytes",
         "kind", "width", "height", "confidence"}

    Auto-active only when all four conditions hold; otherwise returns a pending
    result with a ``reason``. Never raises: a bad file is a pending, not an error.
    """
    brand = str(candidate.get("brand") or "").strip()
    raw = candidate.get("bytes") or b""
    filename = str(candidate.get("filename") or "").strip()
    name_hint = filename.lower()
    w = int(candidate.get("width") or 0)
    h = int(candidate.get("height") or 0)
    vector = raw.lstrip().startswith(b"<svg") or name_hint.endswith(".svg")

    # 1) the file is a logo (name hint not building/facade) and >= min dim or vector
    is_logo = ("logo" in name_hint or str(candidate.get("kind") or "") == "logo") \
        and not ("building" in name_hint or "facade" in name_hint)
    if not is_logo or (not vector and max(w, h) < config.BODY_LOGO_MIN_DIM):
        return {"promoted": False, "reason": "not-a-logo"}

    # 2) brand confidence high
    if str(candidate.get("confidence") or "") != "high":
        return {"promoted": False, "reason": "low-brand-confidence"}

    # 3) the brand already has an active logo
    images = data.setdefault("images", [])
    if not any(str(e.get("brand") or "").lower() == brand.lower()
               and str(e.get("type") or "logo").lower() == "logo"
               and str(e.get("status") or "active").lower() == "active"
               for e in images):
        return {"promoted": False, "reason": "new-brand"}

    # 4) readable + within the size cap
    if not raw or len(raw) > config.GALLERY_MAX_FILE_BYTES:
        return {"promoted": False, "reason": "unreadable"}

    ext = "svg" if vector else ("png" if raw[:8] == b"\x89PNG\r\n\x1a\n" else "jpg")
    dest_name = gallery_name(brand, ext=ext)
    dest = Path(config.GALLERY_DIR) / dest_name
    dest.write_bytes(raw)
    supersede_brand(images, brand, "logo")
    updated = datetime.now(timezone.utc).date().isoformat()
    entry = {
        "id": f"{re.sub(r'[^a-z0-9-]+', '-', brand.lower()).strip('-')}-{updated}",
        "brand": brand,
        "aliases": [str(a) for a in (candidate.get("aliases") or [brand]) if str(a).strip()],
        "domains": [str(d) for d in (candidate.get("domains") or []) if str(d).strip()],
        "type": "logo",
        "file": dest_name,
        "updated": updated,
        "status": "active",
        "source": "sender",
    }
    images.append(entry)
    return {"promoted": True, "reason": "auto-active", "brand": brand, "file": dest_name}
