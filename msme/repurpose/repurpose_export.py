# =============================================================================
# FILE HEADER
# file    : msme/repurpose/repurpose_export.py
# role    : Adapter — export accepted filter results to the Repurpose engine contract
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : pick the latest ACCEPT filter result per article, copy its archived article/images/
#           originals into repurpose_inbox/<subject>/, and write data/repurpose_export.json.
# pages   : n/a (the engine dashboard :8765 reads the exported tree)
# calls   : sqlite3, config.SQLITE_PATH, archive._clean_subject, shutil/json/hashlib
# called  : operator CLI: python3 repurpose_export.py [--apply]
# amend   : never modify the engine or all_emails; export only copies. One folder = one article.
#           Test: python3 repurpose_export.py --apply, then engine preflight.
# =============================================================================
"""Export accepted checklist articles to the external Repurpose engine.

The engine reads one folder per article:
    repurpose_inbox/<subject>/<release>.md + images/ + originals/ + optional link.md

We do NOT copy rejected/editor-review articles, date buckets, _duplicates or _no_article.
The latest filter version wins; an older ACCEPT is not exported if the latest is REJECT.
"""
import argparse
import json
import shutil
import sqlite3
from pathlib import Path

from msme import config, db, paths
from msme.receive import archive

ROOT = paths.ROOT
ARCHIVE_ROOT = paths.ARCHIVE
INBOX = paths.REPURPOSE_INBOX
MANIFEST = paths.DATA / "repurpose_export.json"


def _connect():
    c = sqlite3.connect(config.SQLITE_PATH)
    c.row_factory = sqlite3.Row
    return c


def _accepted_latest():
    """Latest filter version per article key; keep only it if its outcome is ACCEPT."""
    c = _connect()
    rows = c.execute(
        """select f.id, f.checklist_id, f.threadId, f.outcome, f.weighted,
                  f.article_hash, f.config_hash, f.created_at,
                  c.subject, c.articleFile, c.messageId
           from filter_results f join checklist c on c.id = f.checklist_id
           order by f.id desc"""
    ).fetchall()
    c.close()
    latest = {}
    for r in rows:
        d = dict(r)
        key = d.get("articleFile") or d.get("threadId") or str(d["checklist_id"])
        if key not in latest:
            latest[key] = d
    return [v for v in latest.values() if v.get("outcome") == "ACCEPT"]


def _source_folder(article_file):
    if not article_file:
        return None
    hits = [p for p in ARCHIVE_ROOT.rglob(article_file) if p.is_file()]
    if not hits:
        return None

    def rank(p):
        parts = p.parent.parts
        if "_duplicates" in parts or "_no_article" in parts:
            return (-1, 0)
        bucket = 2 if any(x.startswith("received-") for x in parts) else 1
        return (bucket, p.stat().st_mtime)

    return max(hits, key=rank).parent


def _safe_dest_name(row):
    name = archive._clean_subject(row.get("subject") or row.get("articleFile") or "article")
    if not name:
        name = "article"
    return name


def _copy_tree(src_dir, dest_dir):
    if not src_dir.is_dir():
        return 0
    dest_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in sorted(src_dir.iterdir()):
        if p.is_file():
            shutil.copy2(p, dest_dir / p.name)
            n += 1
    return n


def _write_meta(dest, report_url, speech_url):
    """Write the engine's meta.json (report/speech link). Safe to call on an existing folder."""
    if not (report_url or speech_url):
        return False
    meta = {}
    if report_url:
        meta["articleType"] = "report"
        meta["reportUrl"] = report_url
    if speech_url:
        meta.setdefault("articleType", "government_summary")
        meta["speechUrl"] = speech_url
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


def _media_source(row):
    """The archived file for one email_media row (uses `path`, else searches the archive)."""
    raw = str(row.get("path") or row.get("name") or "").strip()
    if not raw:
        return None
    p = Path(raw)
    if p.is_file():
        return p
    name = Path(raw).name
    hits = [h for h in ARCHIVE_ROOT.rglob(name) if h.is_file()]
    if not hits:
        return None
    hits.sort(key=lambda h: h.stat().st_mtime, reverse=True)
    return hits[0]


def _copy_media(dest, media_rows):
    """Copy the email's indexed media (from `email_media`) into `dest/images/`.

    This is the table-driven bridge: the image the receive stage chose (including the
    N-1 gallery fallback) is copied from its stored path, not from a guessed folder.
    """
    n = 0
    if not media_rows:
        return n
    images = dest / "images"
    images.mkdir(parents=True, exist_ok=True)
    for row in media_rows:
        src = _media_source(row)
        if not src:
            continue
        target = images / src.name
        if target.exists():
            continue
        try:
            shutil.copy2(src, target)
            n += 1
        except Exception as e:
            print(f"[export] media copy failed {src.name}: {e}")
    return n


def export(apply=False):
    rows = _accepted_latest()
    plan = []
    used = set()
    for row in rows:
        src = _source_folder(row.get("articleFile"))
        if not src:
            plan.append({"checklist_id": row["checklist_id"], "status": "skip",
                         "reason": "archive folder not found", "articleFile": row.get("articleFile")})
            continue
        name = _safe_dest_name(row)
        if name in used:
            name = f"{name}-{row['checklist_id']}"
        used.add(name)
        dest = INBOX / name
        article = src / row["articleFile"]
        if not article.is_file():
            plan.append({"checklist_id": row["checklist_id"], "status": "skip",
                         "reason": "article file missing", "source": str(src)})
            continue
        plan.append({
            "status": "export", "checklist_id": row["checklist_id"],
            "filter_result_id": row["id"], "subject": row.get("subject"),
            "messageId": row.get("messageId", ""),
            "articleFile": row["articleFile"], "source": str(src), "dest": str(dest),
            "article_hash": row.get("article_hash"), "config_hash": row.get("config_hash"),
            "weighted": row.get("weighted"),
        })
        # N-3/N-4: report / speech link captured for this email.
        links = db.primary_links(row.get("messageId") or "")
        report_url = links.get("report", "")
        speech_url = links.get("speech", "")
        plan[-1]["reportUrl"] = report_url
        plan[-1]["speechUrl"] = speech_url
        # Table-driven media: the receive stage's chosen media (incl. the gallery fallback).
        media_rows = db.list_email_media(row.get("messageId") or "")
        if not apply:
            continue
        if dest.exists() and ((dest / "run.json").exists() or (dest / "draft.md").exists()):
            # keep the engine work; add any missing media + the link so the next build can pass.
            _write_meta(dest, report_url, speech_url)
            added = _copy_media(dest, media_rows)
            plan[-1]["status"] = "skip"
            plan[-1]["reason"] = "engine work already exists"
            if added:
                plan[-1]["reason"] += f" (added {added} media)"
            continue
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        shutil.copy2(article, dest / article.name)
        n_images = _copy_media(dest, media_rows) if media_rows else _copy_tree(src / "images", dest / "images")
        n_originals = _copy_tree(src / "originals", dest / "originals")
        link = src / "link.md"
        if link.is_file():
            shutil.copy2(link, dest / "link.md")
        # N-3/N-4 engine bridge: the link the validator forbids in draft.md.
        _write_meta(dest, report_url, speech_url)
        plan[-1]["images"] = n_images
        plan[-1]["originals"] = n_originals
        try:
            db.save_repurpose_export(
                row["checklist_id"], row["id"], folder=name, dest=str(dest),
                article_hash=row.get("article_hash") or "",
                config_hash=row.get("config_hash") or "",
                weighted=row.get("weighted"), status="exported",
            )
        except Exception as e:
            print(f"[export] DB record failed for cid={row['checklist_id']}: {e}")
        plan[-1]["dest"] = str(dest)

    if apply:
        INBOX.mkdir(parents=True, exist_ok=True)
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps({"exported": plan}, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
    return plan


def main():
    ap = argparse.ArgumentParser(description="Export latest ACCEPT results to repurpose_inbox")
    ap.add_argument("--apply", action="store_true", help="write/copy (default: dry-run)")
    args = ap.parse_args()
    plan = export(apply=args.apply)
    for p in plan:
        if p.get("status") == "export":
            print(f"EXPORT cid={p['checklist_id']} result={p['filter_result_id']} "
                  f"weighted={p.get('weighted')} -> {p['dest']} "
                  f"(images={p.get('images', '?')}, originals={p.get('originals', '?')})")
        else:
            print(f"SKIP   cid={p['checklist_id']} {p.get('reason')}")
    print(f"\n{'APPLIED' if args.apply else 'DRY-RUN'} · {sum(1 for p in plan if p['status']=='export')} "
          f"accepted article(s) · inbox={INBOX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
