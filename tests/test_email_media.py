"""Tests for the N-3/N-4 media index + email_media / email_links storage.

Run: python3 -m unittest tests.test_email_media -v
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from msme import config, db
from msme.receive import media_index
from msme.receive.workflow_lab import _png


class MediaIndexTests(unittest.TestCase):
    def setUp(self):
        self.patch = patch.object(config, "BODY_LOGO_MIN_DIM", 200)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()

    def test_rows_kind_source_usable_chosen(self):
        rows = media_index.build_rows([
            ({"photo.png": _png(800, 600)}, "email_attachment", None),
            ({"logo.png": _png(250, 87)}, "gallery", "logo"),
            ({"icon.png": _png(40, 20)}, "body", "logo"),
        ])
        self.assertEqual(len(rows), 3)
        photo = rows[0]
        self.assertEqual(photo["kind"], "photo")
        self.assertTrue(photo["usable"])
        self.assertFalse(photo["chosen"])
        gallery = rows[1]
        self.assertEqual(gallery["source"], "gallery")
        self.assertTrue(gallery["chosen"])
        self.assertTrue(gallery["usable"])
        icon = rows[2]
        self.assertFalse(icon["usable"])          # 40x20 is below the floor
        self.assertEqual(icon["kind"], "logo")

    def test_non_image_attachment_skipped(self):
        rows = media_index.build_rows([
            ({"release.docx": b"PK\x03\x04not-an-image"}, "email_attachment", None),
        ])
        self.assertEqual(rows, [])

    def test_archive_path_resolved(self):
        import tempfile as _tf
        with _tf.TemporaryDirectory() as d:
            images = Path(d) / "images"
            images.mkdir()
            (images / "logo.png").write_bytes(_png(250, 87))
            rows = media_index.build_rows(
                [({"logo.png": _png(250, 87)}, "gallery", "logo")], archive_dir=d)
            self.assertTrue(Path(rows[0]["path"]).is_file())
            self.assertTrue(rows[0]["path"].endswith("logo.png"))


class DbStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.patches = [
            patch.object(config, "SQLITE_PATH", self.db_path),
            patch.object(config, "BODY_LOGO_MIN_DIM", 200),
        ]
        for p in self.patches:
            p.start()
        db.init_db()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_save_and_list_link(self):
        db.save_email_link(1, "msg-1", "Subject", {
            "linkType": "report", "url": "https://wearesocial.com/digital-2027",
            "source": "docx_rels", "confidence": 0.9,
            "candidates": ["https://wearesocial.com/digital-2027"]})
        db.save_email_link(1, "msg-1", "Subject", {
            "linkType": "speech", "url": "https://kabinet.gov.my/ucapan/2027",
            "source": "email_body"})
        links = db.primary_links("msg-1")
        self.assertEqual(links["report"], "https://wearesocial.com/digital-2027")
        self.assertEqual(links["speech"], "https://kabinet.gov.my/ucapan/2027")
        self.assertEqual(len(db.list_email_links("msg-1")), 2)

    def test_link_upsert_same_type(self):
        db.save_email_link(1, "msg-2", "S", {"linkType": "report", "url": "https://a.com/r"})
        db.save_email_link(2, "msg-2", "S", {"linkType": "report", "url": "https://b.com/r"})
        rows = [r for r in db.list_email_links("msg-2") if r["link_type"] == "report"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "https://b.com/r")

    def test_save_and_list_media(self):
        rows = media_index.build_rows([
            ({"photo.png": _png(800, 600)}, "email_attachment", None),
            ({"logo.png": _png(250, 87)}, "gallery", "logo"),
        ])
        db.save_email_media(5, "msg-3", rows)
        got = db.list_email_media("msg-3")
        self.assertEqual(len(got), 2)
        sources = {r["source"] for r in got}
        self.assertEqual(sources, {"email_attachment", "gallery"})
        gallery = [r for r in got if r["source"] == "gallery"][0]
        self.assertEqual(gallery["chosen"], 1)

    def test_media_replace_clears_stale(self):
        db.save_email_media(5, "msg-4", [{"name": "a.png", "source": "email_attachment"}])
        self.assertEqual(len(db.list_email_media("msg-4")), 1)
        db.save_email_media(6, "msg-4", [])       # a re-run with no media clears the rows
        self.assertEqual(db.list_email_media("msg-4"), [])


if __name__ == "__main__":
    unittest.main()
