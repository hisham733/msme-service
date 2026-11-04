# =============================================================================
# FILE HEADER
# file    : msme/receive/web_fetch.py
# role    : Receive — public web article/speech fetch (HTML only, no auth)
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : in WEB_FETCH_MODE=probe, fetch public links and decide from the page whether it is an
#           article (og:type/JSON-LD/<article>/text); use its featured photo as media; ignore site
#           brand logos. known = configured hosts only; off = no web pages/images.
# pages   : n/a
# calls   : extract (_image_dims/_kind_from_bytes), config, settings_store
# called  : pipeline.py
# amend   : no AI here; stdlib HTML only. Never fetch private/local IPs or non-80/443 ports.
#           Test: python3 -m unittest tests.test_web_probe -v
# =============================================================================
"""Fetch a public HTML article and use its real media.

The 3-state switch is read in pipeline: `off` / `known` / `probe`.
- `known`: only the hosts/paths in WEB_KNOWN_SITES.
- `probe`: any public link from the email is content-probed; site brand logos are not media.
"""
import html as _html
import ipaddress
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

from msme import config, settings_store
from msme.receive import extract

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
_SKIP_HOSTS = (
    "facebook.com", "twitter.com", "x.com", "linkedin.com", "instagram.com",
    "youtube.com", "sendgrid.net", "mailchi.mp", "list-manage.com",
    "googletagmanager.com", "doubleclick.net",
)
_TRACKING_HOST_PREFIXES = ("links.", "click.", "track.", "email.", "go.", "mail.", "t.")
_BLOCK_PATHS = (
    "/unsubscribe", "/media/unsubscribe", "/login", "/signin", "/signup",
    "/register", "/account", "/cart", "/checkout", "/search", "/category/",
    "/tag/", "/author/", "/privacy", "/terms", "/cookie",
)
_ASSET_EXT = (
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".png", ".jpg", ".jpeg",
    ".gif", ".webp", ".svg", ".mp4", ".mp3",
)
_PATH_HINTS = (
    "/news/", "/newswire/", "/speech/", "/article", "/press-release", "/press_release",
    "/media-release", "/media_release", "/blog/", "/story/", "/opinion",
    "/commentary", "/newsroom/",
)
_ARTICLE_HOSTS = ("news.cision.com", "mynewsdesk.com")
_ANCHOR_HINTS = (
    "published release", "view release", "read more", "press release",
    "news release", "media release", "full release", "read the",
    "article", "siaran", "akhbar", "berita",
)


def _host_path(url):
    try:
        p = urllib.parse.urlparse(url or "")
        return (p.hostname or "").lower().rstrip("."), (p.path or "").lower()
    except Exception:
        return "", ""


def _is_blocked(url):
    """True for social/tracking/unsubscribe/login/asset links (never article pages)."""
    low = (url or "").lower()
    if not low.startswith(("http://", "https://")):
        return True
    host, path = _host_path(url)
    if not host:
        return True
    if host in ("localhost", "metadata.google.internal") or host.endswith(".local"):
        return True
    if any(h in low for h in _SKIP_HOSTS):
        return True
    if host.startswith(_TRACKING_HOST_PREFIXES):
        return True
    if any(p in path for p in _BLOCK_PATHS):
        return True
    if any(low.split("?")[0].endswith(ext) for ext in _ASSET_EXT):
        return True
    if any(h in low for h in ("drive.google.com", "onedrive.live.com", "1drv.ms", "app.box.com")):
        return True
    return False


def is_public_http(url):
    """True only for a public http(s) URL on port 80/443 (SSRF guard)."""
    try:
        p = urllib.parse.urlparse(url or "")
        if p.scheme not in ("http", "https"):
            return False
        if p.username or p.password:
            return False
        host = (p.hostname or "").lower().rstrip(".")
        if not host or host == "localhost" or host.endswith(".local"):
            return False
        if host == "metadata.google.internal":
            return False
        port = p.port or (443 if p.scheme == "https" else 80)
        if port not in (80, 443):
            return False
        infos = None
        for attempt in range(3):
            try:
                infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            except Exception:
                infos = None
            if infos:
                break
            if attempt < 2:
                time.sleep(0.4)
        if not infos:
            return False
        for info in infos:
            try:
                addr = ipaddress.ip_address(info[4][0])
            except Exception:
                continue
            if (addr.is_private or addr.is_loopback or addr.is_link_local
                    or addr.is_reserved or addr.is_multicast or addr.is_unspecified):
                return False
        return True
    except Exception:
        return False


def _parse_known(raw):
    out = []
    for line in re.split(r"[\n,]+", raw or ""):
        s = line.strip()
        if not s:
            continue
        if not s.startswith(("http://", "https://")):
            s = "https://" + s
        try:
            p = urllib.parse.urlparse(s)
            host = (p.hostname or "").lower().rstrip(".")
            path = (p.path or "").lower().rstrip("/")
        except Exception:
            continue
        if host:
            out.append((host, path))
    return out


def known_sites():
    """The configured known hosts/paths; an empty saved value means none."""
    try:
        raw = settings_store.get("WEB_KNOWN_SITES")
    except Exception:
        raw = None
    if raw is None:
        raw = config.WEB_KNOWN_SITES
    return _parse_known(raw)


def is_known_url(url):
    host, path = _host_path(url)
    if not host or _is_blocked(url):
        return False
    for h, prefix in known_sites():
        if host == h or host.endswith("." + h):
            if not prefix or path.startswith(prefix):
                return True
    return False


def is_article_url(url):
    """Known-host/path hint check (kept for tests and back-compat)."""
    if not url or _is_blocked(url):
        return False
    low = url.lower()
    if is_known_url(url):
        return True
    if "news.cision.com" in low:
        return "/r/" in low
    if any(h in low for h in _ARTICLE_HOSTS):
        return True
    return any(h in low for h in _PATH_HINTS)


def _looks_like_article(html, title, text, known=False):
    """Content probe: >=2 independent article signals, or a known host + text."""
    og_type = ""
    try:
        m = re.search(r'<meta[^>]+(?:property|name)=["\']og:type["\'][^>]+content=["\']([^"\']+)',
                      html or "", re.I)
        og_type = (m.group(1) if m else "").lower()
    except Exception:
        pass
    signals = {
        "og_type": "article" in og_type,
        "json_ld": bool(re.search(r'"@type"\s*:\s*"(?:NewsArticle|Article|BlogPosting)"',
                                  html or "", re.I)),
        "article_tag": bool(re.search(r"<article\b", html or "", re.I)),
        "title_text": bool((title or "").strip() and len(text or "") >= 500),
        "text": len(text or "") >= 500,
    }
    score = sum(1 for k, v in signals.items() if v and k != "text")
    is_article = score >= 2 or (known and signals["text"] and signals["title_text"])
    return is_article, signals


def candidate_links(trusted_links, link_texts=None, mode="probe"):
    """Pick web pages to fetch: anchor/known first, unknown probe capped."""
    mode = (mode or "probe").lower()
    if mode == "off":
        return []
    texts = link_texts or {}
    seen = set()
    rows = []
    for idx, raw in enumerate(trusted_links or []):
        url = _html.unescape((raw or "").strip())
        if not url or url in seen:
            continue
        seen.add(url)
        if _is_blocked(url) or not is_public_http(url):
            continue
        known = is_known_url(url)
        if mode == "known" and not known:
            continue
        anchor = any(h in (texts.get(url, "") or "").lower() for h in _ANCHOR_HINTS)
        hint = is_article_url(url)
        score = (3 if known else 0) + (2 if anchor else 0) + (1 if hint else 0)
        rows.append((score, idx, url, known))
    rows.sort(key=lambda r: (-r[0], r[1]))
    total = max(1, int(getattr(config, "COLLECT_MAX_WEB_LINKS", 3)))
    unknown_budget = max(0, int(getattr(config, "WEB_PROBE_MAX_LINKS", 2)))
    out = []
    for score, idx, url, known in rows:
        if len(out) >= total:
            break
        if not known:
            if unknown_budget <= 0:
                continue
            unknown_budget -= 1
        out.append(url)
    return out


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.capture = None
        self.buf = []
        self.paras = []
        self.title = ""
        self.h1 = ""
        self.meta = {}
        self.imgs = []
        self._in_title = False
        self._title_buf = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = dict(attrs)
        if tag in ("script", "style", "nav", "header", "footer", "aside",
                   "form", "button", "noscript", "svg"):
            self.skip += 1
            return
        if tag == "title":
            self._in_title = True
            self._title_buf = []
        elif tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key and a.get("content"):
                self.meta[key] = a["content"]
        elif tag == "img":
            src = a.get("src") or a.get("data-src") or ""
            if src:
                self.imgs.append(src)
        elif tag in ("p", "h1", "h2", "h3"):
            self.capture = tag
            self.buf = []
        elif tag == "br" and self.capture:
            self.buf.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("script", "style", "nav", "header", "footer", "aside",
                   "form", "button", "noscript", "svg"):
            if self.skip:
                self.skip -= 1
            return
        if tag == "title":
            self._in_title = False
            self.title = " ".join("".join(self._title_buf).split())
        elif tag == self.capture:
            txt = _html.unescape("".join(self.buf))
            txt = re.sub(r"[ \t]+", " ", txt)
            txt = re.sub(r"\n\s*\n+", "\n", txt).strip()
            if txt:
                if tag == "h1" and not self.h1:
                    self.h1 = " ".join(txt.split())
                self.paras.append(txt)
            self.capture = None
            self.buf = []

    def handle_data(self, data):
        if self._in_title:
            self._title_buf.append(data)
        if self.capture and not self.skip:
            self.buf.append(data)


def _fetch(url, max_bytes, timeout):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read(max_bytes + 1)
                return r.geturl(), (r.headers.get("Content-Type") or "").lower(), data
        except urllib.error.HTTPError:
            raise
        except Exception:
            if attempt == 2:
                raise
            time.sleep(0.5)


def _ext_for(data):
    if data[:2] == b"\xff\xd8":
        return ".jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return ".img"


def fetch_article(url, known=None):
    """Fetch one public page -> probe text/media.

    Returns `{ok, is_article, url, title, text, images, logos, publisher_logos,
    og_image, reason, detail}`. `ok` means fetched+parsed; `is_article` means the
    content probe accepted it. Site brand logos are in `publisher_logos`, never media.
    """
    out = {"ok": False, "is_article": False, "url": url, "title": "", "text": "",
           "images": [], "logos": [], "publisher_logos": [], "og_image": "",
           "reason": "", "detail": {}}
    if not is_public_http(url):
        out["reason"] = "not a public http(s) URL"
        return out
    try:
        final, ctype, raw = _fetch(url, config.WEB_FETCH_MAX_BYTES, config.WEB_FETCH_TIMEOUT)
    except Exception as e:
        out["reason"] = f"fetch failed: {str(e)[:120]}"
        return out
    if "html" not in ctype and "xml" not in ctype:
        out["reason"] = f"not HTML ({ctype[:40]})"
        return out
    try:
        html = raw.decode("utf-8", "replace")
    except Exception:
        out["reason"] = "decode failed"
        return out
    p = _Parser()
    try:
        p.feed(html)
        p.close()
    except Exception as e:
        out["reason"] = f"parse failed: {str(e)[:100]}"
        return out
    title = (p.meta.get("og:title") or p.h1 or p.title or "").strip()
    paras = [x for x in p.paras if x.strip()]
    for i, para in enumerate(paras):
        low = para.strip().lower()
        if len(para) > 120 and not low.startswith(("http://", "https://")):
            paras = paras[i:]
            break
    text = "\n\n".join(paras).strip()
    if not text and p.meta.get("description"):
        text = p.meta["description"].strip()
    if len(text) < 500:
        out["reason"] = f"no article text ({len(text)} chars)"
        out["detail"] = {"final": final[:300], "title": title}
        return out
    known = is_known_url(final) or is_known_url(url) if known is None else known
    is_article, signals = _looks_like_article(html, title, text, known=known)
    out.update({"ok": True, "is_article": is_article, "url": final,
                "title": " ".join(title.split()), "text": text,
                "detail": {"final": final[:300], "title": title, "textLen": len(text),
                           "signals": signals, "known": bool(known)}})
    if not is_article:
        out["reason"] = "not article-like"
        return out

    og = p.meta.get("og:image") or ""
    out["og_image"] = og
    # Publisher JSON-LD logo -> publisher logos (never media)
    lm = re.search(r'"logo"\s*:\s*\{[^}]*?"url"\s*:\s*"([^"]+)"', html, re.I)
    if lm:
        logo = urllib.parse.urljoin(final, _html.unescape(lm.group(1)))
        if logo not in out["publisher_logos"]:
            out["publisher_logos"].append(logo)

    cands = []
    for u in ([og] if og else []) + p.imgs:
        if not u or u.startswith("data:"):
            continue
        absu = urllib.parse.urljoin(final, _html.unescape(u))
        if not absu.startswith(("http://", "https://")):
            continue
        low = absu.lower()
        if any(x in low for x in ("logo", "icon", "/brand/", "default-meta-image")):
            if absu not in out["publisher_logos"]:
                out["publisher_logos"].append(absu)
            continue
        if absu not in cands:
            cands.append(absu)

    for i, u in enumerate(cands[:config.WEB_MAX_IMAGES], 1):
        try:
            _, ctype, data = _fetch(u, config.WEB_IMAGE_MAX_BYTES, config.WEB_FETCH_TIMEOUT)
        except Exception:
            continue
        if "image" not in ctype or not data:
            continue
        kind = extract._kind_from_bytes(data)
        if kind == "photo":
            out["images"].append({"url": u, "name": f"webphoto-{i}{_ext_for(data)}", "bytes": data})
        elif kind == "logo":
            if u not in out["publisher_logos"]:
                out["publisher_logos"].append(u)
    out["detail"]["images"] = len(out["images"])
    out["detail"]["publisherLogos"] = len(out["publisher_logos"])
    return out
