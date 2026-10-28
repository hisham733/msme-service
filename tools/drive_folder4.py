# =============================================================================
# FILE HEADER
# file    : tools/drive_folder4.py
# role    : Ops — publish 20 local articles to Drive Email_Articles/4
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : select local all_emails articles that are already published on the MSME site AND
#           readyToFilter=true (latest checklist row) but not yet in Drive 1/2/3, then upload each
#           folder with article.md + images/ + originals/ + link.md under Drive folder 4. --sync
#           trashes old children of 4 that are not in the new selection. 1/2/3 are never modified.
# pages   : n/a
# calls   : creds.drive, google-api-python-client, docs/published-index.json, all_emails
# called  : developer / operator: --select, then --apply --yes
# amend   : --select is read-only; --apply creates/updates Email_Articles/4; --sync also trashes
#           old 4-only folders not in the selection (1/2/3 untouched). readyToFilter must be true.
#           Test: python3 tools/drive_folder4.py --select
# =============================================================================
"""Publish new MSME articles from all_emails into Drive Email_Articles/4.

    python3 tools/drive_folder4.py --select              # match, write docs/DRIVE-FOLDER-4-SELECTION.json
    python3 tools/drive_folder4.py --apply --yes         # create 4 + upload the selected folders

Selection: local kept articles matched to docs/published-index.json by title/body,
excluding anything already in Drive 1/2/3; newest 20 with a valid MSME URL.
"""
import argparse
import io
import json
import mimetypes
import os
import sqlite3
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from googleapiclient.errors import HttpError
from httplib2 import ServerNotFoundError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

import config
import creds

DRIVE_ROOT = "1FBDLuI9mhMKioX4piwjtPe8BmQEIncTV"   # Email_Articles
FOLDER_MIME = "application/vnd.google-apps.folder"
SELECTION = ROOT_DIR / "docs" / "DRIVE-FOLDER-4-SELECTION.json"
LIMIT = 20
MAX_FILE_MB = 0          # 0 = no cap
SKIP_DIRS = {"_duplicates", "_no_article"}


def svc():
    return creds.drive()


def kids(service, fid):
    out = []
    token = None
    while True:
        for attempt in range(5):
            try:
                r = service.files().list(
                    q=f"'{fid}' in parents and trashed=false",
                    pageSize=200,
                    fields="nextPageToken,files(id,name,mimeType,size,webViewLink,modifiedTime)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                    pageToken=token,
                ).execute()
                break
            except (ServerNotFoundError, OSError) as e:
                if attempt < 4:
                    time.sleep(2 ** attempt)
                    continue
                raise
        out += r.get("files", [])
        token = r.get("nextPageToken")
        if not token:
            break
    return out


def read_text(service, fid):
    try:
        return service.files().get_media(fileId=fid, supportsAllDrives=True).execute().decode(
            "utf-8", "replace")
    except Exception:
        return ""


def tokens(s):
    return set(re.findall(r"[a-z0-9]+", (s or "").lower()))


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def title_of(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    skip = ("for immediate release", "press release", "news release", "media release",
            "note to editors", "media contact")
    for line in lines[:8]:
        low = line.lower()
        if any(low.startswith(s) for s in skip):
            continue
        if re.match(r"^[A-Z ]+,\s*\d", line):
            continue
        return line
    return ""


def ready_map():
    """article .md basename -> readyToFilter is true (receive stage passed)."""
    out = {}
    db = os.environ.get("SQLITE_PATH") or getattr(config, "SQLITE_PATH", "data/msme.sqlite3")
    try:
        con = sqlite3.connect(db)
        for af, ready in con.execute("select articleFile, readyToFilter from checklist"):
            out[os.path.basename(af or "").lower()] = str(ready).lower() == "true"
        con.close()
    except Exception as e:
        print(f"WARNING: cannot read checklist DB ({e}); no article will be ready")
    return out


def local_articles():
    out = []
    ready = ready_map()
    for dp, dirs, files in os.walk(ROOT_DIR / "all_emails"):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith((".", "_"))]
        mds = [f for f in files if f.lower().endswith(".md") and f.lower() != "link.md"]
        if not mds:
            continue
        md = max(mds, key=lambda f: os.path.getsize(os.path.join(dp, f)))
        try:
            text = open(os.path.join(dp, md), encoding="utf-8", errors="replace").read()
        except Exception:
            text = ""
        images = os.listdir(os.path.join(dp, "images")) if os.path.isdir(os.path.join(dp, "images")) else []
        originals = os.listdir(os.path.join(dp, "originals")) if os.path.isdir(os.path.join(dp, "originals")) else []
        size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(dp) for f in fs)
        out.append({
            "folder": os.path.basename(dp),
            "path": str(Path(dp)),
            "md": md,
            "title": title_of(text),
            "text": text[:9000],
            "images": len(images),
            "originals": len(originals),
            "size": size,
            "ready": ready.get(md.lower(), False),
        })
    return out


def drive_existing(service):
    names, articles, urls = set(), set(), set()
    for top in kids(service, DRIVE_ROOT):
        if (top.get("name") or "") not in ("1", "2", "3"):
            continue
        if (top.get("mimeType") or "") != FOLDER_MIME:
            continue
        for f in kids(service, top["id"]):
            if (f.get("mimeType") or "") != FOLDER_MIME:
                continue
            names.add((f.get("name") or "").strip().lower())
            children = kids(service, f["id"])
            for c in children:
                nm = (c.get("name") or "").lower()
                if nm.endswith(".md") and nm != "link.md":
                    articles.add(nm)
                if nm == "link.md":
                    u = read_text(service, c["id"]).strip().splitlines()
                    if u:
                        urls.add(u[0])
    return names, articles, urls


def select(service):
    published = json.load(open(ROOT_DIR / "docs" / "published-index.json", encoding="utf-8"))
    dataset = {x["url"]: x for x in json.load(open(ROOT_DIR / "docs" / "published-dataset.json",
                                                   encoding="utf-8"))}
    drive_names, drive_articles, drive_urls = drive_existing(service)
    locals_ = local_articles()
    remaining = [p for p in published if p["url"] not in drive_urls]
    candidates = []
    for p in remaining:
        pt = tokens(p["title"])
        pb = tokens(dataset.get(p["url"], {}).get("bodyText", ""))
        best, best_score, best_t, best_b = None, 0.0, 0.0, 0.0
        for L in locals_:
            if not L.get("ready"):
                continue
            if L["folder"].strip().lower() in drive_names:
                continue
            if L["md"].lower() in drive_articles:
                continue
            ts = jaccard(pt, tokens(L["title"]))
            body = jaccard(pb, tokens(L["text"]))
            score = max(ts, body)
            if score > best_score:
                best, best_score, best_t, best_b = L, score, ts, body
        if best and (best_t >= 0.40 or best_b >= 0.45):
            candidates.append((p, best, best_score, best_t, best_b))
    by_md = {}
    for c in candidates:
        key = c[1]["md"].lower()
        if key not in by_md or c[2] > by_md[key][2]:
            by_md[key] = c
    selected = sorted(by_md.values(), key=lambda x: (x[0].get("date", ""), x[2]), reverse=True)[:LIMIT]
    out = []
    for p, L, score, ts, body in selected:
        out.append({
            "published_title": p["title"],
            "published_date": p.get("date", ""),
            "url": p["url"],
            "local_folder": L["folder"],
            "local_path": L["path"],
            "article_md": L["md"],
            "images": L["images"],
            "originals": L["originals"],
            "size": L["size"],
            "match": {"score": round(score, 3), "title": round(ts, 3), "body": round(body, 3)},
        })
    SELECTION.parent.mkdir(parents=True, exist_ok=True)
    with open(SELECTION, "w", encoding="utf-8") as f:
        json.dump({"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "drive_root": DRIVE_ROOT, "items": out}, f, ensure_ascii=False, indent=2)
    print(f"selected {len(out)} -> {SELECTION}")
    for i, x in enumerate(out, 1):
        print(f"{i:2}. {'NEW' if not x['match'] else ''} {x['published_date'][:10]} | "
              f"{x['published_title'][:66]}")
        print(f"    local: {x['local_folder'][:70]}")
        print(f"    url  : {x['url']}")
        print(f"    imgs={x['images']} origs={x['originals']} {x['size']//1024}KB "
              f"match={x['match']['score']}")
    return out


def find_child(service, parent, name, mime=None):
    for f in kids(service, parent):
        if (f.get("name") or "") == name and (mime is None or f.get("mimeType") == mime):
            return f
    return None


def create_folder(service, name, parent):
    body = {"name": name, "mimeType": FOLDER_MIME, "parents": [parent]}
    return service.files().create(body=body, fields="id,name,webViewLink",
                                  supportsAllDrives=True).execute()


def upload_file(service, local_path, name, parent, mime=None):
    size = os.path.getsize(local_path)
    mime = mime or mimetypes.guess_type(name)[0] or "application/octet-stream"
    for attempt in range(5):
        try:
            media = MediaFileUpload(local_path, mimetype=mime, resumable=size > 5 * 1024 * 1024)
            body = {"name": name, "parents": [parent]}
            return service.files().create(body=body, media_body=media,
                                          fields="id,name,size", supportsAllDrives=True).execute()
        except HttpError as e:
            if e.resp.status in (403, 429, 500, 502, 503) and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise
        except Exception:
            if attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError("upload retries exhausted")


def update_text(service, text, name, parent, mime="text/markdown"):
    """Create or replace a small text file (e.g. _LINKS.md)."""
    data = io.BytesIO(text.encode("utf-8"))
    media = MediaIoBaseUpload(data, mimetype=mime, resumable=False)
    existing = find_child(service, parent, name)
    if existing:
        return service.files().update(fileId=existing["id"], media_body=media,
                                      fields="id,name,size").execute()
    return service.files().create(body={"name": name, "parents": [parent]},
                                  media_body=media, fields="id,name,size",
                                  supportsAllDrives=True).execute()


def trash_child(service, parent, name):
    f = find_child(service, parent, name, FOLDER_MIME)
    if not f:
        return None
    service.files().update(fileId=f["id"], body={"trashed": True},
                           fields="id,name").execute()
    return f


def apply(selection, previous=None):
    service = svc()
    total = sum(x["size"] for x in selection)
    print(f"uploading {len(selection)} folders, {total/1024/1024:.1f} MB")
    four = find_child(service, DRIVE_ROOT, "4", FOLDER_MIME)
    if four:
        print("reusing existing 4:", four["id"])
    else:
        four = create_folder(service, "4", DRIVE_ROOT)
        print("created 4:", four["id"], four.get("webViewLink"))
    report = []
    for i, item in enumerate(selection, 1):
        local = Path(item["local_path"])
        if not local.is_dir():
            report.append({**item, "status": "missing_local"})
            print(f"[{i:2}] MISSING {local}")
            continue
        child = find_child(service, four["id"], item["local_folder"], FOLDER_MIME)
        if child:
            print(f"[{i:2}] reusing folder {item['local_folder'][:60]}")
        else:
            child = create_folder(service, item["local_folder"], four["id"])
        images = find_child(service, child["id"], "images", FOLDER_MIME) or \
            create_folder(service, "images", child["id"])
        originals = find_child(service, child["id"], "originals", FOLDER_MIME) or \
            create_folder(service, "originals", child["id"])
        uploaded = 0
        size = 0
        article = local / item["article_md"]
        if article.exists() and not find_child(service, child["id"], item["article_md"]):
            res = upload_file(service, str(article), item["article_md"], child["id"], "text/markdown")
            uploaded += 1
            size += int(res.get("size", 0) or 0)
        for sub, fid in (("images", images["id"]), ("originals", originals["id"])):
            d = local / sub
            if d.is_dir():
                for name in sorted(os.listdir(d)):
                    p = d / name
                    if not p.is_file():
                        continue
                    if find_child(service, fid, name):
                        continue
                    res = upload_file(service, str(p), name, fid)
                    uploaded += 1
                    size += int(res.get("size", 0) or 0)
        link = find_child(service, child["id"], "link.md")
        if not link:
            update_text(service, item["url"] + "\n", "link.md", child["id"])
            uploaded += 1
            size += len(item["url"]) + 1
        report.append({**item, "drive_id": child["id"],
                       "drive_url": child.get("webViewLink") or
                       ("https://drive.google.com/drive/folders/" + child["id"]),
                       "uploaded_files": uploaded, "uploaded_bytes": size,
                       "status": "ok"})
        print(f"[{i:2}/20] {item['local_folder'][:60]} -> {uploaded} files, {size//1024} KB")
    # index
    lines = ["# Folder 4 — published MSME articles", "",
             "| # | Article | Local folder | MSME link |", "|---:|---|---|---|"]
    for i, x in enumerate(selection, 1):
        lines.append(f"| {i} | {x['published_title']} | {x['local_folder']} | {x['url']} |")
    update_text(service, "\n".join(lines) + "\n", "_LINKS.md", four["id"])

    trashed = []
    if previous:
        new_names = {x["local_folder"] for x in selection}
        for old in previous:
            if old["local_folder"] in new_names:
                continue
            f = trash_child(service, four["id"], old["local_folder"])
            if f:
                trashed.append({"name": old["local_folder"], "id": f["id"],
                                "url": old.get("url", "")})
                print("trashed (not in new selection):", old["local_folder"][:70])
    # manifest
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    manifest = ROOT_DIR / "docs" / f"DRIVE-FOLDER-4-{stamp}.json"
    with open(manifest, "w", encoding="utf-8") as f:
        json.dump({"created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "drive_root": DRIVE_ROOT, "folder4_id": four["id"],
                   "folder4_url": four.get("webViewLink") or
                   ("https://drive.google.com/drive/folders/" + four["id"]),
                   "items": report, "trashed": trashed}, f, ensure_ascii=False, indent=2)
    md = manifest.with_suffix(".md")
    with open(md, "w", encoding="utf-8") as f:
        f.write(f"# Drive folder 4 — {len(report)} published articles\n\n")
        f.write(f"- folder: {four.get('webViewLink') or four['id']}\n")
        f.write(f"- generated: {stamp} UTC\n\n")
        if trashed:
            f.write("\n## Removed (not ready to filter)\n\n")
            for t in trashed:
                f.write(f"- {t['name']}\n")
            f.write("\n")
        f.write("| # | Local folder | Article | MSME link | Files | Status |\n")
        f.write("|---:|---|---|---|---:|---|\n")
        for i, x in enumerate(report, 1):
            f.write(f"| {i} | {x['local_folder']} | {x['article_md']} | {x['url']} | "
                    f"{x.get('uploaded_files', 0)} | {x['status']} |\n")
    print("manifest:", manifest)
    print("done:", len([x for x in report if x["status"] == "ok"]),
          "ok | trashed:", len(trashed))
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--sync", action="store_true",
                    help="upload the selection and trash old items not in it")
    ap.add_argument("--previous", default=str(ROOT_DIR / "docs" / "DRIVE-FOLDER-4-SELECTION-v1.json"))
    ap.add_argument("--yes", action="store_true")
    args = ap.parse_args(argv)
    service = svc()
    if args.select:
        if args.apply:
            raise SystemExit("choose --select or --apply, not both")
        select(service)
        return 0
    if args.apply or args.sync:
        if not SELECTION.exists():
            raise SystemExit(f"missing {SELECTION}; run --select first")
        selection = json.load(open(SELECTION, encoding="utf-8"))["items"]
        if len(selection) != LIMIT:
            print(f"warning: selection has {len(selection)} items, expected {LIMIT}")
        if not args.yes:
            try:
                ans = input(f"Upload {len(selection)} folders to Drive 4? [y/N] ").strip().lower()
            except EOFError:
                ans = ""
            if ans not in ("y", "yes"):
                print("aborted")
                return 1
        previous = None
        if args.sync and os.path.exists(args.previous):
            previous = json.load(open(args.previous, encoding="utf-8"))["items"]
            print(f"sync: previous selection {len(previous)} items")
        apply(selection, previous=previous)
        return 0
    raise SystemExit("use --select or --apply")


if __name__ == "__main__":
    raise SystemExit(main())
