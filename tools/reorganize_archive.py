# =============================================================================
# FILE HEADER
# file    : tools/reorganize_archive.py
# role    : Ops — sort all_emails into received-date buckets, one version per group
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : keep the newest complete copy of each subject, move older copies to _duplicates/,
#           and place the kept copy in received-<cutoff>-(above|below)/ by received date.
# pages   : n/a
# calls   : archive_layout (version grouping + date map), os, shutil, json, argparse
# called  : developer / operator — dry-run first, then --apply
# amend   : never deletes; every move is written to a manifest. Re-run is a no-op for sorted folders.
#           Test: python3 tools/reorganize_archive.py --dry-run
# =============================================================================
"""Reorganise the live email archive by received date.

Layout after --apply:
    all_emails/received-2026-10-15-and-above/<subject>/
    all_emails/received-2026-10-14-and-below/<subject>/
    all_emails/_duplicates/<group>/<older version>/
    all_emails/_no_article/<folder with no article .md>/

Dry-run (default) prints the plan and writes the manifest; no folder moves.
"""
import argparse
import datetime as _dt
import json
import os
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from msme.receive import archive_layout as AL

DEFAULT_ROOT = "all_emails"
DEFAULT_CUTOFF = "2026-10-15"


def _article(folder):
    return AL.article_md(str(folder))


def _date_maps():
    docs = ROOT_DIR / "docs"
    data = ROOT_DIR / "data"
    return AL.build_date_map(str(docs), str(data), str(data / "msme.sqlite3"))


def scan(root, cutoff):
    """Return (plan, groups) without moving anything."""
    date_map = _date_maps()
    root = Path(root)
    names = sorted(n for n in os.listdir(root)
                   if os.path.isdir(root / n) and not n.startswith(("_", ".")))
    buckets = {
        "above": f"received-{cutoff}-and-above",
        "below": f"received-{_day_before(cutoff)}-and-below",
    }
    groups = {}
    for name in names:
        if name in buckets.values():
            continue
        groups.setdefault(AL.version_base(name), []).append(name)

    plan = []
    for base, versions in sorted(groups.items()):
        items = []
        for name in versions:
            folder = root / name
            md = _article(folder)
            items.append({
                "name": name,
                "path": folder,
                "md": md,
                "mtime": os.stat(folder).st_mtime,
                "chars": _chars(folder / md) if md else 0,
            })
        picked = max((i for i in items if i["md"]),
                     key=lambda i: (i["mtime"], i["chars"]), default=None)
        if picked is None:
            for item in items:
                plan.append({"src": str(item["path"]),
                             "dst": str(root / "_no_article" / item["name"]),
                             "group": base, "action": "no_article", "date": "", "source": ""})
            continue
        date, source = AL.received_date(picked["name"], picked["md"], date_map)
        if not date:
            date = AL.parse_date("", mtime=picked["mtime"])
            source = "mtime"
        bucket = buckets["above"] if date >= cutoff else buckets["below"]
        plan.append({"src": str(picked["path"]),
                     "dst": str(root / bucket / picked["name"]),
                     "group": base, "action": "keep", "date": date, "source": source})
        for item in items:
            if item is picked:
                continue
            plan.append({"src": str(item["path"]),
                         "dst": str(root / "_duplicates" / base / item["name"]),
                         "group": base, "action": "duplicate", "date": date, "source": source})
    return plan, groups


def _chars(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return len(f.read())
    except Exception:
        return 0


def _day_before(iso_date):
    return (_dt.date.fromisoformat(iso_date) - _dt.timedelta(days=1)).isoformat()


def check_conflicts(plan):
    seen = {}
    conflicts = []
    for move in plan:
        dst = move["dst"]
        if os.path.exists(dst):
            conflicts.append(f"destination exists: {dst}")
        if dst in seen:
            conflicts.append(f"two moves target {dst}")
        seen[dst] = move["src"]
    return conflicts


def apply(plan):
    for move in plan:
        dst = Path(move["dst"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        src = Path(move["src"])
        try:
            os.rename(src, dst)
        except OSError:
            shutil.move(str(src), str(dst))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--cutoff", default=DEFAULT_CUTOFF)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="plan only (default)")
    ap.add_argument("--manifest", default="/tmp/opencode/reorganize_archive.json")
    args = ap.parse_args(argv)

    plan, groups = scan(args.root, args.cutoff)
    conflicts = check_conflicts(plan)
    counts = {}
    for move in plan:
        counts[move["action"]] = counts.get(move["action"], 0) + 1
    dates = {}
    for move in plan:
        if move["action"] == "keep":
            dates[move["date"]] = dates.get(move["date"], 0) + 1

    print(f"root={args.root} cutoff={args.cutoff} groups={len(groups)} moves={len(plan)}")
    print(f"actions={counts}")
    print(f"kept dates: from {min(dates) if dates else '-'} to {max(dates) if dates else '-'}")
    above = sum(1 for m in plan if m["action"] == "keep" and m["date"] >= args.cutoff)
    below = sum(1 for m in plan if m["action"] == "keep" and m["date"] < args.cutoff)
    print(f"keep buckets: above={above} below={below}")
    if conflicts:
        print("CONFLICTS — no move performed:")
        for c in conflicts[:20]:
            print("  " + c)
        return 2

    manifest = os.path.abspath(args.manifest)
    os.makedirs(os.path.dirname(manifest), exist_ok=True)
    with open(manifest, "w", encoding="utf-8") as f:
        json.dump({"root": args.root, "cutoff": args.cutoff, "plan": plan}, f,
                  ensure_ascii=False, indent=2)
    print(f"manifest={manifest}")

    if not args.apply:
        print("DRY-RUN — nothing moved. Re-run with --apply to execute.")
        return 0

    apply(plan)
    print(f"APPLIED {len(plan)} moves")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
