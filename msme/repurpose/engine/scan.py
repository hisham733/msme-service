"""scan.py — work queue over the receive folders (assume post-filter).

A release folder (one article) looks like:
    <Email_Articles>/<release folder>/  containing  <slug>.md (release text), Link.md/link.md,
    images/, originals/, and (after the pipeline ran) draft.md, run.json.

The names are configurable (`config.json` → `intake`), because the folder shape is produced by the
PARTNER's receive stage and must not be guessed. Defaults = the contract; `python -m pipeline.preflight`
measures a real tree against it before a single model call is made.

Queue modes (config.json queue_mode or CLI): one folder at a time by default; a selected set is a
serial queue — the pipeline always processes ONE article at a time (MG spec §3.1).
"""
from pathlib import Path

from . import manifest
from .config import intake_cfg


def _intake(intake):
    return intake if intake is not None else intake_cfg()


def find_release_texts(folder: Path, intake=None):
    """Every plausible release text in the folder — ordered, so an ambiguous folder is visible."""
    rules = _intake(intake)
    folder = Path(folder)
    exclude = {n.lower() for n in rules["release_text_exclude"]}
    found = [p for p in sorted(folder.glob(rules["release_text_glob"]))
             if p.is_file() and p.name.lower() not in exclude]
    return found


def find_release_text(folder: Path, intake=None):
    """The release .md (first candidate). `find_release_texts` is the honest API for preflight."""
    texts = find_release_texts(folder, intake)
    return texts[0] if texts else None


def find_link(folder: Path, intake=None):
    rules = _intake(intake)
    for name in rules["link_names"]:
        p = Path(folder) / name
        if p.exists():
            return p
    return None


def find_images(folder: Path, intake=None):
    """All image files under the configured image dirs (default images/ + originals/)."""
    rules = _intake(intake)
    found = []
    for sub in list(rules["image_dirs"]) + list(rules.get("extra_image_dirs") or []):
        d = Path(folder) if sub in ("", ".") else Path(folder) / sub
        if d.is_dir():
            found += [p for p in sorted(d.iterdir())
                      if p.is_file() and p.suffix.lower() in
                      (".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff")]
    return found


def scan_folder(folder: Path, intake=None):
    folder = Path(folder)
    rules = _intake(intake)
    draft = folder / "draft.md"
    run = manifest.read(folder) or {}
    site = folder / "site"
    rendered = sorted(site.glob("*.html")) if site.is_dir() else []
    has_draft = draft.exists()
    validated = bool(run.get("validator", {}).get("ok"))
    if rendered and validated:
        status = "rendered"
    elif has_draft and run.get("status") == "HOLD":
        status = "HOLD"
    elif has_draft and validated is False and run.get("status") == "validate-failed":
        status = "validate-failed"
    elif has_draft:
        status = "drafted"
    else:
        status = "pending"
    texts = find_release_texts(folder, rules)
    return {
        "folder": folder.name,
        "path": str(folder),
        "release": texts[0].name if texts else None,
        "n_release_texts": len(texts),
        "ambiguous": len(texts) > 1,
        "has_link": find_link(folder, rules) is not None,
        "n_images": len(find_images(folder, rules)),
        "draft": str(draft) if has_draft else None,
        "n_rendered": len(rendered),
        "status": status,
        "run": run,
    }


def scan_all(cfg):
    root = Path(cfg["email_articles_root"])
    if not root.is_absolute():
        from msme import paths
        root = paths.ROOT / root
    rules = intake_cfg(cfg)
    folders = sorted(d for d in root.iterdir() if d.is_dir()) if root.is_dir() else []
    return [scan_folder(f, rules) for f in folders]


def select_queue(cfg, folder=None, folders=None, all_folders=False):
    """Resolve the work queue. Default = the configured mode (one at a time)."""
    items = scan_all(cfg)
    if folder:
        return [i for i in items if i["folder"] == folder]
    if folders:
        wanted = {s.strip() for s in folders.split(",")}
        return [i for i in items if i["folder"] in wanted]
    if all_folders or cfg.get("queue_mode") == "all":
        return items
    return [i for i in items if i["status"] == "pending"][:1]  # one at a time (default)


if __name__ == "__main__":
    import argparse
    import json
    from .config import load_config
    ap = argparse.ArgumentParser(description="Scan receive folders -> work queue")
    ap.add_argument("--folder"); ap.add_argument("--folders"); ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    queue = select_queue(cfg, a.folder, a.folders, a.all)
    if a.json:
        print(json.dumps(queue, indent=2, ensure_ascii=False))
    else:
        for i in queue:
            print(f"{i['status']:16} {i['folder'][:70]}")
        print(f"-- {len(queue)} folder(s) in queue (processed one at a time)")
