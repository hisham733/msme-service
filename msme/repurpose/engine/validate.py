"""validate.py — mechanical acceptance checks (D-007) + D-008 graph-never-featured.

Every check returns {code, level: 'fail'|'warn', ok, detail}. A draft passes only when no
'fail' remains; fails drive the bounded re-prompt loop to the LLM (run.py), then HOLD.
"""
import re
from pathlib import Path

from . import assets
from .parser import load_draft
from .scan import find_release_text

RENAMED_TOKEN = "_MALAYSIA-SME."
ALLOWED_RUNGS = {"people", "portrait", "logo", "event-key-visual", "event-visual", "product"}
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
NUM_RE = re.compile(r"\d[\d,.]*")
BAD_WORDS = ("for immediate release", "pillars", "column")

RULEBOOK = [
    ("DRAFT_PARSE", "the draft must parse into the contract sections",
     "all sections present (Branch, Title, Excerpt, Body, Categories, Images, Flags)",
     "engine contract (T-011) — matches the skill output contract"),
    ("BRANCH_RECORDED", "the article type is explicitly recorded",
     "Branch names news / commentary / byline", "skill Step 3 · D-006 (class selects treatment)"),
    ("TITLE_PRESENT", "the article has a title", "non-empty title line", "skill Step 4"),
    ("EXCERPT_WORDS", "news excerpt length", "25–42 words (commentary: no excerpt)",
     "measured corpus range · skill Step 5"),
    ("SUBHEADERS_3_8", "news section count", "3–8 H2 sections (commentary: none)",
     "published practice · skill Step 7"),
    ("QUOTES_SENTENCE_BOUNDARY", "quotes end where they should",
     "each blockquote ends at . ! ?", "skill rule 4 / Step 7"),
    ("DUPLICATE_SUBHEADER", "no repeated section heading", "each heading appears once",
     "MG 2026-10-23 · skill rule 7"),
    ("REPEATED_PARAGRAPH", "no repeated paragraph", "no identical paragraph (8+ words) twice",
     "MG 2026-10-23 · skill rule 7"),
    ("CATEGORIES_1_4", "category count", "1–4 categories", "skill Step 3/11"),
    ("CATEGORIES_BANNED", "reserved categories", "never PILLARS or COLUMN", "site taxonomy · skill"),
    ("NO_CONTACTS_BOILERPLATE", "clean body", "no URLs/emails/phones/'FOR IMMEDIATE RELEASE'/###",
     "skill Step 9"),
    ("NUMBERS_TRACE", "no added facts (D-002)", "every number in the draft must appear in the release",
     "D-002 · engine check (MG 2026-10-23: fail, not warn)"),
    ("QUOTE_TRACE", "quotes are not invented", "every blockquote appears verbatim in the release",
     "N-10 · no external facts"),
    ("ENTITY_TRACE", "no new names, dates or amounts",
     "dates/amounts must be in the release (fail); names/acronyms warn",
     "N-10 · no internet injection"),
    ("SENTENCE_SUPPORT", "no wholly new sentence", "each body paragraph shares ≥20% of its content words with the release (warn)",
     "N-10 · heuristic against invented claims"),
    ("FEATURED_EXISTS", "the featured image is on disk", "file found in images/ or originals/",
     "D-003 · image skill (a library asset must be downloaded first)"),
    ("FEATURED_RENAME_TOKEN", "the rename follows the site convention",
     "renamed contains _MALAYSIA-SME.", "image skill Step 4"),
    ("FEATURED_CAPTION", "the featured image is captioned", "caption non-empty", "image skill Step 5"),
    ("CAPTION_CLEAN", "the caption is publishable",
     "no editorial notes (*(…, [FLAG], 'confirm', 'unverified')", "MG 2026-10-23 live-run finding"),
    ("FEATURED_RUNG_D008", "the ladder rung is valid",
     "rung ∈ people/logo/event key-visual/product; a GRAPH always fails",
     "D-003 ladder · D-008 · image skill rule 1"),
    ("FEATURED_DECLARED_ASSET", "a missing picture is a NAMED asset, not a silent hold",
     "when no usable file exists, the Images block declares kind + subject (T-018)",
     "image skill §3 · v4 calibration 2026-10-23"),
    ("FEATURED_NOT_A_CROP", "a header cropped out of a supplied PDF is not published automatically",
     "the featured file must be supplied artwork or a real embedded image, not a page-header render",
     "D-C (MG 2026-10-24) · pipeline/assets.py"),
    ("IN_BODY_COUNT", "in-body image cap", "0–6 in-body images", "image skill Step 3"),
]


def rulebook():
    return [{"code": c, "what": w, "threshold": t, "source": s} for c, w, t, s in RULEBOOK]


def _norm_num(s):
    return s.strip().rstrip(".,%").replace(",", "")


def _excerpt_words(excerpt):
    return len([w for w in excerpt.split() if w != "-"])


def _quote_ok(lines):
    text = " ".join(l for l in lines if not l.startswith("—") and not l.startswith("- "))
    text = text.strip().strip('"“”').strip()
    return bool(text) and text[-1] in ".!?\"“”"


def _all_numbers(text):
    return {_norm_num(n) for n in NUM_RE.findall(text)} - {""}


# --- N-10 fact trace: no new names / dates / quotes / wholly-new sentences -------------------
DATE_RE = re.compile(
    r"\b(?:\d{1,2}\s+)?(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)(?:\s+\d{1,2})?(?:,?\s+\d{4})?\b",
    re.I,
)
PROPER_RE = re.compile(r"\b([A-Z][A-Za-z&'’+-]*(?:\s+[A-Z][A-Za-z&'’+-]*)+)\b")
ACRONYM_RE = re.compile(r"\b[A-Z]{2,6}\b")
STOP_PROPER = {
    "the", "a", "an", "this", "that", "these", "those", "in", "on", "at", "for", "and", "or",
    "but", "with", "from", "to", "of", "by", "as", "is", "are", "was", "were", "it", "its",
    "he", "she", "they", "we", "you", "our", "their", "his", "her", "what", "when", "where",
    "who", "why", "how", "said", "says", "according", "meanwhile", "however", "also",
}
STOP_WORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "has", "had", "will", "would",
    "were", "was", "are", "its", "their", "they", "them", "there", "which", "what", "when",
    "where", "who", "why", "how", "into", "onto", "over", "under", "about", "after", "before",
    "more", "most", "than", "then", "also", "said", "says", "according", "between", "during",
}
COMMON_ACRONYMS = {"AI", "CEO", "APAC", "SME", "SMES", "RM", "USD", "MOU", "PDF", "DOCX"}


def _norm_text(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def _quote_segments(lines):
    """The quoted text only — attribution outside the quotation marks is not checked."""
    text = " ".join(
        l.strip() for l in (lines or []) if not l.strip().startswith(("—", "- "))
    )
    found = re.findall(r'[“"](.+?)[”"]', text, re.S)
    if found:
        return [f.strip() for f in found if f.strip()]
    text = text.strip().strip('"“”').strip()
    return [text] if text else []


def _entity_scan(text):
    """Return (dates, proper-noun phrases, acronyms) found in the draft body."""
    dates = {m.group(0).strip() for m in DATE_RE.finditer(text or "")}
    names = set()
    for m in PROPER_RE.finditer(text or ""):
        words = m.group(1).split()
        if not words or words[0].lower() in STOP_PROPER:
            continue
        names.add(m.group(1))
    acronyms = set(ACRONYM_RE.findall(text or "")) - COMMON_ACRONYMS
    return dates, names, acronyms


def _content_words(text):
    return {w for w in _norm_text(text).split() if len(w) >= 4 and w not in STOP_WORDS}


def validate_folder(folder) -> dict:
    folder = Path(folder)
    draft_path = folder / "draft.md"
    results = []

    def add(code, ok, detail="", level="fail"):
        results.append({"code": code, "ok": bool(ok), "level": level, "detail": detail})

    try:
        d = load_draft(draft_path)
        add("DRAFT_PARSE", True, f"{len(d['sections'])} sections")
    except Exception as e:  # unparsable draft = fatal
        add("DRAFT_PARSE", False, str(e))
        return {"ok": False, "results": results, "draft": None}

    is_news = d["branch"] == "news"
    add("BRANCH_RECORDED", bool(d["branch"]), d["branch"] or "no branch recorded")
    add("TITLE_PRESENT", bool(d["title"]), d["title"][:60])

    if is_news:
        n = _excerpt_words(d["excerpt"])
        add("EXCERPT_WORDS", 25 <= n <= 42, f"{n} words (25-42)")
        nsubs = len({b["sub"] for b in d["body"] if b["sub"]})
        add("SUBHEADERS_3_8", 3 <= nsubs <= 8, f"{nsubs} H2 subheaders")

    quotes = [q for b in d["body"] for q in b["quotes"]]
    bad_q = [q[-1][-40:] for q in quotes if not _quote_ok(q)]
    add("QUOTES_SENTENCE_BOUNDARY", not bad_q,
        f"{len(quotes)} blockquote(s)" + (f"; not at boundary: {bad_q}" if bad_q else ""))

    by_name = {}
    for b in d["body"]:
        if b["sub"]:
            by_name.setdefault(b["sub"], set()).add(b.get("sid"))
    dup_subs = sorted(n for n, sids in by_name.items() if len(sids) > 1)
    add("DUPLICATE_SUBHEADER", not dup_subs,
        f"repeated: {dup_subs}" if dup_subs else f"{len(by_name)} unique subheaders")

    def sig(p):
        words = re.sub(r"[^a-z0-9 ]+", "", p.lower()).split()
        return " ".join(words[:8]) if len(words) >= 8 else ""

    paras = [p for b in d["body"] for p in b["paras"] if sig(p)]
    seen, dup_paras = set(), []
    for p in paras:
        s = sig(p)
        if s in seen:
            dup_paras.append(p[:70])
        seen.add(s)
    add("REPEATED_PARAGRAPH", not dup_paras,
        f"repeated: {dup_paras}" if dup_paras else f"{len(paras)} distinct paragraphs")

    cats = d["categories"]
    add("CATEGORIES_1_4", 1 <= len(cats) <= 4, ", ".join(cats))
    banned = [c for c in cats if c.lower() in ("pillars", "column")]
    add("CATEGORIES_BANNED", not banned, f"banned: {banned}" if banned else "none of PILLARS/COLUMN")

    body_text = "\n".join(p for b in d["body"] for p in b["paras"])
    contact_hits = []
    if re.search(r"https?://|www\.", body_text, re.I):
        contact_hits.append("URL")
    if EMAIL_RE.search(body_text):
        contact_hits.append("email")
    if re.search(r"\+?\d[\d\s()-]{7,}\d", body_text):
        contact_hits.append("phone")
    for w in BAD_WORDS:
        if w in body_text.lower():
            contact_hits.append(w)
    add("NO_CONTACTS_BOILERPLATE", not contact_hits, f"found: {contact_hits}" if contact_hits else "clean")

    # D-002 / N-10 mechanical trace: numbers, quotes, names/dates, sentence support.
    rel = find_release_text(folder)
    if rel:
        rel_raw = rel.read_text(encoding="utf-8", errors="replace")
        rel_norm_nums = re.sub(r"[,\s]", "", rel_raw).lower()
        used = _all_numbers(body_text + " " + d["excerpt"])
        missing = sorted(n for n in used if n and n not in rel_norm_nums)
        add("NUMBERS_TRACE", not missing,
            f"{len(used)} numbers traced" + (f"; NOT in release: {missing}" if missing else ""))

        rel_norm = _norm_text(rel_raw)
        rel_words = set(rel_norm.split())

        # N-10a: quotes must be verbatim in the release (quote text only, not the attribution)
        segments = [seg for b in d["body"] for q in b["quotes"] for seg in _quote_segments(q)]
        missing_quotes = [seg[:60] for seg in segments if _norm_text(seg) not in rel_norm]
        add("QUOTE_TRACE", not missing_quotes,
            f"{len(segments)} quote segment(s) traced"
            + (f"; NOT in release: {missing_quotes}" if missing_quotes else ""))

        # N-10b: dates (fail) and names/acronyms (warn)
        dates, names, acronyms = _entity_scan(body_text + " " + d["excerpt"])
        bad_dates = []
        for x in dates:
            toks = _norm_text(x).split()
            if not toks:
                continue
            if _norm_text(x) in rel_norm or all(t in rel_words for t in toks):
                continue
            bad_dates.append(x)
        bad_dates.sort()
        bad_names = []
        for n in sorted(names):
            toks = _norm_text(n).split()
            if _norm_text(n) in rel_norm or (toks and all(t in rel_words for t in toks)):
                continue
            bad_names.append(n)
        bad_acr = sorted(a for a in acronyms if a.lower() not in rel_words)
        ent_detail = []
        if bad_dates:
            ent_detail.append(f"dates NOT in release: {bad_dates}")
        if bad_names:
            ent_detail.append(f"names NOT in release: {bad_names[:6]}")
        if bad_acr:
            ent_detail.append(f"acronyms NOT in release: {bad_acr[:6]}")
        add("ENTITY_TRACE", not (bad_dates or bad_names or bad_acr),
            "; ".join(ent_detail) if ent_detail
            else f"{len(dates)} date(s), {len(names)} name(s) traced",
            level="fail" if bad_dates else "warn")

        # N-10c: a paragraph with almost no release words is probably invented (warn)
        low = []
        for p in paras:
            words = _content_words(p)
            if len(words) < 8:
                continue
            overlap = len(words & rel_words) / len(words)
            if overlap < 0.20:
                low.append(f"{round(overlap, 2)}: {p[:50]}")
        add("SENTENCE_SUPPORT", not low,
            f"{len(paras)} paragraphs checked" + (f"; low overlap: {low[:3]}" if low else ""),
            level="warn")
    else:
        add("NUMBERS_TRACE", False, "no release text found to trace against")
        add("QUOTE_TRACE", False, "no release text found to trace against")
        add("ENTITY_TRACE", False, "no release text found to trace against")
        add("SENTENCE_SUPPORT", False, "no release text found to trace against", level="warn")

    # images — the featured ladder + D-008
    feat = d["images"]["featured"]
    # one resolver for every consumer (D-C: a document crop is real but never published silently)
    fpath = assets.resolve(folder, feat["file"], feat["renamed"])
    crop = assets.is_document_crop(folder, fpath)
    add("FEATURED_EXISTS", bool(fpath),
        (feat["file"] or "no featured file recorded")
        + ("" if fpath else " (searched images/, originals/, the folder and the harvest folder)"))
    add("FEATURED_NOT_A_CROP", not crop,
        ("a DOCUMENT HEADER CROP (D-C): the letterhead was rendered, not supplied — a human must "
         "confirm or crop the logo itself") if crop else "supplied artwork or an embedded image")
    why = (feat.get("why") or "").lower()
    declared = "declared asset:" in why and bool(why.split("declared asset:")[-1].strip())
    add("FEATURED_DECLARED_ASSET", bool(fpath) or declared,
        "declared: " + why.split("declared asset:")[-1].strip()[:70] if declared
        else ("file on disk" if fpath else "no file AND no declared asset"))
    add("FEATURED_RENAME_TOKEN", RENAMED_TOKEN in feat["renamed"], feat["renamed"] or "no rename recorded")
    add("FEATURED_CAPTION", bool(feat["caption"]), (feat["caption"] or "missing")[:60])
    cap_bad = [t for t in ("*(", "[flag]", "confirm against", "unverified", "to be confirmed")
               if t in feat["caption"].lower()]
    add("CAPTION_CLEAN", not cap_bad,
        "editorial note inside the caption: " + ", ".join(cap_bad) if cap_bad
        else "one factual sentence")
    rung = feat["rung"].lower()
    if rung == "graph" or rung.startswith("graph"):
        add("FEATURED_RUNG_D008", False, "a GRAPH image is never the key visual (D-008)")
    else:
        add("FEATURED_RUNG_D008", rung in ALLOWED_RUNGS, rung or "rung missing")
    add("IN_BODY_COUNT", len(d["images"]["in_body"]) <= 6, f"{len(d['images']['in_body'])} in-body")

    ok = not any(r["level"] == "fail" and not r["ok"] for r in results)
    return {"ok": ok, "results": results, "draft": d}
