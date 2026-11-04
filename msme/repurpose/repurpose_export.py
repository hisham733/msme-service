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

from msme import config, paths
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
                  c.subject, c.articleFile
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
            "articleFile": row["articleFile"], "source": str(src), "dest": str(dest),
            "article_hash": row.get("article_hash"), "config_hash": row.get("config_hash"),
            "weighted": row.get("weighted"),
        })
        if not apply:
            continue
        if dest.exists() and ((dest / "run.json").exists() or (dest / "draft.md").exists()):
            plan[-1]["status"] = "skip"
            plan[-1]["reason"] = "engine work already exists"
            continue
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        shutil.copy2(article, dest / article.name)
        n_images = _copy_tree(src / "images", dest / "images")
        n_originals = _copy_tree(src / "originals", dest / "originals")
        link = src / "link.md"
        if link.is_file():
            shutil.copy2(link, dest / "link.md")
        plan[-1]["images"] = n_images
        plan[-1]["originals"] = n_originals
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
