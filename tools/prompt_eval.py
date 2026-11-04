# =============================================================================
# FILE HEADER
# file    : tools/prompt_eval.py
# role    : Evaluation — A/B the receive prompts on archived emails
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : rebuild an email from all_emails/ + its checklist row, run the REAL pipeline with
#           prompt_version v0 and v1 in dry-run (no archive/Sheet/DB writes), and compare the verdicts.
# pages   : n/a
# calls   : pipeline, normalize, config, db; the configured AI provider
# called  : developer / operator (python3 tools/prompt_eval.py --limit 6 --yes)
# amend   : the eval never writes the live DB/archive; fake Gmail only. Report outputs go to docs/.
#           Test: python3 -m unittest tests.test_prompt_eval
# =============================================================================
"""Prompt A/B on archived emails — dry-run, no live writes.

For each selected archive folder:
  - rebuild a Gmail message: subject/from/date from the checklist row, a cover note or the
    archived article as the body, and the archived originals/images as attachments;
  - run `pipeline.process_email` twice (prompt_version v0, v1) with a fake Gmail service;
  - compare the resulting 14-column rows with the stored checklist row and the article preview.

Example:
    python3 tools/prompt_eval.py --limit 6 --versions v0,v1 --yes
"""
import argparse
import base64
import hashlib
import json
import mimetypes
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from msme import config
from msme.receive import pipeline

ARCHIVE_ROOTS = ["all_emails"]
SKIP_DIRS = {"_duplicates", "_no_article"}
DOC_EXT = {".pdf", ".docx", ".doc", ".txt", ".md"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".heic", ".tiff"}
FLAGS = ["hasArticle", "hasPic", "hasLogo", "hasLogoInArticle",
         "hasImageInArticle", "subjectMatch", "readyToFilter"]
FLAG_KEYS = [f for f in FLAGS if f != "readyToFilter"]
MAX_FILE_MB = 15


# ---------------------------------------------------------------------------
# archive selection
# ---------------------------------------------------------------------------
def _article_md(folder):
    if not os.path.isdir(folder):
        return ""
    mds = [f for f in os.listdir(folder)
           if f.lower().endswith(".md") and f.lower() != "link.md"]
    return max(mds, key=lambda f: os.path.getsize(os.path.join(folder, f))) if mds else ""


def _archive_index(root="all_emails"):
    """basename(.md) -> folder path, skipping duplicates/no-article."""
    index = {}
    root = Path(root)
    if not root.is_dir():
        return index
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith((".", "_"))]
        md = _article_md(dirpath)
        if md:
            index.setdefault(md, dirpath)
    return index


def _read_rows(db_path=None):
    db_path = db_path or config.SQLITE_PATH
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(
        "select * from checklist where articleFile != '' order by id desc")]
    con.close()
    return rows


def select_cases(limit=6, db_path=None, archive_root="all_emails", include_not_ready=True):
    """Pick a balanced set: ready + not-ready, attachment-first, one row per subject."""
    index = _archive_index(archive_root)
    rows = _read_rows(db_path)
    seen = set()
    cases = []
    for row in rows:
        key = (row.get("subject") or "").strip().lower()
        if not key or key in seen:
            continue
        af = os.path.basename(row.get("articleFile") or "")
        folder = index.get(af)
        if not folder:
            continue
        md = _article_md(folder)
        if not md:
            continue
        seen.add(key)
        originals = sorted(
            f for f in os.listdir(os.path.join(folder, "originals"))
            if os.path.isfile(os.path.join(folder, "originals", f))
        ) if os.path.isdir(os.path.join(folder, "originals")) else []
        images = sorted(
            f for f in os.listdir(os.path.join(folder, "images"))
            if os.path.isfile(os.path.join(folder, "images", f))
        ) if os.path.isdir(os.path.join(folder, "images")) else []
        cases.append({
            "row": row,
            "folder": str(folder),
            "md": md,
            "subject": row.get("subject") or os.path.basename(folder),
            "date": row.get("date") or "",
            "originals": originals,
            "images": images,
            "ready": str(row.get("readyToFilter", "")).lower() == "true",
        })

    ready = [c for c in cases if c["ready"]]
    not_ready = [c for c in cases if not c["ready"]]
    picked = []
    # attachment-first within each bucket, then alternate
    def rank(c):
        return (0 if c["originals"] else 1, -len(c["originals"]), c["subject"].lower())

    ready.sort(key=rank)
    not_ready.sort(key=rank)
    while len(picked) < limit and (ready or not_ready):
        if ready:
            picked.append(ready.pop(0))
        if len(picked) < limit and include_not_ready and not_ready:
            picked.append(not_ready.pop(0))
    return picked


# ---------------------------------------------------------------------------
# fake Gmail service (archive -> message + attachment bytes)
# ---------------------------------------------------------------------------
def _b64(text):
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii").rstrip("=")


def _mime(name):
    return mimetypes.guess_type(name)[0] or "application/octet-stream"


def _safe_read(path, max_mb=MAX_FILE_MB):
    try:
        size = os.path.getsize(path)
        if size > max_mb * 1024 * 1024:
            return None, size
        with open(path, "rb") as f:
            return f.read(), size
    except Exception:
        return None, 0


def build_message(case, max_mb=MAX_FILE_MB):
    """Rebuild a Gmail message + {attachmentId: bytes} from one archive folder."""
    article_path = os.path.join(case["folder"], case["md"])
    with open(article_path, encoding="utf-8", errors="replace") as f:
        article = f.read()
    has_docs = any(os.path.splitext(n)[1].lower() in DOC_EXT for n in case["originals"])
    body = article if not has_docs else (
        "Hi Editor,\n\nPlease find the attached release for publication. "
        "Let me know if you need a photo.\n\nBest regards,\nThe sender"
    )

    parts = [{"mimeType": "text/plain", "body": {"data": _b64(body)}}]
    blobs = {}
    files = []
    if has_docs:
        files += [(n, os.path.join(case["folder"], "originals", n)) for n in case["originals"]]
    files += [(n, os.path.join(case["folder"], "images", n)) for n in case["images"]]
    for i, (name, path) in enumerate(files):
        data, size = _safe_read(path, max_mb)
        if data is None:
            continue
        aid = f"att-{i}"
        blobs[aid] = data
        parts.append({
            "mimeType": _mime(name),
            "filename": name,
            "body": {"attachmentId": aid, "size": size},
        })

    msg_id = "archive-" + hashlib.sha1((case["folder"] + case["md"]).encode()).hexdigest()[:12]
    message = {
        "id": msg_id,
        "threadId": "archive-thread",
        "payload": {
            "mimeType": "multipart/mixed",
            "headers": [
                {"name": "Subject", "value": case["subject"]},
                {"name": "From", "value": "Editor MSME <editor@malaysiasme.com.my>"},
                {"name": "Date", "value": case["date"]},
            ],
            "parts": parts,
        },
    }
    return message, blobs, article, has_docs


class _Req:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return self.data


class _Attachments:
    def __init__(self, blobs):
        self.blobs = blobs

    def get(self, **kwargs):
        aid = kwargs.get("id")
        data = self.blobs.get(aid)
        if data is None:
            raise KeyError(aid)
        return _Req({"data": base64.urlsafe_b64encode(data).decode("ascii")})


class _Messages:
    def __init__(self, message, blobs):
        self.message = message
        self.blobs = blobs

    def get(self, **kwargs):
        return _Req(self.message)

    def attachments(self):
        return _Attachments(self.blobs)


class _Users:
    def __init__(self, message, blobs):
        self.message = message
        self.blobs = blobs

    def messages(self):
        return _Messages(self.message, self.blobs)


class FakeGmail:
    """Minimal Gmail service: one message + its attachment bytes."""

    def __init__(self, message, blobs):
        self.message = message
        self.blobs = blobs

    def users(self):
        return _Users(self.message, self.blobs)


# ---------------------------------------------------------------------------
# comparison
# ---------------------------------------------------------------------------
def _tokens(text):
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _jaccard(a, b):
    sa, sb = set(_tokens(a)), set(_tokens(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _preview_sim(expected, preview):
    # compare the first ~200 chars like-for-like
    return round(_jaccard(expected[:400], preview or ""), 3)


def run_case(case, version="v0", max_mb=MAX_FILE_MB, client=None, capture_text=False):
    message, blobs, article, has_docs = build_message(case, max_mb=max_mb)
    service = FakeGmail(message, blobs)
    stages = {}

    def trace(stage, status, detail):
        stages[stage] = {"status": status, "detail": detail}

    t0 = time.time()
    error = ""
    row = {}
    try:
        row = pipeline.process_email(service, message["id"], dry_run=True, trace=trace,
                                     prompt_version=version, client=client,
                                     capture_text=capture_text)
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    elapsed = round(time.time() - t0, 1)

    extract_d = (stages.get("extract") or {}).get("detail") or {}
    full_text = extract_d.get("bodyText", "") if capture_text else ""
    verify_d = (stages.get("verify") or {}).get("detail") or {}
    tokens = (stages.get("tokens") or {}).get("detail") or {}
    return {
        "version": version,
        "row": row,
        "error": error,
        "elapsed": elapsed,
        "tokens": int(tokens.get("total", 0) or 0),
        "article_source": extract_d.get("articleSource", ""),
        "chosen_candidate": extract_d.get("chosenCandidate", ""),
        "body_len": extract_d.get("bodyTextLen", 0),
        "body_preview": extract_d.get("bodyTextPreview", ""),
        "preview_sim": _preview_sim(article, extract_d.get("bodyTextPreview", "")),
        "full_sim": round(_jaccard(article, full_text), 3) if full_text else 0.0,
        "len_ratio": round(len(full_text) / max(1, len(article)), 3) if full_text else 0.0,
        "full_text": full_text,
        "evidence": extract_d.get("evidence", ""),
        "verify": verify_d,
    }


def compare_case(case, runs):
    expected = case["row"]
    out = {"subject": case["subject"], "date": case["date"], "ready_expected": case["ready"],
           "source": "attachment" if case["originals"] else "body",
           "originals": len(case["originals"]), "images": len(case["images"]),
           "runs": {}, "winner": ""}
    for r in runs:
        row = r["row"] or {}
        flags = {k: (str(row.get(k)) == str(expected.get(k))) for k in FLAG_KEYS}
        ready_ok = str(row.get("readyToFilter")) == str(expected.get("readyToFilter"))
        score = 0
        try:
            score = abs(int(row.get("subjectScore", 0) or 0) - int(expected.get("subjectScore", 0) or 0))
        except Exception:
            pass
        out["runs"][r["version"]] = {
            "ready": row.get("readyToFilter"),
            "ready_ok": ready_ok,
            "flags_ok": sum(1 for v in flags.values() if v),
            "flags_total": len(FLAG_KEYS),
            "bad_flags": [k for k, v in flags.items() if not v],
            "flags": flags,
            "score_delta": score,
            "preview_sim": r["preview_sim"],
            "full_sim": r["full_sim"],
            "len_ratio": r["len_ratio"],
            "body_len": r["body_len"],
            "article_source": r["article_source"],
            "chosen_candidate": r["chosen_candidate"],
            "tokens": r["tokens"],
            "elapsed": r["elapsed"],
            "error": r["error"],
        }
    versions = list(out["runs"])
    if len(versions) == 2:
        a, b = out["runs"][versions[0]], out["runs"][versions[1]]
        score_a = (a["ready_ok"] * 3 + a["flags_ok"] + a["preview_sim"] * 2)
        score_b = (b["ready_ok"] * 3 + b["flags_ok"] + b["preview_sim"] * 2)
        out["winner"] = versions[1] if score_b > score_a else (versions[0] if score_a > score_b else "tie")
    return out


def summarize(comparisons, versions):
    summary = {}
    for v in versions:
        runs = [c["runs"][v] for c in comparisons if v in c["runs"]]
        ok = [r for r in runs if not r["error"]]
        summary[v] = {
            "cases": len(runs),
            "errors": len(runs) - len(ok),
            "ready_ok": sum(1 for r in ok if r["ready_ok"]),
            "flags_ok": sum(r["flags_ok"] for r in ok),
            "flags_total": len(ok) * len(FLAG_KEYS),
            "flag_counts": {k: sum(1 for r in ok if r["flags"].get(k)) for k in FLAG_KEYS},
            "avg_preview_sim": round(sum(r["preview_sim"] for r in ok) / len(ok), 3) if ok else 0,
            "avg_full_sim": round(sum(r["full_sim"] for r in ok) / len(ok), 3) if ok else 0,
            "avg_len_ratio": round(sum(r["len_ratio"] for r in ok) / len(ok), 3) if ok else 0,
            "avg_body_len": round(sum(r["body_len"] for r in ok) / len(ok), 1) if ok else 0,
            "tokens": sum(r["tokens"] for r in runs),
            "seconds": round(sum(r["elapsed"] for r in runs), 1),
        }
    summary["winners"] = {
        "v0": sum(1 for c in comparisons if c["winner"] == versions[0]),
        "v1": sum(1 for c in comparisons if c["winner"] == versions[1]) if len(versions) > 1 else 0,
        "tie": sum(1 for c in comparisons if c["winner"] == "tie"),
    }
    return summary


def write_report(comparisons, summary, out_path, meta):
    lines = [
        "# Prompt A/B — receive AI",
        "",
        f"- generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- provider: {meta.get('provider')} / {meta.get('model')}",
        f"- cases: {meta.get('cases')} · versions: {', '.join(meta.get('versions', []))}",
        f"- archive: `{meta.get('archive')}` · dry-run: no archive/Sheet/DB writes",
        "",
        "## Summary",
        "",
        "| version | cases | errors | ready OK | flag matches | avg full sim | avg len ratio | tokens | seconds |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for v in meta.get("versions", []):
        s = summary.get(v, {})
        lines.append(f"| **{v}** | {s.get('cases',0)} | {s.get('errors',0)} | {s.get('ready_ok',0)} | "
                     f"{s.get('flags_ok',0)}/{s.get('flags_total',0)} | {s.get('avg_full_sim',0)} | {s.get('avg_len_ratio',0)} | "
                     f"{s.get('tokens',0)} | {s.get('seconds',0)} |")
    lines += ["", f"Winners: {summary.get('winners')}", "",
              "## Per email", "",
              "| email | source | expected ready | " +
              " | ".join(f"{v} ready / flags / text" for v in meta.get("versions", [])) +
              " | winner |",
              "|---|---|:--:|" + "|".join("---" for _ in meta.get("versions", [])) + "|---|"]
    for c in comparisons:
        cells = []
        for v in meta.get("versions", []):
            r = c["runs"].get(v, {})
            bad = r.get("bad_flags") or []
            bad_s = (" (" + ", ".join(bad) + ")") if bad else ""
            cells.append(f"{r.get('ready')} / {r.get('flags_ok')}/{r.get('flags_total', 6)}"
                         f"{bad_s} / {r.get('full_sim')} ({r.get('len_ratio')}x)")
        lines.append(f"| {c['subject'][:70]} | {c['source']} | {c['ready_expected']} | "
                     + " | ".join(cells) + f" | {c['winner']} |")
    lines += ["", "## Flag matches by flag", "",
              "| flag | " + " | ".join(meta.get("versions", [])) + " |",
              "|---|" + "|".join("---" for _ in meta.get("versions", [])) + "|"]
    for k in FLAG_KEYS:
        row = [k] + [str(summary.get(v, {}).get("flag_counts", {}).get(k, 0)) + "/" +
                     str(summary.get(v, {}).get("cases", 0)) for v in meta.get("versions", [])]
        lines.append("| " + " | ".join(row) + " |")
    lines += ["", "## Notes", "",
              "- The archive is the expected label; the email was rebuilt from the folder "
              "(cover note + originals/images), not the original Gmail payload.",
              "- `text` compares the FULL extracted bodyText with the archived article (Jaccard) and "
              "the length ratio (1.0 = same length); the preview sim is kept in the JSON.",
              "- Deterministic guards (link guard, media dimensions, readyToFilter) are active in both runs.", ""]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=6)
    ap.add_argument("--versions", default="v0,v1")
    ap.add_argument("--archive", default="all_emails")
    ap.add_argument("--out", default="")
    ap.add_argument("--max-file-mb", type=int, default=MAX_FILE_MB)
    ap.add_argument("--yes", action="store_true", help="skip the cost confirmation")
    args = ap.parse_args(argv)

    versions = [v.strip() for v in args.versions.split(",") if v.strip()]
    cases = select_cases(limit=args.limit, archive_root=args.archive)
    if not cases:
        print("No archived cases found.")
        return 2

    try:
        from msme.llm import LLMClient
        lc = LLMClient()
        provider, model = lc.provider, lc.model
    except Exception as e:
        provider, model = "unknown", f"unknown ({e})"
    calls = len(cases) * len(versions) * 3
    print(f"provider={provider}/{model} · cases={len(cases)} · versions={versions} · ~{calls} AI calls")
    print("cases:")
    for c in cases:
        print(f"  - {c['subject'][:80]} | ready={c['ready']} | originals={len(c['originals'])} "
              f"| images={len(c['images'])} | folder={os.path.basename(c['folder'])[:50]}")
    if not args.yes:
        try:
            ans = input("Run the A/B? [y/N] ").strip().lower()
        except EOFError:
            ans = ""
        if ans not in ("y", "yes"):
            print("Aborted.")
            return 1

    comparisons = []
    for case in cases:
        runs = []
        for v in versions:
            print(f"[{v}] {case['subject'][:70]} ...", flush=True)
            run = run_case(case, version=v, max_mb=args.max_file_mb, capture_text=True)
            if run["error"]:
                print(f"   ERROR {run['error']}")
            else:
                print(f"   ready={run['row'].get('readyToFilter')} src={run['article_source']} "
                      f"len={run['body_len']} sim={run['preview_sim']} tokens={run['tokens']} {run['elapsed']}s")
            runs.append(run)
        comparisons.append(compare_case(case, runs))

    summary = summarize(comparisons, versions)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    out = args.out or f"docs/PROMPT-EVAL-{stamp}.md"
    json_out = os.path.splitext(out)[0] + ".json"
    meta = {"provider": provider, "model": model, "cases": len(cases),
            "versions": versions, "archive": args.archive}
    write_report(comparisons, summary, out, meta)
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "summary": summary, "comparisons": comparisons}, f,
                  ensure_ascii=False, indent=2)
    print(f"\nreport: {out}\njson:   {json_out}")
    print(f"summary: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
