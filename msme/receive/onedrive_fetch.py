# =============================================================================
# FILE HEADER
# file    : msme/receive/onedrive_fetch.py
# role    : Receive — OneDrive public share fetch (1drv.ms / onedrive.live.com)
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : open a public OneDrive share as a guest, list its folder, download docs/images
#           and extract text/classify images — no Microsoft account needed.
# pages   : n/a
# calls   : extract (text + image classifier), config
# called  : pipeline.py
# amend   : keep the browser UA + cookie jar; guest FedAuth + the v2.0 item API is the
#           only anonymous path that works. Test: fetch the APAC CEOs folder in the reply.
# =============================================================================
"""OneDrive fetcher for PUBLIC share links (1drv.ms / onedrive.live.com).

The share page issues a guest `FedAuth` cookie when fetched with a browser UA.
The v2.0 item API on the same host then lists children and the per-file
`@content.downloadUrl` downloads them. The old `api.onedrive.com/shares` API
returns 401 and a bot UA gets 403 — do not use those.

Example:
    kit = onedrive_fetch.fetch_kit("https://1drv.ms/f/c/…")
    kit["mediaKit"]   # [{"name": "...pdf", "text": "..."}]
    kit["images"]     # [{"name", "size", "bytes"}]
"""
import http.cookiejar
import json
import re
import urllib.error
import urllib.parse
import urllib.request

from msme import config
from msme.receive import extract

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
_DOC_EXT = (".pdf", ".docx", ".doc", ".txt", ".md")
_IMG_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".tif", ".tiff")


def is_onedrive_link(url):
    """True for a 1drv.ms / onedrive.live.com share link."""
    low = (url or "").lower()
    return "1drv.ms/" in low or "onedrive.live.com/" in low


def _session():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [
        ("User-Agent", UA),
        ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
        ("Accept-Language", "en-US,en;q=0.9"),
    ]
    return cj, op


def _resolve(link):
    """Open the share link, take the guest cookie and return cid/item/e/path."""
    cj, op = _session()
    try:
        r = op.open(link, timeout=config.ONEDRIVE_TIMEOUT)
        r.read(200000)  # the page shell is enough; cookies are already set
        final = r.geturl()
    except Exception as e:
        raise RuntimeError(f"OneDrive share open failed: {str(e)[:180]}")
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(final).query)
    cid = (qs.get("cid") or [""])[0]
    item = urllib.parse.unquote((qs.get("spopath") or qs.get("id") or [""])[0])
    e = (qs.get("e") or [""])[0]
    path = ""
    if item.startswith("/personal/"):
        path = item
        item = ""
    if not cid:
        m = re.search(r"/personal/([^/?#&]+)", path or final)
        if m:
            cid = m.group(1)
    if not cid:
        raise RuntimeError("OneDrive share has no cid")
    if not item and not path:
        raise RuntimeError("OneDrive share has no item id or path")
    return {"cid": cid, "item": item, "e": e, "path": path,
            "final": final, "opener": op, "cookies": cj}


def _json(op, url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json;odata=verbose",
    })
    with op.open(req, timeout=config.ONEDRIVE_TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", "replace") or "{}")


def _e_param(e):
    return f"?e={urllib.parse.quote(e)}" if e else ""


def _list_item(op, cid, item, e):
    base = f"https://onedrive.live.com/personal/{cid}/_api/v2.0/drive/items"
    q = urllib.parse.quote(item, safe="!")
    try:
        d = _json(op, f"{base}/{q}/children{_e_param(e)}")
        return d.get("value", [])
    except urllib.error.HTTPError as ex:
        if ex.code != 404:
            raise
        # The share may point at a single FILE, not a folder.
        meta = _json(op, f"{base}/{q}{_e_param(e)}")
        return [meta]


def _list_path(op, cid, path):
    base = f"https://onedrive.live.com/personal/{cid}/_api/web"
    q = urllib.parse.quote(path, safe="/")
    files = _json(op, f"{base}/GetFolderByServerRelativeUrl('{q}')/Files"
                       "?$select=Name,ServerRelativeUrl,Length")
    folders = _json(op, f"{base}/GetFolderByServerRelativeUrl('{q}')/Folders"
                         "?$select=Name,ServerRelativeUrl")
    out = []
    for f in files.get("d", {}).get("results", []):
        out.append({"name": f.get("Name", ""), "size": f.get("Length", 0),
                    "file": {}, "path": f.get("ServerRelativeUrl", "")})
    for f in folders.get("d", {}).get("results", []):
        out.append({"name": f.get("Name", ""), "folder": {}, "path": f.get("ServerRelativeUrl", "")})
    return out


def _download(op, child, cid, e):
    url = child.get("@content.downloadUrl", "")
    if not url and child.get("id"):
        url = (f"https://onedrive.live.com/personal/{cid}/_api/v2.0/drive/items/"
               f"{urllib.parse.quote(child['id'], safe='!')}/content{_e_param(e)}")
    if not url and child.get("path"):
        url = (f"https://onedrive.live.com/personal/{cid}/_api/web/"
               f"GetFileByServerRelativeUrl('{urllib.parse.quote(child['path'], safe='/')}')/$value")
    if not url:
        raise RuntimeError("no download url")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with op.open(req, timeout=config.ONEDRIVE_TIMEOUT * 2) as r:
        data = r.read(config.ONEDRIVE_MAX_FILE_BYTES + 1)
    if len(data) > config.ONEDRIVE_MAX_FILE_BYTES:
        raise RuntimeError("file too large")
    return data


def _ext_of(name):
    low = (name or "").lower()
    for ext in _DOC_EXT + _IMG_EXT:
        if low.endswith(ext):
            return ext
    return ""


def fetch_kit(link, max_depth=3):
    """List a public OneDrive share and return docs + images (no AI).

    Returns the same shape the pipeline already uses for Drive:
        mediaKit, images, originals, docHasEmbeddedImage, docImageDetails,
        docLogos, docPhotos, detail
    """
    res = _resolve(link)
    op, cid, e = res["opener"], res["cid"], res["e"]
    media_kit, images, originals, doc_details = [], [], [], []
    doc_logos = doc_photos = False
    detail = {"final": res["final"][:300], "cid": cid, "item": res["item"],
              "files": [], "errors": []}
    queue = [(res["item"], res["path"], 0)]
    seen = set()
    count = 0
    while queue and count < config.ONEDRIVE_MAX_ITEMS:
        item, path, depth = queue.pop(0)
        key = item or path
        if key in seen or depth > max_depth:
            continue
        seen.add(key)
        try:
            children = _list_item(op, cid, item, e) if item else _list_path(op, cid, path)
        except Exception as ex:
            detail["errors"].append({"list": key, "error": str(ex)[:140]})
            continue
        for ch in children:
            if count >= config.ONEDRIVE_MAX_ITEMS:
                break
            count += 1
            name = ch.get("name") or ""
            if "folder" in ch:
                continue  # recurse after files (queue below)
            ext = _ext_of(name)
            size = int(ch.get("size") or 0)
            try:
                if ext in _DOC_EXT:
                    data = _download(op, ch, cid, e)
                    text = extract.extract_text_from_bytes(data, name)
                    originals.append({"name": name, "bytes": data, "size": len(data)})
                    if text.strip():
                        media_kit.append({"name": name, "text": text})
                    if ext in (".pdf", ".docx", ".doc"):
                        cinfo = extract.classify_doc_images(data, name)
                        if cinfo["has_image"]:
                            doc_details.append({"file": name, "hasImage": True,
                                                "images": cinfo["images"],
                                                "truncated": cinfo.get("truncated", False)})
                        doc_logos = doc_logos or cinfo["has_logo"]
                        doc_photos = doc_photos or cinfo["has_photo"]
                    detail["files"].append({"name": name, "kind": "doc", "size": len(data)})
                elif ext in _IMG_EXT and len(images) < config.ONEDRIVE_MAX_IMAGES:
                    data = _download(op, ch, cid, e)
                    images.append({"name": name, "size": len(data), "bytes": data})
                    detail["files"].append({"name": name, "kind": "image", "size": len(data)})
            except Exception as ex:
                detail["errors"].append({"file": name, "error": str(ex)[:140]})
        # enqueue subfolders after the files
        for ch in children:
            if "folder" in ch and (ch.get("id") or ch.get("path")):
                queue.append((ch.get("id", ""), ch.get("path", ""), depth + 1))
    if not detail["files"] and detail["errors"]:
        raise RuntimeError(detail["errors"][0].get("error") or "OneDrive fetch failed")
    return {
        "mediaKit": media_kit,
        "images": images,
        "originals": originals,
        "docHasEmbeddedImage": bool(doc_details),
        "docImageDetails": doc_details,
        "docLogos": doc_logos,
        "docPhotos": doc_photos,
        "detail": detail,
    }
