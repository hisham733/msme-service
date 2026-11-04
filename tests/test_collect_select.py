# =============================================================================
# FILE HEADER
# file    : tests/test_collect_select.py
# role    : Tests — D24 collect-then-select + media dimension rules
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : unit-test the deterministic parts of the receive pipeline without
#           calling Gmail, Drive or an AI provider.
# pages   : n/a
# calls   : pipeline, extract, web_fetch, config
# called  : developer / CI (python3 -m unittest tests.test_collect_select)
# amend   : no network. If a helper moves, update the import, not the assertion.
# =============================================================================
"""Unit tests for the D24 collect-then-select rules.

Run:
    python3 -m unittest tests.test_collect_select -v
"""
import io
import struct
import sys
import unittest
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from msme import config
from msme.receive import extract, pipeline, web_fetch


def _png(width, height):
    """Minimal PNG bytes with a real IHDR (enough for dimension parsing)."""
    sig = b"\x89PNG\r\n\x1a\n"

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def _docx_bytes(n_images, width=520, height=300):
    """Synthetic DOCX zip with n PNGs in word/media/ (no rels needed)."""
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w") as z:
        for i in range(1, n_images + 1):
            z.writestr(f"word/media/image{i}.png", _png(width, height))
    return bio.getvalue()


class DocumentLimitTests(unittest.TestCase):
    def test_limits_are_the_confirmed_values(self):
        self.assertEqual(config.MAX_DOC_IMAGES, 10)
        self.assertEqual(config.DOC_IMAGE_SCAN_MAX, 25)
        self.assertEqual(config.PDF_TEXT_MAX_PAGES, 30)
        self.assertEqual(config.DOC_TEXT_MAX_CHARS, 150000)

    def test_pdf_text_stops_at_30_pages(self):
        class _Page:
            def __init__(self, text):
                self._text = text

            def extract_text(self):
                return self._text

        class _Reader:
            pages = [_Page("x" * 1000) for _ in range(40)]

        text, truncated, pages = extract._extract_pdf_text(_Reader())
        self.assertTrue(truncated)
        self.assertEqual(pages, 30)
        self.assertEqual(len(text.replace("\n\n", "")), 30000)

    def test_docx_image_scan_is_capped_at_10(self):
        data = _docx_bytes(12)
        imgs, truncated = extract._docx_images(data)
        self.assertEqual(len(imgs), 10)
        self.assertTrue(truncated)
        photos = extract.extract_doc_images(data, "many.docx")
        self.assertLessEqual(len(photos), 10)

    def test_text_cap_keeps_150k(self):
        text = extract._cap_text("a" * 200000, config.DOC_TEXT_MAX_CHARS)
        self.assertEqual(len(text.split("\n\n")[0]), 150000)
        self.assertIn("truncated", text)


class MediaDimensionTests(unittest.TestCase):
    def test_logo_dimensions_count_even_when_small_in_bytes(self):
        raw = _png(250, 87)
        self.assertLess(len(raw), 10000)
        self.assertEqual(extract._kind_from_bytes(raw), "logo")
        self.assertGreaterEqual(max(extract._image_dims(raw)), config.BODY_LOGO_MIN_DIM)

    def test_small_thumbnail_is_not_a_logo(self):
        raw = _png(100, 55)
        self.assertEqual(extract._kind_from_bytes(raw), "logo")
        self.assertLess(max(extract._image_dims(raw)), config.BODY_LOGO_MIN_DIM)

    def test_wide_photo_is_photo(self):
        raw = _png(800, 440)
        self.assertEqual(extract._kind_from_bytes(raw), "photo")

    def test_body_image_floor_is_not_a_size_gate(self):
        self.assertLessEqual(config.BODY_IMAGE_MIN_BYTES, 2048)


class CandidateTests(unittest.TestCase):
    def test_release_beats_agenda(self):
        release = {"source": "attachment_pdf", "name": "Press Release.pdf",
                   "text": "FOR IMMEDIATE RELEASE\n\nKUALA LUMPUR, 22 Sept 2026 - "
                           "Finnfund signs a senior loan agreement with EVF. " * 20}
        agenda = {"source": "drive_link", "name": "Agenda.docx",
                  "text": "Agenda programme schedule invitation. " * 30}
        self.assertGreater(pipeline._candidate_score("Finnfund signs loan with EVF", release),
                           pipeline._candidate_score("Finnfund signs loan with EVF", agenda))

    def test_rank_keeps_chosen_attachment(self):
        subject = "Finnfund signs senior loan agreement with EVF"
        chosen = {"source": "attachment_pdf", "name": "cover.pdf",
                  "text": "Short cover note. " * 30}
        better = {"source": "web_link", "name": "Release",
                  "text": "FOR IMMEDIATE RELEASE\n\nKUALA LUMPUR - Finnfund signs a loan. " * 40}
        top = pipeline._rank_candidates(subject, [better, chosen], chosen["text"])
        self.assertTrue(any(c["text"] == chosen["text"] for c in top))

    def test_trusted_links_drops_hallucinated_decision_link(self):
        model = {"linksFound": ["https://news.example.com/release"]}
        self.assertEqual(pipeline._trusted_links(model, "https://evil.example/x"),
                         ["https://news.example.com/release"])

    def test_trusted_links_keeps_decision_link_present_in_email(self):
        model = {"linksFound": ["https://news.example.com/release"]}
        self.assertEqual(pipeline._trusted_links(model, "https://news.example.com/release"),
                         ["https://news.example.com/release"])


class WebSourceTests(unittest.TestCase):
    def test_cision_newsroom_is_an_article_url(self):
        self.assertTrue(web_fetch.is_article_url(
            "https://news.cision.com/finnfund/r/finnfund-signs-senior-loan-agreement,"
            "c4401969"
        ))

    def test_cision_image_page_is_not_an_article(self):
        self.assertFalse(web_fetch.is_article_url(
            "https://news.cision.com/finnfund/i/evf-vietnam,c3568526"))

    def test_social_and_drive_are_not_article_urls(self):
        self.assertFalse(web_fetch.is_article_url("https://www.linkedin.com/posts/x"))
        self.assertFalse(web_fetch.is_article_url(
            "https://drive.google.com/drive/folders/abc"))


if __name__ == "__main__":
    unittest.main()
