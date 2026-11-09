#!/usr/bin/env python3
"""Gallery admin — inspect a match or add a logo to the local N-1 gallery.

Examples:
    python3 tools/gallery_admin.py check \
      --from "noreply@cision.com" --subject "Bank Pembangunan Malaysia Berhad launches..." \
      --body "Bank Pembangunan Malaysia Berhad (BPMB) today announced..."

    python3 tools/gallery_admin.py add \
      --file /path/to/BPMB_11-November-2026_MALAYSIA-SME.png \
      --brand BPMB --aliases "BPMB,Bank Pembangunan Malaysia" --domain bpmb.com.my

The gallery is local (`data/gallery/`), no network and no AI. `check` is read-only;
`add` copies the image and updates `index.json`; `promote`/`discard` accept or discard
a captured N-2 library update (`data/gallery/updates/<id>/`).
"""
import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from msme import config, paths
from msme.receive import gallery


def _index_path():
    return Path(config.GALLERY_INDEX)


def _load_raw():
    path = _index_path()
    if not path.exists():
        return {"version": 1, "updated": "", "images": []}
    return json.loads(path.read_text(encoding="utf-8"))


def check(args):
    email = {
        "subject": args.subject,
        "from_name": args.name,
        "from_email": args.sender,
        "filenames": [f for f in (args.filenames or "").split(",") if f.strip()],
        "body": args.body,
    }
    result = gallery.match(email, gallery.load_index(args.index))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") == "hit" else 1


def add(args):
    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        print(f"ERROR: file not found: {source}", file=sys.stderr)
        return 2
    if source.stat().st_size > config.GALLERY_MAX_FILE_BYTES:
        print("ERROR: file is larger than GALLERY_MAX_FILE_BYTES", file=sys.stderr)
        return 2
    gallery_dir = Path(config.GALLERY_DIR)
    gallery_dir.mkdir(parents=True, exist_ok=True)
    target = gallery_dir / source.name
    if target.exists() and target.resolve() != source:
        print(f"ERROR: {target.name} already exists in the gallery", file=sys.stderr)
        return 2
    if target.resolve() != source:
        shutil.copy2(source, target)

    data = _load_raw()
    images = data.setdefault("images", [])
    brand = args.brand.strip()
    # A newer logo supersedes the older active one for the same brand/type.
    for entry in images:
        if (str(entry.get("brand") or "").lower() == brand.lower()
                and str(entry.get("type") or "logo").lower() == args.type
                and str(entry.get("status") or "active").lower() == "active"):
            entry["status"] = "superseded"
    aliases = [a.strip() for a in (args.aliases or brand).split(",") if a.strip()]
    if brand not in aliases:
        aliases.insert(0, brand)
    domains = [d.strip().lower() for d in (args.domain or "").split(",") if d.strip()]
    updated = datetime.now(timezone.utc).date().isoformat()
    entry = {
        "id": args.id or f"{brand.lower().replace(' ', '-')}-{updated}",
        "brand": brand,
        "aliases": aliases,
        "domains": domains,
        "type": args.type,
        "file": target.name,
        "updated": updated,
        "status": "active",
        "source": "tools/gallery_admin.py add",
    }
    images.append(entry)
    data["updated"] = updated
    _index_path().parent.mkdir(parents=True, exist_ok=True)
    _index_path().write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
    print(json.dumps(entry, indent=2, ensure_ascii=False))
    return 0


def promote(args):
    """Accept a pending library update: promote its logo files into the active index."""
    base = Path(config.GALLERY_UPDATES_DIR) / args.id
    meta_path = base / "update.json"
    if not meta_path.is_file():
        print(f"ERROR: no update '{args.id}' under {config.GALLERY_UPDATES_DIR}", file=sys.stderr)
        return 2
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    data = _load_raw()
    images = data.setdefault("images", [])
    brand = (args.brand or meta.get("brand") or "").strip()
    if not brand:
        print("ERROR: the update has no brand; pass --brand", file=sys.stderr)
        return 2
    aliases = [a.strip() for a in (args.aliases or meta.get("aliases") or "").split(",") if a.strip()]
    if not aliases and (meta.get("aliases") or []):
        aliases = list(meta["aliases"])
    if brand not in aliases:
        aliases.insert(0, brand)
    domains = [d.strip().lower() for d in (args.domain or "").split(",") if d.strip()]
    if not domains and (meta.get("domains") or []):
        domains = list(meta["domains"])

    promoted = 0
    for rec in meta.get("files") or []:
        if str(rec.get("kind") or "") != "logo":
            continue
        fname = rec.get("name") or ""
        src = base / "images" / fname
        if not src.is_file():
            continue
        raw = src.read_bytes()
        ext = ("svg" if fname.lower().endswith(".svg") or raw.lstrip().startswith(b"<svg")
               else "png" if raw[:8] == b"\x89PNG\r\n\x1a\n" else "jpg")
        dest_name = gallery.gallery_name(brand, ext=ext)
        (Path(config.GALLERY_DIR) / dest_name).write_bytes(raw)
        gallery.supersede_brand(images, brand, "logo")
        updated = datetime.now(timezone.utc).date().isoformat()
        images.append({
            "id": f"{brand.lower().replace(' ', '-')}-{updated}",
            "brand": brand, "aliases": aliases, "domains": domains,
            "type": "logo", "file": dest_name, "updated": updated,
            "status": "active", "source": "gallery_admin promote",
        })
        rec["promoted"] = True
        rec["promotionBlockedReason"] = ""
        promoted += 1

    meta["status"] = "active" if promoted else meta.get("status")
    gallery.write_index(data)
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"id": args.id, "brand": brand, "promoted": promoted}, indent=2,
                     ensure_ascii=False))
    return 0 if promoted else 1


def discard(args):
    """Mark a stored library update as discarded (kept for history, never promoted)."""
    base = Path(config.GALLERY_UPDATES_DIR) / args.id
    meta_path = base / "update.json"
    if not meta_path.is_file():
        print(f"ERROR: no update '{args.id}' under {config.GALLERY_UPDATES_DIR}", file=sys.stderr)
        return 2
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["status"] = "discarded"
    meta["notes"] = (args.note or "discarded")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"id": args.id, "status": "discarded"}, indent=2))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="N-1 logo gallery admin")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="dry-run a match")
    c.add_argument("--from", dest="sender", default="", help="sender email")
    c.add_argument("--name", default="", help="sender display name")
    c.add_argument("--subject", default="")
    c.add_argument("--body", default="")
    c.add_argument("--filenames", default="", help="comma-separated attachment filenames")
    c.add_argument("--index", default=None, help="index path (default GALLERY_INDEX)")
    c.set_defaults(func=check)

    a = sub.add_parser("add", help="copy a logo and add/replace its index entry")
    a.add_argument("--file", required=True)
    a.add_argument("--brand", required=True)
    a.add_argument("--aliases", default="", help="comma-separated")
    a.add_argument("--domain", default="", help="comma-separated domains")
    a.add_argument("--type", default="logo", choices=("logo", "photo"))
    a.add_argument("--id", default="")
    a.set_defaults(func=add)

    p = sub.add_parser("promote", help="promote a pending library update's logos into the index")
    p.add_argument("id")
    p.add_argument("--brand", default="", help="override the brand (needed for a new brand)")
    p.add_argument("--aliases", default="", help="comma-separated")
    p.add_argument("--domain", default="", help="comma-separated domains")
    p.set_defaults(func=promote)

    d = sub.add_parser("discard", help="mark a stored library update as discarded")
    d.add_argument("id")
    d.add_argument("--note", default="", help="why it was discarded")
    d.set_defaults(func=discard)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
