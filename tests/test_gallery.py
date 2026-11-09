"""Tests for the N-1 local logo gallery (hybrid priority ladder + option B).

Run: python3 -m unittest tests.test_gallery -v
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from msme import config
from msme.receive import gallery, pipeline
from msme.receive.workflow_lab import _png


class GalleryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "gallery"
        self.dir.mkdir()
        for name in ("bpmb.png", "cimb.png", "maybank.png"):
            (self.dir / name).write_bytes(b"fake-image-bytes")
        index = {
            "version": 1,
            "updated": "2026-11-07",
            "images": [
                {"id": "bpmb", "brand": "BPMB",
                 "aliases": ["Bank Pembangunan Malaysia", "Bank Pembangunan Malaysia Berhad", "BPMB"],
                 "domains": ["bpmb.com.my"], "type": "logo", "file": "bpmb.png",
                 "updated": "2026-11-07", "status": "active"},
                {"id": "cimb", "brand": "CIMB",
                 "aliases": ["CIMB Bank", "CIMB"], "domains": ["cimb.com"],
                 "type": "logo", "file": "cimb.png", "updated": "2026-05-01", "status": "active"},
                {"id": "maybank", "brand": "Maybank",
                 "aliases": ["Maybank", "Malayan Banking"], "domains": ["maybank.com"],
                 "type": "logo", "file": "maybank.png", "updated": "2026-06-01", "status": "active"},
                {"id": "matrade", "brand": "MATRADE",
                 "aliases": ["MATRADE", "Malaysia External Trade Development Corporation"],
                 "domains": ["matrade.gov.my"], "type": "logo", "file": "matrade.png",
                 "updated": "2026-11-07", "status": "pending"},
                {"id": "affin", "brand": "AFFIN",
                 "aliases": ["AFFIN Group", "Affin Bank"], "domains": ["affin.com"],
                 "type": "logo", "file": "affin.png", "updated": "2025-01-01", "status": "superseded"},
            ],
        }
        self.index_path = self.dir / "index.json"
        self.index_path.write_text(json.dumps(index), encoding="utf-8")
        self.patches = [
            patch.object(config, "GALLERY_DIR", str(self.dir)),
            patch.object(config, "GALLERY_INDEX", str(self.index_path)),
            patch.object(config, "GALLERY_AGENCY_DOMAINS",
                         ("cision.com", "mediaoutreach.com", "vritimes.com")),
            patch.object(config, "GALLERY_FUZZY_MIN", 0.88),
            patch.object(config, "GALLERY_BODY_LEAD_CHARS", 600),
            patch.object(config, "BODY_LOGO_MIN_DIM", 200),
            patch.object(config, "GALLERY_MAX_FILE_BYTES", 10 * 1024 * 1024),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def _email(self, **over):
        base = {"subject": "", "from_name": "", "from_email": "",
                "filenames": [], "body": ""}
        base.update(over)
        return base

    def _match(self, **over):
        return gallery.match(self._email(**over), gallery.load_index())

    # --- the seven tiers -------------------------------------------------

    def test_tier1_sender_domain(self):
        r = self._match(from_email="news@bpmb.com.my")
        self.assertEqual(r["status"], "hit")
        self.assertEqual(r["detail"]["brand"], "BPMB")
        self.assertEqual(r["detail"]["tier"], 1)

    def test_tier2_alias_in_subject(self):
        r = self._match(from_email="noreply@cision.com",
                        subject="Bank Pembangunan Malaysia Berhad launches RM500m SME fund")
        self.assertEqual(r["status"], "hit")
        self.assertEqual(r["detail"]["brand"], "BPMB")
        self.assertEqual(r["detail"]["tier"], 2)

    def test_tier3_alias_in_display_name(self):
        r = self._match(from_name="Maybank Newsroom", from_email="news@agency.com",
                        subject="Budget update")
        self.assertEqual(r["status"], "hit")
        self.assertEqual(r["detail"]["brand"], "Maybank")
        self.assertEqual(r["detail"]["tier"], 3)

    def test_tier4_alias_in_filename_and_body(self):
        r = self._match(from_email="noreply@cision.com", subject="Update",
                        filenames=["CIMB_SME_Release.pdf"], body="CIMB today announced...")
        self.assertEqual(r["status"], "hit")
        self.assertEqual(r["detail"]["brand"], "CIMB")
        self.assertEqual(r["detail"]["tier"], 4)

    def test_tier5_body_lead_repeat(self):
        # alias in the first 600 chars AND >= 2x in the body, any sender (a
        # forwarded editor email whose release text names the brand).
        r = self._match(from_email="editor@malaysiasme.com.my", subject="Fwd: release",
                        body="CIMB launches... CIMB said... CIMB will...")
        self.assertEqual(r["status"], "hit")
        self.assertEqual(r["detail"]["brand"], "CIMB")
        self.assertEqual(r["detail"]["tier"], 5)

    def test_tier5_requires_lead_mention(self):
        # >= 2x in the body but never in the first 600 chars -> miss
        r = self._match(from_email="editor@malaysiasme.com.my", subject="Update",
                        body=("x" * 600) + " CIMB ... CIMB ...")
        self.assertEqual(r["status"], "miss")

    def test_tier6_fuzzy_may_bank(self):
        r = self._match(from_email="news@agency.com", subject="May Bank announces results")
        self.assertEqual(r["status"], "hit")
        self.assertEqual(r["detail"]["brand"], "Maybank")
        self.assertEqual(r["detail"]["tier"], 6)
        self.assertGreaterEqual(r["detail"]["score"], 88)

    def test_tier7_ambiguity_is_a_miss(self):
        r = self._match(from_email="news@cimb.com",
                        subject="CIMB and Maybank launch a joint SME programme")
        self.assertEqual(r["status"], "miss")
        self.assertEqual(r["detail"]["reason"], "ambiguous")
        self.assertEqual(r["detail"]["tier"], 7)
        self.assertEqual(set(r["detail"]["brands"]), {"CIMB", "Maybank"})

    # --- entry state / normalisation ------------------------------------

    def test_pending_and_superseded_are_ignored(self):
        self.assertEqual(self._match(subject="MATRADE at FoodExpo")["status"], "miss")
        self.assertEqual(self._match(subject="AFFIN Group results")["status"], "miss")

    def test_exact_normalisation(self):
        self.assertEqual(self._match(subject="BPMB, launches fund")["detail"]["brand"], "BPMB")
        self.assertEqual(self._match(subject="CIMB Bank, launches")["detail"]["brand"], "CIMB")

    def test_short_alias_is_not_exact(self):
        self.assertFalse(gallery._whole("AB", "AB launches"))
        self.assertFalse(gallery._whole("A", "A launches"))

    def test_agency_domain_helper(self):
        self.assertTrue(gallery.is_agency("noreply@cision.com"))
        self.assertTrue(gallery.is_agency("mail.mediaoutreach.com"))
        self.assertFalse(gallery.is_agency("bpmb.com.my"))

    # --- store / path safety --------------------------------------------

    def test_pick_reads_the_file(self):
        picked = gallery.pick({"file": "bpmb.png"})
        self.assertEqual(picked["name"], "bpmb.png")
        self.assertEqual(picked["bytes"], b"fake-image-bytes")

    def test_pick_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            gallery.pick({"file": "../creds/gmail.json"})
        with self.assertRaises(ValueError):
            gallery.pick({"file": "/etc/passwd"})

    def test_pick_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            gallery.pick({"file": "missing.png"})

    def test_pick_oversize(self):
        with patch.object(config, "GALLERY_MAX_FILE_BYTES", 4):
            with self.assertRaises(ValueError):
                gallery.pick({"file": "bpmb.png"})

    def test_load_index_missing_and_corrupt(self):
        with patch.object(config, "GALLERY_INDEX", str(self.dir / "nope.json")):
            with self.assertRaises(FileNotFoundError):
                gallery.load_index()
        bad = self.dir / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            gallery.load_index(str(bad))


class OptionBTests(unittest.TestCase):
    """A tiny logo must not suppress the gallery (N-1 option B)."""

    def setUp(self):
        self.patch = patch.object(config, "BODY_LOGO_MIN_DIM", 200)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()

    def test_doc_logo_needs_200px_or_vector(self):
        small = [{"images": [{"kind": "logo", "width": 40, "height": 20}]}]
        usable = [{"images": [{"kind": "logo", "width": 250, "height": 87}]}]
        vector = [{"images": [{"kind": "logo", "width": 0, "height": 0, "vector": True}]}]
        photo = [{"images": [{"kind": "photo", "width": 1536, "height": 1024}]}]
        self.assertFalse(pipeline._usable_doc_logo(small))
        self.assertTrue(pipeline._usable_doc_logo(usable))
        self.assertTrue(pipeline._usable_doc_logo(vector))
        self.assertFalse(pipeline._usable_doc_logo(photo))

    def test_logo_file_needs_200px_or_svg(self):
        model = {"attachments": [{"filename": "logo.png"}]}
        self.assertFalse(pipeline._usable_logo_files(model, {"logo.png": _png(40, 20)}))
        self.assertTrue(pipeline._usable_logo_files(model, {"logo.png": _png(250, 87)}))
        svg = {"attachments": [{"filename": "logo.svg"}]}
        self.assertTrue(pipeline._usable_logo_files(svg, {"logo.svg": b"<svg/>"}))
        not_logo = {"attachments": [{"filename": "photo.png"}]}
        self.assertFalse(pipeline._usable_logo_files(not_logo, {"photo.png": _png(800, 600)}))


if __name__ == "__main__":
    unittest.main()
