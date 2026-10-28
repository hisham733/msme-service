# =============================================================================
# FILE HEADER
# file    : box_fetch.py
# role    : Receive — public Box press-kit fetch
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : parse a public Box shared-folder page and download its files using only the standard library.
# pages   : n/a
# calls   : config.BOX_MAX_BYTES; urllib
# called  : pipeline.py
# amend   : public links only (no login); the size cap skips large TIFFs on purpose.
#           Test: python3 -c "import box_fetch; print(box_fetch.is_box_link('https://x.app.box.com/s/1'))"
# =============================================================================
"""Box Fetch: pull media from a PUBLIC Box shared-folder link (no login).

The receive pipeline can be pointed at a public Box press-kit link (e.g.
https://voxeureka.app.box.com/s/<token>/folder/<folder_id>). We:
  1. fetch the shared page,
  2. parse each item's file id (typedID "f_<id>") + name from the page,
  3. download each file via Box's public "box_download_shared_file" endpoint
     (which 302-redirects to the real file on public.boxcloud.com).

Only the standard library is used (urllib). Large files (e.g. print-res TIFFs)
are skipped via config.BOX_MAX_BYTES.

Example:
    kit = box_fetch.fetch_press_kit("https://voxeureka.app.box.com/s/<token>/folder/123")
    kit["images"]      # [{"name": "hero.jpg", "bytes": b"..."}]
    kit["originals"]   # [{"name": "Release.docx", "bytes": b"..."}]
    kit["docs"]        # [{"name": "Release.docx", "text": "..."}]
"""
import re
import urllib.request
import urllib.parse

import config

_UA = "Mozilla/5.0 (compatible; MSME-receive/1.0)"
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".heic")
DOC_EXT = (".pdf", ".docx", ".doc")


def is_box_link(url):
    """True for any *.box.com shared link (including the .app.box.com host)."""
    u = (url or "").lower()
    return ("box.com/s/" in u) or bool(re.search(r"https?://[a-z0-9.-]*box\.com/", u))


def _host_of(url):
    m = re.match(r"(https?://[^/]+)", url or "")
    return m.group(1) if m else ""


def parse(link):
    """Return {base, host, token, folder_id} from a Box shared link."""
    host = _host_of(link)
    token = ""
    m = re.search(r"/s/([A-Za-z0-9]+)", link or "")
    if m:
        token = m.group(1)
    folder_id = ""
    m = re.search(r"/folder/(\d+)", link or "")
    if m:
        folder_id = m.group(1)
    return {"base": host, "host": host, "token": token, "folder_id": folder_id}


def _http_get(url, timeout=None, max_bytes=None):
    """GET a URL, following redirects. Returns (bytes|None, content_type, status).

    If max_bytes is set and the body would exceed it, returns (None, ...).
    """
    timeout = timeout or config.BOX_TIMEOUT
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        ct = resp.headers.get("Content-Type", "")
        status = getattr(resp, "status", 200)
        if max_bytes:
            clen = resp.headers.get("Content-Length")
            try:
                if clen and int(clen) > max_bytes:
                    return None, ct, status
            except Exception:
                pass
        chunks = []
        total = 0
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            total += len(chunk)
            if max_bytes and total > max_bytes:
                return None, ct, status
            chunks.append(chunk)
        return b"".join(chunks), ct, status


def list_items(link, max_items=None):
    """Return [{id, name, folder}] for the items in a public Box shared folder."""
    max_items = max_items or config.BOX_MAX_ITEMS
    html, _ct, _st = _http_get(link, max_bytes=8 * 1024 * 1024)
    if not html:
        return []
    text = html.decode("utf-8", "replace")
    items = []
    for chunk in text.split('"typedID":"')[1:]:
        m = re.match(r"([fd])_(\d+)", chunk)
        if not m:
            continue
        kind, fid = m.group(1), m.group(2)
        nm = re.search(r'"name":"([^"]+)"', chunk[:1200])
        name = nm.group(1) if nm else ""
        name = name.replace("&#39;", "'").replace("&amp;", "&")
        items.append({"id": kind + "_" + fid, "name": name, "folder": kind == "d"})
        if len(items) >= max_items:
            break
    return items


def download(base_host, token, file_id, max_bytes=None):
    """Download one Box shared file (token-free). Returns bytes or None."""
    max_bytes = max_bytes or config.BOX_MAX_BYTES
    url = (base_host + "/index.php?rm=box_download_shared_file"
           "&shared_name=" + urllib.parse.quote(token) +
           "&file_id=" + urllib.parse.quote(file_id))
    data, _ct, _st = _http_get(url, max_bytes=max_bytes)
    return data


def _classify_image(raw):
    """Return 'photo' | 'logo' | 'unknown' using size heuristics (reuses extract)."""
    try:
        import extract
        w, h = extract._image_dims(raw)
        if w <= 0 or h <= 0:
            return "unknown"
        if max(w, h) <= extract.LOGO_MAX:
            return "logo"
        if min(w, h) <= extract.BANNER_MIN:
            return "logo"
        if max(w, h) >= extract.PHOTO_MIN:
            return "photo"
        return "unknown"
    except Exception:
        return "unknown"


def fetch_press_kit(link, max_depth=3):
    """Fetch a public Box press kit (recursing subfolders) -> {images, originals, docs, detail}."""
    out = {"images": [], "originals": [], "docs": [],
           "detail": {"link": link, "folders": 0, "files": 0, "images": 0, "originals": 0, "skipped": []}}
    info = parse(link)
    if not info["token"]:
        out["detail"]["error"] = "no box token in link"
        return out
    base, token = info["host"], info["token"]
    start = link if info["folder_id"] else (base + "/s/" + token)
    seen = set()
    stack = [(start, 0)]
    files = []
    while stack and len(files) < config.BOX_MAX_ITEMS:
        url, depth = stack.pop()
        try:
            items = list_items(url)
        except Exception as e:
            out["detail"]["skipped"].append({"name": url, "reason": "list failed: " + str(e)[:60]})
            continue
        for it in items:
            if it["folder"]:
                fid = it["id"].split("_")[-1]
                if fid in seen:
                    continue
                seen.add(fid)
                out["detail"]["folders"] += 1
                if depth + 1 <= max_depth:
                    stack.append((base + "/s/" + token + "/folder/" + fid, depth + 1))
            else:
                files.append(it)

    out["detail"]["files"] = len(files)
    for it in files:
        name = it["name"] or it["id"]
        low = name.lower()
        try:
            data = download(base, token, it["id"])
        except Exception as e:
            out["detail"]["skipped"].append({"name": name, "reason": str(e)[:80]})
            continue
        if not data:
            out["detail"]["skipped"].append({"name": name, "reason": "too large or empty"})
            continue
        if low.endswith(IMAGE_EXT):
            kind = _classify_image(data)
            if kind == "logo":
                out["detail"]["skipped"].append({"name": name, "reason": "logo"})
                continue
            out["images"].append({"name": name, "bytes": data, "kind": kind})
            out["detail"]["images"] += 1
        elif low.endswith(DOC_EXT):
            try:
                import extract
                text = extract.extract_text_from_bytes(data, name) or ""
            except Exception:
                text = ""
            out["originals"].append({"name": name, "bytes": data})
            out["docs"].append({"name": name, "text": text})
            out["detail"]["originals"] += 1
        else:
            out["detail"]["skipped"].append({"name": name, "reason": "unsupported type"})
    return out
