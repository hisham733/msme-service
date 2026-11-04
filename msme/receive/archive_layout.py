# =============================================================================
# FILE HEADER
# file    : msme/receive/archive_layout.py
# role    : Filter — archive version + received-date helpers
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : group archive folders that differ only by a _N version suffix, pick one version per
#           group, and resolve an article's received date from the local date maps.
# pages   : backs the Report Manager (filter_service) and tools/reorganize_archive.py
# calls   : json, os, re, sqlite3, datetime
# called  : filter_service.py; tools/reorganize_archive.py; unit tests
# amend   : version suffix = " <n>" or "_<n>"; a chosen folder must contain an article .md.
#           Test: python3 -m unittest tests.test_report_versions -v
# =============================================================================
"""Archive layout helpers: one chosen version per base folder + received-date lookup.

The receive pipeline names a folder after the subject and appends `_1`, `_2`…
on every reprocess. The report and the ready list must see ONE row per subject,
not one row per reprocessed copy.

Example:
    groups = group_versions("all_emails")
    chosen = choose_version(groups["ACCA Five Priorities ..."])
    chosen["name"]  # newest folder with an article
"""
import datetime as _dt
import json
import os
import re
import sqlite3

VERSION_SUFFIX = re.compile(r"[ _]+\d+$")
SKIP_PREFIXES = ("_", ".")
MONTHS = {
    "ja": 1, "fe": 2, "ma": 3, "ap": 4, "my": 5, "ju": 6,
    "au": 8, "se": 9, "oc": 10, "no": 11, "de": 12,
}


def version_base(name):
    """Base name with a trailing `_2` / ` 2` version suffix removed."""
    return VERSION_SUFFIX.sub("", (name or "")).rstrip()


def article_md(folder):
    """The largest article `.md` in a folder (ignores link.md), or ""."""
    if not os.path.isdir(folder):
        return ""
    mds = [f for f in os.listdir(folder)
           if f.lower().endswith(".md") and f.lower() != "link.md"]
    if not mds:
        return ""
    return max(mds, key=lambda f: os.path.getsize(os.path.join(folder, f)))


def _visible(name):
    return bool(name) and not name.startswith(SKIP_PREFIXES)


def iter_article_dirs(root):
    """Yield article folders under `root`, flat or one date-bucket level deep.

    Returns dicts: {rel, path, name, md}. `_duplicates/`, `_no_article/` and
    dot-folders are skipped. A flat archive (`root/<article>`) and a sorted one
    (`root/<bucket>/<article>`) are both supported.
    """
    if not os.path.isdir(root):
        return []
    out = []
    for name in sorted(os.listdir(root)):
        if not _visible(name):
            continue
        d = os.path.join(root, name)
        if not os.path.isdir(d):
            continue
        md = article_md(d)
        if md:
            out.append({"rel": name, "path": d, "name": name, "md": md})
            continue
        for sub in sorted(os.listdir(d)):
            if not _visible(sub):
                continue
            sd = os.path.join(d, sub)
            if not os.path.isdir(sd):
                continue
            m = article_md(sd)
            if m:
                out.append({"rel": name + "/" + sub, "path": sd, "name": sub, "md": m})
    return out


def group_versions(root):
    """Group article folders by version base.

    Returns {base: [item...]} where each item carries mtime + article chars so
    the caller can pick the newest complete version.
    """
    groups = {}
    for item in iter_article_dirs(root):
        groups.setdefault(version_base(item["name"]), []).append(item)
    for items in groups.values():
        for item in items:
            item["mtime"] = os.stat(item["path"]).st_mtime
            try:
                with open(os.path.join(item["path"], item["md"]),
                          encoding="utf-8", errors="replace") as f:
                    item["chars"] = len(f.read())
            except Exception:
                item["chars"] = 0
    return groups


def filter_by_folder(items, folder):
    """Keep items whose rel is under `folder` (a top-level date bucket).

    An empty folder means "all". A flat top-level article (rel without a slash)
    belongs to the root and is only kept by the empty-folder selection.
    """
    if not folder:
        return list(items)
    prefix = folder.rstrip("/") + "/"
    return [i for i in items if i["rel"].startswith(prefix)]


def top_folders(root):
    """Top-level folders that hold article folders, with their article counts.

    Returns [{"name", "count"}]; flat top-level articles are counted under "".
    """
    counts = {}
    for item in iter_article_dirs(root):
        head = item["rel"].split("/", 1)[0] if "/" in item["rel"] else ""
        counts[head] = counts.get(head, 0) + 1
    return [{"name": name, "count": count} for name, count in sorted(counts.items(), reverse=True)
            if name]


def choose_version(items, keep=None, base=""):
    """Pick one version: keep-map entry first, else newest complete folder."""
    if not base and items:
        base = version_base(items[0]["name"])
    keep = keep or {}
    want = keep.get(base) if isinstance(keep, dict) else None
    if isinstance(keep, dict) and "keep" in keep and isinstance(keep["keep"], dict):
        want = keep["keep"].get(base)
    if want:
        for item in items:
            if want in (item["name"], item.get("rel")):
                return item
    with_md = [i for i in items if i.get("md")]
    if not with_md:
        return None
    return max(with_md, key=lambda i: (i.get("mtime", 0), i.get("chars", 0)))


def parse_date(value, mtime=None):
    """Parse ISO, RFC 2822, or the DB's truncated `Fri, 16 Oc` into YYYY-MM-DD."""
    s = (value or "").strip()
    if not s:
        return ""
    if len(s) >= 10 and s[:4].isdigit() and s[4] == "-":
        return s[:10]
    try:
        import email.utils

        return email.utils.parsedate_to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        pass
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{2,3})", s)
    if not m:
        return ""
    mon = MONTHS.get(m.group(2)[:2].lower())
    if not mon:
        return ""
    year = _dt.datetime.now().year
    if mtime:
        mt = _dt.datetime.fromtimestamp(mtime)
        year = mt.year
        if m.group(2)[:2].lower() == "ju":
            mon = mt.month if mt.month in (6, 7) else 6
        if mon > mt.month + 1:
            year -= 1
    try:
        return _dt.date(year, mon, int(m.group(1))).isoformat()
    except Exception:
        return ""


def norm_subject(value):
    s = re.sub(r"^(fwd|fw|re):\s*", "", (value or "").strip(), flags=re.I)
    s = re.sub(r"\[[^\]]*\]", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _stem(filename):
    return norm_subject(os.path.splitext(os.path.basename(filename or ""))[0])


def build_date_map(docs_dir, data_dir, db_path):
    """Build {normalized subject/filename: (date, source)} from the local maps."""
    out = {}
    sources = (
        (os.path.join(docs_dir, "sme-reject-6-10.json"), "sme-reject"),
        (os.path.join(docs_dir, "email-dates.json"), "email-dates"),
        (os.path.join(docs_dir, "negative-dataset.json"), "negatives"),
    )

    def put(key, date, source):
        key = (key or "").strip()
        if key and date and key not in out:
            out[key] = (date, source)

    for path, source in sources:
        try:
            rows = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        for row in rows if isinstance(rows, list) else []:
            date = parse_date(row.get("date", ""))
            put(norm_subject(row.get("subject", "")), date, source)
            put(_stem(row.get("file", "")), date, source)
    try:
        rows = json.load(open(os.path.join(data_dir, "emails_cache.json"),
                              encoding="utf-8")).get("emails", [])
        for row in rows:
            put(norm_subject(row.get("subject", "")), parse_date(row.get("date", "")),
                "emails_cache")
    except Exception:
        pass
    try:
        con = sqlite3.connect(db_path)
        for subject, date, article_file in con.execute(
                "select subject, date, articleFile from checklist"):
            when = parse_date(date or "")
            put(norm_subject(subject or ""), when, "sqlite")
            put(_stem(article_file or ""), when, "sqlite")
        con.close()
    except Exception:
        pass
    return out


def received_date(folder, md, date_map):
    """Look a folder/article up in the date map; returns (YYYY-MM-DD, source)."""
    keys = (norm_subject(folder), _stem(md))
    for key in keys:
        if key and key in date_map:
            return date_map[key]
    for key in keys:
        if not key:
            continue
        for known, (date, source) in date_map.items():
            if known and date and (key[:30] in known or known[:30] in key):
                return date, source
    return "", ""


def load_keepmap(path):
    """Read docs/archive-versions.json ({"keep": {base: folder}}); {} on error."""
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        return doc.get("keep") if isinstance(doc, dict) else {}
    except Exception:
        return {}


def save_keepmap(path, keep, cutoff="", buckets=None):
    """Write the keep-map after a reorganise run."""
    doc = {"cutoff": cutoff, "keep": keep, "buckets": buckets or {}}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    return doc
