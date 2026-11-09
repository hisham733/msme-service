"""Tests for N-2 "library update" intake (docs/new-rules/N-2-library-update.md).

Run: python3 -m unittest tests.test_library_update -v
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from msme import config
from msme.receive import gallery, library_update
from msme.receive.workflow_lab import _png


class ClassifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        idx = self.dir / "index.json"
        idx.write_text(json.dumps({"version": 1, "updated": "", "images": []}),
                       encoding="utf-8")
        self.patches = [
            patch.object(config, "LIBRARY_UPDATE_MIN_CHARS", 400),
            patch.object(config, "LIBRARY_UPDATE_PHRASES",
                         ("new logo", "building photograph", "facade", "update our records")),
            patch.object(config, "LIBRARY_UPDATE_NEGATIVE",
                         ("for immediate release", "press release", "media release", "siaran akhbar")),
            patch.object(config, "GALLERY_INDEX", str(idx)),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def _ctx(self, **over):
        base = {
            "subject": "", "raw_body": "", "body_text": "",
            "candidates": [], "decision": {}, "attachments": [],
            "files": {}, "needs_human": False, "media": {},
            "from_email": "", "from_name": "", "message_id": "", "date": "",
        }
        base.update(over)
        return base

    def test_bpmb_library_update_hit(self):
        ctx = self._ctx(
            subject="BPMB Group Logo and Building Photographs",
            raw_body="Please find BPMB Group logo files and building photographs.",
            decision={"chosenFileName": "", "imagesAvailable": True},
            attachments=[{"filename": "bpmb-logo.png"}, {"filename": "building.jpg"}],
            files={"bpmb-logo.png": _png(250, 87), "building.jpg": _png(800, 600)},
            media={"hasPic": True, "hasLogo": True},
        )
        hit = library_update.classify(ctx)
        self.assertIsNotNone(hit)
        self.assertEqual(len(hit["files"]), 2)

    def test_press_release_is_not_library_update(self):
        ctx = self._ctx(
            subject="BPMB launches RM500m SME fund",
            raw_body="FOR IMMEDIATE RELEASE. BPMB today announced...",
            body_text="BPMB today announced a new fund. " + ("x" * 400),
            decision={"chosenFileName": "release.docx", "imagesAvailable": True},
            attachments=[{"filename": "release.docx"}, {"filename": "logo.png"}],
            files={"logo.png": _png(250, 87)},
        )
        self.assertIsNone(library_update.classify(ctx))

    def test_missing_attachment_is_not_library_update(self):
        # Climahart: a "new logo" phrase but nothing was collected
        ctx = self._ctx(
            subject="new logo for our records",
            raw_body="Please update our records with the new logo.",
            decision={"chosenFileName": "", "imagesAvailable": False},
            attachments=[], files={}, needs_human=True, media={},
        )
        self.assertIsNone(library_update.classify(ctx))

    def test_release_text_wins_over_phrase(self):
        ctx = self._ctx(
            subject="BPMB new logo and launch",
            raw_body="FOR IMMEDIATE RELEASE " + ("x" * 600),
            body_text="a" * 500,
            decision={"chosenFileName": "release.docx", "imagesAvailable": True},
            attachments=[{"filename": "release.docx"}], files={},
        )
        self.assertIsNone(library_update.classify(ctx))

    def test_needs_human_with_no_asset_goes_normal(self):
        ctx = self._ctx(
            subject="BPMB Group Logo and Building Photographs",
            raw_body="new logo and building photograph",
            decision={"chosenFileName": "", "imagesAvailable": True},
            attachments=[], files={}, needs_human=True, media={},
        )
        self.assertIsNone(library_update.classify(ctx))


class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "gallery"
        self.dir.mkdir()
        (self.dir / "bpmb.png").write_bytes(b"old-bytes")
        index = {"version": 1, "updated": "2026-11-07", "images": [
            {"id": "bpmb-old", "brand": "BPMB", "aliases": ["BPMB"],
             "domains": ["bpmb.com.my"], "type": "logo", "file": "bpmb.png",
             "updated": "2026-11-01", "status": "active"},
        ]}
        (self.dir / "index.json").write_text(json.dumps(index), encoding="utf-8")
        self.patches = [
            patch.object(config, "GALLERY_DIR", str(self.dir)),
            patch.object(config, "GALLERY_INDEX", str(self.dir / "index.json")),
            patch.object(config, "GALLERY_MAX_FILE_BYTES", 10 * 1024 * 1024),
            patch.object(config, "BODY_LOGO_MIN_DIM", 200),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def _data(self):
        return json.loads((self.dir / "index.json").read_text(encoding="utf-8"))

    def _cand(self, **over):
        base = {"brand": "BPMB", "aliases": ["BPMB"], "domains": ["bpmb.com.my"],
                "filename": "bpmb-logo.png", "bytes": _png(250, 87), "kind": "logo",
                "width": 250, "height": 87, "confidence": "high"}
        base.update(over)
        return base

    def test_auto_active_supersedes_old(self):
        data = self._data()
        r = gallery.promote_if_safe(self._cand(), data)
        gallery.write_index(data)
        self.assertTrue(r["promoted"])
        data = self._data()
        active = [e for e in data["images"] if e["brand"] == "BPMB"
                  and e["status"] == "active" and e["type"] == "logo"]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["source"], "sender")
        old = [e for e in data["images"] if e["id"] == "bpmb-old"]
        self.assertEqual(old[0]["status"], "superseded")

    def test_new_brand_pending(self):
        cand = self._cand(brand="NewCorp", aliases=["NewCorp"], domains=["newcorp.com"])
        r = gallery.promote_if_safe(cand, self._data())
        self.assertFalse(r["promoted"])
        self.assertEqual(r["reason"], "new-brand")

    def test_building_photo_pending(self):
        cand = self._cand(filename="building.jpg", kind="photo",
                          bytes=_png(800, 600), width=800, height=600)
        r = gallery.promote_if_safe(cand, self._data())
        self.assertFalse(r["promoted"])
        self.assertEqual(r["reason"], "not-a-logo")

    def test_low_confidence_pending(self):
        cand = self._cand(confidence="low")
        r = gallery.promote_if_safe(cand, self._data())
        self.assertFalse(r["promoted"])
        self.assertEqual(r["reason"], "low-brand-confidence")


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.gallery = self.dir / "gallery"
        self.gallery.mkdir()
        self.updates = self.dir / "updates"
        index = {"version": 1, "updated": "2026-11-07", "images": [
            {"id": "bpmb-old", "brand": "BPMB", "aliases": ["BPMB"],
             "domains": ["bpmb.com.my"], "type": "logo", "file": "bpmb.png",
             "updated": "2026-11-01", "status": "active"},
        ]}
        (self.gallery / "bpmb.png").write_bytes(b"old")
        (self.gallery / "index.json").write_text(json.dumps(index), encoding="utf-8")
        self.patches = [
            patch.object(config, "GALLERY_DIR", str(self.gallery)),
            patch.object(config, "GALLERY_INDEX", str(self.gallery / "index.json")),
            patch.object(config, "GALLERY_UPDATES_DIR", str(self.updates)),
            patch.object(config, "GALLERY_MAX_FILE_BYTES", 10 * 1024 * 1024),
            patch.object(config, "BODY_LOGO_MIN_DIM", 200),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def _hit(self, **over):
        base = {
            "brand": "BPMB", "confidence": "high", "aliases": ["BPMB"],
            "domains": ["bpmb.com.my"], "subject": "BPMB Group Logo and Building Photographs",
            "from_email": "news@bpmb.com.my", "from_name": "BPMB", "message_id": "m1",
            "date": "2026-11-07",
            "files": {"bpmb-logo.png": _png(250, 87), "building.jpg": _png(800, 600)},
            "attachments": [{"filename": "bpmb-logo.png"}, {"filename": "building.jpg"}],
        }
        base.update(over)
        return base

    def test_store_writes_update_and_promotes_logo(self):
        out = library_update.store_update(self._hit())
        self.assertEqual(out["promoted"], 1)
        self.assertEqual(out["pending"], 1)
        meta = json.loads((self.updates / out["folder"] / "update.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["status"], "active")
        self.assertEqual(meta["brand"], "BPMB")
        self.assertTrue((self.updates / out["folder"] / "images" / "bpmb-logo.png").is_file())
        idx = json.loads((self.gallery / "index.json").read_text(encoding="utf-8"))
        active = [e for e in idx["images"] if e["brand"] == "BPMB" and e["status"] == "active"]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["source"], "sender")

    def test_store_with_corrupt_index_does_not_crash(self):
        (self.gallery / "index.json").write_text("{not json", encoding="utf-8")
        hit = self._hit(brand="", confidence="low", aliases=[], domains=[],
                        files={"logo.png": _png(250, 87)})
        out = library_update.store_update(hit)
        self.assertEqual(out["promoted"], 0)
        # update.json is still written; no index rewrite happened (no promotion)
        self.assertTrue((self.updates / out["folder"] / "update.json").is_file())


if __name__ == "__main__":
    unittest.main()
