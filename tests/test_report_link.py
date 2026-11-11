"""Tests for N-3 report link + N-4 speech capture + the build-time link append.

Run: python3 -m unittest tests.test_report_link -v
"""
import io
import unittest
import zipfile

from msme.receive import gov_summary, report_link


def _docx_with_links(urls):
    """A minimal DOCX zip whose document.xml.rels carries hyperlink relationships."""
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(
            f'<Relationship Id="rId{i}" '
            f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
            f'Target="{u}" TargetMode="External"/>'
            for i, u in enumerate(urls)
        )
        + "</Relationships>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/_rels/document.xml.rels", rels)
        z.writestr("word/document.xml", "<w:document/>")
    return buf.getvalue()


MELTWATER_LINKS = [
    "http://www.wearesocial.com/",
    "https://www.meltwater.com/en/global-digital-trends",
    "http://meltwater.com",
    "https://www.meltwater.com/en",
    "https://wearesocial.com/digital-2027",
    "https://wearesocial.com/",
]


class ExtractTests(unittest.TestCase):
    def test_docx_rels_hyperlinks(self):
        got = report_link.extract_docx_links(_docx_with_links(MELTWATER_LINKS))
        self.assertIn("https://wearesocial.com/digital-2027", got)
        self.assertIn("https://www.meltwater.com/en/global-digital-trends", got)

    def test_pdf_uri_fallback(self):
        data = b"%PDF-1.4 ... /A << /S /URI /URI (https://example.gov.my/ucapan/2027) >> ..."
        got = report_link.extract_pdf_links(data)
        self.assertIn("https://example.gov.my/ucapan/2027", got)

    def test_dedupe_and_scheme(self):
        got = report_link._dedupe(["https://a.com/x", "https://a.com/x", "mailto:x@y", "/rel"])
        self.assertEqual(got, ["https://a.com/x"])


class ScoreTests(unittest.TestCase):
    def test_report_like_scores_higher(self):
        self.assertGreater(report_link.score_url("https://wearesocial.com/digital-2027"),
                           report_link.score_url("https://wearesocial.com/"))
        self.assertGreater(report_link.score_url("https://example.com/report"), 0)

    def test_excluded_hosts(self):
        self.assertLess(report_link.score_url("https://facebook.com/report"), 0)
        self.assertLess(report_link.score_url("https://x.com/unsubscribe"), 0)


class DetectTests(unittest.TestCase):
    def test_meltwater_report(self):
        meta = report_link.detect(
            subject="Fifteen years of Digital reports: Meltwater & We Are Social 2027",
            body="The full report is here.",
            links=[],
            files={"release.docx": _docx_with_links(MELTWATER_LINKS)},
        )
        self.assertIsNotNone(meta)
        self.assertEqual(meta["linkType"], "report")
        self.assertEqual(meta["url"], "https://wearesocial.com/digital-2027")
        self.assertEqual(meta["source"], "docx_rels")

    def test_report_wording_without_link_is_none(self):
        self.assertIsNone(report_link.detect(
            subject="Our annual report", body="report", links=[], files={}))

    def test_link_without_report_wording_is_none(self):
        self.assertIsNone(report_link.detect(
            subject="Product launch", body="hello",
            links=["https://wearesocial.com/digital-2027"], files={}))


class GovCaptureTests(unittest.TestCase):
    def test_speech_link_captured(self):
        meta = gov_summary.capture(
            subject="Budget 2027 POV: Where should SMEs start?",
            body="Here is the minister's speech.",
            links=["https://www.kabinet.gov.my/ucapan/2027", "https://example.com/landing"],
            from_email="news@ellerton.co",
        )
        self.assertIsNotNone(meta)
        self.assertEqual(meta["linkType"], "speech")
        self.assertEqual(meta["url"], "https://www.kabinet.gov.my/ucapan/2027")

    def test_no_gov_marker_is_none(self):
        self.assertIsNone(gov_summary.capture(
            subject="Product launch", body="hello",
            links=["https://x.com/speech"], from_email="news@agency.com"))

    def test_gov_marker_without_speech_link_is_none(self):
        self.assertIsNone(gov_summary.capture(
            subject="Budget 2027 commentary", body="our view",
            links=["https://example.com/report"], from_email="news@agency.com"))


class EngineAppendTests(unittest.TestCase):
    def test_render_article_appends_report_and_speech(self):
        from msme.repurpose.engine import build_site
        draft = {
            "title": "Test", "excerpt": "1 January 2026", "categories": ["news"],
            "body": [{"sub": "", "paras": ["Body paragraph."], "quotes": []}],
            "images": {"featured": {}, "in_body": [], "captions": {}},
        }
        html = build_site.render_article(
            draft, {"cover": None, "in_body": {}},
            links={"reportUrl": "https://wearesocial.com/digital-2027",
                   "speechUrl": "https://www.kabinet.gov.my/ucapan/2027"})
        self.assertIn("Read the full report", html)
        self.assertIn("https://wearesocial.com/digital-2027", html)
        self.assertIn("speech", html)
        self.assertIn("https://www.kabinet.gov.my/ucapan/2027", html)


if __name__ == "__main__":
    unittest.main()
