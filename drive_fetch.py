# =============================================================================
# FILE HEADER
# file    : drive_fetch.py
# role    : Receive — Google Drive media-kit walk
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : iterative DFS over a Drive folder (no AI) plus a single-file fetch: collect docs + the 15
#           largest images, extract text, detect an embedded logo, and pick the release-named doc by
#           name + first-paragraph signals (multilingual).
# pages   : n/a
# calls   : creds.drive, config, extract helpers, io/zipfile/re
# called  : pipeline.py
# amend   : no AI here; the image cap, English-only pick and DFS (no agent loop) are deliberate. A single
#           file link (/file/d/<id>) goes through fetch_file(), not the folder walk.
#           Test: run one email with a Drive link and inspect the drive_fetch stage
# =============================================================================
"""Drive Fetch: recursively walk a Google Drive folder, download docs, extract text.

Ports the n8n 'Drive Fetch Tool' sub-workflow, but the recursion that broke the
n8n agent (max-iterations) is now a deterministic iterative DFS walk — so it can
never hit an agent iteration cap.

`fetch_file()` handles the other common case: the email links ONE Drive file
(e.g. /file/d/<id>/view) instead of a media-kit folder.

Example usage:
    kit = drive_fetch.fetch_media_kit("1abc...folderId")
    kit["mediaKit"]              # [{"name": "...", "text": "..."}, ...]
    kit["images"]                # [{"name": "...", "id": "...", "mimeType": "image/png"}, ...]
    kit["docHasEmbeddedImage"]   # True if any doc has a logo image inside

    one = drive_fetch.fetch_file("1xu0...fileId")
    one["ok"]                    # False when the owner disabled download
    one["reason"]                # "cannotDownloadFile" | "file_too_large" | ...
"""
import io
import os
import re
import zipfile

import config
import creds
from extract import classify_doc_images, extract_text_from_bytes

# Max Drive images to keep per media kit (cap the biggest, to bound downloads).
MAX_DRIVE_IMAGES = int(os.environ.get("MAX_DRIVE_IMAGES", "15"))


def _list_children(drive, folder_id):
    """List non-trashed files/folders directly inside `folder_id`."""
    result = (
        drive.files()
        .list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id,name,mimeType,size)",
            pageSize=200,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    return result.get("files", [])


def _download(drive, file_id):
    """Download a Drive file's raw bytes into memory (works in shared drives)."""
    request = drive.files().get_media(fileId=file_id, supportsAllDrives=True)
    from googleapiclient.http import MediaIoBaseDownload

    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue()


# A Drive FILE link (not a folder): /file/d/<id>/view or ?id=<id>
_FILE_ID_RE = re.compile(r"(?:/file/d/|[?&]id=)([A-Za-z0-9_-]{10,})")
# A Google Doc link is a Drive Google-native document, not a Drive file link.
_DOC_ID_RE = re.compile(r"docs\.google\.com/document/(?:u/\d+/)?d/([A-Za-z0-9_-]{10,})")


def doc_id_from_link(link):
    """Return the document id from a docs.google.com/document/d/<id> link."""
    m = _DOC_ID_RE.search(link or "")
    return m.group(1) if m else ""


def file_id_from_link(link):
    """Return the file id from a single-file Drive link, or "" for a folder link.

    Example:
        file_id_from_link("https://drive.google.com/file/d/1xu00.../view")
        -> "1xu00..."
        file_id_from_link("https://drive.google.com/drive/folders/1abc...")
        -> ""
    """
    link = link or ""
    if "drive.google.com" not in link or "/folders/" in link:
        return ""
    m = _FILE_ID_RE.search(link)
    return m.group(1) if m else ""


def fetch_file(file_id):
    """Fetch ONE Drive file and extract its text (no AI).

    Returns:
        {"ok": bool, "id", "name", "mimeType", "size", "owner", "canDownload",
         "bytes": b"...", "text": "...", "imageInfo": {...}|None, "reason": ""}

    `ok` is False with `reason` in {"trashed", "cannotDownloadFile",
    "file_too_large", "unsupported_google_file", "export_failed", "download_failed"}.
    A refused file is a deliberate outcome, not an exception: the caller records
    it as needs-human so an editor can request download access.

    Example:
        one = fetch_file("1xu00...")   # owner disabled download
        one["ok"], one["reason"]       # -> (False, "cannotDownloadFile")
    """
    drive = creds.drive()
    meta = drive.files().get(
        fileId=file_id,
        fields="id,name,mimeType,size,owners(emailAddress),capabilities(canDownload),trashed",
        supportsAllDrives=True,
    ).execute()
    mime = meta.get("mimeType") or ""
    name = meta.get("name") or "drive-file"
    owner = ((meta.get("owners") or [{}])[0]).get("emailAddress", "")
    result = {
        "ok": False,
        "id": file_id,
        "name": name,
        "mimeType": mime,
        "size": int(meta.get("size") or 0),
        "owner": owner,
        "canDownload": bool((meta.get("capabilities") or {}).get("canDownload")),
        "bytes": b"",
        "text": "",
        "imageInfo": None,
        "reason": "",
    }
    if meta.get("trashed"):
        result["reason"] = "trashed"
        return result
    if mime == "application/vnd.google-apps.folder":
        result["reason"] = "is_folder"
        result["folderId"] = file_id
        return result

    # Google-native files are EXPORTED, not downloaded (D17):
    #   Docs -> text; Slides/Sheets -> PDF (text + images); Drawings -> PNG (media).
    if mime.startswith("application/vnd.google-apps"):
        try:
            if mime == "application/vnd.google-apps.document":
                data = drive.files().export(fileId=file_id, mimeType="text/plain").execute()
                text = data.decode("utf-8", "replace") if isinstance(data, bytes) else str(data)
                if not name.lower().endswith((".txt", ".md")):
                    name = name + ".txt"
                raw = data if isinstance(data, bytes) else text.encode("utf-8")
                result.update({"ok": True, "name": name, "bytes": raw, "text": text})
                return result
            if mime in ("application/vnd.google-apps.presentation",
                        "application/vnd.google-apps.spreadsheet"):
                data = drive.files().export(fileId=file_id, mimeType="application/pdf").execute()
                if len(data) > config.DRIVE_MAX_FILE_BYTES:
                    result["reason"] = "file_too_large"
                    return result
                if not name.lower().endswith(".pdf"):
                    name = name + ".pdf"
                text = extract_text_from_bytes(data, name)
                image_info = classify_doc_images(data, name)
                result.update({"ok": True, "name": name, "mimeType": "application/pdf",
                               "bytes": data, "text": text, "imageInfo": image_info})
                return result
            if mime == "application/vnd.google-apps.drawing":
                data = drive.files().export(fileId=file_id, mimeType="image/png").execute()
                if len(data) > config.DRIVE_MAX_FILE_BYTES:
                    result["reason"] = "file_too_large"
                    return result
                if not name.lower().endswith(".png"):
                    name = name + ".png"
                result.update({"ok": True, "name": name, "mimeType": "image/png",
                               "bytes": data, "text": "", "imageInfo": None})
                return result
        except Exception as e:
            print(f"[drive] export {name} failed: {e}")
            result["reason"] = "export_failed"
            return result
        result["reason"] = "unsupported_google_file"
        return result

    if not result["canDownload"]:
        result["reason"] = "cannotDownloadFile"
        return result
    if result["size"] and result["size"] > config.DRIVE_MAX_FILE_BYTES:
        result["reason"] = "file_too_large"
        return result
    try:
        data = _download(drive, file_id)
    except Exception as e:
        print(f"[drive] download {name} failed: {e}")
        result["reason"] = "download_failed"
        return result
    text = extract_text_from_bytes(data, name)
    image_info = None
    if name.lower().endswith((".pdf", ".docx", ".doc")):
        image_info = classify_doc_images(data, name)
    result.update({"ok": True, "bytes": data, "text": text, "imageInfo": image_info})
    return result


def fetch_media_kit(folder_id, max_depth=5):
    """Walk a Drive folder and return { mediaKit, images, originals, docHasEmbeddedImage,
    docImageDetails, docLogos, docPhotos }.

    - mediaKit  : docs whose text extracted OK (name + text)
    - images    : image files found (not downloaded)
    - originals : ALL source docs/images (id + name) so we can save them later
    - docHasEmbeddedImage : True if any doc contains an embedded image
    - docImageDetails : [{file, hasImage, images:[{name,width,height,kind}]}] for
                        each doc with an embedded image (position-aware for DOCX)
    - docLogos  : True if any doc has a LOGO-classified embedded image
    - docPhotos : True if any doc has a PHOTO-classified embedded image

    Uses an iterative stack (DFS) instead of recursion to avoid n8n's
    max-iterations crash.

    Example:
        {"mediaKit": [{"name": "EN_RELEASE.docx", "text": "..."}],
         "images": [{"name": "hero.jpg", "id": "...", "mimeType": "image/jpeg"}],
         "originals": [...], "docHasEmbeddedImage": True,
         "docImageDetails": [{"file": "EN_RELEASE.docx", "images": [{"name": "word/media/image1.png", "kind": "logo"}]}],
         "docLogos": True, "docPhotos": False}
    """
    drive = creds.drive()
    media_kit = []
    images = []
    originals = []
    any_embedded = False
    doc_logos = False
    doc_photos = False
    doc_image_details = []
    seen_dirs = set()

    # iterative DFS over subfolders
    stack = [(folder_id, 0)]
    while stack:
        fid, depth = stack.pop()
        if fid in seen_dirs or depth > max_depth:
            continue
        seen_dirs.add(fid)
        try:
            children = _list_children(drive, fid)
        except Exception as e:
            print(f"[drive] list {fid} failed: {e}")
            continue
        for child in children:
            mime = child.get("mimeType", "")
            name = child.get("name", "")
            cid = child.get("id")
            if mime == "application/vnd.google-apps.folder":
                stack.append((cid, depth + 1))
            elif mime.startswith("image/"):
                images.append({"name": name, "id": cid, "mimeType": mime, "size": int(child.get("size", 0) or 0)})
            elif mime in (
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
                "text/plain",
                "text/markdown",
            ) or name.lower().endswith((".pdf", ".docx", ".doc", ".txt", ".md")):
                originals.append({"name": name, "id": cid, "mimeType": mime})
                try:
                    data = _download(drive, cid)
                except Exception as e:
                    print(f"[drive] download {name} failed: {e}")
                    continue
                text = extract_text_from_bytes(data, name)
                if text.strip():
                    # position-aware classification: DOCX header images -> logo,
                    # size-based otherwise.
                    cinfo = classify_doc_images(data, name)
                    if cinfo["has_image"]:
                        any_embedded = True
                        doc_image_details.append({"file": name, "hasImage": True, "images": cinfo["images"], "truncated": cinfo.get("truncated", False)})
                    if cinfo["has_logo"]:
                        doc_logos = True
                    if cinfo["has_photo"]:
                        doc_photos = True
                    media_kit.append({"name": name, "text": text})
    # Cap images to the largest N (highest resolution) to bound downloads.
    images_truncated = len(images) > MAX_DRIVE_IMAGES
    images.sort(key=lambda i: int(i.get("size", 0) or 0), reverse=True)
    images = images[:MAX_DRIVE_IMAGES]

    return {
        "mediaKit": media_kit,
        "images": images,
        "imagesTruncated": images_truncated,
        "originals": originals,
        "docHasEmbeddedImage": any_embedded,
        "docImageDetails": doc_image_details,
        "docLogos": doc_logos,
        "docPhotos": doc_photos,
    }


# Release-vs-speech name signals (multilingual). A release-named doc always
# outranks a longer speech/deck — the HARI EKSPORT case sent the release DOCX
# plus two speeches and the longest-text pick chose a speech.
_RELEASE_WORDS = re.compile(
    r"siaran\s+akhbar|siaran\s+media|kenyataan\s+media|kenyataan\s+akhbar|"
    r"press\s*release|news\s*release|media\s*release|media\s*statement|press\s*statement|"
    r"statement|nota\s+kepada\s+editor|hebahan\s+serta-merta|for\s+immediate\s+release|"
    r"announcement|launch",
    re.I,
)
_SPEECH_WORDS = re.compile(
    r"ucapan|teks\s+ucapan|speech|remarks|keynote|welcoming|opening\s+address|perasmian",
    re.I,
)
# A "report"/"summary" is not the release, even if the name also says "press release".
_REPORT_NAME = re.compile(r"\breport\b|\bsummary\b|\bminutes\b|\bagenda\b|\bappendix\b", re.I)


def _doc_name_score(name):
    """Score a media-kit doc name: +100 release, −100 speech, +10 English."""
    name = name or ""
    score = 0
    if _RELEASE_WORDS.search(name):
        score += 100
    if _SPEECH_WORDS.search(name):
        score -= 100
    if _REPORT_NAME.search(name):
        score -= 60
    if re.search(r"\b(english|en_|eng\b)", name, re.I):
        score += 10
    return score


# Content signals in the first ~1,200 chars. Name rules are strong, but a
# generic filename ("document.pdf") must not lose to a long report/speech.
_RELEASE_TEXT = re.compile(
    r"for\s+immediate\s+release|immediate\s+release|nota\s+kepada\s+editor|"
    r"hebahan\s+serta-merta|siaran\s+akhbar|siaran\s+media|"
    r"kenyataan\s+media|kenyataan\s+akhbar|press\s*release|media\s*release|news\s*release",
    re.I,
)
_SPEECH_TEXT = re.compile(
    r"teks\s+ucapan|ucapan\s+aluan|ucapan\s+perasmian|opening\s+address|"
    r"keynote|welcome\s+remarks|speech\s+by|remarks\s+by",
    re.I,
)
_REPORT_TEXT = re.compile(
    r"executive\s+summary|table\s+of\s+contents|methodology|appendix|figure\s+\d|chapter\s+\d",
    re.I,
)
_DATELINE = re.compile(
    r"\b(kuala\s+lumpur|singapore|jakarta|bangkok|manila|hanoi|phnom\s+penh|yangon|"
    r"asia\s+pacific)[^\n]{0,80}\d{1,2}\s+[A-Za-z]+\s+20\d\d",
    re.I,
)


def _doc_text_score(text):
    """Score the first ~1,200 chars for release / speech / report signals."""
    head = (text or "")[:1200]
    score = 0
    if _RELEASE_TEXT.search(head):
        score += 50
    if _DATELINE.search(head):
        score += 15
    if re.search(r"(?im)^\s*about\s+[A-Z]", head):
        score += 5
    if _SPEECH_TEXT.search(head):
        score -= 50
    if _REPORT_TEXT.search(head):
        score -= 20
    return score


def _doc_score(doc):
    return _doc_name_score(doc.get("name", "")) + _doc_text_score(doc.get("text", ""))


def pick_release_doc(media):
    """Pick the press release from a media kit by NAME + first-paragraph signals.

    Release names (`siaran akhbar`, `press release`, `kenyataan media`, …) win;
    speech names (`ucapan`, `speech`, `remarks`, `perasmian`, …) are pushed down.
    The first ~1,200 chars add release markers (immediate release, dateline,
    media statement) and subtract speech/report markers — so a generic filename
    does not lose to a long report. Fallback: English names, then longest text.

    Example:
        pick_release_doc(kit)
        -> {"name": "[SIARAN AKHBAR] …docx", "text": "NOTA KEPADA EDITOR…"}
    """
    docs = media.get("mediaKit", []) or []
    if not docs:
        return None
    best = max(docs, key=lambda d: (_doc_score(d), len(d.get("text", "") or "")))
    if _doc_score(best) > 0:
        return best
    # No release/speech signal: English first, then longest text.
    english = [d for d in docs if re.search(r"\b(english|en_|eng\b)", d.get("name", ""), re.I)]
    pool = english or docs
    pool = sorted(pool, key=lambda d: len(d.get("text", "") or ""), reverse=True)
    for d in pool:
        if len(d.get("text", "") or "") > 200:
            return d
    return pool[0] if pool else None


# Backward-compatible name (older callers/docs).
pick_english_release = pick_release_doc


def format_media_kit(media):
    """Format ONLY the chosen release for the Extract prompt (token-saver).

    Previously this concatenated every doc in the media kit (EN+BM+ID+programme+deck),
    which was wasteful. Now only the best release text is sent (release-name aware,
    multilingual), plus the image names so the AI knows what media exists.

    Example return:
        "[RELEASE] EN_Lion Parcel Expands.docx\nKUALA LUMPUR, 22 Sept ..."
        "[IMAGES] hero.jpg, logo.png"
    """
    doc = pick_release_doc(media)
    parts = []
    if doc:
        parts.append(f"[RELEASE] {doc['name']}\n{doc['text']}")
    img_names = ", ".join(i["name"] for i in media.get("images", []))
    if img_names:
        parts.append(f"[IMAGES] {img_names}")
    return "\n\n".join(parts)