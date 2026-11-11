"""build_site.py — stage 4-5: render article .html + regenerate the DLW index (one script).

Placement (§2 = A): each article renders to <release folder>/site/<slug>.html; images stay in the
release folder; DLW/ = index.html + assets/css + data/articles.js linking across via relative
prefixes derived from config.json (the single edit point after export).

The writer sits behind the Uploader interface — the real Upload stage replaces dlw_writer with
wp_uploader without touching the stages above.
"""
import html as html_mod
import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from .parser import load_draft

CSS = """
:root{--txt:#111111;--acc:#ea7423;--meta:#999999;--blue:#0c599e}
*{box-sizing:border-box}html{font-size:62.5%}
body{margin:0;background:#fff;color:var(--txt);font:400 1.6rem/1.65 'Lato',Verdana,Arial,sans-serif}
h1,h2,h3,blockquote{font-family:'Montserrat',Arial,sans-serif;font-weight:700;color:var(--txt)}
h1{font-size:2.8rem;line-height:1.25;margin:0 0 14px}h2{font-size:2.4rem;margin:34px 0 10px}
p{margin:0 0 18px}a{color:var(--acc);text-decoration:none}
.wrap{max-width:1104px;margin:0 auto;padding:0 18px}
.meta{color:var(--meta);font-size:1.2rem;text-transform:uppercase;margin:10px 0 22px}
img{max-width:100%;height:auto}
.cover{max-width:1104px;margin:0 auto}
.cover img{width:100%;max-height:540px;object-fit:cover;display:block}
.title-band{background:var(--blue);color:#fff;padding:34px 0;margin-bottom:26px}
.cats{color:var(--acc);font-size:1.2rem;text-transform:uppercase;letter-spacing:.4px;margin-bottom:10px}
.title-band h1{color:#fff;max-width:900px}
.standfirst{font-weight:700;font-size:1.8rem;line-height:1.5;margin-bottom:22px}
blockquote{border-left:4px solid var(--acc);margin:24px 0;padding:6px 0 6px 20px;font-size:2rem;line-height:1.5}
blockquote .att{display:block;margin-top:8px;font:400 1.4rem 'Lato',sans-serif;color:var(--meta)}
figure{margin:24px 0}figure img{width:100%;height:auto;display:block}figcaption{color:var(--meta);font-size:1.2rem;padding-top:6px}
footer.dlw{color:var(--meta);font-size:1.2rem;padding:30px 0;text-align:center}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:26px 22px;margin:26px 0}
.card img{width:100%;aspect-ratio:249/140;object-fit:cover;display:block}
.card h2{font-size:1.6rem;line-height:1.35;margin:8px 0 0}
.card a{color:var(--txt)}.card a:hover{color:var(--acc)}
.loadbar{text-align:center;padding:16px 0 40px}
.load-more{background:var(--acc);color:#fff;border:0;padding:12px 34px;font:700 1.4rem 'Montserrat',sans-serif;text-transform:uppercase;cursor:pointer}
@media(max-width:900px){.grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.grid{grid-template-columns:1fr}}
"""

INDEX_SHELL = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>News — Malaysia SME (DLW)</title>
<link rel="stylesheet" href="assets/fonts/fonts.css">
<link rel="stylesheet" href="assets/css/msme.css">
</head><body>
<main class="wrap"><div class="grid" id="grid"></div>
<div class="loadbar"><button class="load-more" id="more">Load more</button></div></main>
<footer class="dlw">DLW — local upload-stage demo (not the live site)</footer>
<script src="data/articles.js"></script>
<script>
var PAGE = 8, shown = 0, grid = document.getElementById('grid'), btn = document.getElementById('more');
function card(a){var d=document.createElement('article');d.className='card';
  var img=(a.image?'<a href="'+a.url+'"><img src="'+a.image+'" alt=""></a>':'');
  d.innerHTML=img+'<h2><a href="'+a.url+'">'+a.title+'</a></h2>';return d;}
function fill(){var next=DLW_ARTICLES.slice(shown,shown+PAGE);
  next.forEach(function(a){grid.appendChild(card(a))});shown+=next.length;
  btn.style.display=shown>=DLW_ARTICLES.length?'none':'inline-block';}
btn.addEventListener('click',fill);fill();
</script></body></html>
"""

ARTICLE_TPL = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ — Malaysia SME (DLW)</title>
<link rel="stylesheet" href="__CSS__/assets/fonts/fonts.css">
<link rel="stylesheet" href="__CSS__/assets/css/msme.css">
</head><body>
__COVER__
<div class="title-band"><div class="wrap">__CATS__<h1>__TITLE__</h1></div></div>
<main class="wrap entry">
<div class="meta">__DATE__</div>
__STANDFIRST__
__BODY__
</main>
<footer class="dlw">DLW — local upload-stage demo (not the live site)</footer>
</body></html>
"""


def esc(t):
    return html_mod.escape(t or "", quote=False)


def rel_path(target: Path, start: Path):
    return Path(os.path.relpath(Path(target).resolve(), Path(start).resolve())).as_posix()


def find_image(folder: Path, names):
    """First existing candidate: images/ · originals/ · folder · the harvest folder (pipeline/assets.py).

    The harvest folder matters: the image skill may choose a picture mined out of the supplied
    .pdf/.docx, which lives under Files_from_MSME/_harvest/<slug>/.
    """
    from .assets import resolve
    return resolve(folder, *[n for n in names if n])


def _quote_html(qlines):
    text_lines = [l for l in qlines if not (l.startswith("—") or l.startswith("- "))]
    att = [l for l in qlines if l.startswith("—") or l.startswith("- ")]
    out = "<blockquote>" + esc(" ".join(text_lines))
    if att:
        out += f'<span class="att">{esc(" ".join(att).lstrip("—- ").strip())}</span>'
    return out + "</blockquote>"


def _links_html(links):
    """N-3/N-4: the report/speech line, appended at BUILD time so draft.md stays URL-free."""
    links = links or {}
    parts = []
    style = 'style="margin-top:1.6em;border-top:1px solid #eee;padding-top:1em"'
    if links.get("reportUrl"):
        u = links["reportUrl"]
        parts.append(f'<p {style}><strong>Read the full report:</strong> '
                     f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(u)}</a></p>')
    if links.get("speechUrl"):
        u = links["speechUrl"]
        parts.append(f'<p {style}><strong>Read the minister&rsquo;s speech:</strong> '
                     f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(u)}</a></p>')
    return "\n".join(parts)


def render_article(draft: dict, assets: dict, links=None) -> str:
    """Render one article. assets = {"cover": rel-src|None, "in_body": {key: rel-src}}.

    `links` (optional) is the folder's meta.json (reportUrl/speechUrl); it is appended
    at the end of the body AFTER validation, because the validator rejects URLs in the
    draft body (`NO_CONTACTS_BOILERPLATE`).

    The page lives in DLW\\articles\\, so every asset path is short and relative (../images/…) —
    Windows browsers refuse file paths over ~260 characters (measured 2026-10-23: a 272-char path
    gave ERR_FILE_NOT_FOUND in Edge while the file existed).
    """
    feat = draft["images"]["featured"]
    cover = f'<div class="cover"><img src="{esc(assets.get("cover") or "")}" alt=""></div>' if assets.get("cover") else ""
    cats = f'<div class="cats">{esc(" , ".join(draft["categories"]))}</div>' if draft["categories"] else ""
    stand = f'<div class="standfirst">{esc(draft["excerpt"])}</div>' if draft["excerpt"] else ""

    inserts = {}
    for im in draft["images"]["in_body"]:
        pos_after = im.get("position", "").lower().split("after ", 1)[-1].strip('"').strip()
        src = assets.get("in_body", {}).get(im.get("file") or im.get("renamed"))
        if not pos_after or not src:
            continue
        matches = [i for i, b in enumerate(draft["body"])
                   if b["sub"] and pos_after in b["sub"].lower()]
        if not matches:
            continue
        cap = draft["images"]["captions"].get(im.get("renamed"), im.get("caption", ""))
        inserts.setdefault(max(matches), []).append(
            f'<figure><img src="{esc(src)}" alt="">'
            f'<figcaption>{esc(cap)}</figcaption></figure>')

    parts = []
    prev_sub = None
    for i, b in enumerate(draft["body"]):
        if b["sub"] and b["sub"] != prev_sub:
            parts.append(f"<h2>{esc(b['sub'])}</h2>")
        prev_sub = b["sub"] or prev_sub
        for q in b["quotes"]:
            parts.append(_quote_html(q))
        for p in b["paras"]:
            parts.append(f"<p>{esc(p)}</p>")
        parts += inserts.get(i, [])
    body_html = "\n".join(parts)
    links_html = _links_html(links)
    if links_html:
        body_html = body_html + "\n" + links_html

    date = ""
    m = re.search(r"(\d{1,2} [A-Z]+ \d{4})", draft["excerpt"])
    if m:
        date = m.group(1)
    return (ARTICLE_TPL
            .replace("__TITLE__", esc(draft["title"]))
            .replace("__CSS__", "..")
            .replace("__COVER__", cover)
            .replace("__CATS__", cats)
            .replace("__DATE__", esc(date))
            .replace("__STANDFIRST__", stand)
            .replace("__BODY__", body_html))


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)[:70] or "article"


class DlwWriter:
    """The current uploader implementation: regenerate the DLW index + articles.js."""

    def write(self, cfg, entries):
        dlw = Path(cfg["dlw_root"]); dlw = dlw if dlw.is_absolute() else (Path(__file__).resolve().parent.parent / dlw)
        (dlw / "data").mkdir(parents=True, exist_ok=True)
        (dlw / "assets" / "css").mkdir(parents=True, exist_ok=True)
        css_path = dlw / "assets" / "css" / "msme.css"
        if not css_path.exists():
            css_path.write_text(CSS, encoding="utf-8")
        (dlw / "index.html").write_text(INDEX_SHELL, encoding="utf-8")
        (dlw / "data" / "articles.js").write_text(
            "var DLW_ARTICLES=" + json.dumps(entries, ensure_ascii=False) + ";", encoding="utf-8")
        return dlw / "index.html"


class WordPressUploader:
    """The real Upload stage (later): post to WordPress — built when MSME credentials exist."""

    def write(self, cfg, entries):
        raise NotImplementedError("Real WordPress upload replaces the DLW writer at that stage "
                                  "(no credentials locally — by design).")


def _seed_fonts(dlw: Path) -> None:
    """Copy the vendored site fonts into the output root when they are missing."""
    import shutil
    src = Path(__file__).resolve().parent / "dlw_shell" / "fonts"
    dst = dlw / "assets" / "fonts"
    if not src.is_dir():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.iterdir():
        if p.is_file() and not (dst / p.name).exists():
            shutil.copy2(p, dst / p.name)


def build_all(cfg):
    """Render every validated release folder into DLW\\articles + copy its images into DLW\\images."""
    import shutil
    from . import scan
    root = Path(cfg["email_articles_root"]); root = root if root.is_absolute() else (Path(__file__).resolve().parent.parent / root)
    dlw = Path(cfg["dlw_root"]); dlw = dlw if dlw.is_absolute() else (Path(__file__).resolve().parent.parent / dlw)
    _seed_fonts(dlw)
    (dlw / "articles").mkdir(parents=True, exist_ok=True)
    (dlw / "images").mkdir(parents=True, exist_ok=True)
    entries, pages = [], set()
    built = 0
    for item in scan.scan_all(cfg):
        folder = Path(item["path"])
        run = item["run"] or {}
        if not (folder / "draft.md").exists():
            continue
        if not run.get("validator", {}).get("ok"):
            continue
        draft = load_draft(folder / "draft.md")
        try:
            report_links = json.loads((folder / "meta.json").read_text(encoding="utf-8")) or {}
        except Exception:
            report_links = {}
        assets = {"cover": None, "in_body": {}}
        for im, key in [(draft["images"]["featured"], "cover")] + [
                (x, x.get("file") or x.get("renamed")) for x in draft["images"]["in_body"]]:
            src = find_image(folder, [im.get("file"), im.get("renamed")])
            if not src:
                continue
            name = im.get("renamed") or src.name
            shutil.copy2(src, dlw / "images" / name)
            ref = "../images/" + quote(name, safe="")
            if key == "cover":
                assets["cover"] = ref
            else:
                assets["in_body"][key] = ref
        slug = slugify(draft["title"])
        page = dlw / "articles" / f"{slug}.html"
        page.write_text(render_article(draft, assets, links=report_links), encoding="utf-8")
        pages.add(page.name)
        old_site = folder / "site"
        if old_site.is_dir():
            for stale in old_site.glob("*.html"):
                stale.unlink()
        m = re.search(r"(\d{1,2} [A-Z]+ \d{4})", draft["excerpt"])
        date = datetime.strptime(m.group(1), "%d %B %Y").strftime("%Y-%m-%d") if m \
            else datetime.now().strftime("%Y-%m-%d")
        entries.append({
            "title": draft["title"],
            "url": "articles/" + quote(page.name, safe=""),
            "image": ("images/" + quote(assets["cover"].split("/")[-1], safe="")) if assets.get("cover") else "",
            "date": date, "cats": draft["categories"][:4],
            # Last publish = the last engine run for this release (run.json updated).
            "published": run.get("updated") or "",
        })
        built += 1
    for stale in (dlw / "articles").glob("*.html"):
        if stale.name not in pages:
            stale.unlink()
    entries.sort(key=lambda e: (e.get("published") or "", e.get("date") or ""), reverse=True)
    index_path = DlwWriter().write(cfg, entries)
    return {"built": built, "index": str(index_path)}
