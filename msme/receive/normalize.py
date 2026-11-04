# =============================================================================
# FILE HEADER
# file    : msme/receive/normalize.py
# role    : Receive — Gmail message -> email model
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : parse subject/from/date/body, attachment inventory, links and remote body-image URLs; build
#           cleanBody (strip cover/disclaimer)
#           and resolve short/branded/tracker links to reveal hidden Drive folders.
# pages   : n/a
# calls   : gmail (decode helpers), urllib, re, html
# called  : pipeline.py
# amend   : cleanBody rules feed decide/extract; URL resolution is capped at 8 (network cost) — change deliberately.
#           Test: run one email and inspect the normalize stage detail
# =============================================================================
"""Normalize a Gmail message into the email model used by the pipeline.

Ports the n8n 'Filter & Normalize' node: subject/from/fromEmail/date/bodyText,
plus an attachment inventory (names/types/sizes) and links found in the body.

The result (`email model`) is what every later stage reads from.

Example model:
    {
      "from": "Editor MSME <editor@malaysiasme.com.my>",
      "fromName": "Editor MSME",
      "fromEmail": "editor@malaysiasme.com.my",
      "subject": "Fwd: [PRESS RELEASE] MALAYSIA'S EXPORTS...",
      "threadId": "1a0c6a780d5e67d8",
      "messageId": "1a0c6a780d5e67d8",
      "date": "Tue, 22 Sep 2026 10:30:00 +0800",
      "bodyText": "<full raw body>",
      "cleanBody": "<body minus cover/disclaimer/forwarders>",
      "attachments": [
        {"filename": "EN_RELEASE.docx", "mimeType": "...", "size": 12345, "attachmentId": "..."}
      ],
      "linksFound": ["https://drive.google.com/drive/folders/abc123..."],
      "bodyImageUrls": ["https://imagedelivery.net/.../public"],
      "rawEmail": "Subject: ...\nFrom: ...\n\n<full body>",
      "cleanRawEmail": "Subject: ...\nFrom: ...\n\n<cleaned body>",
    }
"""
import base64
import html as _html
import re
import urllib.request

from msme.receive import gmail


def _extract_address(v):
    """Pull just the email address out of a header like 'Name <a@b.com>'."""
    if not v:
        return ""
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", str(v))
    return m.group(0) if m else ""


def _display_name(v):
    """Strip angle-brackets/quotes from a From header to get the name only."""
    if v is None:
        return ""
    return re.sub(r"<[^>]*>", "", str(v)).replace('"', "").strip()


def _plain_text(html):
    """Convert an HTML email body to readable plain text (block→newline)."""
    t = re.sub(r"<style[\s\S]*?</style>", " ", html)
    t = re.sub(r"<script[\s\S]*?</script>", " ", t)
    t = re.sub(r"<br\s*/?>|</p>|</div>|</tr>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"&nbsp;", " ", t)
    t = re.sub(r"&amp;", "&", t)
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t).strip()


# ESP click-tracker hosts whose destination is NOT encoded in the URL and must
# be resolved by following the redirect (Campaign Monitor, SendGrid, Mailchimp…).
_TRACKER_HOSTS = (
    "cmail20.com", "createsend.com", "mjt.lu", "sendgrid.net", "mailchi.mp",
    "list-manage.com", "hubspotlinks.com", "hubspotemail.net", "exct.net",
    "sparkpostmail.com", "mailgun.org", "rs6.net", "clickdimensions.com",
)


# Browser-like headers: many brand/press-kit sites return 403 to bot UAs but
# hand a normal browser a redirect (e.g. go.mercedes-benz.com -> Drive folder).
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.4 Safari/605.1.15"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}


def _resolve_redirect(url, timeout=6):
    """Follow a link's redirect chain and return the FINAL url (or None).

    Works for ESP click-trackers AND branded/short links (e.g. a Mercedes
    press-kit short link that 307s to a Google Drive folder). urllib follows
    redirects automatically, so `geturl()` is the real destination. Tries GET
    first (some brand sites 403 on HEAD but answer a browser-like GET). Fail-safe:
    None on error.
    """
    for method in ("GET", "HEAD"):
        try:
            req = urllib.request.Request(url, method=method, headers=_BROWSER_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.geturl()
        except Exception:
            continue
    return None


def _decode_tracking_url(url):
    """Unwrap an email-service click-tracker into the real destination URL.

    Many ESPs (Mailjet `*.mjt.lu`, SendGrid, etc.) wrap every link in a
    redirect whose FINAL path segment is base64url of the real target. A
    Google Drive media-kit link is often hidden this way, so the raw body has
    no literal `drive.google.com/...` string and downstream link detection
    misses it. Returns the decoded http(s) URL, or None.

    Example:
        _decode_tracking_url("https://s6zik.mjt.lu/lnk/AAA/.../aHR0cHM6Ly9kcml2ZS5nb29nbGUuY29tL2RyaXZlL2ZvbGRlcnMvMXhP...")
        -> "https://drive.google.com/drive/folders/1xO8..."
    """
    try:
        seg = url.split("?")[0].rstrip("/").split("/")[-1]
        if len(seg) < 8:
            return None
        pad = "=" * (-len(seg) % 4)
        decoded = base64.urlsafe_b64decode(seg + pad).decode("utf-8", "ignore")
        if decoded.startswith(("http://", "https://")):
            return decoded
    except Exception:
        return None
    return None


def _clean_body(body):
    """Return a trimmed body for the AI: strip cover note, disclaimer, forward
    carrier headers, SendGrid/link-tracker URLs and social footers.

    Keeps the article portion (from the first real headline/dateline onward).
    The archived files use the FULL body; only the AI prompt input is cleaned.

    Example:
        _clean_body("Hi Isabel,\nPlease repurpose and publish.\n\n"
                    "---------- Forwarded message ---------\nFrom: X\n"
                    "[PRESS RELEASE] COMPANY LAUNCHES...\n\nDisclaimer: ...")
        -> "COMPANY LAUNCHES..."
    """
    if not body:
        return ""
    text = body
    # 1) Drop the MSME cover note + disclaimer up to the first forward marker,
    #    and drop the marker line itself.
    idx = text.find("---------- Forwarded message ---------")
    if idx != -1:
        text = text[idx + len("---------- Forwarded message ---------"):]
    # 2) Drop disclaimer/cover blocks that may appear again (line-by-line filter).
    lines = text.split("\n")
    out = []
    skip = False
    for ln in lines:
        s = ln.strip()
        low = s.lower()
        # skip disclaimer block
        if low.startswith("disclaimer:"):
            skip = True
            continue
        if skip:
            if low.startswith(("this e-mail", "this email", "if you are not", "opinions, conclusions")):
                continue
            skip = False
        # skip carrier header lines within a forward block
        if low in ("from:", "date:", "subject:", "to:", "cc:", "best regards,") or low.startswith(
            ("from: ", "date: ", "subject: ", "to: ", "cc: ")
        ):
            continue
        # skip link-tracker / social footer URLs
        if "sendgrid.net/ls/click" in low or low.startswith(("http://", "https://")):
            continue
        # skip "please repurpose and publish" cover line
        if low == "please repurpose and publish." or low == "hi isabel,":
            continue
        # skip short orphaned fragments (< 12 chars) that are just header residue
        if len(s) < 12 and not s.endswith("."):
            continue
        out.append(ln)
    cleaned = "\n".join(out)
    # collapse 3+ blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


# <img> URLs that are almost always tracking pixels / spacers / signature logos.
_IMG_SKIP_HINTS = ("/wf/open", "open?", "pixel", "beacon", "spacer", "1x1", "transparent",
                   "/mail-sig/", "signature")


def _image_urls(html):
    """Unique remote <img src> URLs from the HTML body (cap 12).

    Only http(s) — `cid:` (inline attachments) and `data:` are not remote
    images. Tracking pixels, spacers, signature logos and images declared small
    in the tag (`width`/`height` attributes) are dropped here; the real photo
    test happens after download in pipeline (`extract._kind_from_bytes`).

    Example:
        _image_urls('<img src="https://imagedelivery.net/.../public">')
        -> ["https://imagedelivery.net/.../public"]
        _image_urls('<img width="96" height="41" src=".../mail-sig/...">')
        -> []
    """
    out = []
    for tag in re.findall(r"<img\b[^>]*>", html or "", re.I):
        m = re.search(r"""src=["']([^"']+)["']""", tag, re.I)
        if not m:
            continue
        u = _html.unescape(m.group(1)).strip()
        if not u.startswith(("http://", "https://")):
            continue
        low = u.lower()
        if any(h in low for h in _IMG_SKIP_HINTS):
            continue
        # Display-size hint in the tag (a signature logo can be a big file, so
        # the bytes alone would look like a photo).
        w = re.search(r"""\bwidth=["']?(\d+)""", tag, re.I)
        h = re.search(r"""\bheight=["']?(\d+)""", tag, re.I)
        if w and h and (int(w.group(1)) <= 150 or int(h.group(1)) <= 60):
            continue
        if u not in out:
            out.append(u)
        if len(out) >= 12:
            break
    return out


def build_email_model(service, msg_id, message=None):
    """Fetch + normalize one Gmail message into the email model dict.

    Example:
        m = normalize.build_email_model(gmail_service, "1a0ea6d2dad4b996")
        m["cleanBody"]   # cleaned body for the AI
        m["linksFound"]  # ["https://drive.google.com/...", ...]
    """
    if message is None:
        message = gmail.get_message(service, msg_id)
    payload = message["payload"]
    parsed = gmail.parse_message(payload)
    headers = parsed["headers"]

    subject = headers.get("subject", "")
    from_raw = headers.get("from", "")
    from_name = _display_name(from_raw)
    from_email = _extract_address(from_raw)
    date = headers.get("date", "")

    text = parsed["text"]
    if not text and parsed["html"]:
        text = _plain_text(parsed["html"])
    body_text = text

    thread_id = message.get("threadId", "")
    msg_id_str = message.get("id", "")

    # Attachment inventory (names + types + sizes — bytes are downloaded later)
    attachments = []
    for att in parsed["attachments"]:
        attachments.append(
            {
                "filename": att["filename"],
                "mimeType": att["mimeType"],
                "size": att.get("size", 0),
                "attachmentId": att.get("attachmentId", ""),
            }
        )

    # Links found in the email body (used by the link-guard vs AI hallucination).
    # Visible text URLs + HTML href URLs (tag-stripping below drops href-only
    # links, which is how a branded press-kit button went missing).
    all_text = body_text + " " + re.sub(r"<[^>]+>", " ", parsed["html"])
    links = re.findall(r"https?://[^\s<>\"']+", all_text)
    links = [u.rstrip(".,;:)") for u in links if "malaysiasme.com.my" not in u]
    html_links = re.findall(r"""href=["'](https?://[^"']+)["']""", parsed["html"] or "")
    links += [_html.unescape(u).rstrip(".,;:)") for u in html_links if "malaysiasme.com.my" not in u]
    links_found = list(dict.fromkeys(links))
    # Anchor text helps the web probe tell "View the published release" from
    # a footer/social link. Keyed by the href; copied to resolved final URLs.
    link_texts = {}
    for m in re.finditer(r'<a\b[^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>',
                         parsed["html"] or "", re.I | re.S):
        href = _html.unescape(m.group(1)).strip()
        text = re.sub(r"<[^>]+>", " ", m.group(2))
        text = " ".join(_html.unescape(text).split())
        if href and text:
            link_texts[href] = (link_texts.get(href, "") + " " + text).strip()
    # Unwrap ESP click-trackers so hidden destinations (e.g. a Drive media-kit
    # folder behind a Mailjet redirect) are visible to link detection + the guard.
    for u in list(links_found):
        decoded = _decode_tracking_url(u)
        if decoded and decoded not in links_found:
            links_found.append(decoded)
            if u in link_texts and decoded not in link_texts:
                link_texts[decoded] = link_texts[u]
    # Reveal the destination of short/branded/tracker links by FOLLOWING the
    # redirect (e.g. go.mercedes-benz.com/2026AMGGT -> Google Drive folder).
    # Capped at 8 lookups per email to bound latency.
    resolved = 0
    for u in list(links_found):
        if resolved >= 8:
            break
        if not u.startswith(("http://", "https://")) or "drive.google.com" in u:
            continue
        resolved += 1
        final = _resolve_redirect(u)
        if final and final != u and final not in links_found:
            links_found.append(final)
            if u in link_texts and final not in link_texts:
                link_texts[final] = link_texts[u]

    return {
        "from": f"{from_name} <{from_email}>" if from_name else (from_email or from_raw),
        "fromName": from_name,
        "fromEmail": from_email,
        "subject": subject,
        "threadId": thread_id,
        "messageId": msg_id_str,
        "date": date,
        "bodyText": body_text,
        "cleanBody": _clean_body(body_text),
        "attachments": attachments,
        "linksFound": links_found,
        "linkTexts": link_texts,
        "bodyImageUrls": _image_urls(parsed["html"]),
        "rawEmail": (
            f"Subject: {subject}\nFrom: {from_raw}\nDate: {date}\n\n{body_text}"
        ),
        "cleanRawEmail": (
            f"Subject: {subject}\nFrom: {from_raw}\nDate: {date}\n\n{_clean_body(body_text)}"
        ),
    }
