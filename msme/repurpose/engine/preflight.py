"""preflight.py — a READ-ONLY check of a post-filter release tree against the intake contract.

Why this exists
---------------
The receive stage belongs to the partner; we do not know its folder shape. Rather than guess it, this
tool measures a real tree and says which folders the repurpose stage can consume as-is, which need a
warning accepted, and which it cannot read at all. It costs no API call and writes nothing.

    python -m pipeline.preflight                          # the configured email_articles_root
    python -m pipeline.preflight --root <path> --json      # any tree (e.g. after the partner's filter)
    python -m pipeline.preflight --root <path> --report evidence/preflight.json --strict

Exit code: 0 when every folder can be consumed (warnings allowed), 1 when any folder FAILs or the root
holds release texts loose instead of one-folder-per-article, 2 when the root does not exist.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import scan
from msme import paths
from .config import intake_cfg, load_config

MIN_TEXT_CHARS = 200


def _read_text(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return exc


def check_folder(folder: Path, rules) -> dict:
    errors, warnings = [], []
    texts = scan.find_release_texts(folder, rules)
    if not texts:
        errors.append(f"no release text (looked for {rules['release_text_glob']}, excluding "
                      f"{', '.join(rules['release_text_exclude'])})")
    elif len(texts) > 1:
        errors.append(f"ambiguous: {len(texts)} release-text candidates "
                      f"({', '.join(p.name for p in texts[:4])}) — one folder must hold ONE article")
    else:
        text = _read_text(texts[0])
        if isinstance(text, UnicodeDecodeError):
            errors.append(f"release text is not UTF-8 ({texts[0].name})")
        elif len(text.strip()) < MIN_TEXT_CHARS:
            warnings.append(f"release text looks empty ({len(text.strip())} chars, "
                            f"expected >= {MIN_TEXT_CHARS})")

    link = scan.find_link(folder, rules)
    if link is None:
        (errors if rules.get("require_link") else warnings).append(
            "no link file (published URL unknown — optional, but the corpus needs it)")

    images = scan.find_images(folder, rules)
    if not images:
        warnings.append("no image files: the featured image must arrive in the pack "
                        "or be a declared library asset")

    if (folder / "draft.md").exists() or (folder / "run.json").exists():
        warnings.append("already processed (draft.md/run.json present) — use a fresh folder to test")

    return {
        "folder": folder.name,
        "status": "FAIL" if errors else ("WARN" if warnings else "PASS"),
        "release_texts": [p.name for p in texts],
        "link": link.name if link else None,
        "n_images": len(images),
        "errors": errors,
        "warnings": warnings,
    }


def check_root(root, rules=None) -> dict:
    root = Path(root)
    rules = rules or intake_cfg()
    report = {"root": str(root), "exists": root.is_dir(), "flat_release_texts": [],
              "folders": [], "summary": {}}
    if not root.is_dir():
        report["error"] = f"root does not exist: {root}"
        report["summary"] = {"folders": 0, "pass": 0, "warn": 0, "fail": 0}
        return report

    report["flat_release_texts"] = sorted(
        p.name for p in root.glob(rules["release_text_glob"])
        if p.is_file() and p.name.lower() not in {n.lower() for n in rules["release_text_exclude"]})
    directories = sorted((d for d in root.iterdir() if d.is_dir()), key=lambda d: d.name.lower())
    report["folders"] = [check_folder(d, rules) for d in directories]
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for row in report["folders"]:
        counts[row["status"]] += 1
    report["summary"] = {"folders": len(report["folders"]),
                         "pass": counts["PASS"], "warn": counts["WARN"], "fail": counts["FAIL"]}
    return report


def render(report: dict) -> str:
    lines = [f"preflight — {report['root']}"]
    if not report["exists"]:
        lines.append(f"FAIL  {report.get('error')}")
        return "\n".join(lines)
    for row in report["folders"]:
        detail = f"release={'yes' if row['release_texts'] else 'no'} · " \
                 f"link={'yes' if row['link'] else 'no'} · images={row['n_images']}"
        if row["status"] != "PASS":
            detail += " — " + "; ".join(row["errors"] + row["warnings"])[:120]
        lines.append(f"[{row['status']}] {row['folder'][:64]:64} {detail}")
    if report["flat_release_texts"]:
        lines.append(f"\nFAIL  {len(report['flat_release_texts'])} release text(s) sit at the root — "
                     "the contract is ONE FOLDER PER ARTICLE: "
                     + ", ".join(report["flat_release_texts"][:4]))
    s = report["summary"]
    lines.append(f"\nsummary: {s['folders']} folder(s) · {s['pass']} pass · {s['warn']} warn · "
                 f"{s['fail']} fail" + (" · flat layout" if report["flat_release_texts"] else ""))
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Read-only preflight of a post-filter release tree")
    ap.add_argument("--root", help="tree to check (default: config email_articles_root)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--report", help="write the JSON report to this path (evidence folder)")
    ap.add_argument("--strict", action="store_true", help="warnings also exit non-zero")
    a = ap.parse_args(argv)

    cfg = load_config()
    rules = intake_cfg(cfg)
    root = Path(a.root) if a.root else Path(cfg["email_articles_root"])
    if a.root is None and not root.is_absolute():
        root = paths.ROOT / root
    report = check_root(root, rules)

    if a.report:
        out = Path(a.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if a.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render(report))

    if not report["exists"]:
        return 2
    s = report["summary"]
    bad = s["fail"] > 0 or bool(report["flat_release_texts"]) or (a.strict and s["warn"] > 0)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
