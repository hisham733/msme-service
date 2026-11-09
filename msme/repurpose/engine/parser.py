"""parser.py — parse a skill draft (the cold-run format is the contract) into a Draft dict.

Contract sections (## headings): Branch · Title · Excerpt (news only) · Body · Categories ·
Images · Flags · Final check. Every '## ' section between Body and Categories is an article H2
subheader; '> ' lines are blockquotes (an attribution line '> — Name' attaches to the blockquote).

Sections are kept as an ORDERED list (name, lines) — never a name-keyed dict — so a repeated
heading stays visible (the validator must be able to catch it).
"""
import re
from pathlib import Path

SECTION = re.compile(r"^##\s+(.*)$")
RUNG_RE = re.compile(
    r"rung[^a-z]*(people|portrait|logo|event[\s-]*key[\s-]*visual|event[\s-]*visual|product|graph\w*)",
    re.I)
BODY_STOP = {"Categories", "Images", "Flags", "Final check"}


def _clean(t):
    return t.replace("**", "").replace("`", "").strip()


def _unquote(t):
    t = t.strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in '"“”':
        t = t[1:-1].strip()
    return t


def parse_draft(md_text: str) -> dict:
    ordered = []
    for ln in md_text.splitlines():
        m = SECTION.match(ln)
        if m:
            ordered.append((m.group(1).strip(), []))
        elif ordered:
            ordered[-1][1].append(ln)

    def text_of(name):
        for n, lines in ordered:
            if n == name:
                return "\n".join(lines).strip()
        return ""

    branch_raw = text_of("Branch")
    bm = re.search(r"\*\*\s*(news|commentary|signed opinion|byline)\b", branch_raw, re.I)
    if bm:
        branch = bm.group(1).lower()
    else:
        branch = ("commentary" if re.search(r"commentary", branch_raw, re.I)
                  else "byline" if re.search(r"byline|signed opinion", branch_raw, re.I)
                  else "news" if re.search(r"news", branch_raw, re.I) else "")

    title_lines = [l for l in text_of("Title").splitlines() if l.strip()]
    title = _clean(title_lines[0]) if title_lines else ""

    body_secs, started = [], False
    for name, lines in ordered:
        if name == "Body":
            started = True
        if not started:
            continue
        if name in BODY_STOP:
            break
        body_secs.append((name, lines))

    def collect(lines, sub, sid):
        blocks, cur_quote = [{"sub": sub, "sid": sid, "paras": [], "quotes": []}], None

        def flush_quote():
            nonlocal cur_quote
            if cur_quote:
                blocks[-1]["quotes"].append(cur_quote)
                cur_quote = None

        for ln in lines:
            s = ln.strip()
            if s.startswith(">"):
                q = s[1:].strip()
                if q:
                    if cur_quote is None:
                        cur_quote = []
                    cur_quote.append(q)
            elif not s:
                flush_quote()
                if blocks[-1]["paras"] or blocks[-1]["quotes"]:
                    blocks.append({"sub": sub, "sid": sid, "paras": [], "quotes": []})
            else:
                flush_quote()
                blocks[-1]["paras"].append(s)
        flush_quote()
        return [b for b in blocks if b["paras"] or b["quotes"]]

    body_blocks = []
    for sid, (name, lines) in enumerate(body_secs):
        body_blocks += collect(lines, None if name == "Body" else _clean(name), sid)

    cats_raw = text_of("Categories")
    if "·" in cats_raw:
        categories = [c.strip() for c in cats_raw.split("·") if c.strip()]
    else:
        categories = [_clean(l.lstrip("-").strip()) for l in cats_raw.splitlines() if l.strip()]

    img = {"featured": {"file": "", "renamed": "", "rung": "", "caption": ""},
           "in_body": [], "captions": {}}
    mode, last_cap_key = None, None
    feat = img["featured"]
    images_lines = []
    for name, lines in ordered:
        if name == "Images":
            images_lines = lines
            break
    for ln in images_lines:
        s = ln.strip()
        low = s.lower()
        if low.startswith("**featured") or low == "featured":
            mode = "featured"
        elif low.startswith("**in_body"):
            mode = "in_body"
        elif low.startswith("**captions"):
            mode = "captions"
        elif low.startswith("**classification"):
            mode = None
        if not s:
            continue
        if mode == "featured":
            fm = re.match(r"-\s*(file|renamed|why|rung|caption)\s*:\s*(.+)", s, re.I)
            if fm:
                feat[fm.group(1).lower()] = _unquote(_clean(fm.group(2)))
            inline = re.match(r"\*\*featured:?\*\*\s*(.+)", s, re.I)
            if inline:
                names = re.findall(r"`([^`]+)`", inline.group(1))
                if names:
                    feat["file"] = names[0].strip()
                if len(names) > 1:
                    feat["renamed"] = names[1].strip()
            cap_line = re.match(r"\*\*caption[^*]*\*\*:?\s*(.+)", s, re.I)
            if cap_line:
                feat["caption"] = _unquote(_clean(cap_line.group(1)))
            rm = RUNG_RE.search(s)
            if rm:
                feat["rung"] = re.sub(r"\s+", "-", rm.group(1).lower())
            feat["rung"] = re.sub(r"\s+", "-", feat["rung"].lower()) if feat["rung"] else ""
        elif mode == "in_body":
            entry = dict(re.findall(r"(file|renamed|position|caption)\s*:\s*`?([^`·]+)`?", s))
            if entry:
                img["in_body"].append({k: _unquote(_clean(v)) for k, v in entry.items()})
        elif mode == "captions":
            cm = re.match(r"-\s*`?([^`:]+)`?\s*:\s*[\"“](.*)$", s)
            if cm:
                last_cap_key = cm.group(1).strip()
                img["captions"][last_cap_key] = cm.group(2).strip()
            elif last_cap_key and not s.startswith("-"):
                img["captions"][last_cap_key] += " " + s.strip()

    if not feat["caption"]:
        key = feat.get("renamed") or feat.get("file")
        for k, v in img["captions"].items():
            if key and (key in k or k in key):
                feat["caption"] = v
                break

    flags_raw = []
    for name, lines in ordered:
        if name == "Flags":
            flags_raw = lines
            break
    flags = [s.strip("-> ").strip() for s in flags_raw
             if s.strip() and ("context opportunity" in s.lower() or "[flag]" in s.lower())]

    return {
        "branch": branch, "title": title, "excerpt": text_of("Excerpt"),
        "body": body_blocks, "categories": categories, "images": img,
        "flags": flags, "sections": [n for n, _ in ordered],
    }


def load_draft(path) -> dict:
    return parse_draft(Path(path).read_text(encoding="utf-8"))
