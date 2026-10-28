"""T-043 tests: 3-state web fetch, article probe, publisher logos, WebP, SSRF.

Run: python3 -m unittest tools.test_web_probe -v
"""
import socket
import unittest
from unittest.mock import patch

import config
import extract
import web_fetch

PUBLIC_INFO = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]


def _vp8(w, h):
    payload = b"\x00\x00\x00\x9d\x01\x2a" + w.to_bytes(2, "little") + h.to_bytes(2, "little")
    chunk = b"VP8 " + len(payload).to_bytes(4, "little") + payload
    return b"RIFF" + (4 + len(chunk)).to_bytes(4, "little") + b"WEBP" + chunk


def _vp8l(w, h):
    bits = (w - 1) | ((h - 1) << 14)
    payload = b"\x2f" + bits.to_bytes(4, "little") + b"\x00" * 5
    chunk = b"VP8L" + len(payload).to_bytes(4, "little") + payload
    return b"RIFF" + (4 + len(chunk)).to_bytes(4, "little") + b"WEBP" + chunk


def _vp8x(w, h):
    payload = b"\x00" * 4 + (w - 1).to_bytes(3, "little") + (h - 1).to_bytes(3, "little")
    chunk = b"VP8X" + len(payload).to_bytes(4, "little") + payload
    return b"RIFF" + (4 + len(chunk)).to_bytes(4, "little") + b"WEBP" + chunk


def _article_html(text):
    return f"""<!doctype html><html><head>
<title>Event release</title>
<meta property="og:type" content="article">
<meta property="og:title" content="Event release">
<meta property="og:image" content="/featured.webp">
<script type="application/ld+json">{{"@type":"NewsArticle","logo":{{"url":"/brand/json-logo.png"}}}}</script>
</head><body><h1>Event release</h1>
<article><p>{text}</p></article>
<img src="/brand/site-logo.png">
</body></html>"""


class TestWebModes(unittest.TestCase):
    def setUp(self):
        self.known = patch.object(web_fetch, "known_sites",
                                  return_value=[("www.pitchmystory.com", "/newswire")]).start()
        self.addCleanup(patch.stopall)
        self.public = patch.object(web_fetch, "is_public_http", return_value=True).start()

    def test_known_and_blocked(self):
        self.assertTrue(web_fetch.is_known_url("https://www.pitchmystory.com/newswire/x"))
        self.assertFalse(web_fetch.is_known_url("https://www.pitchmystory.com/about"))
        self.assertFalse(web_fetch.is_known_url("https://links.pitchmystory.com/CL0/x"))
        self.assertFalse(web_fetch.is_known_url("https://www.pitchmystory.com/media/unsubscribe?x=1"))
        self.assertTrue(web_fetch.is_article_url("https://www.pitchmystory.com/newswire/x"))
        self.assertFalse(web_fetch.is_article_url("https://links.pitchmystory.com/CL0/x"))

    def test_candidate_links_modes(self):
        links = [
            "https://www.pitchmystory.com/newswire/x",
            "https://links.pitchmystory.com/CL0/y",
            "https://www.pitchmystory.com/media/unsubscribe?x=1",
            "https://one.example/one",
            "https://two.example/two",
            "https://three.example/three",
        ]
        texts = {"https://two.example/two": "View the published release"}
        self.assertEqual(web_fetch.candidate_links(links, texts, "off"), [])
        self.assertEqual(web_fetch.candidate_links(links, texts, "known"),
                         ["https://www.pitchmystory.com/newswire/x"])
        got = web_fetch.candidate_links(links, texts, "probe")
        self.assertEqual(got[0], "https://www.pitchmystory.com/newswire/x")
        self.assertIn("https://two.example/two", got)
        self.assertLessEqual(len(got), int(config.COLLECT_MAX_WEB_LINKS))
        self.assertNotIn("https://links.pitchmystory.com/CL0/y", got)
        self.assertNotIn("https://www.pitchmystory.com/media/unsubscribe?x=1", got)


class TestSSRF(unittest.TestCase):
    def test_private_and_bad_schemes_blocked(self):
        for u in ("http://localhost/x", "http://127.0.0.1/x", "http://10.0.0.1/x",
                  "http://169.254.169.254/latest", "http://192.168.1.1/x",
                  "http://172.16.0.1/x", "http://example.com:8080/x",
                  "ftp://example.com/x", "http://user:pass@example.com/x",
                  "http://printer.local/x"):
            self.assertFalse(web_fetch.is_public_http(u), u)

    def test_public_ok(self):
        with patch("web_fetch.socket.getaddrinfo", return_value=PUBLIC_INFO):
            self.assertTrue(web_fetch.is_public_http("https://example.com/x"))
            self.assertTrue(web_fetch.is_public_http("http://example.com/x"))
        with patch("web_fetch.socket.getaddrinfo", return_value=PUBLIC_INFO):
            self.assertFalse(web_fetch.is_public_http("https://example.com:8443/x"))


class TestWebP(unittest.TestCase):
    def test_webp_dimensions(self):
        self.assertEqual(extract._image_dims(_vp8(640, 480)), (640, 480))
        self.assertEqual(extract._image_dims(_vp8l(500, 300)), (500, 300))
        self.assertEqual(extract._image_dims(_vp8x(1536, 1024)), (1536, 1024))
        self.assertEqual(extract._kind_from_bytes(_vp8(640, 480)), "photo")
        self.assertEqual(web_fetch._ext_for(_vp8x(1536, 1024)), ".webp")


class TestFetchArticle(unittest.TestCase):
    def test_article_uses_og_photo_and_separates_publisher_logos(self):
        text = ("KUALA LUMPUR: Event Me Now is a new digital home for the events "
                "industry in Malaysia, connecting organisers, venues and suppliers. ") * 6
        page = _article_html(text)
        image = _vp8(640, 480)

        def fake_fetch(url, max_bytes, timeout):
            if url.endswith(".webp"):
                return url, "image/webp", image
            return ("https://www.pitchmystory.com/newswire/x", "text/html; charset=utf-8",
                    page.encode())

        with patch.object(web_fetch, "is_public_http", return_value=True), \
             patch.object(web_fetch, "is_known_url", return_value=False), \
             patch.object(web_fetch, "_fetch", side_effect=fake_fetch):
            out = web_fetch.fetch_article("https://www.pitchmystory.com/newswire/x")
        self.assertTrue(out["ok"])
        self.assertTrue(out["is_article"])
        self.assertEqual(len(out["images"]), 1)
        self.assertEqual(out["images"][0]["name"], "webphoto-1.webp")
        self.assertEqual(out["logos"], [])
        self.assertTrue(any("/brand/" in u for u in out["publisher_logos"]))
        self.assertGreater(len(out["text"]), 500)

    def test_non_article_page_not_accepted(self):
        text = "Contact us for more information about our services. " * 20
        page = f"<html><head><title>Contact us</title></head><body><p>{text}</p></body></html>"

        with patch.object(web_fetch, "is_public_http", return_value=True), \
             patch.object(web_fetch, "is_known_url", return_value=False), \
             patch.object(web_fetch, "_fetch",
                          return_value=("https://example.com/contact",
                                        "text/html; charset=utf-8", page.encode())):
            out = web_fetch.fetch_article("https://example.com/contact")
        self.assertTrue(out["ok"])
        self.assertFalse(out["is_article"])
        self.assertEqual(out["images"], [])


if __name__ == "__main__":
    unittest.main()
