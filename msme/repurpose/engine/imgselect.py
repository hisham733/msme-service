"""imgselect.py — the image-selection skill as executable code.

The skill (`msme-image-select/SKILL.md`) says what to do; this module does it, so an image decision can
be reproduced, scored and diffed. Everything it knows was measured against 30 published MALAYSIA SME
articles (`analysis/imageeval/`).

Pipeline of one call
--------------------
1. gather     — loose images (images/, originals/) + whatever pipeline/harvest.py pulled out of the
                supplied .pdf/.docx. This is the receive-stage fix: MSME hides pictures in the
                attachment (measured: 10 of 17 "missing" TARGET images were inside the PDF/DOCX).
2. clean      — byte duplicates, icons, tracking pixels and near-blank strips are dropped.
3. see        — every survivor is read with a vision model (pipeline/vision.py); tags are cached.
4. context    — story type, organisations, named people and month come from the release text/draft.
5. decide     — the ladder, gated by story type (see RULEBOOK_IMAGE below).
6. name       — <Subject>_<Month>_<Year>_MALAYSIA-SME.ext, as the site does it.
7. caption    — optional: one factual sentence per used image, supplied facts only.

Run:  python -m pipeline.imgselect --folder "<EXACT NAME>" [--caption]
      python -m pipeline.imgselect --all
"""
from __future__ import annotations

import io
import json
import math
import re
from collections import Counter
from pathlib import Path

from msme import paths
from .config import load_config
from .scan import find_images, find_release_text

IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heif", ".heic"}
# A byte-size junk gate is UNSAFE: the smallest published TARGET featured image is a 2,423 B logo, and
# a flat wordmark on white is statistically identical to an email signature strip. Measured separately
# by a model probe (2026-10-23): a "small and wide / few colours" rule dropped accuracy 0.938 -> 0.785
# and flipped 8 logos into junk. So only a degenerate-DIMENSION gate is allowed here; every other junk
# decision is made by the vision tag.
MIN_BYTES = 2_000           # below this it is an empty stub, not a judgement about content
MIN_PIXELS = 3_000          # 55x55 — nothing publishable is smaller
MIN_LONG_SIDE = 64
MAX_IN_BODY = 6
RENAMED_TOKEN = "_MALAYSIA-SME."

MONTHS = ("JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER",
          "OCTOBER", "NOVEMBER", "DECEMBER")

# --- vocabulary used to read a vision tag's free-text subject (measured on the 30 pairs) ---------
GROUP_CUES = ("group photo", "posing", "pose", "on stage", "signing", "memorandum", "mou",
              "shaking hands", "handshake", "award", "plaque", "certificate", "ceremony",
              "line-up", "lineup", "ribbon", "delegation", "winners", "nominees", "panel",
              "team photo", "holding a", "holding the", "presentation of", "exchange of",
              "three people", "four people", "media launch")
CROWD_CUES = ("crowd", "audience", "attendees", "visitors", "shoppers", "queue", "booth", "kiosk",
              "shelves", "exhibition hall", "browsing", "matching tables", "booths", "livestream",
              "conference audience")
PORTRAIT_CUES = ("smiling", "portrait", "headshot", "seated", "podium", "speaking", "standing alone",
                 "arms crossed", "in a blazer", "in a patterned shirt")
# measured: the only product-hero featured images in 30 pairs are vehicles. Food/drink stories were
# people-first (Tealive, Wagyu), so the rung is restricted to manufactured goods.
PRODUCT_CUES = ("car", "coupe", "coupé", "sedan", "suv", "vehicle", "motorcycle", "device",
                "smartphone", "laptop", "machine", "convertible", "motor car", "roadster")
EVENTVIS_CUES = ("banner", "poster", "key art", "backdrop", "flyer", "billboard", "standee",
                 "workshop poster", "show banner")
ORG_SUFFIX = ("sdn bhd", "berhad", "bhd", "group", "bank", "association", "council", "ministry",
              "board", "agency", "company", "chamber", "federation", "institute", "university",
              "college", "corporation", "holdings", "capital", "insurance", "takaful", "media",
              "authority", "commission", "co-operative", "cooperative", "society", "limited", "plc",
              "retail chain")
TITLE_WORDS = ("chief", "executive", "officer", "ceo", "director", "president", "chairman",
               "founder", "head", "minister", "general manager", "managing", "partner", "leader",
               "country", "regional")
HERO_NAME_CUES = ("main photo", "group photo", "hero", "cover")
# words that are never the organisation, measured from the extraction failures on this corpus
GENERIC_ORG_WORDS = {
    "malaysia", "budget", "press", "statement", "media", "release", "single", "arrangement", "new",
    "the", "a", "an", "this", "that", "how", "why", "what", "opinion", "reader", "force", "future",
    "profession", "announces", "launches", "calls", "welcomes", "shares", "reaction", "response",
    "commentary", "giants", "among", "liberating", "september", "october", "november", "august",
    "kuala", "lumpur", "asia", "today", "says", "said", "unveils", "pioneering", "first"}
# a picture the release actually shipped outranks one mined out of an attachment's furniture
ORIGIN_BONUS = {"folder": 1.0, "docx-media": 0.4, "pdf-media": 0.0, "pdf-header": -2.0, "asset": 0.0}

RULEBOOK_IMAGE = [
    ("IMG_RUNG", "the featured image follows the evidence-based ladder",
     "rung in people / product / event-visual / logo (never graph)", "30 measured pairs · D-003"),
    ("IMG_EXISTS", "the chosen featured asset is on disk, or declared as a fetch",
     "file found in images/, originals/ or harvest/, else asset declared", "T-018 · D-003"),
    ("IMG_RENAME", "the rename follows the site convention",
     "Subject_Month_Year_MALAYSIA-SME.ext", "site practice · skill Step 4"),
    ("IMG_CAPTION", "every used image carries one factual sentence",
     "non-empty, one sentence, no editorial note", "MSME guideline · skill Step 5"),
    ("IMG_NO_GUESS", "no identity is invented",
     "a name appears only if the release names it", "skill rule 1 · MSME question 4"),
    ("IMG_INBODY", "in-body count inside the cap", "0-6 images", "skill Step 3"),
    ("IMG_NO_GRAPH_FEATURED", "a chart is never the key visual",
     "featured rung is not graph", "D-008 · MSME question 1"),
]


# ================================================================== candidates
def candidate_paths(folder: Path, harvest: bool = True) -> list[dict]:
    """Every picture the run may choose from, with where it came from."""
    folder = Path(folder)
    out, seen = [], set()

    def add(p: Path, source: str, origin: str = "folder"):
        key = str(p.resolve()).lower()
        if key in seen or not p.is_file():
            return
        seen.add(key)
        try:
            out.append({"path": p, "file": p.name, "source": source, "origin": origin,
                        "bytes": p.stat().st_size})
        except OSError:
            pass

    for p in find_images(folder):
        add(p, "folder")
    for sub in ("images", "originals"):
        d = folder / sub
        if d.is_dir():
            for p in sorted(d.rglob("*")):
                if p.suffix.lower() in IMG_EXT:
                    add(p, "folder")
    for p in sorted(folder.glob("*")):
        if p.suffix.lower() in IMG_EXT:
            add(p, "folder")
    if harvest:
        try:
            from .harvest import harvest_folder
            res = harvest_folder(folder)
            base = Path(res.get("harvest_dir", ""))
            for row in res.get("assets", []):
                p = base / row["file"]
                if p.exists():
                    add(p, "harvest", row.get("origin", "asset"))
        except Exception:  # noqa: BLE001 — harvest is an improvement, never a blocker
            pass
    return out


def _drop_obvious(cands: list[dict]) -> list[dict]:
    """Drop only what is degenerate. Never guess "junk" from pixels or file size (see MIN_BYTES)."""
    from PIL import Image
    keep = []
    for c in cands:
        if c["bytes"] < MIN_BYTES:
            continue
        if c["bytes"] < 20_000:                 # cheap: only small files can be degenerate
            try:
                with Image.open(c["path"]) as im:
                    w, h = im.size
                if max(w, h) < MIN_LONG_SIDE or w * h < MIN_PIXELS:
                    continue
            except Exception:                    # noqa: BLE001 — undecodable, leave it to the tagger
                pass
        keep.append(c)
    return keep


def dedupe_perceptual(cands: list[dict], threshold: float = 0.96) -> list[dict]:
    """Collapse near-duplicates ACROSS sources (a photo often ships loose *and* inside the .docx).

    Byte-deduping cannot see it: the .docx copy is re-encoded, so the two files differ byte for byte
    while showing the same photograph (live defect 2026-10-24: `Assisting Photo 1.jpg` and
    `docx_Byline Article - W_image1.jpeg` were both published in-body).
    """
    if len(cands) < 2:
        return cands
    try:
        from tools.imgtruth import fingerprint, similarity
    except Exception:  # noqa: BLE001
        try:
            from ..tools.imgtruth import fingerprint, similarity   # type: ignore
        except Exception:  # noqa: BLE001
            return cands
    keep, prints = [], []
    for c in sorted(cands, key=lambda x: -x["bytes"]):
        try:
            fp = fingerprint(c["path"])
        except Exception:  # noqa: BLE001
            keep.append(c)
            continue
        dup = next((k for k, kfp in zip(keep, prints) if similarity(fp, kfp)[0] >= threshold), None)
        if dup is not None:
            dup.setdefault("dupes", []).append(c["file"])
            continue
        keep.append(c)
        prints.append(fp)
    return keep


def dedupe(cands: list[dict]) -> list[dict]:
    """Byte duplicates collapse; the largest copy wins (it is the one worth publishing)."""
    import hashlib
    by_hash, uniq = {}, []
    for c in sorted(cands, key=lambda x: -x["bytes"]):
        try:
            sha = hashlib.sha256(c["path"].read_bytes()).hexdigest()
        except OSError:
            continue
        if sha in by_hash:
            by_hash[sha].setdefault("dupes", []).append(c["file"])
            continue
        c.setdefault("dupes", [])
        by_hash[sha] = c
        uniq.append(c)
    return uniq


# ================================================================== context
def read_texts(folder: Path) -> dict:
    folder = Path(folder)
    rel = find_release_text(folder)
    draft = folder / "draft.md"
    text = ""
    if rel:
        text = rel.read_text(encoding="utf-8", errors="replace")
    elif draft.exists():
        text = draft.read_text(encoding="utf-8", errors="replace")
    title = ""
    if draft.exists():
        m = re.search(r"^##\s*Title\s*\n+(.+)$", draft.read_text(encoding="utf-8", errors="replace"),
                      re.M)
        if m:
            title = m.group(1).strip()
    if not title:
        for line in text.splitlines():
            s = line.strip().lstrip("#").strip()
            if len(s) > 25 and not s.lower().startswith(("http", "link")):
                title = s
                break
    return {"release_text": text, "title": title, "release_file": rel.name if rel else ""}


def _scene_caption(tag: dict, ctx: dict) -> str:
    """A caption that describes the frame without naming anyone."""
    subj = _clean(tag.get("subject", "")) or "the event"
    subj = subj[:1].upper() + subj[1:]
    org = (ctx.get("orgs") or [""])[0]
    return f"{subj}{(' at ' + org) if org else ''}.".replace("..", ".")


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def acronym_orgs(text: str) -> list[str]:
    """Organisations the release itself names in short form: `Long Form (ACRONYM)`.

    Measured (T-020 turn 2, 2026-10-25): MICSEA's release writes "The Malaysian Industrial, Commercial,
    Service Employers Association (MICSEA)", but `org_candidates`' phrase pattern stops at the comma and
    offers `Malaysian Industrial` — so the declared asset, the rename and C2 all carried a fragment of
    the name. MALAYSIA SME published `MICSEA-Logo_June_2026_MALAYSIA-SME.jpg`, so the acronym is the
    subject the site uses. A release that spells its own acronym has already answered the question; this
    is the brand-alias step IMAGE_GUIDE §6 names as the next real mechanism (T-019), kept general.
    """
    out = []
    for m in re.finditer(r"\(([A-Z][A-Za-z0-9&.\-]{2,9})\)", text or ""):
        acro = m.group(1).upper()
        if not any(c.isalpha() for c in acro):
            continue
        words = re.findall(r"\b[A-Za-z][A-Za-z0-9&.\-]*", (text or "")[:m.start()][-160:])
        caps = [w for w in words if w[:1].isupper() and w.lower() not in ("the", "a", "an")]
        if len(caps) < len(acro):
            continue
        # the letters must spell the initials of the words immediately before the bracket, in order
        if "".join(w[0].upper() for w in caps[-len(acro):]) != acro:
            continue
        # and the release must actually keep using it as a short name, not define it once in passing
        if len(re.findall(rf"\b{re.escape(acro)}\b", text or "")) < 3:
            continue
        if acro not in out:
            out.append(acro)
    return out


def org_candidates(text: str, title: str, boost: str = "", lead_name: str = "") -> list[str]:
    """Capitalised 1-4-word sequences, weighted title > lead > body, org-like suffix, and the
    folder/release file name (the sender put the brand there — measured: FCM, PIKOM, MICSEA, MRCA,
    Global Electronics Association were all lost to a generic phrase without this)."""
    lead = " ".join((text or "").split()[:220])
    boost_tokens = {w.lower() for w in re.split(r"[^A-Za-z0-9]+", boost or "") if len(w) > 1}
    pat = re.compile(r"\b((?:[A-Z][A-Za-z&.\-']+)(?:\s+(?:of|and|&|the|for)?\s*"
                     r"(?:[A-Z][A-Za-z&.\-']+|[A-Z]{2,})){0,3})\b")
    score: Counter = Counter()
    for zone, weight in ((title, 5.0), (lead, 2.0), (text or "", 1.0)):
        for m in pat.finditer(zone or ""):
            phrase = _clean(m.group(1))
            words = phrase.split()
            if not (1 <= len(words) <= 4):
                continue
            if phrase.lower() in ("the", "a", "an", "this", "that"):
                continue
            if len(words) == 1 and words[0].isupper() and len(words[0]) <= 4:
                continue
            s = weight
            low = phrase.lower()
            if len(words) == 1 and low in GENERIC_ORG_WORDS:
                continue
            if words[0].lower() in GENERIC_ORG_WORDS:
                s -= 3.0
            if len(words) == 1 and not (phrase.isupper() and 2 <= len(phrase) <= 6):
                s -= 2.0            # a lone word is usually a topic, not an organisation
            if any(w.isupper() and 2 <= len(w) <= 6 for w in words):
                s += 2.0            # acronyms are organisations (FCM, PIKOM, AICPA, MRCA, OCBC)
            if any(low.endswith(" " + suf) or low == suf for suf in ORG_SUFFIX):
                s *= 2.2
            if len(words) >= 2 and phrase.isupper():
                s *= 1.3
            clean_phrase = not ({w.strip(".,&").lower() for w in words} & GENERIC_ORG_WORDS)
            if clean_phrase and boost_tokens and all(
                    w.strip(".,&").lower() in boost_tokens for w in words):
                s += 6.0
            if clean_phrase and boost and boost.lower().lstrip("- ").startswith(low):
                s += 8.0            # the sender leads with the organisation
            if clean_phrase and lead_name and lead_name.lower().lstrip("- ").startswith(
                    low.replace(" ", "-")):
                s += 12.0           # the release FILE name opens with the issuer
            # an organisation is what ANNOUNCES: "… survey finds", "… said", "… announced"
            tail = (text or "")[m.end():m.end() + 40].lower()
            if any(tail.lstrip(" ,'\"") .startswith(k) for k in
                   ("survey", "said", "says", "announced", "announces", "finds", "group",
                    "malaysia", "asia", "berhad", "sdn")):
                s += 4.0
            score[phrase] += s
    return [p for p, _ in score.most_common(40)]


def named_people(text: str) -> list[dict]:
    """`Name, Title of Org` / `Name said` — the people the release actually names."""
    out = []
    pat = re.compile(r"\b([A-Z][a-z'\-]+(?:\s+[A-Z][a-z'\-]+){1,3})\s*,?\s*"
                     r"((?:(?:[A-Z][A-Za-z&.\-']+\s*){1,6}?)(?:,)?\s*(?:of|at)\s+"
                     r"((?:[A-Z][A-Za-z&.\-']+)(?:\s+(?:[A-Z][A-Za-z&.\-']+|[A-Z]{2,})){0,4}))")
    for m in pat.finditer(text or ""):
        name, role, org = _clean(m.group(1)), _clean(m.group(2)), _clean(m.group(3))
        if not any(w in role.lower() for w in TITLE_WORDS):
            continue
        if name not in [o["name"] for o in out]:
            out.append({"name": name, "role": role, "org": org})
    for m in re.finditer(r"\b([A-Z][a-z'\-]+(?:\s+[A-Z][a-z'\-]+){1,3})\s+said\b", text or ""):
        name = _clean(m.group(1))
        if name not in [o["name"] for o in out]:
            out.append({"name": name, "role": "", "org": ""})
    return out[:12]


STORY_RULES = (
    ("commentary", ()),                       # measured from the pack's own labels, see story_type
    ("appointment", ("appointed", "appointment", "to succeed", "conclude his", "conclude her",
                     "tenure", "steps down", "takes over", "named as", "new ceo", "new chief")),
    ("product-launch", ("new model", "variant", "coupé", "coupe", "suv", "sedan", "smartphone",
                        "priced from", "now available at", "device", "new series",
                        # T-020 turn 3 (measured 2026-10-25): a release whose news is a vehicle
                        # prototype entering testing is a product launch, and MALAYSIA SME published
                        # the vehicle ("black Rolls-Royce convertible prototype on a road") while the
                        # skill offered the marque's wordmark. The cues are the release's own words:
                        # "PROJECT NIGHTINGALE, A COACHBUILD COLLECTION", "Prototype motor cars".
                        "prototype", "coachbuild", "motor car")),
    ("event", ("memorandum of understanding", "mou", "signing ceremony", "launch of", "officiated",
               "graced by", "opening ceremony", "awards night", "graduation", "agm", "anniversary",
               "expo 2026", "trade expo", "exhibition hall")),
    ("data-report", ("survey", "index", "study finds", "respondents", "per cent of", "data shows",
                     "statistics", "report finds")),
    ("statement", ("press statement", "press release statement", "statement", "calls for",
                   "call for", "urges the", "urges a", "welcomes the", "welcomes the government",
                   "in response to", "reaction to", "commentary on the budget", "shares perspective",
                   "responds to")),
)


COMMENTARY_MARKERS = ("opinion piece", "byline", "commentary", "column", "for your reader",
                      "in my view")


def story_type(text: str, branch: str = "", extra: str = "") -> tuple[str, list[str]]:
    low = ((text or "") + " " + (extra or "")).lower()
    if branch == "commentary" or any(k in (extra or "").lower() for k in COMMENTARY_MARKERS):
        return "commentary", ["commentary"]
    if any(k in low for k in ("memorandum of understanding", " mou ", "mou signed")):
        return "event", ["event"]
    hits = []
    for name, cues in STORY_RULES:
        n = sum(low.count(c) for c in cues)
        if n:
            hits.append((n, name))
    hits.sort(reverse=True)
    if branch == "commentary":
        return "commentary", [h[1] for h in hits]
    if not hits:
        return "news", []
    return hits[0][1], [h[1] for h in hits]


def month_year(text: str, folder_name: str = "", received: Path | None = None) -> tuple[str, str]:
    m = re.search(r"(\d{1,2})\s*(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|"
                  r"OCTOBER|NOVEMBER|DECEMBER)\s*(\d{4})", (text or "").upper())
    if m:
        return m.group(2).capitalize(), m.group(3)
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|"
                  r"December)\s+(\d{4})", text or "")
    if m:
        return m.group(1).upper(), m.group(2)
    for mon in MONTHS:
        if mon.capitalize() in (text or ""):
            y = re.search(r"\b(20\d\d)\b", text or "")
            return mon.capitalize(), (y.group(1) if y else "")
    # a byline piece often carries no date at all. "Undated" is not a month and breaks the site
    # convention (live defect 2026-10-24), so use the month the release arrived.
    if received is not None and Path(received).exists():
        import datetime
        d = datetime.date.fromtimestamp(Path(received).stat().st_mtime)
        return MONTHS[d.month - 1].capitalize(), str(d.year)
    return "", ""


# ================================================================== scoring
def _people_score(c: dict, ctx: dict | None = None) -> float:
    t = c.get("tag") or {}
    if t.get("kind") != "people":
        return -1.0
    if c.get("origin") == "pdf-header":
        return -1.0
    s = _clean(t.get("subject", "")).lower()
    people = int(t.get("people") or 0)
    score = 1.0 + min(people, 15) * 0.25
    if any(cue in s for cue in GROUP_CUES):
        score += 5.0
    if any(cue in s for cue in CROWD_CUES):
        score -= 5.0
    if people <= 1 and any(cue in s for cue in PORTRAIT_CUES):
        score -= 2.0
    if any(cue in c["file"].lower() for cue in HERO_NAME_CUES):
        score += 1.5
    score += ORIGIN_BONUS.get(c.get("origin", "folder"), 0.0)
    score += 0.30 * math.log10(max(c["bytes"], 10_000))
    # T-020 turn 4 (measured 2026-10-25): when several photographs compete, the one whose own content
    # names a player in THIS story is the marque's hero shot — BMW's release photographed a rider on a
    # BMW in dust, the oracle published that frame, and the skill took a handshake instead. A token of
    # the issuer, a brand, or a named person in the vision subject is evidence the picture is *about*
    # the story rather than merely shipped with it.
    if ctx:
        want = {w.lower() for o in (ctx.get("orgs") or [])[:6]
                for w in re.split(r"[^A-Za-z0-9]+", o) if len(w) > 2}
        want |= {w.lower() for o in (ctx.get("llm_brands") or [])[:6]
                 for w in re.split(r"[^A-Za-z0-9]+", o) if len(w) > 2}
        want |= {(p.get("name") or "").split()[-1].lower()
                 for p in (ctx.get("people") or []) if p.get("name")}
        if want and any(w in s for w in want if w):
            score += 3.0
        # The same evidence often sits in the supplied file NAME rather than in the pixels' description:
        # TARGET's own file for the SEAM cohort story is `Group Photo of IKEA Thought Partners ISE
        # Co-workers and Biji-biji Initiative Team.jpg`, while the skill took the generic
        # `Cohort 2 Group Photo Beacon Resort 2.jpg`. A longer token (>3) is required so that short
        # brand initials do not start matching every file in the folder.
        if want and any(w in c["file"].lower() for w in want if len(w) > 3):
            score += 3.0
    return score


def _product_score(c: dict, orgs: list[str] | None = None) -> float:
    t = c.get("tag") or {}
    if t.get("kind") not in ("product", "people"):
        return -1.0
    s = _clean(t.get("subject", "")).lower()
    hits = sum(1.0 for cue in PRODUCT_CUES if cue in s)
    people = int(t.get("people") or 0)
    named = any(len((o.split() or [""])[0]) > 3 and (o.split() or [""])[0].lower() in s
                for o in (orgs or [])[:3])
    wordy = any(w in s for w in ("poster", "banner", "key art", "backdrop", "infographic"))
    # food and drink are people-first: if they are HOLDING the product it is a people photograph
    # (Tealive, Wagyu). The product hero is a vehicle/device presented on its own (Mercedes-AMG).
    if "holding" in s and any(w in s for w in ("drink", "coffee", "cup", "bottle", "plate")):
        return -1.0
    # the product rung needs the product to be VISIBLE with someone presenting it, or a clear
    # vehicle/device shot. A brand name printed on a poster is not a product hero (measured: Tealive).
    if not hits and not (named and people >= 1 and not wordy):
        return -1.0
    return (hits + (1.0 if named and not wordy else 0.0)) * 2.0 - people * 0.5 \
        + 0.2 * math.log10(max(c["bytes"], 10_000))


def _eventvis_score(c: dict) -> float:
    t = c.get("tag") or {}
    # a poster/banner has to be a supplied picture; a document header or an image lifted out of a
    # PDF body is never the event key-visual (measured: it stole the Legacy Planning decision)
    if t.get("kind") != "event-visual" or c.get("origin") not in ("folder", "docx-media"):
        return -1.0
    s = _clean(t.get("subject", "")).lower()
    return 4.0 + (2.0 if any(cue in s for cue in EVENTVIS_CUES) else 0.0)


def _logo_score(c: dict, orgs: list[str] | None = None) -> float:
    t = c.get("tag") or {}
    if t.get("kind") != "logo":
        return -1.0
    # D-C (MG 2026-10-24): a PDF letterhead render is a picture of a PAGE, not supplied artwork.
    # It is never auto-published; it is offered to a human as a crop candidate instead.
    if c.get("origin") == "pdf-header":
        return -1.0
    score = 1.5 if c.get("origin") == "folder" else 1.0
    s = _clean(t.get("subject", "")).lower()
    for i, o in enumerate((orgs or [])[:8]):
        key = (o.split() or [""])[0].lower()
        if len(key) > 2 and key in s:
            score += 5.0 - i * 0.3
            break
    return score


def declare_kind(story: str, text: str, staged_hint: bool = False,
                 has_people_photo: bool = True) -> str:
    """Which asset must be fetched when the folder holds no usable picture.

    Measured against the 17 articles whose TARGET featured image was not a loose file: a staged
    launch/ceremony gets an event photograph, an expo gets its own banner, a byline gets the author's
    portrait, everything else gets the organisation's logo.

    `has_people_photo` (T-020 turn 1, measured 2026-10-25): 23 of the 52 scored folders hold nothing
    that carries the published picture, and in **16 of the 22 that have a rung TARGET published a
    logo** (event-visual 2, people 4). So an event-photograph declaration is only honest when the pack
    contains a photograph at all; asking a sender for a picture we have positive evidence they never
    sent is an unfillable request. On the new batch this cost two rows — Java Kapital and SME Malaysia
    — where TARGET published the organisation's logo.
    """
    low = (text or "").lower()
    if story == "commentary":
        return "people"                      # the byline author's portrait
    if any(k in low for k in (" expo", "trade fair", "trade show", "festival", "showcase 2026")):
        return "event-visual"                # an expo's own banner, whatever else it reports
    staged = bool(staged_hint) or any(k in low for k in ("launch event", "officiated", "graced by",
                                                         "at the launch",
                                    "held at", "took place at", "at a ceremony", "ceremony was",
                                    "at a media launch", "launched today", "at the event",
                                    "signing ceremony", "witnessed the"))
    if staged and has_people_photo:
        return "people"                      # a photograph of the event itself
    if story in ("statement", "data-report", "appointment"):
        return "logo"
    return "logo"


def choose(cands: list[dict], tags: dict, ctx: dict) -> dict:
    """The ladder, gated by story type. Returns the whole decision record."""
    story = ctx["story"]
    flags, audit, live = ctx["flags"], ctx["audit"], []
    for c in cands:
        t = tags.get(c["file"]) or {}
        if not t:
            audit.append({"file": c["file"], "skipped": "not tagged"})
            continue
        kind = t.get("kind", "unknown")
        if kind in ("junk", "unknown"):
            audit.append({"file": c["file"], "skipped": kind})
            continue
        c = {**c, "tag": t}
        c["graph_only"] = (kind == "graph")          # D-008: a graph may sit in-body only
        live.append(c)

    def best(fn):
        scored = [(fn(c), c) for c in live if not c.get("graph_only")]
        scored = [x for x in scored if x[0] > 0]
        return max(scored, key=lambda x: x[0])[1] if scored else None

    people = [c for c in live if c["tag"].get("kind") == "people" and not c.get("graph_only")]
    strong_people = [c for c in people if int(c["tag"].get("people") or 0) >= 2
                     or "group photo" in _clean(c["tag"].get("subject", "")).lower()]
    # measured: a supplied spokesperson portrait loses to the logo in a statement/data-report
    # (MICSEA, Legacy Planning) and wins only when the piece is about that person (IKEA, Boehringer,
    # MDEC). So the people rung needs the person to BE the story.
    person_is_story = story in ("commentary", "appointment")

    featured, rung, why = None, "", ""
    if story == "product-launch":
        c = best(lambda x: _product_score(x, ctx["orgs"]))
        if c:
            featured, rung = c, "product"
            why = f"product rung: product-launch story ({c['tag'].get('subject', '')[:56]})"
    if featured is None and strong_people and story not in ("commentary", "appointment"):
        c = max(strong_people, key=lambda x: _people_score(x, ctx))
        featured, rung = c, "people"
        why = f"people rung: a scene with the story's people ({c['tag'].get('subject', '')[:56]})"
    if featured is None and people and person_is_story:
        solo = [x for x in people if int(x["tag"].get("people") or 0) <= 1] or people
        c = max(solo, key=lambda x: _people_score(x, ctx)
                + (6.0 if any(cue in x["file"].lower() for cue in HERO_NAME_CUES) else 0.0)
                + (0.8 if int(x["tag"].get("people") or 0) == 1 else 0.0))
        featured, rung = c, "people"
        why = (f"people rung: the named subject of this {story} piece "
               f"({c['tag'].get('subject', '')[:50]})")
    if featured is None:
        c = best(_eventvis_score)
        if c:
            featured, rung = c, "event-visual"
            why = f"event key-visual ({c['tag'].get('subject', '')[:56]})"
    if featured is None:
        c = best(lambda x: _logo_score(x, ctx["orgs"]))
        if c:
            featured, rung = c, "logo"
            why = f"logo rung: {c['tag'].get('subject', '')[:56]}"
    if featured is None and people and story not in ("statement", "data-report"):
        c = max(people, key=lambda x: _people_score(x, ctx))
        featured, rung = c, "people"
        why = f"people rung: the only usable photograph, {story} story"

    asset = None
    if featured is None:
        kind = declare_kind(story, ctx["release_text"], ctx.get("llm_staged", False),
                            has_people_photo=bool(people))
        if kind == "event-visual":
            m = re.match(r"\s*([A-Z][A-Za-z0-9\-]+(?:\s+[A-Z][A-Za-z0-9\-]+){0,2})", ctx["title"])
            subject = _clean(m.group(1)) if m else (ctx["orgs"] or [ctx["title"][:40]])[0]
        else:
            acr = (ctx.get("acronyms") or [])
            subject = (acr[0] if acr else
                       (ctx["orgs"][0] if ctx["orgs"] else ctx["title"][:40])) or ctx["title"][:40]
        asset = {"kind": kind, "subject": subject, "fetch": True,
                 "why": "no usable picture in the folder — fetch from the release media kit or the "
                        "MSME media library (T-018)"}
        crops = [c["file"] for c in live if c.get("origin") == "pdf-header"]
        if crops:
            asset["crop_candidate"] = crops[0]
            asset["why"] += (f"; the supplied PDF header was rendered as `{crops[0]}` — a human may "
                            "crop the logo itself (D-C)")
        rung = kind
        flags.append(f"[FLAG] no usable image supplied — declared {kind} asset '{subject}' must be "
                     "fetched before build")

    # ---- in-body: further photographs, duplicates already collapsed
    used = {featured["file"]} if featured else set()
    in_body = []
    people_live = [c for c in live if c["tag"].get("kind") == "people"]
    # measured: only event / product-launch stories carried in-body images (Tealive 2, CAEXPO 4,
    # Wagyu 6, MYHK 1, Mercedes 6); every byline, statement and report was featured-only.
    if len(people_live) >= 3 and story in ("event", "product-launch"):
        for c in sorted([c for c in people_live if c["file"] not in used],
                        key=lambda c: -_people_score(c, ctx))[:4]:
            if _people_score(c, ctx) <= 0:
                continue
            in_body.append(c)
            used.add(c["file"])
    for c in live:
        if c.get("graph_only") and c["file"] not in used and len(in_body) < MAX_IN_BODY:
            in_body.append(c)
            used.add(c["file"])
    return {"featured": featured, "rung": rung, "why": why, "asset": asset,
            "in_body": in_body[:MAX_IN_BODY], "flags": flags, "audit": audit, "live": live}


# ================================================================== naming / captions
LOGO_WORDS = {"logo", "the", "a", "an", "wordmark", "mark", "of", "and", "on", "white", "background"}


def subject_token(ctx: dict, tag: dict | None = None) -> str:
    """A short hyphenated subject for the file name.

    Measured: the organisation extractor loses the brand on a third of the releases, but the picture
    itself is legible — a logo's own wording ("MRCA", "PIKOM", "SME Association of Malaysia") is the
    most reliable subject there is, so it wins when the chosen asset is a logo.
    """
    if tag and tag.get("kind") == "logo":
        words = [w for w in re.split(r"[^A-Za-z0-9]+", _clean(tag.get("subject", "")))
                 if w and w.lower() not in LOGO_WORDS]
        if words:
            return "-".join(words[:3])
    for o in (ctx.get("orgs") or [])[:3]:
        words = [w for w in re.split(r"[^A-Za-z0-9]+", o)
                 if w and w.lower() not in ("the", "of", "and", "for", "malaysia", "sdn", "bhd",
                                            "berhad")]
        if words:
            return "-".join(words[:3])
    if tag:
        words = [w for w in re.split(r"[^A-Za-z0-9]+", _clean(tag.get("subject", ""))) if len(w) > 2]
        if words:
            return "-".join(words[:3])
    return "Article"


def rename(base: str, month: str, year: str, n: int = 1, ext: str = ".jpg") -> str:
    if not month:                      # never emit a non-month: the site convention is Subject_Month
        import datetime
        month = MONTHS[datetime.date.today().month - 1].capitalize()
        year = year or str(datetime.date.today().year)
    stem = f"{base}_{month}{('_' + year) if year else ''}_MALAYSIA-SME"
    return f"{stem}{('-' + str(n)) if n > 1 else ''}{ext.lower()}"


CONTEXT_SYSTEM = """You read a Malaysian press release and report, in strict JSON, the organisation that
issued it and what kind of story it is. Judge only from the text. No prose."""

CONTEXT_PROMPT = """Return JSON:
{"issuer":"<the organisation that issued this release, as it writes its own name>",
 "brands":["<other organisations/brands the story is about>"],
 "story":"event|product-launch|appointment|commentary|data-report|statement|news",
 "event_staged":true|false,
 "people":["<full names of people the release names>"],
 "why":"<max 12 words>"}
story meanings: event = a launch/ceremony/MoU/award/expo the piece reports on; product-launch = a new
product/model is the subject; appointment = someone's appointment/tenure is the subject; commentary =
an opinion/byline piece; data-report = a survey/index/study is the news; statement = an organisation's
position on a policy/budget; news = anything else.
event_staged = true only if the release describes a physical event that was or will be held
("at the launch", "officiated by", "held at", "ceremony at")."""

CTX_CACHE = paths.DATA / "repurpose" / "ctx_cache.json"


def llm_context(folder: Path, texts: dict, cfg=None, model=None) -> dict:
    """The language half of the decision: who issued this release and what kind of story it is.

    Deterministic keyword rules get ~80% of these right; naming the issuer is exactly the kind of
    judgement an LLM makes from a title the way a sub-editor does. Cached per folder + release length.
    """
    import hashlib
    import json as _json
    cfg = cfg or load_config()
    key = hashlib.sha256((folder.name + "|" + str(len(texts.get("release_text") or "")) + "|v1")
                         .encode("utf-8")).hexdigest()[:24]
    cache = {}
    if CTX_CACHE.exists():
        try:
            cache = _json.loads(CTX_CACHE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            cache = {}
    if key in cache:
        return cache[key]
    ask = (f"Folder name: {folder.name}\n\n"
           f"Release (first 7000 chars):\n{(texts.get('release_text') or '')[:7000]}")
    try:
        from .vision import _post
        raw = _post(cfg, [{"role": "system", "content": CONTEXT_SYSTEM},
                          {"role": "user", "content": CONTEXT_PROMPT + "\n\n" + ask}],
                    model=model)
        i, j = raw.find("{"), raw.rfind("}")
        obj = _json.loads(raw[i:j + 1]) if i >= 0 and j > i else {}
    except Exception:  # noqa: BLE001
        obj = {}
    if isinstance(obj, dict) and obj.get("issuer"):
        obj["issuer"] = _clean(str(obj["issuer"]))
        cache[key] = obj
        try:
            CTX_CACHE.parent.mkdir(parents=True, exist_ok=True)
            CTX_CACHE.write_text(_json.dumps(cache, indent=1, ensure_ascii=False), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    return obj


CAPTION_SYSTEM = """You write ONE factual sentence captions for a Malaysian business news article.
Use only facts present in the supplied press release. Never invent a name, title, role, number or
place. If a person cannot be named from the release, caption the scene without naming them."""


def caption_one(ctx: dict, tag: dict, cfg=None, model=None) -> str:
    """One factual sentence from supplied facts. Falls back to a safe scene description."""
    cfg = cfg or load_config()
    names = ", ".join(p["name"] for p in ctx.get("people", [])[:12]) or "(none supplied)"
    ask = (f"Article title: {ctx.get('title', '')}\n"
           f"People named in the release: {names}\n"
           f"Organisations: {', '.join(ctx.get('orgs', [])[:5])}\n"
           f"What the photo actually shows (from an image reader): {tag.get('subject', '')} "
           f"({tag.get('people', 0)} people, text in image: {tag.get('text_in_image', '')})\n\n"
           f"Release (excerpt):\n{(ctx.get('release_text') or '')[:6000]}\n\n"
           "Write ONE sentence (max 28 words) for this photograph. No 'Picture shows', no quotes "
           "around it, no editorial note, no bracket. Reply with the sentence only.")
    try:
        from .vision import _post
        out = _clean(_post(cfg, [{"role": "system", "content": CAPTION_SYSTEM},
                                 {"role": "user", "content": ask}], model=model))
        out = out.strip('"“”').strip()
        if out and len(out.split()) >= 5:
            seen = _clean(f"{tag.get('subject','')} {tag.get('caption_facts','')}").lower()
            named = [p["name"] for p in (ctx.get("people") or [])
                     if p.get("name") and p["name"].split()[-1].lower() in out.lower()]
            # a name may only appear if the reader could see it in THIS frame
            if not any(n.split()[-1].lower() in seen for n in named):
                return _scene_caption(tag, ctx)
            return out
    except Exception:  # noqa: BLE001
        pass
    people = int(tag.get("people") or 0)
    org = (ctx.get("orgs") or ["the organisation"])[0]
    subj = _clean(tag.get("subject", "")) or "the event"
    return (f"{subj[:1].upper() + subj[1:]}"
            f"{', with ' + str(people) + ' people visible,' if people else ''} at {org}.")


# ================================================================== public entry point
def select(folder, cfg=None, captions: bool = False, tags: dict | None = None,
           use_llm: bool = False) -> dict:
    """Run the whole selection for one release folder. Returns the decision record."""
    folder = Path(folder)
    cfg = cfg or load_config()
    texts = read_texts(folder)
    branch = ""
    draft = folder / "draft.md"
    if draft.exists():
        m = re.search(r"^##\s*Branch\s*\n+\s*(\w+)",
                      draft.read_text(encoding="utf-8", errors="replace"), re.M)
        branch = (m.group(1).lower() if m else "")
    story, story_hits = story_type(texts["release_text"], branch,
                                   " ".join([folder.name.replace("-", " "), texts["title"],
                                             (texts["release_file"] or "").replace("-", " ")]))
    branch = branch
    rel = find_release_text(folder)
    month, year = month_year(texts["release_text"], folder.name, rel)
    llm = llm_context(folder, texts, cfg=cfg) if use_llm else {}
    # T-020 turn 3 (measured 2026-10-25): a rule change to STORY_RULES was a silent no-op because the
    # cached LLM answer won. `news` is what the model returns when it has no better label — it is the
    # absence of a classification, so it must not overwrite one the release's own words gave:
    # Rolls-Royce's "PROJECT NIGHTINGALE, A COACHBUILD COLLECTION" + "Prototype motor cars" is a
    # product launch, and TARGET published the car.
    if llm.get("story") in ("event", "product-launch", "appointment", "commentary", "data-report",
                            "statement", "news"):
        if not (llm["story"] == "news" and story != "news"):
            story = llm["story"]
    ctx = {
        "title": texts["title"], "release_text": texts["release_text"],
        "llm_issuer": llm.get("issuer", ""),
        "llm_brands": llm.get("brands") or [],
        "llm_staged": bool(llm.get("event_staged")),
        "llm_people": llm.get("people") or [],
        "orgs": org_candidates(texts["release_text"], texts["title"],
                               folder.name + " " + (texts["release_file"] or ""),
                               (texts["release_file"] or "").replace(".md", "")),
        "people": named_people(texts["release_text"]),
        "story": story, "story_hits": story_hits, "month": month, "year": year,
        "flags": [], "audit": [],
    }

    if ctx.get("llm_issuer"):
        first = re.split(r"\s+(?:and|x|&|with|partners?)\s+|,", ctx["llm_issuer"])[0].strip()
        ctx["llm_issuer"] = first or ctx["llm_issuer"]
        ctx["orgs"] = [ctx["llm_issuer"]] + [o for o in ctx["orgs"]
                                             if o.lower() != ctx["llm_issuer"].lower()]
    # The release's own acronym is the subject a *declaration* should name (turn 2, measured
    # 2026-10-25). It is deliberately NOT pushed into `orgs`, because `orgs` also drives the rename
    # token, and rewriting that on every release with a parenthesised acronym traded 4 rows away for 1
    # (CAL 78.1 -> 75.0, B3 60.0 -> 55.0) — the rename was already carrying TARGET's tokens by then.
    ctx["acronyms"] = acronym_orgs(texts["release_text"])
    if ctx.get("llm_people"):
        have = {p["name"] for p in ctx["people"]}
        ctx["people"] = [{"name": n, "role": "", "org": ""} for n in ctx["llm_people"]
                         if n not in have] + ctx["people"]

    cands = dedupe_perceptual(dedupe(_drop_obvious(candidate_paths(folder))))
    if tags is None:
        from .vision import tag_folder
        tags = tag_folder([c["path"] for c in cands], cfg=cfg)
    decision = choose(cands, tags, ctx)

    base = subject_token(ctx, decision["featured"]["tag"] if decision["featured"] else None)
    out = {
        "folder": folder.name, "story": story, "orgs": ctx["orgs"][:6],
        "people_named": [p["name"] for p in ctx["people"]],
        "month_year": [month, year], "rung": decision["rung"], "why": decision["why"],
        "featured": None, "asset": decision["asset"], "in_body": [],
        "flags": decision["flags"], "audit": decision["audit"], "candidate_count": len(cands),
    }
    if decision["featured"]:
        f = decision["featured"]
        out["featured"] = {
            "file": f["file"], "path": str(f["path"]), "source": f["source"],
            "origin": f.get("origin", "folder"),
            "renamed": rename(base, month, year, 1, f["path"].suffix), "rung": decision["rung"],
            "people": f["tag"].get("people", 0), "subject": f["tag"].get("subject", ""),
            "caption": "", "why": decision["why"],
        }
        if captions:
            out["featured"]["caption"] = caption_one(ctx, f["tag"], cfg=cfg)
    for i, c in enumerate(decision["in_body"], start=2):
        out["in_body"].append({
            "file": c["file"], "path": str(c["path"]), "source": c["source"],
            "origin": c.get("origin", "folder"),
            "renamed": rename(base, month, year, i, c["path"].suffix),
            "people": c["tag"].get("people", 0), "subject": c["tag"].get("subject", ""),
            "caption": caption_one(ctx, c["tag"], cfg=cfg) if captions else "",
        })
    return out


def to_draft_block(sel: dict) -> str:
    """Render the `## Images` section exactly as the draft contract wants it."""
    lines = ["## Images", "", "**featured**"]
    if sel["featured"]:
        f = sel["featured"]
        lines += [f"- file: `{f['file']}`", f"- renamed: `{f['renamed']}`",
                  f"- rung: {f['rung']}", f"- caption: \"{f['caption']}\"",
                  f"- why: {f['why']}"]
    else:
        a = sel.get("asset") or {}
        lines += ["- file: `(none supplied)`", "- renamed: `(blocked)`", f"- rung: {sel['rung']}",
                  "- caption: \"\"",
                  f"- why: {a.get('why', 'no usable image')} — declared asset: "
                  f"{a.get('kind', '')} '{a.get('subject', '')}'"]
    lines += ["", "**in_body[]**"]
    if sel["in_body"]:
        for i, c in enumerate(sel["in_body"], 1):
            lines.append(f"{i}. file: `{c['file']}` · renamed: `{c['renamed']}` · "
                         f"position: after the relevant section · caption: \"{c['caption']}\"")
    else:
        lines.append("(none — featured-only is the common case)")
    lines += ["", "**captions**"]
    if sel["featured"]:
        lines.append(f"- `{sel['featured']['renamed']}`: \"{sel['featured']['caption']}\"")
    for c in sel["in_body"]:
        if c["caption"]:
            lines.append(f"- `{c['renamed']}`: \"{c['caption']}\"")
    return "\n".join(lines)


def rulebook() -> list[dict]:
    return [{"code": c, "what": w, "threshold": t, "source": s} for c, w, t, s in RULEBOOK_IMAGE]


if __name__ == "__main__":
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    cfg = load_config()
    root = Path(cfg["email_articles_root"])
    if "--all" in sys.argv:
        for d in sorted(p for p in root.iterdir() if p.is_dir()):
            try:
                s = select(d, cfg=cfg, captions="--caption" in sys.argv)
            except Exception as e:  # noqa: BLE001
                print(f"{d.name[:50]:52} ERROR {type(e).__name__}: {e}")
                continue
            f = s["featured"]
            picked = f["file"][:30] if f else "(declare: " + str(
                (s.get("asset") or {}).get("subject"))[:16] + ")"
            print(f"{d.name[:42]:44} {s['story'][:13]:14} {s['rung'][:12]:13} {picked}")
    else:
        name = sys.argv[sys.argv.index("--folder") + 1]
        sel = select(root / name, cfg=cfg, captions="--caption" in sys.argv)
        print(json.dumps(sel, indent=1, ensure_ascii=False))
        print("\n" + to_draft_block(sel))
