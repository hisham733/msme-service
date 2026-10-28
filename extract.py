# =============================================================================
# FILE HEADER
# file    : extract.py
# role    : Receive · AI step 2 + deterministic text/image helpers
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : select the article from the D24 candidate pool and return it verbatim + metadata; extract
#           PDF/DOCX text; classify embedded logo/image presence, including VECTOR logos drawn in a PDF
#           page header (no raster image XObject). D25 caps text at 30 pages / 150k chars and images at 10 per doc.
# pages   : n/a
# calls   : llm.LLMClient, config, prompts/extract_prompt.txt; zipfile/pypdf/docx
# called  : pipeline.py; drive_fetch (classify_doc_images, extract_text_from_bytes)
# amend   : the deterministic detectors feed the weekly image counts (todo/T-008) — re-run those counts on change.
#           Test: python3 -m compileall -q extract.py + one email's logo_scan stage
# =============================================================================
"""Extract & Clean PR — AI step #2 + deterministic text/logo helpers.

The AI is TEXT-ONLY: it never sees an image. Logo/photo flags therefore come
from the deterministic classifiers below (`classify_doc_images`), which read
raster XObjects/images AND vector artwork in a PDF `/Header` artifact.

The AI reads the email body plus the labelled D24 candidate pool (attachments, Drive, OneDrive,
Box, web) and
returns the VERBATIM article + metadata. This module also has the deterministic
PDF/DOCX text extraction and embedded-logo detection (no AI needed).

Example extract output:
    {
      "bodyText": "NOTE TO EDITORS:\nFOR IMMEDIATE RELEASE...",
      "articleSource": "attachment_pdf",
      "hasLogoInArticle": false, "hasImageInArticle": false,
      "needsHumanFetch": false, "confidence": 0.96,
      "evidence": "The email is a forwarded press release; the PDF is the article."
    }
"""
import io
import re
import zipfile

import config
from llm import LLMClient

# Used when scanning text for banner lines that should NOT be treated as the
# headline (e.g. "FOR IMMEDIATE RELEASE", "NOTE TO EDITORS", "MEDIA CONTACT").
BANNER_RE = re.compile(
    r"^[_*]*\s*((for\s+)?immediate\s+)?(press\s+|news\s+|media\s+)?release([\s:]*|\s+immediate\s*[:]?)|"
    r"note[s]? to editors?|editor['’]?s? note|media contact|for (more|further) information|contact[:\s]",
    re.IGNORECASE,
)


def _cap_text(text: str, max_chars: int) -> str:
    """Trim document text to the configured budget, with a visible marker."""
    text = text or ""
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars] + (
        f"\n\n[... truncated to the first {max_chars} characters ...]"
    )


def _extract_pdf_text(reader):
    """Read at most PDF_TEXT_MAX_PAGES pages / DOC_TEXT_MAX_CHARS characters.

    Returns (text, truncated, pages_read). Split out so the limit can be tested
    with a fake reader (no pypdf dependency).
    """
    max_pages = max(1, int(getattr(config, "PDF_TEXT_MAX_PAGES", 30) or 30))
    max_chars = max(1000, int(getattr(config, "DOC_TEXT_MAX_CHARS", 150000) or 150000))
    parts = []
    chars = 0
    pages = 0
    truncated = False
    for page in reader.pages:
        if pages >= max_pages or chars >= max_chars:
            truncated = True
            break
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        pages += 1
        if t.strip():
            parts.append(t)
            chars += len(t)
    return "\n\n".join(parts), truncated, pages


def extract_text_from_bytes(data: bytes, filename: str) -> str:
    """Extract plain text from PDF or DOCX bytes. Returns '' on failure.

    D25: PDFs are read only up to PDF_TEXT_MAX_PAGES / DOC_TEXT_MAX_CHARS; a
    906-page report must not block the worker for 15 minutes. A truncation
    marker is appended so the AI knows the text is partial.

    Example:
        extract_text_from_bytes(pdf_bytes, "release.pdf")
        -> "KUALA LUMPUR, 22 Sept 2026 - Company launches new product..."
    """
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        text, truncated, pages = _extract_pdf_text(reader)
        if truncated:
            text += (
                f"\n\n[... truncated to the first {pages} pages / "
                f"{config.DOC_TEXT_MAX_CHARS} characters ...]"
            )
        return text
    elif name.endswith((".docx", ".doc")):
        try:
            import docx

            d = docx.Document(io.BytesIO(data))
            return _cap_text("\n".join(p.text for p in d.paragraphs),
                             config.DOC_TEXT_MAX_CHARS)
        except Exception:
            # fallback: read word/document.xml directly from the zip
            return _cap_text(_docx_text_raw(data), config.DOC_TEXT_MAX_CHARS)
    return ""


def _docx_text_raw(data: bytes) -> str:
    """Fallback DOCX text: unzip word/document.xml and strip XML tags."""
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        xml = z.read("word/document.xml").decode("utf-8", "replace")
        return re.sub(r"<[^>]+>", " ", xml)
    except Exception:
        return ""


def doc_has_embedded_image(data: bytes, filename: str) -> bool:
    """Detect ANY embedded image inside a PDF or DOCX (rough check).

    - PDF  : looks for `/Subtype /Image` (an image XObject).
    - DOCX : looks for a `word/media/*` entry.

    Prefer `classify_doc_images()` when you need logo-vs-photo; this is kept
    for cheap "does it contain any image at all" checks (e.g. Drive walk).
    """
    name = (filename or "").lower()
    try:
        if name.endswith(".pdf"):
            return b"/Subtype /Image" in data or b"/Subtype/Image" in data
        else:
            try:
                z = zipfile.ZipFile(io.BytesIO(data))
                names = z.namelist()
                return any(n.startswith("word/media/") for n in names)
            except Exception:
                return b"word/media/" in data
    except Exception:
        return False


# --- Deterministic logo-vs-photo classification --------------------------------
# Thresholds (in pixels) used by classify_doc_images():
#   small image (both dims <= LOGO_MAX)          -> logo
#   banner image (min dim <= BANNER_MIN)         -> logo (wide header strip)
#   large image (any dim >= PHOTO_MIN)           -> photo
#   repeated on every page + medium size          -> header logo
LOGO_MAX = 300
BANNER_MIN = 150
PHOTO_MIN = 500


def _image_dims(raw: bytes):
    """Read (width, height) from PNG/JPEG/GIF/BMP/WebP bytes.

    Returns (0, 0) if the format is not recognized or headers are malformed.
    """
    try:
        if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP" and len(raw) >= 30:
            chunk = raw[12:16]
            if chunk == b"VP8X":
                w = int.from_bytes(raw[24:27], "little") + 1
                h = int.from_bytes(raw[27:30], "little") + 1
                return (w, h)
            if chunk == b"VP8 ":
                w = int.from_bytes(raw[26:28], "little") & 0x3FFF
                h = int.from_bytes(raw[28:30], "little") & 0x3FFF
                return (w, h)
            if chunk == b"VP8L":
                bits = int.from_bytes(raw[21:25], "little")
                w = (bits & 0x3FFF) + 1
                h = ((bits >> 14) & 0x3FFF) + 1
                return (w, h)
        if raw[:8] == b"\x89PNG\r\n\x1a\n" and len(raw) >= 24:
            # PNG: IHDR width/height are big-endian at offset 16/20
            import struct
            return struct.unpack(">II", raw[16:24])
        if raw[:2] == b"\xff\xd8":
            # JPEG: scan markers for a SOF0/SOF1/SOF2 segment (contains HxW)
            i = 2
            while i < len(raw) - 9:
                if raw[i] != 0xFF:
                    i += 1
                    continue
                marker = raw[i + 1]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h = int.from_bytes(raw[i + 5:i + 7], "big")
                    w = int.from_bytes(raw[i + 7:i + 9], "big")
                    return (w, h)
                seg_len = int.from_bytes(raw[i + 2:i + 4], "big")
                i += 2 + seg_len
        if raw[:6] in (b"GIF87a", b"GIF89a") and len(raw) >= 10:
            import struct
            w, h = struct.unpack("<HH", raw[6:10])
            return (w, h)
        if raw[:2] == b"BM" and len(raw) >= 26:
            import struct
            w, h = struct.unpack("<ii", raw[18:26])
            return (abs(w), abs(h))
    except Exception:
        pass
    return (0, 0)


def _pdf_images(data: bytes):
    """Return ([{name,width,height,pages}], truncated) for a PDF's image XObjects.

    D25: at most MAX_DOC_IMAGES unique images are inspected. `truncated` is True
    when the cap stopped the scan before the last page.
    """
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    max_images = max(1, int(getattr(config, "MAX_DOC_IMAGES", 10) or 10))
    seen = {}
    truncated = False
    for page in reader.pages:
        if len(seen) >= max_images:
            truncated = True
            break
        try:
            res = page.get("/Resources", {})
            xo = res.get("/XObject", {})
            if hasattr(xo, "get_object"):
                xo = xo.get_object()
            for name in xo:
                if len(seen) >= max_images:
                    truncated = True
                    break
                obj = xo[name]
                if hasattr(obj, "get_object"):
                    obj = obj.get_object()
                if obj.get("/Subtype") == "/Image":
                    key = str(name)
                    d = seen.get(key, {"width": obj.get("/Width", 0), "height": obj.get("/Height", 0), "pages": 0})
                    d["pages"] += 1
                    seen[key] = d
        except Exception:
            continue
        if truncated:
            break
    return ([{"name": k, "width": v["width"], "height": v["height"], "pages": v["pages"]}
             for k, v in seen.items()], truncated)


def _pdf_header_vector_logo(reader):
    """Detect a VECTOR logo/branding block in a PDF page header (no AI, no render).

    Some PDFs draw the logo as vector paths (e.g. ACCA's red badge), so there is
    no image XObject for `page.images` to find. A PDF `/Artifact … /Subtype
    /Header` is page branding; inside it we flag:
      - a complex vector shape (>= 20 path ops) with a non-white fill, or
      - a painted (fill/stroke) block 20-400 pt, in the top 30% of the page,
        with a non-white fill or vector detail.

    Deliberately conservative: clips (`W*`) and full-bleed backgrounds are not a
    logo, and a text-only wordmark is left to the raster/AI evidence.

    Returns (found, detail) with detail {"page", "reason", ...}.
    """
    for pno, page in enumerate(reader.pages[:3], 1):
        try:
            W = float(page.mediabox.width)
            H = float(page.mediabox.height)
            data = page.get_contents().get_data()
        except Exception:
            continue
        for art in re.finditer(rb"/Artifact(.*?)BDC(.*?)EMC", data, re.S):
            if b"/Header" not in art.group(1):
                continue
            body = art.group(2)
            paths = len(re.findall(rb"\d+\.?\d*\s+\d+\.?\d*\s+[mlc](?![A-Za-z])", body))
            colors = []
            for c in re.findall(rb"([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(?:rg|RG)", body):
                try:
                    colors.append(tuple(float(v) for v in c))
                except ValueError:
                    pass
            nonwhite = any(
                not (abs(r - 1) < 0.02 and abs(g - 1) < 0.02 and abs(b - 1) < 0.02)
                for r, g, b in colors
            )
            if paths >= 20 and nonwhite:
                return True, {"page": pno, "reason": "vector_paths", "paths": paths}
            for m in re.finditer(
                rb"(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+re\s*"
                rb"([fFbBsS][*]?|B[*]?)",
                body,
            ):
                try:
                    x, y, w, h = (float(m.group(i)) for i in (1, 2, 3, 4))
                except ValueError:
                    continue
                if w >= 0.8 * W or h >= 0.8 * H:
                    continue  # full-bleed background/clip, not a logo
                if 20 <= w <= 400 and 20 <= h <= 400 and (y + h) >= 0.70 * H:
                    if nonwhite or paths >= 5:
                        return True, {"page": pno, "reason": "painted_header_block",
                                      "width": round(w), "height": round(h),
                                      "paths": paths}
    return False, {}


def _docx_images(data: bytes):
    """Return ([{name,width,height,pages,location}], truncated) for a DOCX.

    `location` tells where each image is anchored:
      - "header": referenced by a word/header*.xml  -> branding/letterhead logo
      - "body"  : referenced by word/document.xml    -> article image (photo/banner)
      - "unknown": in word/media/ but referenced by neither (or footer-only;
                  footers are intentionally NOT scanned)
    This is the fix for header logos being miscalled "photo" by size alone.
    """
    out = []
    truncated = False
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        names = set(z.namelist())

        # Build rId -> media target maps for headers and the body.
        def _media_map(rels_name):
            """Return {rId: mediaPath} for IMAGE relationships in a .rels file."""
            m = {}
            if rels_name not in names:
                return m
            try:
                rels = z.read(rels_name).decode("utf-8", "replace")
            except Exception:
                return m
            for rid, typ, target in re.findall(
                r'<Relationship Id="([^"]+)"[^>]*Type="([^"]+)"[^>]*Target="([^"]+)"', rels
            ):
                if "image" in typ and target.startswith("media/"):
                    m[rid] = target[len("media/"):]  # strip "media/" prefix
            return m

        header_maps = {}
        for n in names:
            if re.match(r"word/_rels/header\d+\.xml\.rels$", n):
                header_maps[n] = _media_map(n)

        body_map = _media_map("word/_rels/document.xml.rels")

        # Which media files are referenced in headers vs body (by their rId).
        header_media = set()
        body_media = set()

        def _embedded_targets(xml_name):
            """Return set of media paths referenced via r:embed in one xml part."""
            if xml_name not in names:
                return set()
            try:
                xml = z.read(xml_name).decode("utf-8", "replace")
            except Exception:
                return set()
            refs = set(re.findall(r'r:embed="([^"]+)"', xml))
            return refs

        # headers: rId -> media via each header rels map
        for rels_name, rmap in header_maps.items():
            header_xml = rels_name.replace("_rels/", "").replace(".rels", "")
            for rid in _embedded_targets(header_xml):
                if rid in rmap:
                    header_media.add(rmap[rid])

        # body: rId -> media via document rels
        for rid in _embedded_targets("word/document.xml"):
            if rid in body_map:
                body_media.add(body_map[rid])

        # Classify each media file's location (D25: at most MAX_DOC_IMAGES).
        max_images = max(1, int(getattr(config, "MAX_DOC_IMAGES", 10) or 10))
        media_names = [n for n in names
                       if n.startswith("word/media/") and not n.endswith("/")]
        truncated = False
        for idx, n in enumerate(media_names):
            if len(out) >= max_images:
                truncated = idx < len(media_names)
                break
            media = n[len("word/media/"):]
            if media in header_media:
                location = "header"
            elif media in body_media:
                location = "body"
            else:
                location = "unknown"  # footer-only or unreferenced — not scanned
            w, h = _image_dims(z.read(n))
            out.append({"name": n, "width": w, "height": h, "pages": 1, "location": location})
    except Exception:
        pass
    return out, truncated


def classify_doc_images(data: bytes, filename: str):
    """Deterministically classify every embedded image in a PDF/DOCX.

    This is the fix for the "photo mistaken for logo" problem: instead of just
    checking `any image exists`, we read each image's real dimensions and decide
    logo vs photo from size + page repetition.

    Returns:
        {
          "has_image": bool,
          "images":   [{"name", "width", "height", "pages", "kind": logo|photo|unknown}],
          "has_logo":  bool,   # at least one image classified as a logo
          "has_photo": bool,   # at least one image classified as a photo
        }

    Example (MICSEA press statement PDF):
        {"has_image": true,
         "images": [{"name": "/Image5", "width": 1414, "height": 2000, "pages": 3, "kind": "photo"},
                    {"name": "/Image32", "width": 80,  "height": 77,  "pages": 1, "kind": "logo"}],
         "has_logo": true, "has_photo": true}
    """
    name = (filename or "").lower()
    imgs = []
    truncated = False
    try:
        if name.endswith(".pdf"):
            imgs, truncated = _pdf_images(data)
            # Vector logos have no image XObject; a /Header artifact with vector
            # artwork is the only deterministic trace (e.g. the ACCA badge).
            try:
                from pypdf import PdfReader
                found, detail = _pdf_header_vector_logo(PdfReader(io.BytesIO(data)))
                if found:
                    imgs.append({"name": "pdf-header-vector", "width": 0, "height": 0,
                                 "pages": 1, "location": "header", "vector": True,
                                 "vectorDetail": detail})
            except Exception:
                pass
        elif name.endswith((".docx", ".doc")):
            imgs, truncated = _docx_images(data)
    except Exception:
        imgs = []

    classified = []
    for im in imgs:
        w, h, pages = im["width"], im["height"], im.get("pages", 1)
        key = im["name"].lower()
        location = im.get("location", "")  # DOCX: "header" | "body" | "unknown"
        if location == "header":
            kind = "logo"                      # header image = branding/letterhead logo
        elif "logo" in key:
            kind = "logo"
        elif w <= 0 or h <= 0:
            kind = "unknown"
        elif max(w, h) <= LOGO_MAX:
            kind = "logo"                      # small image = badge/logo
        elif min(w, h) <= BANNER_MIN:
            kind = "logo"                      # wide-short strip = header banner logo
        elif min(w, h) > 0 and (max(w, h) / min(w, h)) >= 3.0:
            kind = "logo"                      # wide banner / logo strip
        elif max(w, h) >= PHOTO_MIN:
            # A repeated page-wide strip (header letterhead / footer band) is
            # branding, not a news photo — even when it is large.
            wide = min(w, h) > 0 and (max(w, h) / min(w, h)) >= 3.0
            if pages > 1 and (max(w, h) <= 700 or wide):
                kind = "logo"
            else:
                kind = "photo"
        else:
            kind = "unknown"
        classified.append({**im, "kind": kind})

    return {
        "has_image": bool(classified),
        "images": classified,
        "truncated": truncated,
        "has_logo": any(i["kind"] == "logo" for i in classified),
        "has_photo": any(i["kind"] == "photo" for i in classified),
    }


def _kind_from_bytes(raw: bytes, location: str = "") -> str:
    """Classify a raw image as logo/photo/unknown from dimensions (+location)."""
    if location == "header":
        return "logo"
    w, h = _image_dims(raw)
    if w <= 0 or h <= 0:
        return "unknown"
    if max(w, h) <= LOGO_MAX:
        return "logo"
    if min(w, h) <= BANNER_MIN:
        return "logo"
    if min(w, h) > 0 and (max(w, h) / min(w, h)) >= 3.0:
        return "logo"                      # wide banner / logo strip (e.g. 1033x275)
    if max(w, h) >= PHOTO_MIN:
        return "photo"
    return "unknown"


def extract_doc_images(data: bytes, filename: str, only_photos: bool = True):
    """Return {safe_name: bytes} for images embedded in a DOCX or PDF.

    only_photos=True (default) drops images classified as logos (header/letterhead
    + small/banner sizes), keeping only real photos. Names are generic
    ("docphoto-1.jpg") so they are always filesystem-safe.

    Example:
        extract_doc_images(docx_bytes, "release.docx")
        -> {"docphoto-1.png": b"\\x89PNG...", "docphoto-2.jpg": b"\\xff\\xd8..."}
    """
    name = (filename or "").lower()
    out = {}
    n = 0
    max_images = max(1, int(getattr(config, "MAX_DOC_IMAGES", 10) or 10))
    scan_max = max(max_images, int(getattr(config, "DOC_IMAGE_SCAN_MAX", 25) or 25))

    def _add(raw, ext, location=""):
        nonlocal n
        if not raw or n >= max_images:
            return
        if only_photos and _kind_from_bytes(raw, location) != "photo":
            return
        n += 1
        out["docphoto-%d%s" % (n, ext)] = raw

    try:
        if name.endswith(".docx"):
            z = zipfile.ZipFile(io.BytesIO(data))
            names = set(z.namelist())

            def _media_map(rels_name):
                m = {}
                if rels_name not in names:
                    return m
                try:
                    rels = z.read(rels_name).decode("utf-8", "replace")
                except Exception:
                    return m
                for rid, typ, target in re.findall(
                    r'<Relationship Id="([^"]+)"[^>]*Type="([^"]+)"[^>]*Target="([^"]+)"', rels
                ):
                    if "image" in typ and target.startswith("media/"):
                        m[rid] = target[len("media/"):]
                return m

            header_media = set()
            for rels_name in names:
                if re.match(r"word/_rels/header\d+\.xml\.rels$", rels_name):
                    rmap = _media_map(rels_name)
                    hx = rels_name.replace("_rels/", "").replace(".rels", "")
                    if hx in names:
                        try:
                            xml = z.read(hx).decode("utf-8", "replace")
                        except Exception:
                            xml = ""
                        for rid in re.findall(r'r:embed="([^"]+)"', xml):
                            if rid in rmap:
                                header_media.add(rmap[rid])

            examined = 0
            for member in names:
                if examined >= scan_max or n >= max_images:
                    break
                if member.startswith("word/media/") and member.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")):
                    examined += 1
                    loc = "header" if member[len("word/media/"):] in header_media else "body"
                    ext = "." + member.rsplit(".", 1)[-1].lower()
                    _add(z.read(member), ext, loc)
        elif name.endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            examined = 0
            for page in reader.pages:
                if examined >= scan_max or n >= max_images:
                    break
                try:
                    for img in page.images:
                        if examined >= scan_max or n >= max_images:
                            break
                        examined += 1
                        raw = img.data
                        if raw[:2] == b"\xff\xd8":
                            ext = ".jpg"
                        elif raw[:8] == b"\x89PNG\r\n\x1a\n":
                            ext = ".png"
                        else:
                            ext = ".bin"
                        _add(raw, ext)
                except Exception:
                    continue
    except Exception:
        pass
    return out


def _cap(text):
    """Trim article text to the prompt budget (a long PDF must not overflow the AI)."""
    text = text or ""
    limit = int(getattr(config, "EXTRACT_MAX_CHARS", 120000) or 120000)
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[... truncated to the first %d characters ...]" % limit


def build_extract_user(model, attachment_text, drive_media=None, drive_logo=False,
                       candidates=None):
    """Build the user message for the Extract & Clean PR prompt.

    `model`         : the normalized email model
    `attachment_text`: legacy first attachment text (fallback when no candidates)
    `drive_media`   : legacy Drive media-kit text (fallback when no candidates)
    `drive_logo`    : whether the fetched Drive doc has an embedded image
    `candidates`    : D24 pool [{label, source, name, text}] — the collect-then-
                      select input. When present, the AI chooses among these plus
                      the email body; the legacy sections are omitted.
    """
    subject = model.get("subject", "")
    from_ = model.get("from", "")
    date = model.get("date", "")
    # Use the cleaned body for the AI (cover/disclaimer/forwarders removed)
    raw_email = model.get("cleanRawEmail", "") or model.get("rawEmail", "")
    attachment_names = ", ".join(a["filename"] for a in model.get("attachments", []))

    user = (
        f"HERE IS THE RAW EMAIL:\n"
        f"- Subject: {subject}\n- From header: {from_}\n- Date: {date}\n"
        f"- Email body text (cleaned):\n{raw_email}\n\n"
        f"ATTACHMENT INFO:\n- attachmentNames: {attachment_names}"
    )
    if candidates:
        max_chars = int(getattr(config, "COLLECT_CANDIDATE_MAX_CHARS", 30000) or 30000)
        user += "\n\nCANDIDATE SOURCES (fetched; choose the ONE that is the article):\n"
        for c in candidates:
            text = (c.get("text") or "")[:max_chars]
            truncated = "\n[... truncated ...]" if len(c.get("text") or "") > max_chars else ""
            user += (
                f"\n[{c.get('label', 'C?')}] source={c.get('source', '')} "
                f"name={c.get('name', '')}\n{text}{truncated}\n"
            )
        user += (
            "\nReturn chosenCandidate as the [C#] label of the candidate you selected, "
            "or \"email_body\" if the email body itself is the article, or \"none\"."
        )
    else:
        user += (
            f"\n- attachmentText (extracted from attached release if present): "
            f"{_cap(attachment_text)}"
        )
        if drive_media is not None:
            user += f"\n\nDRIVE MEDIA KIT (fetched):\n{_cap(drive_media)}\n"
            user += f"\nDRIVE DOC HAS EMBEDDED IMAGE (logo): {drive_logo}"
    return user


def extract(model, attachment_text, drive_media=None, drive_logo=False, candidates=None, client=None, prompt_version=None):
    """Run the Extract & Clean PR AI call and return its JSON dict.

    Also applies the LINK-GUARD: the model's `mediaKitLink` is only trusted if
    it actually appears in the email body — otherwise it is cleared (prevents
    hallucinated drive/box links).

    Example:
        r = extract(model, attachment_text, candidates=pool)
        r["bodyText"]        # -> the verbatim article
        r["chosenCandidate"] # -> "C1" | "email_body" | "none"
        r["articleSource"]   # -> "attachment_pdf" | "drive_link" | "email_body"
    """
    system = config.load_prompt("extract_prompt.txt", version=prompt_version)
    # Strip the n8n template tail ("HERE IS THE RAW EMAIL: ... {{ $json... }}")
    # since the actual data is supplied via the user message.
    marker = "HERE IS THE RAW EMAIL:"
    idx = system.find(marker)
    if idx != -1:
        system = system[:idx].rstrip()
    user = build_extract_user(model, attachment_text, drive_media, drive_logo,
                              candidates=candidates)
    result = (client or LLMClient()).chat_json(system, user, max_tokens=12000)

    # link-guard: only trust mediaKitLink if it's actually in the email body
    media_link = str(result.get("mediaKitLink", "") or "").strip()
    links = model.get("linksFound", [])
    if media_link:
        trusted = False
        for l in links:
            a1 = re.sub(r"[#?].*$", "", l).rstrip("/")
            a2 = re.sub(r"[#?].*$", "", media_link).rstrip("/")
            if a1 == a2 or a1 in a2 or a2 in a1:
                trusted = True
                break
        if not trusted:
            result["mediaKitLink"] = ""
    return result